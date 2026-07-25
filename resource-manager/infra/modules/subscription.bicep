// =============================================================
// Week 9 最終プロジェクト：サブスクリプションスコープの部品
//   - targetScope = 'subscription'（Week 4）
//   - リソースグループを作成（Week 2：RG はサブスクスコープでしか作れない）
//   - そのRGへさらに入れ子デプロイして実リソースを作る（Week 2/4）
// =============================================================

targetScope = 'subscription'

@description('作成するリソースグループ名')
param rgName string

@description('リソースのリージョン')
param location string

@description('ストレージ名の接頭辞')
param storagePrefix string

@description('RG に Reader を与えるプリンシパル ID（空ならスキップ）')
param readerPrincipalId string = ''

// リソースグループの作成（サブスクスコープの仕事）
resource rg 'Microsoft.Resources/resourceGroups@2024-11-01' = {
  name: rgName
  location: location
}

// 作成した RG へ入れ子デプロイ（scope を RG に切り替え）。
// rg.name を参照することで「rg が先に要る」依存が自動で張られる（Week 4）。
module rgScope 'resourceGroup.bicep' = {
  name: 'deploy-to-resourcegroup'
  scope: resourceGroup(rg.name)
  params: {
    location: location
    storagePrefix: storagePrefix
    readerPrincipalId: readerPrincipalId
  }
}

output storageId string = rgScope.outputs.storageId
