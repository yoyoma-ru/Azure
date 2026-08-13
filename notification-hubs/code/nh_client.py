"""Azure Notification Hubs の最小クライアント（REST + SAS 署名）。

Notification Hubs の「送信（データプレーン）」には公式の Python SDK が無いため、
REST API を直接叩く。SAS トークンは自前で生成する（W8）。
これにより W2（PNS）〜W9（監視）で学んだ流れを 1 本のコードで体験する。

参照：
  - SAS 生成: https://learn.microsoft.com/en-us/rest/api/notificationhubs/common-concepts
  - テンプレート送信: https://learn.microsoft.com/en-us/rest/api/notificationhubs/send-template-notification
  - インストール作成: https://learn.microsoft.com/en-us/rest/api/notificationhubs/create-overwrite-installation
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.parse

import requests

API_VERSION = "2015-01"


def parse_connection_string(cs: str) -> tuple[str, str, str]:
    """接続文字列を (endpoint, key_name, key) に分解する（W8 §6）。

    形式: Endpoint=sb://<ns>.servicebus.windows.net/;SharedAccessKeyName=<name>;SharedAccessKey=<key>
    """
    endpoint = key_name = key = ""
    for part in cs.split(";"):
        if not part:
            continue
        name, _, value = part.partition("=")  # 鍵値の base64 '=' は最初の '=' でだけ分割
        if name == "Endpoint":
            endpoint = value.replace("sb://", "https://")
        elif name == "SharedAccessKeyName":
            key_name = value
        elif name == "SharedAccessKey":
            key = value
    if not (endpoint and key_name and key):
        raise ValueError("接続文字列の形式が不正です。")
    return endpoint.rstrip("/"), key_name, key


def create_sas_token(resource_uri: str, key_name: str, key: str, ttl_seconds: int = 3600) -> str:
    """SAS 認可トークンを生成する（HMAC-SHA256 署名）。

    string-to-sign = <URLエンコード済み小文字リソースURI> + "\\n" + 有効期限(epoch秒)
    """
    target = urllib.parse.quote_plus(resource_uri.lower()).lower()
    expiry = int(time.time()) + ttl_seconds
    to_sign = f"{target}\n{expiry}".encode("utf-8")
    digest = hmac.new(key.encode("utf-8"), to_sign, hashlib.sha256).digest()
    signature = urllib.parse.quote(base64.b64encode(digest))
    return f"SharedAccessSignature sr={target}&sig={signature}&se={expiry}&skn={key_name}"


class NotificationHubClient:
    """ハブへの送信・インストール登録を行う薄いクライアント。"""

    def __init__(self, connection_string: str, hub_name: str):
        self.endpoint, self.key_name, self.key = parse_connection_string(connection_string)
        self.hub_name = hub_name
        # 署名対象・宛先はハブ URI（W8：ハブレベルのポリシーで送信）
        self.hub_uri = f"{self.endpoint}/{hub_name}"

    def _auth_header(self) -> str:
        return create_sas_token(self.hub_uri, self.key_name, self.key)

    def upsert_installation(
        self,
        installation_id: str,
        platform: str,
        push_channel: str,
        tags: list[str] | None = None,
        templates: dict | None = None,
    ) -> requests.Response:
        """Installation を作成/上書きする（W4：冪等。同じ id なら何度でも安全）。

        実端末が無い学習では push_channel はダミーで可（PNS 配信は失敗するが、
        登録レコードが作られ、タグでのターゲット解決が体験できる）。
        """
        url = f"{self.hub_uri}/installations/{installation_id}?api-version={API_VERSION}"
        body = {
            "installationId": installation_id,
            "platform": platform,
            "pushChannel": push_channel,
            "tags": tags or [],
        }
        if templates:
            body["templates"] = templates
        headers = {
            "Authorization": self._auth_header(),
            "Content-Type": "application/json",
            "x-ms-version": API_VERSION,
        }
        return requests.put(url, headers=headers, data=json.dumps(body), timeout=30)

    def send_template(self, message: dict, tag_expression: str | None = None) -> requests.Response:
        """テンプレート通知を送る（W6：非依存メッセージ／W7：ターゲット指定）。

        tag_expression=None ならブロードキャスト。指定すればタグ/タグ式で絞る。
        戻りが 201 なら「NH のキューに入った（Enqueued）」＝受付成功（W2 §4・W7 §5）。
        """
        url = f"{self.hub_uri}/messages/?api-version={API_VERSION}"
        headers = {
            "Authorization": self._auth_header(),
            "Content-Type": "application/json;charset=utf-8",
            "ServiceBusNotification-Format": "template",
            "x-ms-version": API_VERSION,
        }
        if tag_expression:
            headers["ServiceBusNotification-Tags"] = tag_expression
        return requests.post(url, headers=headers, data=json.dumps(message), timeout=30)
