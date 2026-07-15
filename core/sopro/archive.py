"""sopro 压缩包读写。"""

import zipfile
from pathlib import Path


class SoproArchiveError(Exception):
    """sopro 压缩包处理异常。"""


class SoproArchive:
    """封装 .sopro（ZIP）文件的打开与解压。"""

    def __init__(self, sopro_path: Path) -> None:
        self.sopro_path = sopro_path.resolve()
        self._zip: zipfile.ZipFile | None = None

    def open(self) -> None:
        """打开压缩包并校验格式。"""
        if not self.sopro_path.is_file():
            raise SoproArchiveError(
                f"工程文件不存在: {self.sopro_path}",
            )
        try:
            self._zip = zipfile.ZipFile(self.sopro_path, "r")
        except zipfile.BadZipFile as exc:
            raise SoproArchiveError(
                f"不是有效的 sopro 压缩包: {self.sopro_path}",
            ) from exc
        if not self._zip.namelist():
            raise SoproArchiveError("压缩包为空")

    def close(self) -> None:
        """关闭压缩包。"""
        if self._zip is not None:
            self._zip.close()
            self._zip = None

    def extract_to(self, dest_dir: Path) -> Path:
        """解压到目标目录。"""
        if self._zip is None:
            raise SoproArchiveError("压缩包尚未打开")
        dest_dir.mkdir(parents=True, exist_ok=True)
        self._zip.extractall(dest_dir)
        return dest_dir

    def read_manifest_text(self) -> str:
        """读取压缩包内 XML 工程清单文本。"""
        if self._zip is None:
            raise SoproArchiveError("压缩包尚未打开")
        manifest_names = [
            name
            for name in self._zip.namelist()
            if name.lower().endswith(".sopro")
            and not name.endswith("/")
        ]
        if not manifest_names:
            raise SoproArchiveError("未找到工程清单文件")
        raw = self._zip.read(manifest_names[0])
        return raw.decode("utf-8", errors="replace")

    def __enter__(self) -> "SoproArchive":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
