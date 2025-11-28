from __future__ import annotations

import os

from ..theme import Theme
from ..utils import human_timestamp, mask_ip, system_info


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_banner(ip_info: dict | None = None) -> None:
    clear_screen()
    sys_info = system_info()
    header = (
        f"{Theme.PRIMARY}{Theme.BOLD}TikTok Downloader Pro{Theme.RESET}\n"
        f"{Theme.MUTED}Trinh tai video TikTok, gon nhe va de dung{Theme.RESET}\n"
    )
    meta = (
        f"{Theme.MUTED}Nguoi dung: {Theme.ACCENT}{sys_info['username']}{Theme.RESET}  "
        f"{Theme.MUTED}May: {Theme.ACCENT}{sys_info['hostname']}{Theme.RESET}  "
        f"{Theme.MUTED}Nen tang: {Theme.ACCENT}{sys_info['platform']}{Theme.RESET}  "
        f"{Theme.MUTED}Thoi gian: {Theme.ACCENT}{human_timestamp()}{Theme.RESET}"
    )
    print(header)
    print(meta)
    if ip_info:
        masked = mask_ip(ip_info.get("ip", ""))
        print(
            f"{Theme.MUTED}IP: {Theme.ACCENT}{masked}{Theme.RESET}  "
            f"Vi tri: {Theme.ACCENT}{ip_info.get('city', 'unknown')}, {ip_info.get('country', 'unknown')}{Theme.RESET}"
        )
    print()
