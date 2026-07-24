"""Extract the local, source-backed fixtures for ALL-00-01.

This script is intentionally limited to fixture extraction and inventory. It
does not declare historical INPUT/OUTPUT files to be golden results and it
does not contact a network service.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from xml.etree import ElementTree

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = WORKSPACE_ROOT / "Single-Floating-Body-Solvers"
SOURCE_ROOT = WORKSPACE_ROOT / "单浮体求解器集成包"
SOURCE_PROJECT = (
    SOURCE_ROOT
    / "reference"
    / "example-project"
    / "single-floater-ten-riser.sopro"
)
DEST_ROOT = REPOSITORY_ROOT / "tests" / "fixtures" / "golden"


def sha256_bytes(chunks: Iterable[bytes]) -> str:
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk)
    return digest.hexdigest().upper()


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return sha256_bytes(iter(lambda: stream.read(1024 * 1024), b""))


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def direct_text(element: ElementTree.Element, name: str) -> str:
    for child in element:
        if local_name(child.tag) == name and child.text:
            return child.text.strip()
    return ""


def parse_packet_entries(xml_bytes: bytes) -> list[dict[str, Any]]:
    root = ElementTree.fromstring(xml_bytes)
    packets: list[dict[str, Any]] = []

    def visit(element: ElementTree.Element, parent_id: str | None) -> None:
        for child in element:
            if local_name(child.tag) == "PACKET":
                packet_id = direct_text(child, "UUID")
                packet_type = direct_text(child, "Type")
                entry: dict[str, Any] = {
                    "uuid": packet_id,
                    "name": direct_text(child, "Name"),
                    "type": (
                        int(packet_type)
                        if packet_type.isdigit()
                        else packet_type
                    ),
                    "path": direct_text(child, "Path"),
                    "parent_uuid": parent_id,
                    "children": [],
                }
                packets.append(entry)
                visit(child, packet_id or None)
            else:
                visit(child, parent_id)

    visit(root, None)
    by_parent: dict[str, list[str]] = {}
    for packet in packets:
        parent_id = packet["parent_uuid"]
        if parent_id:
            by_parent.setdefault(parent_id, []).append(packet["uuid"])
    for packet in packets:
        packet["children"] = by_parent.get(packet["uuid"], [])
    return packets


def archive_inventory(archive: zipfile.ZipFile) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for info in archive.infolist():
        item: dict[str, Any] = {
            "path": info.filename,
            "is_dir": info.is_dir(),
            "size": info.file_size,
            "compressed_size": info.compress_size,
        }
        if not info.is_dir():
            with archive.open(info, "r") as stream:
                item["sha256"] = sha256_bytes(
                    iter(lambda: stream.read(1024 * 1024), b""),
                )
        inventory.append(item)
    return inventory


def input_relative_path(name: str) -> PurePosixPath | None:
    parts = PurePosixPath(name).parts
    try:
        input_index = parts.index("INPUT")
    except ValueError:
        return None
    relative = PurePosixPath(*parts[input_index + 1 :])
    if not relative.parts:
        return None
    return relative


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    if not SOURCE_PROJECT.is_file():
        raise FileNotFoundError(f"source project not found: {SOURCE_PROJECT}")

    projects_dir = DEST_ROOT / "projects"
    historical_input_dir = (
        DEST_ROOT / "expected_input" / "historical_reference"
    )
    expected_project_dir = DEST_ROOT / "expected_project"
    projects_dir.mkdir(parents=True, exist_ok=True)
    historical_input_dir.mkdir(parents=True, exist_ok=True)
    expected_project_dir.mkdir(parents=True, exist_ok=True)

    copied_project = projects_dir / SOURCE_PROJECT.name
    shutil.copy2(SOURCE_PROJECT, copied_project)

    with zipfile.ZipFile(SOURCE_PROJECT, "r") as archive:
        manifest_names = sorted(
            name
            for name in archive.namelist()
            if name.lower().endswith(".sopro") and not name.endswith("/")
        )
        if not manifest_names:
            raise ValueError("no manifest .sopro entry found")
        manifest_name = manifest_names[0]
        manifest_bytes = archive.read(manifest_name)
        packets = parse_packet_entries(manifest_bytes)
        inventory = archive_inventory(archive)

        extracted_inputs: list[str] = []
        for info in archive.infolist():
            relative = input_relative_path(info.filename)
            if relative is None or info.is_dir():
                continue
            destination = historical_input_dir.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with (
                archive.open(info, "r") as source,
                destination.open("wb") as target,
            ):
                shutil.copyfileobj(source, target)
            extracted_inputs.append(str(relative).replace("\\", "/"))

    type_counts = Counter(str(packet["type"]) for packet in packets)
    write_json(expected_project_dir / "archive_entries.json", inventory)
    write_json(expected_project_dir / "manifest_packets.json", packets)
    write_json(
        expected_project_dir / "manifest_type_summary.json",
        {
            "packet_count": len(packets),
            "type_counts": dict(sorted(type_counts.items())),
        },
    )
    write_json(
        expected_project_dir / "resource_hashes.json",
        {
            item["path"]: item["sha256"]
            for item in inventory
            if not item["is_dir"]
        },
    )
    write_json(
        DEST_ROOT / "source_hashes.json",
        {
            "source_project": {
                "path": str(SOURCE_PROJECT.relative_to(WORKSPACE_ROOT)),
                "sha256": sha256_file(SOURCE_PROJECT),
            },
            "copied_project": {
                "path": str(copied_project.relative_to(REPOSITORY_ROOT)),
                "sha256": sha256_file(copied_project),
            },
        },
    )
    write_json(
        DEST_ROOT / "catalog.json",
        {
            "mode": "LOCAL_ONLY",
            "scope": "ALL-00-01 fixture extraction only",
            "manifest_entry": manifest_name,
            "assets": [
                {
                    "id": "G-PROJECT-01",
                    "path": str(copied_project.relative_to(REPOSITORY_ROOT)),
                    "status": "extracted_source",
                    "allowed_use": [
                        "manifest",
                        "project_structure",
                        "historical_input_reference",
                    ],
                    "limitations": [
                        "OUTPUT is not a complete static/dynamic golden result"
                    ],
                },
                {
                    "id": "G-HISTORICAL-INPUT-01",
                    "path": str(
                        historical_input_dir.relative_to(REPOSITORY_ROOT)
                    ),
                    "status": "historical_reference_only",
                    "files": sorted(extracted_inputs),
                    "allowed_use": [
                        "format_inventory",
                        "compatibility_comparison",
                    ],
                    "limitations": [
                        "not declared as model-generated golden INPUT"
                    ],
                },
                {
                    "id": "G-ENV-XML-01",
                    "path": (
                        "tests/fixtures/environment_project/"
                        "case001/环境数据.4048"
                    ),
                    "status": "existing_local_fixture",
                    "allowed_use": ["environment_codec_tests"],
                },
            ],
            "missing_for_full_m0": [
                "G-INPUT-EXPECTED-01",
                "G-RESULT-STATIC-01",
                "G-RESULT-DYNAMIC-01",
                "G-HYDRO-SLICE-01",
                "G-UI-RESULT-01",
            ],
        },
    )


if __name__ == "__main__":
    main()
