"""Validate a Graph-Rec research-export 0.2 bundle.json. Stdlib only."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from validate_export import (
    ARTIST_KEYS,
    COMMIT,
    DATASET_KEYS,
    INPUT_KEYS,
    PRODUCER_KEYS,
    PROVIDER_KEYS,
    SHA256,
    SOURCE_PATH,
    BundleError,
    _fail,
    _keys,
    _text,
    is_iso_z,
    load_object,
)

SCHEMA_VERSION = "0.2"
BUNDLE_KEYS = {"manifest", "catalog", "cases", "events", "human_ratings", "llm_predictions"}
MANIFEST_KEYS = {
    "schema_version", "bundle_id", "created_at", "purpose", "data_kind", "session_id",
    "producer", "provider", "dataset", "case_count", "event_count", "cases_sha256", "events_sha256",
}
CATALOG_KEYS = {
    "id", "title", "artists", "genre_ids", "genre_names", "source_url",
    "license_url", "audio_sha256", "preview_duration_ms",
}
CASE_KEYS = {"case_id", "participant_id", "session_id", "requested_at", "input", "recommendations", "presentation"}
REC_KEYS = {"rank", "track_id", "shared_genre_count", "union_genre_count"}
EVENT_KEYS = {"event_id", "session_id", "case_id", "track_id", "occurred_at", "type", "value"}
EVENT_TYPES = {
    "node_impression", "node_expand", "preview_start", "preview_pause", "preview_complete", "like", "save",
}
TRACK_ID = re.compile(r"^fma-\d{6}$")
HTTPS = re.compile(r"^https://[^ ]+$")
LICENSE_ALLOW = {
    "https://creativecommons.org/licenses/by/3.0/",
    "https://creativecommons.org/licenses/by/3.0/us/",
}


def canonical_json(value: object) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        raise ValueError("floats are not permitted in canonical JSON")
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ",".join(canonical_json(item) for item in value) + "]"
    if isinstance(value, dict):
        keys = sorted(value)
        return "{" + ",".join(json.dumps(key, ensure_ascii=False) + ":" + canonical_json(value[key]) for key in keys) + "}"
    raise ValueError("unsupported canonical JSON value")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _instant(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def _fma_num(track_id: str) -> int:
    return int(track_id[4:])


def rank_jaccard(catalog: list[dict], seed_id: str, excluded: set[str], limit: int) -> list[dict]:
    seed = next(item for item in catalog if item["id"] == seed_id)
    seed_genres = set(seed["genre_ids"])
    eligible = []
    for record in catalog:
        if record["id"] in excluded or record["id"] == seed_id:
            continue
        genres = set(record["genre_ids"])
        shared = len(seed_genres & genres)
        union = len(seed_genres | genres)
        eligible.append({"id": record["id"], "shared": shared, "union": union})
    def better(left: dict, right: dict) -> bool:
        cross = left["shared"] * right["union"] - right["shared"] * left["union"]
        if cross != 0:
            return cross > 0
        return _fma_num(left["id"]) < _fma_num(right["id"])
    ordered: list[dict] = []
    remaining = eligible[:]
    while remaining:
        best = remaining[0]
        for item in remaining[1:]:
            if better(item, best):
                best = item
        ordered.append(best)
        remaining.remove(best)
    return ordered[:limit]


def validate_manifest_v2(raw: dict) -> dict:
    file = "bundle.json"
    _keys(raw, MANIFEST_KEYS, file, "manifest")
    if raw["schema_version"] != SCHEMA_VERSION:
        _fail(file, "schema_version", "unsupported schema")
    _text(raw["bundle_id"], file, "bundle_id")
    if not is_iso_z(raw["created_at"]):
        _fail(file, "created_at", "must be a real UTC ISO-8601 timestamp ending with Z")
    if raw["purpose"] != "engineering_demo":
        _fail(file, "purpose", "must be engineering_demo")
    if raw["data_kind"] != "real_catalog":
        _fail(file, "data_kind", "must be real_catalog")
    _text(raw["session_id"], file, "session_id")
    producer = raw["producer"]
    if not isinstance(producer, dict):
        _fail(file, "producer", "must be an object")
    _keys(producer, PRODUCER_KEYS, file, "producer")
    if producer["project"] != "Graph-Rec":
        _fail(file, "producer.project", "must be Graph-Rec")
    commit = producer["commit"]
    if commit is not None and not (isinstance(commit, str) and COMMIT.match(commit)):
        _fail(file, "producer.commit", "must be 40-char lowercase hex or null")
    if commit is None:
        if producer["dirty"] is not None:
            _fail(file, "producer.dirty", "must be null when commit is null")
    elif not isinstance(producer["dirty"], bool):
        _fail(file, "producer.dirty", "must be boolean when commit is set")
    source_files = producer["source_files"]
    if not isinstance(source_files, dict) or not source_files:
        _fail(file, "producer.source_files", "must be a non-empty object")
    for path, digest in source_files.items():
        if "provenance.generated" in path or ".." in path.split("/") or path.startswith("/") or not SOURCE_PATH.match(path):
            _fail(file, "producer.source_files", f"illegal path {path}")
        if not isinstance(digest, str) or not SHA256.match(digest):
            _fail(file, "producer.source_files", f"hash for {path}")
    provider = raw["provider"]
    if not isinstance(provider, dict):
        _fail(file, "provider", "must be an object")
    _keys(provider, PROVIDER_KEYS, file, "provider")
    if provider["id"] != "genre-jaccard-v1" or provider["config"] != {}:
        _fail(file, "provider", "must be genre-jaccard-v1 with empty config")
    dataset = raw["dataset"]
    if not isinstance(dataset, dict):
        _fail(file, "dataset", "must be an object")
    _keys(dataset, DATASET_KEYS, file, "dataset")
    if dataset["id"] != "sonder-fma-40-v1" or not isinstance(dataset["sha256"], str) or not SHA256.match(dataset["sha256"]):
        _fail(file, "dataset", "must be sonder-fma-40-v1 with sha256")
    if type(raw["case_count"]) is not int or isinstance(raw["case_count"], bool) or raw["case_count"] < 1:
        _fail(file, "case_count", "must be a positive integer")
    if type(raw["event_count"]) is not int or isinstance(raw["event_count"], bool) or raw["event_count"] < 0:
        _fail(file, "event_count", "must be a nonnegative integer")
    if not isinstance(raw["cases_sha256"], str) or not SHA256.match(raw["cases_sha256"]):
        _fail(file, "cases_sha256", "must be sha256")
    if not isinstance(raw["events_sha256"], str) or not SHA256.match(raw["events_sha256"]):
        _fail(file, "events_sha256", "must be sha256")
    return raw


def validate_catalog(raw: object) -> list[dict]:
    file = "bundle.json"
    if not isinstance(raw, list) or len(raw) != 40:
        _fail(file, "catalog", "must contain exactly 40 records")
    ids: set[str] = set()
    genre_map: dict[int, str] = {}
    previous = 0
    records = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            _fail(file, "catalog", f"each record must be an object at {index}")
        _keys(item, CATALOG_KEYS, file, "catalog")
        if not isinstance(item["id"], str) or not TRACK_ID.match(item["id"]):
            _fail(file, "catalog.id", "must be fma- plus six digits")
        numeric = _fma_num(item["id"])
        if numeric <= previous:
            _fail(file, "catalog", "must be sorted by numeric FMA ID")
        previous = numeric
        if item["id"] in ids:
            _fail(file, "catalog.id", "duplicate")
        ids.add(item["id"])
        _text(item["title"], file, "catalog.title")
        if not isinstance(item["artists"], list) or not item["artists"]:
            _fail(file, "catalog.artists", "need one or more artists")
        for artist in item["artists"]:
            if not isinstance(artist, dict):
                _fail(file, "catalog.artists", "each artist must be an object")
            _keys(artist, ARTIST_KEYS, file, "catalog.artists")
            _text(artist["name"], file, "catalog.artists")
        genre_ids = item["genre_ids"]
        genre_names = item["genre_names"]
        if (
            not isinstance(genre_ids, list) or not genre_ids
            or any(type(value) is not int or isinstance(value, bool) or value < 1 for value in genre_ids)
            or len(set(genre_ids)) != len(genre_ids)
            or any(genre_ids[i] <= genre_ids[i - 1] for i in range(1, len(genre_ids)))
        ):
            _fail(file, "catalog.genre_ids", "must be unique ascending positive integers")
        if not isinstance(genre_names, list) or len(genre_names) != len(genre_ids) or any(not isinstance(name, str) or not name for name in genre_names):
            _fail(file, "catalog.genre_names", "must match genre_ids")
        for genre_id, name in zip(genre_ids, genre_names):
            seen = genre_map.get(genre_id)
            if seen is not None and seen != name:
                _fail(file, "catalog.genre_names", f"id {genre_id} maps to more than one name")
            genre_map[genre_id] = name
        if not isinstance(item["source_url"], str) or not HTTPS.match(item["source_url"]):
            _fail(file, "catalog.source_url", "must be https")
        if item["license_url"] not in LICENSE_ALLOW:
            _fail(file, "catalog.license_url", "not on the audited allowlist")
        if not isinstance(item["audio_sha256"], str) or not SHA256.match(item["audio_sha256"]):
            _fail(file, "catalog.audio_sha256", "must be sha256")
        if type(item["preview_duration_ms"]) is not int or isinstance(item["preview_duration_ms"], bool) or item["preview_duration_ms"] < 1:
            _fail(file, "catalog.preview_duration_ms", "must be a positive integer")
        records.append(item)
    return records


def validate_case_v2(raw: dict, catalog: list[dict], created_at: str, session_id: str, line: int) -> dict:
    file = "bundle.json"
    catalog_ids = {item["id"] for item in catalog}
    _keys(raw, CASE_KEYS, file, "cases", line)
    _text(raw["case_id"], file, "case_id", line)
    if raw["participant_id"] is not None:
        _fail(file, "participant_id", "must be null", line)
    if raw["session_id"] != session_id:
        _fail(file, "session_id", "must match manifest.session_id", line)
    if not is_iso_z(raw["requested_at"]) or _instant(raw["requested_at"]) > _instant(created_at):
        _fail(file, "requested_at", "must be a real UTC timestamp <= created_at", line)
    inp = raw["input"]
    if not isinstance(inp, dict):
        _fail(file, "input", "must be an object", line)
    if "human_rating" in inp:
        _fail(file, "input.human_rating", "ratings must not be mixed into input", line)
    _keys(inp, INPUT_KEYS, file, "input", line)
    current = _text(inp["current_track_id"], file, "input.current_track_id", line)
    if current not in catalog_ids:
        _fail(file, "input.current_track_id", "unknown catalog id", line)
    path = inp["session_path"]
    if not isinstance(path, list) or not path or not all(isinstance(item, str) and item for item in path) or len(set(path)) != len(path):
        _fail(file, "input.session_path", "must be a unique non-empty string array", line)
    if path[-1] != current:
        _fail(file, "input.session_path", "must end with current_track_id", line)
    explored = inp["explored_track_ids"]
    if not isinstance(explored, list) or not all(isinstance(item, str) and item for item in explored) or len(set(explored)) != len(explored):
        _fail(file, "input.explored_track_ids", "must be unique strings", line)
    for track_id in [current, *path]:
        if track_id not in explored:
            _fail(file, "input.explored_track_ids", f"missing {track_id}", line)
    if any(track_id not in catalog_ids for track_id in explored):
        _fail(file, "input.explored_track_ids", "unknown catalog id", line)
    limit = inp["limit"]
    expected_limit = 8 if len(path) == 1 else 7
    if isinstance(limit, bool) or type(limit) is not int or limit != expected_limit:
        _fail(file, "input.limit", "must be 8 for a one-track seed path, otherwise 7", line)
    recs = raw["recommendations"]
    if not isinstance(recs, list) or len(recs) > limit:
        _fail(file, "recommendations", "must have 0..limit items", line)
    seen = set()
    for index, item in enumerate(recs):
        if not isinstance(item, dict):
            _fail(file, "recommendations", "each item must be an object", line)
        _keys(item, REC_KEYS, file, "recommendations", line)
        if type(item["rank"]) is not int or item["rank"] != index + 1:
            _fail(file, "rank", "must be consecutive integers starting at 1", line)
        track_id = _text(item["track_id"], file, "track_id", line)
        if track_id not in catalog_ids:
            _fail(file, "track_id", "unknown catalog id", line)
        if track_id in explored or track_id in seen:
            _fail(file, "track_id", "duplicate or already explored", line)
        seen.add(track_id)
        if type(item["union_genre_count"]) is not int or item["union_genre_count"] < 1:
            _fail(file, "union_genre_count", "must be a positive integer", line)
        if type(item["shared_genre_count"]) is not int or isinstance(item["shared_genre_count"], bool) or not 0 <= item["shared_genre_count"] <= item["union_genre_count"]:
            _fail(file, "shared_genre_count", "must be 0..union", line)
    expected = rank_jaccard(catalog, current, set(explored), limit)
    if len(expected) != len(recs):
        _fail(file, "recommendations", "omitted eligible candidates or extra rows", line)
    for item, want in zip(recs, expected):
        if item["track_id"] != want["id"] or item["shared_genre_count"] != want["shared"] or item["union_genre_count"] != want["union"]:
            _fail(file, "recommendations", "rank or counts do not match recomputed Jaccard order", line)
    presentation = raw["presentation"]
    if not isinstance(presentation, dict) or set(presentation) != {"mode"}:
        _fail(file, "presentation", "must be {mode}", line)
    if presentation["mode"] not in {"graph_committed", "not_presented"}:
        _fail(file, "presentation.mode", "unsupported", line)
    return raw


def validate_event_v2(raw: dict, cases: list[dict], created_at: str, session_id: str, line: int) -> dict:
    file = "bundle.json"
    _keys(raw, EVENT_KEYS, file, "events", line)
    _text(raw["event_id"], file, "event_id", line)
    if raw["session_id"] != session_id:
        _fail(file, "session_id", "must match manifest.session_id", line)
    associated = next((item for item in cases if item["case_id"] == raw["case_id"]), None)
    if associated is None:
        _fail(file, "case_id", "must reference an existing case", line)
    _text(raw["track_id"], file, "track_id", line)
    allowed = {associated["input"]["current_track_id"], *[item["track_id"] for item in associated["recommendations"]]}
    if raw["track_id"] not in allowed:
        _fail(file, "track_id", "must be the case seed or a recommendation", line)
    if not is_iso_z(raw["occurred_at"]) or not (_instant(associated["requested_at"]) <= _instant(raw["occurred_at"]) <= _instant(created_at)):
        _fail(file, "occurred_at", "must be requested_at..created_at", line)
    if raw["type"] not in EVENT_TYPES:
        _fail(file, "type", "unknown event type", line)
    if raw["type"] in {"like", "save"}:
        if not isinstance(raw["value"], bool):
            _fail(file, "value", "like/save value must be boolean", line)
    elif raw["value"] is not None:
        _fail(file, "value", "must be null for this event type", line)
    return raw


def validate_bundle_v2(path: Path) -> tuple[dict, list[dict], list[dict]]:
    raw = load_object(path.read_text(encoding="utf-8"), "bundle.json")
    _keys(raw, BUNDLE_KEYS, "bundle.json", "")
    if raw["human_ratings"] != []:
        _fail("bundle.json", "human_ratings", "version 0.2 requires an empty array")
    if raw["llm_predictions"] != []:
        _fail("bundle.json", "llm_predictions", "version 0.2 requires an empty array")
    manifest = validate_manifest_v2(raw["manifest"])
    catalog = validate_catalog(raw["catalog"])
    catalog_hash = canonical_sha256(catalog)
    if catalog_hash != manifest["dataset"]["sha256"]:
        _fail("bundle.json", "dataset.sha256", "does not match canonical catalog")
    cases_raw = raw["cases"]
    if not isinstance(cases_raw, list) or len(cases_raw) != manifest["case_count"]:
        _fail("bundle.json", "case_count", "does not match cases.length")
    cases = [validate_case_v2(item, catalog, manifest["created_at"], manifest["session_id"], index + 1) for index, item in enumerate(cases_raw)]
    if len({item["case_id"] for item in cases}) != len(cases):
        _fail("bundle.json", "case_id", "duplicate case_id")
    modes = {item["presentation"]["mode"] for item in cases}
    if len(modes) != 1:
        _fail("bundle.json", "presentation.mode", "do not mix modes in one bundle")
    events_raw = raw["events"]
    if not isinstance(events_raw, list) or len(events_raw) != manifest["event_count"]:
        _fail("bundle.json", "event_count", "does not match events.length")
    if "not_presented" in modes and events_raw:
        _fail("bundle.json", "events", "not_presented bundles require an empty events array")
    events = [validate_event_v2(item, cases, manifest["created_at"], manifest["session_id"], index + 1) for index, item in enumerate(events_raw)]
    if len({item["event_id"] for item in events}) != len(events):
        _fail("bundle.json", "event_id", "duplicate event_id")
    seen_impressions = set()
    for event in events:
        if event["type"] != "node_impression":
            continue
        key = (event["case_id"], event["track_id"])
        if key in seen_impressions:
            _fail("bundle.json", "events", "duplicate viewport impression")
        seen_impressions.add(key)
    if canonical_sha256(cases) != manifest["cases_sha256"]:
        _fail("bundle.json", "cases_sha256", "does not match canonical cases")
    if canonical_sha256(events) != manifest["events_sha256"]:
        _fail("bundle.json", "events_sha256", "does not match canonical events")
    return manifest, cases, events
