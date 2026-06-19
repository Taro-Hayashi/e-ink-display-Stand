#!/usr/bin/env python3
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO

from render_apod_image import render_apod_image, render_apod_planes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "apod_state.json")


def load_state():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "title": "NASA APOD",
            "date": None,
            "explanation": "Run fetch_apod.py first.",
            "image_path": None,
        }


def build_text(payload):
    lines = [
        payload.get("title") or "NASA APOD",
    ]
    if payload.get("date"):
        lines.append(payload["date"])
    if payload.get("copyright"):
        lines.append(f"Credit: {payload['copyright']}")
    return "\n".join(lines) + "\n"


class ApodHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/apod.json", "/apod.txt", "/apod_image.bin", "/apod_image.png"):
            self.send_error(404)
            return

        payload = load_state()
        if self.path == "/apod.json":
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        elif self.path == "/apod_image.bin":
            body = render_apod_planes(payload)
            content_type = "application/octet-stream"
        elif self.path == "/apod_image.png":
            output = BytesIO()
            render_apod_image(payload).save(output, format="PNG")
            body = output.getvalue()
            content_type = "image/png"
        else:
            body = build_text(payload).encode("utf-8")
            content_type = "text/plain; charset=utf-8"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"{self.client_address[0]} - {fmt % args}")


def main():
    parser = argparse.ArgumentParser(description="Serve NASA APOD e-paper images for local devices.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), ApodHandler)
    print(f"Serving APOD API on http://{args.host}:{args.port}/apod_image.png")
    server.serve_forever()


if __name__ == "__main__":
    main()
