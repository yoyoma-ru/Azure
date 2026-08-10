#!/usr/bin/env bash
# =============================================================================
# Week 10 — ① デプロイ：Bicep でポリシー定義／イニシアティブ／割り当てを作成
#   サブスクリプションスコープのデプロイ（az deployment sub create）
# 前提： az login 済み・対象サブスクを az account set で選択済み
# =============================================================================
set -euo pipefail

LOCATION="${LOCATION:-japaneast}"
DEPLOYMENT_NAME="policy-week10-$(date +%Y%m%d%H%M%S)"
INFRA_DIR="$(cd "$(dirname "$0")/../infra" && pwd)"

echo "==> サブスクリプションスコープでデプロイ: ${DEPLOYMENT_NAME}"
az deployment sub create \
  --name "${DEPLOYMENT_NAME}" \
  --location "${LOCATION}" \
  --template-file "${INFRA_DIR}/main.bicep" \
  --parameters "${INFRA_DIR}/main.bicepparam"

echo ""
echo "==> デプロイ結果の出力（ID 群）"
az deployment sub show --name "${DEPLOYMENT_NAME}" \
  --query "properties.outputs" -o json

echo ""
echo "完了。割り当て ID は上記 outputs.assignmentId.value を控えておく（remediate.sh で使用）。"
