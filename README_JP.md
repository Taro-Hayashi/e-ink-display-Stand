# E-ink APOD Display （[English](README.md)）

![E-ink APOD Display](docs/images/apod-display.jpeg)

NASA Astronomy Picture of the Day (APOD) をMacで取得し、XIAO ESP32C3 + 2.13インチ3色電子ペーパーへ表示するローカル表示システム。  
MakerWorld: [E-ink Display Stand](https://makerworld.com/ja/models/2952512)

- WeAct 2.13-Black-White-Red（3色のディスプレイです）
- XIAO ESP32C3
- LiPo 602040

## 構成

- `image-render/`: Mac側。NASA APODを取得し、電子ペーパー用画像を生成してHTTP配信する。
- `xiao-esp32c3-display/`: XIAO ESP32C3側。Macの `/apod_image.bin` を取得して電子ペーパーへ描画し、12時間 deep sleep する。

## セットアップ概要

### Mac側

```bash
cd image-render
python3 -m pip install -r requirements.txt
cp config.example.json config.json
python3 fetch_apod.py
python3 apod_api.py --host 0.0.0.0 --port 8765
```

配信エンドポイント:

- `http://localhost:8765/apod.txt`
- `http://localhost:8765/apod.json`
- `http://localhost:8765/apod_image.png`
- `http://localhost:8765/apod_image.bin`

### XIAO ESP32C3側

```bash
cd xiao-esp32c3-display
```

`secrets.h` に Wi-Fi SSID、パスワード、Macのホスト名またはIPアドレスを設定し、Arduino IDE で `xiao-esp32c3-display.ino` を書き込む。

## 管理外ファイル

- `image-render/config.json`
- `image-render/apod_state.json`
- `image-render/cache/`
- `plasticity-private/`

## 3Dモデル

`step/` に公開用の3Dモデルを置く。編集や寸法確認にはSTEP、スライサーへの読み込みには3MFを使う。

Plasticityの作業ファイルは `plasticity-private/` に置き、公開対象には含めない。

## ライセンス

- コードとドキュメント: MIT License。詳細は `LICENSE`。
- `step/` 以下の3Dモデル: CC0 1.0 Universal。詳細は `step/LICENSE`。
