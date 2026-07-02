// Week 17 最終プロジェクト — 3サービス連携の基盤を一括構築
// Service Bus（確実な処理）／ Event Hubs（大量取り込み）／ Event Grid（反応）＋ Storage（checkpoint/DLQ）
// 注意：学習用テンプレート。本番はネットワーク制限・マネージドID・最小権限を追加すること。

@description('リソース名のベース（グローバル一意化に uniqueString を使用）')
param baseName string = 'msg${uniqueString(resourceGroup().id)}'

@description('デプロイ先リージョン')
param location string = resourceGroup().location

// ---- Service Bus：業務メッセージング（確実な処理） ----
resource sb 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: 'sb-${baseName}'
  location: location
  sku: { name: 'Standard', tier: 'Standard' } // Topic/セッション/重複検出を使うため Standard
}

resource ordersQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: sb
  name: 'orders'
  properties: {
    maxDeliveryCount: 10 // 超過で DLQ 行き（Week 4 §1）
    deadLetteringOnMessageExpiration: true
    lockDuration: 'PT1M'
  }
}

// ---- Event Hubs：ストリーミング（大量取り込み） ----
resource eh 'Microsoft.EventHub/namespaces@2024-01-01' = {
  name: 'eh-${baseName}'
  location: location
  sku: { name: 'Standard', tier: 'Standard' }
  properties: {
    isAutoInflateEnabled: true // Week 7 §5
    maximumThroughputUnits: 4
  }
}

resource telemetryHub 'Microsoft.EventHub/namespaces/eventhubs@2024-01-01' = {
  parent: eh
  name: 'telemetry'
  properties: {
    partitionCount: 4 // 作成時に固定（Week 7 §2）
    messageRetentionInDays: 1
  }
}

resource analyticsCg 'Microsoft.EventHub/namespaces/eventhubs/consumergroups@2024-01-01' = {
  parent: telemetryHub
  name: 'analytics' // $Default 以外の用途別グループ（Week 7 §3）
}

// ---- Event Grid：反応（CloudEvents 入力の Custom トピック） ----
resource egTopic 'Microsoft.EventGrid/topics@2022-06-15' = {
  name: 'egt-${baseName}'
  location: location
  properties: {
    inputSchema: 'CloudEventSchemaV1_0' // Week 11 §4 推奨
  }
}

// ---- Storage：Event Hubs の checkpoint と Event Grid の DLQ 用 ----
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: take('st${baseName}', 24)
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storage
  name: 'default'
}

resource checkpointContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'checkpoints' // Event Hubs コンシューマーの checkpoint（Week 8）
}

resource deadletterContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'eventgrid-deadletter' // Event Grid の DLQ（Week 12 §3-3）
}

// ---- 出力（クライアント/Functions が使う接続先） ----
output serviceBusFqdn string = '${sb.name}.servicebus.windows.net'
output eventHubsFqdn string = '${eh.name}.servicebus.windows.net'
output eventHubName string = telemetryHub.name
output eventGridEndpoint string = egTopic.properties.endpoint
output storageAccountName string = storage.name
output storageBlobEndpoint string = storage.properties.primaryEndpoints.blob
