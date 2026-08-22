# W10 最終PJ — Azure Container Apps 上に FastAPI アプリを E2E デプロイ

W2〜W9 の知識を **Bicep（IaC）＋自前コンテナ**で 1 つの動くシステムに束ねる最終課題。
**ACR にイメージをビルド → Bicep でデプロイ → 公開 URL で動作確認**までを通す。

## 構成

```
code/
  app.py            # FastAPI 最小アプリ（/ , /health , /info）
  requirements.txt  # fastapi + uvicorn
  Dockerfile        # python:3.12-slim ベース（linux/amd64）
  README.md         # このファイル
infra/
  main.bicep        # Log Analytics + 環境 + UAMI + AcrPull + Container App
  main.bicepparam   # パラメータ（ACR 名などを埋める）
```

## デプロイ手順

```bash
# 0) 変数（自分の値に置換。ACR 名は世界で一意・英数小文字）
RG=aca-capstone-rg
LOC=japaneast
ACR=acacapstone$RANDOM

# 1) リソースグループと ACR を作成
az group create -n $RG -l $LOC
az acr create -g $RG -n $ACR --sku Basic

# 2) イメージをクラウドビルドして ACR に push（既定で linux/amd64）
#    このディレクトリ（code/）で実行する
az acr build -r $ACR -t aca-capstone:v1 .

# 3) Bicep をデプロイ（main.bicepparam の <YOUR_ACR_NAME> を $ACR に置換しておく）
#    ワンライナーでパラメータを上書きする例：
az deployment group create \
  -g $RG \
  --template-file ../infra/main.bicep \
  --parameters acrName=$ACR containerImage=$ACR.azurecr.io/aca-capstone:v1 \
  --query properties.outputs.appUrl.value -o tsv

# 4) 出力された URL にアクセスして確認
#    /        → {"message": "...", "hostname": "..."}
#    /health  → {"status": "ok"}
#    /info    → 設定注入の確認
```

## 動作確認のポイント（各週の回収）

- **W3 Ingress**：`appUrl`（外部 Ingress の FQDN）に HTTPS で到達できる。
- **W5 スケール**：`/` を並行大量アクセスするとレプリカが増え、`hostname` が複数に振れる。
  無アクセスで放置すると 0 個に戻る（`az containerapp replica list`）。
- **W8 セキュリティ**：ユーザー名/パスワードを一切置かず、UAMI＋AcrPull で pull できている。
- **W9 プローブ/ログ**：`/health` が liveness/readiness に使われる。
  `az containerapp logs show` でアプリの標準出力を確認。

## 後片付け

```bash
az group delete -n $RG --yes --no-wait
```

## ローカル実行（任意・Azure 不要）

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
# http://localhost:8000/ で確認
```
