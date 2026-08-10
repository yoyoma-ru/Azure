using './main.bicep'

// マネージドID を置くリージョン（システム割り当てに必須・W7）
param location = 'japaneast'

// 必須タグ（modify で自動付与・W4）
param requiredTagName = 'environment'
param requiredTagValue = 'production'

// 作成を許可するリージョン（組み込み Allowed locations に渡す・W1/W5）
param allowedLocations = [
  'japaneast'
  'japanwest'
]
