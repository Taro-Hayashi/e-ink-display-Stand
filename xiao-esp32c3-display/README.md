# xiao-esp32c3-display （[日本語](README_JP.md)）

Arduino sketch for showing NASA Astronomy Picture of the Day (APOD) on a XIAO ESP32C3 with a 2.13-inch three-color e-paper display (SSD1680 / GxEPD2_213_Z98c). It fetches `/apod_image.bin` served by `../image-render/apod_api.py` every 12 hours, draws the image, and then enters deep sleep.

## Setup

1. Edit `secrets.h` with your Wi-Fi credentials and Mac-side API host.

```cpp
#define WIFI_SSID "your-wifi-ssid"
#define WIFI_PASSWORD "your-wifi-password"
#define IMAGE_HOST "your-image-host"
#define IMAGE_PORT 8765
#define IMAGE_PATH "/apod_image.bin"
```

2. Select the XIAO ESP32C3 board in the Arduino IDE and upload `xiao-esp32c3-display.ino`.

## Mac Side

First run `fetch_apod.py` in `../image-render/` to create `apod_state.json` and the image cache, then start `apod_api.py --host 0.0.0.0 --port 8765`.

`/apod_image.bin` is a 122x250 black plane plus red plane binary. The sketch reads `EPD_IMAGE_BYTES` bytes from that endpoint.

## Behavior

- Boot -> connect to Wi-Fi -> fetch `/apod_image.bin` -> draw to e-paper -> stop Wi-Fi -> enter deep sleep for 12 hours.
- If fetching fails, the sketch retries once, shows a failure message on the e-paper display, and then enters deep sleep.
- RAM contents are lost during deep sleep.

## Wiring

| Function | XIAO pin | GPIO |
|---|---|---|
| EPD_BUSY | D0 | GPIO2 |
| EPD_RST | D1 | GPIO3 |
| EPD_DC | D2 | GPIO4 |
| EPD_CS | D3 | GPIO5 |
| SPI SCK | D8 | GPIO8 |
| SPI MOSI | D10 | GPIO10 |

## Display Image

The Mac-side `render_apod_image.py` converts the APOD image into a 122x250 black-and-white dithered image and serves small accents on the red plane.
