from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class UserProfile:
    nickname: str
    unique_id: str
    signature: str
    follower_count: int
    following_count: int
    heart_count: int
    video_count: int
    verified: bool
    private: bool


@dataclass
class VideoItem:
    id: str
    url: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None


@dataclass
class DownloadResult:
    index: int
    video: VideoItem
    success: bool
    status: str
    target: Path
