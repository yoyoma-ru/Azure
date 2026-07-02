"""
Week 17 — Event Grid ハンドラ（Azure Functions・Python v2 モデル）

役割：Event Grid の「注文イベント（Order.Placed）」を受けて、
      Service Bus の orders キューへ橋渡しする（反応→確実処理・Week 16 §2）。

デプロイ後、Event Grid の Custom トピックにこの関数を購読させる（notes/week17.md 参照）。
認証はマネージドID＋宛先ロール（Service Bus Data Sender）を推奨（Week 6 §1）。
"""
import json
import os

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage

app = func.FunctionApp()

SB_FQDN = os.environ.get("SB_FQDN", "")  # 例: sb-xxxxx.servicebus.windows.net
QUEUE = "orders"


@app.event_grid_trigger(arg_name="event")
def on_order_event(event: func.EventGridEvent) -> None:
    data = event.get_json()
    order_id = str(data.get("orderId", ""))

    # Event Grid は即応・fire-and-forget（Week 11）。確実な処理は Service Bus に委ねる。
    credential = DefaultAzureCredential()
    with ServiceBusClient(SB_FQDN, credential) as client:
        with client.get_queue_sender(QUEUE) as sender:
            # message_id を注文IDにして重複投入を防ぐ（重複検出／冪等性・Week 4 §3）
            sender.send_messages(
                ServiceBusMessage(json.dumps(data), message_id=f"order/{order_id}")
            )
