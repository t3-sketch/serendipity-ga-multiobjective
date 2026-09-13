"""Acceptance checks for research-export 0.1. Uses temp fixtures, not Graph-Rec paths."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validate_export import (
    BundleError,
    is_iso_z,
    load_cases,
    load_object,
    validate_bundle,
    validate_case,
    validate_manifest,
)

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE / "validate_export.py"

CASE = {
    "case_id": "case-001",
    "participant_id": None,
    "session_id": "synthetic-session-001",
    "requested_at": "2026-09-13T00:00:00Z",
    "input": {
        "current_track_id": "sonder-1",
        "session_path": ["sonder-1"],
        "explored_track_ids": ["sonder-1"],
        "limit": 1,
    },
    "recommendations": [
        {"rank": 1, "track": {"id": "sonder-2", "title": "Glass Cities", "artists": [{"name": "Luma"}]}},
    ],
    "presentation": {"mode": "not_presented"},
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _manifest(cases_bytes: bytes, count: int) -> dict:
    return {
        "schema_version": "0.1",
        "bundle_id": "sonder-mock-integration-001",
        "created_at": "2026-09-13T00:00:00Z",
        "purpose": "integration_test",
        "data_kind": "synthetic",
        "producer": {
            "project": "Graph-Rec",
            "commit": None,
            "dirty": None,
            "source_files": {"package.json": "a" * 64},
        },
        "provider": {"id": "mock-recommendation", "config": {}},
        "dataset": {"id": "sonder-fictional-catalog", "sha256": "b" * 64},
        "case_count": count,
        "cases_sha256": _sha(cases_bytes),
    }


def _write_bundle(directory: Path, cases: list[dict], manifest: dict | None = None) -> None:
    payload = "".join(json.dumps(item, separators=(",", ":")) + "\n" for item in cases)
    cases_bytes = payload.encode("utf-8")
    body = manifest or _manifest(cases_bytes, len(cases))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "cases.jsonl").write_bytes(cases_bytes)
    (directory / "manifest.json").write_text(json.dumps(body) + "\n", encoding="utf-8")
    (directory / "human-ratings.jsonl").write_bytes(b"")
    (directory / "llm-predictions.jsonl").write_bytes(b"")


class ValidateExportTests(unittest.TestCase):
    def test_valid_synthetic_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write_bundle(root, [CASE])
            manifest, cases = validate_bundle(root)
            self.assertEqual(manifest["schema_version"], "0.1")
            self.assertEqual(len(cases), 1)
            self.assertEqual(cases[0]["recommendations"][0]["track"]["title"], "Glass Cities")

    def test_cli_success_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write_bundle(root, [CASE])
            completed = subprocess.run(
                [sys.executable, "-B", str(VALIDATOR), str(root)],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("schema_version=0.1", completed.stdout)
            self.assertIn("case_count=1", completed.stdout)
            self.assertIn("recommendation_count=1", completed.stdout)

    def test_unknown_schema_and_keys(self) -> None:
        bad = _manifest(b"x\n", 1)
        bad["schema_version"] = "0.2"
        with self.assertRaises(BundleError) as error:
            validate_manifest(bad)
        self.assertIn("schema_version", str(error.exception))
        extra = _manifest(b"x\n", 1)
        extra["extra"] = True
        with self.assertRaises(BundleError):
            validate_manifest(extra)
        with self.assertRaises(BundleError):
            validate_case({**CASE, "participant_id": "p1"}, 1)
        mixed = {**CASE, "input": {**CASE["input"], "human_rating": 5}}
        with self.assertRaises(BundleError) as error:
            validate_case(mixed, 1)
        self.assertIn("human_rating", str(error.exception))
        shown = {**CASE, "presentation": {"mode": "shown"}}
        with self.assertRaises(BundleError) as error:
            validate_case(shown, 1)
        self.assertIn("presentation.mode", str(error.exception))

    def test_rank_and_duplicate_track_and_explored(self) -> None:
        with self.assertRaises(BundleError):
            validate_case({**CASE, "recommendations": [{"rank": 2, "track": CASE["recommendations"][0]["track"]}]}, 1)
        dup = {
            **CASE,
            "input": {**CASE["input"], "limit": 2},
            "recommendations": [
                CASE["recommendations"][0],
                {"rank": 2, "track": CASE["recommendations"][0]["track"]},
            ],
        }
        with self.assertRaises(BundleError) as error:
            validate_case(dup, 1)
        self.assertIn("duplicate", str(error.exception))
        explored = {
            **CASE,
            "recommendations": [{"rank": 1, "track": {**CASE["recommendations"][0]["track"], "id": "sonder-1"}}],
        }
        with self.assertRaises(BundleError) as error:
            validate_case(explored, 1)
        self.assertIn("already explored", str(error.exception))

    def test_nan_and_duplicate_json_key(self) -> None:
        with self.assertRaises(BundleError):
            load_object('{"limit": NaN}', "cases.jsonl", 1)
        with self.assertRaises(BundleError) as error:
            load_object('{"case_id":"a","case_id":"b"}', "cases.jsonl", 1)
        self.assertIn("duplicate JSON key", str(error.exception))
        with self.assertRaises(BundleError) as error:
            load_object(r'{"case_id":"first","\u0063ase_id":"second"}', "cases.jsonl", 1)
        self.assertIn("duplicate JSON key", str(error.exception))
        with self.assertRaises(BundleError) as error:
            load_object(r'{"case_id":"first","case_\u0069d":"second"}', "cases.jsonl", 1)
        self.assertIn("duplicate JSON key", str(error.exception))

    def test_real_utc_timestamps(self) -> None:
        for stamp in (
            "2024-02-29T23:59:59Z",
            "2000-02-29T00:00:00Z",
            "2026-01-31T00:00:00Z",
            "2026-04-30T12:00:00.123Z",
            "2026-09-13T00:00:00Z",
        ):
            self.assertTrue(is_iso_z(stamp), stamp)
        for stamp in (
            "2026-99-99T99:99:99Z",
            "2025-02-29T00:00:00Z",
            "1900-02-29T00:00:00Z",
            "2026-04-31T00:00:00Z",
            "2026-02-30T00:00:00Z",
            "2026-13-01T00:00:00Z",
            "2026-00-01T00:00:00Z",
            "2026-01-00T00:00:00Z",
            "2026-09-13T24:00:00Z",
            "2026-09-13T00:60:00Z",
            "2026-09-13T00:00:60Z",
        ):
            self.assertFalse(is_iso_z(stamp), stamp)
            with self.assertRaises(BundleError) as error:
                validate_manifest({**_manifest(b"x\n", 1), "created_at": stamp})
            self.assertIn("created_at", str(error.exception))
            with self.assertRaises(BundleError) as error:
                validate_case({**CASE, "requested_at": stamp}, 1)
            self.assertIn("requested_at", str(error.exception))

    def test_hash_and_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write_bundle(root, [CASE])
            cases_path = root / "cases.jsonl"
            cases_path.write_bytes(cases_path.read_bytes() + b" ")
            with self.assertRaises(BundleError) as error:
                validate_bundle(root)
            self.assertIn("cases_sha256", str(error.exception))
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            payload = (json.dumps(CASE, separators=(",", ":")) + "\n").encode()
            _write_bundle(root, [CASE], _manifest(payload, 2))
            with self.assertRaises(BundleError) as error:
                validate_bundle(root)
            self.assertIn("case_count", str(error.exception))

    def test_structure_fails_after_hash_rewrite(self) -> None:
        broken = {**CASE, "recommendations": []}
        payload = (json.dumps(broken, separators=(",", ":")) + "\n").encode()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write_bundle(root, [broken], _manifest(payload, 1))
            with self.assertRaises(BundleError) as error:
                validate_bundle(root)
            self.assertIn("recommendations", str(error.exception))

    def test_nonempty_rating_files_and_cli_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write_bundle(root, [CASE])
            (root / "human-ratings.jsonl").write_text("{}\n", encoding="utf-8")
            with self.assertRaises(BundleError):
                validate_bundle(root)
            completed = subprocess.run(
                [sys.executable, "-B", str(VALIDATOR), str(root)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("human-ratings.jsonl", completed.stderr)

    def test_duplicate_case_id(self) -> None:
        text = json.dumps(CASE, separators=(",", ":")) + "\n" + json.dumps(CASE, separators=(",", ":")) + "\n"
        with self.assertRaises(BundleError) as error:
            load_cases(text)
        self.assertIn("case_id", str(error.exception))


if __name__ == "__main__":
    unittest.main()
