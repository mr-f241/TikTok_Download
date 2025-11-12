from __future__ import annotations

from ..theme import Theme


def ask_username() -> str:
    return input(
        f"{Theme.MUTED}Enter TikTok username or profile URL: {Theme.PRIMARY}"
    ).strip()


def ask_video_count(total: int) -> str:
    return input(
        f"{Theme.MUTED}How many recent videos? (1-{total}, 'all' for everything) {Theme.RESET}"
    ).strip()


def confirm_start(count: int, folder: str) -> bool:
    reply = input(
        f"{Theme.MUTED}Download {count} video(s) to {folder}? (y/n) {Theme.RESET}"
    ).strip().lower()
    return reply in {"y", "yes"}
