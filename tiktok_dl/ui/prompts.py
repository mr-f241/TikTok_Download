from __future__ import annotations

import sys
from typing import Optional

from ..theme import Theme

try:
    import curses
except Exception:  # curses không có trên một số môi trường (Windows cũ, v.v.)
    curses = None  # type: ignore[assignment]


def ask_username() -> str:
    return input(
        f"{Theme.MUTED}Nhập username TikTok hoặc link profile: {Theme.PRIMARY}"
    ).strip()


def _arrow_video_picker(total: int) -> str:
    """
    Giao diện chọn số video bằng phím mũi tên.
    - Lên / Xuống: tăng / giảm 1
    - Trái / Phải: giảm / tăng 10
    - A: chọn tất cả
    - Enter: xác nhận
    Trả về:
      - "all"  nếu chọn tất cả
      - str(n) nếu chọn số n
    """

    def _ui(stdscr: "curses._CursesWindow") -> str:
        curses.curs_set(0)
        stdscr.nodelay(False)
        stdscr.keypad(True)

        current = min(20, total) if total > 0 else 0
        if current <= 0:
            current = total

        while True:
            stdscr.clear()
            stdscr.addstr(
                0,
                0,
                "Chon so video gan nhat can tai:",
                curses.A_BOLD,
            )
            stdscr.addstr(2, 0, f"Co san: {total}")
            if current >= total:
                label = f"TAT CA ({total})"
            else:
                label = str(current)
            stdscr.addstr(4, 0, f"Lua chon hien tai: {label}", curses.A_REVERSE)

            stdscr.addstr(6, 0, "Dieu khien:")
            stdscr.addstr(7, 2, "↑ / ↓ : +/- 1")
            stdscr.addstr(8, 2, "← / → : -/+ 10")
            stdscr.addstr(9, 2, "A     : Tat ca video")
            stdscr.addstr(10, 2, "Enter : Xac nhan")
            stdscr.addstr(12, 0, "Nhan 'q' de huy (se quay ve che do nhap so).")

            stdscr.refresh()
            key = stdscr.getch()

            if key in (ord("q"), ord("Q")):
                # Huỷ: để code ngoài tự fallback
                return ""

            if key in (curses.KEY_UP, ord("k")):
                current = max(1, current - 1)
            elif key in (curses.KEY_DOWN, ord("j")):
                current = min(total, current + 1)
            elif key in (curses.KEY_LEFT, ord("h")):
                current = max(1, current - 10)
            elif key in (curses.KEY_RIGHT, ord("l")):
                current = min(total, current + 10)
            elif key in (ord("a"), ord("A")):
                return "all"
            elif key in (curses.KEY_ENTER, 10, 13):
                if current >= total:
                    return "all"
                return str(current)

    result: Optional[str] = curses.wrapper(_ui)  # type: ignore[arg-type]
    return result or ""


def ask_video_count(total: int) -> str:
    # Nếu có curses và đang chạy trong TTY, cho phép dùng giao diện mũi tên.
    if curses is not None and sys.stdin.isatty() and sys.stdout.isatty():
        try:
            value = _arrow_video_picker(total)
            if value:
                return value
        except Exception:
            # Nếu có lỗi với curses thì fallback về input chuẩn.
            pass

    # Fallback: dùng nhập số như bình thường
    return input(
        f"{Theme.MUTED}Tải bao nhiêu video gần nhất? (1-{total}, 0 hoặc 'all' hoặc Enter = tất cả) {Theme.RESET}"
    ).strip()


def confirm_start(count: int, folder: str) -> bool:
    reply = input(
        f"{Theme.MUTED}Tải {count} video vào thư mục {folder}? (y/n) {Theme.RESET}"
    ).strip().lower()
    return reply in {"y", "yes"}
