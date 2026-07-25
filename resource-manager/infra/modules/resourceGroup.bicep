// =============================================================
// Week 9 最終プロジェクト：リソースグループスコープの部品
//   - targetScope は既定の resourceGroup（Week 4：RG デプロイでは省略可）
//   - 実リソース（ストレージアカウント）を作成（Week 3/4）
//   - RG スコープの RBAC ロール割り当て（Week 6）。principalId が空ならスキップ（Week 4 の if）
// =============================================================

@description('リソースのリージョン')
param location string = resourceGroup().location

@description('ストレージ名の接頭辞')
@minLength(3)
@maxLength(11)
param storagePrefix string

@description('Reader を与えるプリンシパル ID（空ならスキップ）')
param readerPrincipalId string = ''

// Azure 全体で一意なストレージ名を生成（Week 3：uniqueString）
var storageName = '${storagePrefix}${uniqueString(resourceGroup().id)}'

// 組み込みロール Reader の定義 ID（GUID）
var readerRoleId = 'acdd72a7-3385-48ef-bd42-f606fba81ae7'

resource storage 'Microsoft.Storage/storageAccounts@2025-06-01' = {
  name: storageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
  tags: {
    env: 'capstone'
    managedBy: 'arm-template'
  }
}

// RBAC：指定プリンシパルに、このストレージへの Reader を割り当て（Week 6）
// principalId が空のときは条件でスキップ（Week 4 の if）。
resource readerAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(readerPrincipalId)) {
  name: guid(storage.id, readerPrincipalId, readerRoleId)
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', readerRoleId)
    principalId: readerPrincipalId
  }
}

output storageId string = storage.id
