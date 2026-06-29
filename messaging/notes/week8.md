# Week 8 — Event Hubs を実装する：プロデューサ・コンシューマ・Blob チェックポイント

> **Phase B**（Event Hubs）| 学習プラン Week 8 / 17
> 学習目標：`EventHubProducerClient` でバッチ送信（partition key 付き）でき、`EventHubConsumerClient` ＋ Blob チェックポイントストアで受信して落ちても続きから再開でき、処理インスタンスを増やすとパーティションが自動分配される様子を体感し、Service Bus の `complete` と Event Hubs の `update_checkpoint` の違いをコードで説明できる

---

## 0. 今週の位置づけ

Week 7 で概念（パーティション・offset・checkpoint・TU）を押さえた。Week 8 はそれを **Python SDK（`azure-eventhub`）で実装**して、手で動かして腹落ちさせる。

1. **準備**：リソースと2つのロール（Event Hubs と Storage）（§1）
2. **送る**：`EventHubProducerClient` でバッチ送信（§2）
3. **受ける**：`EventHubConsumerClient` ＋ Blob チェックポイント（§3）
4. **スケール**：インスタンスを増やしてパーティション自動分配を体感（§4）
5. **対比**：SB の `complete` と EH の `update_checkpoint`（§5）

> Week 7 §4 で「チェックポイントの保存は消費側の責任・Blob に保存」と学んだ。今週その **Blob チェックポイントストアを実際に繋ぐ**。

---

## 1. 準備：リソースと2つのロール

Week 7 で作った名前空間／イベントハブ（`telemetry`・パーティション4・`analytics` グループ）を使う。**Event Hubs に加えて、チェックポイント用に Storage が要る**のが Event Hubs 実装の特徴。

```bash
# Week 7 の続き（無ければ Week 7 §6 で作成）
RG=rg-messaging-week7
EHNS=ehns-week7-xxxxx
EH=telemetry

# チェックポイント用ストレージ＋コンテナ（コンシューマーグループごとに別コンテナ推奨）
ST=stehckpt$RANDOM
az storage account create -g $RG -n $ST --sku Standard_LRS
az storage container create --account-name $ST -n analytics-cp --auth-mode login

# 自分に2つのロールを付与（passwordless）
ME=$(az ad signed-in-user show --query id -o tsv)
# ① Event Hubs：送受信
az role assignment create --assignee "$ME" --role "Azure Event Hubs Data Owner" \
  --scope $(az eventhubs namespace show -g $RG -n $EHNS --query id -o tsv)
# ② Storage：チェックポイント Blob の読み書き
az role assignment create --assignee "$ME" --role "Storage Blob Data Contributor" \
  --scope $(az storage account show -g $RG -n $ST --query id -o tsv)
```

```bash
pip install azure-eventhub azure-eventhub-checkpointstoreblob-aio azure-identity aiohttp
```

> **ポイント**：Service Bus は SB のロール1つで済んだが、**Event Hubs のコンシューマは「Event Hubs Data Owner/Receiver」＋「Storage Blob Data Contributor」の2つ**が要る。チェックポイントを Blob に書くから（Week 7 §4）。Storage のコンテナは**コンシューマーグループごとに分ける**のが公式推奨。

---

## 2. プロデューサ：バッチ送信

```python
# send.py
import asyncio
from azure.eventhub import EventData
from azure.eventhub.aio import EventHubProducerClient
from azure.identity.aio import DefaultAzureCredential

FQDN = "ehns-week7-xxxxx.servicebus.windows.net"
EH = "telemetry"

async def run():
    credential = DefaultAzureCredential()
    producer = EventHubProducerClient(
        fully_qualified_namespace=FQDN, eventhub_name=EH, credential=credential
    )
    async with producer:
        # ① パーティションキーなし（ラウンドロビンで分散）
        batch = await producer.create_batch()
        for i in range(5):
            batch.add(EventData(f"telemetry #{i}"))
        await producer.send_batch(batch)

        # ② パーティションキー付き（同じ device は同じパーティションへ・順序保持）
        batch2 = await producer.create_batch(partition_key="device-1")
        for t in ["temp=21", "temp=22", "temp=23"]:
            batch2.add(EventData(t))
        await producer.send_batch(batch2)
    await credential.close()
    print("送信完了")

asyncio.run(run())
```

