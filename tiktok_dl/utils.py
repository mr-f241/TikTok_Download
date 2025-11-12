from __future__ import annotations

import platform
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict

import getpass
import requests


def human_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def system_info() -> Dict[str, str]:
    return {
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "platform": platform.platform(),
        "cwd": str(Path.cwd()),
    }


def fetch_ip_metadata(session: requests.Session, timeout: int) -> Dict[str, str]:
    try:
        response = session.get("http://ip-api.com/json/", timeout=timeout)
        data = response.json()
        return {
            "ip": data.get("query", "unknown"),
            "city": data.get("city", "unknown"),
            "country": data.get("country", "unknown"),
            "isp": data.get("isp", "unknown"),
            "timezone": data.get("timezone", "unknown"),
        }
    except Exception:
        return {"ip": "unknown", "city": "unknown", "country": "unknown"}


def mask_ip(ip: str) -> str:
    parts = ip.split(".")
    if len(parts) == 4:
        return ".".join(parts[:2] + ["***", "***"])
    return "hidden"
