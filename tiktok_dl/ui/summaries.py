from __future__ import annotations

from typing import Iterable

from ..logging import Logger
from ..models import DownloadResult, UserProfile
from ..theme import Theme
from ..utils import human_timestamp


def print_profile(profile: UserProfile | None, logger: Logger) -> None:
    if not profile:
        logger.warn("Proceeding without profile details.")
        return

    logger.bullet_list(
        "Profile summary:",
        [
            f"{Theme.MUTED}Nickname: {Theme.ACCENT}{profile.nickname}{Theme.RESET}",
            f"{Theme.MUTED}Username: {Theme.ACCENT}@{profile.unique_id}{Theme.RESET}",
            f"{Theme.MUTED}Followers: {Theme.ACCENT}{profile.follower_count:,}{Theme.RESET}",
            f"{Theme.MUTED}Videos: {Theme.ACCENT}{profile.video_count:,}{Theme.RESET}",
            f"{Theme.MUTED}Verified: {Theme.ACCENT}{'Yes' if profile.verified else 'No'}{Theme.RESET}",
            f"{Theme.MUTED}Private: {Theme.ACCENT}{'Yes' if profile.private else 'No'}{Theme.RESET}",
        ],
    )
    if profile.signature:
        print(f"{Theme.MUTED}Bio: {Theme.RESET}{profile.signature[:120]}")


def print_results(results: list[DownloadResult], logger: Logger) -> None:
    success = sum(1 for r in results if r.success and r.status != "skipped")
    skipped = sum(1 for r in results if r.status == "skipped")
    failed = sum(1 for r in results if not r.success)
    blocked = sum(1 for r in results if r.status == "blocked")

    print()
    print(f"{Theme.PRIMARY}{Theme.BOLD}Download summary - {human_timestamp()}{Theme.RESET}")
    print(f"{Theme.SUCCESS}Downloaded: {success}{Theme.RESET}")
    print(f"{Theme.WARNING}Skipped:   {skipped}{Theme.RESET}")
    if blocked:
        print(f"{Theme.WARNING}Blocked:   {blocked}{Theme.RESET}")
    print(f"{Theme.ERROR}Failed:    {failed}{Theme.RESET}")
    print()

    for entry in results:
        status_color = {
            "downloaded": Theme.SUCCESS,
            "skipped": Theme.WARNING,
            "failed": Theme.ERROR,
            "blocked": Theme.WARNING,
        }.get(entry.status, Theme.MUTED)
        print(
            f"{status_color}{entry.index:03d} "
            f"{entry.status.upper():<10} "
            f"{entry.video.url}{Theme.RESET}"
        )

    print()
    logger.info("Done.")
