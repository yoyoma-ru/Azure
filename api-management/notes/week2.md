# Week 2 — オブジェクトモデルとリクエストの流れ

> **Phase 1a** | 学習プラン Week 2 / 10  
> 学習目標：APIM の中核オブジェクト（API・Operation・Product・Subscription・Backend・Named value）の役割と関係を図解でき、1 リクエストがどう処理されるかを説明できる

---

## 0. 今週の見取り図

Week 1 で「APIM は API の公開面（ファサード）」と理解した。
今週は、その公開面が**どんな部品（オブジェクト）で構成されているか**を分解する。

```mermaid
flowchart LR
    U["User<br/>利用者"]
    SUB["Subscription<br/>アクセス権 + キー"]
    PRD["Product<br/>公開単位"]
    API["API<br/>操作のまとまり"]
    OP["Operation<br/>個々のエンドポイント"]
    BE["Backend<br/>実体への接続"]

    U -->|"保有"| SUB
    SUB -->|"スコープ"| PRD
    PRD -->|"含む"| API
    API -->|"含む"| OP
    API -->|"転送先"| BE
```

> ざっくり：**利用者**が**サブスクリプション（キー）**を持ち、それで**プロダクト**に含まれる**API**の**オペレーション**を呼ぶ。API は**バックエンド**へ転送する。

---

## 1. API と Operation

### API
関連する操作を 1 つにまとめた**論理的なまとまり**。
- **フロントエンド**（外部に公開される形：URL・パラメータ・認証）と、**バックエンド**（実体）を持つ
- 例：「注文 API」「天気 API」

> **「論理的なまとまり」とは？**
> 「物理的には別々でも、意味の上で 1 つにグループ化したもの」のこと。
> 注文に関する操作が技術的にはバラバラの URL でも──
> ```
> GET    /orders/{id}        注文を取得
> POST   /orders             注文を作る
> DELETE /orders/{id}        注文を消す
> ```
> 人間から見れば「全部"注文"に関する操作」。これを「注文 API」という 1 つの箱にまとめる括り方が**論理的なまとまり**。
> **イメージ**：本棚の「料理」コーナー。物理的には別々の本（= Operation）を、「料理」の札（= API）で 1 棚にまとめている。「論理的」= 物理的な実体ではなく人間が意味で決めたグループ。

### Operation
API の中の**個々のエンドポイント**。HTTP メソッド + URL テンプレートで定義する。
- 例：`GET /orders/{id}`、`POST /orders`、`DELETE /orders/{id}`

### API の URL 構造

```
https://{apim名}.azure-api.net / {api-suffix} / {operationのパス}
        └─ ゲートウェイのホスト ─┘ └ API 識別 ┘ └─ 操作 ─┘
```

例：`https://contoso.azure-api.net/store/orders/42`
- `contoso.azure-api.net` … APIM ゲートウェイ
- `store` … この API の suffix（API ごとに設定）
- `orders/42` … Operation `GET /orders/{id}` に id=42 でマッチ

> **フロントエンドとバックエンドは別 URL でよい**
> 公開 URL が `.../store/orders/42` でも、転送先のバックエンドは `https://internal-order-svc:8080/api/v3/order?id=42` のように全く違ってよい。この「付け替え」こそファサードの役割（変換は Week 4）。

---

## 2. Product（プロダクト）

1 つ以上の API を束ねた**公開単位**。「誰に・どんな条件で使わせるか」を定義する。

| Product が決めること | 例 |
|---|---|
| どの API を含むか | 注文 API + 在庫 API をまとめて公開 |
| 利用条件 | 月 1000 コールまで、レート 10/分 |
| 公開状態 | 公開（published）/ 非公開（draft） |
| サブスクリプション要否 | 必要 / 不要 |
| 承認フロー | 申請を自動承認 / 管理者が手動承認 |

### 典型例：同じ API を別条件で出す

