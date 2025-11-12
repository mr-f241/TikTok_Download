from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .theme import Theme


@dataclass
class Logger:
    prefix: str = "[TikTokDL]"

    def _line(self, level: str, message: str) -> str:
        return f"{Theme.MUTED}{self.prefix}{Theme.RESET} {level} {message}{Theme.RESET}"

    def info(self, message: str) -> None:
        print(self._line(f"{Theme.PRIMARY}INFO", message))

    def success(self, message: str) -> None:
        print(self._line(f"{Theme.SUCCESS}OK", message))

    def warn(self, message: str) -> None:
        print(self._line(f"{Theme.WARNING}WARN", message))

    def error(self, message: str) -> None:
        print(self._line(f"{Theme.ERROR}ERROR", message))

    def bullet_list(self, title: str, items: Iterable[str]) -> None:
        self.info(title)
        for item in items:
            print(f"  • {item}")
