// =============================================================================
// W10 最終PJ：Azure Container Apps 一式を Bicep で宣言する。
//   Log Analytics（W2/W9） + Managed Environment（W2） +
//   User-assigned マネージド ID（W8） + ACR への AcrPull ロール割り当て（W8） +
//   Container App（Ingress=W3・スケールルール=W5・ヘルスプローブ=W9）。
//
// 前提：ACR を作成し、`az acr build` でイメージを push 済みであること（README 参照）。
//       ACR は本テンプレの外で用意し、ここでは existing 参照する（ビルド→デプロイの順序を守るため）。
//
// マネージド ID は user-assigned を採用：principalId が即時に判明するため、
// AcrPull ロール割り当てを同一デプロイ内で確実に先行させられる
// （system-assigned だとアプリ作成前に principalId が無く、pull と権限付与が競合しやすい＝W8）。
// =============================================================================

targetScope = 'resourceGroup'

@description('リソースの配置リージョン')
param location string = resourceGroup().location

@description('リソース名の接頭辞')
param namePrefix string = 'aca-capstone'

@description('既存 ACR 名（az acr build でイメージを push 済みであること）')
param acrName string

@description('デプロイするイメージ（例: <acr>.azurecr.io/aca-capstone:v1）')
param containerImage string

@description('コンテナが待ち受けるポート（Dockerfile / app の PORT と一致させる）')
param targetPort int = 8000

@description('最小レプリカ数（0 = ゼロスケール＝無アクセス時は課金なし）')
param minReplicas int = 0

@description('最大レプリカ数')
param maxReplicas int = 5

// AcrPull 組み込みロールの定義 ID（イメージの pull のみ許す最小権限＝W8）
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

var laName = '${namePrefix}-logs'
var envName = '${namePrefix}-env'
var appName = '${namePrefix}-app'
var uamiName = '${namePrefix}-id'

// ---- 既存 ACR（テンプレ外で作成・ビルド済み）を参照 --------------------------
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

// ---- Log Analytics ワークスペース（環境のログ集約先＝W2/W9） -----------------
resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: laName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// ---- User-assigned マネージド ID（W8） --------------------------------------
resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: uamiName
  location: location
}

// ---- ACR に対し UAMI へ AcrPull を付与（RBAC＝W8） --------------------------
// scope を acr にすることで「この ACR に限って pull を許す」最小スコープにする。
resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, uami.id, acrPullRoleId)
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ---- Managed Environment（アプリを囲う器＝W2） -----------------------------
resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

// ---- Container App 本体 ------------------------------------------------------
resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  // UAMI をアプリに割り当て（この ID で ACR から pull する）
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uami.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      // 単一リビジョンモード（W4）。HTTP 以外のイベントスケールでは single が推奨（W5）。
      activeRevisionsMode: 'single'
      // Ingress（W3）：外部公開・targetPort へ橋渡し・最新リビジョンへ 100%
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'auto'
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      // レジストリ認証（W8）：ユーザー名/パスワードではなく UAMI で pull
      registries: [
        {
          server: '${acrName}.azurecr.io'
          identity: uami.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'main'
          image: containerImage
          // Consumption の割当は決まった組み合わせ（0.5 vCPU : 1.0Gi＝W2）
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          // 設定注入（W8）：挨拶文とポートを環境変数で渡す
          env: [
            {
              name: 'APP_GREETING'
              value: 'Hello from Azure Container Apps (W10 capstone)'
            }
            {
              name: 'PORT'
              value: string(targetPort)
            }
          ]
          // ヘルスプローブ（W9）：/health を liveness/readiness の両方で叩く
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: targetPort
              }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: targetPort
              }
              initialDelaySeconds: 3
              periodSeconds: 5
            }
          ]
        }
      ]
      // スケール（W5）：HTTP 同時 50 リクエストで増、min=0 でゼロスケール
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
  // ロール割り当てが先に効いてからアプリを作る（pull 失敗を避ける）
  dependsOn: [
    acrPull
  ]
}

// ---- 出力 -------------------------------------------------------------------
output fqdn string = app.properties.configuration.ingress.fqdn
output appUrl string = 'https://${app.properties.configuration.ingress.fqdn}'
