const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Azure AI Search 入門 Week 1";

// Color palette
const C = {
  azureBlue:   "0078D4",
  darkBlue:    "003A6B",
  accentBlue:  "005BA1",
  lightBlue:   "E8F4FE",
  iceBlue:     "EFF6FF",
  white:       "FFFFFF",
  darkText:    "1A1A2E",
  grayText:    "605E5C",
  lightGray:   "F3F3F3",
  midGray:     "C8C6C4",
};
const F = { title: "Calibri", body: "Calibri", mono: "Consolas" };

// Helper: title bar (shared pattern)
function addTitleBar(slide, text, fontSize) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: C.lightBlue },
    line: { color: C.lightBlue, width: 0 },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.25, h: 0.9,
    fill: { color: C.azureBlue },
    line: { color: C.azureBlue, width: 0 },
  });
  slide.addText(text, {
    x: 0.45, y: 0, w: 9.3, h: 0.9,
    fontSize: fontSize || 27, fontFace: F.title, bold: true,
    color: C.darkBlue, align: "left", valign: "middle", margin: 0,
  });
}

// Helper: bottom note bar
function addBottomNote(slide, text, bg, border, textColor, y) {
  y = y || 4.2;
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y, w: 9.3, h: 0.72,
    fill: { color: bg || C.lightBlue },
    line: { color: border || "BDD7EE", width: 1 },
  });
  slide.addText(text, {
    x: 0.35, y, w: 9.3, h: 0.72,
    fontSize: 13, fontFace: F.body, bold: true,
    color: textColor || C.darkBlue,
    align: "center", valign: "middle", margin: 0,
  });
}

// ================================================================
// SLIDE 1 — Title
// ================================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.darkBlue };

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.4, h: 5.625,
    fill: { color: C.azureBlue },
    line: { color: C.azureBlue, width: 0 },
  });

  slide.addText("Azure AI Search 入門", {
    x: 0.75, y: 1.6, w: 8.8, h: 1.0,
    fontSize: 44, fontFace: F.title, bold: true,
    color: C.white, align: "left", margin: 0,
  });

  slide.addText("Week 1 — 製品の存在理由と設計思想", {
    x: 0.75, y: 2.75, w: 8.8, h: 0.6,
    fontSize: 22, fontFace: F.body,
    color: "A8D4F5", align: "left", margin: 0,
  });

  slide.addShape(pres.shapes.LINE, {
    x: 0.75, y: 3.5, w: 6.5, h: 0,
    line: { color: C.azureBlue, width: 1.5 },
  });

  slide.addText("Phase 1a  |  学習プラン Week 1 / 8", {
    x: 0.75, y: 3.75, w: 8.8, h: 0.4,
    fontSize: 12, fontFace: F.body,
    color: "7FBEE8", align: "left", margin: 0,
  });
}

// ================================================================
// SLIDE 2 — Section header
// ================================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.azureBlue };

  slide.addShape(pres.shapes.OVAL, {
    x: 7.5, y: -0.8, w: 3.5, h: 3.5,
    fill: { color: "0091FF", transparency: 70 },
    line: { color: "0091FF", width: 0 },
  });
  slide.addShape(pres.shapes.OVAL, {
    x: 8.2, y: 3.5, w: 2.5, h: 2.5,
    fill: { color: "005BA1", transparency: 60 },
    line: { color: "005BA1", width: 0 },
  });

  slide.addText("WHY?", {
    x: 0.75, y: 1.1, w: 2.5, h: 0.42,
    fontSize: 13, fontFace: F.body, bold: true,
    color: "A8D4F5", align: "left", charSpacing: 4, margin: 0,
  });

  slide.addText("なぜ Azure AI Search が\n必要なのか", {
    x: 0.75, y: 1.6, w: 7.8, h: 1.8,
    fontSize: 38, fontFace: F.title, bold: true,
    color: C.white, align: "left", margin: 0,
  });

  slide.addText("「データベースで検索する」ことの限界から考える", {
    x: 0.75, y: 3.5, w: 7.5, h: 0.55,
    fontSize: 18, fontFace: F.body, italic: true,
    color: "C9E4F8", align: "left", margin: 0,
  });
}

