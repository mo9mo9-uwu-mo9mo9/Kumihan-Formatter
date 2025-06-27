# 🎮 実践ガイド - Kumihan-Formatterの効果的な使い方

> **プロの技を伝授！** 効率的なワークフローと実践的なテクニック

## 🎯 このガイドの対象

- **Kumihan-Formatter**を使って文書を作成する方
- **効率的な作業フロー**を身につけたい方
- **配布用HTML**を美しく仕上げたい方
- **大規模文書**を管理したい方

---

## 📝 効率的な制作ワークフロー

### 📋 推奨制作スケジュール

#### **フェーズ1: 計画・準備**
```
;;;枠線
作業内容：
- 文書の構成・章立てを決定
- 必要な画像・資料を整理
- ディレクトリ構造を作成

所要時間：全体の20%
成果物：
- 目次案
- ディレクトリ構成
- 素材ファイル
;;;
```

#### **フェーズ2: 執筆・記法適用**
```
;;;枠線
作業内容：
- Kumihan記法での本文執筆
- 画像の配置・最適化
- 段階的なHTML変換・確認

所要時間：全体の60%
成果物：
- 本文テキストファイル
- 最適化済み画像
- プレビューHTML
;;;
```

#### **フェーズ3: 調整・配布準備**
```
;;;枠線
作業内容：
- レイアウト調整・スタイル適用
- 動作確認・互換性テスト
- 配布パッケージ作成

所要時間：全体の20%
成果物：
- 最終版HTML
- 配布用ZIPファイル
;;;
```

### 🛠️ 推奨ディレクトリ構造

```
プロジェクト/
├── document.txt           ← メイン文書
├── images/                ← 画像ファイル
│   ├── thumbnail.jpg      ← サムネイル
│   └── content_*.jpg      ← コンテンツ画像
├── config.yaml            ← 設定ファイル
├── backup/                ← バックアップ
│   └── document_v*.txt    ← 過去バージョン
└── dist/                  ← 出力先
    └── document.html      ← 最終HTML
```

### 📁 ファイル命名規則

**推奨命名パターン**:
- **メイン文書**: `document_v1.0.txt`
- **画像ファイル**: `img_01_scene.jpg`
- **設定ファイル**: `config_mobile.yaml`
- **出力ファイル**: `document_final.html`

**バージョン管理**:
```bash
# 大きな変更前のバックアップ
cp document.txt backup/document_v1.0_$(date +%Y%m%d).txt

# 変更履歴をファイル末尾に記録
echo "# 変更履歴" >> document.txt
echo "- $(date): 大幅な構成変更" >> document.txt
```

---

## 🎨 Kumihan記法の実践テクニック

### 📊 文書構造の最適化

#### **見出し階層の設計**
```
;;;見出し1
文書タイトル
;;;

;;;見出し2
第1章 - 大項目
;;;

;;;見出し3
1.1 中項目
;;;

;;;見出し4
詳細説明
;;;
```

**推奨階層深度**: 最大4レベルまで

#### **情報の重要度別記法**
```
;;;ハイライト color=#ffe6e6
緊急・重要な情報
;;;

;;;ハイライト color=#fff3cd
注意・ヒント
;;;

;;;ハイライト color=#e6ffe6
参考・補足情報
;;;

;;;枠線
まとめ・要点
;;;
```

### 🖼️ 画像の効果的な活用

#### **推奨画像仕様**
- **形式**: JPEG（写真）、PNG（図表）
- **サイズ**: 幅1200px以下
- **容量**: 1ファイル500KB以下
- **命名**: 連番 + 内容説明

#### **画像記法の使い分け**
```
;;;画像 alt=概要図
overview_diagram.png
;;;

;;;画像 alt=詳細画面
detail_screenshot.jpg
;;;
```

### 📱 レスポンシブ対応のテクニック

**config.yaml設定例**:
```yaml
responsive_design:
  mobile_breakpoint: "768px"
  
mobile_optimization:
  font_size_scale: 1.1
  line_height_scale: 1.2
  
styles:
  max_width: "800px"
  margin: "0 auto"
```

---

## 🔧 配布用HTML最適化

### 📦 配布パッケージの作成

#### **基本的な配布準備**
```bash
# 配布用ZIPの作成
python -m kumihan_formatter zip-dist . -o release/

# ファイルサイズの確認
ls -lh release/*.zip
```

#### **最適化チェックリスト**
- [ ] HTMLファイルサイズ（1MB以下推奨）
- [ ] 画像合計サイズ（5MB以下推奨）
- [ ] モバイル表示の確認
- [ ] オフライン閲覧の確認

### 🌐 Web配布の最適化

#### **SEO対応（オプション）**
```yaml
# config.yaml
metadata:
  title: "文書タイトル"
  description: "文書の説明（120文字以内）"
  keywords: "キーワード1, キーワード2"
  author: "作成者名"
```

#### **ソーシャル共有対応**
```yaml
# config.yaml
social_media:
  og_title: "ソーシャル用タイトル"
  og_description: "ソーシャル用説明"
  og_image: "images/thumbnail.jpg"
```

---

## 📊 大規模文書の管理技法

### 📄 文書分割戦略

#### **分割の判断基準**
- **ファイルサイズ**: 100KB以上
- **行数**: 1,000行以上
- **セクション数**: 10章以上

