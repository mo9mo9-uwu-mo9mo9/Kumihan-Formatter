# Kumihan-Formatter 使用例・チュートリアル

**Issue #1172対応**: アーキテクチャ最適化最終フェーズ - 使用例・チュートリアル作成  
**作成日**: 2025年8月24日

---

## 🚀 クイックスタート

### インストール・セットアップ

```bash
# プロジェクトのクローン
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter

# 依存関係のインストール
pip install -r requirements.txt

# 基本動作確認
python3 -m kumihan_formatter --version
```

### 最初の変換

**1. テストファイル作成**
```bash
# test.txt を作成
cat > test.txt << 'EOF'
# 見出し1 #私の最初のKumihan文書##

これは通常のパラグラフです。

# 太字 #重要: この部分は強調されます##

# リスト #
- 項目1
- 項目2 
- 項目3
##

普通のテキストも、もちろん使えます。
EOF
```

**2. HTML変換実行**
```bash
python3 -m kumihan_formatter convert test.txt
```

**3. 結果確認**
```bash
# 生成されたHTMLファイルを確認
open test.html  # macOS
```

---

## 📝 Kumihan記法詳細ガイド

### 基本ブロック記法

#### 見出し
```
# 見出し1 #メインタイトル##
# 見出し2 #サブタイトル##  
# 見出し3 #小見出し##
```

#### テキスト装飾
```
# 太字 #強調したいテキスト##
# イタリック #斜体で表現したいテキスト##
# アンダーライン #下線付きテキスト##
```

#### 色付きハイライト
```
# ハイライト color=yellow #注意点##
# ハイライト color=red #警告##
# ハイライト color=green #成功メッセージ##
```

### 複合記法

#### リスト構造
```
# リスト #
- メイン項目1
  - サブ項目1-1
  - サブ項目1-2
- メイン項目2
- メイン項目3
  - サブ項目3-1
##
```

#### 番号付きリスト
```
# 番号リスト #
1. 最初のステップ
2. 2番目のステップ
3. 最後のステップ
##
```

#### コードブロック
```
# コード #
def hello_kumihan():
    print("Hello, Kumihan-Formatter!")
    return True
##
```

#### 引用ブロック
```
# 引用 #
これは重要な引用文です。
出典を明記することが大切です。
##
```

---

## 💻 プログラマティック使用例

### 例1: 基本的なAPI使用

```python
from kumihan_formatter import parse, render, convert

# 1. 最もシンプルな使用方法
kumihan_text = "# 見出し #サンプル##\n通常のテキスト"
html_output = convert(kumihan_text)
print(html_output)

# 2. ステップバイステップ処理
ast = parse(kumihan_text)
html = render(ast)
print(html)
```

### 例2: ファイル処理

```python
from kumihan_formatter.unified_api import KumihanFormatter

# フォーマッター初期化
formatter = KumihanFormatter()

# 単一ファイル変換
formatter.convert_file('input.txt', 'output.html')

# 複数ファイル一括変換
input_files = ['doc1.txt', 'doc2.txt', 'doc3.txt']
for input_file in input_files:
    output_file = input_file.replace('.txt', '.html')
    formatter.convert_file(input_file, output_file)
    print(f"変換完了: {input_file} → {output_file}")
```

### 例3: カスタム設定

```python
from kumihan_formatter.config import ConfigManager
from kumihan_formatter.parser import Parser
from kumihan_formatter.renderer import Renderer

# カスタム設定
custom_config = {
    'output': {
        'format': 'html',
        'encoding': 'utf-8',
        'template': 'modern'
    },
    'processing': {
        'parallel': True,
        'threads': 4
    }
}

# 設定付きで初期化
config_manager = ConfigManager()
config_manager.update_config(custom_config)

parser = Parser(config=custom_config)
renderer = Renderer(config=custom_config)

# 処理実行
text = "# 見出し #カスタム設定テスト##"
ast = parser.parse(text)
html = renderer.render(ast)
```

### 例4: エラーハンドリング

```python
from kumihan_formatter import convert
from kumihan_formatter.core.common.error_types import ParsingError, RenderingError

def safe_convert(text):
    try:
        return convert(text)
    except ParsingError as e:
        print(f"パースエラー: {e}")
        return None
    except RenderingError as e:
        print(f"レンダリングエラー: {e}")
        return None
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return None

# 安全な変換実行
result = safe_convert("# 見出し #テスト##")
if result:
    print("変換成功")
    print(result)
else:
    print("変換失敗")
```

