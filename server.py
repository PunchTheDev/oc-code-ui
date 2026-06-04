#!/usr/bin/env python3
"""SPA-aware static file server.

Serves files directly when they exist (JS, CSS, images, data.json, etc.).
Falls back to index.html for all other paths — enables browser-refresh and
direct-link access on hash-routed single-page apps like this dashboard.

Usage:
    python3 server.py [port]   (default: 8082)
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

SERVE_DIR = Path(__file__).parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8082

# These extensions are served directly from the filesystem.
STATIC_EXTS = {
    ".html", ".js", ".css", ".json", ".png", ".jpg", ".jpeg",
    ".svg", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".map",
    ".txt", ".md",
}


# Map clean paths to their hash-router equivalents.
SPA_ROUTES = {
    "/problems":   "/#/problems",
    "/leaderboard": "/#/leaderboard",
    "/scoring":    "/#/scoring",
    "/mining":     "/#/mining",
}


class SPAHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SERVE_DIR), **kwargs)

    def _resolve(self):
        """Shared path-resolution logic for GET and HEAD.

        Returns ("redirect", target) for SPA redirects,
        ("serve", rewritten_path) for files to serve, or
        ("404", path) for hard 404s on missing static assets.
        """
        path = self.path.split("?")[0].split("#")[0].rstrip("/") or "/"
        candidate = SERVE_DIR / path.lstrip("/")

        if path in SPA_ROUTES:
            return ("redirect", SPA_ROUTES[path])
        if candidate.is_file():
            return ("serve", self.path)
        if candidate.is_dir() and (candidate / "index.html").exists():
            return ("serve", path.rstrip("/") + "/index.html")
        ext = Path(path).suffix.lower()
        if ext and ext in STATIC_EXTS:
            return ("404", path)
        return ("serve", "/index.html")

    def _dispatch(self, base_method):
        action, target = self._resolve()
        if action == "redirect":
            self.send_response(301)
            self.send_header("Location", target)
            self.end_headers()
            return
        if action == "404":
            self.send_error(404, f"File not found: {target}")
            return
        self.path = target
        base_method()

    def do_GET(self):
        self._dispatch(super().do_GET)

    def do_HEAD(self):
        self._dispatch(super().do_HEAD)

    def log_message(self, fmt, *args):
        # Suppress noisy access logs in PM2 output.
        pass


if __name__ == "__main__":
    server = HTTPServer(("", PORT), SPAHandler)
    print(f"Dashboard serving on :{PORT} (SPA mode, root={SERVE_DIR})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
