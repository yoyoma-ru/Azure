#!/usr/bin/env bash
# =============================================================================
# Week 10 — ② 評価と修復：オンデマンド評価 → 準拠確認 → 既存を remediation で是正
# 前提： deploy.sh 実行済み・az login 済み
# 使い方：
#   RESOURCE_GROUP=<検証用RG> ./remediate.sh
#   （割り当て ID は自動取得。任意で ASSIGNMENT_ID を環境変数で上書き可）
# =============================================================================
set -euo pipefail

ASSIGNMENT_NAME="governance-baseline-assign"
SUB_ID="$(az account show --query id -o tsv)"
ASSIGNMENT_ID="${ASSIGNMENT_ID:-/subscriptions/${SUB_ID}/providers/Microsoft.Authorization/policyAssignments/${ASSIGNMENT_NAME}}"

echo "==> ① オンデマンド評価スキャンを起動（W8：24時間を待たず今すぐ測る）"
if [[ -n "${RESOURCE_GROUP:-}" ]]; then
  az policy state trigger-scan --resource-group "${RESOURCE_GROUP}"
else
  az policy state trigger-scan   # サブスク全体（時間がかかる）
fi

echo ""
echo "==> ② 準拠状況の要約（非準拠が多い割り当て）"
az policy state summarize --top 5 -o table || true

echo ""
echo "==> ③ 非準拠リソースの一覧（この割り当て分）"
az policy state list \
  --filter "PolicyAssignmentId eq '${ASSIGNMENT_ID}' and ComplianceState eq 'NonCompliant'" \
  --query "[].{resource:resourceId, policy:policyDefinitionReferenceId}" -o table || true

echo ""
echo "==> ④ 既存の非準拠を修復（modify のタグ付与を remediation task で適用）"
echo "    ※ deny（許可リージョン）は修復対象外。modify のみが是正可能（W8）。"
az policy remediation create \
  --name "week10-remediation-$(date +%Y%m%d%H%M%S)" \
  --policy-assignment "${ASSIGNMENT_ID}" \
  --definition-reference-id "ensureTag"

echo ""
echo "完了。数分後に再度 trigger-scan → state list で Compliant 化を確認する。"
