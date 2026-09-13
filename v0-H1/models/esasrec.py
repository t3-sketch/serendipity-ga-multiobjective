"""eSASRec: SASRec's next-item objective with LiGR blocks and sampled softmax.

Reference:
    Daria Tikhonovich et al. "eSASRec: Enhancing Transformer-based Recommendations
    in a Modular Fashion." RecSys 2025. arXiv:2508.06450.
    LiGR blocks follow Borisyuk et al. arXiv:2502.03417, eq. (1) of the eSASRec paper:
    h^{j+1} = h^j + F(LayerNorm(h^j)) * sigmoid(h^j W).
    The gate reads the un-normalised residual stream, matching the RecTools
    LiGRLayer implementation the paper's authors released.

Deviations from the paper are recorded in ../REPORT.md: the training target comes
from RecBole's prefix augmentation (one next item per prefix) instead of predicting
every shifted position in one pass, and mixed negative sampling is left off.
"""
from __future__ import annotations

import math

import torch
from torch import nn
from torch.nn import functional as F

from recbole.model.sequential_recommender.sasrec import SASRec
from recbole.utils import InputType


class CausalSelfAttention(nn.Module):
    """Multi-head attention without the residual and normalisation of RecBole's block.

    The LiGR block owns the residual path, so this module only returns the
    attention output for the additive mask RecBole builds in get_attention_mask.
    """

    def __init__(self, n_heads, hidden_size, attn_dropout_prob, hidden_dropout_prob):
        super().__init__()
        if hidden_size % n_heads != 0:
            raise ValueError(f"hidden size {hidden_size} must divide into {n_heads} heads")
        self.n_heads = n_heads
        self.head_size = hidden_size // n_heads
        self.scale = math.sqrt(self.head_size)
        self.query = nn.Linear(hidden_size, hidden_size)
        self.key = nn.Linear(hidden_size, hidden_size)
        self.value = nn.Linear(hidden_size, hidden_size)
        self.dense = nn.Linear(hidden_size, hidden_size)
        self.attn_dropout = nn.Dropout(attn_dropout_prob)
        self.out_dropout = nn.Dropout(hidden_dropout_prob)

    def _split(self, x):
        batch, length, _ = x.shape
        return x.view(batch, length, self.n_heads, self.head_size).permute(0, 2, 1, 3)

    def forward(self, hidden_states, attention_mask):
        query = self._split(self.query(hidden_states))
        key = self._split(self.key(hidden_states))
        value = self._split(self.value(hidden_states))
        scores = torch.matmul(query, key.transpose(-1, -2)) / self.scale
        scores = scores + attention_mask
        probs = self.attn_dropout(F.softmax(scores, dim=-1))
        context = torch.matmul(probs, value).permute(0, 2, 1, 3).contiguous()
        context = context.view(hidden_states.size(0), hidden_states.size(1), -1)
        return self.out_dropout(self.dense(context))


class SwiGLU(nn.Module):
    """Feed-forward layer with SwiGLU activation, as used by the eSASRec authors."""

    def __init__(self, hidden_size, multiplier, hidden_dropout_prob):
        super().__init__()
        inner = hidden_size * multiplier
        self.gate_proj = nn.Linear(hidden_size, inner, bias=False)
        self.up_proj = nn.Linear(hidden_size, inner, bias=False)
        self.down_proj = nn.Linear(inner, hidden_size, bias=False)
        self.dropout = nn.Dropout(hidden_dropout_prob)

    def forward(self, hidden_states):
        activated = F.silu(self.gate_proj(hidden_states)) * self.up_proj(hidden_states)
        return self.dropout(self.down_proj(activated))


