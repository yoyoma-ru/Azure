// W10 最終PJ：main.bicep のパラメータ。
// <YOUR_ACR_NAME> を実際に作成した ACR 名（世界で一意・英数小文字）に置換すること。
using './main.bicep'

param acrName = '<YOUR_ACR_NAME>'
param containerImage = '<YOUR_ACR_NAME>.azurecr.io/aca-capstone:v1'
param targetPort = 8000
param minReplicas = 0
param maxReplicas = 5
