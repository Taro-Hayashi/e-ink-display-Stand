# xiao-esp32c3-display （[English](README.md)）

XIAO ESP32C3 + 2.13インチ3色電子ペーパー (SSD1680 / GxEPD2_213_Z98c) でNASA Astronomy Picture of the Day (APOD) を表示するArduinoスケッチ。Mac側の `../image-render/apod_api.py` が配信する `/apod_image.bin` を12時間ごとに取得し、描画後に deep sleep する。

## セットアップ

1. `secrets.h` にWi-FiとMac側APIの接続先を設定する。

```cpp
#define WIFI_SSID "your-wifi-ssid"
#define WIFI_PASSWORD "your-wifi-password"
#define IMAGE_HOST "your-image-host"
#define IMAGE_PORT 8765
#define IMAGE_PATH "/apod_image.bin"
```

2. Arduino IDEでXIAO ESP32C3ボードを選択し、`xiao-esp32c3-display.ino` を書き込む。

## Mac側

先に `../image-render/` で `fetch_apod.py` を実行して `apod_state.json` と画像キャッシュを作成し、`apod_api.py --host 0.0.0.0 --port 8765` を起動する。

`/apod_image.bin` は 122x250 の黒プレーンと赤プレーンを連結したデータで、スケッチ側では `EPD_IMAGE_BYTES` 分を読み込む。

## 動作

- 起動 → WiFi接続 → `/apod_image.bin` 取得 → 電子ペーパー描画 → WiFi停止 → 12時間 deep sleep
- 取得に失敗した場合は1回リトライし、失敗メッセージを電子ペーパーへ表示して deep sleep する
- deep sleep中はRAM内容が失われる

## 配線

| 機能 | XIAOピン | GPIO |
|---|---|---|
| EPD_BUSY | D0 | GPIO2 |
| EPD_RST | D1 | GPIO3 |
| EPD_DC | D2 | GPIO4 |
| EPD_CS | D3 | GPIO5 |
| SPI SCK | D8 | GPIO8 |
| SPI MOSI | D10 | GPIO10 |

## 表示画像

Mac側の `render_apod_image.py` が、APOD画像を122x250の白黒ディザ画像へ変換し、一部アクセントだけ赤プレーンとして配信する。