// ================================================================
// SLIDE 3 — Database weakness
// ================================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  addTitleBar(slide, "データベースは「検索」が苦手", 27);

  slide.addText("SQL の LIKE 句での試み：", {
    x: 0.5, y: 1.05, w: 9, h: 0.3,
    fontSize: 13, fontFace: F.body, color: C.grayText, align: "left", margin: 0,
  });

  // Code block
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.4, w: 9, h: 0.55,
    fill: { color: "1E1E1E" },
    line: { color: "1E1E1E", width: 0 },
  });
  slide.addText("SELECT * FROM documents WHERE content LIKE '%コスト削減%'", {
    x: 0.5, y: 1.4, w: 9, h: 0.55,
    fontSize: 13, fontFace: F.mono, color: "9CDCFE",
    align: "left", valign: "middle", margin: [0, 0, 0, 10],
  });

  // Table
  const rows = [
    [
      { text: "問題", options: { bold: true, color: C.white, fill: { color: C.azureBlue }, fontSize: 14, fontFace: F.body, align: "center", valign: "middle" } },
      { text: "説明", options: { bold: true, color: C.white, fill: { color: C.azureBlue }, fontSize: 14, fontFace: F.body, align: "left", valign: "middle" } },
    ],
    [
      { text: "語彙不一致", options: { bold: true, color: C.darkBlue, fill: { color: C.iceBlue }, fontSize: 14, fontFace: F.body, align: "center", valign: "middle" } },
      { text: "「費用低減」「コストカット」はヒットしない", options: { color: C.darkText, fill: { color: C.iceBlue }, fontSize: 13, fontFace: F.body, align: "left", valign: "middle" } },
    ],
    [
      { text: "全行スキャン", options: { bold: true, color: C.darkBlue, fill: { color: C.white }, fontSize: 14, fontFace: F.body, align: "center", valign: "middle" } },
      { text: "文書が増えるほど遅くなる", options: { color: C.darkText, fill: { color: C.white }, fontSize: 13, fontFace: F.body, align: "left", valign: "middle" } },
    ],
    [
      { text: "ランキング不可", options: { bold: true, color: C.darkBlue, fill: { color: C.iceBlue }, fontSize: 14, fontFace: F.body, align: "center", valign: "middle" } },
      { text: "「どれが一番関連性が高いか」を判断できない", options: { color: C.darkText, fill: { color: C.iceBlue }, fontSize: 13, fontFace: F.body, align: "left", valign: "middle" } },
    ],
  ];
  slide.addTable(rows, {
    x: 0.5, y: 2.1, w: 9, h: 2.9,
    colW: [2.3, 6.7],
    rowH: 0.7,
    border: { pt: 0.5, color: C.midGray },
  });
}

