"""
Markdown Converter - 統合エントリーポイント
==========================================

Issue #1215対応: 不足していたmarkdown_converterモジュールの作成
core/markdown_converter.py へのエントリーポイント
"""

from .core.markdown_converter import SimpleMarkdownConverter


def convert_markdown_file(file_path: str, **kwargs) -> str:
    """
    Markdownファイルを変換

    Args:
        file_path: 変換対象ファイルパス
        **kwargs: 追加オプション

    Returns:
        変換結果HTML
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        converter = SimpleMarkdownConverter()
        return converter.convert(content)

    except Exception as e:
        return f'<div class="error">Markdown変換エラー: {str(e)}</div>'


def convert_markdown_text(text: str, **kwargs) -> str:
    """
    Markdownテキストを変換

    Args:
        text: 変換対象テキスト
        **kwargs: 追加オプション

    Returns:
        変換結果HTML
    """
    try:
        converter = SimpleMarkdownConverter()
        return converter.convert(text)

    except Exception as e:
        return f'<div class="error">Markdown変換エラー: {str(e)}</div>'


__all__ = ["convert_markdown_file", "convert_markdown_text", "SimpleMarkdownConverter"]
