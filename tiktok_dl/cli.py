from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List

import requests
import yt_dlp

from .config import Settings
from .http import build_session
from .logging import Logger
from .models import VideoItem
from .services.download_service import DownloadService
from .services.profile_service import ProfileService
from .services.video_service import VideoService
from .theme import Theme
from .ui import banners, prompts, summaries
from .utils import fetch_ip_metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TikTok Downloader Pro - trinh tai video TikTok don gian, de dung",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-u", "--username", help="Username TikTok hoac link profile")
    parser.add_argument("-n", "--count", type=int, help="So video moi nhat can tai")
    parser.add_argument("--all", dest="download_all", action="store_true", help="Tai tat ca video tim duoc")
    parser.add_argument("--url", help="Tai video tu bat ky URL nao (YouTube, TikTok, ...)")
    parser.add_argument("-d", "--download-dir", help="Thu muc luu video")
    parser.add_argument("--proxy", help="HTTP/HTTPS proxy (neu co)")
    parser.add_argument("--max-workers", type=int, help="So luong tai song song toi da")
    parser.add_argument("--request-timeout", type=int, help="Thoi gian timeout mang (giay)")
    parser.add_argument("--quick", action="store_true", help="Che do nhanh (giam mau sac trong shell)")
    parser.add_argument("--privacy", action="store_true", help="An thong tin IP tren banner")
    parser.add_argument("--metadata", choices=["json", "csv"], help="Xuat metadata kem theo video")
    parser.add_argument("--thumbnails", action="store_true", help="Tai thumbnail cho tung video")
    parser.add_argument("--playlist", action="store_true", help="Xuat file playlist (.m3u) chua link video")
    parser.add_argument("--rate-limit", type=int, help="Gioi han so luong tai moi phut")
    parser.add_argument("--schedule", help="Hen gio chay (dinh dang HH:MM, 24h)")
    parser.add_argument("--watchlist", help="File chua danh sach username (moi dong 1 username)")
    parser.add_argument("--self-check", action="store_true", help="Kiem tra moi truong va thoat")
    parser.add_argument("--verify", action="store_true", help="Kiem tra file checksum hien co va thoat")
    parser.add_argument("--yes", action="store_true", help="Tu dong chap nhan cac cau hoi (khong hoi lai)")
    parser.add_argument("--api", action="store_true", help="Du phong cho che do REST API trong tuong lai")
    return parser.parse_args()


def run_self_check(logger: Logger) -> None:
    logger.info(f"Python version: {sys.version.split()[0]}")
    dependencies = ["requests", "yt_dlp", "tqdm"]
    for dep in dependencies:
        try:
            module = __import__(dep)
            version = getattr(module, "__version__", "unknown")
            logger.success(f"Dependency {dep} available (version {version})")
        except Exception as exc:
            logger.error(f"Dependency {dep} missing: {exc}")
    color_support = sys.stdout.isatty()
    logger.info(f"TTY color support: {color_support}")


def parse_schedule(spec: str, logger: Logger) -> None:
    try:
        hour, minute = map(int, spec.split(":", 1))
    except Exception:
        logger.warn("Invalid schedule format (expected HH:MM). Skipping delay.")
        return
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    delta = (target - now).total_seconds()
    logger.info(
        "Scheduled run at {:%Y-%m-%d %H:%M}. Waiting {:.1f} minutes...".format(
            target, delta / 60
        )
    )
    time.sleep(delta)


def export_metadata(videos: Iterable[VideoItem], target: Path, fmt: str) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        payload = [video.__dict__ for video in videos]
        target.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    else:
        with target.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "url", "description", "thumbnail_url"])
            for video in videos:
                writer.writerow(
                    [video.id, video.url, video.description or "", video.thumbnail_url or ""]
                )
    return target


