# Notification Hubs 最終PJ（W10）— Bicep ＋ Python で E2E

Bicep で Namespace＋Hub を作り、Python から REST でテンプレート通知をタグ指定送信する。
実端末なしでも「送信の受付（Enqueued）とターゲット解決」を体験できる。

## 構成

| ファイル | 役割 |
| --- | --- |
| `../infra/main.bicep` | Namespace＋Hub＋Send専用ポリシー（W3・W8） |
| `nh_client.py` | SAS 署名＋REST クライアント（W2・W6・W7・W8） |
| `send_e2e.py` | E2E デモ（登録→各ターゲットへ送信） |
| `config.py` | 環境変数から接続文字列を読む（W8） |

## 手順

### 1. インフラをデプロイ（Bicep）

```bash
az group create --name rg-nh-week10 --location japaneast

# main.bicepparam の namespaceName を世界で一意な値に編集してから：
az deployment group create \
  --resource-group rg-nh-week10 \
  --template-file ../infra/main.bicep \
  --parameters ../infra/main.bicepparam
```

### 2. 接続文字列を取得（バックエンド用＝Full）

学習用デモは登録も送信も行うため Full を使う（本番は用途別に分ける：W8）。

```bash
az notification-hub authorization-rule list-keys \
  --resource-group rg-nh-week10 \
  --namespace-name nhns-yourname-w10 \
  --notification-hub-name hub-demo \
  --name DefaultFullSharedAccessSignature \
  --query primaryConnectionString -o tsv
```

### 3. 環境変数を設定して実行

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export NH_CONNECTION_STRING='Endpoint=sb://...;SharedAccessKeyName=DefaultFullSharedAccessSignature;SharedAccessKey=...'
export NH_HUB_NAME='hub-demo'

python send_e2e.py
```

（`.env` に同じ 2 変数を書いてもよい。`.env` は `.gitignore` 済み。）

### 4. 出力の見方

- `status=201 OK(Enqueued)` … NH がキューに受付（W2 §4）。**端末到達ではない**。
- `upsert_installation` が 4xx … 実 PNS 資格情報が未設定だと起こりうる（学習では想定内）。
- 実際の配信可否は **Azure ポータル → ハブ → Metrics**（Successful / 各 PNS エラー：W9）で確認。

### 5. 後片付け

```bash
az group delete --name rg-nh-week10 --yes --no-wait
```

## 注意

- 送信データプレーンに公式 Python SDK は無いため REST を直叩きする。SAS は `nh_client.create_sas_token` が自前生成（W8）。
- 実端末へ実際に届けるには、ハブに APNs（`.p8`/`.p12`）や FCM v1（サービスアカウント JSON）の資格情報を設定し（W3 §4）、実機で取得したハンドルで登録する必要がある。
