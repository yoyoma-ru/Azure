"""Week 10 最終プロジェクトの設定値。

Bicep（infra/main.bicep）が出力した値を環境変数で渡す想定。
    export BATCH_ACCOUNT_URL="https://<batchAccountUrl の出力値>"
    export STORAGE_ACCOUNT_NAME="<storageAccountName の出力値>"
    export POOL_ID="e2e-pool"   # Bicep が作成するプール ID（既定）
"""

import os

# --- Bicep の出力から渡す（データプレーン エンドポイント／Week 8） ---
BATCH_ACCOUNT_URL = os.environ.get("BATCH_ACCOUNT_URL", "https://<batch-account>.<region>.batch.azure.com")
STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT_NAME", "<storage-account>")
STORAGE_ACCOUNT_DOMAIN = "blob.core.windows.net"

# --- Bicep が作成済みのプールを参照（ジョブ/タスクだけ Python で投入） ---
POOL_ID = os.environ.get("POOL_ID", "e2e-pool")

# --- このアプリで作るジョブ／コンテナ名 ---
JOB_ID = "e2e-job"
INPUT_CONTAINER = "input"    # Resource Files（入力）の置き場（Week 7）
OUTPUT_CONTAINER = "output"  # Output Files（出力）の書き出し先（Week 7）

# タスクの標準出力ファイル名（Week 1・9）
STANDARD_OUT_FILE_NAME = "stdout.txt"
