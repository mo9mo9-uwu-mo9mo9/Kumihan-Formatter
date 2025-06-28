#!/usr/bin/env python3
"""Enhanced ZIP Distribution Demo

Issue #118対応: 拡張ZIP配布機能のデモンストレーション
エンドユーザー向け文書変換とフレンドリーな配布構造のデモ
"""

import tempfile
import shutil
from pathlib import Path
import sys

# パスを追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# デモ対象のインポート
from kumihan_formatter.core.markdown_converter import SimpleMarkdownConverter
from kumihan_formatter.core.doc_classifier import DocumentClassifier, DocumentType
from kumihan_formatter.core.distribution_manager import create_user_distribution


def create_demo_project(project_dir: Path) -> None:
    """デモ用プロジェクトを作成"""
    print(f"📁 デモプロジェクト作成中: {project_dir}")
    
    # README.md（最重要文書）
    (project_dir / "README.md").write_text("""# Kumihan-Formatter

**Kumihan-Formatter**は、同人作家向けのテキスト組版ツールです。

## 🎯 特徴

- **簡単操作**: 技術知識不要でプロ品質の組版が可能
- **美しい出力**: HTML形式で配布可能な美しい文書を生成
- **日本語対応**: 日本語文書に最適化された組版エンジン

## 🚀 クイックスタート

1. ツールをダウンロード
2. テキストファイルを用意
3. 変換実行
4. 美しいHTML文書の完成！

**重要**: 最初に[インストールガイド](docs/user/install.html)をお読みください。

詳細な使い方は[ユーザーガイド](docs/user/usage.html)をご覧ください。
""", encoding='utf-8')
    
    # LICENSE（重要文書）
    (project_dir / "LICENSE").write_text("""MIT License

Copyright (c) 2025 Kumihan-Formatter

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""", encoding='utf-8')
    
    # docs/user/install.md（ユーザーガイド）
    docs_user = project_dir / "docs/user"
    docs_user.mkdir(parents=True)
    (docs_user / "install.md").write_text("""# インストールガイド

Kumihan-Formatterのインストール方法を説明します。

## 🖥️ 動作環境

- **Windows**: Windows 10 以降
- **macOS**: macOS 10.15 以降
- **Python**: 3.9 以降（自動インストール）

## 📦 インストール手順

### Windows の場合

1. **setup_windows.bat** をダブルクリック
2. インストールが自動的に実行されます
3. 完了メッセージが表示されるまで待機
4. インストール完了！

### macOS の場合

1. **setup_macos.command** をダブルクリック
2. 「開発元を確認できません」と表示された場合：
   - 右クリック → 開く を選択
   - 「開く」をクリックして実行
3. インストールが自動実行されます
4. 完了メッセージが表示されるまで待機

## ✅ インストール確認

インストール後、以下の方法で動作確認できます：

```
python -m kumihan_formatter --version
```

バージョン情報が表示されれば成功です。

## 🆘 トラブルシューティング

### よくある問題

**Q: Pythonがインストールされていないと言われる**  
A: セットアップスクリプトが自動的にPythonをインストールします。再実行してください。

**Q: 権限エラーが発生する**  
A: 管理者権限で実行するか、ユーザーディレクトリにインストールしてください。

**Q: Macで実行できない**  
A: システム環境設定 → セキュリティとプライバシー で許可してください。

詳細なトラブルシューティングは[こちら](troubleshooting.html)をご覧ください。
""", encoding='utf-8')
    
    # docs/user/usage.md（ユーザーガイド）
    (docs_user / "usage.md").write_text("""# 使い方ガイド

Kumihan-Formatterの基本的な使い方を説明します。

## 📝 基本的な変換方法

### 1. テキストファイルの準備

まず、変換したいテキストファイルを用意します：

```
;;;見出し1
私の同人小説
;;;

これは物語の始まりです...

;;;見出し2  
第1章: 出会い
;;;

主人公は突然...
```

### 2. 変換の実行

#### Windows の場合
1. **convert.bat** をダブルクリック
2. ファイル選択画面でテキストファイルを選択
3. 変換完了まで待機

#### macOS の場合  
1. **convert.command** をダブルクリック
2. ファイル選択画面でテキストファイルを選択
3. 変換完了まで待機

### 3. 結果の確認

変換が完了すると：
- HTMLファイルが生成されます
- 自動的にブラウザで表示されます
- 同人誌即売会などで配布可能な形式です

## 🎨 記法について

Kumihan-Formatterでは以下の記法が使用できます：

### 見出し
```
;;;見出し1
大見出し
;;;

;;;見出し2  
中見出し
;;;
```

### 強調
```
;;;太字
重要なテキスト
;;;

;;;ハイライト color=#ffe6e6
注意事項
;;;
```

### リスト
```
- 項目1
- 項目2
- 項目3

1. 順序のある項目
2. 2番目の項目  
3. 3番目の項目
```

## 💡 上級者向けコマンドライン

技術に詳しい方は、コマンドラインからも実行できます：

```bash
python -m kumihan_formatter input.txt -o output/
```

詳細なオプションについては技術仕様書をご覧ください。
""", encoding='utf-8')
    
    # CONTRIBUTING.md（開発者文書）
    (project_dir / "CONTRIBUTING.md").write_text("""# Contributing Guide

Thank you for your interest in contributing to Kumihan-Formatter!

## Development Setup

1. Clone the repository
2. Install dependencies: `pip install -e .[dev]`
3. Run tests: `pytest`

## Code Style

- Follow PEP 8
- Use type hints
- Write comprehensive tests

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

For more details, see the technical documentation.
""", encoding='utf-8')
    
    # SPEC.md（技術文書）
    (project_dir / "SPEC.md").write_text("""# Technical Specification

## Architecture

Kumihan-Formatter consists of:
- Parser: Text → AST
- Renderer: AST → HTML  
- CLI: User interface

## File Format

Input files use Kumihan markup syntax:
- Block markers: `;;;keyword;;;`
- Inline formatting
- Japanese-optimized

## API Reference

### Core Classes

- `Parser`: Text parsing
- `Renderer`: HTML generation
- `CLI`: Command interface

Internal implementation details for developers.
""", encoding='utf-8')
    
    # examples/（サンプルファイル）
    examples_dir = project_dir / "examples"
    examples_dir.mkdir()
    
    (examples_dir / "sample_story.txt").write_text(""";;;見出し1
サンプル小説: 魔法の図書館
;;;

;;;見出し2
プロローグ
;;;

古い図書館の奥で、少女は不思議な本を見つけた。

;;;太字+ハイライト color=#f0fff0
「この本は...何だろう？」
;;;

ページをめくると、文字が光り始めた。

;;;見出し2
第1章: 始まりの魔法
;;;

- 魔法の本の発見
- 図書館での出会い
- 新たな冒険の始まり

物語は今、始まったばかりである。
""", encoding='utf-8')
    
    # kumihan_formatter/（メインプログラム）
    main_dir = project_dir / "kumihan_formatter"
    main_dir.mkdir()
    (main_dir / "__init__.py").write_text('__version__ = "0.3.0"', encoding='utf-8')
    (main_dir / "cli.py").write_text("# Main CLI module", encoding='utf-8')
    (main_dir / "parser.py").write_text("# Parser module", encoding='utf-8')
    (main_dir / "renderer.py").write_text("# Renderer module", encoding='utf-8')
    
    # セットアップファイル
    (project_dir / "setup_windows.bat").write_text("""@echo off
echo Kumihan-Formatter セットアップ（Windows版）
echo ========================================
echo.
echo Python環境のセットアップ中...
echo セットアップが完了するまでお待ちください。
echo.
pause
""", encoding='utf-8')
    
    (project_dir / "setup_macos.command").write_text("""#!/bin/bash
echo "Kumihan-Formatter セットアップ（macOS版）"
echo "========================================"
echo
echo "Python環境のセットアップ中..."
echo "セットアップが完了するまでお待ちください。"
echo
read -p "Enterキーを押して続行..."
""", encoding='utf-8')
    
    print("✅ デモプロジェクト作成完了")


