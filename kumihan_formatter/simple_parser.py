"""
シンプルKumihanパーサー - 緊急復旧版
基本的なKumihan記法を最小限実装で解析
"""

import re
import logging
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ParsedElement:
    """解析済み要素"""

    type: str
    content: str
    attributes: Dict[str, str]
    children: List["ParsedElement"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "attributes": self.attributes,
            "children": [child.to_dict() for child in self.children],
        }


class SimpleKumihanParser:
    """シンプルKumihanパーサー"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 基本パターン定義
        self.patterns = {
            # # 装飾名 #内容##
            "decorated_block": re.compile(r"#\s*([^#]+?)\s*#([^#]+?)##"),
            # 見出し
            "heading": re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE),
            # リスト
            "list_item": re.compile(r"^\s*[-*+]\s+(.+)$", re.MULTILINE),
            # 番号付きリスト
            "numbered_list": re.compile(r"^\s*\d+\.\s+(.+)$", re.MULTILINE),
            # 強調
            "bold": re.compile(r"\*\*(.+?)\*\*"),
            "italic": re.compile(r"\*(.+?)\*"),
        }

    def parse(self, text: str) -> Dict[str, Any]:
        """テキストを解析してパース結果を返す"""
        try:
            elements = []

            # Kumihan装飾ブロックの解析
            decorated_matches = list(self.patterns["decorated_block"].finditer(text))
            if decorated_matches:
                for match in decorated_matches:
                    decoration = match.group(1).strip()
                    content = match.group(2).strip()

                    element = ParsedElement(
                        type="kumihan_block",
                        content=content,
                        attributes={"decoration": decoration},
                        children=[],
                    )
                    elements.append(element)

            # 見出しの解析
            for match in self.patterns["heading"].finditer(text):
                level = len(match.group(1))
                title = match.group(2).strip()

                element = ParsedElement(
                    type=f"heading_{level}",
                    content=title,
                    attributes={"level": str(level)},
                    children=[],
                )
                elements.append(element)

            # 基本的なマークダウン要素
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # リストアイテム
                if self.patterns["list_item"].match(line):
                    match = self.patterns["list_item"].match(line)
                    if match:
                        element = ParsedElement(
                            type="list_item",
                            content=match.group(1).strip(),
                            attributes={"list_type": "unordered"},
                            children=[],
                        )
                        elements.append(element)

                # 番号付きリスト
                elif self.patterns["numbered_list"].match(line):
                    match = self.patterns["numbered_list"].match(line)
                    if match:
                        element = ParsedElement(
                            type="list_item",
                            content=match.group(1).strip(),
                            attributes={"list_type": "ordered"},
                            children=[],
                        )
                        elements.append(element)

                # 通常のテキスト
                elif not any(
                    pattern.search(line)
                    for pattern in [
                        self.patterns["decorated_block"],
                        self.patterns["heading"],
                    ]
                ):
                    # 強調の処理
                    processed_content = self._process_inline_formatting(line)
                    element = ParsedElement(
                        type="paragraph",
                        content=processed_content,
                        attributes={},
                        children=[],
                    )
                    elements.append(element)

            return {
                "status": "success",
                "elements": [elem.to_dict() for elem in elements],
                "parser": "SimpleKumihanParser",
                "total_elements": len(elements),
            }

        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "elements": [],
                "parser": "SimpleKumihanParser",
            }

    def _process_inline_formatting(self, text: str) -> str:
        """インライン装飾の処理"""
        # 太字
        text = self.patterns["bold"].sub(r"<strong>\1</strong>", text)
        # イタリック
        text = self.patterns["italic"].sub(r"<em>\1</em>", text)
        return text

    def validate(self, text: str) -> List[str]:
        """基本的な構文検証"""
        errors = []

        # Kumihan記法の基本構文チェック
        decorated_blocks = self.patterns["decorated_block"].findall(text)
        for decoration, content in decorated_blocks:
            if not decoration.strip():
                errors.append("装飾名が空です")
            if not content.strip():
                errors.append("内容が空です")

        return errors
