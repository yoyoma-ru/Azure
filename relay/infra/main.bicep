// Azure Relay 最終PJ: 名前空間 + Hybrid Connection + Listen専用/Send専用 認可ルール
// 教材 relay/notes/relay-week8.md の成果物。W2(リソースモデル)+W6(最小権限)の実装。

@description('Relay 名前空間名（6〜50文字・グローバル一意）')
@minLength(6)
@maxLength(50)
param namespaceName string

@description('Hybrid Connection 名（＝path）')
param hybridConnectionName string = 'inventory'

@description('デプロイ先リージョン')
param location string = resourceGroup().location

@description('センダーにも認可(Send トークン)を要求するか。false で匿名センダー許可')
param requiresClientAuthorization bool = true

// 名前空間（SKU は Standard のみ）
resource ns 'Microsoft.Relay/namespaces@2024-01-01' = {
  name: namespaceName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {}
}

// Hybrid Connection（中継の1単位・ランデブーポイント）
resource hc 'Microsoft.Relay/namespaces/hybridConnections@2024-01-01' = {
  parent: ns
  name: hybridConnectionName
  properties: {
    requiresClientAuthorization: requiresClientAuthorization
    userMetadata: 'inventory listener endpoint'
  }
}

// この Hybrid Connection 専用の Listen だけの鍵（社内リスナーへ配布）
resource listenRule 'Microsoft.Relay/namespaces/hybridConnections/authorizationRules@2024-01-01' = {
  parent: hc
  name: 'listen-only'
  properties: {
    rights: [
      'Listen'
    ]
  }
}

// この Hybrid Connection 専用の Send だけの鍵（外部センダーへ配布）
resource sendRule 'Microsoft.Relay/namespaces/hybridConnections/authorizationRules@2024-01-01' = {
  parent: hc
  name: 'send-only'
  properties: {
    rights: [
      'Send'
    ]
  }
}

output namespaceHost string = '${ns.name}.servicebus.windows.net'
output hybridConnectionName string = hc.name
output listenRuleName string = listenRule.name
output sendRuleName string = sendRule.name