def demo_markdown_conversion():
    """Markdown変換のデモ"""
    print("\n🔄 Markdown変換デモ")
    print("=" * 50)
    
    converter = SimpleMarkdownConverter()
    
    sample_markdown = """# サンプル文書

これは**Markdown→HTML変換**のデモです。

## 機能一覧

- 見出し変換
- **太字**・*斜体*対応
- リスト処理
- [リンク](https://example.com)対応

```python
# コードブロックも対応
print("Hello, World!")
```

---

変換完了！
"""
    
    html_result = converter.convert_text(sample_markdown)
    
    print("📝 入力Markdown:")
    print(sample_markdown[:200] + "..." if len(sample_markdown) > 200 else sample_markdown)
    print("\n🌐 出力HTML（抜粋）:")
    html_preview = html_result[:300] + "..." if len(html_result) > 300 else html_result
    print(html_preview)
    print("\n✅ Markdown変換デモ完了")


def demo_document_classification():
    """文書分類のデモ"""
    print("\n📋 文書分類デモ")
    print("=" * 50)
    
    classifier = DocumentClassifier()
    
    # テスト用ファイルパス
    test_files = [
        ("README.md", "プロジェクトルート"),
        ("LICENSE", "プロジェクトルート"),
        ("docs/user/install.md", "ユーザー文書"),
        ("docs/user/usage.md", "ユーザー文書"),
        ("CONTRIBUTING.md", "プロジェクトルート"),
        ("SPEC.md", "プロジェクトルート"),
        ("dev/README.md", "開発者フォルダ"),
        ("examples/sample.txt", "サンプルフォルダ")
    ]
    
    base_path = Path("/project")
    
    print("ファイル分類結果:")
    for file_rel_path, description in test_files:
        file_path = base_path / file_rel_path
        doc_type = classifier.classify_file(file_path, base_path)
        
        type_names = {
            DocumentType.USER_ESSENTIAL: "🎯重要文書",
            DocumentType.USER_GUIDE: "📖ユーザーガイド",
            DocumentType.DEVELOPER: "🔧開発者文書",
            DocumentType.TECHNICAL: "⚙️技術文書",
            DocumentType.EXAMPLE: "📝サンプル",
            DocumentType.EXCLUDE: "🚫除外対象"
        }
        
        type_name = type_names.get(doc_type, str(doc_type))
        strategy, output_dir = classifier.get_conversion_strategy(doc_type)
        
        print(f"  {file_rel_path:<25} → {type_name:<12} ({strategy})")
    
    print("\n✅ 文書分類デモ完了")


