"""Integrity checks for the source-backed ALL-00-01 fixture extraction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "golden"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def test_all_00_01_catalog_is_source_backed() -> None:
    catalog = json.loads(
        (_FIXTURE_ROOT / "catalog.json").read_text(encoding="utf-8"),
    )
    assert catalog["mode"] == "LOCAL_ONLY"
    assert catalog["scope"] == "ALL-00-01 fixture extraction only"
    assert "G-INPUT-EXPECTED-01" in catalog["missing_for_full_m0"]
    assert "G-RESULT-DYNAMIC-01" in catalog["missing_for_full_m0"]


def test_sopro_inventory_matches_extracted_manifest() -> None:
    summary = json.loads(
        (
            _FIXTURE_ROOT / "expected_project" / "manifest_type_summary.json"
        ).read_text(
            encoding="utf-8",
        ),
    )
    archive_entries = json.loads(
        (
            _FIXTURE_ROOT / "expected_project" / "archive_entries.json"
        ).read_text(encoding="utf-8"),
    )
    packets = json.loads(
        (
            _FIXTURE_ROOT / "expected_project" / "manifest_packets.json"
        ).read_text(encoding="utf-8"),
    )
    assert len(archive_entries) == 514
    assert summary["packet_count"] == 173
    assert len(packets) == 173
    assert summary["type_counts"]["4042"] == 52
    assert summary["type_counts"]["4071"] == 26


def test_copied_sopro_hash_is_recorded() -> None:
    hashes = json.loads(
        (_FIXTURE_ROOT / "source_hashes.json").read_text(encoding="utf-8"),
    )
    copied_path = _FIXTURE_ROOT.parents[2] / hashes["copied_project"]["path"]
    assert copied_path.is_file()
    assert _sha256(copied_path) == hashes["copied_project"]["sha256"]


def test_historical_input_is_not_declared_as_golden_input() -> None:
    catalog = json.loads(
        (_FIXTURE_ROOT / "catalog.json").read_text(encoding="utf-8"),
    )
    historical = next(
        asset
        for asset in catalog["assets"]
        if asset["id"] == "G-HISTORICAL-INPUT-01"
    )
    assert historical["status"] == "historical_reference_only"
    assert historical["limitations"] == [
        "not declared as model-generated golden INPUT",
    ]
