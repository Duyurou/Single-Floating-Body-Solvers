"""Tests for manifest and key-value parsing."""

from core.sopro.manifest import parse_key_value_lines, parse_manifest


def test_parse_manifest_reads_namespaced_fields() -> None:
    xml_text = """
    <heu:Project xmlns:heu="https://www.hrbeu.edu.cn/HEU">
        <heu:Name>Demo Project</heu:Name>
        <heu:Version>1.0</heu:Version>
        <heu:Author>Team</heu:Author>
        <heu:Company>Lab</heu:Company>
        <heu:Info>Sample</heu:Info>
    </heu:Project>
    """

    info = parse_manifest(xml_text)

    assert info.name == "Demo Project"
    assert info.version == "1.0"
    assert info.author == "Team"
    assert info.company == "Lab"
    assert info.info == "Sample"


def test_parse_key_value_lines_ignores_namelist_markers() -> None:
    text = """
    &config
    mass = 1200d0
    waveType= 1
    invalid line
    /
    """

    result = parse_key_value_lines(text)

    assert result == {
        "mass": "1200",
        "waveType": "1",
    }