class LiGRLayer(nn.Module):
    def __init__(self, n_heads, hidden_size, ff_multiplier, hidden_dropout_prob,
                 attn_dropout_prob, layer_norm_eps):
        super().__init__()
        self.attn_norm = nn.LayerNorm(hidden_size, eps=layer_norm_eps)
        self.attention = CausalSelfAttention(n_heads, hidden_size, attn_dropout_prob,
                                             hidden_dropout_prob)
        self.attn_gate = nn.Linear(hidden_size, hidden_size)
        self.ff_norm = nn.LayerNorm(hidden_size, eps=layer_norm_eps)
        self.feed_forward = SwiGLU(hidden_size, ff_multiplier, hidden_dropout_prob)
        self.ff_gate = nn.Linear(hidden_size, hidden_size)

    def forward(self, hidden_states, attention_mask):
        attn_out = self.attention(self.attn_norm(hidden_states), attention_mask)
        hidden_states = hidden_states + torch.sigmoid(self.attn_gate(hidden_states)) * attn_out
        ff_out = self.feed_forward(self.ff_norm(hidden_states))
        hidden_states = hidden_states + torch.sigmoid(self.ff_gate(hidden_states)) * ff_out
        return hidden_states


class LiGREncoder(nn.Module):
    """Drop-in replacement for RecBole's TransformerEncoder call signature."""

    def __init__(self, n_layers, n_heads, hidden_size, ff_multiplier,
                 hidden_dropout_prob, attn_dropout_prob, layer_norm_eps):
        super().__init__()
        self.layer = nn.ModuleList([
            LiGRLayer(n_heads, hidden_size, ff_multiplier, hidden_dropout_prob,
                      attn_dropout_prob, layer_norm_eps)
            for _ in range(n_layers)
        ])

    def forward(self, hidden_states, attention_mask, output_all_encoded_layers=True):
        all_layers = []
        for layer in self.layer:
            hidden_states = layer(hidden_states, attention_mask)
            if output_all_encoded_layers:
                all_layers.append(hidden_states)
        if not output_all_encoded_layers:
            all_layers.append(hidden_states)
        return all_layers


class ESASRec(SASRec):
    """SASRec with LiGR blocks and sampled softmax loss.

    Everything outside the encoder and the loss is inherited from RecBole's SASRec,
    so embeddings, positional encoding, sequence readout and full_sort_predict stay
    identical to the baseline arm.
    """

    # RecBole otherwise infers the batch layout from loss_type, which it only knows
    # for CE and BPR. Sequences with one positive target are pointwise inputs.
    input_type = InputType.POINTWISE

    def __init__(self, config, dataset):
        if config["loss_type"] != "SS":
            raise ValueError("eSASRec is defined with the sampled softmax loss")
        # RecBole's SASRec constructor accepts only BPR and CE, so the parent runs
        # under CE and the sampled softmax is installed here.
        config["loss_type"] = "CE"
        try:
            super().__init__(config, dataset)
        finally:
            config["loss_type"] = "SS"
        self.loss_type = "SS"
        self.ff_multiplier = config["ff_emb_mult"]
        self.n_negatives = config["n_negatives"]
        self.trm_encoder = LiGREncoder(
            n_layers=self.n_layers,
            n_heads=self.n_heads,
            hidden_size=self.hidden_size,
            ff_multiplier=self.ff_multiplier,
            hidden_dropout_prob=self.hidden_dropout_prob,
            attn_dropout_prob=self.attn_dropout_prob,
            layer_norm_eps=self.layer_norm_eps,
        )
        self.loss_fct = nn.CrossEntropyLoss()
        self.apply(self._init_weights)

    def calculate_loss(self, interaction):
        seq_output = self.forward(interaction[self.ITEM_SEQ], interaction[self.ITEM_SEQ_LEN])
        pos_items = interaction[self.POS_ITEM_ID]
        # Uniform negatives over the real catalogue; token 0 is padding. A uniform
        # proposal adds the same log q to every candidate, so no logQ correction.
        negatives = torch.randint(1, self.n_items, (pos_items.size(0), self.n_negatives),
                                  device=pos_items.device)
        candidates = torch.cat([pos_items.unsqueeze(1), negatives], dim=1)
        candidate_emb = self.item_embedding(candidates)
        logits = torch.einsum("bh,bch->bc", seq_output, candidate_emb)
        target = torch.zeros(pos_items.size(0), dtype=torch.long, device=pos_items.device)
        return self.loss_fct(logits, target)
