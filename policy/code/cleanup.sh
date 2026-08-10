#!/usr/bin/env bash
# =============================================================================
# Week 10 — ③ 後片付け：割り当て → ロール割り当て → イニシアティブ → 定義 の順で削除
#   依存の逆順で消す（割り当てを先に消さないと定義を消せない）
# =============================================================================
set -euo pipefail

ASSIGNMENT_NAME="governance-baseline-assign"
INITIATIVE_NAME="governance-baseline"
POLICY_NAME="ensure-required-tag"
SUB_ID="$(az account show --query id -o tsv)"

echo "==> ① マネージドID のロール割り当てを削除（割り当て前に principalId を取得）"
PRINCIPAL_ID="$(az policy assignment show --name "${ASSIGNMENT_NAME}" --query identity.principalId -o tsv 2>/dev/null || true)"
if [[ -n "${PRINCIPAL_ID}" && "${PRINCIPAL_ID}" != "null" ]]; then
  az role assignment delete --assignee "${PRINCIPAL_ID}" --scope "/subscriptions/${SUB_ID}" || true
fi

echo "==> ② ポリシー割り当てを削除"
az policy assignment delete --name "${ASSIGNMENT_NAME}" || true

echo "==> ③ イニシアティブ（policySet）を削除"
az policy set-definition delete --name "${INITIATIVE_NAME}" || true

echo "==> ④ カスタムポリシー定義を削除"
az policy definition delete --name "${POLICY_NAME}" || true

echo ""
echo "後片付け完了。remediation で付いたタグは残る（必要なら手動で外す）。"