def export_playlist(videos: Iterable[VideoItem], target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        fh.write("#EXTM3U\n")
        for video in videos:
            title = video.description or video.id
            fh.write(f"#EXTINF:-1,{title}\n{video.url}\n")
    return target


def download_thumbnails(
    session: requests.Session,
    videos: Iterable[VideoItem],
    target_dir: Path,
    logger: Logger,
    timeout: int,
) -> None:
    thumb_dir = target_dir / "thumbnails"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    for video in videos:
        if not video.thumbnail_url:
            continue
        filename = thumb_dir / f"{video.id}.jpg"
        if filename.exists():
            continue
        try:
            resp = session.get(video.thumbnail_url, timeout=timeout)
            if resp.status_code == 200:
                filename.write_bytes(resp.content)
                logger.success(f"Saved thumbnail {filename.name}")
        except Exception as exc:
            logger.warn(f"Failed to download thumbnail for {video.id}: {exc}")


def verify_checksums(root: Path, logger: Logger) -> None:
    import hashlib

    issues = 0
    for sha_path in root.rglob("*.sha256"):
        target = sha_path.with_suffix("")
        if not target.exists():
            logger.warn(f"Thieu file tuong ung cho checksum: {sha_path}")
            issues += 1
            continue
        expected = sha_path.read_text(encoding="utf-8").strip()
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if expected != digest:
            logger.error(f"File sai checksum: {target}")
            issues += 1
    if issues == 0:
        logger.success("Tat ca file checksum deu hop lely.")
    else:
        logger.warn(f"Verification completed with {issues} issue(s).")


def resolve_username(raw: str, profile_service: ProfileService) -> str:
    normalized = profile_service.normalize(raw)
    return normalized


def choose_subset(total: int, desired: int | None, download_all: bool) -> int:
    if download_all:
        return total
    if desired is None or desired <= 0:
        return min(total, 20)
    return min(total, desired)


def run_batch(
    usernames: List[str],
    settings: Settings,
    args: argparse.Namespace,
    session: requests.Session,
    logger: Logger,
) -> None:
    profile_service = ProfileService(session, settings.request_timeout, logger)
    video_service = VideoService(session, settings.request_timeout, logger)

    for raw_name in usernames:
        name = raw_name.strip()
        if not name:
            continue
        username = resolve_username(name, profile_service)
        profile = profile_service.fetch_profile(username)
        summaries.print_profile(profile, logger)
        videos = video_service.discover_videos(username)
        if not videos:
            logger.warn(f"No videos for {username}")
            continue
        count = choose_subset(len(videos), args.count, args.download_all)
        download_service = DownloadService(
            base_dir=settings.download_dir,
            username=username,
            max_workers=settings.max_workers,
            proxy=settings.proxy,
            logger=logger,
            rate_limit=args.rate_limit,
        )
        subset = videos[:count]
        results = download_service.download_all(subset)
        summaries.print_results(results, logger)

        if args.metadata:
            metadata_path = download_service.target_dir / f"metadata.{args.metadata}"
            export_metadata(subset, metadata_path, args.metadata)
            logger.info(f"Metadata saved to {metadata_path}")

        if args.playlist:
            playlist_path = download_service.target_dir / "playlist.m3u"
            export_playlist(subset, playlist_path)
            logger.info(f"Playlist exported to {playlist_path}")

        if args.thumbnails:
            download_thumbnails(
                session,
                subset,
                download_service.target_dir,
                logger,
                settings.request_timeout,
            )


def run_interactive(settings: Settings, logger: Logger, args: argparse.Namespace) -> None:
    session = build_session(settings.proxy)
    ip_info = None if args.privacy else fetch_ip_metadata(session, settings.request_timeout)
    profile_service = ProfileService(session, settings.request_timeout, logger)
    video_service = VideoService(session, settings.request_timeout, logger)

    while True:
        banners.print_banner(ip_info)
        raw_username = prompts.ask_username()
        if not raw_username:
            logger.warn("Khong co username, thoat che do tuong tac.")
            return
        username = resolve_username(raw_username, profile_service)
        profile = profile_service.fetch_profile(username)
        summaries.print_profile(profile, logger)

        videos = video_service.discover_videos(username)
        if not videos:
            logger.error("Khong co video nao. Thu tai khoan khac.")
            continue

        selection = prompts.ask_video_count(len(videos))

        # Hỗ trợ chọn bằng số:
        # - Enter hoặc "0" hoặc "all" => tải tất cả
        # - Số bất kỳ > 0           => giới hạn theo số đó
        if not selection or selection == "0" or selection.lower() == "all":
            count = len(videos)
        else:
            try:
                count = max(1, min(int(selection), len(videos)))
            except ValueError:
                count = min(20, len(videos))
                logger.warn("Nhap sai, mac dinh tai 20 video.")

        download_service = DownloadService(
            base_dir=settings.download_dir,
            username=username,
            max_workers=settings.max_workers,
            proxy=settings.proxy,
            logger=logger,
            rate_limit=args.rate_limit,
        )

        if prompts.confirm_start(count, str(download_service.target_dir)):
            subset = videos[:count]
            results = download_service.download_all(subset)
            summaries.print_results(results, logger)
            if args.metadata:
                metadata_path = download_service.target_dir / f"metadata.{args.metadata}"
                export_metadata(subset, metadata_path, args.metadata)
                logger.info(f"Da luu metadata tai {metadata_path}")
            if args.playlist:
                playlist_path = download_service.target_dir / "playlist.m3u"
                export_playlist(subset, playlist_path)
                logger.info(f"Da xuat playlist tai {playlist_path}")
            if args.thumbnails:
                download_thumbnails(
                    session,
                    subset,
                    download_service.target_dir,
                    logger,
                    settings.request_timeout,
                )
        else:
            logger.info("Da huy theo yeu cau nguoi dung.")

        again = input(
            f"{Theme.MUTED}Tai tiep tai khoan khac? (y/n) {Theme.RESET}"
        ).strip().lower()
        if again not in {"y", "yes"}:
            break


def run_cli(settings: Settings, args: argparse.Namespace, logger: Logger) -> None:
    session = build_session(settings.proxy)
    ip_info = None if args.privacy else fetch_ip_metadata(session, settings.request_timeout)
    banners.print_banner(ip_info)

    # Che do tai tu URL bat ky (YouTube, TikTok, ...), khong can username
    if args.url:
        target_dir = settings.download_dir / "generic"
        target_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Tai noi dung tu URL: {args.url}")
        logger.info(f"Thu muc luu: {target_dir}")

        ydl_opts = {
            "outtmpl": str(target_dir / "%(title)s.%(ext)s"),
            "format": "best",
            "noplaylist": False,
            "quiet": False,
        }
        if settings.proxy:
            ydl_opts["proxy"] = settings.proxy

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([args.url])
            logger.success("Da tai xong noi dung tu URL.")
        except Exception as exc:
            logger.error(f"Loi khi tai tu URL: {exc}")
        return

    usernames: List[str] = []
    if args.watchlist:
        watchlist_path = Path(args.watchlist)
        if not watchlist_path.exists():
            logger.error(f"Khong tim thay file watchlist: {watchlist_path}")
            return
        usernames.extend(
            line.strip() for line in watchlist_path.read_text(encoding="utf-8").splitlines()
        )
    if args.username:
        usernames.append(args.username)

    if not usernames:
        logger.error("Khong co username nao. Su dung --username hoac --watchlist.")
        return

    profile_service = ProfileService(session, settings.request_timeout, logger)
    video_service = VideoService(session, settings.request_timeout, logger)

    for raw_name in usernames:
        if not raw_name:
            continue
        username = resolve_username(raw_name, profile_service)
        profile = profile_service.fetch_profile(username)
        summaries.print_profile(profile, logger)

        videos = video_service.discover_videos(username)
        if not videos:
            logger.warn(f"Khong co video nao cho {username}.")
            continue

        count = choose_subset(len(videos), args.count, args.download_all)
        download_service = DownloadService(
            base_dir=settings.download_dir,
            username=username,
            max_workers=settings.max_workers,
            proxy=settings.proxy,
            logger=logger,
            rate_limit=args.rate_limit,
        )

        if not args.yes:
            if not prompts.confirm_start(count, str(download_service.target_dir)):
                logger.info("Nguoi dung da huy.")
                continue

        subset = videos[:count]
        results = download_service.download_all(subset)
        summaries.print_results(results, logger)

        if args.metadata:
            metadata_path = download_service.target_dir / f"metadata.{args.metadata}"
            export_metadata(subset, metadata_path, args.metadata)
            logger.info(f"Da luu metadata tai {metadata_path}")

        if args.playlist:
            playlist_path = download_service.target_dir / "playlist.m3u"
            export_playlist(subset, playlist_path)
            logger.info(f"Da xuat playlist tai {playlist_path}")

        if args.thumbnails:
            download_thumbnails(
                session,
                subset,
                download_service.target_dir,
                logger,
                settings.request_timeout,
            )


def main() -> None:
    args = parse_args()
    logger = Logger()

    if args.self_check:
        run_self_check(logger)
        return

    if args.verify:
        settings = Settings.load()
        verify_checksums(settings.download_dir, logger)
        return

    settings = Settings.load()
    settings.apply_overrides(
        download_dir=args.download_dir,
        max_workers=args.max_workers,
        quick_mode=args.quick,
        proxy=args.proxy,
        request_timeout=args.request_timeout,
    )

    if args.schedule:
        parse_schedule(args.schedule, logger)

    if args.watchlist and args.username:
        logger.info("Processing --watchlist first, then explicit --username.")

    if args.api:
        logger.warn("REST API mode is not implemented yet. Continuing with CLI mode.")

    if args.username or args.watchlist:
        run_cli(settings, args, logger)
    else:
        run_interactive(settings, logger, args)
