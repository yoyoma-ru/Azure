"""Week 9 実装：E2E テスト

Items API（Functions）に対して Cache-Aside の挙動を検証する：
  1. 1回目 GET /api/items/{id}      → 200・cache="miss"（元データから充填）… Week 3
  2. 2回目 GET /api/items/{id}      → 200・cache="hit"（Redis から即返す）… Week 3
  3. DELETE /api/items/{id}         → 200（キャッシュ無効化）… Week 3
  4. 無効化後の GET                  → 再び cache="miss"（再充填される）

実行前に環境変数を設定する：
  export FUNC_BASE_URL="https://<your-func-app>.azurewebsites.net/api"
  export FUNC_KEY="<function key>"   # AuthLevel.FUNCTION のため
"""
import os

import requests

BASE = os.environ["FUNC_BASE_URL"].rstrip("/")
KEY = os.environ.get("FUNC_KEY", "")
PARAMS = {"code": KEY} if KEY else {}

ITEM_ID = "42"


def main() -> None:
    # 1. 1回目 GET -> miss（元データから Redis に充填）
    r = requests.get(f"{BASE}/items/{ITEM_ID}", params=PARAMS)
    assert r.status_code == 200, f"1st get failed: {r.status_code} {r.text}"
    assert r.json()["cache"] == "miss", f"expected miss, got {r.json()}"
    print("1. first GET OK: cache=miss（充填された）")

    # 2. 2回目 GET -> hit（Redis から返る）
    r = requests.get(f"{BASE}/items/{ITEM_ID}", params=PARAMS)
    assert r.status_code == 200, f"2nd get failed: {r.status_code} {r.text}"
    assert r.json()["cache"] == "hit", f"expected hit, got {r.json()}"
    print("2. second GET OK: cache=hit（キャッシュから即返した）")

    # 3. DELETE -> キャッシュ無効化
    r = requests.delete(f"{BASE}/items/{ITEM_ID}", params=PARAMS)
    assert r.status_code == 200, f"delete failed: {r.status_code} {r.text}"
    print("3. DELETE OK: invalidated", r.json())

    # 4. 無効化後の GET -> 再び miss
    r = requests.get(f"{BASE}/items/{ITEM_ID}", params=PARAMS)
    assert r.status_code == 200, f"post-invalidation get failed: {r.status_code} {r.text}"
    assert r.json()["cache"] == "miss", f"expected miss after invalidation, got {r.json()}"
    print("4. GET after invalidation OK: cache=miss（再充填された）")

    print("\nAll E2E assertions passed.")


if __name__ == "__main__":
    main()
