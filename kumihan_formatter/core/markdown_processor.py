"""
マークダウン プロセッサー

コードブロック処理・特殊要素変換機能
Issue #492 Phase 5A - markdown_converter.py分割
"""

import re
from typing import Any


class MarkdownProcessor:
    """Markdown processing functionality

    Handles code blocks, special element processing,
    and text normalization operations.
    """

    def __init__(self) -> None:
        """Initialize processor"""
        pass

    def _convert_code_blocks(self, text: str) -> str:
        """コードブロック（```）を変換"""

        def replace_code_block(match: Any) -> str:
            code_content = match.group(1)
            # HTMLエスケープ
            code_content = (
                code_content.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            return f"<pre><code>{code_content}</code></pre>"

        # ```code``` パターンを処理
        pattern = re.compile(r"```\n?(.*?)\n?```", re.DOTALL)
        return pattern.sub(replace_code_block, text)

    def _generate_heading_id(self, heading_text: str) -> str:
        """見出しからIDを生成"""
        # 英数字以外を除去してIDを生成
        clean_text = re.sub(r"[^\w\s-]", "", heading_text.lower())
        clean_text = re.sub(r"[-\s]+", "-", clean_text)
        return clean_text.strip("-")

    def normalize_text(self, text: str) -> str:
        """テキストの正規化処理"""
        # 改行を正規化
        return text.replace("\r\n", "\n").replace("\r", "\n")