// ================================================================
// SLIDE 4 — Inverted Index
// ================================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  addTitleBar(slide, "転置インデックスとは", 27);

  // LEFT header
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 1.05, w: 4.15, h: 0.4,
    fill: { color: C.grayText },
    line: { color: C.grayText, width: 0 },
  });
  slide.addText("通常のインデックス", {
    x: 0.35, y: 1.05, w: 4.15, h: 0.4,
    fontSize: 13, fontFace: F.body, bold: true,
    color: C.white, align: "center", valign: "middle", margin: 0,
  });

  const leftRows = [
    [
      { text: "文書", options: { bold: true, color: C.white, fill: { color: "555555" }, fontSize: 13, fontFace: F.body, align: "center" } },
      { text: "含まれる単語", options: { bold: true, color: C.white, fill: { color: "555555" }, fontSize: 13, fontFace: F.body, align: "left" } },
    ],
    [
      { text: "文書1", options: { color: C.darkText, fill: { color: C.iceBlue }, fontSize: 13, fontFace: F.body, align: "center" } },
      { text: "コスト、削減、品質", options: { color: C.darkText, fill: { color: C.iceBlue }, fontSize: 13, fontFace: F.body, align: "left" } },
    ],
    [
      { text: "文書2", options: { color: C.darkText, fill: { color: C.white }, fontSize: 13, fontFace: F.body, align: "center" } },
      { text: "コスト、品質、改善", options: { color: C.darkText, fill: { color: C.white }, fontSize: 13, fontFace: F.body, align: "left" } },
    ],
  ];
  slide.addTable(leftRows, {
    x: 0.35, y: 1.45, w: 4.15, h: 1.55,
    colW: [1.4, 2.75],
    rowH: 0.52,
    border: { pt: 0.5, color: C.midGray },
  });

  // Arrow
  slide.addText("→", {
    x: 4.6, y: 2.05, w: 0.8, h: 0.45,
    fontSize: 26, fontFace: F.body, bold: true,
    color: C.azureBlue, align: "center", margin: 0,
  });
  slide.addText("逆引き", {
    x: 4.55, y: 2.5, w: 0.9, h: 0.28,
    fontSize: 10, fontFace: F.body,
    color: C.grayText, align: "center", margin: 0,
  });

  // RIGHT header
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.5, y: 1.05, w: 4.15, h: 0.4,
    fill: { color: C.azureBlue },
    line: { color: C.azureBlue, width: 0 },
  });
  slide.addText("転置インデックス（逆引き）", {
    x: 5.5, y: 1.05, w: 4.15, h: 0.4,
    fontSize: 13, fontFace: F.body, bold: true,
    color: C.white, align: "center", valign: "middle", margin: 0,
  });

  const rightRows = [
    [
      { text: "単語", options: { bold: true, color: C.white, fill: { color: C.accentBlue }, fontSize: 13, fontFace: F.body, align: "center" } },
      { text: "含まれる文書", options: { bold: true, color: C.white, fill: { color: C.accentBlue }, fontSize: 13, fontFace: F.body, align: "left" } },
    ],
    [
      { text: "コスト", options: { bold: true, color: C.darkBlue, fill: { color: C.iceBlue }, fontSize: 13, fontFace: F.body, align: "center" } },
      { text: "文書1, 文書2", options: { color: C.darkText, fill: { color: C.iceBlue }, fontSize: 13, fontFace: F.body, align: "left" } },
    ],
    [
      { text: "削減", options: { bold: true, color: C.darkBlue, fill: { color: C.white }, fontSize: 13, fontFace: F.body, align: "center" } },
      { text: "文書1", options: { color: C.darkText, fill: { color: C.white }, fontSize: 13, fontFace: F.body, align: "left" } },
    ],
    [
      { text: "品質", options: { bold: true, color: C.darkBlue, fill: { color: C.iceBlue }, fontSize: 13, fontFace: F.body, align: "center" } },
      { text: "文書1, 文書2", options: { color: C.darkText, fill: { color: C.iceBlue }, fontSize: 13, fontFace: F.body, align: "left" } },
    ],
  ];
  slide.addTable(rightRows, {
    x: 5.5, y: 1.45, w: 4.15, h: 2.07,
    colW: [1.4, 2.75],
    rowH: 0.52,
    border: { pt: 0.5, color: "BDD7EE" },
  });

  // Bottom note
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 3.8, w: 9.3, h: 0.75,
    fill: { color: "FFF4CE" },
    line: { color: "F0BC30", width: 1 },
  });
  slide.addText("「コスト削減」で検索　→　コストと削減の両方に含まれる 文書1 が上位にくる", {
    x: 0.35, y: 3.8, w: 9.3, h: 0.75,
    fontSize: 14, fontFace: F.body, bold: true,
    color: "7A5400", align: "center", valign: "middle", margin: 0,
  });
}

