// Week 10 実装：Blob Storage 一式を IaC 化
// - Storage アカウント（汎用v2・LRS・HTTPS強制・最小TLS1.2・公開アクセス無効）… Week 5
// - Blob サービス（バージョニング・ソフトデリート）… Week 6
// - コンテナ uploads … Week 2
// - Log Analytics ＋ 診断設定 … Week 8

// ---- パラメータ ----
@minLength(3)
@maxLength(24)
@description('グローバルで一意な小文字英数字のストレージアカウント名')
param storageAccountName string

@description('リソースを作成するリージョン')
param location string = resourceGroup().location

@description('Blob を入れるコンテナ名')
param containerName string = 'uploads'

@description('Log Analytics ワークスペース名')
param logAnalyticsName string = '${storageAccountName}-law'

@description('ソフトデリートの保持日数')
@minValue(1)
@maxValue(365)
param softDeleteDays int = 7

// ---- Log Analytics（監視の受け皿）… Week 8 ----
resource law 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// ---- ストレージアカウント本体 … Week 1/5 ----
resource sa 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: { name: 'Standard_LRS' } // Week 6：学習用は最安の LRS（本番は ZRS/GZRS を検討）
  kind: 'StorageV2'             // Week 1：汎用 v2
  properties: {
    supportsHttpsTrafficOnly: true   // Week 5：HTTPS 強制
    minimumTlsVersion: 'TLS1_2'      // Week 5：最小 TLS 1.2
    allowBlobPublicAccess: false     // Week 5：匿名公開を禁止
    allowSharedKeyAccess: true       // 学習用に true。キーレス徹底なら false も可（Week 4）
    accessTier: 'Hot'                // Week 7：既定のアクセス層
  }
}

// ---- Blob サービス（データ保護）… Week 6 ----
resource blobSvc 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: sa
  name: 'default'
  properties: {
    isVersioningEnabled: true // Week 6：バージョニング（上書き前の版を保持）
    deleteRetentionPolicy: {
      enabled: true
      days: softDeleteDays // Week 6：Blob ソフトデリート
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: softDeleteDays // Week 6：コンテナ ソフトデリート
    }
  }
}

// ---- コンテナ uploads … Week 2 ----
resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobSvc
  name: containerName
  properties: {
    publicAccess: 'None' // Week 4/5：匿名アクセス不可
  }
}

// ---- 診断設定（Blob のログ/メトリックを Log Analytics へ）… Week 8 ----
resource diag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-law'
  scope: blobSvc
  properties: {
    workspaceId: law.id
    logs: [
      { category: 'StorageRead', enabled: true }
      { category: 'StorageWrite', enabled: true }
      { category: 'StorageDelete', enabled: true }
    ]
    metrics: [
      { category: 'Transaction', enabled: true }
    ]
  }
}

// ---- 出力 ----
output storageAccountName string = sa.name
output blobEndpoint string = sa.properties.primaryEndpoints.blob
output containerName string = container.name
