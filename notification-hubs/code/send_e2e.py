"""Notification Hubs E2E デモ（W10 最終PJ）。

これまでの 9 週を 1 本のコードに束ねる：
  W4 登録  … ダミー Installation をテンプレート付きで作成（冪等）
  W5 タグ  … tags でセグメントを表現
  W6 テンプレ … $(message) の穴を持つテンプレートを登録し、非依存メッセージを送る
  W7 送信  … ブロードキャスト／タグ／タグ式／InstallationId 宛
  W8 認証  … SAS 署名（接続文字列は環境変数から）
  W9 監視  … 戻り値 Enqueued（201）を確認。実配信はポータルのメトリクスで見る

実端末・実 PNS 資格情報が無くても、送信の受付（Enqueued）とターゲット解決は体験できる。
"""
from __future__ import annotations

import config
from nh_client import NotificationHubClient

hub = NotificationHubClient(config.CONNECTION_STRING, config.HUB_NAME)

INSTALLATION_ID = "demo-device-1"


def show(label: str, resp) -> None:
    ok = "OK(Enqueued)" if resp.status_code in (200, 201) else "NG"
    loc = resp.headers.get("Location", "-")  # Standard のみ：メッセージID（W7 §5）
    print(f"[{label}] status={resp.status_code} {ok}  Location={loc}")


def register_dummy_device() -> None:
    """W4/W6：ダミー Installation をテンプレート付きで登録する。

    push_channel は実端末が無いためダミー。実 PNS 資格情報が未設定だと 4xx に
    なることがあるが、学習では想定内（登録の流れとターゲット解決を体験するのが目的）。
    """
    templates = {
        # 端末が「この器で受け取る」と宣言するテンプレート（W6）
        "default": {"body": '{"data":{"message":"$(message)"}}', "tags": ["user_demo"]}
    }
    resp = hub.upsert_installation(
        installation_id=INSTALLATION_ID,
        platform="fcm",  # 学習用。実運用は端末に合わせて fcmv1/apns/wns
        push_channel="DUMMY-HANDLE-FOR-LEARNING",
        tags=["user_demo", "location_tokyo", "lang_ja"],
        templates=templates,
    )
    print(f"[upsert_installation] status={resp.status_code} (登録レコード作成の試行)")


def main() -> None:
    print(f"Hub: {config.HUB_NAME}\n")

    register_dummy_device()

    # W7：さまざまなターゲットへテンプレート送信
    msg = {"message": "メンテナンスは 23 時開始"}  # プラットフォーム非依存メッセージ（W6）

    show("broadcast", hub.send_template(msg))                              # 全登録
    show("tag", hub.send_template(msg, "location_tokyo"))                  # タグ
    show("tag-expr", hub.send_template(msg, "location_tokyo && lang_ja"))  # タグ式（AND）
    show("installationId",
         hub.send_template(msg, f"$InstallationId:{{{INSTALLATION_ID}}}"))  # 1端末

    print(
        "\n注：status 201 は『NH のキューに受付（Enqueued）』であって端末到達ではない"
        "（W2 §4・W7 §5）。\n実際の配信可否は Azure ポータルのメトリクス"
        "（Successful / 各PNSエラー：W9）で確認する。"
    )


if __name__ == "__main__":
    main()
