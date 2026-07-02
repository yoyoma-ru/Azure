"""
Week 17 — 注文パイプラインのクライアント（発行側）

1件の注文に対して 3サービスを役割分担で使う（Week 16 §6 の EC サイト例）：
  ① Event Grid  … 「注文が入った」という状態変化を発行（反応の起点）
  ② Event Hubs  … サイトのテレメトリ（行動ログ）を大量ストリームへ
  （② の裏で Function が Event Grid→Service Bus に橋渡しし、確実処理へ）

使い方：
  export EG_ENDPOINT=...   EG_KEY=...            # Event Grid Custom トピック
  export EH_FQDN=eh-xxxxx.servicebus.windows.net EH_NAME=telemetry
  python pipeline.py 1234
"""
import os
import sys

from azure.core.credentials import AzureKeyCredential
from azure.core.messaging import CloudEvent
from azure.eventgrid import EventGridPublisherClient
from azure.eventhub import EventData, EventHubProducerClient
from azure.identity import DefaultAzureCredential


def publish_order_event(order_id: str) -> None:
    """① Event Grid に「注文イベント」を CloudEvents 形式で発行（Week 11 §4）。"""
    endpoint = os.environ["EG_ENDPOINT"]
    client = EventGridPublisherClient(endpoint, AzureKeyCredential(os.environ["EG_KEY"]))
    event = CloudEvent(
        source="/shop/orders",
        type="Order.Placed",
        subject=f"orders/{order_id}",
        data={"orderId": order_id, "amount": 12000},
    )
    client.send([event])
    print(f"[EventGrid] Order.Placed 発行: {order_id}")


def send_telemetry(order_id: str) -> None:
    """② Event Hubs にテレメトリを送る（partition key で注文ごとに順序保持・Week 8）。"""
    producer = EventHubProducerClient(
        fully_qualified_namespace=os.environ["EH_FQDN"],
        eventhub_name=os.environ["EH_NAME"],
        credential=DefaultAzureCredential(),
    )
    with producer:
        batch = producer.create_batch(partition_key=f"order-{order_id}")
        for step in ("view", "add_to_cart", "checkout"):
            batch.add(EventData(f'{{"orderId":"{order_id}","event":"{step}"}}'))
        producer.send_batch(batch)
    print(f"[EventHubs] telemetry 送信: {order_id}")


if __name__ == "__main__":
    oid = sys.argv[1] if len(sys.argv) > 1 else "1234"
    publish_order_event(oid)
    send_telemetry(oid)
    print("パイプライン発行完了")
