// =============================================================================
// Week 10 最終プロジェクト：Batch アカウント ＋ オートスケール付きプール（Spot 併用）
// -----------------------------------------------------------------------------
// この Bicep は「計算資源の器」を宣言的に作る（Resource Manager 教材の宣言型・冪等）。
//   1) Storage アカウント  … autostorage（入出力・アプリ配布の倉庫／Week 7）
//   2) Batch アカウント     … Storage を autoStorage として紐づけ（Week 2・7）
//   3) プール               … Ubuntu ノード＋オートスケール式で Spot を増減（Week 3・4）
// ジョブ／タスクの投入は Python（azure-batch SDK）側で行う（code/ を参照）。
// デプロイ先スコープはリソースグループ（既定）。
// =============================================================================

@description('リソース名の接頭辞（英小文字・数字。Storage 名の一意性のため短めに）')
@minLength(3)
@maxLength(11)
param prefix string = 'batchlearn'

@description('デプロイ先リージョン（既定はリソースグループと同じ）')
param location string = resourceGroup().location

@description('プールの VM サイズ（学習用は小さめ。作成後は変更不可／Week 3）')
param vmSize string = 'STANDARD_D2S_V3'

@description('オートスケールの上限ノード数（暴走防止のキャップ／Week 4）')
@minValue(1)
@maxValue(10)
param maxNodes int = 3

// Storage 名は 3-24 文字・英小文字数字のみ。prefix＋一意サフィックスで衝突回避。
var storageAccountName = toLower('${prefix}${uniqueString(resourceGroup().id)}')
var batchAccountName = toLower('${prefix}${uniqueString(resourceGroup().id, 'batch')}')
var poolId = 'e2e-pool'

// オートスケール式（Week 4 §5 の定番を Spot 主体にアレンジ）。
//   直近5分の保留タスク数の平均で Spot ノードを increase/decrease。
//   標本が 70% 未満なら 0 台（信頼できないので増やさない）。
//   Dedicated は 0、縮小時は走っているタスクを終わらせてから（taskcompletion）。
// 注：Bicep の三重引用符（複数行）文字列は補間されないため、${maxNodes} を効かせるには
//     単一引用符文字列＋改行エスケープ \n を使う（$Pending... 等の $ はそのままリテラル）。
var autoScaleFormula = '$samples = $PendingTasks.GetSamplePercent(TimeInterval_Minute * 5);\n$tasks = $samples < 70 ? 0 : avg($PendingTasks.GetSample(TimeInterval_Minute * 5));\n$TargetLowPriorityNodes = min(${maxNodes}, $tasks);\n$TargetDedicatedNodes = 0;\n$NodeDeallocationOption = taskcompletion;'

// 1) autostorage 用の Storage アカウント（Week 7）
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    // 注：Application Packages を使う場合、ファイアウォールや階層型名前空間は不可（Week 7）
  }
}

// 2) Batch アカウント（Storage を autoStorage として紐づけ／Week 2・7）
resource batchAccount 'Microsoft.Batch/batchAccounts@2024-07-01' = {
  name: batchAccountName
  location: location
  properties: {
    // Batch サービス割り当てモード（既定）。コアクォータはこのモードの上限に従う（Week 3・9）
    poolAllocationMode: 'BatchService'
    autoStorage: {
      storageAccountId: storage.id
    }
  }
}

// 3) オートスケール付きプール（Spot 併用／Week 3・4）
resource pool 'Microsoft.Batch/batchAccounts/pools@2024-07-01' = {
  parent: batchAccount
  name: poolId
  properties: {
    vmSize: vmSize
    deploymentConfiguration: {
      virtualMachineConfiguration: {
        // Marketplace イメージ＋対応する node agent SKU（組で指定／Week 3）
        imageReference: {
          publisher: 'canonical'
          offer: '0001-com-ubuntu-server-jammy'
          sku: '22_04-lts'
          version: 'latest'
        }
        nodeAgentSkuId: 'batch.node.ubuntu 22.04'
      }
    }
    // 手動固定（fixedScale）ではなくオートスケール式に委ねる（Week 4）
    scaleSettings: {
      autoScale: {
        formula: autoScaleFormula
        evaluationInterval: 'PT5M' // 最小 5 分（Week 4）
      }
    }
    // ノード起動時の初期化（Week 3）。ここでは共有ディレクトリに印を書くだけの例。
    startTask: {
      commandLine: '/bin/bash -c "echo started > $AZ_BATCH_NODE_SHARED_DIR/started.txt"'
      waitForSuccess: true
      userIdentity: {
        autoUser: {
          scope: 'Pool'
          elevationLevel: 'NonAdmin'
        }
      }
    }
  }
}

// 出力：Python アプリ（code/）が使う値
output batchAccountName string = batchAccount.name
@description('Batch アカウントのデータプレーン エンドポイント（Week 8）')
output batchAccountUrl string = 'https://${batchAccount.properties.accountEndpoint}'
output storageAccountName string = storage.name
output poolId string = poolId
