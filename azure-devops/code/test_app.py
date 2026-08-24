"""app.py の単体テスト（W8: 自動テストのパイプライン統合用）。

パイプラインでは `pytest --junitxml=test-results.xml` で実行し、
PublishTestResults@2 で結果を Azure Pipelines に発行する。
"""
import os

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_root() -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "message" in res.json()


def test_health() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_version_default() -> None:
    # APP_VERSION 未設定なら dev を返す。
    os.environ.pop("APP_VERSION", None)
    res = client.get("/version")
    assert res.status_code == 200
    assert res.json()["version"] == "dev"


def test_version_from_env() -> None:
    os.environ["APP_VERSION"] = "1.2.3"
    res = client.get("/version")
    assert res.status_code == 200
    assert res.json()["version"] == "1.2.3"
    os.environ.pop("APP_VERSION", None)
