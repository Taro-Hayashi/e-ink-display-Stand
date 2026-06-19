# AGENTS.md

## プロジェクト概要

NASA Astronomy Picture of the Day (APOD) の電子ペーパー表示システム。Mac 側の `image-render/` でAPODメタデータと画像を取得し、電子ペーパー用画像 (`/apod_image.bin`) をHTTP配信する。XIAO ESP32C3 側の `xiao-esp32c3-display/` がその画像を取得し、2.13インチ 3色電子ペーパー (SSD1680, 122×250, 黒/赤/白) に表示する。

## ターゲットハードウェア

- **XIAO ESP32C3** (Seeed Studio) — LiPo 充電対応モデル
- **電子ペーパー**: 2.13" 3色 (SSD1680 / GxEPD2_213_Z98c)
- 元は Raspberry Pi Pico W 向けに実装されていたが、現行構成では Pico W 版は含めない。

## ディレクトリ構成

```
e-ink-display-Stand/
├── image-render/               # Mac 側: APOD取得、画像生成、HTTP配信
│   ├── fetch_apod.py           # APODメタデータと画像を取得
│   ├── apod_api.py             # /apod_image.bin などを配信
│   ├── render_apod_image.py    # 122x250 の黒/赤2プレーン画像を生成
│   ├── config.example.json     # config.json のテンプレート
│   ├── config.json             # .gitignore 対象
│   ├── apod_state.json         # .gitignore 対象
│   └── cache/                  # .gitignore 対象
├── xiao-esp32c3-display/ # XIAO ESP32C3 向け Arduino スケッチ
│   ├── xiao-esp32c3-display.ino
│   ├── config.example.h       # secrets.h と同内容のテンプレート
│   ├── secrets.h              # 公開用サンプル設定
│   └── assets/                # 将来の固定画像用
├── step/                       # 公開用3Dモデル (CC0)
├── plasticity-private/         # 非公開CAD作業ファイル (.gitignore 対象)
└── README.md
```

## コーディングルール

- Arduino スケッチ (.ino) は C++ スタイルで記述する。
- XIAO側の `secrets.h` は公開用サンプル値 (`your-wifi-ssid`, `your-image-host` 等) のみを置く。実SSIDや実パスワードを入れた場合はコミットしない。
- Mac 側のNASA APIキー、取得状態、画像キャッシュは `image-render/config.json`, `image-render/apod_state.json`, `image-render/cache/` に分離し、git 管理外とする。テンプレートは `image-render/config.example.json`。
- `constexpr` を使い `#define` による定数定義は `secrets.h` のみに限定する。
- ピン番号は Arduino のピンラベル定数 (`D0`, `D1` 等) を使用し、生の GPIO 番号はコメントで補足する。

## XIAO ESP32C3 ピンマッピング

| 機能 | XIAO ピン | GPIO |
|---|---|---|
| EPD_BUSY | D0 | GPIO2 |
| EPD_RST | D1 | GPIO3 |
| EPD_DC | D2 | GPIO4 |
| EPD_CS | D3 | GPIO5 |
| SPI SCK | D8 | GPIO8 (デフォルト) |
| SPI MOSI | D10 | GPIO10 (デフォルト) |

## 動作仕様

1. Mac 側で `fetch_apod.py` がNASA APOD APIからメタデータと画像を取得し、`apod_state.json` と `cache/` を更新する
2. Mac 側で `apod_api.py` が `/apod.txt`, `/apod.json`, `/apod_image.png`, `/apod_image.bin` を配信する
3. XIAO ESP32C3 が起動 → WiFi 接続 → `/apod_image.bin` を HTTP GET で取得
4. 黒プレーン + 赤プレーンに分離して電子ペーパーに描画
5. WiFi を停止し、12時間の deep sleep に入る
6. タイマー起床 → `setup()` から再実行

## 注意事項

- `secrets.h` に実SSID、実パスワード、実ホスト名を入れた状態では絶対にコミットしない。
- `image-render/config.json`, `image-render/apod_state.json`, `image-render/cache/` は絶対にコミットしない。
- `plasticity-private/` は非公開の作業ファイル置き場なので絶対にコミットしない。
- コードとドキュメントはMIT、`step/` 以下の3DモデルはCC0として扱う。
- `image-render/render_apod_image.py` はAPOD画像を白黒ディザ化し、アクセントだけ赤プレーンに載せる。
- deep sleep 中は RAM 内容が失われるため、状態保持が必要な場合は `RTC_DATA_ATTR` を使用する。
