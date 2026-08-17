# Azure Lighthouse 最終PJ（W7）— Bicep で委任オンボード＋ Python でテナント横断クエリ

Bicep で顧客サブスクをプロバイダーテナントへ委任（オンボード）し、
Python（Azure Resource Graph）で委任済みリソースを `tenantId` 付きで横断クエリする E2E。

Lighthouse は本来 **2 テナント（プロバイダー側＋顧客側）** が必要。
ここでは **顧客側デプロイはシミュレート（手順で解説）**、クエリはプロバイダー側の視点で動かす。
1 テナントしか無くても、Python 側は「自分の tenantId のみが並ぶ」状態で最後まで実行できる。

## 構成

| ファイル | 役割 |
| --- | --- |
| `../infra/main.bicep` | 委任の2リソース（registrationDefinition＋Assignment）をサブスクスコープで作成（W2・W3・W4） |
| `../infra/main.bicepparam` | authorizations（常時Reader＋Delete Role）＋ eligibleAuthorizations（Contributor JIT）。GUID はプレースホルダ |
| `cross_tenant_query.py` | Resource Graph でテナント横断クエリ（W5） |
| `config.py` | 環境変数を読む（W6：秘密は直書きしない） |
| `requirements.txt` | 依存パッケージ |

## 役割分担（2 テナント）

```
プロバイダー側（あなた）           顧客側（Owner を持つ人）
--------------------------        ------------------------
① ID 収集（テナントID/objectId）
② main.bicepparam を編集
                    ── テンプレを渡す ──▶
                                          ③ 顧客テナントで az deployment sub create（Owner 必要）
④ Python でテナント横断クエリ ◀── 委任成立 ──
```

## 手順

### 1. プロバイダー側：ID を集めて param を編集（W2 §7）

```bash
az account show --query tenantId -o tsv          # managedByTenantId に入れる
az ad signed-in-user show --query id -o tsv       # principalId（本来はグループの objectId 推奨）
```

`../infra/main.bicepparam` の各プレースホルダ GUID を実値に置換する。

### 2. Bicep を検証（1 テナントで可・W3 §7）

```bash
az bicep build --file ../infra/main.bicep
```

エラーが出なければリソース種別・プロパティが正しい。生成 JSON は W2 の公式サンプルと同じ構造になる。

### 3. 顧客側：デプロイ（★2 テナント環境がある場合のみ・W3 §4）

**顧客テナントにサインインした Owner が**実行する。プロバイダーは代われない（W3・W6）。

```bash
# （顧客テナントで）az login した状態で：
az deployment sub create \
  --name lighthouse-onboard \
  --location japaneast \
  --template-file ../infra/main.bicep \
  --parameters ../infra/main.bicepparam

# 確認：委任の2リソースができたか
az managedservices definition list -o table
az managedservices assignment list -o table
```

> 単一テナントでは `managedByTenantId` が自分になり委任不可（自分に委任は不可・W3 §7）。
> その場合はこの手順を飛ばし、次の Python クエリで「自分の tenantId のみ」を確認する。

### 4. プロバイダー側：テナント横断クエリを実行（W5）

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 委任サブスクの印付けに使う（任意）。自分のテナントIDを入れる
export LH_MANAGING_TENANT_ID="$(az account show --query tenantId -o tsv)"
# 対象サブスクを絞るなら（任意）。未設定ならアクセス可能な全て（委任含む）
# export LH_SUBSCRIPTIONS="sub-id-1,sub-id-2"

az login   # DefaultAzureCredential が使う
python cross_tenant_query.py
```

出力（3 ブロック）:
1. 見えているサブスク一覧（`tenantId` 付き。委任分は「◎ 委任」印）
2. `tenantId` ごとのリソース件数
3. HTTPS 未強制ストレージの横断抽出（是正候補）

委任済み環境では 1〜3 に**別テナント（顧客）の行**が混じる。単一テナントでは全行が自分の `tenantId`。

### 5. 後片付け（委任した場合・W6 §3）

```bash
# プロバイダー側から解除（param に Delete Role を入れてある場合）
az managedservices assignment list
az managedservices assignment delete --assignment <id または フルresourceId>
# または顧客側：Service providers 画面 → オファーのゴミ箱アイコン
```

Python 実行自体は読み取りのみで、Azure 上に作成物なし。

## 注意

- 認証は `DefaultAzureCredential`（`az login` 済みでよい）。接続文字列やキーは扱わない。
- Resource Graph は **ARM（コントロールプレーン）** の情報のみ。Blob の中身等データプレーンは対象外（W1・W6）。
- クエリ結果に `tenantId` が出るのが Lighthouse 横断の要（W5 §2）。委任サブスクは `tenantId != 自分` で見分ける。
