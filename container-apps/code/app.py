"""W10 最終PJ：Azure Container Apps 上で動かす最小 FastAPI アプリ。

- GET /        : 挨拶メッセージ＋自分のホスト名（＝レプリカ識別）を JSON で返す。
                 スケール（W5）でレプリカが増えると hostname が変わるのを観察できる。
- GET /health  : ヘルスプローブ（W9）用。liveness/readiness の両方がこれを叩く。
- GET /info    : 環境変数の一部を返す（シークレット参照や設定注入の確認用、W8）。

環境変数：
- APP_GREETING : 挨拶文（Bicep の env で注入。既定値あり）
- PORT         : 待ち受けポート（Dockerfile / Bicep の targetPort と一致させる）
"""

import os
import socket

from fastapi import FastAPI

app = FastAPI(title="ACA Capstone", version="1.0.0")

# 挨拶文はコンテナ外（Bicep の env）から注入する。未設定でも動くよう既定値を持つ。
GREETING = os.environ.get("APP_GREETING", "Hello from Azure Container Apps")


@app.get("/")
def root() -> dict:
    # HOSTNAME はレプリカごとに異なる（＝どのレプリカが応答したか分かる）。
    return {
        "message": GREETING,
        "hostname": os.environ.get("HOSTNAME", socket.gethostname()),
    }


@app.get("/health")
def health() -> dict:
    # 200 を返せば healthy 判定（W9：HTTP プローブは 200-399 を成功とみなす）。
    # 実運用では依存先（DB 等）の疎通確認をここに書く。
    return {"status": "ok"}


@app.get("/info")
def info() -> dict:
    # 設定注入の確認用。機密値そのものは返さない（存在の有無だけ見せる）。
    return {
        "greeting_source": "env:APP_GREETING" if "APP_GREETING" in os.environ else "default",
        "port": os.environ.get("PORT", "8000"),
        "revision": os.environ.get("CONTAINER_APP_REVISION", "unknown"),
    }