---

## 🎯 実用的なユースケース

### ユースケース1: ブログ記事作成

```python
blog_content = """
# 見出し1 #Kumihan-Formatter を使ったブログ作成##

# 見出し2 #はじめに##

このブログでは、Kumihan-Formatter の素晴らしさについて説明します。

# 太字 #なぜKumihan-Formatterなのか？##

# リスト #
- 直感的な記法
- 美しいHTML出力
- 日本語に特化した設計
##

# 見出し2 #使用方法##

# コード #
from kumihan_formatter import convert
html = convert(text)
##

# イタリック #詳細は公式ドキュメントをご覧ください##
"""

from kumihan_formatter import convert
html = convert(blog_content)

# ブログファイルとして保存
with open('blog_post.html', 'w', encoding='utf-8') as f:
    f.write(html)
```

### ユースケース2: ドキュメンテーション生成

```python
# プロジェクトドキュメント自動生成
import os
from pathlib import Path
from kumihan_formatter import convert

def generate_docs(source_dir, output_dir):
    """ディレクトリ内の全Kumihanファイルを変換"""
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    
    # 出力ディレクトリ作成
    output_path.mkdir(exist_ok=True)
    
    # .txt ファイルを検索・変換
    for txt_file in source_path.glob('*.txt'):
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        html = convert(content)
        
        output_file = output_path / f"{txt_file.stem}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"変換完了: {txt_file} → {output_file}")

# 実行例
generate_docs('./docs_source', './docs_html')
```

### ユースケース3: 自動レポート生成

```python
def generate_daily_report(data):
    """データから日次レポートを生成"""
    
    report_template = """
# 見出し1 #日次レポート - {date}##

# 見出し2 #サマリー##

本日の処理結果:

# リスト #
- 処理件数: {processed_count}件
- 成功件数: {success_count}件  
- エラー件数: {error_count}件
##

# 見出し2 #詳細結果##

# 太字 #成功率: {success_rate:.1f}%##

{details}

# イタリック #レポート生成時刻: {timestamp}##
"""
    
    from datetime import datetime
    
    # レポート内容生成
    success_rate = (data['success_count'] / data['processed_count']) * 100
    
    report_text = report_template.format(
        date=datetime.now().strftime('%Y-%m-%d'),
        processed_count=data['processed_count'],
        success_count=data['success_count'],
        error_count=data['error_count'], 
        success_rate=success_rate,
        details=data['details'],
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    # HTML変換
    from kumihan_formatter import convert
    html = convert(report_text)
    
    # ファイル保存
    output_file = f"daily_report_{datetime.now().strftime('%Y%m%d')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_file

# 使用例
sample_data = {
    'processed_count': 1500,
    'success_count': 1487,
    'error_count': 13,
    'details': '処理詳細情報...'
}

report_file = generate_daily_report(sample_data)
print(f"レポート生成完了: {report_file}")
```

---

## 🛠️ 高度な使用法

### カスタムパーサー作成

```python
from kumihan_formatter.parsers.parser_protocols import ParserProtocol
from kumihan_formatter.core.ast_nodes.node import Node

class CustomTableParser(ParserProtocol):
    """カスタムテーブルパーサー"""
    
    def parse(self, text: str) -> List[Node]:
        """テーブル記法をパース"""
        # カスタムロジック
        nodes = []
        
        if '|' in text and '--' in text:
            # Markdown風テーブルを検出
            table_node = self.parse_table(text)
            nodes.append(table_node)
        
        return nodes
    
    def parse_table(self, text: str) -> Node:
        """テーブル専用パース"""
        lines = text.strip().split('\n')
        # テーブル解析ロジック
        return Node(type='table', content=lines)

# パーサー登録
from kumihan_formatter.managers.plugin_manager import PluginManager

plugin_manager = PluginManager()
plugin_manager.register_parser(CustomTableParser())
```

### カスタムレンダラー作成

