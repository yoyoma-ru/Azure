# topics/ — 機能別まとめ（Week 別カリキュラムとは独立）

学習プラン（`notes/` の 10 週カリキュラム）とは**独立した別の保管場所**。会話や検証で深掘りした「製品の特定機能」を、**1 トピック 1 ファイルで self-contained（それ単体で読める）**にまとめる。

> **運用の分離**：`notes/`＝体系的な学習プラン、`topics/`＝それ以外に学んだこと。両者は別トラックとして分けて保存する。

## 索引

| トピック | 内容 | ファイル |
|---|---|---|
| カスタムスクリプト | Custom Script Extension の正体・Batch では予約で start task を使う・**Linux/インターネット経由の実機検証（成功）**・start task か拡張かの判定・拡張機能の許可リスト/2種類のDL/WireServer・DL 失敗トラブルシュート・出典 | [custom-script.md](custom-script.md) |
| ノード通信モード | クラシック vs 簡略化（接続の向き・ネットワークルール 29876/29877 vs 443・簡略化のメリット・クラシック廃止・2つのエンドポイント(アカウント/ノード管理)・private endpoint のつまずき・ノード間通信との混同注意） | [node-communication-mode.md](node-communication-mode.md) |
| 計算ノードの用語整理 | 計算ノード＝コンピューティングノード＝Batch 計算ノード＝compute node（訳語の揺れ）・compute node の正体・「Simplified 計算ノード通信」との違い | [compute-node-terminology.md](compute-node-terminology.md) |

## 書き方の方針
- である調。Mermaid・表・用語補足を使う。
- 技術的事実は公式ドキュメントで裏取りし、出典 URL を残す。
- **各ノートは self-contained**：それ単体で完結させ、`notes/`（Week）へはリンクしない。相互参照するなら **topic 同士**でリンクする。
