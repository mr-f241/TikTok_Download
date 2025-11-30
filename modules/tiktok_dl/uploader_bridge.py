from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from .logging import Logger


def _ensure_tiktok_uploader_on_path(logger: Logger) -> None:
    """
    Đưa thư mục src của project tiktok-uploader vào sys.path
    để có thể import được package tiktok_uploader mà bạn đã clone sẵn.
    """
    root = Path(__file__).resolve().parent.parent
    candidate = root / "tiktok-uploader" / "src"
    if not candidate.exists():
        logger.error(
            f"Khong tim thay thu muc 'tiktok-uploader/src' ben canh project (duong dan: {candidate})"
        )
        raise SystemExit(1)
    sys.path.insert(0, str(candidate))


def upload_with_tiktok_uploader(
    video_path: str,
    description: str | None,
    logger: Logger,
    cookies_file: Optional[str] = None,
    sessionid: Optional[str] = None,
    proxy: Optional[str] = None,
) -> None:
    """
    Gọi thư viện tiktok_uploader (code bạn đã clone) để upload 1 video.

    Ưu tiên:
    - Nếu có cookies_file: đọc cookie từ file JSON (dạng Chrome/Firefox export)
    - Nếu có sessionid: truyền sessionid trực tiếp
    """

    _ensure_tiktok_uploader_on_path(logger)

    try:
        from tiktok_uploader.upload import upload_video  # type: ignore[import]
        from tiktok_uploader.types import Cookie, ProxyDict  # type: ignore[import]
    except Exception as exc:  # pragma: no cover - chỉ chạy khi import lỗi
        logger.error(f"Khong the import 'tiktok_uploader' tu code clone: {exc}")
        raise SystemExit(1)

    video_path_obj = Path(video_path).expanduser().resolve()
    if not video_path_obj.exists():
        logger.error(f"Khong tim thay file video: {video_path_obj}")
        raise SystemExit(1)

    cookies_list: list[Cookie] = []
    cookies_str: str | None = None

    if cookies_file:
        cookies_path = Path(cookies_file).expanduser().resolve()
        if not cookies_path.exists():
            logger.error(f"Khong tim thay file cookies: {cookies_path}")
            raise SystemExit(1)
        try:
            raw = cookies_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            # tiktok-uploader chap nhan list[Cookie] hoac string cookie jar
            if isinstance(data, list):
                cookies_list = data  # type: ignore[assignment]
            else:
                cookies_str = raw
            logger.info(f"Da nap cookies tu file: {cookies_path}")
        except Exception as exc:
            logger.error(f"Loi khi doc file cookies: {exc}")
            raise SystemExit(1)

    proxy_dict: Optional["ProxyDict"] = None
    if proxy:
        # tiktok_uploader ky vong ProxyDict: {"host": "...", "port": ..., "user": "...", "pass": "..."}
        # Để đơn giản: nếu người dùng truyền dạng host:port thì tách ra.
        host = proxy
        port = 0
        if "://" in proxy:
            host = proxy.split("://", 1)[1]
        if ":" in host:
            host, port_str = host.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 0
        proxy_dict = {"host": host, "port": port, "user": "", "pass": ""}  # type: ignore[assignment]

    logger.info(f"Bat dau upload video len TikTok: {video_path_obj}")
    if description:
        logger.info(f"Mo ta: {description}")

    failed = upload_video(
        filename=str(video_path_obj),
        description=description or "",
        cookies_list=cookies_list,
        cookies_str=cookies_str,
        sessionid=sessionid,
        proxy=proxy_dict,
    )

    if failed:
        logger.error("Upload khong thanh cong (co video bi fail).")
    else:
        logger.success("Upload thanh cong.")