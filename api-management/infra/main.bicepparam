using './main.bicep'

// デプロイ前にここを自分の値に変更する
param publisherEmail = 'you@example.com'
param publisherName = 'Learning Lab'

// Azure Functions のベース URL（/api まで含める）
// 例: https://func-orders-xxxx.azurewebsites.net/api
param backendUrl = 'https://REPLACE-ME.azurewebsites.net/api'

// apimName は既定で一意名が生成される。固定したい場合のみ指定:
// param apimName = 'apim-week10-demo'
