from __future__ import annotations

import collections
import re
import time
from typing import Deque, List, Set

import requests

from ..logging import Logger
from ..models import VideoItem


class VideoService:
    def __init__(self, session: requests.Session, timeout: int, logger: Logger) -> None:
        self.session = session
        self.timeout = timeout
        self.logger = logger
        self.error_window: Deque[float] = collections.deque(maxlen=5)

    def _extract_video_id(self, url: str) -> str | None:
        patterns = [
            r"/video/(\d+)",
            r"tiktok\.com.*?(\d{19})",
            r"@[\w\.-]+/video/(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _cooldown_if_needed(self) -> None:
        if len(self.error_window) == self.error_window.maxlen:
            span = self.error_window[-1] - self.error_window[0]
            if span < 30:
                self.logger.warn("TikTok appears to be throttling requests. Cooling down for 120 seconds.")
                time.sleep(120)
                self.error_window.clear()

    def discover_videos(self, username: str, max_pages: int = 10) -> List[VideoItem]:
        username = username.lstrip("@")
        collected: List[VideoItem] = []
        seen: Set[str] = set()

        self.logger.info(f"Scanning @{username} for available videos...")

        # Method 1: yt-dlp flat extraction
        try:
            import yt_dlp  # noqa: PLC0415

            opts = {"quiet": True, "extract_flat": True, "playlistend": 500}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(
                    f"https://www.tiktok.com/@{username}",
                    download=False,
                )
            entries = info.get("entries", []) if isinstance(info, dict) else []
            for entry in entries:
                url = entry.get("url")
                if not url:
                    continue
                vid = self._extract_video_id(url)
                if vid and vid not in seen:
                    seen.add(vid)
                    collected.append(
                        VideoItem(
                            id=vid,
                            url=url,
                            description=entry.get("title"),
                            thumbnail_url=entry.get("thumbnail"),
                        )
                    )
            if collected:
                self.logger.success(f"yt-dlp discovered {len(collected)} videos so far.")
        except Exception as exc:
            self.logger.warn(f"yt-dlp discovery failed: {exc}")

        # Method 2: TikWM API pagination
        for page in range(1, max_pages + 1):
            cursor = (page - 1) * 30
            api_url = (
                f"https://www.tikwm.com/api/user/posts?"
                f"unique_id=@{username}&count=30&cursor={cursor}"
            )
            try:
                resp = self.session.get(api_url, timeout=self.timeout)
                if resp.status_code in (403, 429):
                    self.error_window.append(time.time())
                    self._cooldown_if_needed()
                    continue
                if resp.status_code != 200:
                    continue
                payload = resp.json()
                videos = payload.get("data", {}).get("videos", [])
                new_count = 0
                for video in videos:
                    vid = video.get("video_id")
                    if not vid or vid in seen:
                        continue
                    seen.add(vid)
                    collected.append(
                        VideoItem(
                            id=vid,
                            url=f"https://www.tiktok.com/@{username}/video/{vid}",
                            description=video.get("title"),
                            thumbnail_url=video.get("cover"),
                        )
                    )
                    new_count += 1
                if new_count:
                    self.logger.info(
                        f"Page {page}: +{new_count} videos (total {len(collected)})."
                    )
                else:
                    break
            except Exception as exc:
                self.logger.warn(f"TikWM page {page} failed: {exc}")
            time.sleep(0.3)

        if not collected:
            self.logger.warn("No videos discovered.")
        else:
            self.logger.info(f"Discovered total {len(collected)} unique videos.")
        return collected
