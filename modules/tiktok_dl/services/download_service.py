from __future__ import annotations

import re
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urlparse

import yt_dlp

from ..logging import Logger
from ..models import DownloadResult, VideoItem

ALLOWED_HOSTS = {"www.tiktok.com", "m.tiktok.com", "tiktok.com"}
SAFE_SLUG = re.compile(r"[^A-Z0-9\-]")


def safe_folder(username: str) -> Path:
    slug = SAFE_SLUG.sub("_", username.upper()) or "UNKNOWN"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(slug) / timestamp


def write_checksum(target: Path) -> None:
    digest = sha256(target.read_bytes()).hexdigest()
    target.with_suffix(target.suffix + ".sha256").write_text(digest, encoding="utf-8")


class DownloadService:
    def __init__(
        self,
        base_dir: Path,
        username: str,
        max_workers: int,
        proxy: Optional[str],
        logger: Logger,
        rate_limit: Optional[int] = None,
    ) -> None:
        self.base_dir = base_dir
        self.username = username
        self.max_workers = max(1, int(max_workers))
        self.proxy = proxy
        self.logger = logger
        self.rate_limit = rate_limit
        self.completed_window: deque[float] = deque(maxlen=rate_limit or 0)
        self.target_dir = base_dir / safe_folder(username)
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def _allowed_url(self, url: str) -> bool:
        try:
            host = urlparse(url).netloc.lower()
        except Exception:
            return False
        return host in ALLOWED_HOSTS

    def _respect_rate_limit(self) -> None:
        if not self.rate_limit:
            return
        now = time.time()
        if len(self.completed_window) == self.completed_window.maxlen:
            span = now - self.completed_window[0]
            if span < 60:
                sleep_for = 60 - span
                self.logger.warn(f"Rate limit hit. Sleeping for {sleep_for:.1f}s")
                time.sleep(sleep_for)
        self.completed_window.append(time.time())

    def _download(self, index: int, video: VideoItem) -> DownloadResult:
        target = self.target_dir / f"{index:04d}_{video.id}.mp4"
        if target.exists() and target.stat().st_size > 1024:
            return DownloadResult(index, video, True, "skipped", target)

        if not self._allowed_url(video.url):
            return DownloadResult(index, video, False, "blocked", target)

        opts = {
            "outtmpl": str(target),
            "format": "best",
            "quiet": True,
            "retries": 3,
            "noprogress": True,
            "nocheckcertificate": True,
        }
        if self.proxy:
            opts["proxy"] = self.proxy

        for attempt in range(1, 4):
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([video.url])
                if target.exists() and target.stat().st_size > 1024:
                    write_checksum(target)
                    self._respect_rate_limit()
                    return DownloadResult(index, video, True, "downloaded", target)
            except Exception as exc:
                self.logger.warn(
                    f"Attempt {attempt} failed for video {video.id}: {exc}"
                )
                time.sleep(attempt)
        return DownloadResult(index, video, False, "failed", target)

    def download_all(self, videos: Iterable[VideoItem]) -> List[DownloadResult]:
        videos = list(videos)
        if not videos:
            return []

        self.logger.info(
            f"Starting parallel download with {self.max_workers} worker(s) into {self.target_dir}"
        )

        results: List[DownloadResult] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_map = {
                executor.submit(self._download, idx, video): (idx, video)
                for idx, video in enumerate(videos, start=1)
            }
            for future in as_completed(future_map):
                results.append(future.result())

        results.sort(key=lambda r: r.index)
        return results