// ================================================================
// SLIDE 5 — BM25
// ================================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  addTitleBar(slide, "関連度ランキングの仕組み：BM25", 25);

  slide.addText("BM25（Best Match 25）— Azure AI Search が使うスコアリングアルゴリズム", {
    x: 0.45, y: 0.95, w: 9.1, h: 0.35,
    fontSize: 12, fontFace: F.body, italic: true,
    color: C.grayText, align: "left", margin: 0,
  });

  const cards = [
    {
      label: "TF（Term Frequency）",
      subLabel: "出現頻度",
      detail: "文書内の出現頻度が高いほど高スコア。ただし逓減する（10回は2回の5倍ではない）",
      x: 0.3,
    },
    {
      label: "IDF\n（Inverse Document Frequency）",
      subLabel: "希少度",
      detail: "「コスト」は多くの文書に出現 → 低スコア\n「HNSW」はほぼ出現しない → 高スコア",
      x: 3.55,
    },
    {
      label: "フィールド長\n正規化",
      subLabel: "位置の重み",
      detail: "短いタイトルでの出現は、長い本文での出現より重い",
      x: 6.8,
    },
  ];

  cards.forEach(({ label, subLabel, detail, x }) => {
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.42, w: 3.1, h: 2.65,
      fill: { color: C.iceBlue },
      line: { color: "BDD7EE", width: 1.5 },
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.42, w: 3.1, h: 0.08,
      fill: { color: C.azureBlue },
      line: { color: C.azureBlue, width: 0 },
    });
    slide.addText(label, {
      x: x + 0.12, y: 1.55, w: 2.86, h: 0.7,
      fontSize: 13, fontFace: F.body, bold: true,
      color: C.darkBlue, align: "center", valign: "middle", margin: 0,
    });
    slide.addShape(pres.shapes.LINE, {
      x: x + 0.12, y: 2.28, w: 2.86, h: 0,
      line: { color: "BDD7EE", width: 0.75 },
    });
    slide.addText(subLabel, {
      x: x + 0.12, y: 2.33, w: 2.86, h: 0.35,
      fontSize: 13, fontFace: F.body, bold: true,
      color: C.azureBlue, align: "center", margin: 0,
    });
    slide.addText(detail, {
      x: x + 0.12, y: 2.73, w: 2.86, h: 1.25,
      fontSize: 12, fontFace: F.body,
      color: C.darkText, align: "left", valign: "top", margin: 0,
    });
  });

  addBottomNote(slide, "この 3 つのバランスで「最も関連性の高い文書」を順位付けする", C.lightBlue, "BDD7EE", C.darkBlue, 4.22);
}

// ================================================================
// SLIDE 6 — Separation of Concerns
// ================================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  addTitleBar(slide, "Azure AI Search の設計思想：関心の分離", 23);

  slide.addText("データの「保管」と「検索」は、別のシステムが担当する", {
    x: 0.45, y: 0.95, w: 9.1, h: 0.35,
    fontSize: 12, fontFace: F.body, italic: true,
    color: C.grayText, align: "left", margin: 0,
  });

  const boxes = [
    {
      title: "元データ（正本）",
      lines: ["Blob Storage", "Azure SQL", "Cosmos DB"],
      x: 0.3, bg: C.lightGray, border: C.midGray, titleColor: C.darkText,
    },
    {
      title: "Azure AI Search",
      lines: ["検索インデックス", "（派生・最適化された表現）", "元データの正本ではない"],
      x: 3.5, bg: C.iceBlue, border: C.azureBlue, titleColor: C.darkBlue,
    },
    {
      title: "アプリケーション",
      lines: ["App Service", "Azure Functions", "API Management"],
      x: 6.7, bg: C.lightGray, border: C.midGray, titleColor: C.darkText,
    },
  ];

  boxes.forEach(({ title, lines, x, bg, border, titleColor }) => {
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.45, w: 3.0, h: 2.35,
      fill: { color: bg }, line: { color: border, width: 1.5 },
    });
    slide.addText(title, {
      x: x + 0.08, y: 1.55, w: 2.84, h: 0.52,
      fontSize: 15, fontFace: F.body, bold: true,
      color: titleColor, align: "center", valign: "middle", margin: 0,
    });
    slide.addShape(pres.shapes.LINE, {
      x: x + 0.08, y: 2.1, w: 2.84, h: 0,
      line: { color: border, width: 0.75 },
    });
    lines.forEach((line, i) => {
      slide.addText(line, {
        x: x + 0.08, y: 2.17 + i * 0.4, w: 2.84, h: 0.38,
        fontSize: 12, fontFace: F.body, color: C.grayText,
        align: "center", valign: "middle", margin: 0,
      });
    });
  });

  // Arrows
  [3.35, 6.55].forEach(ax => {
    slide.addText("→", {
      x: ax, y: 2.35, w: 0.2, h: 0.4,
      fontSize: 22, fontFace: F.body, bold: true,
      color: C.azureBlue, align: "center", margin: 0,
    });
  });

  // Bottom note (dark)
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 4.0, w: 9.3, h: 0.95,
    fill: { color: C.darkBlue },
    line: { color: C.darkBlue, width: 0 },
  });
  slide.addText("AI Search はシステムオブレコードではない  —  検索に特化したコピーを保持する", {
    x: 0.35, y: 4.0, w: 9.3, h: 0.95,
    fontSize: 14, fontFace: F.body, bold: true,
    color: C.white, align: "center", valign: "middle", margin: 0,
  });
}

