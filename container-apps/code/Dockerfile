# W10 最終PJ：FastAPI アプリのコンテナイメージ。
# ACA は linux/amd64 の Linux イメージのみ対応（W2 の制限）。
# ARM Mac 等でローカルビルドする場合は buildx で --platform linux/amd64 を指定するか、
# クラウドビルド（az acr build。既定で linux/amd64）を使う（README 参照）。
FROM python:3.12-slim

WORKDIR /app

# 依存だけ先に入れてレイヤキャッシュを効かせる
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# 既定ポート。Bicep の targetPort / env PORT と一致させること。
ENV PORT=8000
EXPOSE 8000

# シェル形式で ${PORT} を展開して uvicorn を起動（0.0.0.0 で待受＝コンテナ外から到達可能に）
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
