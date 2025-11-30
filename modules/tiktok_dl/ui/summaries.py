from __future__ import annotations

from typing import Iterable

from ..logging import Logger
from ..models import DownloadResult, UserProfile
from ..theme import Theme
from ..utils import human_timestamp


def print_profile(profile: UserProfile | None, logger: Logger) -> None:
    if not profile:
        logger.warn("Khong lay duoc thong tin profile, tiep tuc khong co chi tiet.")
        return

    logger.bullet_list(
        "Thong tin tai khoan:",
        [
            f"{Theme.MUTED}Ten hien thi: {Theme.ACCENT}{profile.nickname}{Theme.RESET}",
            f"{Theme.MUTED}Username: {Theme.ACCENT}@{profile.unique_id}{Theme.RESET}",
            f"{Theme.MUTED}Follower: {Theme.ACCENT}{profile.follower_count:,}{Theme.RESET}",
            f"{Theme.MUTED}So video: {Theme.ACCENT}{profile.video_count:,}{Theme.RESET}",
            f"{Theme.MUTED}Da tick xanh: {Theme.ACCENT}{'Co' if profile.verified else 'Khong'}{Theme.RESET}",
            f"{Theme.MUTED}Tai khoan rieng tu: {Theme.ACCENT}{'Co' if profile.private else 'Khong'}{Theme.RESET}",
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
    print(f"{Theme.PRIMARY}{Theme.BOLD}Tong ket tai video - {human_timestamp()}{Theme.RESET}")
    print(f"{Theme.SUCCESS}Da tai:   {success}{Theme.RESET}")
    print(f"{Theme.WARNING}Bo qua:   {skipped}{Theme.RESET}")
    if blocked:
        print(f"{Theme.WARNING}Bi chan: {blocked}{Theme.RESET}")
    print(f"{Theme.ERROR}That bai: {failed}{Theme.RESET}")
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
    logger.info("Hoan thanh.")
