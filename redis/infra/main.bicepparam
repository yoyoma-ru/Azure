using './main.bicep'

// リージョン内で一意な名前に変更してよい（既定でも一意文字列が付く）
param redisName = 'redis-week9-REPLACEME'

// 必要に応じて変更
param location = 'japaneast'

// 学習用は最小の Balanced_B0。容量を増やすなら Balanced_B1 / Balanced_B3 / MemoryOptimized_M10 など（Week 6）
param skuName = 'Balanced_B0'

// Functions のマネージドID の objectId を入れるとキーレス認証の割り当てが作られる（Week 7）。
// 空のままならアクセスポリシー割り当ては作成されない。
//   取得例: az functionapp identity show -g <rg> -n <func> --query principalId -o tsv
param principalId = ''