// ================================================================
// SLIDE 7 — Azure Ecosystem
// ================================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  addTitleBar(slide, "Azure エコシステムの中での位置づけ", 25);

  const cols = [
    {
      header: "データ層（上流）",
      items: ["Azure Blob Storage", "Azure SQL Database", "Azure Cosmos DB"],
      x: 0.2, headerBg: "444444", bg: C.lightGray, border: C.midGray,
    },
    {
      header: "処理・検索層",
      items: ["Azure AI Search", "← データ取り込み / クエリ応答 →", "Azure AI Services\n（OCR・翻訳・NER）", "Azure OpenAI Service\n（Embedding 生成）"],
      x: 3.55, headerBg: C.azureBlue, bg: C.iceBlue, border: C.azureBlue,
    },
    {
      header: "アプリ層（下流）",
      items: ["App Service", "Azure Functions", "API Management"],
      x: 6.9, headerBg: "444444", bg: C.lightGray, border: C.midGray,
    },
  ];

  cols.forEach(({ header, items, x, headerBg, bg, border }) => {
    const w = 2.9;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.0, w, h: 4.35,
      fill: { color: bg }, line: { color: border, width: 1.5 },
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.0, w, h: 0.48,
      fill: { color: headerBg }, line: { color: headerBg, width: 0 },
    });
    slide.addText(header, {
      x, y: 1.0, w, h: 0.48,
      fontSize: 13, fontFace: F.body, bold: true,
      color: C.white, align: "center", valign: "middle", margin: 0,
    });
    items.forEach((item, i) => {
      const isBig = i === 0 && header.includes("処理");
      slide.addText(item, {
        x: x + 0.1, y: 1.58 + i * 0.7, w: w - 0.2, h: 0.65,
        fontSize: isBig ? 14 : 12, fontFace: F.body, bold: isBig,
        color: isBig ? C.darkBlue : C.grayText,
        align: "center", valign: "middle", margin: 0,
      });
    });
  });

  // Arrows
  [3.3, 6.65].forEach(ax => {
    slide.addText("→", {
      x: ax, y: 2.8, w: 0.3, h: 0.4,
      fontSize: 22, fontFace: F.body, bold: true,
      color: C.azureBlue, align: "center", margin: 0,
    });
  });
}

// ================================================================
// SLIDE 8 — RAG
// ================================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  addTitleBar(slide, "Azure OpenAI との組み合わせ：RAG とは", 24);

  slide.addText("Retrieval-Augmented Generation — 検索と生成の組み合わせ", {
    x: 0.45, y: 0.95, w: 9.1, h: 0.35,
    fontSize: 12, fontFace: F.body, italic: true,
    color: C.grayText, align: "left", margin: 0,
  });

  const steps = [
    { n: "1", text: "ユーザーの質問", tag: null, bg: C.lightGray, border: C.midGray, textColor: C.darkText },
    { n: "2", text: "Azure AI Search で関連情報を「検索」する", tag: "Retrieval", bg: C.iceBlue, border: C.azureBlue, textColor: C.darkBlue },
    { n: "3", text: "Azure OpenAI GPT-4 で検索結果をもとに「回答を生成」する", tag: "Generation", bg: "E8F5E9", border: "2E7D32", textColor: "1B5E20" },
    { n: "4", text: "根拠付きの回答", tag: null, bg: C.lightGray, border: C.midGray, textColor: C.darkText },
  ];

  steps.forEach(({ n, text, tag, bg, border, textColor }, i) => {
    const y = 1.42 + i * 0.84;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 1.0, y, w: 6.5, h: 0.65,
      fill: { color: bg }, line: { color: border, width: 1.5 },
    });
    slide.addShape(pres.shapes.OVAL, {
      x: 1.05, y: y + 0.07, w: 0.52, h: 0.52,
      fill: { color: border }, line: { color: border, width: 0 },
    });
    slide.addText(n, {
      x: 1.05, y: y + 0.07, w: 0.52, h: 0.52,
      fontSize: 14, fontFace: F.body, bold: true,
      color: C.white, align: "center", valign: "middle", margin: 0,
    });
    slide.addText(text, {
      x: 1.68, y, w: 5.1, h: 0.65,
      fontSize: 13, fontFace: F.body,
      color: textColor, align: "left", valign: "middle", margin: 0,
    });
    if (tag) {
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 6.85, y: y + 0.1, w: 0.9, h: 0.42,
        fill: { color: border }, line: { color: border, width: 0 },
      });
      slide.addText(tag, {
        x: 6.85, y: y + 0.1, w: 0.9, h: 0.42,
        fontSize: 11, fontFace: F.body, bold: true,
        color: C.white, align: "center", valign: "middle", margin: 0,
      });
    }
    if (i < steps.length - 1) {
      slide.addText("↓", {
        x: 4.1, y: y + 0.63, w: 0.4, h: 0.22,
        fontSize: 14, fontFace: F.body, color: C.azureBlue,
        align: "center", margin: 0,
      });
    }
  });

  // Week 6 note
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 7.95, y: 2.25, w: 1.75, h: 0.72,
    fill: { color: "FFF4CE" }, line: { color: "F0BC30", width: 1 },
  });
  slide.addText("Week 6 で\n詳しく学習", {
    x: 7.95, y: 2.25, w: 1.75, h: 0.72,
    fontSize: 11, fontFace: F.body, color: "7A5400",
    align: "center", valign: "middle", margin: 0,
  });
}

