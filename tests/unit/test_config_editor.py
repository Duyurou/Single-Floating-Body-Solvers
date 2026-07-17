"""Tests for solver input config editing helpers."""

from pathlib import Path

from core.solver.config_editor import (
    patch_mooringline_for_dynamic,
    replace_config_value,
)


def test_replace_config_value_updates_existing_key() -> None:
    text = "sta_Type = 1\ncal_time = 500.0d0\n"

    updated = replace_config_value(text, "sta_Type", "0")

    assert updated == "sta_Type = 0\ncal_time = 500.0d0\n"


def test_replace_config_value_keeps_text_when_key_missing() -> None:
    text = "sta_Type = 1\n"

    updated = replace_config_value(text, "missing", "0")

    assert updated == text


def test_patch_mooringline_for_dynamic_updates_sixth_line() -> None:
    mooring_file = Path(__file__).with_name("_mooringline_test.dat")
    mooring_file.write_text(
        "1\n2\n3\n4\n5\nold\n7\n",
        encoding="utf-8",
    )

    try:
        patch_mooringline_for_dynamic(mooring_file)

        assert mooring_file.read_text(encoding="utf-8").splitlines()[5] == "3"
    finally:
        mooring_file.unlink(missing_ok=True)
