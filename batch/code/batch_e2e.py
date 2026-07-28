"""Week 10 最終プロジェクト：Azure Batch E2E（Python / azure-batch SDK）

全 9 週の総まとめ。Bicep（infra/）が作った「計算資源の器」に対して、
このスクリプトが「仕事」を投入し、入力→処理→出力の一連を流す。

流れ：
  1. Entra 認証（DefaultAzureCredential／Week 8）でクライアントを作る
  2. 入力ファイルを Blob にアップロードし、Resource Files 化（Week 7）
  3. 出力コンテナへの書き込み用 SAS を用意（Week 7・8）
  4. ジョブを作成し、Bicep 製プールに紐づける（Week 2・5）
  5. タスクを追加：各タスクが入力を処理し、結果を Output Files で Blob へ（Week 5・7）
  6. 全タスクの完了を監視（Week 5・9）し、stdout を表示
  7. 後片付け（ジョブ削除・プールは Bicep 管理なので任意）

前提：`az login` 済み、または実行環境にマネージドID があること（Week 8）。
      Batch アカウントに対して Entra RBAC ロール（例：Azure Batch 関連ロール）、
      Storage に対して Blob データ系ロールが割り当て済みであること。
"""

import datetime
import io
import os
import sys
import time

from azure.identity import DefaultAzureCredential
from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    ContainerSasPermissions,
    generate_blob_sas,
    generate_container_sas,
)
from azure.batch import BatchClient, models

import config

# 学習用の入力ファイル（このフォルダの inputs/ に置く）
INPUT_FILES = ["taskdata0.txt", "taskdata1.txt", "taskdata2.txt"]
SAS_LIFETIME_HOURS = 2


# ---------------------------------------------------------------------------
# 1. クライアント生成（Entra 認証／Week 8）
# ---------------------------------------------------------------------------
def build_clients():
    """DefaultAzureCredential で Blob / Batch のクライアントを作る。

    DefaultAzureCredential は、ローカルなら az login、Azure 上ならマネージドID を
    自動で使う（Week 8）。共有キーは使わない。
    """
    credential = DefaultAzureCredential()

    blob_service_client = BlobServiceClient(
        account_url=f"https://{config.STORAGE_ACCOUNT_NAME}.{config.STORAGE_ACCOUNT_DOMAIN}/",
        credential=credential,
    )
    batch_client = BatchClient(
        endpoint=config.BATCH_ACCOUNT_URL,
        credential=credential,
    )
    return blob_service_client, batch_client


