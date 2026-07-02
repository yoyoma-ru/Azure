"""
Week 17 — 注文の確実処理ワーカー（Service Bus 受信側）

Function が Event Grid→Service Bus に橋渡しした注文メッセージを、
PeekLock で受け取り、冪等に処理して complete する（Week 3 §3・Week 4）。

使い方：
  export SB_FQDN=sb-xxxxx.servicebus.windows.net
  python process_orders.py
"""
import json
import os

from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient

SB_FQDN = os.environ["SB_FQDN"]
QUEUE = "orders"

# 冪等性：処理済み注文IDを記録し、再配信された重複はスキップ（at-least-once 前提・Week 2 §4-2）
_processed: set[str] = set()


def process(order: dict) -> None:
    oid = order["orderId"]
    if oid in _processed:
        print(f"  重複スキップ: {oid}")
        return
    # …ここで在庫引当・決済・出荷などの確実な業務処理…
    _processed.add(oid)
    print(f"  処理完了: 注文 {oid} (amount={order.get('amount')})")


def main() -> None:
    with ServiceBusClient(SB_FQDN, DefaultAzureCredential()) as client:
        with client.get_queue_receiver(QUEUE) as receiver:  # 既定 PeekLock
            print("orders キューを待受中（Ctrl+C で停止）…")
            for msg in receiver:
                try:
                    process(json.loads(str(msg)))
                    receiver.complete_message(msg)  # 成功→消す
                except Exception as e:  # noqa: BLE001
                    print(f"  失敗（再配信されDLQへ）：{e}")
                    receiver.abandon_message(msg)  # 失敗→戻す（10回超で DLQ・Week 4 §1）


if __name__ == "__main__":
    main()
