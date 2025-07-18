# Kumihan記法 コア仕様

> **Kumihan-Formatter のKumihan記法テキスト変換仕様（コア部分）**
> 
> **簡素化**: 初心者向けに固定マーカーセットのみサポート
> 
> **寛容な記法**: 全角スペース・スペースなし・複数スペースに対応

---

## 📋 Kumihan記法 基本構文

| 入力構文 | 出力 HTML |
|--------------|---------------|
| 空行区切り | `<p>` 段落 |
| 改行のみ | `<br>` 改行 |
| `- ` リスト | `<ul><li>` |
| `・` 中黒リスト | `<ul><li>` |
| `1. ` 番号リスト | `<ol><li>` |
| `- ;;;キーワード;;; テキスト` | **キーワード付きリスト項目** |
| `・;;;キーワード;;; テキスト` | **キーワード付き中黒リスト項目** |
| `- ;;;キー1＋キー2;;; テキスト` | **複合キーワード付きリスト項目** |
| `;;;キーワード\n内容\n;;;` | 単一ブロックタグ |
| `;;;キー1＋キー2\n内容\n;;;` | **複合ブロックタグ**（順不同・全適用） |
| `;;;目次;;;` | 目次マーカー（見出しから自動生成） |
| `;;;filename.jpg;;;` | `<img src="images/filename.jpg" alt="filename.jpg">` |

---

## 🏷️ ブロックキーワード → タグ対照表

| キーワード | HTML | 備考 |
|---------|------|-------|
| 太字 | `<strong>` | ブロック全体 |
| イタリック | `<em>` | |
| 枠線 | `<div class="box">` | 標準枠線 + padding |
| ハイライト | `<div class="highlight">` | デフォルト色 |
| ハイライトcolor=#hex | `<div class="highlight" style="background-color:#hex">` | 色指定可 |
| 見出しN | `<hN>` | N = 1–5 |
| 折りたたみ | `<details><summary>詳細を表示</summary>` | HTML5折りたたみブロック |
| ネタバレ | `<details><summary>ネタバレを表示</summary>` | ネタバレ隠し専用 |
| 目次 | `<div class="toc">` | 見出しから自動生成される目次 |
| 画像（簡易） | `<img src="images/filename" alt="filename">` | ファイル名のみ指定 |
| 画像（詳細） | `<img src="images/filename" alt="説明">` | 複数行でalt明示 |

---

## 🔗 複合キーワードのルール

* **連結記号**: 半角 `+` **または** 全角 `＋` のいずれでも認識
* **順序**: キーワードの指定順序は関係なし（`太字+枠線` = `枠線+太字`）
* **全適用**: 複数のキーワードがすべて有効になる
* **制限**: 最大3つまでの組み合わせを推奨

### 複合例
```
;;;太字+枠線
重要なお知らせ
;;;
```
→ `<div class="box"><strong>重要なお知らせ</strong></div>`

---

## 🔄 基本動作フロー

1. **入力受付**: テキストファイルまたは文字列
2. **行分割**: 改行で各行に分解
3. **パターンマッチング**: Kumihan記法の識別
4. **HTML変換**: 対応するHTMLタグに変換
5. **出力**: HTMLファイルまたは文字列

---

**関連ドキュメント:**
- 詳細な構文例: [SPEC_SYNTAX.md](SPEC_SYNTAX.md)
- リファレンス: [SPEC_REFERENCE.md](SPEC_REFERENCE.md)
- 実装指針: [SPEC_IMPLEMENTATION.md](SPEC_IMPLEMENTATION.md)