"""
Week 17 — E2E テスト（SDK で直接検証・デプロイ不要の部分）

Function/Event Grid の配線はデプロイが要るため、ここでは pure-SDK で
「Service Bus に確実に届く／Event Hubs に取り込まれる」核の2レグを検証する。

  Service Bus：注文メッセージを送って PeekLock で受け取り、内容一致を確認
  Event Hubs ：先に受信を待ち受け → 送信 → 直近イベントとして読めることを確認

前提の環境変数：
  SB_FQDN, EH_FQDN, EH_NAME
実行：
  pytest test_e2e.py -s      （または python test_e2e.py）
"""
import json
import os
import threading
import time
import uuid

from azure.eventhub import EventData, EventHubConsumerClient, EventHubProducerClient
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage

CRED = DefaultAzureCredential()


def test_service_bus_reliable_delivery() -> None:
    """注文メッセージが Service Bus 経由で失われず受信できる（Week 3）。"""
    order_id = str(uuid.uuid4())
    payload = {"orderId": order_id, "amount": 12000}
    fqdn = os.environ["SB_FQDN"]

    with ServiceBusClient(fqdn, CRED) as client:
        with client.get_queue_sender("orders") as sender:
            sender.send_messages(
                ServiceBusMessage(json.dumps(payload), message_id=f"order/{order_id}")
            )
        received = {}
        with client.get_queue_receiver("orders", max_wait_time=10) as receiver:
            for msg in receiver.receive_messages(max_message_count=20, max_wait_time=10):
                body = json.loads(str(msg))
                receiver.complete_message(msg)
                if body.get("orderId") == order_id:
                    received = body
        assert received.get("orderId") == order_id, "Service Bus で注文が受信できない"
    print("OK: Service Bus 確実配信")


def test_event_hubs_ingestion() -> None:
    """テレメトリが Event Hubs に取り込まれ、新着として読める（Week 8）。"""
    tag = str(uuid.uuid4())
    found = threading.Event()

    consumer = EventHubConsumerClient(
        fully_qualified_namespace=os.environ["EH_FQDN"],
        eventhub_name=os.environ["EH_NAME"],
        consumer_group="analytics",
        credential=CRED,
    )

    def on_event(ctx, event) -> None:
        if event and tag in event.body_as_str():
            found.set()

    # 先に「末尾（新着のみ）」で待ち受けを開始してから送る
    reader = threading.Thread(
        target=lambda: consumer.receive(on_event=on_event, starting_position="@latest"),
        daemon=True,
    )
    reader.start()
    time.sleep(5)  # 待ち受けが全パーティションに着くのを待つ

    producer = EventHubProducerClient(
        fully_qualified_namespace=os.environ["EH_FQDN"],
        eventhub_name=os.environ["EH_NAME"],
        credential=CRED,
    )
    with producer:
        batch = producer.create_batch()
        batch.add(EventData(json.dumps({"tag": tag, "event": "checkout"})))
        producer.send_batch(batch)

    got = found.wait(timeout=20)
    consumer.close()
    assert got, "Event Hubs でテレメトリが読めない"
    print("OK: Event Hubs 取り込み")


if __name__ == "__main__":
    test_service_bus_reliable_delivery()
    test_event_hubs_ingestion()
    print("E2E テスト成功")
