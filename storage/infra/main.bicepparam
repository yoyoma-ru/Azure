using './main.bicep'

// グローバルで一意な名前に変更すること（小文字英数字・3〜24文字）
param storageAccountName = 'stweek10REPLACEME'

// 必要に応じて変更
param location = 'japaneast'
param containerName = 'uploads'
param softDeleteDays = 7
