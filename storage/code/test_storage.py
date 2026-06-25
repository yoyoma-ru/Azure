"""Week 10 実装：E2E テスト

Files API（Functions）に対して以下を検証する：
  1. アップロード（POST /api/files）          → 201
  2. 一覧に出る（GET /api/files）             → アップロードした名前が含まれる
  3. ダウンロードで内容一致（GET /api/files/{name}）
  4. （任意）User Delegation SAS の URL が返り、その URL で読める

実行前に環境変数を設定する：
  export FUNC_BASE_URL="https://<your-func-app>.azurewebsites.net/api"
  export FUNC_KEY="<function key>"   # AuthLevel.FUNCTION のため
"""
import os
import time

import requests

BASE = os.environ["FUNC_BASE_URL"].rstrip("/")
KEY = os.environ.get("FUNC_KEY", "")
PARAMS = {"code": KEY} if KEY else {}

BLOB_NAME = f"e2e/test-{int(time.time())}.txt"
CONTENT = b"hello azure storage week10"


def _p(extra=None):
    p = dict(PARAMS)
    if extra:
        p.update(extra)
    return p


def main() -> None:
    # 1. アップロード -> 201
    r = requests.post(f"{BASE}/files", params=_p({"name": BLOB_NAME}), data=CONTENT)
    assert r.status_code == 201, f"upload failed: {r.status_code} {r.text}"
    print("1. upload OK:", r.json())

    # 2. 一覧に出る
    r = requests.get(f"{BASE}/files", params=_p())
    assert r.status_code == 200, f"list failed: {r.status_code} {r.text}"
    names = r.json()["blobs"]
    assert BLOB_NAME in names, f"{BLOB_NAME} not in list: {names}"
    print("2. list OK: found", BLOB_NAME)

    # 3. ダウンロードで内容一致
    r = requests.get(f"{BASE}/files/{BLOB_NAME}", params=_p())
    assert r.status_code == 200, f"download failed: {r.status_code} {r.text}"
    assert r.content == CONTENT, f"content mismatch: {r.content!r}"
    print("3. download OK: content matches")

    # 4. User Delegation SAS の URL が返り、その URL 単体で読める
    r = requests.get(f"{BASE}/files/{BLOB_NAME}", params=_p({"sas": "1"}))
    assert r.status_code == 200, f"sas failed: {r.status_code} {r.text}"
    sas_url = r.json()["sasUrl"]
    # SAS URL は Function キー無しでも、署名だけで直接 Blob にアクセスできる
    r2 = requests.get(sas_url)
    assert r2.status_code == 200, f"sas access failed: {r2.status_code} {r2.text}"
    assert r2.content == CONTENT, "sas content mismatch"
    print("4. SAS OK: direct blob access works")

    print("\nAll E2E assertions passed.")


if __name__ == "__main__":
    main()