> **ポイント**：
> - **バッチ送信が基本**：`create_batch()` で器を作り、`add()` で詰め、`send_batch()` でまとめて送る（大量送信を効率化）。1バッチは最大1MB。
> - **partition key**：`create_batch(partition_key=...)` で指定。同じキーは**同じパーティションに・到着順**で入る（Week 2 §1-3／Week 7 §2）。未指定はラウンドロビン分散。
> - Service Bus と違い **complete/peek-lock の概念はない**（送るだけ。受信側が後で読む）。

---

## 3. コンシューマ：Blob チェックポイントで受信

```python
# recv.py
import asyncio
from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore
from azure.identity.aio import DefaultAzureCredential

FQDN = "ehns-week7-xxxxx.servicebus.windows.net"
EH = "telemetry"
BLOB_URL = "https://stehckptxxxxx.blob.core.windows.net/"
CONTAINER = "analytics-cp"

async def on_event(partition_context, event):
    print(f'受信: "{event.body_as_str()}" / partition {partition_context.partition_id}')
    # ★ チェックポイント更新＝「ここまで処理した」を Blob に保存（消費側の責任）
    await partition_context.update_checkpoint(event)

async def main():
    credential = DefaultAzureCredential()
    # チェックポイントストア（Blob）
    checkpoint_store = BlobCheckpointStore(
        blob_account_url=BLOB_URL, container_name=CONTAINER, credential=credential
    )
    client = EventHubConsumerClient(
        fully_qualified_namespace=FQDN, eventhub_name=EH,
        consumer_group="analytics",                 # Week 7 で作ったグループ
        checkpoint_store=checkpoint_store,
        credential=credential,
    )
    async with client:
        # checkpoint があればそこから、無ければ starting_position から
        #   "-1" = 先頭から / "@latest" = 末尾（新着のみ）
        await client.receive(on_event=on_event, starting_position="-1")
    await credential.close()

asyncio.run(main())
```

```bash
python recv.py   # 受信待受（Ctrl+C で停止）
# 別ターミナルで
python send.py
```

> **ポイント**：
> - **`on_event` コールバック方式**：受信ループは SDK が回し、イベント1件ごとに `on_event` が呼ばれる（全パーティションを自動で面倒みる）。
> - **`update_checkpoint(event)`**：これが Week 7 の「しおりを Blob に挟む」操作。呼ぶと、その event の位置が **Blob に保存**され、次回起動時はそこから再開。
> - **`starting_position`** は**チェックポイントが無いときの初期位置**。一度 checkpoint が書かれれば、再起動しても**続きから**読む（`-1` の先頭からには戻らない）。
> - **再開を体感**：recv を Ctrl+C → 再実行すると、**処理済みは飛ばして続きから**になる（checkpoint が効いている証拠）。

> **初学者向け用語補足：`update_checkpoint` を「毎件」呼ぶ？**
> 毎件呼ぶと安全（再開時の読み直しが最小）だが、Blob 書き込みが増えてオーバーヘッド大。実務では**N件ごと・数秒ごと**にまとめて checkpoint するのが定石。粗くすると再開時に**処理済みを読み直す＝重複**が起きるので、受信処理は**冪等**に（Week 2 §4-2）。「どのくらいの頻度で checkpoint するか」は**再処理コスト vs 書き込みコスト**のトレードオフ。

---

## 4. 負荷分散を体感：インスタンスを増やす

同じ `consumer_group` ＋ 同じ `checkpoint_store` で **recv.py を複数起動**すると、SDK（epoch consumer）が**パーティションを自動で分け合う**（Week 7 §3-2）。

```text
recv.py インスタンス① 起動 → 4パーティション全部を担当
recv.py インスタンス② 追加 → パーティションが再分配され ①②で2つずつ担当
recv.py インスタンス③④ 追加 → 1つずつ（パーティション数=4が並列上限）
インスタンス⑤ 追加 → 担当なしで待機（誰かが落ちたら引き継ぐ）
```

> これが「処理インスタンスを増やすだけでスケールアウト」（Week 7 §3-2）。担当の割り当て・引き継ぎ・チェックポイントの共有はすべて `checkpoint_store`（Blob）を介して SDK が自動でやる。だから**全インスタンスが同じ Blob コンテナ**を指すことが重要。

---

## 5. 対比：Service Bus の `complete` と Event Hubs の `update_checkpoint`

