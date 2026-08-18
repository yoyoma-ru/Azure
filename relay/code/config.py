"""接続情報を環境変数から読む（鍵をコード/リポジトリに置かない）。

必要な環境変数:
  RELAY_NAMESPACE  例 relay-learn-xxx（.servicebus.windows.net は付けても付けなくてもよい）
  RELAY_PATH       Hybrid Connection 名（省略時 inventory）
  RELAY_KEY_NAME   認可ルール名（listen-only / send-only など）
  RELAY_KEY        上記ルールの Primary Key
"""
import os

_SUFFIX = ".servicebus.windows.net"


def load() -> dict:
    ns = os.environ["RELAY_NAMESPACE"]
    return {
        "namespace": ns if ns.endswith(_SUFFIX) else ns + _SUFFIX,
        "path": os.environ.get("RELAY_PATH", "inventory"),
        "key_name": os.environ["RELAY_KEY_NAME"],
        "key": os.environ["RELAY_KEY"],
    }
