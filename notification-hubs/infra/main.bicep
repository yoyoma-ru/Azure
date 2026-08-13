// Azure Notification Hubs 最終PJ（W10）インフラ定義
// Namespace（名前空間）＋ Hub（ハブ）＋ 送信専用アクセスポリシーを宣言的に作成する。
// 参照：W3（名前空間とハブ・SKU）、W8（最小権限の Send 専用ポリシー）

@description('デプロイ先リージョン（既定：リソースグループと同じ）')
param location string = resourceGroup().location

@description('NH 名前空間名（DNS 名になるためグローバルに一意にする）')
param namespaceName string

@description('ハブ名（1 アプリ分の通知窓口）')
param hubName string = 'hub-demo'

@allowed([
  'Free'
  'Basic'
  'Standard'
])
@description('料金プラン（SKU）。学習は Free で十分（W3）')
param skuName string = 'Free'

// 名前空間：料金・課金・DNS 名の単位（W3 §1）
resource namespace 'Microsoft.NotificationHubs/namespaces@2023-09-01' = {
  name: namespaceName
  location: location
  sku: {
    name: skuName
  }
}

// ハブ：アプリ／環境ごとの通知窓口。PNS 資格情報はここに設定する（W3 §4）
resource hub 'Microsoft.NotificationHubs/namespaces/notificationHubs@2023-09-01' = {
  parent: namespace
  name: hubName
  location: location
  properties: {}
}

// 最小権限：送信専用ポリシー（W8 §6）。送信サービスには Full ではなくこれを渡す想定。
resource sendRule 'Microsoft.NotificationHubs/namespaces/notificationHubs/authorizationRules@2023-09-01' = {
  parent: hub
  name: 'SendOnly'
  properties: {
    rights: [
      'Send'
    ]
  }
}

output namespaceName string = namespace.name
output hubName string = hub.name
output sendRuleName string = sendRule.name
