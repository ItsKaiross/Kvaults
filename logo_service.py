"""Asynchronous, cached brand-logo lookup backed by the public SVGL API."""

from __future__ import annotations

import hashlib
import io
import json
import queue
import re
import threading
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageTk

SVGL_API = "https://api.svgl.app"


class LogoService:
    def __init__(self, widget, cache_dir: str | Path = ".logo_cache"):
        self.widget = widget
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.images = {}
        self._pending = {}
        self._results = queue.Queue()
        self.widget.after(100, self._poll)

    def request(self, site: str, url: str, size: int, callback) -> None:
        key = (self._identity(site, url), size)
        if key in self.images:
            callback(self.images[key])
            return
        self.images[key] = self._placeholder(site, size)
        callback(self.images[key])
        if key in self._pending:
            self._pending[key].append(callback)
            return
        self._pending[key] = [callback]

        def worker():
            try:
                png = self._fetch_png(site, url, size)
            except Exception:
                png = None
            self._results.put((key, png))

        threading.Thread(target=worker, daemon=True).start()

    def _poll(self):
        try:
            while True:
                key, png = self._results.get_nowait()
                self._finish(key, png)
        except queue.Empty:
            pass
        if self.widget.winfo_exists():
            self.widget.after(100, self._poll)

    def _finish(self, key, png):
        callbacks = self._pending.pop(key, [])
        if png:
            image = Image.open(io.BytesIO(png)).convert("RGBA")
            self.images[key] = ImageTk.PhotoImage(image)
        for callback in callbacks:
            callback(self.images[key])

    def _fetch_png(self, site: str, url: str, size: int):
        identity = self._identity(site, url)
        digest = hashlib.sha256(f"{identity}:{size}".encode()).hexdigest()[:20]
        cached = self.cache_dir / f"{digest}.png"
        if cached.exists():
            return cached.read_bytes()
        query = urllib.parse.quote(site.strip())
        req = urllib.request.Request(
            f"{SVGL_API}?search={query}", headers={"User-Agent": "Kvaults/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            results = json.load(response)
        match = self._best_match(results, site, url)
        if not match:
            return None
        route = match.get("route")
        if isinstance(route, dict):
            route = route.get("dark") or route.get("light")
        if not route:
            return None
        req = urllib.request.Request(route, headers={"User-Agent": "Kvaults/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            svg = response.read()
        png = cairosvg.svg2png(bytestring=svg, output_width=size, output_height=size)
        cached.write_bytes(png)
        return png

    @staticmethod
    def _best_match(results, site, url):
        wanted = LogoService._normalise(site)
        host = urlparse(url if "://" in url else f"https://{url}").hostname or ""
        host_brand = LogoService._normalise(host.split(".")[-2] if "." in host else host)
        for item in results:
            title = LogoService._normalise(item.get("title", ""))
            item_host = urlparse(item.get("url", "")).hostname or ""
            if title == wanted or (host_brand and host_brand in LogoService._normalise(item_host)):
                return item
        return None

    @staticmethod
    def _identity(site, url):
        host = urlparse(url if "://" in url else f"https://{url}").hostname
        return (host or site).lower().strip()

    @staticmethod
    def _normalise(value):
        return re.sub(r"[^a-z0-9]", "", value.lower())

    @staticmethod
    def _placeholder(site, size):
        palette = ("#7C6FF7", "#2CB67D", "#EF8354", "#3A86FF", "#D65DB1")
        color = palette[sum(site.lower().encode()) % len(palette)]
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((1, 1, size - 2, size - 2), radius=max(8, size // 4), fill=color)
        letter = (site.strip()[:1] or "?").upper()
        try:
            font = ImageFont.truetype("arial.ttf", max(12, int(size * .46)))
        except OSError:
            font = ImageFont.load_default()
        box = draw.textbbox((0, 0), letter, font=font)
        draw.text(((size - box[2]) / 2, (size - box[3]) / 2 - 1), letter, font=font, fill="white")
        return ImageTk.PhotoImage(image)
