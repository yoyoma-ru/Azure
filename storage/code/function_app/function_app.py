"""Week 10 実装：Files API（Python v2 モデル）

Blob を upload / list / download し、必要なら User Delegation SAS を発行する。
- 認証：アクセスキーや接続文字列は使わず DefaultAzureCredential（Managed Identity）… Week 4
- SAS：アカウントキーではなく User Delegation SAS（Entra ID 署名・短期・読み取りのみ）… Week 4
"""
import json
import os
from datetime import datetime, timedelta, timezone

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas,
)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

ACCOUNT_URL = os.environ["STORAGE_ACCOUNT_URL"]          # 例: https://<acct>.blob.core.windows.net
CONTAINER = os.environ.get("UPLOAD_CONTAINER", "uploads")

# キーを持たず、ID ベースで認証（ローカルは az login、本番は Managed Identity）… Week 4
_credential = DefaultAzureCredential()
_service = BlobServiceClient(ACCOUNT_URL, credential=_credential)


def _container_client():
    return _service.get_container_client(CONTAINER)


@app.route(route="files", methods=["POST"])
def upload_file(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/files?name=<blob名>  本体＝Blob の中身をアップロード"""
    name = req.params.get("name")
    if not name:
        return _json({"error": "query param 'name' is required"}, 400)
    body = req.get_body()
    if not body:
        return _json({"error": "request body is empty"}, 400)

    blob = _container_client().get_blob_client(name)
    # SDK が分割・並列・commit を自動処理（Week 2）
    blob.upload_blob(body, overwrite=True)
    return _json({"uploaded": name, "size": len(body)}, 201)


@app.route(route="files", methods=["GET"])
def list_files(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/files  コンテナ内の Blob を一覧（イテレータで継続トークンを自動処理）… Week 3"""
    prefix = req.params.get("prefix")
    names = [b.name for b in _container_client().list_blobs(name_starts_with=prefix)]
    return _json({"container": CONTAINER, "count": len(names), "blobs": names}, 200)


@app.route(route="files/{name}", methods=["GET"])
def get_file(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/files/{name}        Blob をダウンロード
    GET /api/files/{name}?sas=1   ダウンロードの代わりに User Delegation SAS URL を返す
    """
    name = req.route_params.get("name")
    blob = _container_client().get_blob_client(name)
    if not blob.exists():
        return _json({"error": f"blob '{name}' not found"}, 404)

    if req.params.get("sas") == "1":
        return _json({"name": name, "sasUrl": _user_delegation_sas_url(name)}, 200)

    data = blob.download_blob().readall()
    return func.HttpResponse(body=data, status_code=200,
                             mimetype="application/octet-stream")


def _user_delegation_sas_url(name: str, minutes: int = 5) -> str:
    """User Delegation SAS（キー不使用・短期・読み取りのみ）を発行… Week 4"""
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(minutes=minutes)
    # アカウントキーではなく Entra ID 由来の委任キーで署名（最長7日・revoke 可能）
    udk = _service.get_user_delegation_key(key_start_time=now, key_expiry_time=expiry)
    token = generate_blob_sas(
        account_name=_service.account_name,
        container_name=CONTAINER,
        blob_name=name,
        user_delegation_key=udk,
        permission=BlobSasPermissions(read=True),  # 最小権限（読みのみ）… Week 4
        expiry=expiry,
        start=now,
    )
    return f"{ACCOUNT_URL}/{CONTAINER}/{name}?{token}"


def _json(obj: dict, status: int) -> func.HttpResponse:
    return func.HttpResponse(json.dumps(obj, ensure_ascii=False),
                             status_code=status, mimetype="application/json")