// ================================================================
// SLIDE 9 — Three eras
// ================================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  addTitleBar(slide, "製品の3つの時代", 30);

  slide.addText("機能が「重層的」に見える理由", {
    x: 0.45, y: 0.95, w: 9.1, h: 0.35,
    fontSize: 12, fontFace: F.body, italic: true,
    color: C.grayText, align: "left", margin: 0,
  });

  // Timeline line
  slide.addShape(pres.shapes.LINE, {
    x: 0.5, y: 1.65, w: 9.0, h: 0,
    line: { color: C.midGray, width: 1.5 },
  });

  const eras = [
    {
      year: "2015年〜",
      label: "クラシック全文検索",
      items: ["BM25スコアリング", "クエリ構文（simple / full）", "フィルター・ファセット", "スコアリングプロファイル"],
      x: 0.3, color: "64748B",
    },
    {
      year: "2019年〜",
      label: "AI Enrichment",
      items: ["認知スキルパイプライン", "OCR・翻訳・エンティティ認識", "ナレッジストア"],
      x: 3.55, color: C.accentBlue,
    },
    {
      year: "2023年〜",
      label: "ベクター・セマンティック",
      items: ["ベクター検索（HNSW）", "ハイブリッド検索（RRF）", "セマンティックランキング", "RAGパターン"],
      x: 6.8, color: C.azureBlue,
    },
  ];

  eras.forEach(({ year, label, items, x, color }) => {
    // Dot
    slide.addShape(pres.shapes.OVAL, {
      x: x + 1.2, y: 1.47, w: 0.36, h: 0.36,
      fill: { color }, line: { color, width: 0 },
    });
    // Year label
    slide.addText(year, {
      x, y: 1.87, w: 2.9, h: 0.36,
      fontSize: 13, fontFace: F.body, bold: true,
      color, align: "center", margin: 0,
    });
    // Card
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 2.27, w: 2.9, h: 2.3,
      fill: { color: C.iceBlue }, line: { color, width: 1.5 },
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 2.27, w: 2.9, h: 0.08,
      fill: { color }, line: { color, width: 0 },
    });
    slide.addText(label, {
      x: x + 0.08, y: 2.35, w: 2.74, h: 0.48,
      fontSize: 13, fontFace: F.body, bold: true,
      color, align: "center", valign: "middle", margin: 0,
    });
    // Items as bullets
    const bulletItems = items.map((item, idx) => ({
      text: item,
      options: { bullet: true, breakLine: idx < items.length - 1 },
    }));
    slide.addText(bulletItems, {
      x: x + 0.1, y: 2.87, w: 2.7, h: 1.6,
      fontSize: 11, fontFace: F.body,
      color: C.darkText, align: "left", margin: 0,
    });
  });

  addBottomNote(slide, "「これは古いやり方か、新しいやり方か？」と意識しながら学ぶと整理しやすい",
    C.lightBlue, "BDD7EE", C.darkBlue, 4.72);
}

