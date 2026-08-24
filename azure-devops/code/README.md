# capstone sample app（Azure DevOps 学習 W10）

最小の FastAPI アプリ。W10 のマルチステージ `azure-pipelines.yml` が
build → test → deploy する対象。

## ローカル実行

```bash
cd code
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app:app --reload
```

- http://127.0.0.1:8000/          あいさつ
- http://127.0.0.1:8000/health    ヘルスチェック
- http://127.0.0.1:8000/version   APP_VERSION（未設定なら dev）
- http://127.0.0.1:8000/docs      Swagger UI（FastAPI 自動生成）

## テスト

```bash
cd code
pytest                              # ローカル
pytest --junitxml=test-results.xml # パイプライン（結果を PublishTestResults@2 で発行）
```

## エンドポイント

| メソッド | パス | 返すもの |
|---|---|---|
| GET | `/` | `{"message": ...}` |
| GET | `/health` | `{"status": "ok"}` |
| GET | `/version` | `{"version": "<APP_VERSION or dev>"}` |

APP_VERSION は Variable Group / 環境変数から注入する想定（W5）。
