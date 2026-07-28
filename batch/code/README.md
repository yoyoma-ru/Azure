# Week 10 最終プロジェクト（code/）

Bicep（`../infra/`）が作った Batch アカウント＋オートスケール付きプール（Spot 併用）に対して、
Python（azure-batch SDK）でジョブ／タスクを投入し、**入力（Blob）→ 処理 → 出力（Blob）** を流す E2E アプリ。

## 構成
- `batch_e2e.py` … メイン。認証→入力アップロード→ジョブ/タスク投入→完了監視→出力表示→後片付け
- `config.py` … Batch/Storage の接続情報（環境変数で渡す）
- `inputs/` … 学習用の入力テキスト（各タスクが 1 本ずつ処理）
- `requirements.txt` … 依存パッケージ

## 前提（Week 8）
- `az login` 済み、または実行環境にマネージドID がある（`DefaultAzureCredential` が使う）
- 実行主体に、Batch アカウントへの Entra RBAC ロールと、Storage への Blob データ系ロール
  （`Storage Blob Data Contributor` 等）が割り当て済み

## 手順
```bash
# 1) インフラをデプロイ（別ディレクトリ）
az group create -n rg-batch-e2e -l japaneast
az deployment group create -g rg-batch-e2e -f ../infra/main.bicep -p ../infra/main.bicepparam

# 2) Bicep の出力を環境変数へ（例）
export BATCH_ACCOUNT_URL="https://<batchAccountUrl の出力値>"
export STORAGE_ACCOUNT_NAME="<storageAccountName の出力値>"
export POOL_ID="e2e-pool"

# 3) 依存を入れて実行
pip install -r requirements.txt
python batch_e2e.py
```

## 後片付け（Week 1・9：課金停止）
- アプリ内でジョブ削除を選べる。
- ノード課金を止めるには **プールを畳む**：`az batch pool delete --pool-id e2e-pool ...`
  もしくはリソースグループごと削除：`az group delete -n rg-batch-e2e`

> 注：ノードは動いている間だけ課金される（Batch 本体は無料／Week 1）。学習後は必ず畳む。
