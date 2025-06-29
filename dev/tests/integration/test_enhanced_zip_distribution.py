#!/usr/bin/env python3
"""Enhanced ZIP Distribution Tests

Issue #118対応: 拡張ZIP配布機能のテスト
エンドユーザー向け文書変換とフレンドリーな配布構造のテスト
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

# テスト対象のインポート
from kumihan_formatter.core.markdown_converter import SimpleMarkdownConverter, convert_markdown_file
from kumihan_formatter.core.doc_classifier import DocumentClassifier, DocumentType, classify_document
from kumihan_formatter.core.distribution_manager import DistributionManager, create_user_distribution


class TestMarkdownConverter:
    """Markdown変換器のテスト"""
    
    def test_basic_markdown_conversion(self):
        """基本的なMarkdown変換テスト"""
        converter = SimpleMarkdownConverter()
        
        markdown_text = """# テスト見出し
        
これは**テスト**文書です。

## サブ見出し

- リスト項目1
- リスト項目2

[リンクテキスト](https://example.com)

```
コードブロック
```
"""
        
        html = converter.convert_text(markdown_text)
        
        # 基本要素の確認
        assert '<h1 id="テスト見出し">テスト見出し</h1>' in html
        assert '<h2 id="サブ見出し">サブ見出し</h2>' in html
        assert '<strong>テスト</strong>' in html
        assert '<ul>' in html and '<li>リスト項目1</li>' in html
        assert '<a href="https://example.com">リンクテキスト</a>' in html
        assert '<pre><code>' in html and 'コードブロック' in html
    
    def test_japanese_content_handling(self):
        """日本語コンテンツの処理テスト"""
        converter = SimpleMarkdownConverter()
        
        markdown_text = """# Kumihan-Formatterについて

**Kumihan-Formatter**は、同人作家向けの組版ツールです。

## 特徴

- 簡単操作
- 美しい出力
- 日本語対応

詳細は[こちら](https://github.com/example)をご覧ください。
"""
        
        html = converter.convert_text(markdown_text)
        
        # 日本語処理の確認
        assert 'Kumihan-Formatterについて' in html
        assert '同人作家向けの組版ツール' in html
        assert '<strong>Kumihan-Formatter</strong>' in html
        assert '簡単操作' in html
    
    def test_file_conversion(self):
        """ファイル変換のテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# サンプル文書

これはテスト用のサンプル文書です。

## 使い方

1. ファイルを開く
2. 内容を確認
3. HTMLに変換

**重要**: このファイルはテスト用です。
""")
            temp_md = Path(f.name)
        
        try:
            temp_html = temp_md.with_suffix('.html')
            success = convert_markdown_file(temp_md, temp_html, "サンプル文書")
            
            assert success
            assert temp_html.exists()
            
            # HTMLファイルの内容確認
            with open(temp_html, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            assert '<!DOCTYPE html>' in html_content
            assert '<title>サンプル文書 - Kumihan-Formatter</title>' in html_content
            assert 'このファイルはテスト用です' in html_content
        
        finally:
            temp_md.unlink()
            if temp_html.exists():
                temp_html.unlink()


class TestDocumentClassifier:
    """文書分類器のテスト"""
    
    def test_essential_document_classification(self):
        """重要文書の分類テスト"""
        classifier = DocumentClassifier()
        base_path = Path("/project")
        
        # 重要文書の分類
        readme_path = base_path / "README.md"
        assert classifier.classify_file(readme_path, base_path) == DocumentType.USER_ESSENTIAL
        
        license_path = base_path / "LICENSE"
        assert classifier.classify_file(license_path, base_path) == DocumentType.USER_ESSENTIAL
        
        quickstart_path = base_path / "quickstart.md"
        assert classifier.classify_file(quickstart_path, base_path) == DocumentType.USER_ESSENTIAL
    
    def test_user_guide_classification(self):
        """ユーザーガイドの分類テスト"""
        classifier = DocumentClassifier()
        base_path = Path("/project")
        
        install_path = base_path / "docs/user/INSTALL.md"
        assert classifier.classify_file(install_path, base_path) == DocumentType.USER_GUIDE
        
        usage_path = base_path / "USAGE.md"
        assert classifier.classify_file(usage_path, base_path) == DocumentType.USER_GUIDE
        
        tutorial_path = base_path / "tutorial.md"
        assert classifier.classify_file(tutorial_path, base_path) == DocumentType.USER_GUIDE
    
    def test_developer_document_classification(self):
        """開発者文書の分類テスト"""
        classifier = DocumentClassifier()
        base_path = Path("/project")
        
        contrib_path = base_path / "CONTRIBUTING.md"
        assert classifier.classify_file(contrib_path, base_path) == DocumentType.DEVELOPER
        
        dev_path = base_path / "dev/README.md"
        assert classifier.classify_file(dev_path, base_path) == DocumentType.DEVELOPER
        
        api_path = base_path / "API.md"
        assert classifier.classify_file(api_path, base_path) == DocumentType.DEVELOPER
    
    def test_technical_document_classification(self):
        """技術文書の分類テスト"""
        classifier = DocumentClassifier()
        base_path = Path("/project")
        
        claude_path = base_path / "CLAUDE.md"
        assert classifier.classify_file(claude_path, base_path) == DocumentType.TECHNICAL
        
        spec_path = base_path / "SPEC.md"
        assert classifier.classify_file(spec_path, base_path) == DocumentType.TECHNICAL
        
        style_path = base_path / "STYLE_GUIDE.md"
        assert classifier.classify_file(style_path, base_path) == DocumentType.TECHNICAL
    
    def test_conversion_strategy(self):
        """変換戦略の取得テスト"""
        classifier = DocumentClassifier()
        
        # 各文書タイプの変換戦略を確認
        essential_strategy = classifier.get_conversion_strategy(DocumentType.USER_ESSENTIAL)
        assert essential_strategy == ("markdown_to_txt", "docs/essential")
        
        guide_strategy = classifier.get_conversion_strategy(DocumentType.USER_GUIDE)
        assert guide_strategy == ("markdown_to_html", "docs/user")
        
        dev_strategy = classifier.get_conversion_strategy(DocumentType.DEVELOPER)
        assert dev_strategy == ("copy_as_is", "docs/developer")


class TestDistributionManager:
    """配布構造管理器のテスト"""
    
    def setup_test_project(self, temp_dir: Path) -> Path:
        """テスト用プロジェクト構造を作成"""
        project_dir = temp_dir / "test_project"
        project_dir.mkdir()
        
        # README.md（重要文書）
        (project_dir / "README.md").write_text("""# Test Project

This is a test project for Kumihan-Formatter.

## Features

- Feature 1
- Feature 2

**Important**: This is a test.
""", encoding='utf-8')
        
        # docs/user/usage.md（ユーザーガイド）
        docs_user = project_dir / "docs/user"
        docs_user.mkdir(parents=True)
        (docs_user / "usage.md").write_text("""# 使い方ガイド

## 基本操作

1. ステップ1
2. ステップ2
3. ステップ3

詳細な説明...
""", encoding='utf-8')
        
        # CONTRIBUTING.md（開発者文書）
        (project_dir / "CONTRIBUTING.md").write_text("""# Contributing Guide

## Development Setup

For developers only.
""", encoding='utf-8')
        
        # kumihan_formatter/（メインプログラム）
        main_dir = project_dir / "kumihan_formatter"
        main_dir.mkdir()
        (main_dir / "__init__.py").write_text("# Main package", encoding='utf-8')
        (main_dir / "main.py").write_text("def main(): pass", encoding='utf-8')
        
        # examples/（サンプル）
        examples_dir = project_dir / "examples"
        examples_dir.mkdir()
        (examples_dir / "sample.txt").write_text("Sample content", encoding='utf-8')
        
        return project_dir
    
    def test_user_distribution_creation(self):
        """ユーザー配布構造の作成テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # テストプロジェクトをセットアップ
            source_dir = self.setup_test_project(temp_path)
            output_dir = temp_path / "distribution"
            
            # Mock UI
            mock_ui = Mock()
            
            # 配布構造を作成
            manager = DistributionManager(ui=mock_ui)
            stats = manager.create_user_friendly_distribution(
                source_dir, output_dir, 
                convert_docs=True, 
                include_developer_docs=False
            )
            
            # 基本構造の確認
            assert (output_dir / "docs/essential").exists()
            assert (output_dir / "docs/user").exists()
            assert (output_dir / "docs/index.html").exists()
            assert (output_dir / "配布情報.txt").exists()
            
            # 変換統計の確認
            assert stats['converted_to_txt'] > 0  # README.mdがTXT変換された
            assert stats['converted_to_html'] > 0  # usage.mdがHTML変換された
            
            # 変換されたファイルの確認
            readme_txt = output_dir / "docs/essential/はじめに.txt"
            assert readme_txt.exists()
            
            usage_html = output_dir / "docs/user/使い方ガイド.html"
            assert usage_html.exists()
            
            # HTML内容の確認
            with open(usage_html, 'r', encoding='utf-8') as f:
                html_content = f.read()
            assert '使い方ガイド' in html_content
            assert '基本操作' in html_content
    
    def test_developer_docs_inclusion(self):
        """開発者文書の包含テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            source_dir = self.setup_test_project(temp_path)
            output_dir = temp_path / "distribution"
            
            manager = DistributionManager()
            manager.create_user_friendly_distribution(
                source_dir, output_dir,
                convert_docs=True,
                include_developer_docs=True
            )
            
            # 開発者文書ディレクトリの確認
            assert (output_dir / "docs/developer").exists()
            
            # CONTRIBUTING.mdがコピーされているか確認
            contributing_file = output_dir / "docs/developer/CONTRIBUTING.md"
            assert contributing_file.exists()
    
    def test_index_page_generation(self):
        """インデックスページ生成のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            source_dir = self.setup_test_project(temp_path)
            output_dir = temp_path / "distribution"
            
            manager = DistributionManager()
            manager.create_user_friendly_distribution(
                source_dir, output_dir, convert_docs=True
            )
            
            index_file = output_dir / "docs/index.html"
            assert index_file.exists()
            
            # インデックス内容の確認
            with open(index_file, 'r', encoding='utf-8') as f:
                index_content = f.read()
            
            assert 'Kumihan-Formatter ドキュメント' in index_content
            assert 'まず最初に読む文書' in index_content
            assert 'はじめに.txt' in index_content
            assert '使い方ガイド' in index_content


class TestIntegration:
    """統合テスト"""
    
    def test_complete_workflow(self):
        """完全なワークフローのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # サンプルプロジェクトの作成
            project_dir = temp_path / "sample_project"
            project_dir.mkdir()
            
            # 複数の文書タイプを作成
            documents = {
                "README.md": "# Sample Project\n\nThis is a sample.",
                "LICENSE": "MIT License\n\nCopyright...",
                "docs/user/install.md": "# Installation\n\nHow to install...",
                "CONTRIBUTING.md": "# Contributing\n\nFor developers...",
                "SPEC.md": "# Technical Spec\n\nInternal spec..."
            }
            
            for doc_path, content in documents.items():
                file_path = project_dir / doc_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding='utf-8')
            
            # メインプログラムファイル
            (project_dir / "main.py").write_text("print('Hello')", encoding='utf-8')
            
            # 配布物作成
            output_dir = temp_path / "distribution"
            stats = create_user_distribution(
                project_dir, output_dir,
                convert_docs=True,
                include_developer_docs=False
            )
            
            # 結果の検証
            assert (output_dir / "docs/essential").exists()
            assert (output_dir / "docs/user").exists()
            assert (output_dir / "docs/index.html").exists()
            
            # 統計の検証
            assert stats['converted_to_txt'] >= 2  # README.md, LICENSE
            assert stats['converted_to_html'] >= 1  # install.md
            assert stats['total_files'] >= 5
            
            # 開発者文書が除外されていることを確認
            assert not (output_dir / "docs/developer").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])