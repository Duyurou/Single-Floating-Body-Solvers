"""工程 XML 清单解析。"""

import re
import xml.etree.ElementTree as ET

from core.models.project import ManifestInfo

_NS = {"heu": "https://www.hrbeu.edu.cn/HEU"}


def parse_manifest(xml_text: str) -> ManifestInfo:
    """解析工程清单 XML。"""
    root = ET.fromstring(xml_text)
    return ManifestInfo(
        name=_find_text(root, "Name"),
        version=_find_text(root, "Version"),
        author=_find_text(root, "Author"),
        company=_find_text(root, "Company"),
        info=_find_text(root, "Info"),
    )


def _find_text(root: ET.Element, tag: str) -> str:
    """在根节点下查找首个匹配标签文本。"""
    element = root.find(f"heu:{tag}", _NS)
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def strip_d0_suffix(value: str) -> str:
    """移除 Fortran 风格 d0 后缀。"""
    value = value.strip()
    if value.lower().endswith("d0"):
        return value[:-2]
    return value


def parse_key_value_lines(text: str) -> dict[str, str]:
    """解析 key = value 或 key=value 文本行。"""
    result: dict[str, str] = {}
    pattern = re.compile(
        r"^\s*([A-Za-z_][\w]*)\s*=\s*(.+?)\s*$",
    )
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("&") or line.startswith("/"):
            continue
        match = pattern.match(line)
        if match:
            key = match.group(1)
            value = strip_d0_suffix(match.group(2))
            result[key] = value
    return result
