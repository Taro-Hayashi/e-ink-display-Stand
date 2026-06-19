# image-render （[日本語](README_JP.md)）

Mac-side scripts for fetching NASA Astronomy Picture of the Day (APOD), rendering an e-paper image, and serving it over HTTP. `fetch_apod.py` downloads APOD metadata and image data, and `apod_api.py` serves the rendered image for the XIAO ESP32C3.

## Files

- `fetch_apod.py`: Fetches APOD metadata and image data from the NASA APOD API, then saves `apod_state.json` and files under `cache/`.
- `apod_api.py`: Serves text, JSON, PNG preview, and packed e-paper binary data.
- `render_apod_image.py`: Renders a 122x250 black/red two-plane image.
- `config.example.json`: Template for `config.json`.
- `requirements.txt`: Python dependencies.

## Setup

```bash
python3 -m pip install -r requirements.txt
cp config.example.json config.json
```

Set your NASA API key in `config.json`. The public sample uses `DEMO_KEY`, but a personal NASA Open APIs key is recommended to avoid shared rate limits.

If you see `HTTP Error 429` or `HTTP Error 503`, the NASA API may be temporarily unavailable or the shared `DEMO_KEY` limit may have been reached. Wait and retry, or set your own NASA API key in `config.json`.

## Run

Fetch APOD:

```bash
python3 fetch_apod.py
```

Fetch a specific date:

```bash
python3 fetch_apod.py --date 2024-04-08
```

Start the HTTP server:

```bash
python3 apod_api.py --host 0.0.0.0 --port 8765
```

## Endpoints

- `http://localhost:8765/apod.txt`
- `http://localhost:8765/apod.json`
- `http://localhost:8765/apod_image.png`
- `http://localhost:8765/apod_image.bin`

`/apod_image.bin` is the black plane plus red plane binary fetched by the XIAO ESP32C3. `/apod_image.png` is a local preview image.

## Image Conversion

APOD images are converted to black-and-white dithering, with small accents such as `NASA` placed on the red plane. If the APOD entry is a video or image fetching fails, the renderer uses a placeholder image.

## Ignored Files

- `config.json`: NASA API key.
- `apod_state.json`: Latest APOD metadata.
- `cache/`: APOD image cache.
- `*.log`, `*.err`, `__pycache__/`
