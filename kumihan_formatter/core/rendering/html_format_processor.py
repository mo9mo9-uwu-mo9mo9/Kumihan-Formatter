"""HTML Format Processing - フォーマット処理専用モジュール

HTMLFormatter分割により抽出 (Phase3最適化)
HTMLフォーマット関連の処理をすべて統合
"""

import re
from typing import List, Optional


class HTMLFormatProcessor:
    """HTMLフォーマット処理専用クラス"""

    def __init__(self, indent_size: int = 2):
        self.indent_size = indent_size
        self.tag_stack = []
        self.semantic_mode = True

    def format_html(self, html_content: str, compress: bool = False) -> str:
        """HTMLをフォーマット"""
        if not html_content:
            return ""

        if compress:
            return self.compress_html(html_content)

        # インデント適用
        formatted = self._apply_indentation(html_content)

        # セマンティック改善
        if self.semantic_mode:
            formatted = self._apply_semantic_improvements(formatted)

        # 空白正規化
        formatted = self._normalize_whitespace(formatted)

        return formatted

    def _apply_indentation(self, html_content: str) -> str:
        """HTMLにインデントを適用"""
        lines = html_content.split("\n")
        formatted_lines = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # 閉じタグの場合はインデントレベルを下げる
            if stripped.startswith("</") and not stripped.startswith("</br>"):
                # インライン要素でない場合のみ
                tag_name = stripped[2:].split(">")[0].split()[0]
                if not self._is_inline_tag(tag_name):
                    indent_level = max(0, indent_level - 1)

            # インデント適用
            indent = " " * (indent_level * self.indent_size)
            formatted_lines.append(indent + stripped)

            # 開始タグの場合はインデントレベルを上げる
            if stripped.startswith("<") and not stripped.startswith("</"):
                # 自己完結タグでない場合
                if not stripped.endswith("/>") and not stripped.startswith("<!"):
                    tag_name = stripped[1:].split(">")[0].split()[0]
                    if not self._is_inline_tag(tag_name):
                        indent_level += 1

        return "\n".join(formatted_lines)

    def _is_inline_tag(self, tag_name: str) -> bool:
        """インライン要素かどうかを判定"""
        inline_tags = {
            "a",
            "abbr",
            "acronym",
            "b",
            "bdi",
            "bdo",
            "big",
            "br",
            "button",
            "cite",
            "code",
            "dfn",
            "em",
            "i",
            "img",
            "input",
            "kbd",
            "label",
            "map",
            "mark",
            "meter",
            "noscript",
            "object",
            "output",
            "progress",
            "q",
            "ruby",
            "s",
            "samp",
            "script",
            "select",
            "small",
            "span",
            "strong",
            "sub",
            "sup",
            "textarea",
            "time",
            "tt",
            "u",
            "var",
            "wbr",
        }
        return tag_name.lower() in inline_tags

    def _apply_semantic_improvements(self, html_content: str) -> str:
        """セマンティックな改善を適用"""
        # div を意味のあるタグに置換
        improvements = {
            r'<div class="[^"]*header[^"]*"[^>]*>': "<header>",
            r"</div>(\s*<!--[^>]*header[^>]*-->)": "</header>",
            r'<div class="[^"]*footer[^"]*"[^>]*>': "<footer>",
            r"</div>(\s*<!--[^>]*footer[^>]*-->)": "</footer>",
            r'<div class="[^"]*nav[^"]*"[^>]*>': "<nav>",
            r"</div>(\s*<!--[^>]*nav[^>]*-->)": "</nav>",
            r'<div class="[^"]*article[^"]*"[^>]*>': "<article>",
            r"</div>(\s*<!--[^>]*article[^>]*-->)": "</article>",
            r'<div class="[^"]*section[^"]*"[^>]*>': "<section>",
            r"</div>(\s*<!--[^>]*section[^>]*-->)": "</section>",
        }

        for pattern, replacement in improvements.items():
            html_content = re.sub(
                pattern, replacement, html_content, flags=re.IGNORECASE
            )

        # 不要な空のdivを削除
        html_content = re.sub(r"<div[^>]*>\s*</div>", "", html_content)

        # 連続する空行を単一に
        html_content = re.sub(r"\n\s*\n\s*\n", "\n\n", html_content)

        return html_content

    def _normalize_whitespace(self, html_content: str) -> str:
        """空白を正規化"""
        # タグ内の余分な空白を除去
        html_content = re.sub(r"<([^>]+)\s+>", r"<\1>", html_content)

        # 属性間の余分な空白を正規化
        html_content = re.sub(r"\s+", " ", html_content)

        # 行末の空白を除去
        lines = [line.rstrip() for line in html_content.split("\n")]

        return "\n".join(lines)

    def compress_html(self, html_content: str) -> str:
        """HTMLを圧縮（最小化）"""
        if not html_content:
            return ""

        # コメントを除去（IE条件コメント以外）
        html_content = re.sub(
            r"<!--(?!\[if\s).*?-->", "", html_content, flags=re.DOTALL
        )

        # 連続する空白文字を単一の空白に置換
        html_content = re.sub(r"\s+", " ", html_content)

        # タグ間の空白を除去（ただしpreタグ内は除く）
        html_content = re.sub(r">\s+<", "><", html_content)

        # 行頭・行末の空白を除去
        html_content = html_content.strip()

        return html_content
