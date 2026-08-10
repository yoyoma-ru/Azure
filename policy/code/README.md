# Week 10 最終PJ — 実行手順（Bicep + az policy）

Azure Policy の全要素を Bicep と Azure CLI で E2E に動かす。詳しい解説は [`../notes/week10.md`](../notes/week10.md)。

## 構成物

| ファイル | 役割 |
| --- | --- |
| `../infra/main.bicep` | カスタム定義（modify）＋イニシアティブ＋割り当て（マネージドID）＋ロール割り当て |
| `../infra/main.bicepparam` | パラメータ（リージョン・タグ・許可地域） |
| `deploy.sh` | ① サブスクスコープでデプロイ |
| `remediate.sh` | ② オンデマンド評価 → 準拠確認 → 既存を修復 |
| `cleanup.sh` | ③ 後片付け（依存の逆順で削除） |

## 前提

```bash
az login
az account set --subscription "<SUBSCRIPTION_ID_OR_NAME>"
# 権限：定義/割り当て作成に Resource Policy Contributor、
#       マネージドID へのロール付与に User Access Administrator（または Owner）が必要（W8）
```

## 手順

```bash
# ① デプロイ（定義・イニシアティブ・割り当て・ロール割り当てを作成）
LOCATION=japaneast ./deploy.sh

# 動作確認用に、タグ無しリソースを検証用RGに1つ作っておくと非準拠が観察できる
#   例： az group create -n rg-policy-demo -l japaneast
#        az storage account create -n <uniquename> -g rg-policy-demo -l japaneast --sku Standard_LRS

# ② 評価 → 修復（数分の反映待ちが入る）
RESOURCE_GROUP=rg-policy-demo ./remediate.sh

# ③ 後片付け
./cleanup.sh
#   検証用RGも消す場合： az group delete -n rg-policy-demo --yes --no-wait
```

## 事前チェック（デプロイ不要のローカル検証）

```bash
az bicep build --file ../infra/main.bicep      # 構文検証（このPJで通過確認済み）
```

## 注意

- `deny`（許可リージョン）は**新規作成のみ**をブロックする。既存の違反は可視化のみで、修復対象外（W8）。
- `modify`（タグ付与）だけが `remediate.sh` の remediation で既存を是正できる。
- マネージドID のロール付与は Bicep（④ロール割り当て）で明示的に行う。Portal のような自動付与は無い（W8）。
