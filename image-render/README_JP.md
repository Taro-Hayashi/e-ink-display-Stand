# image-render （[English](README.md)）

Mac側で動かすNASA Astronomy Picture of the Day (APOD) 取得・画像生成・HTTP配信用スクリプト群。`fetch_apod.py` がAPODメタデータと画像を取得し、`apod_api.py` がXIAO ESP32C3向けの電子ペーパー画像を配信する。

## ファイル

- `fetch_apod.py`: NASA APOD APIからメタデータと画像を取得し、`apod_state.json` と `cache/` に保存する。
- `apod_api.py`: テキスト、JSON、PNGプレビュー、電子ペーパー用バイナリをHTTP配信する。
- `render_apod_image.py`: 122x250 の黒/赤2プレーン画像を生成する。
- `config.example.json`: `config.json` のテンプレート。
- `requirements.txt`: Python依存関係。

## セットアップ

```bash
python3 -m pip install -r requirements.txt
cp config.example.json config.json
```

`config.json` にはNASA APIキーを設定する。公開サンプルとしては `DEMO_KEY` のまま動作するが、利用制限を避ける場合はNASA Open APIsで取得したキーを指定する。

`HTTP Error 429` や `HTTP Error 503` が出る場合は、NASA API側の一時エラーまたは `DEMO_KEY` の共有制限の可能性がある。少し待って再実行するか、自分のNASA APIキーを `config.json` に設定する。

## 実行

APODを取得:

```bash
python3 fetch_apod.py
```

特定日付を取得:

```bash
python3 fetch_apod.py --date 2024-04-08
```

HTTPサーバーを起動:

```bash
python3 apod_api.py --host 0.0.0.0 --port 8765
```

## エンドポイント

- `http://localhost:8765/apod.txt`
- `http://localhost:8765/apod.json`
- `http://localhost:8765/apod_image.png`
- `http://localhost:8765/apod_image.bin`

`/apod_image.bin` はXIAO ESP32C3が取得する黒プレーン + 赤プレーンの連結データ。`/apod_image.png` はMac上でのレイアウト確認用。

## 画像変換

APOD画像は白黒ディザに変換し、ヘッダーの `NASA` など一部だけ赤プレーンに載せる。APODが動画の日や画像取得に失敗した場合は、プレースホルダー画像を表示する。

## 管理外ファイル

- `config.json`: NASA APIキー。
- `apod_state.json`: 直近のAPODメタデータ。
- `cache/`: APOD画像キャッシュ。
- `*.log`, `*.err`, `__pycache__/`
