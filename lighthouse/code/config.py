"""環境変数から設定を読み込む（W6：秘密はコードに直書きしない）。

必要な環境変数（.env または export で設定）:
  LH_MANAGING_TENANT_ID  プロバイダー（管理する側）のテナントID(GUID)。
                         委任サブスク（tenantId != これ）の判定に使う。
                         省略時は「自分以外の tenantId＝委任」とだけ表示する。
  LH_SUBSCRIPTIONS       クエリ対象サブスクID（カンマ区切り）。任意。
                         未設定なら、サインインしている ID がアクセスできる
                         すべて（Lighthouse 委任サブスクを含む）を対象にする（W5 §2-1）。

認証は DefaultAzureCredential（az login 済みなら追加設定不要）。
"""
import os

from dotenv import load_dotenv

load_dotenv()  # カレントの .env を読む（あれば）

MANAGING_TENANT_ID = os.environ.get("LH_MANAGING_TENANT_ID", "").strip()

_subs = os.environ.get("LH_SUBSCRIPTIONS", "").strip()
# 未設定なら None（＝アクセス可能な全サブスクを対象。委任分を含む）
SUBSCRIPTIONS = [s.strip() for s in _subs.split(",") if s.strip()] or None
