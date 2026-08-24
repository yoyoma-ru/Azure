"""最小の FastAPI サンプルアプリ（Azure DevOps 学習 W10 用）。

エンドポイント:
  GET /         あいさつを返す
  GET /health   ヘルスチェック（W5: environment health / readiness 相当）
  GET /version  APP_VERSION 環境変数を返す（W5: 環境ごとに変わる変数の例）
"""
import os

from fastapi import FastAPI

app = FastAPI(title="azure-devops-capstone", version="1.0.0")


@app.get("/")
def root() -> dict:
    return {"message": "Hello from Azure DevOps capstone"}


@app.get("/health")
def health() -> dict:
    # デプロイ先の生存確認に使う。常に ok を返す最小実装。
    return {"status": "ok"}


@app.get("/version")
def version() -> dict:
    # APP_VERSION は Variable Group / 環境変数から注入される想定（未設定なら dev）。
    return {"version": os.environ.get("APP_VERSION", "dev")}
