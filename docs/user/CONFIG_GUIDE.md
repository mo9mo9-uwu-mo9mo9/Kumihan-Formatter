# ⚠️ 非推奨: Kumihan-Formatter 設定ガイド

> **重要**: この機能は非推奨となりました。
> 
> **理由**: 
> - 初心者ユーザーには過剰に複雑
> - YAMLファイル・CSS知識が必要で、「開発知識なしで使える」という本来の目標と矛盾
> - 設定なしで「そのまま使える」ことがKumihan-Formatterの価値
> 
> **代替案**: 標準の記法セット（見出し、太字、枠線、ハイライト等）で十分な表現が可能です。
> 
> ---
> 
> ## ⚠️ 以下は削除予定の機能です

## 設定ファイルの基本

Kumihan-Formatterは、YAML/JSON形式の設定ファイルでカスタマイズ可能です。

### 設定ファイルの使用方法

```bash
kumihan input.txt --config my_config.yaml
```

## 設定可能な項目

### 1. カスタムマーカー

新しいマーカー（記法）を追加できます：

```yaml
# config.yaml
markers:
  カスタム注意:
    tag: div
    classes: ["custom-warning"]
    styles:
      background-color: "#ffcc00"
      border: "2px solid #ff9900"
      padding: "10px"
```

使用例：
```
;;;カスタム注意
これはカスタムマーカーの例です
;;;
```

### 2. テーマのカスタマイズ

既存テーマの色やフォントを調整：

```yaml
theme:
  name: "カスタムテーマ"
  base: "default"  # default, dark, sepia から選択
  overrides:
    colors:
      background: "#f5f5f5"
      text: "#2c3e50"
      heading: "#34495e"
    fonts:
      body: "Noto Sans JP, sans-serif"
      heading: "Noto Serif JP, serif"
```

### 3. 出力設定

HTML出力の詳細を制御：

```yaml
output:
  # タイトルタグの設定
  title_suffix: " - My Document"
  
  # メタタグの追加
  meta_tags:
    author: "Your Name"
    description: "Document description"
  
  # カスタムCSS/JSの追加
  custom_css: |
    .custom-class {
      color: blue;
    }
  custom_js: |
    console.log('Document loaded');
```

### 4. 画像処理

画像の扱い方を設定：

```yaml
images:
  # 画像フォルダのパス
  source_dir: "assets/images"
  
  # 最大幅の設定
  max_width: 800
  
  # 遅延読み込み
  lazy_loading: true
```

## 完全な設定例

### YAML形式（推奨）

```yaml
# my_config.yaml
# カスタムマーカーの定義
markers:
  重要:
    tag: div
    classes: ["important-box"]
    styles:
      background-color: "#fff3cd"
      border-left: "5px solid #ffc107"
      padding: "15px"
      margin: "10px 0"
  
  メモ:
    tag: div
    classes: ["memo"]
    styles:
      background-color: "#e3f2fd"
      border: "1px dashed #2196f3"
      padding: "10px"
      font-style: "italic"

# テーマ設定
theme:
  name: "My Custom Theme"
  base: "default"
  overrides:
    colors:
      background: "#fafafa"
      text: "#333333"
      link: "#0066cc"
      heading: "#222222"

# 出力設定
output:
  title_suffix: " | My Project"
  meta_tags:
    author: "Your Name"
    keywords: "CoC, シナリオ, TRPG"
```

### JSON形式

```json
{
  "markers": {
    "重要": {
      "tag": "div",
      "classes": ["important-box"],
      "styles": {
        "background-color": "#fff3cd",
        "border-left": "5px solid #ffc107",
        "padding": "15px",
        "margin": "10px 0"
      }
    }
  },
  "theme": {
    "name": "My Custom Theme",
    "base": "default",
    "overrides": {
      "colors": {
        "background": "#fafafa",
        "text": "#333333"
      }
    }
  }
}
```

## 高度な使用例

### プロジェクト固有の設定

プロジェクトルートに `.kumihan.yaml` を配置：

```yaml
# .kumihan.yaml
# プロジェクト全体で使用する設定
markers:
  NPC:
    tag: div
    classes: ["npc-info"]
    styles:
      background: "linear-gradient(to right, #f0f0f0, #ffffff)"
      border: "1px solid #ddd"
      padding: "20px"
      
  アイテム:
    tag: div
    classes: ["item-box"]
    styles:
      background-color: "#f9f9f9"
      border: "2px solid #666"
      border-radius: "5px"
      padding: "15px"
```

### 複数設定の組み合わせ

```bash
# ベース設定とプロジェクト設定を組み合わせ
kumihan input.txt --config base.yaml --config project.yaml
```

## トラブルシューティング

### 設定が反映されない

1. YAMLの構文エラーを確認
2. インデントが正しいか確認（スペース2つまたは4つ）
3. 設定ファイルのパスが正しいか確認

### カスタムマーカーが認識されない

- マーカー名に使用できる文字：日本語、英数字、ハイフン、アンダースコア
- 予約語（太字、枠線など）との重複を避ける

## サンプル設定ファイル

`examples/config-sample.yaml` に詳細なサンプルがあります：

```bash
# サンプルをコピーして編集
cp examples/config-sample.yaml my_config.yaml
```

## 注意事項

- 設定ファイルは上級者向けの機能です
- 基本的な用途では標準機能で十分です
- 設定を複雑にしすぎると、保守が困難になります
- チーム開発では設定ファイルを共有してください