```mermaid
flowchart LR
    API["注文 API（実体は 1 つ）"]
    FREE["Free プロダクト<br/>月 1000 コール・承認制"]
    PRO["Premium プロダクト<br/>無制限・自動承認"]

    API -->|"含まれる"| FREE
    API -->|"含まれる"| PRO
```

同じ 1 つの API を、「無料枠（制限あり）」と「有料枠（制限なし）」の 2 プロダクトで提供できる。

### Open product と Protected product
- **Protected（保護）**：利用にサブスクリプションが必要（既定・一般的）
- **Open（開放）**：サブスクリプション不要で誰でも呼べる

---

## 3. Subscription（サブスクリプション）とキー

利用者が持つ**アクセス権**。これに紐づく**サブスクリプションキー**で API を呼ぶ。

> ⚠️ Azure の「サブスクリプション（課金単位）」とは**全く別物**。APIM 内の「API を使う権利」のこと。

### キーの渡し方
呼び出し時に HTTP ヘッダ（またはクエリ）でキーを送る：
```
curl -H "Ocp-Apim-Subscription-Key: <キー>" \
  "https://contoso.azure-api.net/store/orders/42"
```
- ヘッダ：`Ocp-Apim-Subscription-Key: <キー>`
- クエリ：`?subscription-key=<キー>`（簡便だが URL に残るので非推奨寄り）

> **ヘッダとクエリとは？**
> どちらも「HTTP リクエストに追加情報を載せる場所」。場所が違うだけ。手紙にたとえると：
>
> | 場所 | 書き方 | イメージ |
> |---|---|---|
> | **クエリ** | URL の `?key=value` 部分 | 住所末尾の補足。**URL に丸見え** |
> | **ヘッダ** | リクエストの付帯情報欄 | 封筒に貼る付箋。URL には出ない |
> | （参考）ボディ | リクエスト本文 | 手紙の中身そのもの |
>
> **なぜヘッダ推奨か**：クエリ（URL）に書くとブラウザ履歴・サーバのアクセスログ・共有 URL にキーが残る。ヘッダなら URL に出ないので漏れにくい。

### キーが 2 本ある理由（primary / secondary）
**無停止でローテーション**するため。
1. 普段は primary を使う
2. 漏洩・定期更新時：secondary に切り替え → primary を再生成 → また primary に戻す
3. どの瞬間も「有効なキーが 1 本以上ある」状態を保てる

### サブスクリプションのスコープ（3 種）

```mermaid
flowchart TD
    S1["全 API（All APIs）<br/>サービス全体に有効"]
    S2["Product 単位<br/>そのプロダクトの API に有効"]
    S3["API 単位<br/>特定の 1 API だけに有効"]
```

| スコープ | 用途 |
|---|---|
| All APIs | 管理者・内部利用など全部使いたい |
| Product | 一般的。プロダクトの利用条件ごと管理 |
| API | 単一 API だけをピンポイントで使わせたい |

---

## 4. Backend（バックエンド）

バックエンドサービスの**接続情報を再利用可能なエンティティ**として定義したもの。

| Backend が持つ情報 | 例 |
|---|---|
| URL | `https://internal-order-svc.example.com` |
| 認証 | クライアント証明書 / ヘッダ / Managed Identity |
| TLS 設定 | 証明書検証の有無など |

> **「エンティティ」とは？**
> 「名前を付けて独立して管理できる"モノ"」のこと。日本語なら「登録された 1 件の項目／オブジェクト」が近い。
> **イメージ**：スマホの「連絡先」。毎回電話番号を手打ちする（= URL 直書き）のではなく、「お母さん」という連絡先を 1 件登録しておけば、各アプリから名前で選べる。番号が変わっても連絡先を 1 回直すだけで全部に反映される。
> Backend をエンティティにする = バックエンドの接続情報を"連絡先"として 1 件登録し、各 API から名前で参照できるようにすること。

### なぜ「エンティティ」にするのか（直書きとの違い）
API のバックエンド URL を直接書くこともできるが、Backend エンティティにしておくと：
- **再利用**：複数 API が同じバックエンドを参照できる
- **一元管理**：URL や認証が変わっても 1 箇所直すだけ
- **発展**：ロードバランシング・サーキットブレーカーを後付けできる（Week 9）

