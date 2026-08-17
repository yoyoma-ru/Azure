// main.bicep 用パラメータ（W7）
// すべての GUID はプレースホルダ。実行前に自分のテナント／グループの値に置換する。
//   - managedByTenantId : プロバイダーのテナントID   → az account show --query tenantId -o tsv
//   - principalId       : プロバイダー側グループ等のobjectId → az ad group list / az ad signed-in-user show
// ロール定義ID（well-known GUID・W2/W4）:
//   Reader      = acdd72a7-3385-48ef-bd42-f606fba81ae7
//   Contributor = b24988ac-6180-42a0-ab88-20f7382dd24c
//   Managed Services Registration Assignment Delete Role = 91c1777a-f3dc-4fae-b103-61d183457e46
using './main.bicep'

param mspOfferName = 'Contoso Lighthouse 運用オファー'
param mspOfferDescription = 'Contoso による Azure 委任運用（常時Reader＋Contributor eligible）'

// ↓ プロバイダー（管理する側）のテナントIDに置換
param managedByTenantId = '00000000-0000-0000-0000-000000000000'

// 常時（permanent）権限（W4 §5：常時は狭く）
param authorizations = [
  {
    // 運用グループ：常時 Reader（閲覧＋eligible昇格の土台。W4 §6-4 の必須ルール）
    principalId: '11111111-1111-1111-1111-111111111111'
    principalIdDisplayName: 'MSP Operators (Reader 常時)'
    roleDefinitionId: 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
  }
  {
    // 委任解除担当：プロバイダー側から委任を外せるようにする（W4 §5・W6 §3-2）
    principalId: '22222222-2222-2222-2222-222222222222'
    principalIdDisplayName: 'MSP Delegation Remover'
    roleDefinitionId: '91c1777a-f3dc-4fae-b103-61d183457e46'
  }
]

// Just-in-Time（PIM）権限（W4 §6：privileged は必要時だけ）
param eligibleAuthorizations = [
  {
    // 上と同じ運用グループに Contributor を eligible 付与（同principalに常時Reader併記済み）
    principalId: '11111111-1111-1111-1111-111111111111'
    principalIdDisplayName: 'MSP Operators (Contributor JIT)'
    roleDefinitionId: 'b24988ac-6180-42a0-ab88-20f7382dd24c'
    justInTimeAccessPolicy: {
      multiFactorAuthProvider: 'Azure' // 昇格時に Entra MFA 必須（W4 §6-3・W6 §4-1）
      maximumActivationDuration: 'PT8H' // 最大8時間（PT30M〜PT8H）
      managedByTenantApprovers: [
        {
          principalId: '33333333-3333-3333-3333-333333333333'
          principalIdDisplayName: 'PIM Approvers'
        }
      ]
    }
  }
]
