# Azure Relay 最終PJ — Bicep + Python E2E

教材 `relay/notes/relay-week8.md` の成果物。Bicep で名前空間＋Hybrid Connection＋
Listen/Send 専用の認可ルールを構築し、Python 自前実装（SAS 署名＋WebSocket）で
リスナー／センダーを E2E 通信させる。

## 構成

```
relay/infra/main.bicep        名前空間 + Hybrid Connection + listen-only/send-only 認可ルール
relay/infra/main.bicepparam   パラメータ（namespaceName を一意名に置換）
relay/code/relaylib.py        SAS トークン自前署名 + WebSocket URL 生成（標準ライブラリのみ）
relay/code/config.py          接続情報を環境変数から読む
relay/code/listener.py        リスナー（Listen 権限・学習用の最小形）
relay/code/sender.py          センダー（Send 権限）
relay/code/requirements.txt   websockets のみ
```

## 静的検証（Azure 不要）

```bash
python -m py_compile relay/code/*.py
az bicep build --file relay/infra/main.bicep
```

## デプロイ（要 Azure サブスクリプション）

```bash
az group create -n rg-relay-learn -l japaneast
az deployment group create -g rg-relay-learn \
  --template-file relay/infra/main.bicep \
  --parameters relay/infra/main.bicepparam
```

`main.bicepparam` の `namespaceName` は事前にグローバル一意な名前へ置換すること。

## 実行

依存インストール：

```bash
pip install -r relay/code/requirements.txt
```

**端末1（リスナー・Listen 鍵）**：

```bash
export RELAY_NAMESPACE=relay-learn-xxx
export RELAY_PATH=inventory
export RELAY_KEY_NAME=listen-only
export RELAY_KEY=$(az relay hyco authorization-rule keys list \
  -g rg-relay-learn --namespace-name relay-learn-xxx \
  --hybrid-connection-name inventory --name listen-only --query primaryKey -o tsv)
python relay/code/listener.py
```

**端末2（センダー・Send 鍵）**：

```bash
export RELAY_NAMESPACE=relay-learn-xxx
export RELAY_PATH=inventory
export RELAY_KEY_NAME=send-only
export RELAY_KEY=$(az relay hyco authorization-rule keys list \
  -g rg-relay-learn --namespace-name relay-learn-xxx \
  --hybrid-connection-name inventory --name send-only --query primaryKey -o tsv)
python relay/code/sender.py "在庫A1を3個出荷"
```

端末1に `received: {"message": "在庫A1を3個出荷"}` が出れば E2E 成功。

## セキュリティ注意

- 鍵は環境変数に置き、**ファイルにもコミットにも残さない**。
- リスナーには Listen 専用、センダーには Send 専用の鍵のみ配る（最小権限・教材 W6）。
- 本番は接続文字列/SAS より **Microsoft Entra ID／マネージド ID** を推奨（教材 W6）。
- `listener.py` は学習用の最小形。本番強度のリスナー（accept ハンドシェイクの完全実装）は
  公式 SDK（.NET / Node `hyco-ws`）に委ねるのが実務判断（教材 W7/W8）。

## 後片付け

```bash
az group delete -n rg-relay-learn --yes --no-wait
```
