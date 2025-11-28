from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG = {
    "download_dir": str(Path.home() / "Downloads" / "TikTokDownloads"),
    "max_workers": 4,
    "request_timeout_sec": 15,
    "quick_mode": True,
    "proxy": "",
}

CONFIG_FILE = Path("tiktok_termux_ultimate.config.json")


@dataclass
class Settings:
    download_dir: Path = Path(DEFAULT_CONFIG["download_dir"])
    max_workers: int = DEFAULT_CONFIG["max_workers"]
    request_timeout: int = DEFAULT_CONFIG["request_timeout_sec"]
    quick_mode: bool = DEFAULT_CONFIG["quick_mode"]
    proxy: str = DEFAULT_CONFIG["proxy"]

    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Settings":
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}
            CONFIG_FILE.write_text(
                json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        merged = {**DEFAULT_CONFIG, **data}
        settings = cls(
            download_dir=Path(merged["download_dir"]).expanduser(),
            max_workers=max(int(merged["max_workers"]), 1),
            request_timeout=max(int(merged["request_timeout_sec"]), 5),
            quick_mode=bool(merged["quick_mode"]),
            proxy=str(merged["proxy"] or "").strip(),
        )
        settings.extra = merged
        settings.download_dir.mkdir(parents=True, exist_ok=True)
        return settings

    def apply_overrides(
        self,
        download_dir: str | None = None,
        max_workers: int | None = None,
        quick_mode: bool | None = None,
        proxy: str | None = None,
        request_timeout: int | None = None,
    ) -> None:
        if download_dir:
            path = Path(download_dir).expanduser()
            path.mkdir(parents=True, exist_ok=True)
            self.download_dir = path
        if max_workers:
            self.max_workers = max(1, int(max_workers))
        if quick_mode is not None:
            self.quick_mode = bool(quick_mode)
        if proxy is not None:
            self.proxy = proxy.strip()
        if request_timeout:
            self.request_timeout = max(5, int(request_timeout))
