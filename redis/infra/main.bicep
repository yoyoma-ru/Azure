// =============================================================
// Week 9 実装：Azure Managed Redis 一式（IaC）
//   - Redis Enterprise クラスタ（= Azure Managed Redis 本体・Balanced_B0・学習用最小）… Week 1/6
//   - Redis Enterprise データベース（default・TLS必須・ポート10000）… Week 5/6
//   - Log Analytics + Application Insights（監視）… Week 8
//   - 診断設定（メトリック/ログを Log Analytics へ）… Week 8
//   - （任意）Entra ID アクセスポリシー割り当て：接続元プリンシパルに権限付与 … Week 7
// 学習用なので 1 ファイルにまとめている（実務ではモジュール分割を検討）
//
// ▼ 従来製品との違い（Cache for Redis vs Managed Redis）
//   - Cache for Redis  : リソース種別 Microsoft.Cache/redis、SKU は Basic/Standard/Premium/Enterprise（family C/P）
//   - Managed Redis    : リソース種別 Microsoft.Cache/redisEnterprise（Redis Enterprise ベース）、
//                        SKU は Balanced/MemoryOptimized/ComputeOptimized/FlashOptimized（例: Balanced_B0）
//   本ファイルは Managed Redis（redisEnterprise）を使う。
// =============================================================

@description('Managed Redis（Redis Enterprise）クラスタ名。リージョン内で一意')
param redisName string = 'redis-week9-${uniqueString(resourceGroup().id)}'

@description('リソースのリージョン')
param location string = resourceGroup().location

@description('Managed Redis の SKU。学習用は最小の Balanced_B0（約0.5GB・低コスト）。容量を増やすなら Balanced_B1, B3 … MemoryOptimized_M10 などへ（Week 6）')
param skuName string = 'Balanced_B0'

@description('Entra ID 認証を与える接続元プリンシパルの objectId（Functions のマネージドID など）。空なら割り当てを作らない（Week 7）')
param principalId string = ''

// ---------- 監視：Log Analytics + Application Insights … Week 8 ----------
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${redisName}'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${redisName}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// ---------- Managed Redis 本体（Redis Enterprise クラスタ）… Week 1/6 ----------
resource redis 'Microsoft.Cache/redisEnterprise@2024-10-01' = {
  name: redisName
  location: location
  sku: {
    name: skuName // Week 6：階層＝SKU 名で決まる。Balanced_B0 が最小
  }
  identity: {
    type: 'None' // このクラスタ自身は他リソースを呼ばないので ID 不要
  }
  properties: {
    minimumTlsVersion: '1.2' // Week 7：TLS 1.2 以上を強制（Managed Redis は常に TLS 必須）
  }
}

// ---------- Redis データベース（default）… Week 5/6 ----------
// Managed Redis は「クラスタ＋データベース」の2階層。実際の Redis エンドポイントはこの DB。
resource redisDb 'Microsoft.Cache/redisEnterprise/databases@2024-10-01' = {
  parent: redis
  name: 'default' // Managed Redis では DB 名は 'default' 固定
  properties: {
    clientProtocol: 'Encrypted'   // Week 7：TLS 必須（平文 'Plaintext' は学習でも使わない）
    port: 10000                   // Managed Redis 既定ポート（Cache for Redis の 6380 とは異なる）
    clusteringPolicy: 'OSSCluster' // Week 6：OSS クラスタ互換（クライアントがスロットを意識）
    evictionPolicy: 'VolatileLRU'  // Week 4：キャッシュ用途。TTL付きキーから LRU で追い出す
    persistence: {
      aofEnabled: false // Week 5：キャッシュ用途なので永続化なし（DB が真実源・落ちても再充填）
      rdbEnabled: false
    }
  }
}

// ---------- Entra ID アクセスポリシー割り当て（任意）… Week 7 ----------
// principalId が指定されたときだけ作成。接続元（Functions のマネージドID等）に
// 組み込みポリシー 'default'（フルアクセス相当）を与える。アクセスキー不要のキーレス認証。
resource accessPolicy 'Microsoft.Cache/redisEnterprise/databases/accessPolicyAssignments@2024-10-01' = if (!empty(principalId)) {
  parent: redisDb
  name: 'app-access'
  properties: {
    accessPolicyName: 'default'
    user: {
      objectId: principalId
    }
  }
}

// ---------- 診断設定（DB のメトリック/ログを Log Analytics へ）… Week 8 ----------
resource diag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-law'
  scope: redisDb
  properties: {
    workspaceId: logAnalytics.id
    metrics: [
      { category: 'AllMetrics', enabled: true }
    ]
  }
}

// ---------- 出力 ----------
output redisName string = redis.name
output redisHostName string = redis.properties.hostName // 接続先ホスト（例: <name>.<region>.redis.azure.net）
output redisPort int = redisDb.properties.port
output appInsightsConnectionString string = appInsights.properties.ConnectionString
