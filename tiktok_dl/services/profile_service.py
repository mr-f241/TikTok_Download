from __future__ import annotations

from typing import Optional

import requests

from ..logging import Logger
from ..models import UserProfile


class ProfileService:
    def __init__(self, session: requests.Session, timeout: int, logger: Logger) -> None:
        self.session = session
        self.timeout = timeout
        self.logger = logger

    def normalize(self, raw: str) -> str:
        raw = (raw or "").strip()
        if not raw:
            return ""
        if raw.startswith("@"):
            raw = raw[1:]
        return raw

    def fetch_profile(self, username: str) -> Optional[UserProfile]:
        username = self.normalize(username)
        if not username:
            self.logger.warn("Username is empty.")
            return None

        apis = [
            f"https://www.tikwm.com/api/user/info?unique_id=@{username}",
            f"https://api.tiktokuserinfo.com/user/info?username={username}",
        ]

        for url in apis:
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                user = (
                    data.get("data", {}).get("user")
                    or data.get("user")
                    or data.get("data")
                    or {}
                )
                stats = data.get("data", {}).get("stats")
                
                if not user and not stats:
                    continue

                return UserProfile(
                    nickname=user.get("nickname", username),
                    unique_id=user.get("uniqueId", username),
                    signature=user.get("signature", "No bio"),
                    follower_count=stats.get("followerCount", user.get("fans", 0)),
                    following_count=stats.get("followingCount", user.get("follow", 0)),
                    heart_count=stats.get("heartCount", user.get("heart", 0)),
                    video_count=stats.get("videoCount", user.get("video", 0)),
                    verified=bool(user.get("verified", False)),
                    private=bool(user.get("private", False)),
                )
            except Exception as exc:
                self.logger.warn(f"Profile API failed: {exc}")

        self.logger.warn("Unable to fetch profile from available APIs.")
        return None