def demo_distribution_creation():
    """配布構造作成のデモ"""
    print("\n📦 配布構造作成デモ")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # デモプロジェクトを作成
        project_dir = temp_path / "demo_project"
        create_demo_project(project_dir)
        
        # 配布構造を作成
        output_dir = temp_path / "user_distribution"
        
        print("📋 エンドユーザー向け配布構造を作成中...")
        
        # Mock UI for demo
        class MockUI:
            def info(self, message, details=None):
                if details:
                    print(f"ℹ️  {message}: {details}")
                else:
                    print(f"ℹ️  {message}")
            
            def success(self, message):
                print(f"✅ {message}")
            
            def warning(self, message):
                print(f"⚠️  {message}")
        
        mock_ui = MockUI()
        
        stats = create_user_distribution(
            project_dir, output_dir,
            convert_docs=True,
            include_developer_docs=False,
            ui=mock_ui
        )
        
        print(f"\n📊 処理統計:")
        print(f"  総ファイル数: {stats['total_files']}")
        print(f"  HTML変換: {stats['converted_to_html']}件")
        print(f"  TXT変換: {stats['converted_to_txt']}件")
        print(f"  コピー: {stats['copied_as_is']}件")
        print(f"  除外: {stats.get('excluded', 0)}件")
        
        print(f"\n📁 作成された配布構造:")
        for path in sorted(output_dir.rglob("*")):
            if path.is_file():
                rel_path = path.relative_to(output_dir)
                print(f"  {rel_path}")
        
        # 生成されたファイルの内容をプレビュー
        readme_txt = output_dir / "docs/essential/はじめに.txt"
        if readme_txt.exists():
            print(f"\n📄 生成例: {readme_txt.name}")
            with open(readme_txt, 'r', encoding='utf-8') as f:
                content = f.read()[:300]
            print(f"内容プレビュー: {content}...")
        
        index_html = output_dir / "docs/index.html"
        if index_html.exists():
            print(f"\n🌐 インデックスページも生成されました: docs/index.html")
    
    print("\n✅ 配布構造作成デモ完了")


def main():
    """メイン関数"""
    print("🚀 Enhanced ZIP Distribution Demo")
    print("Issue #118対応: エンドユーザー向け文書変換とフレンドリーな配布構造")
    print("=" * 80)
    
    try:
        # 各機能のデモを実行
        demo_markdown_conversion()
        demo_document_classification()
        demo_distribution_creation()
        
        print("\n" + "=" * 80)
        print("🎉 全デモが正常に完了しました！")
        print("\n💡 主な改善点:")
        print("  - Markdownファイルが読みやすいHTML・TXTに自動変換")
        print("  - ユーザー向けと開発者向け文書が適切に分離")
        print("  - 美しい文書インデックスページを自動生成")
        print("  - 同人作家など非技術者でも読みやすい配布物")
        print("\n🔧 zip-distコマンドの新オプション:")
        print("  --no-convert-docs    文書変換をスキップ")
        print("  --include-dev-docs   開発者向け文書も含める")
        print("=" * 80)
    
    except Exception as e:
        print(f"❌ デモ実行中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())