```python
from kumihan_formatter.core.rendering.base_renderer import BaseRenderer

class MarkdownRenderer(BaseRenderer):
    """Markdownレンダラー"""
    
    def render_heading(self, node):
        level = node.get('level', 1)
        content = node.get('content', '')
        return '#' * level + ' ' + content + '\n\n'
    
    def render_text(self, node):
        return node.get('content', '') + '\n\n'
    
    def render_bold(self, node):
        content = node.get('content', '')
        return f"**{content}**"

# 使用例
custom_renderer = MarkdownRenderer()
```

---

## 🔧 CLI詳細使用法

### 基本コマンド

```bash
# ヘルプ表示
kumihan-formatter --help
kumihan-formatter convert --help

# バージョン確認
kumihan-formatter --version

# 基本変換
kumihan-formatter convert input.txt

# 出力先指定
kumihan-formatter convert input.txt --output custom_output.html

# 複数ファイル変換
kumihan-formatter convert doc1.txt doc2.txt doc3.txt
```

### 高度なオプション

```bash
# ファイル監視モード（自動再変換）
kumihan-formatter convert document.txt --watch

# 詳細ログ出力
kumihan-formatter convert document.txt --verbose

# 設定ファイル指定
kumihan-formatter convert document.txt --config custom_config.yaml

# 出力形式指定
kumihan-formatter convert document.txt --format html --encoding utf-8
```

### 一括処理スクリプト

```bash
#!/bin/bash
# batch_convert.sh - 一括変換スクリプト

INPUT_DIR="./source_docs"
OUTPUT_DIR="./html_docs"

# 出力ディレクトリ作成
mkdir -p "$OUTPUT_DIR"

# 全txtファイルを変換
for file in "$INPUT_DIR"/*.txt; do
    if [ -f "$file" ]; then
        filename=$(basename "$file" .txt)
        echo "変換中: $file"
        python3 -m kumihan_formatter convert "$file" --output "$OUTPUT_DIR/$filename.html"
        echo "完了: $OUTPUT_DIR/$filename.html"
    fi
done

echo "一括変換完了！"
```

---

## 📊 実践的なサンプル

### サンプル1: 技術文書

```
# 見出し1 #API設計ドキュメント##

# 見出し2 #概要##

このAPIは、ユーザー管理機能を提供します。

# 見出し3 #エンドポイント一覧##

# 太字 #ユーザー操作##

# リスト #
- GET /users - ユーザー一覧取得
- POST /users - 新規ユーザー作成
- PUT /users/{id} - ユーザー情報更新
- DELETE /users/{id} - ユーザー削除
##

# 見出し3 #リクエスト例##

# コード #
POST /users
Content-Type: application/json

{
  "name": "田中太郎",
  "email": "tanaka@example.com"
}
##

# 見出し3 #レスポンス例##

# コード #
{
  "id": 12345,
  "name": "田中太郎", 
  "email": "tanaka@example.com",
  "created_at": "2025-08-24T10:00:00Z"
}
##

# ハイライト color=yellow #注意: APIキーが必要です##
```

### サンプル2: 議事録

```
# 見出し1 #プロジェクト会議議事録##

# 太字 #日時: 2025年8月24日 14:00-15:00##
# 太字 #参加者: 山田、佐藤、田中##

# 見出し2 #アジェンダ##

# 番号リスト #
1. 前回議事録の確認
2. 進捗報告
3. 今後のスケジュール
4. その他
##

# 見出し2 #討議内容##

# 見出し3 #進捗報告##

# リスト #
- フロントエンド: 90%完了
- バックエンド: 75%完了  
- テスト: 60%完了
##

# 見出し3 #今後のスケジュール##

# 太字 #来週までのタスク:##

# リスト #
- 佐藤: API仕様書完成
- 田中: ユニットテスト追加
- 山田: UI/UXレビュー
##

# ハイライト color=red #重要: 納期は来月末です##

# 見出し2 #次回会議##

# 太字 #日時: 2025年8月31日 14:00##
# イタリック #場所: 第2会議室##
```

### サンプル3: マニュアル・手順書

