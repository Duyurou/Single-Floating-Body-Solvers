"""Tests for body displacement result parsing."""

from pathlib import Path

import pytest

from core.results.body_parser import BodyParserError, parse_output_disp


def test_parse_output_disp_reads_six_degree_series() -> None:
    result_file = Path(__file__).with_name("_output_disp_test.dat")
    result_file.write_text(
        "0.0 1.0 2.0 3.0 4.0 5.0 6.0\n" "0.5 1.5 2.5 3.5 4.5 5.5 6.5\n",
        encoding="utf-8",
    )

    try:
        series = parse_output_disp(result_file)
    finally:
        result_file.unlink(missing_ok=True)

    assert series.point_count == 2
    assert series.time == (0.0, 0.5)
    assert series.surge == (1.0, 1.5)
    assert series.yaw == (6.0, 6.5)


def test_parse_output_disp_rejects_short_rows() -> None:
    result_file = Path(__file__).with_name("_short_disp_test.dat")
    result_file.write_text("0.0 1.0 2.0\n", encoding="utf-8")

    try:
        with pytest.raises(BodyParserError, match="列数不足"):
            parse_output_disp(result_file)
    finally:
        result_file.unlink(missing_ok=True)


def test_parse_output_disp_rejects_missing_file() -> None:
    missing_file = Path(__file__).with_name("_missing_disp_test.dat")
    missing_file.unlink(missing_ok=True)

    with pytest.raises(BodyParserError, match="结果文件不存在"):
        parse_output_disp(missing_file)
