// =============================================================================
// Week 10 最終PJ — Azure Policy を Bicep で E2E 実装
//
// 構成：
//   ① カスタムポリシー定義（modify）  … 必須タグが無ければ自動付与
//   ② イニシアティブ（policySet）      … ①のカスタム定義 ＋ 組み込み「許可される場所」を束ねる
//   ③ 割り当て（assignment）           … ②をサブスクに割り当て（システム割り当てマネージドID付き）
//   ④ ロール割り当て                   … マネージドID に Tag Contributor を付与（SDK は手動＝W8）
//
// スコープはサブスクリプション（tenant ではなく subscription をターゲット）。
//   デプロイ： az deployment sub create -l <location> -f main.bicep -p main.bicepparam
// =============================================================================

targetScope = 'subscription'

// ---- パラメータ（割り当て時に差し込む値・W5/W6/W7）----------------------------
@description('マネージドID を置くリージョン（システム割り当てには location 必須・W7）')
param location string = 'japaneast'

@description('必須にするタグ名')
param requiredTagName string = 'environment'

@description('タグが無いとき自動付与する既定値')
param requiredTagValue string = 'production'

@description('リソース作成を許可するリージョン一覧（組み込み Allowed locations に渡す）')
param allowedLocations array = [
  'japaneast'
  'japanwest'
]

// ---- 定数：組み込みロール／組み込みポリシーの ID ------------------------------
// Tag Contributor（タグの読み書き）… modify の remediation 用（W4/W8）
var tagContributorRoleId = '4a9ae827-6dc8-4573-8ac7-8239d42aa03f'
// 組み込みポリシー「Allowed locations」（effect: deny）
var allowedLocationsBuiltinId = subscriptionResourceId('Microsoft.Authorization/policyDefinitions', 'e56962a6-4747-49cd-b67b-bf8b01975c4c')

// =============================================================================
// ① カスタムポリシー定義（modify）：必須タグが無ければ addOrReplace で付与
//    - mode: indexed（タグ強制なので・W2）
//    - if: タグが存在しない（W3 の exists false）
//    - then: modify（W4 の operations／roleDefinitionIds／conflictEffect）
// =============================================================================
resource ensureTagPolicy 'Microsoft.Authorization/policyDefinitions@2023-04-01' = {
  name: 'ensure-required-tag'
  properties: {
    policyType: 'Custom'
    mode: 'Indexed'
    displayName: '必須タグを自動付与する（modify）'
    description: '指定タグが無いリソースに、既定値でタグを付与する。'
    metadata: {
      category: 'Tags'
      version: '1.0.0'
    }
    parameters: {
      tagName: {
        type: 'String'
        metadata: {
          displayName: 'タグ名'
          description: '必須にするタグの名前'
        }
      }
      tagValue: {
        type: 'String'
        metadata: {
          displayName: 'タグ既定値'
          description: 'タグが無いとき付与する値'
        }
      }
    }
    policyRule: {
      if: {
        field: '[concat(\'tags[\', parameters(\'tagName\'), \']\')]'
        exists: 'false'
      }
      then: {
        effect: 'modify'
        details: {
          roleDefinitionIds: [
            subscriptionResourceId('Microsoft.Authorization/roleDefinitions', tagContributorRoleId)
          ]
          conflictEffect: 'deny'
          operations: [
            {
              operation: 'addOrReplace'
              field: '[concat(\'tags[\', parameters(\'tagName\'), \']\')]'
              value: '[parameters(\'tagValue\')]'
            }
          ]
        }
      }
    }
  }
}

// =============================================================================
// ② イニシアティブ（policySet）：カスタム modify ＋ 組み込み deny を束ねる（W6）
//    - イニシアティブのパラメータを各定義へ [parameters('...')] で引き回す
// =============================================================================
resource governanceInitiative 'Microsoft.Authorization/policySetDefinitions@2023-04-01' = {
  name: 'governance-baseline'
  properties: {
    policyType: 'Custom'
    displayName: 'ガバナンス基本セット（タグ＋リージョン）'
    description: '必須タグの自動付与と、許可リージョンの強制をまとめたイニシアティブ。'
    metadata: {
      category: 'Governance'
      version: '1.0.0'
    }
    parameters: {
      initTagName: {
        type: 'String'
        metadata: { displayName: 'タグ名' }
        defaultValue: 'environment'
      }
      initTagValue: {
        type: 'String'
        metadata: { displayName: 'タグ既定値' }
        defaultValue: 'production'
      }
      initAllowedLocations: {
        type: 'Array'
        metadata: {
          displayName: '許可リージョン'
          strongType: 'location'
        }
      }
    }
    policyDefinitions: [
      {
        policyDefinitionReferenceId: 'ensureTag'
        policyDefinitionId: ensureTagPolicy.id
        parameters: {
          tagName: { value: '[parameters(\'initTagName\')]' }
          tagValue: { value: '[parameters(\'initTagValue\')]' }
        }
      }
      {
        policyDefinitionReferenceId: 'allowedLocations'
        policyDefinitionId: allowedLocationsBuiltinId
        parameters: {
          listOfAllowedLocations: { value: '[parameters(\'initAllowedLocations\')]' }
        }
      }
    ]
  }
}

// =============================================================================
// ③ 割り当て（assignment）：イニシアティブをサブスクに割り当て（W7）
//    - identity: SystemAssigned（＋ location 必須）… modify の remediation 用
//    - enforcementMode: Default（強制）
// =============================================================================
resource assignment 'Microsoft.Authorization/policyAssignments@2023-04-01' = {
  name: 'governance-baseline-assign'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'ガバナンス基本セットの割り当て'
    policyDefinitionId: governanceInitiative.id
    enforcementMode: 'Default'
    parameters: {
      initTagName: { value: requiredTagName }
      initTagValue: { value: requiredTagValue }
      initAllowedLocations: { value: allowedLocations }
    }
  }
}

// =============================================================================
// ④ ロール割り当て：マネージドID に Tag Contributor を付与（W8）
//    - SDK/Bicep では自動付与されない → 明示的に作る（Portal のみ自動）
//    - name はスコープ内で一意な GUID
// =============================================================================
resource tagRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, assignment.name, tagContributorRoleId)
  properties: {
    principalId: assignment.identity.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', tagContributorRoleId)
    principalType: 'ServicePrincipal'
  }
}

// ---- 出力（後続の az policy コマンドで使う）----------------------------------
output policyDefinitionId string = ensureTagPolicy.id
output initiativeId string = governanceInitiative.id
output assignmentId string = assignment.id
output assignmentPrincipalId string = assignment.identity.principalId
