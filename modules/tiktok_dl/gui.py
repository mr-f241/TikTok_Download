from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import List, Optional

import requests

from .config import Settings
from .http import build_session
from .logging import Logger
from .models import VideoItem
from .services.download_service import DownloadService
from .services.profile_service import ProfileService
from .services.video_service import VideoService
from .uploader_bridge import upload_with_tiktok_uploader
from .utils import fetch_ip_metadata


class TikTokGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("TikTok Downloader Pro - GUI")
        self.geometry("800x600")
        self.minsize(800, 500)

        self.settings = Settings.load()
        self.logger = Logger()
        self.session = build_session(self.settings.proxy)

        self._build_ui()

    # UI BUILDING

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        header.columnconfigure(0, weight=1)

        title_label = ttk.Label(
            header,
            text="TikTok Downloader Pro",
            font=("Segoe UI", 16, "bold"),
        )
        subtitle_label = ttk.Label(
            header,
            text="Tải và upload video TikTok với giao diện trực quan",
            font=("Segoe UI", 10),
        )
        title_label.grid(row=0, column=0, sticky="w")
        subtitle_label.grid(row=1, column=0, sticky="w")

        notebook = ttk.Notebook(self)
        notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Tabs
        self.tab_download_user = ttk.Frame(notebook)
        self.tab_download_url = ttk.Frame(notebook)
        self.tab_upload = ttk.Frame(notebook)

        notebook.add(self.tab_download_user, text="Tải theo username")
        notebook.add(self.tab_download_url, text="Tải từ URL")
        notebook.add(self.tab_upload, text="Upload TikTok")

        # Log frame
        log_frame = ttk.LabelFrame(self, text="Nhật ký")
        log_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_frame,
            height=8,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text["yscrollcommand"] = scrollbar.set

        # Build each tab
        self._build_tab_download_user()
        self._build_tab_download_url()
        self._build_tab_upload()

        # Load and show IP info (optional)
        self._log_ip_info()

    def _build_tab_download_user(self) -> None:
        frame = self.tab_download_user
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Username hoặc link profile:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.username_entry = ttk.Entry(frame)
        self.username_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(frame, text="Số video cần tải (0 = tất cả):").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.count_spin = ttk.Spinbox(frame, from_=0, to=999, width=10)
        self.count_spin.set("20")
        self.count_spin.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(frame, text="Thư mục lưu:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.download_dir_var = tk.StringVar(
            value=str(self.settings.download_dir)
        )
        dir_frame = ttk.Frame(frame)
        dir_frame.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        dir_frame.columnconfigure(0, weight=1)
        dir_entry = ttk.Entry(dir_frame, textvariable=self.download_dir_var)
        dir_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(
            dir_frame, text="Chọn...", command=self._choose_download_dir
        ).grid(row=0, column=1, padx=(5, 0))

        options_frame = ttk.Frame(frame)
        options_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self.metadata_var = tk.BooleanVar(value=False)
        self.thumbs_var = tk.BooleanVar(value=False)
        self.playlist_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            options_frame, text="Lưu metadata (JSON)", variable=self.metadata_var
        ).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(
            options_frame, text="Tải thumbnail", variable=self.thumbs_var
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Checkbutton(
            options_frame, text="Xuất playlist .m3u", variable=self.playlist_var
        ).grid(row=0, column=2, sticky="w", padx=(10, 0))

        ttk.Button(
            frame,
            text="Bắt đầu tải",
            command=self._on_download_user_clicked,
        ).grid(row=4, column=0, columnspan=2, pady=10)

    def _build_tab_download_url(self) -> None:
        frame = self.tab_download_url
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="URL (YouTube, TikTok, ...):").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.url_entry = ttk.Entry(frame)
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Button(
            frame,
            text="Bắt đầu tải URL",
            command=self._on_download_url_clicked,
        ).grid(row=1, column=0, columnspan=2, pady=10)

    def _build_tab_upload(self) -> None:
        frame = self.tab_upload
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="File video:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.upload_video_var = tk.StringVar()
        upload_frame = ttk.Frame(frame)
        upload_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        upload_frame.columnconfigure(0, weight=1)
        ttk.Entry(upload_frame, textvariable=self.upload_video_var).grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Button(
            upload_frame, text="Chọn...", command=self._choose_upload_video
        ).grid(row=0, column=1, padx=(5, 0))

        ttk.Label(frame, text="Mô tả (caption):").grid(
            row=1, column=0, sticky="nw", padx=5, pady=5
        )
        self.upload_desc = tk.Text(frame, height=4)
        self.upload_desc.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(frame, text="File cookies JSON (tuỳ chọn):").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.cookies_var = tk.StringVar()
        cookies_frame = ttk.Frame(frame)
        cookies_frame.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        cookies_frame.columnconfigure(0, weight=1)
        ttk.Entry(cookies_frame, textvariable=self.cookies_var).grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Button(
            cookies_frame, text="Chọn...", command=self._choose_cookies_file
        ).grid(row=0, column=1, padx=(5, 0))

        ttk.Label(frame, text="Cookie sessionid (tuỳ chọn):").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        self.sessionid_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.sessionid_var).grid(
            row=3, column=1, sticky="ew", padx=5, pady=5
        )

        ttk.Button(
            frame,
            text="Upload lên TikTok",
            command=self._on_upload_clicked,
        ).grid(row=4, column=0, columnspan=2, pady=10)

    # HELPERS

    def _log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _log_ip_info(self) -> None:
        try:
            ip_info = fetch_ip_metadata(self.session, self.settings.request_timeout)
            self._log(
                f"IP: {ip_info.get('ip', 'unknown')} | Vị trí: {ip_info.get('city', 'unknown')}, {ip_info.get('country', 'unknown')}"
            )
        except Exception:
            pass

    def _choose_download_dir(self) -> None:
        directory = filedialog.askdirectory(
            title="Chọn thư mục lưu video",
            initialdir=self.download_dir_var.get() or str(self.settings.download_dir),
        )
        if directory:
            self.download_dir_var.set(directory)

    def _choose_upload_video(self) -> None:
        filename = filedialog.askopenfilename(
            title="Chọn file video cần upload",
            filetypes=[("Video files", "*.mp4 *.mov *.mkv *.webm *.avi"), ("All files", "*.*")],
        )
        if filename:
            self.upload_video_var.set(filename)

    def _choose_cookies_file(self) -> None:
        filename = filedialog.askopenfilename(
            title="Chọn file cookies JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if filename:
            self.cookies_var.set(filename)

    # BUTTON HANDLERS

    def _on_download_user_clicked(self) -> None:
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập username hoặc link profile.")
            return

        try:
            count = int(self.count_spin.get())
        except ValueError:
            count = 20

        download_dir = Path(self.download_dir_var.get() or self.settings.download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)
        self.settings.download_dir = download_dir

        metadata = self.metadata_var.get()
        thumbs = self.thumbs_var.get()
        playlist = self.playlist_var.get()

        threading.Thread(
            target=self._download_by_username_worker,
            args=(username, count, metadata, thumbs, playlist),
            daemon=True,
        ).start()

    def _download_by_username_worker(
        self,
        username_raw: str,
        count_input: int,
        metadata: bool,
        thumbs: bool,
        playlist: bool,
    ) -> None:
        try:
            self._log(f"[GUI] Đang quét tài khoản: {username_raw}")
            session = build_session(self.settings.proxy)
            profile_service = ProfileService(session, self.settings.request_timeout, self.logger)
            video_service = VideoService(session, self.settings.request_timeout, self.logger)

            username = profile_service.normalize(username_raw)
            profile = profile_service.fetch_profile(username)
            videos: List[VideoItem] = video_service.discover_videos(username)

            if not videos:
                self._log("[GUI] Không tìm thấy video nào cho tài khoản này.")
                messagebox.showinfo("Kết quả", "Không có video nào được tìm thấy.")
                return

            total = len(videos)
            if count_input <= 0:
                count = total
            else:
                count = min(count_input, total)

            self._log(f"[GUI] Tìm thấy {total} video, sẽ tải {count} video mới nhất.")

            download_service = DownloadService(
                base_dir=self.settings.download_dir,
                username=username,
                max_workers=self.settings.max_workers,
                proxy=self.settings.proxy,
                logger=self.logger,
                rate_limit=None,
            )
            subset = videos[:count]
            results = download_service.download_all(subset)

            success = sum(1 for r in results if r.success and r.status != "skipped")
            failed = sum(1 for r in results if not r.success)
            skipped = sum(1 for r in results if r.status == "skipped")

            self._log(
                f"[GUI] Hoàn thành: {success} thành công, {skipped} bỏ qua, {failed} thất bại."
            )

            if metadata:
                metadata_path = download_service.target_dir / "metadata.json"
                from .cli import export_metadata  # tránh import vòng

                export_metadata(subset, metadata_path, "json")
                self._log(f"[GUI] Đã lưu metadata tại: {metadata_path}")

            if playlist:
                playlist_path = download_service.target_dir / "playlist.m3u"
                from .cli import export_playlist

                export_playlist(subset, playlist_path)
                self._log(f"[GUI] Đã xuất playlist tại: {playlist_path}")

            if thumbs:
                from .cli import download_thumbnails

                download_thumbnails(
                    session=session,
                    videos=subset,
                    target_dir=download_service.target_dir,
                    logger=self.logger,
                    timeout=self.settings.request_timeout,
                )
                self._log("[GUI] Đã tải thumbnail (nếu có).")

            messagebox.showinfo(
                "Hoàn thành",
                f"Tải xong {success} video.\nThư mục lưu: {download_service.target_dir}",
            )
        except Exception as exc:
            self._log(f"[GUI] Lỗi khi tải: {exc}")
            messagebox.showerror("Lỗi", f"Lỗi khi tải video: {exc}")

    def _on_download_url_clicked(self) -> None:
        from .cli import yt_dlp  # reuse existing import

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập URL cần tải.")
            return

        target_dir = self.settings.download_dir / "generic"
        target_dir.mkdir(parents=True, exist_ok=True)

        def worker() -> None:
            try:
                self._log(f"[GUI] Đang tải từ URL: {url}")
                ydl_opts = {
                    "outtmpl": str(target_dir / "%(title)s.%(ext)s"),
                    "format": "best",
                    "noplaylist": False,
                    "quiet": False,
                }
                if self.settings.proxy:
                    ydl_opts["proxy"] = self.settings.proxy
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                self._log(f"[GUI] Đã tải xong vào: {target_dir}")
                messagebox.showinfo("Hoàn thành", f"Đã tải xong.\nThư mục: {target_dir}")
            except Exception as exc:
                self._log(f"[GUI] Lỗi khi tải URL: {exc}")
                messagebox.showerror("Lỗi", f"Lỗi khi tải URL: {exc}")

        threading.Thread(target=worker, daemon=True).start()

    def _on_upload_clicked(self) -> None:
        video_path = self.upload_video_var.get().strip()
        if not video_path:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn file video cần upload.")
            return

        desc = self.upload_desc.get("1.0", "end").strip()
        cookies_file = self.cookies_var.get().strip() or None
        sessionid = self.sessionid_var.get().strip() or None

        def worker() -> None:
            try:
                self._log(f"[GUI] Bắt đầu upload video: {video_path}")
                upload_with_tiktok_uploader(
                    video_path=video_path,
                    description=desc or None,
                    logger=self.logger,
                    cookies_file=cookies_file,
                    sessionid=sessionid,
                    proxy=self.settings.proxy,
                )
                self._log("[GUI] Upload đã kết thúc (xem log để biết chi tiết).")
                messagebox.showinfo("Upload", "Quá trình upload đã kết thúc.\nXem log để biết chi tiết.")
            except SystemExit:
                # uploader_bridge dùng SystemExit khi lỗi nặng
                self._log("[GUI] Upload gặp lỗi, dừng lại.")
            except Exception as exc:
                self._log(f"[GUI] Lỗi khi upload: {exc}")
                messagebox.showerror("Lỗi", f"Lỗi khi upload video: {exc}")

        threading.Thread(target=worker, daemon=True).start()


def run_gui() -> None:
    app = TikTokGUI()
    app.mainloop()