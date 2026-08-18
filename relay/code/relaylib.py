"""Azure Relay Hybrid Connections 用ヘルパ。

SAS トークンの自前署名（HMAC-SHA256）と、listen/connect の WebSocket URL 生成。
外部依存なし（標準ライブラリのみ）。教材 relay/notes/relay-week6.md・week8.md 参照。
"""
import base64
import hashlib
import hmac
import math
import time
import urllib.parse


def hmac_sha256(key: bytes, msg: bytes) -> bytes:
    """key で msg を HMAC-SHA256 したバイト列を返す。"""
    return hmac.new(key=key, msg=msg, digestmod=hashlib.sha256).digest()


def create_sas_token(
    service_namespace: str,
    entity_path: str,
    sas_key_name: str,
    sas_key: str,
    valid_seconds: int = 60 * 60 * 48,
) -> str:
    """SAS トークンを生成する。

    リソース URI と失効時刻を結合した文字列を、認可ルールの鍵で HMAC-SHA256 署名する。
    返り値: 'SharedAccessSignature sr=...&sig=...&se=...&skn=...'
    """
    uri = "http://" + service_namespace + "/" + entity_path
    encoded_uri = urllib.parse.quote(uri, safe="")             # (1) URLエンコード
    expiry = math.floor(time.time()) + valid_seconds           # 失効=今+valid_seconds(UNIX秒)
    string_to_sign = encoded_uri + "\n" + str(expiry)          # (2) string-to-sign
    signature = hmac_sha256(sas_key.encode("utf-8"),
                            string_to_sign.encode("utf-8"))    # (3) HMAC-SHA256
    sig = urllib.parse.quote(base64.b64encode(signature))      # (4)(5) Base64 → URLエンコード
    return (
        "SharedAccessSignature sr=" + encoded_uri
        + "&sig=" + sig
        + "&se=" + str(expiry)
        + "&skn=" + sas_key_name
    )


def create_listen_url(service_namespace: str, entity_path: str, token: str) -> str:
    """リスナー（待ち受け）のコントロールチャネル URL。"""
    return (
        "wss://" + service_namespace + "/$hc/" + entity_path
        + "?sb-hc-action=listen&sb-hc-token=" + urllib.parse.quote(token)
    )


def create_send_url(service_namespace: str, entity_path: str, token: str) -> str:
    """センダー（接続開始）の connect URL。"""
    return (
        "wss://" + service_namespace + "/$hc/" + entity_path
        + "?sb-hc-action=connect&sb-hc-token=" + urllib.parse.quote(token)
    )
