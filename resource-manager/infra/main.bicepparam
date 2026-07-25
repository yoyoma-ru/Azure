using './main.bicep'

// デプロイ前にここを自分の値に変更する。
// 実行例：
//   az deployment mg create --management-group-id <MG-ID> \
//     --location japaneast --template-file main.bicep --parameters main.bicepparam

// 実リソースを作るサブスクリプションの ID（必須）
param subscriptionId = '00000000-0000-0000-0000-000000000000'

// 作成するリソースグループ名
param rgName = 'rg-arm-capstone'

// リージョン（allowedLocations に含まれる値にすること）
param location = 'japaneast'

// ストレージ名の接頭辞（3〜11文字）
param storagePrefix = 'capstone'

// 管理グループに割り当てる Allowed locations Policy が許可するリージョン
param allowedLocations = [
  'japaneast'
  'japanwest'
]

// RG に Reader を与えたいプリンシパル ID。不要なら空文字のまま（RBAC 割り当てをスキップ）
param readerPrincipalId = ''
