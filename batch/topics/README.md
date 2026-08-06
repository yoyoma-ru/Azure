# topics/ — 機能別まとめ（Week 別カリキュラムとは独立）

`notes/weekN.md` の 10 週カリキュラムとは別に、**製品の特定機能について学んだことを 1 トピック 1 ファイル**でまとめていく場所。会話や検証で深掘りした内容を、後から引ける形で残す。

## 索引

| トピック | 内容 | ファイル |
|---|---|---|
| カスタムスクリプト | Custom Script Extension の正体・Batch では予約済みで start task を使う・Windows 検証手順・DL 失敗のトラブルシュート・出典 | [custom-script.md](custom-script.md) |
| ノード通信モード | クラシック vs 簡略化（接続の向き・ネットワークルール 29876/29877 vs 443・簡略化のメリット・クラシック廃止・2つのエンドポイント(アカウント/ノード管理)・private endpoint のつまずき・ノード間通信との混同注意） | [node-communication-mode.md](node-communication-mode.md) |
| 計算ノードの用語整理 | 計算ノード＝コンピューティングノード＝Batch 計算ノード＝compute node（訳語の揺れ）・compute node の正体・「Simplified 計算ノード通信」との違い | [compute-node-terminology.md](compute-node-terminology.md) |

## 書き方の方針
- である調。Mermaid・表・用語補足を使う（カリキュラムと同じ）。
- 技術的事実は公式ドキュメントで裏取りし、出典 URL を残す。
- 関連する `notes/weekN.md` へ相互リンクする（Week とトピックを行き来できるように）。
