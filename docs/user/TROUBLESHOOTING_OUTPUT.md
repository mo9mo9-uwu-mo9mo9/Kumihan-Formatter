# 🖥️ 出力・表示のトラブルシューティング

> **ブラウザ・画像・レイアウト関連の問題を解決**

[← トラブルシューティング目次に戻る](TROUBLESHOOTING.md)

---

## 📋 出力・表示問題一覧

- [ブラウザが開かない / プレビューが表示されない](#-症状-ブラウザが開かない--プレビューが表示されない)
- [画像が表示されない / 画像リンクエラー](#-症状-画像が表示されない--画像リンクエラー)
- [出力HTMLが崩れている / レイアウト問題](#-症状-出力htmlが崩れている--レイアウト問題)

---

## ❌ **症状**: ブラウザが開かない / プレビューが表示されない

### 🔍 **原因**
- 既定ブラウザが設定されていない
- ブラウザのセキュリティ設定
- ファイルパスにスペースや特殊文字
- ファイアウォールによるブロック

### ✅ **解決方法**

#### **Step 1: 手動でHTMLファイルを開く**
```bash
# 変換をプレビューなしで実行
python -m kumihan_formatter sample.txt --no-preview

# 生成されたHTMLファイルの場所確認
ls dist/                    # macOS/Linux  
dir dist\                   # Windows

# 手動でブラウザで開く
# ファイルをダブルクリック、またはブラウザにドラッグ&ドロップ
```

#### **Step 2: ブラウザ設定の確認**

**Windows:**
1. **設定** → **アプリ** → **既定のアプリ**
2. **Webブラウザー** を確認・設定
3. Chrome、Firefox、Edge等の主要ブラウザを推奨

**macOS:**
1. **システム環境設定** → **一般**
2. **デフォルトWebブラウザ** を確認・設定

#### **Step 3: プレビュー無効化での実行**
```bash
# 常にプレビューを無効にする場合
alias kumi="python -m kumihan_formatter --no-preview"

# 設定ファイルでプレビュー無効化
# config.yaml
output:
  auto_preview: false
```

---

## ❌ **症状**: 画像が表示されない / 画像リンクエラー

### 🔍 **原因**
- 画像ファイルのパス間違い
- 画像ファイル形式が非対応
- ファイル名に使用できない文字
- 画像ファイルの破損

### ✅ **解決方法**

#### **Step 1: 推奨フォルダ構成の確認**

**正しいフォルダ構成:**
```
project/
├── document.txt           ← テキストファイル
├── images/                ← 画像専用フォルダ
│   ├── image01.jpg        ← 画像ファイル
│   ├── screenshot.png
│   └── diagram.gif
└── dist/                  ← 出力先
    ├── document.html      ← HTMLファイル
    └── images/            ← 画像が自動コピーされる
        ├── image01.jpg
        ├── screenshot.png
        └── diagram.gif
```

#### **Step 2: 画像記法の確認**

**✅ 正しい記法:**
```text
;;;画像 alt=サンプル画像
image01.jpg
;;;

;;;画像 alt=スクリーンショット
screenshot.png
;;;
```

**❌ よくある間違い:**
```text
# パス指定は不要（images/フォルダ内のファイル名のみ）
;;;画像 alt=画像
images/image01.jpg  ← 間違い
;;;

# ファイル拡張子忘れ
;;;画像 alt=画像  
image01             ← 間違い（.jpg がない）
;;;

# スペースを含むファイル名
;;;画像 alt=画像
my image.jpg        ← 避けるべき
;;;
```

#### **Step 3: 対応画像形式の確認**
- **JPEG** (`.jpg`, `.jpeg`) ✅
- **PNG** (`.png`) ✅  
- **GIF** (`.gif`) ✅
- **WebP** (`.webp`) ✅

**非対応形式:**
- **BMP** (`.bmp`) ❌
- **TIFF** (`.tiff`, `.tif`) ❌
- **SVG** (`.svg`) ❌（将来対応予定）

#### **Step 4: 画像ファイルの確認**
```bash
# 画像ファイル存在確認
ls -la images/              # macOS/Linux
dir images\                 # Windows

# ファイルサイズ確認（大きすぎないか）
du -h images/*              # macOS/Linux
dir images\ /s              # Windows

# 画像ファイルの詳細情報
file images/*.jpg           # macOS/Linux
```

**推奨画像仕様:**
- **サイズ**: 1920×1080px以下
- **ファイルサイズ**: 1MB以下
- **ファイル名**: 英数字・ハイフン・アンダースコアのみ

---

## ❌ **症状**: 出力HTMLが崩れている / レイアウト問題

### 🔍 **原因**
- ブラウザの互換性問題
- CSSの読み込みエラー
- 記法の間違いによるHTML構造の破綻
- カスタムCSS設定の問題

### ✅ **解決方法**

#### **Step 1: 生成HTMLの確認**
```bash
# HTMLファイルを直接確認
cat dist/document.html      # macOS/Linux
type dist\document.html     # Windows

# HTMLの妥当性確認（オンラインツール）
# https://validator.w3.org/nu/ にHTMLをアップロード
```

#### **Step 2: ブラウザ開発者ツールでの確認**
1. **F12** キーで開発者ツールを開く
2. **Console** タブでエラーメッセージ確認
3. **Elements** タブでHTML構造確認
4. **Network** タブでリソース読み込み確認

**よくあるエラー:**
- `404 Not Found` → CSSファイルが見つからない
- `CORS error` → ローカルファイルのセキュリティ制限
- `Syntax Error` → 無効なCSS

#### **Step 3: 最小再現コードでのテスト**

**test_simple.txt:**
```text
;;;見出し1
テストページ
;;;

これは普通のテキストです。

;;;太字
重要な情報
;;;

;;;枠線
- 項目1
- 項目2  
- 項目3
;;;
```

```bash
# 最小コードで変換テスト
python -m kumihan_formatter test_simple.txt

# 問題が再現するか確認
```

#### **Step 4: 記法の段階的追加テスト**

記法を段階的に追加して問題箇所を特定：

**段階1（基本）:**
```text
;;;見出し1
タイトル
;;;

普通のテキスト
```

**段階2（装飾追加）:**
```text
;;;見出し1  
タイトル
;;;

;;;太字
重要情報
;;;
```

**段階3（複合記法）:**
```text
;;;太字+ハイライト color=#ffe6e6
複合スタイル
;;;
```

各段階でHTMLが正常に生成されるか確認し、問題のある記法を特定。

---

## 🔧 **高度なトラブルシューティング**

### **HTMLデバッグ手法**

#### **1. 構造検証**
```bash
# HTML構造の確認
grep -n "<.*>" dist/document.html | head -20

# 閉じタグの確認
python3 -c "
import re
html = open('dist/document.html').read()
tags = re.findall(r'</?(\w+)', html)
print('開始タグ:', len([t for t in tags if not t.startswith('/')]))
print('終了タグ:', len([t for t in tags if t.startswith('/')]))
"
```

#### **2. CSSの確認**
```bash
# 埋め込みCSSの抽出
grep -A 50 "<style>" dist/document.html

# カスタムCSS設定の確認
cat config.yaml | grep -A 10 "custom_css"
```

#### **3. パフォーマンス確認**
```bash
# ファイルサイズ確認
ls -lh dist/document.html

# 画像サイズ合計確認
du -sh dist/images/

# 推奨サイズ（合計5MB以下）
```

### **互換性テスト**

**テスト推奨ブラウザ:**
- **Chrome** (最新版)
- **Firefox** (最新版)
- **Safari** (macOS)
- **Edge** (Windows)

**モバイルテスト:**
- Chrome DevTools のモバイル表示
- 実機での確認（iPhone/Android）

---

## 📱 **レスポンシブ対応の確認**

### **設定例（config.yaml）**
```yaml
responsive_design:
  mobile_breakpoint: "768px"
  tablet_breakpoint: "1024px"

mobile_optimization:
  font_size_scale: 1.1
  line_height_scale: 1.2
  padding_scale: 1.5

styles:
  max_width: "800px"
  margin: "0 auto"
```

### **確認方法**
1. ブラウザ幅を狭める（768px以下）
2. 文字サイズが適切か確認
3. 横スクロールが発生しないか確認
4. ボタン・リンクが押しやすいサイズか確認

---

## 📞 **サポートが必要な場合**

出力・表示問題の報告テンプレート：

```
## 出力・表示問題報告

### 環境情報
- OS: [Windows 10 / macOS Big Sur など]
- ブラウザ: [Chrome 98 / Firefox 97 など]
- 画面解像度: [1920x1080 など]

### 問題の詳細
- 期待される表示: [どう表示されるべきか]
- 実際の表示: [実際にどう表示されているか]
- 問題のスクリーンショット: [可能であれば添付]

### ファイル情報
- HTMLファイルサイズ: [サイズ]
- 画像ファイル数: [数]
- 使用している記法: [複合記法、カスタムCSS等]

### ブラウザコンソールエラー
[F12開発者ツールのConsoleタブに表示されるエラー]

### 試した解決方法
- [ ] 他のブラウザでテスト
- [ ] 最小ファイルでテスト
- [ ] キャッシュクリア
- [ ] 開発者ツールで確認
```

---

## 📚 関連リソース

- **[トラブルシューティング目次](TROUBLESHOOTING.md)** - 他の問題も確認
- **[記法リファレンス](SYNTAX_REFERENCE.md)** - 正しい記法を確認
- **[実践ガイド](PRACTICAL_GUIDE.md)** - 配布用HTML最適化のコツ

---

**表示問題が解決することを願っています！ 🖥️✨**