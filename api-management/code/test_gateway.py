"""
Week 10 E2E テスト：APIM ゲートウェイ経由の挙動を検証する。

検証内容（学習プランの Verification）:
  1. キー付き        -> 200（正常）
  2. キーなし        -> 401（サブスクリプションキー必須・Week 2）
  3. 連打            -> 429（rate-limit-by-key・Week 4）

事前に環境変数を設定:
  export APIM_GATEWAY_URL="https://<apim>.azure-api.net/store"   # Bicep の出力 apimGatewayUrl
  export APIM_SUBSCRIPTION_KEY="<starter-sub の primaryKey>"

サブスクリプションキーの取得（CLI 例）:
  az apim subscription show ... もしくはポータルの Subscriptions から primaryKey をコピー

実行:
  pip install requests
  python test_gateway.py
"""
import os
import sys
import requests

BASE = os.environ.get("APIM_GATEWAY_URL")
KEY = os.environ.get("APIM_SUBSCRIPTION_KEY")

if not BASE or not KEY:
    sys.exit("環境変数 APIM_GATEWAY_URL と APIM_SUBSCRIPTION_KEY を設定してください")

HEADERS = {"Ocp-Apim-Subscription-Key": KEY}


def check(label: str, got: int, expected: int) -> bool:
    ok = got == expected
    mark = "OK " if ok else "NG "
    print(f"[{mark}] {label}: status={got}（期待 {expected}）")
    return ok


results = []

# 1. キー付き -> 200
r = requests.get(f"{BASE}/orders/42", headers=HEADERS)
results.append(check("キー付き GET /orders/42", r.status_code, 200))
if r.status_code == 200:
    print("       body:", r.text)
    print("       X-Powered-By:", r.headers.get("X-Powered-By"))  # outbound ポリシー(Week 4)

# 2. キーなし -> 401
r = requests.get(f"{BASE}/orders/42")
results.append(check("キーなし GET /orders/42", r.status_code, 401))

# 3. 連打 -> 429（5回/30秒の制限を超える）
print("--- レート制限テスト（8回連打）---")
got_429 = False
for i in range(8):
    r = requests.get(f"{BASE}/orders/42", headers=HEADERS)
    remaining = r.headers.get("X-RateLimit-Remaining", "-")
    print(f"  {i + 1}回目: status={r.status_code} 残り={remaining}")
    if r.status_code == 429:
        got_429 = True
results.append(check("連打でレート制限", 429 if got_429 else 200, 429))

print("\n=== 結果:", "全て成功 ✅" if all(results) else "失敗あり ❌", "===")
sys.exit(0 if all(results) else 1)
