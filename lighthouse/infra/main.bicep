// Azure Lighthouse 最終PJ（W7）インフラ定義
// 顧客テナントに委任の2リソース（Registration Definition ＋ Registration Assignment）を作る。
// 顧客サブスクをまるごとプロバイダーテナントへ委任する（サブスクスコープのデプロイ）。
// 参照：W2（2オブジェクト）、W3（Bicep/デプロイ）、W4（ロール制約・eligible/PIM・Delete Role）
targetScope = 'subscription'

@description('オファー名。顧客の Service providers 画面に表示される。同一スコープで一意にする（W2・W3）')
param mspOfferName string = 'Contoso Lighthouse 運用オファー'

@description('オファーの説明。顧客に見える（W2）')
param mspOfferDescription string = 'Contoso による Azure 委任運用（常時Reader＋Contributorはeligible/JIT）'

@description('管理する側（プロバイダー）のテナントID。顧客サブスクのテナントIDと同じ値は不可（W2・W3）')
param managedByTenantId string

@description('常時付与する authorizations。principalId × roleDefinitionId × 表示名 の配列（W2 §3・W4）')
param authorizations array

@description('Just-in-Time（PIM）で昇格させる eligibleAuthorizations。空配列なら常時のみ（W4 §6）')
param eligibleAuthorizations array = []

// 定義／割り当ての名前は決定的GUID：同じ入力なら同じ名前＝再デプロイでも冪等（W3 §3-1）
var registrationId = guid(mspOfferName, managedByTenantId, subscription().subscriptionId)

// 登録定義：誰に何を許すかの設計図（W2 §2）
resource registrationDefinition 'Microsoft.ManagedServices/registrationDefinitions@2022-10-01' = {
  name: registrationId
  properties: {
    registrationDefinitionName: mspOfferName
    description: mspOfferDescription
    managedByTenantId: managedByTenantId
    authorizations: authorizations
    eligibleAuthorizations: eligibleAuthorizations
  }
}

// 登録割り当て：その定義を「このサブスク」に効かせる（W2 §4）。定義を参照して依存が解決される
resource registrationAssignment 'Microsoft.ManagedServices/registrationAssignments@2022-10-01' = {
  name: registrationId
  properties: {
    registrationDefinitionId: registrationDefinition.id
  }
}

output offerName string = mspOfferName
output registrationDefinitionId string = registrationDefinition.id
output assignmentName string = registrationAssignment.name