同じ「処理し終えた」を表すが、**意味が根本的に違う**（Week 7 §1・§4 の実装版）。

| | Service Bus `complete_message` | Event Hubs `update_checkpoint` |
|---|---|---|
| 何が起きる | そのメッセージを**キューから削除** | 読み取り位置（offset）を **Blob に保存**するだけ |
| データは | 消える | **残る**（保持期間まで） |
| 1件ごとか | **1件ごとに確定**（消す/戻す） | **位置の記録**（まとめて間引ける） |
| 他の読み手 | 関係ない（取った人だけ） | 他グループは**自分の checkpoint で独立に**読む |
| 戻せるか | DLQ 等の仕組み | **過去 offset 指定でリプレイ自由** |

```python
# Service Bus：1件ずつ「消す/戻す」を確定
receiver.complete_message(msg)     # 消す
receiver.abandon_message(msg)      # 戻す（再配信）

# Event Hubs：位置を記録するだけ（データは消えない）
await partition_context.update_checkpoint(event)   # 「ここまで読んだ」を Blob に
```

> **核心**：Service Bus は「**ToDo を消す**」、Event Hubs は「**読んだページにしおりを挟む**」。だから Event Hubs は同じデータを別グループが独立に読め、巻き戻せる。Week 7 §1 の「作業キュー vs 録画ログ」がコードに現れている。

---

## 6. Week 8 全体の整理

```mermaid
flowchart LR
    SEND["send.py<br/>create_batch→add→send_batch<br/>(partition_key)"] --> EH["Event Hub: telemetry"]
    EH --> RECV["recv.py<br/>on_event コールバック"]
    RECV -->|"update_checkpoint"| CP["Blob チェックポイント<br/>(位置を保存)"]
    CP -.->|"再起動時は続きから"| RECV
    RECV2["recv.py 追加インスタンス"] -->|"同じ group/Blob"| CP
```

| 用語 | 一言説明 |
|---|---|
| EventHubProducerClient / create_batch / send_batch | 送信窓口 / バッチの器 / まとめ送信 |
| partition_key | 同じキーを同じパーティションへ（順序保持） |
| EventHubConsumerClient / on_event | 受信窓口 / 1件ごとのコールバック |
| BlobCheckpointStore / update_checkpoint | チェックポイント保存先 / 位置を保存 |
| starting_position | checkpoint が無いときの初期位置（-1=先頭） |

---

## ハンズオン チェックリスト

- [ ] Event Hubs Data Owner と Storage Blob Data Contributor の2ロールを自分に付与した
- [ ] `send.py` でバッチ送信（partition key 付き／なし）した
- [ ] `recv.py` で受信し、partition ID 付きで表示されることを確認した
- [ ] recv を停止→再実行し、**処理済みを飛ばして続きから**になることを確認した（checkpoint）
- [ ] recv を2つ起動し、パーティションが分配される（負荷分散）ことを確認した
- [ ] `complete`（消す）と `update_checkpoint`（位置を保存）の違いを説明できた

---

## 自己チェック

1. **Event Hubs のコンシューマに Storage のロールが要るのはなぜ？**
   - キーワード：チェックポイントを Blob に保存・消費側の責任
2. **`update_checkpoint` は何をする？呼ばないとどうなる？**
   - キーワード：位置を Blob に保存・再起動で読み直し
3. **checkpoint を毎件 vs まとめて、のトレードオフは？**
   - キーワード：書き込みコスト vs 再処理（重複）・冪等性
4. **recv を2インスタンスにすると何が起きる？上限は？**
   - キーワード：パーティション自動分配・パーティション数が並列上限
5. **`complete_message` と `update_checkpoint` の決定的な違いは？**
   - キーワード：消す vs 位置を記録・残る・リプレイ

---

## 次週の予告（Week 9）

Event Hubs を「取り込み基盤」として周辺と繋ぐ：

- **Event Hubs Capture**：流れるストリームを自動で Blob / Data Lake に保存（Avro/Parquet）——Week 1 の Storage と繋がる
- **Kafka 互換エンドポイント**：既存 Kafka アプリを接続先変更だけで載せ替え（Week 2 §1-3 の Kafka）
- **Schema Registry**：イベントのスキーマを管理し、送受信で整合を保つ
- 「大量に取り込んで、後段の分析・保管へ流す」という Event Hubs の本領
