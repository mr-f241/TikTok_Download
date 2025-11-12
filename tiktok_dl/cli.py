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
        description="TikTok Downloader Pro - clean, modular edition",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-u", "--username", help="TikTok username or profile URL")
    parser.add_argument("-n", "--count", type=int, help="Number of latest videos")
    parser.add_argument("--all", dest="download_all", action="store_true", help="Download every video discovered")
    parser.add_argument("-d", "--download-dir", help="Custom download directory")
    parser.add_argument("--proxy", help="HTTP/HTTPS proxy")
    parser.add_argument("--max-workers", type=int, help="Max simultaneous downloads")
    parser.add_argument("--request-timeout", type=int, help="Network timeout seconds")
    parser.add_argument("--quick", action="store_true", help="Quick mode (less shell coloring)")
    parser.add_argument("--privacy", action="store_true", help="Suppress IP information in banners")
    parser.add_argument("--metadata", choices=["json", "csv"], help="Export metadata alongside downloads")
    parser.add_argument("--thumbnails", action="store_true", help="Download thumbnails for each video")
    parser.add_argument("--playlist", action="store_true", help="Export playlist file (.m3u) with video URLs")
    parser.add_argument("--rate-limit", type=int, help="Maximum downloads per minute")
    parser.add_argument("--schedule", help="Defer run until HH:MM (24 hour)")
    parser.add_argument("--watchlist", help="Path to file containing one username per line")
    parser.add_argument("--self-check", action="store_true", help="Run environment diagnostics and exit")
    parser.add_argument("--verify", action="store_true", help="Verify existing checksum files and exit")
    parser.add_argument("--yes", action="store_true", help="Auto-confirm prompts in CLI mode")
    parser.add_argument("--api", action="store_true", help="Reserved for future REST API mode")
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
            logger.warn(f"Missing referenced file for {sha_path}")
            issues += 1
            continue
        expected = sha_path.read_text(encoding="utf-8").strip()
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if expected != digest:
            logger.error(f"Checksum mismatch: {target}")
            issues += 1
    if issues == 0:
        logger.success("All checksum files verified successfully.")
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
            logger.warn("Empty username, exiting interactive mode.")
            return
        username = resolve_username(raw_username, profile_service)
        profile = profile_service.fetch_profile(username)
        summaries.print_profile(profile, logger)

        videos = video_service.discover_videos(username)
        if not videos:
            logger.error("No videos available. Try another account.")
            continue

        selection = prompts.ask_video_count(len(videos))
        if selection.lower() == "all":
            count = len(videos)
        else:
            try:
                count = max(1, min(int(selection), len(videos)))
            except ValueError:
                count = min(20, len(videos))
                logger.warn("Invalid input, defaulting to 20 videos.")

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
        else:
            logger.info("Cancelled by user.")

        again = input(
            f"{Theme.MUTED}Download another account? (y/n) {Theme.RESET}"
        ).strip().lower()
        if again not in {"y", "yes"}:
            break


def run_cli(settings: Settings, args: argparse.Namespace, logger: Logger) -> None:
    session = build_session(settings.proxy)
    ip_info = None if args.privacy else fetch_ip_metadata(session, settings.request_timeout)
    banners.print_banner(ip_info)

    usernames: List[str] = []
    if args.watchlist:
        watchlist_path = Path(args.watchlist)
        if not watchlist_path.exists():
            logger.error(f"Watchlist file not found: {watchlist_path}")
            return
        usernames.extend(
            line.strip() for line in watchlist_path.read_text(encoding="utf-8").splitlines()
        )
    if args.username:
        usernames.append(args.username)

    if not usernames:
        logger.error("No username provided. Use --username or --watchlist.")
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
            logger.warn(f"No videos available for {username}.")
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
                logger.info("Cancelled by user input.")
                continue

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
