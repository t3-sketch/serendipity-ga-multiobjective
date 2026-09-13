"""ComiRec-SA: self-attentive multi-interest candidate generation.

Reference:
    Yukuo Cen et al. "Controllable Multi-Interest Framework for Recommendation."
    KDD 2020. arXiv:2005.09347. https://github.com/THUDM/ComiRec

Interest extraction follows the paper's self-attentive variant:
    A = softmax(W2 tanh(W1 H)) over sequence positions, V_u = A^T H,
producing n_interests read-out vectors. Training routes each target item to the
interest that scores it highest (the paper's argmax routing).

Two choices are recorded in ../REPORT.md. The loss is the full-catalogue softmax
used by the SASRec arm rather than the paper's sampled softmax, so that this arm
differs from the baseline only in architecture. The controllable aggregation module
(the lambda-weighted greedy diversification) is switched off: subset selection is
the job of the reranking stage this experiment holds fixed, so scoring is the
paper's per-item retrieval score max_k v_k . e_i.
"""
from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F

from recbole.model.abstract_recommender import SequentialRecommender
from recbole.utils import InputType


class ComiRecSA(SequentialRecommender):
    input_type = InputType.POINTWISE

    def __init__(self, config, dataset):
        super().__init__(config, dataset)

        self.hidden_size = config["hidden_size"]
        self.n_interests = config["n_interests"]
        self.attn_hidden_size = config["attn_hidden_size"]
        self.hidden_dropout_prob = config["hidden_dropout_prob"]
        self.layer_norm_eps = config["layer_norm_eps"]
        self.initializer_range = config["initializer_range"]
        self.loss_type = config["loss_type"]
        if self.loss_type != "CE":
            raise ValueError("This arm is defined with the full-catalogue softmax loss")

        self.item_embedding = nn.Embedding(self.n_items, self.hidden_size, padding_idx=0)
        self.position_embedding = nn.Embedding(self.max_seq_length, self.hidden_size)
        self.LayerNorm = nn.LayerNorm(self.hidden_size, eps=self.layer_norm_eps)
        self.dropout = nn.Dropout(self.hidden_dropout_prob)
        self.interest_w1 = nn.Linear(self.hidden_size, self.attn_hidden_size, bias=False)
        self.interest_w2 = nn.Linear(self.attn_hidden_size, self.n_interests, bias=False)
        self.loss_fct = nn.CrossEntropyLoss()

        # Diagnostic only: how often each interest wins the argmax routing.
        self.register_buffer("interest_usage", torch.zeros(self.n_interests, dtype=torch.long),
                             persistent=False)

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            module.weight.data.normal_(mean=0.0, std=self.initializer_range)
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)
        if isinstance(module, nn.Linear) and module.bias is not None:
            module.bias.data.zero_()

    def forward(self, item_seq, item_seq_len):
        """Return the n_interests read-out vectors of each sequence: [B K H]."""
        position_ids = torch.arange(item_seq.size(1), dtype=torch.long, device=item_seq.device)
        position_ids = position_ids.unsqueeze(0).expand_as(item_seq)
        hidden = self.item_embedding(item_seq) + self.position_embedding(position_ids)
        hidden = self.dropout(self.LayerNorm(hidden))

        attention = self.interest_w2(torch.tanh(self.interest_w1(hidden)))  # [B T K]
        padding = (item_seq == 0).unsqueeze(-1)
        attention = attention.masked_fill(padding, float("-inf"))
        attention = F.softmax(attention, dim=1)
        # Sequences shorter than the window keep only real positions; a fully padded
        # row cannot occur because RecBole never yields an empty prefix.
        return torch.einsum("btk,bth->bkh", attention, hidden)

    def calculate_loss(self, interaction):
        interests = self.forward(interaction[self.ITEM_SEQ], interaction[self.ITEM_SEQ_LEN])
        pos_items = interaction[self.POS_ITEM_ID]
        pos_emb = self.item_embedding(pos_items)
        routing = torch.einsum("bkh,bh->bk", interests, pos_emb)
        chosen = routing.argmax(dim=1)
        readout = interests[torch.arange(interests.size(0), device=interests.device), chosen]
        logits = torch.matmul(readout, self.item_embedding.weight.transpose(0, 1))
        self.interest_usage += torch.bincount(chosen.detach(), minlength=self.n_interests)
        return self.loss_fct(logits, pos_items)

    def predict(self, interaction):
        interests = self.forward(interaction[self.ITEM_SEQ], interaction[self.ITEM_SEQ_LEN])
        test_emb = self.item_embedding(interaction[self.ITEM_ID])
        return torch.einsum("bkh,bh->bk", interests, test_emb).max(dim=1).values

    def full_sort_predict(self, interaction):
        interests = self.forward(interaction[self.ITEM_SEQ], interaction[self.ITEM_SEQ_LEN])
        scores = torch.matmul(interests, self.item_embedding.weight.transpose(0, 1))
        return scores.max(dim=1).values  # [B n_items]

    def interest_assignment(self, item_seq, item_seq_len, item_ids):
        """Diagnostic: which interest supplies the score of each given item."""
        interests = self.forward(item_seq, item_seq_len)
        scores = torch.matmul(interests, self.item_embedding.weight.transpose(0, 1))
        return scores[:, :, item_ids].argmax(dim=1)