#### **分割方法**
```
main_document.txt           ← 目次・概要
├── chapter01_intro.txt     ← 第1章
├── chapter02_basic.txt     ← 第2章
├── chapter03_advanced.txt  ← 第3章
└── appendix.txt           ← 付録
```

**一括変換例**:
```bash
# 複数ファイルの一括変換
kumihan *.txt -o dist/

# 設定ファイル適用での一括変換
kumihan *.txt --config config.yaml -o dist/
```

### 🔄 バージョン管理

#### **Git活用パターン**
```bash
# 初期設定
git init
git add *.txt images/
git commit -m "初回版"

# 変更管理
git add document.txt
git commit -m "第2章追加"

# タグによるバージョン管理
git tag v1.0.0
```

#### **ファイルベース管理**
```
backup/
├── 2024-01-15_v1.0/
│   ├── document.txt
│   └── images/
├── 2024-01-20_v1.1/
│   ├── document.txt
│   └── images/
└── 2024-01-25_v1.2/
    ├── document.txt
    └── images/
```

---

## ⚡ 作業効率化のコツ

### 🎯 テンプレート活用

#### **基本構成テンプレート**
```
;;;見出し1
[文書タイトル]
;;;

;;;枠線
基本情報：
- 作成日：[日付]
- 更新日：[日付]  
- バージョン：[バージョン]
- 作成者：[名前]
;;;

;;;見出し2
概要
;;;

[文書の概要説明]

;;;見出し2
詳細
;;;

[詳細内容]

;;;見出し2
まとめ
;;;

[まとめ・結論]
```

#### **セクションテンプレート**
```
;;;見出し3
[セクションタイトル]
;;;

;;;太字
重要ポイント
;;;
[重要な情報]

;;;枠線
詳細情報：
- 項目1：[内容]
- 項目2：[内容]
- 項目3：[内容]
;;;

;;;ハイライト color=#fff3cd
注意事項
;;;
[注意すべき点]
```

### ⌨️ ショートカット的記法

#### **よく使うパターンの省略**
```bash
# エイリアス設定例（bashrc/zshrc）
alias kumi="python -m kumihan_formatter"
alias kumic="python -m kumihan_formatter --config config.yaml"
alias kumip="python -m kumihan_formatter --no-preview"

# 使用例
kumi document.txt          # 基本変換
kumic document.txt         # 設定適用変換
kumip document.txt         # プレビューなし変換
```

#### **繰り返し処理の自動化**
```bash
#!/bin/bash
# convert_all.sh - 全文書変換スクリプト

for file in *.txt; do
    echo "Converting $file..."
    python -m kumihan_formatter "$file" --config config.yaml
done

echo "変換完了！"
```

---

## 🎨 カスタマイズのベストプラクティス

### 🎭 テーマ設定

#### **ライトテーマ（デフォルト）**
```yaml
# config.yaml
styles:
  background_color: "#ffffff"
  text_color: "#2c3e50"
  heading_color: "#34495e"
  link_color: "#3498db"
  border_color: "#ecf0f1"
```

#### **ダークテーマ**
```yaml
# config_dark.yaml
styles:
  background_color: "#2c3e50"
  text_color: "#ecf0f1"
  heading_color: "#ffffff"
  link_color: "#74b9ff"
  border_color: "#636e72"
```

#### **印刷用テーマ**
```yaml
# config_print.yaml
print_styles:
  font_family: "serif"
  font_size: "11pt"
  margin: "20mm"
  background_images: false
  colors: false
```

### 🎨 カスタムCSS活用

```yaml
# config.yaml
custom_css: |
  /* カスタムスタイル */
  .highlight {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px;
    border-radius: 8px;
  }
  
  .box {
    border: 2px solid #3498db;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  }
  
  h1, h2, h3 {
    border-left: 4px solid #e74c3c;
    padding-left: 15px;
  }
```

---

## 📈 品質向上のチェックポイント

### 🔍 変換前チェック

- [ ] **記法確認**: 全ての`;;;`マーカーが正しく閉じられている
- [ ] **画像確認**: 全ての画像ファイルが存在する
- [ ] **リンク確認**: 内部リンクが正しく設定されている
- [ ] **文字コード**: UTF-8で保存されている

### 🌐 変換後チェック

- [ ] **表示確認**: 意図した通りに表示されている
- [ ] **レスポンシブ**: モバイルで正常に表示される
- [ ] **パフォーマンス**: ページ読み込みが2秒以内
- [ ] **互換性**: 主要ブラウザで動作する

### 📋 配布前最終チェック

- [ ] **ファイルサイズ**: 合計5MB以下
- [ ] **オフライン動作**: インターネット接続なしで閲覧可能
- [ ] **エラーなし**: ブラウザコンソールにエラーが出ない
- [ ] **完全性**: 全てのコンテンツが含まれている

---

## 📚 関連リソース

### 🛠️ 基本ガイド
- **[クイックスタートガイド](QUICKSTART.md)** - 初回セットアップ
- **[記法リファレンス](SYNTAX_REFERENCE.md)** - 全記法の詳細
- **[よくある質問](FAQ.md)** - 困ったときの解決法

### 🔧 技術情報
- **[トラブルシューティング](TROUBLESHOOTING.md)** - 問題解決ガイド
- **[設定ガイド](CONFIG_GUIDE.md)** - 詳細カスタマイズ方法

---

**効率的な文書作成をサポートします！ 🚀**