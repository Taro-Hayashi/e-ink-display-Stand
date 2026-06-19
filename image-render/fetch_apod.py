#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATE_PATH = os.path.join(BASE_DIR, "apod_state.json")
CACHE_DIR = os.path.join(BASE_DIR, "cache")

APOD_ENDPOINT = "https://api.nasa.gov/planetary/apod"
RETRY_HTTP_STATUSES = {429, 500, 502, 503, 504}


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


class FetchError(Exception):
    pass


def fetch_url(url, attempts=3):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "apod-eink-display/1.0",
        },
    )

    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read(), response.headers.get_content_type()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace").strip()
            message = f"HTTP {e.code} {e.reason}"
            if body:
                message = f"{message}: {body[:300]}"
            last_error = FetchError(message)
            if e.code not in RETRY_HTTP_STATUSES or attempt == attempts:
                break
        except urllib.error.URLError as e:
            last_error = FetchError(f"Network error: {e.reason}")
            if attempt == attempts:
                break

        wait_seconds = 2 * attempt
        print(f"Fetch failed ({last_error}). Retrying in {wait_seconds}s...", file=sys.stderr)
        time.sleep(wait_seconds)

    raise last_error


def fetch_json(url):
    body, _ = fetch_url(url)
    return json.loads(body.decode("utf-8"))


def choose_image_url(apod):
    if apod.get("media_type") == "image":
        return apod.get("hdurl") or apod.get("url")
    return apod.get("thumbnail_url")


def extension_from_content_type(content_type):
    if content_type == "image/png":
        return ".png"
    if content_type in ("image/jpeg", "image/jpg"):
        return ".jpg"
    if content_type == "image/gif":
        return ".gif"
    return ".img"


def build_apod_url(config, requested_date=None):
    params = {
        "api_key": config.get("api_key", "DEMO_KEY"),
        "thumbs": "true",
    }
    if requested_date:
        params["date"] = requested_date
    return f"{APOD_ENDPOINT}?{urllib.parse.urlencode(params)}"


def update_apod(requested_date=None):
    config = load_json(CONFIG_PATH, {})
    apod = fetch_json(build_apod_url(config, requested_date))
    image_url = choose_image_url(apod)
    image_path = None

    os.makedirs(CACHE_DIR, exist_ok=True)

    if image_url:
        image_data, content_type = fetch_url(image_url)
        apod_date = apod.get("date") or date.today().isoformat()
        image_path = os.path.join(CACHE_DIR, f"apod-{apod_date}{extension_from_content_type(content_type)}")
        with open(image_path, "wb") as f:
            f.write(image_data)

    state = {
        "date": apod.get("date"),
        "title": apod.get("title", "NASA APOD"),
        "explanation": apod.get("explanation", ""),
        "media_type": apod.get("media_type"),
        "service_version": apod.get("service_version"),
        "url": apod.get("url"),
        "hdurl": apod.get("hdurl"),
        "copyright": apod.get("copyright"),
        "image_path": image_path,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    save_json(STATE_PATH, state)
    return state


def main():
    parser = argparse.ArgumentParser(description="Fetch NASA Astronomy Picture of the Day for the e-paper display.")
    parser.add_argument("--date", help="Fetch a specific APOD date in YYYY-MM-DD format.")
    args = parser.parse_args()

    try:
        state = update_apod(args.date)
    except FetchError as e:
        print(f"Failed to fetch APOD: {e}", file=sys.stderr)
        print("If you are using DEMO_KEY, create a free NASA API key and put it in config.json.", file=sys.stderr)
        if os.path.exists(STATE_PATH):
            print(f"Existing cache remains available: {STATE_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetched APOD: {state.get('date')} - {state.get('title')}")
    if state.get("image_path"):
        print(f"Cached image: {state['image_path']}")
    else:
        print("No image was available; the renderer will use a placeholder.")


if __name__ == "__main__":
    main()