ポリシーから `set-backend-service` で参照する（Week 3〜4）。

---

## 5. Named value（名前付き値）

ポリシーやバックエンド設定で使う**定数・シークレットの集中管理**。プログラミングの環境変数／定数とほぼ同じ発想。「APIM 全体で使い回せる名前付きの変数」と捉えるとよい。

### 何が嬉しいのか（問題 → 解決）

複数のポリシーで同じ URL や API キーを使う場面を考える。

**❌ Named value なし**
```xml
<!-- ポリシーA -->
<set-backend-service base-url="https://api.weather.com/v3" />
<set-header name="X-Api-Key"><value>secret-xyz-123</value></set-header>

<!-- ポリシーB（別のAPI）-->
<set-backend-service base-url="https://api.weather.com/v3" />   <!-- 同じURLをまた書く -->
<set-header name="X-Api-Key"><value>secret-xyz-123</value></set-header>  <!-- キーが平文で重複 -->
```
- URL やキーが**あちこちにコピペ**される
- 本番切り替え時に全ポリシーを探して書き換える羽目になる
- シークレットが**ポリシー XML に平文で残る**

**✅ Named value あり**
```
[Named value 一覧]   ← ここに1回だけ登録
  weather-url = https://api.weather.com/v3   (プレーン値)
  weather-key = secret-xyz-123               (シークレット → 値はマスク)
```
```xml
<!-- ポリシーA も B も同じ書き方 -->
<set-backend-service base-url="{{weather-url}}" />
<set-header name="X-Api-Key"><value>{{weather-key}}</value></set-header>
```
`{{名前}}` と書くと、実行時に実際の値に**展開**される。

### 3 つの種類

| 種類 | 中身 | 表示 | 使いどころ |
|---|---|---|---|
| **プレーン値** | ただの文字列 | そのまま見える | URL・フラグ・タイムアウト秒数など隠す必要のない設定 |
| **シークレット** | 秘密の文字列 | `••••` でマスク | API キー・パスワード |
| **Key Vault 参照** | Key Vault のシークレットを指す | Vault 側で管理 | 本番シークレット（ローテーション自動追従）→ Week 5 |

### 一番効く場面：環境の切り替え
```
dev 環境の APIM:   weather-url = https://api-dev.weather.com
prod 環境の APIM:  weather-url = https://api.weather.com
```
ポリシー本体（`{{weather-url}}`）は**全環境で完全に同じ**。違うのは Named value の中身だけ。
→ dev で書いたポリシーを 1 文字も変えずに prod へ持っていける。

> **イメージ**：レシピの「塩 適量」。レシピ（= ポリシー）には「塩」とだけ書き、どの塩をどれだけ使うかは別管理。レシピを書き換えずに、使う塩だけ差し替えられる。

---

## 6. User / Group

主に **Developer Portal**（API 利用者向けサイト）の利用者管理。

| 概念 | 説明 |
|---|---|
| **User** | Developer Portal に登録した API 利用者（開発者） |
| **Group** | User の権限グループ。Product の可視性を Group 単位で制御 |

### 組み込み Group
- **Administrators** … APIM 管理者
- **Developers** … 登録済みの利用者
- **Guests** … 未登録の閲覧者
- + カスタム Group（例：「パートナー企業」だけに特定 Product を見せる）

---

## 7. 全体オブジェクト関係と用語の整理

### オブジェクト関係図

```mermaid
flowchart LR
    U["User"]
    G["Group"]
    SUB["Subscription<br/>+ キー"]
    PRD["Product"]
    API["API"]
    OP["Operation"]
    BE["Backend"]
    NV["Named value"]
    POL["Policy"]

    U -->|"所属"| G
    U -->|"保有"| SUB
    SUB -->|"スコープ対象"| PRD
    PRD -->|"含む"| API
    API -->|"含む"| OP
    API -->|"転送先"| BE
    POL -->|"参照"| NV
    POL -->|"適用先"| API
```

