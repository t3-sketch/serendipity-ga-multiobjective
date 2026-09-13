"""Validate a Graph-Rec research-export 0.1 bundle. Stdlib only. No network."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "0.1"
MANIFEST_KEYS = {
    "schema_version", "bundle_id", "created_at", "purpose", "data_kind",
    "producer", "provider", "dataset", "case_count", "cases_sha256",
}
PRODUCER_KEYS = {"project", "commit", "dirty", "source_files"}
PROVIDER_KEYS = {"id", "config"}
DATASET_KEYS = {"id", "sha256"}
CASE_KEYS = {
    "case_id", "participant_id", "session_id", "requested_at", "input",
    "recommendations", "presentation",
}
INPUT_KEYS = {"current_track_id", "session_path", "explored_track_ids", "limit"}
REC_KEYS = {"rank", "track"}
TRACK_KEYS = {"id", "title", "artists"}
ARTIST_KEYS = {"name"}
ISO_Z = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?Z$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SOURCE_PATH = re.compile(r"^(?!\.)(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+$")


class BundleError(Exception):
    def __init__(self, file: str, field: str, message: str, line: int | None = None):
        where = file if line is None else f"{file}:{line}"
        at = f" field={field}" if field else ""
        super().__init__(f"{where}{at} {message}")


def _fail(file: str, field: str, message: str, line: int | None = None) -> None:
    raise BundleError(file, field, message, line)


def _object_pairs(pairs: list[tuple[str, object]]) -> dict:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate JSON key")
    return dict(pairs)


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON value {value}")


def load_object(text: str, file: str, line: int | None = None) -> dict:
    if text.startswith("\ufeff"):
        _fail(file, "", "BOM is not allowed", line)
    try:
        value = json.loads(text, object_pairs_hook=_object_pairs, parse_constant=_reject_constant)
    except ValueError as error:
        _fail(file, "", str(error), line)
    if not isinstance(value, dict):
        _fail(file, "", "root must be an object", line)
    return value


def _keys(value: dict, expected: set[str], file: str, field: str, line: int | None = None) -> None:
    if set(value) != expected:
        _fail(file, field, "unexpected or missing keys", line)


def _text(value: object, file: str, field: str, line: int | None = None) -> str:
    if not isinstance(value, str) or value == "":
        _fail(file, field, "must be a non-empty string", line)
    return value


def _days_in_month(year: int, month: int) -> int:
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    return (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[month]


def is_iso_z(value: object) -> bool:
    if not isinstance(value, str):
        return False
    match = ISO_Z.fullmatch(value)
    if match is None:
        return False
    year, month, day, hour, minute, second = (int(part) for part in match.groups())
    if not 1 <= month <= 12:
        return False
    if not 1 <= day <= _days_in_month(year, month):
        return False
    return 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59


def validate_manifest(raw: dict) -> dict:
    file = "manifest.json"
    _keys(raw, MANIFEST_KEYS, file, "")
    if raw["schema_version"] != SCHEMA_VERSION:
        _fail(file, "schema_version", "unsupported schema")
    _text(raw["bundle_id"], file, "bundle_id")
    if not is_iso_z(raw["created_at"]):
        _fail(file, "created_at", "must be UTC ISO-8601 ending with Z")
    if raw["purpose"] != "integration_test":
        _fail(file, "purpose", "must be integration_test")
    if raw["data_kind"] != "synthetic":
        _fail(file, "data_kind", "must be synthetic")
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
        if ".." in path.split("/") or path.startswith("/") or not SOURCE_PATH.match(path):
            _fail(file, "producer.source_files", f"illegal path {path}")
        if not isinstance(digest, str) or not SHA256.match(digest):
            _fail(file, "producer.source_files", f"hash for {path}")
    provider = raw["provider"]
    if not isinstance(provider, dict):
        _fail(file, "provider", "must be an object")
    _keys(provider, PROVIDER_KEYS, file, "provider")
    if provider["id"] != "mock-recommendation":
        _fail(file, "provider.id", "must be mock-recommendation")
    if provider["config"] != {}:
        _fail(file, "provider.config", "must be empty object")
    dataset = raw["dataset"]
    if not isinstance(dataset, dict):
        _fail(file, "dataset", "must be an object")
    _keys(dataset, DATASET_KEYS, file, "dataset")
    if dataset["id"] != "sonder-fictional-catalog":
        _fail(file, "dataset.id", "must be sonder-fictional-catalog")
    if not isinstance(dataset["sha256"], str) or not SHA256.match(dataset["sha256"]):
        _fail(file, "dataset.sha256", "must be sha256")
    if type(raw["case_count"]) is not int or isinstance(raw["case_count"], bool) or raw["case_count"] < 1:
        _fail(file, "case_count", "must be a positive integer")
    if not isinstance(raw["cases_sha256"], str) or not SHA256.match(raw["cases_sha256"]):
        _fail(file, "cases_sha256", "must be sha256")
    return raw


def validate_case(raw: dict, line: int) -> dict:
    file = "cases.jsonl"
    _keys(raw, CASE_KEYS, file, "", line)
    _text(raw["case_id"], file, "case_id", line)
    if raw["participant_id"] is not None:
        _fail(file, "participant_id", "must be null", line)
    _text(raw["session_id"], file, "session_id", line)
    if not is_iso_z(raw["requested_at"]):
        _fail(file, "requested_at", "must be UTC ISO-8601 ending with Z", line)
    inp = raw["input"]
    if not isinstance(inp, dict):
        _fail(file, "input", "must be an object", line)
    if "human_rating" in inp or "human_ratings" in inp:
        _fail(file, "input.human_rating", "ratings must not be mixed into input", line)
    if inp.get("playlistContext") not in (None, ""):
        if "playlistContext" in inp:
            _fail(file, "input.playlistContext", "unsupported", line)
    _keys(inp, INPUT_KEYS, file, "input", line)
    current = _text(inp["current_track_id"], file, "input.current_track_id", line)
    path = inp["session_path"]
    if not isinstance(path, list) or not path or not all(isinstance(item, str) and item for item in path):
        _fail(file, "input.session_path", "must be a non-empty string array", line)
    if path[-1] != current:
        _fail(file, "input.session_path", "must end with current_track_id", line)
    explored = inp["explored_track_ids"]
    if not isinstance(explored, list) or not all(isinstance(item, str) and item for item in explored):
        _fail(file, "input.explored_track_ids", "must be a string array", line)
    if len(set(explored)) != len(explored):
        _fail(file, "input.explored_track_ids", "must be unique", line)
    for track_id in [current, *path]:
        if track_id not in explored:
            _fail(file, "input.explored_track_ids", f"missing {track_id}", line)
    limit = inp["limit"]
    if isinstance(limit, bool) or type(limit) is not int or not 1 <= limit <= 100:
        _fail(file, "input.limit", "must be an integer 1..100", line)
    recs = raw["recommendations"]
    if not isinstance(recs, list) or not 1 <= len(recs) <= limit:
        _fail(file, "recommendations", "must have 1..limit items", line)
    seen = set()
    for index, item in enumerate(recs):
        if not isinstance(item, dict):
            _fail(file, "recommendations", "each item must be an object", line)
        _keys(item, REC_KEYS, file, "recommendations", line)
        if type(item["rank"]) is not int or isinstance(item["rank"], bool) or item["rank"] != index + 1:
            _fail(file, "rank", "must be consecutive integers starting at 1", line)
        track = item["track"]
        if not isinstance(track, dict):
            _fail(file, "track", "must be an object", line)
        _keys(track, TRACK_KEYS, file, "track", line)
        track_id = _text(track["id"], file, "track.id", line)
        _text(track["title"], file, "track.title", line)
        if track_id in explored:
            _fail(file, "track.id", "already explored", line)
        if track_id in seen:
            _fail(file, "track.id", "duplicate in case", line)
        seen.add(track_id)
        artists = track["artists"]
        if not isinstance(artists, list) or not artists:
            _fail(file, "track.artists", "need one or more artists", line)
        for artist in artists:
            if not isinstance(artist, dict):
                _fail(file, "track.artists", "each artist must be an object", line)
            _keys(artist, ARTIST_KEYS, file, "track.artists", line)
            _text(artist["name"], file, "track.artists", line)
    presentation = raw["presentation"]
    if not isinstance(presentation, dict) or set(presentation) != {"mode"}:
        _fail(file, "presentation", "must be {mode}", line)
    if presentation["mode"] != "not_presented":
        _fail(file, "presentation.mode", "must be not_presented", line)
    return raw


def load_cases(text: str) -> list[dict]:
    file = "cases.jsonl"
    if text.startswith("\ufeff"):
        _fail(file, "", "BOM is not allowed")
    if not text.endswith("\n"):
        _fail(file, "", "missing trailing newline")
    lines = text[:-1].split("\n")
    if any(line == "" for line in lines):
        _fail(file, "", "empty line")
    cases = [validate_case(load_object(line, file, index + 1), index + 1) for index, line in enumerate(lines)]
    ids = [item["case_id"] for item in cases]
    if len(ids) != len(set(ids)):
        _fail(file, "case_id", "duplicate case_id")
    return cases


def validate_bundle(directory: Path) -> tuple[dict, list[dict]]:
    if not directory.is_dir():
        _fail(str(directory), "", "bundle directory does not exist")
    manifest_path = directory / "manifest.json"
    cases_path = directory / "cases.jsonl"
    ratings = directory / "human-ratings.jsonl"
    predictions = directory / "llm-predictions.jsonl"
    for path in (manifest_path, cases_path, ratings, predictions):
        if not path.is_file():
            _fail(path.name, "", "missing file")
    if ratings.stat().st_size != 0:
        _fail("human-ratings.jsonl", "", "version 0.1 requires an empty file")
    if predictions.stat().st_size != 0:
        _fail("llm-predictions.jsonl", "", "version 0.1 requires an empty file")
    manifest = validate_manifest(load_object(manifest_path.read_text(encoding="utf-8"), "manifest.json"))
    cases_bytes = cases_path.read_bytes()
    digest = hashlib.sha256(cases_bytes).hexdigest()
    if digest != manifest["cases_sha256"]:
        _fail("manifest.json", "cases_sha256", "does not match cases.jsonl bytes")
    cases = load_cases(cases_bytes.decode("utf-8"))
    if len(cases) != manifest["case_count"]:
        _fail("manifest.json", "case_count", "does not match cases.jsonl rows")
    return manifest, cases


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python -B studies/music-evaluator/validate_export.py <bundle-dir-or-bundle.json>", file=sys.stderr)
        return 2
    target = Path(argv[1])
    try:
        if target.is_file():
            from validate_export_v02 import validate_bundle_v2
            manifest, cases, events = validate_bundle_v2(target)
            recs = sum(len(item["recommendations"]) for item in cases)
            print(
                f"schema_version={manifest['schema_version']} case_count={len(cases)} "
                f"recommendation_count={recs} event_count={len(events)}"
            )
            return 0
        manifest, cases = validate_bundle(target)
    except BundleError as error:
        print(error, file=sys.stderr)
        return 1
    recs = sum(len(item["recommendations"]) for item in cases)
    print(f"schema_version={manifest['schema_version']} case_count={len(cases)} recommendation_count={recs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
