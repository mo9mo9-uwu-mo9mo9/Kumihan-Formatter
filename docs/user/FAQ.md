# ❓ よくある質問（FAQ）

> **一般的な疑問をサクッと解決！** 使い方・機能・設定に関する質問集

## 🔍 カテゴリ別索引

1. [基本的な使い方](#-基本的な使い方)
2. [機能・記法について](#-機能記法について) 
3. [カスタマイズ・設定](#-カスタマイズ設定)
4. [配布・共有](#-配布共有)
5. [上級者向け](#-上級者向け)

---

## 💻 基本的な使い方

### Q1: Pythonって何ですか？インストールしても大丈夫？

**A:** Pythonは世界中で使われている安全なプログラミング言語です。

- **安全性**: Google、Netflix、Instagram等の大企業も使用
- **影響範囲**: 他のソフトウェアには一切影響しません
- **必要性**: Kumihan-Formatterの動作に必要

**インストール方法**:
1. [Python公式サイト](https://www.python.org/downloads/)にアクセス
2. 「Download Python 3.x.x」をクリック
3. インストール時に **「Add Python to PATH」にチェック**

---

### Q2: どんなテキストエディタを使えばいいですか？

**A:** 以下のエディタが推奨です：

**Windows**:
- メモ帳（標準）
- Notepad++（無料・高機能）
- Visual Studio Code（無料・多機能）

**macOS**:
- テキストエディット（標準）
- CotEditor（無料・日本語対応）
- Visual Studio Code（無料・多機能）

**保存時の注意**:
- 文字コード: **UTF-8** を選択
- ファイル拡張子: **.txt**

---

### Q3: 変換したファイルはどこに保存されますか？

**A:** デフォルトでは **`dist/`** フォルダに保存されます。

```
あなたのプロジェクト/
├── input.txt        ← 元ファイル
└── dist/           ← 出力先
    └── input.html  ← 変換結果
```

**出力先を変更したい場合**:
```bash
kumihan input.txt -o my_output/
```

---

### Q4: 複数のファイルを一度に変換できますか？

**A:** はい、複数の方法があります：

**方法1: ワイルドカード使用**
```bash
kumihan *.txt  # すべての.txtファイル
```

**方法2: ファイルを個別指定**
```bash
kumihan file1.txt file2.txt file3.txt
```

**方法3: フォルダ全体**
```bash
kumihan examples/  # フォルダ内のすべて
```

---

## 📝 機能・記法について

### Q5: Markdownとの違いは何ですか？

**A:** Kumihan記法はCoC6th TRPGシナリオに特化した記法です：

| 項目 | Markdown | Kumihan記法 |
|------|----------|-------------|
| **見出し** | `# 見出し` | `;;;見出し1\n見出し\n;;;` |
| **太字** | `**太字**` | `;;;太字\n太字\n;;;` |
| **特徴** | 汎用的 | TRPG特化（枠線、ネタバレ等） |

---

### Q6: よく使う記法のチートシートはありますか？

**A:** 基本記法TOP5：

```
;;;見出し1
章タイトル
;;;

;;;太字
重要な情報
;;;

;;;枠線
- リスト項目1
- リスト項目2
;;;

;;;ハイライト color=#ffe6e6
注意事項
;;;

;;;ネタバレ
重要なネタバレ情報
;;;
```

詳細は [記法リファレンス](SYNTAX_REFERENCE.md) をご覧ください。

---

### Q7: 画像を埋め込むことはできますか？

**A:** はい、可能です：

**フォルダ構成**:
```
プロジェクト/
├── シナリオ.txt
├── images/          ← 画像専用フォルダ
│   └── map.jpg
└── dist/           ← 出力先
```

**記法例**:
```
;;;画像 alt=ダンジョンマップ
map.jpg
;;;
```

**対応形式**: JPG、PNG、GIF、WebP

---

### Q8: 目次は自動生成されますか？

**A:** はい、見出しがある場合は自動生成されます。

- **自動検出**: `;;;見出し1;;;` ~ `;;;見出し5;;;` を検出
- **リンク付き**: クリックでその場所にジャンプ
- **手動挿入**: `;;;目次;;;` は使用禁止（自動のみ）

---

## 🎨 カスタマイズ・設定

### Q9: HTMLのデザインを変更したいです

**A:** `config.yaml` ファイルで設定可能です：

```yaml
# config.yaml
styles:
  body_font: "游ゴシック, YuGothic, sans-serif"
  heading_color: "#2c3e50"
  background_color: "#ffffff"
  
custom_css: |
  .box {
    border: 2px solid #3498db;
    border-radius: 8px;
  }
  
  .highlight {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
```

**適用方法**:
```bash
kumihan input.txt --config config.yaml
```

---

### Q10: フォントを変更したいです

**A:** config.yamlで日本語フォントを指定できます：

```yaml
styles:
  body_font: "ヒラギノ角ゴ Pro W3, Hiragino Kaku Gothic Pro, sans-serif"
  heading_font: "游明朝, YuMincho, serif"
```

**おすすめフォント**:
- **ゴシック**: 游ゴシック、ヒラギノ角ゴ、Noto Sans JP
- **明朝**: 游明朝、ヒラギノ明朝、Noto Serif JP

---

### Q11: 印刷用の設定はありますか？

**A:** 印刷用最適化の設定が可能です：

```yaml
print_optimization:
  page_size: "A4"
  margin: "20mm"
  font_size: "12pt"
  background_colors: false  # 印刷時は背景色を無効
```

**推奨印刷設定**:
- 用紙: A4縦
- マージン: 標準（20mm）
- 背景色: 印刷しない

---

## 📦 配布・共有

### Q12: 作成したHTMLファイルを配布したいです

**A:** 複数の配布方法があります：

**方法1: HTML単体配布**
- そのまま共有可能
- メール添付、クラウドストレージ

**方法2: PDF変換後配布**
```bash
# 1. HTMLを生成
kumihan シナリオ.txt

# 2. PDFに変換（要wkhtmltopdf）
wkhtmltopdf dist/シナリオ.html シナリオ.pdf
```

---

### Q13: Boothで販売する際の注意点は？

**A:** 以下の点にご注意ください：

**ライセンス関係**:
- **Kumihan-Formatter**: 改変自由、再配布禁止
- **あなたの作品**: 自由に販売・配布可能
- **使用素材**: 画像等のライセンス確認必須

**販売時の推奨事項**:
- サンプル版（無料）の提供
- 動作環境の明記（「HTMLファイル、モダンブラウザ対応」）
- 問い合わせ先の記載

**ファイル形式**:
- HTML: そのまま販売OK
- PDF: 印刷用途におすすめ

---

### Q14: 商用利用は可能ですか？

**A:** はい、可能です：

**利用可能な用途**:
- 同人誌即売会での販売
- Boothでの商品販売
- 有料セッション資料
- 商業出版（出版社要相談）

**禁止事項**:
- Kumihan-Formatter自体の再配布・販売
- 「Kumihan-Formatter製」の表記削除

---

## 🎓 上級者向け

### Q15: APIとして利用できますか？

**A:** Pythonモジュールとして利用可能です：

```python
from kumihan_formatter import parse, render

# テキストを読み込み
with open('input.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# パース
ast = parse(text)

# HTML生成
html = render(ast, config={
    'styles': {'body_font': 'Arial'}
})

print(html)
```

**応用例**:
- Webアプリケーションへの組み込み
- バッチ処理スクリプト
- 他ツールとの連携

---

### Q16: 独自のブロック記法を追加できますか？

**A:** 現在は基本記法のみですが、将来対応予定です：

**v1.0で実装予定**:
- カスタムCSS設定
- テーマシステム

**v2.0で実装予定**:
- プラグインシステム
- カスタムブロック定義
- 記法拡張API

**現在の回避策**:
```yaml
custom_css: |
  .my-custom-block {
    border: 3px solid #ff6b6b;
    background: #ffe0e0;
  }
```

---

### Q17: 他の形式（PDF、EPUB）に変換したいです

**A:** 外部ツールとの連携で可能です：

**PDF変換**:
```bash
# HTMLを生成
kumihan input.txt

# PDFに変換
wkhtmltopdf dist/input.html output.pdf
```

**EPUB変換**:
```bash
# Pandocを使用
pandoc dist/input.html -o output.epub
```

**推奨ツール**:
- **PDF**: wkhtmltopdf, Chrome headless
- **EPUB**: Pandoc, Calibre
- **Word**: Pandoc

---

### Q18: 大容量ファイルの変換は可能ですか？

**A:** 現在は小〜中規模ファイル向けですが、対応予定です：

**現在の推奨**:
- 1ファイル: 10,000行以下
- 画像: 合計50MB以下
- メモリ: 1GB以下

**大容量対応策**:
```bash
# ファイル分割
kumihan chapter1.txt chapter2.txt chapter3.txt

# 軽量オプション（実装予定）
kumihan large_file.txt --streaming
```

**v1.1で実装予定**:
- ストリーミング処理
- プログレスバー
- メモリ最適化

---

## 🤝 サポート・コミュニティ

### Q19: バグを見つけた場合はどうすればよいですか？

**A:** GitHubのIssueで報告をお願いします：

**報告先**: [GitHub Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)

**報告時に含める情報**:
- OS（Windows 10、macOS Big Sur等）
- Pythonバージョン（`python --version`）
- エラーメッセージの全文
- 問題のあるファイル（可能な範囲で）
- 期待していた動作

---

### Q20: 機能要望はどこで出せますか？

**A:** 以下の方法で要望をお寄せください：

**GitHubIssues**: 詳細な要望
**Twitter**: @username（カジュアルな提案）
**Discord**: Kumihan-Formatterコミュニティ（検討中）

**要望例**:
- 新しい記法の追加
- 出力形式の拡張
- UI/UXの改善
- ドキュメントの改善

---

**解決できましたか？他にご質問があれば、お気軽にお聞かせください！ 🤝**