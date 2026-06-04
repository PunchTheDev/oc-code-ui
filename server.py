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

    def do_GET(self):
        # Strip query string for filesystem lookup.
        path = self.path.split("?")[0].split("#")[0].rstrip("/") or "/"
        candidate = SERVE_DIR / path.lstrip("/")

        # Redirect known SPA routes to their hash-based equivalents so that
        # pasted-in URLs like /problems land on the correct page.
        if path in SPA_ROUTES:
            self.send_response(301)
            self.send_header("Location", SPA_ROUTES[path])
            self.end_headers()
            return

        # Serve file directly if it exists.
        if candidate.is_file():
            return super().do_GET()

        # Serve directory index if it exists.
        if candidate.is_dir() and (candidate / "index.html").exists():
            self.path = path.rstrip("/") + "/index.html"
            return super().do_GET()

        # SPA fallback — any path with a recognised static extension that
        # doesn't exist is a real 404; everything else gets index.html.
        ext = Path(path).suffix.lower()
        if ext and ext in STATIC_EXTS:
            self.send_error(404, f"File not found: {path}")
            return

        # Rewrite to index.html for SPA routing.
        self.path = "/index.html"
        super().do_GET()

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
