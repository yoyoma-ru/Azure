"""
Week 10 バックエンド：Orders API（Azure Functions・Python v2 モデル）

ルートは既定で /api が前置される（host.json で変更可）。
  GET  /api/orders/{id}   注文を1件取得
  GET  /api/orders        注文一覧
  POST /api/orders        注文を作成

APIM 側の serviceUrl は「https://<func>.azurewebsites.net/api」を指す想定。
学習デモのため authLevel は ANONYMOUS（誰でも呼べる）。
本番では Function キーや Entra 認証(Easy Auth)+ APIM の Managed Identity を使う。
"""
import json
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# 簡易のインメモリ・データ（学習用）
ORDERS: dict[str, dict] = {
    "42": {"orderId": 42, "item": "コーヒー豆", "quantity": 2, "status": "shipped"},
    "43": {"orderId": 43, "item": "紅茶", "quantity": 1, "status": "pending"},
}
_next_id = 44


def _json(body: dict | list, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(body, ensure_ascii=False),
        status_code=status,
        mimetype="application/json",
    )


@app.route(route="orders/{id}", methods=["GET"])
def get_order(req: func.HttpRequest) -> func.HttpResponse:
    order_id = req.route_params.get("id")
    order = ORDERS.get(order_id)
    if order is None:
        return _json({"error": f"order {order_id} not found"}, status=404)
    return _json(order)


@app.route(route="orders", methods=["GET"])
def list_orders(req: func.HttpRequest) -> func.HttpResponse:
    return _json(list(ORDERS.values()))


@app.route(route="orders", methods=["POST"])
def create_order(req: func.HttpRequest) -> func.HttpResponse:
    global _next_id
    try:
        payload = req.get_json()
    except ValueError:
        return _json({"error": "invalid JSON body"}, status=400)

    order = {
        "orderId": _next_id,
        "item": payload.get("item", "unknown"),
        "quantity": payload.get("quantity", 1),
        "status": "pending",
    }
    ORDERS[str(_next_id)] = order
    _next_id += 1
    return _json(order, status=201)
