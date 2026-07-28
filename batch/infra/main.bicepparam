// Week 10 最終プロジェクト：main.bicep 用のパラメータ（Week 4/ARM教材の .bicepparam）
using './main.bicep'

param prefix = 'batchlearn'
param vmSize = 'STANDARD_D2S_V3'
param maxNodes = 3
// location は既定でリソースグループのリージョンを使う（必要なら明示指定）