// ================================================================
// SLIDE 10 — Action Plan
// ================================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.white };

  // Dark title bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: C.darkBlue }, line: { color: C.darkBlue, width: 0 },
  });
  slide.addText("Week 1 アクションプラン", {
    x: 0.45, y: 0, w: 9.3, h: 0.9,
    fontSize: 28, fontFace: F.title, bold: true,
    color: C.white, align: "left", valign: "middle", margin: 0,
  });

  slide.addText("今週やること・確認すること", {
    x: 0.45, y: 0.95, w: 9.1, h: 0.35,
    fontSize: 12, fontFace: F.body, italic: true,
    color: C.grayText, align: "left", margin: 0,
  });

  // LEFT: Hands-on
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 1.4, w: 4.55, h: 0.42,
    fill: { color: C.azureBlue }, line: { color: C.azureBlue, width: 0 },
  });
  slide.addText("ハンズオン（1.5時間）", {
    x: 0.3, y: 1.4, w: 4.55, h: 0.42,
    fontSize: 13, fontFace: F.body, bold: true,
    color: C.white, align: "center", valign: "middle", margin: 0,
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 1.82, w: 4.55, h: 2.6,
    fill: { color: C.iceBlue }, line: { color: "BDD7EE", width: 1 },
  });

  const handsonItems = [
    "Azure Portal で AI Search サービスを作成\n（Free または Basic ティア）",
    "各ブレードを開き 1 文でメモする\n（Indexes / Indexers / Data Sources /\nSkillsets / Scale / Keys / Networking）",
    "データフロー図を手描きする\n（正確でなくてOK）",
  ];
  handsonItems.forEach((text, i) => {
    slide.addShape(pres.shapes.OVAL, {
      x: 0.44, y: 1.97 + i * 0.83, w: 0.3, h: 0.3,
      fill: { color: C.azureBlue }, line: { color: C.azureBlue, width: 0 },
    });
    slide.addText(String(i + 1), {
      x: 0.44, y: 1.97 + i * 0.83, w: 0.3, h: 0.3,
      fontSize: 11, fontFace: F.body, bold: true,
      color: C.white, align: "center", valign: "middle", margin: 0,
    });
    slide.addText(text, {
      x: 0.84, y: 1.94 + i * 0.83, w: 3.9, h: 0.78,
      fontSize: 11, fontFace: F.body, color: C.darkText,
      align: "left", valign: "top", margin: 0,
    });
  });

  // RIGHT: Self check
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.15, y: 1.4, w: 4.55, h: 0.42,
    fill: { color: C.accentBlue }, line: { color: C.accentBlue, width: 0 },
  });
  slide.addText("自己チェック（週末に試す）", {
    x: 5.15, y: 1.4, w: 4.55, h: 0.42,
    fontSize: 13, fontFace: F.body, bold: true,
    color: C.white, align: "center", valign: "middle", margin: 0,
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.15, y: 1.82, w: 4.55, h: 2.6,
    fill: { color: C.iceBlue }, line: { color: "BDD7EE", width: 1 },
  });

  const checkItems = [
    "転置インデックスを図なしで\n口頭説明できるか？",
    "AI Search が元データを保存しない\n理由を言えるか？",
    "フィルター（完全一致）と検索\n（関連度ランキング）の違いを例で説明できるか？",
    "Azure エコシステムの中で\nAI Search はどの層に位置するか？",
  ];
  checkItems.forEach((text, i) => {
    slide.addText("✓", {
      x: 5.25, y: 1.97 + i * 0.6, w: 0.3, h: 0.5,
      fontSize: 14, fontFace: F.body, bold: true,
      color: C.azureBlue, align: "center", valign: "middle", margin: 0,
    });
    slide.addText(text, {
      x: 5.6, y: 1.97 + i * 0.6, w: 4.0, h: 0.55,
      fontSize: 11, fontFace: F.body, color: C.darkText,
      align: "left", valign: "top", margin: 0,
    });
  });

  // Bottom note
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 4.58, w: 9.4, h: 0.72,
    fill: { color: "FFF4CE" }, line: { color: "F0BC30", width: 1 },
  });
  slide.addText("詰まる場所がまだ理解できていない場所  —  遠慮なく質問してください", {
    x: 0.3, y: 4.58, w: 9.4, h: 0.72,
    fontSize: 13, fontFace: F.body, bold: true,
    color: "7A5400", align: "center", valign: "middle", margin: 0,
  });
}

pres.writeFile({ fileName: "/Users/yoyo/Desktop/azure/ai-search/slides/week1_design_philosophy.pptx" })
  .then(() => console.log("Done!"))
  .catch(err => console.error(err));
