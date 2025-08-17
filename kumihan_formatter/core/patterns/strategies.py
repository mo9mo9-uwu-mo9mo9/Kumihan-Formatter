"""Strategy実装例"""

import re
from typing import Any, Dict

from .strategy import ParsingStrategy, RenderingStrategy


class KumihanParsingStrategy(ParsingStrategy):
    """Kumihan記法パーシング戦略"""

    def parse(self, content: str, context: Dict[str, Any]) -> Any:
        # Kumihan記法の基本パターン
        pattern = r"# (\w+) #([^#]+)##"
        matches = re.findall(pattern, content)

        blocks = []
        for decoration, text in matches:
            blocks.append(
                {
                    "type": "kumihan_block",
                    "decoration": decoration,
                    "content": text.strip(),
                }
            )

        return {
            "blocks": blocks,
            "total_blocks": len(blocks),
            "strategy": self.get_strategy_name(),
        }

    def get_strategy_name(self) -> str:
        return "kumihan_parsing"

    def supports_content(self, content: str) -> float:
        # Kumihan記法パターンの検出
        pattern = r"# \w+ #[^#]+##"
        matches = re.findall(pattern, content)
        total_lines = len(content.split("\n"))

        if total_lines == 0:
            return 0.0

        # マッチ率を返す
        return min(len(matches) / max(total_lines, 1), 1.0)


class HTMLRenderingStrategy(RenderingStrategy):
    """HTMLレンダリング戦略"""

    def render(self, data: Any, context: Dict[str, Any]) -> str:
        if not isinstance(data, dict) or "blocks" not in data:
            return ""

        html_parts = ["<!DOCTYPE html>", "<html>", "<body>"]

        for block in data["blocks"]:
            if block["type"] == "kumihan_block":
                decoration = block["decoration"]
                content = block["content"]

                if decoration == "太字":
                    html_parts.append(f"<strong>{content}</strong>")
                elif decoration == "イタリック":
                    html_parts.append(f"<em>{content}</em>")
                elif decoration == "見出し":
                    html_parts.append(f"<h2>{content}</h2>")
                else:
                    html_parts.append(f"<span class='{decoration}'>{content}</span>")

        html_parts.extend(["</body>", "</html>"])
        return "\n".join(html_parts)

    def get_strategy_name(self) -> str:
        return "html_rendering"

    def supports_format(self, output_format: str) -> bool:
        return output_format.lower() in ["html", "htm"]
