"""Local, bundled brand-logo lookup with offline monogram fallbacks."""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageTk


class LogoService:
    """Render bundled SVG brand marks without making network requests."""

    def __init__(self, widget, logo_dir: str | Path | None = None):
        self.widget = widget
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        self.logo_dir = Path(logo_dir) if logo_dir else bundle_root / "assets" / "logos"
        self.logo_aliases = self._load_manifest()
        self.images = {}

    def _load_manifest(self):
        aliases = {}
        manifest_path = self.logo_dir / "manifest.json"
        try:
            catalog = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return aliases
        # Exact product names always win over incidental hosting domains
        # (many projects point to github.com without being the GitHub product).
        for item in catalog:
            filename = item.get("file")
            if not filename:
                continue
            title = self._normalise(item.get("title", ""))
            if title:
                aliases[title] = filename
        for item in catalog:
            filename = item.get("file")
            if not filename:
                continue
            host = urlparse(item.get("url", "")).hostname or ""
            host = host.lower().removeprefix("www.")
            if host:
                aliases.setdefault(self._normalise(host), filename)
                for part in host.split(".")[:-1]:
                    if part not in {"www", "app", "mail", "accounts"}:
                        aliases.setdefault(self._normalise(part), filename)
        return aliases

    def request(self, site: str, url: str, size: int, callback) -> None:
        key = (self._identity(site, url), size)
        if key not in self.images:
            self.images[key] = self._load_logo(site, url, size)
        callback(self.images[key])

    def _load_logo(self, site: str, url: str, size: int):
        logo_name = self._logo_name(site, url)
        logo_path = self.logo_dir / logo_name if logo_name else None
        if logo_path and logo_path.is_file():
            try:
                png = cairosvg.svg2png(
                    bytestring=logo_path.read_bytes(),
                    output_width=size,
                    output_height=size,
                )
                return ImageTk.PhotoImage(Image.open(io.BytesIO(png)).convert("RGBA"))
            except (OSError, ValueError):
                pass
        return self._placeholder(site, size)

    def _logo_name(self, site: str, url: str):
        host = urlparse(url if "://" in url else f"https://{url}").hostname or ""
        candidates = [site, host.lower().removeprefix("www."), *host.lower().split(".")]
        for candidate in candidates:
            filename = self.logo_aliases.get(self._normalise(candidate))
            if filename:
                return filename
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