# ---------------------------------------------------------------------------
# 2-3. Storage の準備：入力アップロード＋SAS 生成（Week 7・8）
# ---------------------------------------------------------------------------
def get_user_delegation_key(blob_service_client):
    """アカウントキーを使わず、Entra 資格情報から user delegation key を得る（Week 8）。

    これを使って SAS を発行すれば、Storage のアカウントキーを持ち歩かずに済む。
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    return blob_service_client.get_user_delegation_key(
        key_start_time=now - datetime.timedelta(minutes=5),
        key_expiry_time=now + datetime.timedelta(hours=SAS_LIFETIME_HOURS),
    )


def upload_inputs(blob_service_client, udk):
    """入力ファイルを input コンテナへアップロードし、Resource File のリストを返す（Week 7）。

    各 Blob に read 権限の SAS URL を付けて ResourceFile 化する。Batch はタスク実行前に
    この URL からノードの作業ディレクトリへ自動ダウンロードする。
    """
    container_client = blob_service_client.get_container_client(config.INPUT_CONTAINER)
    try:
        container_client.create_container()
    except Exception:
        pass  # 既にあれば無視

    expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=SAS_LIFETIME_HOURS)
    resource_files = []

    for name in INPUT_FILES:
        local_path = os.path.join(os.path.dirname(__file__), "inputs", name)
        with open(local_path, "rb") as f:
            container_client.upload_blob(name=name, data=f, overwrite=True)

        # 単一 Blob への read SAS（コンテナ全体でなく Blob なら read だけでよい／Week 7）
        sas = generate_blob_sas(
            account_name=config.STORAGE_ACCOUNT_NAME,
            container_name=config.INPUT_CONTAINER,
            blob_name=name,
            user_delegation_key=udk,
            permission=BlobSasPermissions(read=True),
            expiry=expiry,
        )
        url = (
            f"https://{config.STORAGE_ACCOUNT_NAME}.{config.STORAGE_ACCOUNT_DOMAIN}/"
            f"{config.INPUT_CONTAINER}/{name}?{sas}"
        )
        # file_path＝ノード上の相対パス（作業ディレクトリ基準）
        resource_files.append(models.ResourceFile(http_url=url, file_path=name))
        print(f"アップロード＋ResourceFile 化: {name}")

    return resource_files


def make_output_container_url(blob_service_client, udk):
    """出力コンテナを作り、書き込み用の container SAS URL を返す（Week 7・8）。

    Output Files は「書き込み」なので write 権限が要る。create/list も付けておく。
    """
    container_client = blob_service_client.get_container_client(config.OUTPUT_CONTAINER)
    try:
        container_client.create_container()
    except Exception:
        pass

    expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=SAS_LIFETIME_HOURS)
    sas = generate_container_sas(
        account_name=config.STORAGE_ACCOUNT_NAME,
        container_name=config.OUTPUT_CONTAINER,
        user_delegation_key=udk,
        permission=ContainerSasPermissions(write=True, create=True, list=True),
        expiry=expiry,
    )
    return (
        f"https://{config.STORAGE_ACCOUNT_NAME}.{config.STORAGE_ACCOUNT_DOMAIN}/"
        f"{config.OUTPUT_CONTAINER}?{sas}"
    )


# ---------------------------------------------------------------------------
# 4. ジョブ作成（Bicep 製プールに紐づけ／Week 2・5）
# ---------------------------------------------------------------------------
def create_job(batch_client):
    print(f"ジョブ作成: {config.JOB_ID}（プール {config.POOL_ID} に紐づけ）")
    job = models.BatchJobCreateOptions(
        id=config.JOB_ID,
        pool_info=models.BatchPoolInfo(pool_id=config.POOL_ID),
        # 全タスク完了で自動終了（Week 5）。タスクを足し終えてから効かせたいので、
        # ここでは既定（noaction）のままにし、投入後は手動で監視する。
    )
    batch_client.create_job(job=job)


# ---------------------------------------------------------------------------
# 5. タスク追加：入力を処理し結果を Output Files で書き出す（Week 5・7）
# ---------------------------------------------------------------------------
def add_tasks(batch_client, resource_files, output_container_url):
    print(f"{len(resource_files)} 個のタスクを追加")
    tasks = []
    for idx, rf in enumerate(resource_files):
        task_id = f"Task{idx}"
        # 入力ファイルの単語数を数えて result.txt に書き、標準出力にも出す。
        # コマンドラインはシェルを介さないので /bin/bash -c で明示的にシェルを噛ませる（Week 2）。
        command = (
            f'/bin/bash -c "wc -w < {rf.file_path} > result.txt; '
            f'echo processed {rf.file_path}; cat result.txt"'
        )

        # Output Files：result.txt と std*.txt を出力コンテナへ（Week 7）。
        # Path にタスク ID を入れて同名衝突を回避（stdout.txt が衝突しないように）。
        output_files = [
            models.OutputFile(
                file_pattern="result.txt",
                destination=models.OutputFileDestination(
                    container=models.OutputFileBlobContainerDestination(
                        container_url=output_container_url,
                        path=f"{task_id}/result.txt",
                    )
                ),
                upload_options=models.OutputFileUploadConfiguration(
                    upload_condition=models.OutputFileUploadCondition.TASK_SUCCESS
                ),
            ),
            models.OutputFile(
                file_pattern="../std*.txt",  # 1つ上（タスクディレクトリ）の stdout/stderr
                destination=models.OutputFileDestination(
                    container=models.OutputFileBlobContainerDestination(
                        container_url=output_container_url,
                        path=task_id,
                    )
                ),
                upload_options=models.OutputFileUploadConfiguration(
                    upload_condition=models.OutputFileUploadCondition.TASK_COMPLETION
                ),
            ),
        ]

        tasks.append(
            models.BatchTaskCreateOptions(
                id=task_id,
                command_line=command,
                resource_files=[rf],
                output_files=output_files,
            )
        )

    batch_client.create_tasks(job_id=config.JOB_ID, task_collection=tasks)


# ---------------------------------------------------------------------------
# 6. 完了監視（Week 5・9）
# ---------------------------------------------------------------------------
def wait_for_tasks(batch_client, timeout_minutes=30):
    print(f"全タスクの完了を監視（timeout {timeout_minutes} 分）...")
    deadline = datetime.datetime.now() + datetime.timedelta(minutes=timeout_minutes)
    while datetime.datetime.now() < deadline:
        tasks = list(batch_client.list_tasks(job_id=config.JOB_ID))
        incomplete = [t for t in tasks if t.state != models.BatchTaskState.COMPLETED]
        if not incomplete:
            print("全タスク完了。")
            return True
        time.sleep(10)
    raise TimeoutError("タイムアウト：完了しないタスクがある（Week 9 の切り分けへ）")


def print_task_output(batch_client):
    """各タスクの stdout と exit code を表示（Week 5・9）。"""
    for task in batch_client.list_tasks(job_id=config.JOB_ID):
        info = batch_client.get_task(job_id=config.JOB_ID, task_id=task.id)
        node_id = info.node_info.node_id if info.node_info else "(未割当)"
        exit_code = info.execution_info.exit_code if info.execution_info else "?"
        print(f"\n--- {task.id} / node={node_id} / exit_code={exit_code} ---")
        stream = batch_client.download_task_file(
            job_id=config.JOB_ID,
            task_id=task.id,
            file_path=config.STANDARD_OUT_FILE_NAME,
        )
        print(_read_stream(stream))


def _read_stream(stream):
    buf = io.BytesIO()
    for chunk in stream:
        buf.write(chunk)
    return buf.getvalue().decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# 7. 後片付け（Week 1・9：課金を止める）
# ---------------------------------------------------------------------------
def cleanup(batch_client):
    print(f"\nジョブ削除: {config.JOB_ID}")
    try:
        batch_client.delete_job(job_id=config.JOB_ID)
    except Exception as e:
        print(f"ジョブ削除でエラー（無視可）: {e}")
    print(
        "プールは Bicep 管理。ノード課金を止めるには infra/ の削除、または\n"
        "  az batch pool delete --pool-id e2e-pool ...\n"
        "で削除する（Week 3・9）。"
    )


def main():
    blob_service_client, batch_client = build_clients()
    udk = get_user_delegation_key(blob_service_client)

    resource_files = upload_inputs(blob_service_client, udk)
    output_container_url = make_output_container_url(blob_service_client, udk)

    create_job(batch_client)
    add_tasks(batch_client, resource_files, output_container_url)

    try:
        wait_for_tasks(batch_client)
        print_task_output(batch_client)
        print(
            f"\n結果は Storage の '{config.OUTPUT_CONTAINER}' コンテナ配下"
            f"（TaskN/result.txt・TaskN/stdout.txt）にも保存されている（Week 7）。"
        )
    finally:
        # 学習用途：確認できたら後片付け（本番はワークフローに合わせて）
        answer = input("\nジョブを削除して後片付けする？ [y/N] ").strip().lower()
        if answer == "y":
            cleanup(batch_client)


if __name__ == "__main__":
    main()
