// =============================================================
// Week 9 最終プロジェクト：マルチスコープ Bicep（管理グループ → サブスク → RG）
//   これ 1 本で、全 9 週の要素を縦断的にデプロイする。
//   - 管理グループスコープ（Week 2）で開始：targetScope = 'managementGroup'（Week 4）
//   - ① 管理グループに Azure Policy「Allowed locations」を割り当て（Week 6）
//   - ② サブスクリプションへ入れ子デプロイ（module + scope、Week 2/4）
//        → その中で RG を作成（Week 2）
//        → さらに RG へ入れ子デプロイして 実リソース（ストレージ）＋RBAC（Week 6）
//   デプロイは GitHub Actions + OIDC（Week 8）で E2E 実行する想定。
//   コマンド例：
//     az deployment mg create \
//       --management-group-id <MG-ID> \
//       --location japaneast \
//       --template-file main.bicep \
//       --parameters main.bicepparam
// =============================================================

targetScope = 'managementGroup'

@description('デプロイ先サブスクリプションの ID')
param subscriptionId string

@description('作成するリソースグループ名')
param rgName string = 'rg-arm-capstone'

@description('リソースのリージョン')
param location string = 'japaneast'

@description('ストレージ名の接頭辞（3〜11文字）')
@minLength(3)
@maxLength(11)
param storagePrefix string = 'capstone'

@description('Allowed locations Policy で許可するリージョン一覧')
param allowedLocations array = [
  'japaneast'
  'japanwest'
]

@description('組み込み Policy「Allowed locations」の定義 ID（GUID）')
param allowedLocationsPolicyId string = 'e56962a6-4747-49cd-b67b-bf8b01975c4c'

@description('RG に Reader を与えるプリンシパル ID（空なら RBAC 割り当てをスキップ）')
param readerPrincipalId string = ''

// ---------- ① 管理グループスコープ：Policy 割り当て（Week 6）----------
// 組み込みポリシー定義はテナントレベルなので tenantResourceId で参照する。
resource allowedLocationsAssignment 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: 'capstone-allowed-locations'
  properties: {
    displayName: '許可リージョン以外へのリソース作成を拒否'
    policyDefinitionId: tenantResourceId('Microsoft.Authorization/policyDefinitions', allowedLocationsPolicyId)
    parameters: {
      listOfAllowedLocations: {
        value: allowedLocations
      }
    }
  }
}

// ---------- ② サブスクリプションへ入れ子デプロイ（Week 2/4）----------
// scope を切り替えることで、MG スコープのテンプレートから配下サブスクへ潜る。
module subScope 'modules/subscription.bicep' = {
  name: 'deploy-to-subscription'
  scope: subscription(subscriptionId)
  params: {
    rgName: rgName
    location: location
    storagePrefix: storagePrefix
    readerPrincipalId: readerPrincipalId
  }
}

@description('作成されたストレージアカウントのリソース ID')
output storageId string = subScope.outputs.storageId