### 重要な用語まとめ

| 用語 | 一言説明 |
|---|---|
| API | 関連する操作の論理的なまとまり（フロント/バック両面を持つ） |
| Operation | API 内の個々のエンドポイント（メソッド + URL テンプレート） |
| Product | API を束ねた公開単位。利用条件・承認・公開状態を定義 |
| Subscription | 利用者のアクセス権。キーで API を呼ぶ。スコープは All/Product/API |
| サブスクリプションキー | primary/secondary の 2 本。無停止ローテーション用 |
| Backend | 再利用可能なバックエンド接続定義（URL・認証・TLS） |
| Named value | 定数・シークレットの集中管理（環境変数的） |
| User / Group | Developer Portal の利用者と権限グループ |

---

## 8. リクエストが処理される流れ（1 本のリクエスト視点）

ここまでの部品が、1 リクエストでどう絡むかを追う。

```mermaid
flowchart LR
    C["クライアント<br/>キー付きで呼び出し"]
    K["キー検証<br/>Subscription が有効か"]
    M["Operation 照合<br/>メソッド + パス"]
    F["転送<br/>Backend へ"]
    B["バックエンド処理"]
    R["クライアントへ応答"]

    C -->|"Ocp-Apim-Subscription-Key"| K
    K -->|"OK"| M
    M -->|"マッチした Operation"| F
    F -->|"Backend エンティティ"| B
    B -->|"結果"| R
```

1. クライアントが**サブスクリプションキー付き**でゲートウェイ URL を呼ぶ
2. APIM が**キーを検証**（無効なら `401 Access denied`）
3. URL とメソッドから**どの Operation か**を照合
4. （ポリシーを適用しつつ）**Backend へ転送**
5. バックエンドの応答を（ポリシーで加工しつつ）**クライアントへ返却**

> 「ポリシーを適用しつつ」の中身が Week 3〜4。今週は**部品の名前と関係**を確実に押さえる。

---

## ハンズオン チェックリスト

- [ ] Portal の「APIs」でデモ API を作成（`Echo API` テンプレート、または httpbin.org を手動登録）
- [ ] Operation を 1 つ追加（例：`GET /get`）し、**Test タブ**でゲートウェイ経由の呼び出しを実行
- [ ] Product を 1 つ作成 → 作った API を割り当て → Subscription を作成 → 発行キーを取得
- [ ] キー付きで `curl` 実行して 200 応答を確認
  ```
  curl -H "Ocp-Apim-Subscription-Key: <key>" \
    "https://<apim名>.azure-api.net/<suffix>/get"
  ```
- [ ] **キーを付けずに**呼んで `401 Access denied`（subscription key not found）を確認
- [ ] Week 1 のリクエストフロー図に Product / Subscription / Key を書き加える

---

## 自己チェック

週末にドキュメントを閉じて答えてみる。

1. **API・Product・Subscription の関係を第三者に図で説明できるか？**
   - キーワード：API＝操作のまとまり、Product＝公開単位、Subscription＝アクセス権

2. **同じ API を「無料枠」と「有料枠」で提供するには何を作るか？**
   - キーワード：Product を 2 つ、利用条件で差をつける

3. **サブスクリプションキーが 2 本ある理由は？**
   - キーワード：無停止ローテーション、primary/secondary

4. **Backend エンティティと、API にバックエンド URL を直書きする違いは？**
   - キーワード：再利用、一元管理、LB/サーキットブレーカーへの発展

5. **キーなしで呼ぶとどうなるか？どのステップで弾かれるか？**
   - キーワード：401 Access denied、キー検証ステップ

---

## 次週の予告（Week 3）

いよいよ APIM の心臓、**ポリシー**に入る：

- **4 セクション** — inbound / backend / outbound / on-error
- **4 スコープ** — Global / Product / API / Operation と評価順序
- **継承と `<base/>`** — 親ポリシーをどこで実行するか
- ポリシーがリクエスト/レスポンスの「どこで」効くかを正確に掴む
