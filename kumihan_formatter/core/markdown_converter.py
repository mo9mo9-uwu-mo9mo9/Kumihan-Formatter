"""
マークダウン変換器 統合モジュール

分割された各コンポーネントを統合し、後方互換性を確保
Issue #492 Phase 5A - markdown_converter.py分割
"""

from pathlib import Path
from typing import Optional

from .markdown_parser import MarkdownParser
from .markdown_processor import MarkdownProcessor
from .markdown_renderer import MarkdownRenderer


class SimpleMarkdownConverter:
    """Simple Markdown to HTML Converter - backward compatibility wrapper

    Provides unified interface to all markdown functionality
    while delegating to specialized component classes.
    """

    def __init__(self) -> None:
        """変換器を初期化"""
        self.parser = MarkdownParser()
        self.processor = MarkdownProcessor()
        self.renderer = MarkdownRenderer()
        self.patterns = self.parser.patterns

    def convert_file(self, markdown_file: Path, title: Optional[str] = None) -> str:
        """Markdownファイルを変換してHTMLを返す

        Args:
            markdown_file: 変換するMarkdownファイル
            title: HTMLのタイトル（未指定時はファイル名から生成）

        Returns:
            str: 変換されたHTML
        """
        if not markdown_file.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {markdown_file}")

        try:
            with open(markdown_file, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # UTF-8で読めない場合はShift_JISを試す
            with open(markdown_file, "r", encoding="shift_jis") as f:
                content = f.read()

        # タイトルを決定
        if title is None:
            title = self._extract_title_from_content(content) or markdown_file.stem

        # Markdown→HTML変換
        html_content = self.convert_text(content)

        return self._create_full_html(title, html_content, markdown_file.name)

    def convert_text(self, markdown_text: str) -> str:
        """Markdownテキストを変換してHTML本文を返す

        Args:
            markdown_text: 変換するMarkdownテキスト

        Returns:
            str: 変換されたHTML本文
        """
        # 改行を正規化
        text = self.processor.normalize_text(markdown_text)

        # コードブロック（```）を先に処理
        text = self._convert_code_blocks(text)

        # 見出しを変換
        text = self._convert_headings(text)

        # リストを変換
        text = self._convert_lists(text)

        # インライン要素を変換
        text = self._convert_inline_elements(text)

        # 段落を作成
        text = self._convert_paragraphs(text)

        return text

    # Delegate methods to appropriate components for backward compatibility

    def _extract_title_from_content(self, content: str) -> Optional[str]:
        """コンテンツから最初のH1見出しを抽出"""
        return self.renderer._extract_title_from_content(content, self.patterns)

    def _convert_code_blocks(self, text: str) -> str:
        """コードブロック（```）を変換"""
        return self.processor._convert_code_blocks(text)

    def _convert_headings(self, text: str) -> str:
        """見出しを変換"""
        return self.parser._convert_headings(text)

    def _generate_heading_id(self, heading_text: str) -> str:
        """見出しからIDを生成"""
        return self.parser._generate_heading_id(heading_text)

    def _convert_lists(self, text: str) -> str:
        """リストを変換"""
        return self.parser._convert_lists(text)

    def _convert_inline_elements(self, text: str) -> str:
        """インライン要素を変換"""
        return self.parser._convert_inline_elements(text)

    def _convert_paragraphs(self, text: str) -> str:
        """段落を作成"""
        return self.renderer._convert_paragraphs(text)

    def _create_full_html(self, title: str, content: str, source_filename: str) -> str:
        """完全なHTMLページを作成"""
        return self.renderer._create_full_html(title, content, source_filename)


def convert_markdown_file(
    input_file: Path, output_file: Path, title: Optional[str] = None
) -> bool:
    """Markdownファイルを変換してHTMLファイルを作成

    Args:
        input_file: 入力Markdownファイル
        output_file: 出力HTMLファイル
        title: HTMLのタイトル（省略時は自動生成）

    Returns:
        bool: 変換成功時True
    """
    try:
        converter = SimpleMarkdownConverter()
        html_content = converter.convert_file(input_file, title)

        # 出力ディレクトリを作成
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # HTMLファイルを保存
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return True

    except Exception as e:
        print(f"変換エラー: {e}")
        return False


def convert_markdown_text(markdown_text: str, title: str = "文書") -> str:
    """Markdownテキストを変換してHTMLを返す

    Args:
        markdown_text: 変換するMarkdownテキスト
        title: HTMLのタイトル

    Returns:
        str: 変換されたHTML
    """
    converter = SimpleMarkdownConverter()
    content = converter.convert_text(markdown_text)
    return converter._create_full_html(title, content, "テキスト")
