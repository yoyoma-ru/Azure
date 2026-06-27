"""Week 9 実装：Items API（Python v2 モデル）— Cache-Aside パターン

Azure Managed Redis を「読み取りキャッシュ」として使い、Cache-Aside（Week 3）を実装する。
  GET    /api/items/{id}   1件取得。Redis ヒットなら即返す／ミスなら擬似DBから取り Redis に書く
  DELETE /api/items/{id}   キャッシュを無効化（次の GET は再びミス＝再充填）… Week 3

認証（Week 7）：
  - アクセスキーは使わず Microsoft Entra ID（DefaultAzureCredential）でトークン認証する。
  - ローカルは az login、本番は Functions のマネージドID が使われる。
  - Managed Redis は常に TLS 必須・既定ポート 10000。
"""
import json
import os
import time

import azure.functions as func
import redis
from redis_entraid.cred_provider import create_from_default_azure_credential

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

REDIS_HOST = os.environ["REDIS_HOST_NAME"]                 # 例: <name>.<region>.redis.azure.net
REDIS_PORT = int(os.environ.get("REDIS_PORT", "10000"))    # Managed Redis 既定は 10000
TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "60"))  # Week 3：TTL を短く保ち陳腐化を防ぐ

# Entra ID（キーレス）でトークンを取得し、期限が来たら背後で自動更新する … Week 7
_cred_provider = create_from_default_azure_credential(("https://redis.azure.com/.default",))

# 接続は使い回す（毎リクエスト張り直さない）。TLS 必須なので ssl=True。
_r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    ssl=True,
    decode_responses=True,
    credential_provider=_cred_provider,
    socket_timeout=10,
    socket_connect_timeout=10,
)

# 擬似データベース（学習用・本来は RDB などの真実源）… Week 3 でいう「遅い元データ」
_DB: dict[str, dict] = {
    "42": {"id": "42", "name": "Coffee", "price": 380},
    "43": {"id": "43", "name": "Tea", "price": 320},
}


def _db_lookup(item_id: str) -> dict | None:
    """遅い元データの取得を模す（実DBアクセス相当・わざと少し待つ）。"""
    time.sleep(0.05)
    return _DB.get(item_id)


@app.route(route="items/{id}", methods=["GET"])
def get_item(req: func.HttpRequest) -> func.HttpResponse:
    """Cache-Aside の読み取り：キャッシュ→ミスなら元データ→キャッシュ充填 … Week 3"""
    item_id = req.route_params.get("id")
    key = f"item:{item_id}"

    cached = _r.get(key)
    if cached is not None:
        # ヒット：Redis の値をそのまま返す（元データには触らない）
        body = json.loads(cached)
        return _json({"item": body, "cache": "hit", "ttl": _r.ttl(key)}, 200)

    # ミス：元データを引き、あれば TTL 付きで書き戻す（SETEX 相当）… Week 3/4
    item = _db_lookup(item_id)
    if item is None:
        return _json({"error": f"item '{item_id}' not found"}, 404)

    _r.set(key, json.dumps(item, ensure_ascii=False), ex=TTL_SECONDS)
    return _json({"item": item, "cache": "miss", "ttl": TTL_SECONDS}, 200)


@app.route(route="items/{id}", methods=["DELETE"])
def invalidate_item(req: func.HttpRequest) -> func.HttpResponse:
    """キャッシュ無効化：元データを更新したとき陳腐なキャッシュを消す … Week 3"""
    item_id = req.route_params.get("id")
    deleted = _r.delete(f"item:{item_id}")
    return _json({"invalidated": item_id, "removed": bool(deleted)}, 200)


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Redis への疎通確認（PING）。接続・認証が通っているかの簡易チェック。"""
    return _json({"redis": _r.ping()}, 200)


def _json(obj: dict, status: int) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(obj, ensure_ascii=False),
        status_code=status,
        mimetype="application/json",
    )