```
# 見出し1 #システム運用マニュアル##

# 見出し2 #日常運用手順##

# 見出し3 #朝の確認作業##

# 番号リスト #
1. システム稼働状況確認
2. ログファイルチェック
3. ディスク容量確認
4. バックアップ状況確認
##

# 見出し3 #システム稼働確認##

# コード #
# サーバー状態確認
systemctl status application
systemctl status database

# プロセス確認  
ps aux | grep application
##

# 見出し3 #ログチェック##

# コード #
# エラーログ確認
tail -100 /var/log/application/error.log

# アクセスログ確認
tail -100 /var/log/application/access.log
##

# ハイライト color=red #緊急時: 障害発生時はすぐに管理者に連絡##

# 見出し2 #トラブルシューティング##

# 太字 #よくある問題と解決方法##

# リスト #
- データベース接続エラー → データベースサービス再起動
- アプリケーション応答なし → アプリケーション再起動
- ディスク容量不足 → 不要ファイル削除・ログローテーション
##
```

---

## 🔧 設定ファイル例

### 基本設定 (config.yaml)

```yaml
# Kumihan-Formatter 基本設定
output:
  format: html
  encoding: utf-8
  template: default
  minify: false

processing:
  parallel: false
  threads: 1
  timeout: 30

debug:
  enabled: false
  log_level: INFO
  verbose: false

# テンプレート設定
templates:
  default:
    css_framework: bootstrap
    theme: light
  
# 出力カスタマイズ  
html:
  include_css: true
  include_js: false
  responsive: true
```

### 高度な設定 (advanced_config.yaml)

```yaml
# 高度な設定例
output:
  format: html
  encoding: utf-8
  template: custom
  
processing:
  parallel: true
  threads: 4
  chunk_size: 1000
  memory_limit: 512MB

optimization:
  cache_enabled: true
  cache_size: 100MB
  precompile_patterns: true

custom_parsers:
  - name: table_parser
    enabled: true
  - name: math_parser  
    enabled: false

templates:
  custom:
    css_framework: tailwind
    theme: dark
    custom_css: styles/custom.css
```

---

## 📚 よくある質問 (FAQ)

### Q1: 大きなファイルの処理方法は？

```python
# 大きなファイルの効率的な処理
from kumihan_formatter.streaming_parser import StreamingParser

streaming_parser = StreamingParser()

# ファイルをチャンクに分けて処理
def process_large_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        for chunk in iter(lambda: f.read(8192), ''):
            if chunk:
                parsed_chunk = streaming_parser.parse_chunk(chunk)
                yield parsed_chunk

# 使用例
for chunk_result in process_large_file('large_document.txt'):
    print(f"チャンク処理完了: {len(chunk_result)} 要素")
```

### Q2: カスタムCSSの適用方法は？

```python
# カスタムCSS付きレンダリング
from kumihan_formatter.renderer import Renderer

custom_css = """
.kumihan-heading1 { color: #2c3e50; font-size: 2em; }
.kumihan-bold { color: #e74c3c; font-weight: bold; }
.kumihan-highlight { background-color: #f1c40f; padding: 0.2em; }
"""

renderer = Renderer(custom_css=custom_css)
html = renderer.render(ast_nodes)
```

### Q3: エラー処理のベストプラクティスは？

```python
from kumihan_formatter import convert
from kumihan_formatter.core.common.error_handler import ErrorHandler

def robust_convert(text, fallback_format='plain'):
    """堅牢な変換処理"""
    error_handler = ErrorHandler()
    
    try:
        return convert(text)
    except Exception as e:
        error_handler.handle_error(e)
        
        if fallback_format == 'plain':
            # プレーンテキストとして返す
            return f"<pre>{text}</pre>"
        else:
            raise
```

---

## 🎉 まとめ

Kumihan-Formatter は以下の特徴により、効率的で美しい文書作成を実現します:

### ✅ 主な利点
- **直感的**: 見たままの記法
- **高速**: 30,000要素/秒の処理能力
- **柔軟**: カスタマイズ・拡張可能
- **日本語特化**: 日本語文書に最適化

### 🎯 適用範囲
- ブログ記事作成
- 技術ドキュメント
- 議事録・レポート
- マニュアル・手順書
- プレゼンテーション資料

### 📞 サポート
- GitHub Issues: 問題報告・機能要求
- ドキュメント: 継続的に更新
- コミュニティ: 開発者フレンドリー

---

**Happy Formatting with Kumihan! 🎨**

*このチュートリアルは Issue #1172 アーキテクチャ最適化の一環として作成されました*