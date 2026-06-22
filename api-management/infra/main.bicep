// =============================================================
// Week 10 実装：API Management 一式（IaC）
//   - APIM サービス（Developer ティア・システム割り当て Managed Identity）
//   - Application Insights + Log Analytics（監視・Week 8）
//   - APIM ロガー/診断（App Insights 連携）
//   - Backend エンティティ（Week 2）
//   - Named value（Week 2/5）
//   - Orders API + Operation 3つ + API ポリシー（Week 3/4）
//   - Product + API 割り当て + Subscription（Week 2/6）
// 学習用なので 1 ファイルにまとめている（実務ではモジュール分割を検討）
// =============================================================

@description('APIM サービス名（グローバルに一意）')
param apimName string = 'apim-week10-${uniqueString(resourceGroup().id)}'

@description('発行者メール（必須・通知先）')
param publisherEmail string

@description('発行者名')
param publisherName string = 'Learning Lab'

@description('リソースのリージョン')
param location string = resourceGroup().location

@description('バックエンドの URL。Azure Functions の場合は /api まで含める（例: https://<func>.azurewebsites.net/api）')
param backendUrl string

// ---------- 監視：Log Analytics + Application Insights ----------
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${apimName}'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${apimName}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// ---------- APIM サービス本体（Managed Identity 有効化）----------
resource apim 'Microsoft.ApiManagement/service@2023-09-01-preview' = {
  name: apimName
  location: location
  sku: {
    name: 'Developer' // 学習用。全機能が使え安価（本番 SLA なし）
    capacity: 1
  }
  identity: {
    type: 'SystemAssigned' // バックエンド認証（authentication-managed-identity）や Key Vault 参照に使う
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
}

// ---------- APIM ロガー（App Insights 連携・Week 8）----------
resource apimLogger 'Microsoft.ApiManagement/service/loggers@2023-09-01-preview' = {
  parent: apim
  name: 'appinsights-logger'
  properties: {
    loggerType: 'applicationInsights'
    resourceId: appInsights.id
    credentials: {
      instrumentationKey: appInsights.properties.InstrumentationKey
    }
  }
}

// ---------- 診断（ゲートウェイのテレメトリを App Insights へ）----------
resource apimDiagnostics 'Microsoft.ApiManagement/service/diagnostics@2023-09-01-preview' = {
  parent: apim
  name: 'applicationinsights'
  properties: {
    loggerId: apimLogger.id
    alwaysLog: 'allErrors'
    sampling: {
      samplingType: 'fixed'
      percentage: 100 // 学習用に全件。本番はコストに応じて下げる（Week 8）
    }
  }
}

// ---------- Named value（環境ごとに差し替える値・Week 2/5）----------
resource backendNamedValue 'Microsoft.ApiManagement/service/namedValues@2023-09-01-preview' = {
  parent: apim
  name: 'orders-backend-url'
  properties: {
    displayName: 'orders-backend-url'
    value: backendUrl
    secret: false
  }
}

// ---------- Backend エンティティ（再利用可能な接続定義・Week 2）----------
resource ordersBackend 'Microsoft.ApiManagement/service/backends@2023-09-01-preview' = {
  parent: apim
  name: 'orders-backend'
  properties: {
    title: 'Orders Function backend'
    url: backendUrl
    protocol: 'http'
  }
}

// ---------- Orders API ----------
resource ordersApi 'Microsoft.ApiManagement/service/apis@2023-09-01-preview' = {
  parent: apim
  name: 'orders-api'
  properties: {
    displayName: 'Orders API'
    path: 'store' // 公開 URL: https://<apim>.azure-api.net/store/...
    protocols: [ 'https' ]
    subscriptionRequired: true
    serviceUrl: backendUrl
  }
}

// Operation: GET /orders/{id}
resource opGetOrder 'Microsoft.ApiManagement/service/apis/operations@2023-09-01-preview' = {
  parent: ordersApi
  name: 'get-order'
  properties: {
    displayName: 'Get order'
    method: 'GET'
    urlTemplate: '/orders/{id}'
    templateParameters: [
      { name: 'id', type: 'string', required: true }
    ]
  }
}

// Operation: GET /orders
resource opListOrders 'Microsoft.ApiManagement/service/apis/operations@2023-09-01-preview' = {
  parent: ordersApi
  name: 'list-orders'
  properties: {
    displayName: 'List orders'
    method: 'GET'
    urlTemplate: '/orders'
  }
}

// Operation: POST /orders
resource opCreateOrder 'Microsoft.ApiManagement/service/apis/operations@2023-09-01-preview' = {
  parent: ordersApi
  name: 'create-order'
  properties: {
    displayName: 'Create order'
    method: 'POST'
    urlTemplate: '/orders'
  }
}

// ---------- API ポリシー（XML を外部ファイルから読み込み・Week 3/4）----------
resource ordersApiPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-09-01-preview' = {
  parent: ordersApi
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: loadTextContent('policies/api-policy.xml')
  }
  dependsOn: [ opGetOrder, opListOrders, opCreateOrder ]
}

// ---------- Product + API 割り当て + Subscription（Week 2/6）----------
resource starterProduct 'Microsoft.ApiManagement/service/products@2023-09-01-preview' = {
  parent: apim
  name: 'starter'
  properties: {
    displayName: 'Starter'
    description: '学習用プロダクト（自動承認・公開）'
    subscriptionRequired: true
    approvalRequired: false
    state: 'published'
  }
}

resource productApiLink 'Microsoft.ApiManagement/service/products/apis@2023-09-01-preview' = {
  parent: starterProduct
  name: ordersApi.name
}

resource starterSubscription 'Microsoft.ApiManagement/service/subscriptions@2023-09-01-preview' = {
  parent: apim
  name: 'starter-sub'
  properties: {
    displayName: 'Starter subscription'
    scope: starterProduct.id // プロダクト単位のサブスクリプション
    state: 'active'
  }
  dependsOn: [ productApiLink ]
}

// ---------- 出力 ----------
output apimGatewayUrl string = '${apim.properties.gatewayUrl}/store'
output apimName string = apim.name
output subscriptionName string = starterSubscription.name
// ※ サブスクリプションキーは出力しない（シークレットのため）。取得方法は week10.md 参照
output appInsightsName string = appInsights.name
