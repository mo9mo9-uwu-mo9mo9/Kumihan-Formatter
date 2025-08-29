"""HTML Footnote Processing - 脚注処理専用モジュール

HTMLFormatter分割により抽出 (Phase3最適化)
脚注関連の処理をすべて統合
"""

import re
from typing import Any, Dict, List, Optional, Tuple


class FootnoteManager:
    """脚注管理クラス"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.footnotes: Dict[str, str] = {}
        self.footnote_counter = 0
        self.footnote_links: List[Tuple[str, str]] = []

    def add_footnote(self, footnote_id: str, content: str) -> str:
        """脚注を追加して参照リンクを返す"""
        if footnote_id not in self.footnotes:
            self.footnote_counter += 1
            self.footnotes[footnote_id] = content

        self.footnote_links.append((footnote_id, content))
        return f'<a href="#{footnote_id}" class="footnote-ref" id="ref-{footnote_id}">{self.footnote_counter}</a>'

    def get_footnotes_html(self) -> str:
        """全脚注のHTMLを生成"""
        if not self.footnotes:
            return ""

        html_parts = ['<div class="footnotes">', "<ol>"]
        for footnote_id, content in self.footnotes.items():
            backlink = f'<a href="#ref-{footnote_id}" class="footnote-backlink">↩</a>'
            html_parts.append(f'<li id="{footnote_id}">{content} {backlink}</li>')
        html_parts.extend(["</ol>", "</div>"])
        return "\n".join(html_parts)

    def set_footnote_data(self, footnotes_data: Dict[str, Any]) -> None:
        """脚注データ設定"""
        if isinstance(footnotes_data, dict):
            self.footnotes.update(footnotes_data)

    def clear(self) -> None:
        """脚注データをクリア"""
        self.footnotes.clear()
        self.footnote_links.clear()
        self.footnote_counter = 0


class HTMLFootnoteProcessor:
    """HTML脚注処理専用クラス"""

    def __init__(self) -> None:
        self._footnote_manager = FootnoteManager()

    def handle_footnote(self, content: str, footnote_id: Optional[str] = None) -> str:
        """脚注要素を処理"""
        if not content.strip():
            return ""

        # 脚注IDを生成（未指定の場合）
        if not footnote_id:
            footnote_id = f"footnote-{len(self._footnote_manager.footnotes) + 1}"

        # 脚注として登録
        footnote_ref = self._footnote_manager.add_footnote(footnote_id, content)

        # 脚注参照を返す
        return f"<sup>{footnote_ref}</sup>"

    def generate_footnotes_html(self) -> str:
        """脚注セクションのHTMLを生成"""
        return self._footnote_manager.get_footnotes_html()

    def process_footnote_links(self, html_content: str) -> str:
        """HTMLコンテンツ内の脚注リンクを処理"""
        import re

        # 脚注記法を検出して変換 [^footnote-id] → 脚注リンク
        footnote_pattern = r"\[\^([^\]]+)\]"

        def replace_footnote(match: re.Match[str]) -> str:
            footnote_id = match.group(1)
            # 脚注内容を取得（この実装では簡略化）
            content = f"脚注: {footnote_id}"
            return self.handle_footnote(content, footnote_id)

        processed_html = re.sub(footnote_pattern, replace_footnote, html_content)

        # 脚注セクションを末尾に追加
        footnotes_html = self.generate_footnotes_html()
        if footnotes_html:
            processed_html += "\n\n" + footnotes_html

        return processed_html

    def clear_footnotes(self) -> None:
        """脚注データをリセット"""
        self._footnote_manager.clear()

    def get_footnote_count(self) -> int:
        """現在の脚注数を取得"""
        return len(self._footnote_manager.footnotes)

    def has_footnotes(self) -> bool:
        """脚注が存在するかチェック"""
        return len(self._footnote_manager.footnotes) > 0
