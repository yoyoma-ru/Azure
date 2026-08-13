"""環境変数から設定を読み込む（W8：接続文字列はコードに直書きしない）。

必要な環境変数（.env または export で設定）:
  NH_CONNECTION_STRING  ハブレベルの接続文字列（例：DefaultFullSharedAccessSignature）
  NH_HUB_NAME           ハブ名（例：hub-demo）

接続文字列は az CLI で取得する（README 参照）。
"""
import os

from dotenv import load_dotenv

load_dotenv()  # カレントの .env を読む（あれば）

CONNECTION_STRING = os.environ.get("NH_CONNECTION_STRING", "")
HUB_NAME = os.environ.get("NH_HUB_NAME", "hub-demo")

if not CONNECTION_STRING:
    raise SystemExit(
        "環境変数 NH_CONNECTION_STRING が未設定です。README の手順で接続文字列を設定してください。"
    )
