"""テキストパーサー"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from difflib import get_close_matches


@dataclass
class Node:
    """ASTノードの基底クラス"""
    type: str
    content: Any
    attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


class Parser:
    """テキストをASTに変換するパーサー"""
    
    # デフォルトのブロックマーカー定義
    DEFAULT_BLOCK_KEYWORDS = {
        "太字": {"tag": "strong"},
        "イタリック": {"tag": "em"},
        "枠線": {"tag": "div", "class": "box"},
        "ハイライト": {"tag": "div", "class": "highlight"},
        "見出し1": {"tag": "h1"},
        "見出し2": {"tag": "h2"},
        "見出し3": {"tag": "h3"},
        "見出し4": {"tag": "h4"},
        "見出し5": {"tag": "h5"},
        "折りたたみ": {"tag": "details", "summary": "詳細を表示"},
        "ネタバレ": {"tag": "details", "summary": "ネタバレを表示"},
        "コードブロック": {"tag": "pre", "class": "code-block"},
        "コード": {"tag": "code", "class": "inline-code"},
    }
    
    def __init__(self, config=None):
        self.lines = []
        self.current = 0
        self.errors = []
        self.heading_counter = 0  # 見出しID用のカウンター
        
        # 設定からマーカー定義を取得
        if config:
            self.BLOCK_KEYWORDS = config.get_markers()
        else:
            self.BLOCK_KEYWORDS = self.DEFAULT_BLOCK_KEYWORDS
    
    def parse(self, text: str) -> List[Node]:
        """メインパース処理"""
        self.lines = text.split('\n')
        self.current = 0
        self.errors = []
        
        nodes = []
        
        while self.current < len(self.lines):
            node = self._parse_line()
            if node:
                nodes.append(node)
        
        return nodes
    
    def _parse_line(self) -> Optional[Node]:
        """1行をパース"""
        if self.current >= len(self.lines):
            return None
            
        line = self.lines[self.current]
        
        # 空行チェック
        if not line.strip():
            self.current += 1
            return None
        
        # エスケープ処理（### で ;;; を表示）
        if line.strip().startswith("###"):
            escaped_line = line.replace("###", ";;;")
            self.current += 1
            return Node(type="p", content=[escaped_line])
        
        # コメント行チェック（# で始まる行は無視）
        if line.strip().startswith("#"):
            self.current += 1
            return None
        
        # ブロックマーカーのチェック
        if line.strip().startswith(";;;"):
            return self._parse_block_marker()
        
        # リストのチェック
        if line.strip().startswith("- "):
            return self._parse_list()
        
        # 番号付きリストのチェック（1. 2. 3. など）
        if re.match(r'^\s*\d+\.\s+', line):
            return self._parse_numbered_list()
        
        # 通常の段落
        return self._parse_paragraph()
    
    def _parse_block_marker(self) -> Optional[Node]:
        """ブロックマーカーをパース"""
        start_line = self.current
        marker_line = self.lines[self.current].strip()
        
        # 開始マーカーの解析
        if not marker_line.startswith(";;;"):
            return None
        
        # 目次マーカーのチェック（最優先）
        if marker_line == ";;;目次;;;":
            self.current += 1
            return Node(
                type="toc",
                content="",
                attributes={}
            )
        
        # 画像の単一行記法のチェック (;;;filename.ext;;;)
        if marker_line.endswith(";;;") and len(marker_line) > 6:
            content = marker_line[3:-3].strip()
            # 画像拡張子のパターン
            if re.match(r'^[^/\\]+\.(png|jpg|jpeg|gif|webp|svg)$', content, re.IGNORECASE):
                self.current += 1
                return Node(
                    type="image",
                    content=content,
                    attributes={"alt": content}
                )
            
            # 単一行ブロック記法のチェック (;;;キーワード;;;)
            # キーワードと属性の抽出
            keywords, attributes = self._parse_marker_keywords(content)
            
            if len(keywords) == 1:
                node = self._create_single_block(keywords[0], "", attributes)
                self.current += 1
                return node
            elif len(keywords) > 1:
                node = self._create_compound_block(keywords, "", attributes)
                self.current += 1
                return node
            else:
                self.current += 1
                return Node(
                    type="error",
                    content="",
                    attributes={"message": "キーワードが指定されていません"}
                )
        
        # キーワードと属性の抽出
        marker_content = marker_line[3:].strip()
        keywords, attributes = self._parse_marker_keywords(marker_content)
        
        # コンテンツの収集
        self.current += 1
        content_lines = []
        
        while self.current < len(self.lines):
            line = self.lines[self.current]
            if line.strip() == ";;;":
                self.current += 1
                break
            content_lines.append(line)
            self.current += 1
        else:
            # 閉じマーカーが見つからない
            error_node = Node(
                type="error",
                content="\n".join(content_lines),
                attributes={"message": f"閉じマーカー ';;;' が見つかりません（開始: ';;;{marker_content}'）", "line": start_line + 1}
            )
            return error_node
        
        content = "\n".join(content_lines)
        
        # ブロック内にリストが含まれているかチェック
        has_list = self._contains_list(content)
        if has_list:
            attributes["contains_list"] = True
            # print(f"DEBUG: Found list in block, content: {content[:50]}")
        
        # 複合キーワードの処理
        if len(keywords) > 1:
            return self._create_compound_block(keywords, content, attributes)
        elif len(keywords) == 1:
            return self._create_single_block(keywords[0], content, attributes)
        else:
            # キーワードなし
            return Node(
                type="error",
                content=content,
                attributes={"message": "キーワードが指定されていません", "line": start_line + 1}
            )
    
    def _contains_list(self, content: str) -> bool:
        """コンテンツにリスト項目が含まれているかチェック"""
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- ') or re.match(r'^\d+\.\s+', stripped):
                return True
        return False
    
    def _parse_marker_keywords(self, marker_content: str):
        """マーカーのキーワードと属性を解析"""
        # color=#hexのような属性を抽出
        attributes = {}
        color_match = re.search(r'color=(#[0-9a-fA-F]{3,6})', marker_content)
        if color_match:
            attributes["color"] = color_match.group(1)
            # color属性を削除するが、残りの部分は保持
            marker_content = marker_content[:color_match.start()] + marker_content[color_match.end():]
            marker_content = marker_content.strip()
        
        # キーワードを+または＋で分割
        keywords = re.split(r'[+＋]', marker_content)
        keywords = [k.strip() for k in keywords if k.strip()]
        
        return keywords, attributes
    
    def _create_single_block(self, keyword: str, content: str, attributes: dict) -> Node:
        """単一ブロックノードを作成"""
        if keyword not in self.BLOCK_KEYWORDS:
            # 類似するキーワードの候補を提案
            suggestions = self._get_keyword_suggestions(keyword)
            suggestion_text = ""
            if suggestions:
                suggestion_text = f" (候補: {', '.join(suggestions)})"
            
            return Node(
                type="error",
                content=content,
                attributes={"message": f"未知のキーワード: {keyword}{suggestion_text}"}
            )
        
        block_def = self.BLOCK_KEYWORDS[keyword]
        node_type = block_def["tag"]
        node_attrs = attributes.copy()
        
        if "class" in block_def:
            node_attrs["class"] = block_def["class"]
        
        # detailsタグの場合はsummary属性を設定
        if "summary" in block_def:
            node_attrs["summary"] = block_def["summary"]
        
        # 見出しの場合はIDを自動付与
        if node_type in ["h1", "h2", "h3", "h4", "h5"]:
            self.heading_counter += 1
            node_attrs["id"] = f"heading-{self.heading_counter}"
        
        # コンテンツを再帰的にパース（見出しは除く）
        if content.strip():
            if node_type in ["h1", "h2", "h3", "h4", "h5"]:
                # 見出しの場合はコンテンツをそのまま使用
                parsed_content = [content]
            else:
                # その他のブロックは再帰的にパース
                temp_parser = Parser()
                temp_parser.BLOCK_KEYWORDS = self.BLOCK_KEYWORDS
                parsed_content = temp_parser.parse(content)
        else:
            parsed_content = []
        
        return Node(type=node_type, content=parsed_content, attributes=node_attrs)
    
    def _create_compound_block(self, keywords: List[str], content: str, attributes: dict) -> Node:
        """複合ブロックノードを作成"""
        # 無効なキーワードのチェック
        invalid_keywords = [k for k in keywords if k not in self.BLOCK_KEYWORDS]
        if invalid_keywords:
            # 各無効キーワードに対して候補を提案
            error_messages = []
            for invalid_keyword in invalid_keywords:
                suggestions = self._get_keyword_suggestions(invalid_keyword)
                suggestion_text = ""
                if suggestions:
                    suggestion_text = f" (候補: {', '.join(suggestions)})"
                error_messages.append(f"{invalid_keyword}{suggestion_text}")
            
            return Node(
                type="error",
                content=content,
                attributes={"message": f"未知のキーワード: {', '.join(error_messages)}"}
            )
        
        # ネスト順序の決定（外側から内側へ）
        nesting_order = ["details", "div", "見出し", "strong", "em"]  # detailsを最外側に追加
        sorted_keywords = []
        
        for order_prefix in nesting_order:
            for keyword in keywords:
                if keyword.startswith(order_prefix) or (
                    order_prefix == "details" and keyword in ["折りたたみ", "ネタバレ"]
                ) or (
                    order_prefix == "div" and keyword in ["枠線", "ハイライト"]
                ) or (
                    order_prefix == "strong" and keyword == "太字"
                ) or (
                    order_prefix == "em" and keyword == "イタリック"
                ):
                    if keyword not in sorted_keywords:
                        sorted_keywords.append(keyword)
        
        # 最外側のキーワードを取得（最初にネストされるもの）
        outermost_keyword = sorted_keywords[-1] if sorted_keywords else None
        outermost_tag = self.BLOCK_KEYWORDS.get(outermost_keyword, {}).get("tag", "") if outermost_keyword else ""
        
        # コンテンツを再帰的にパース（最外側が見出しの場合は除く）
        if content.strip():
            if outermost_tag in ["h1", "h2", "h3", "h4", "h5"]:
                # 最外側が見出しの場合はコンテンツをそのまま使用
                parsed_content = [content]
            else:
                # その他の場合は再帰的にパース
                temp_parser = Parser()
                temp_parser.BLOCK_KEYWORDS = self.BLOCK_KEYWORDS
                parsed_content = temp_parser.parse(content)
        else:
            parsed_content = []
        
        # 内側から外側へ向かってネスト
        for keyword in reversed(sorted_keywords):
            block_def = self.BLOCK_KEYWORDS[keyword]
            
            node_attrs = {}
            # 属性は一番内側のハイライト要素に適用
            if keyword == "ハイライト" and attributes:
                node_attrs.update(attributes)
            
            if "class" in block_def:
                node_attrs["class"] = block_def["class"]
            
            # detailsタグの場合はsummary属性を設定
            if "summary" in block_def:
                node_attrs["summary"] = block_def["summary"]
            
            # 見出しの場合はIDを自動付与
            if block_def["tag"] in ["h1", "h2", "h3", "h4", "h5"]:
                self.heading_counter += 1
                node_attrs["id"] = f"heading-{self.heading_counter}"
            
            parsed_content = [Node(
                type=block_def["tag"],
                content=parsed_content,
                attributes=node_attrs
            )]
        
        return parsed_content[0] if parsed_content else None
    
    def _get_keyword_suggestions(self, invalid_keyword: str, max_suggestions: int = 3) -> List[str]:
        """無効なキーワードに対して類似するキーワードの候補を提案"""
        # 編集距離に基づく類似度で候補を検索
        valid_keywords = list(self.BLOCK_KEYWORDS.keys())
        suggestions = get_close_matches(
            invalid_keyword, 
            valid_keywords, 
            n=max_suggestions,
            cutoff=0.4  # 40%以上の類似度を要求
        )
        return suggestions
    
    def _parse_list(self) -> Node:
        """リストをパース（キーワード付きリストも含む）"""
        items = []
        
        while self.current < len(self.lines):
            line = self.lines[self.current]
            if not line.strip().startswith("- "):
                break
            
            item_content = line.strip()[2:]  # "- "を削除
            
            # キーワード付きリストのチェック（;;;キーワード;;; テキスト形式）
            keyword_match = re.match(r'^;;;([^;]+);;;\s*(.*)$', item_content)
            if keyword_match:
                keywords_str = keyword_match.group(1)
                text_content = keyword_match.group(2)
                
                # キーワードと属性を解析
                keywords, attributes = self._parse_marker_keywords(keywords_str)
                
                if len(keywords) > 1:
                    # 複合キーワード
                    node = self._create_compound_block(keywords, text_content, attributes)
                    items.append(Node(type="li", content=[node]))
                elif len(keywords) == 1:
                    # 単一キーワード
                    node = self._create_single_block(keywords[0], text_content, attributes)
                    items.append(Node(type="li", content=[node]))
                else:
                    # キーワードなし（エラー）
                    error_node = Node(
                        type="error",
                        content=text_content,
                        attributes={"message": "キーワードが指定されていません"}
                    )
                    items.append(Node(type="li", content=[error_node]))
            else:
                # 通常のリスト項目
                items.append(Node(type="li", content=[item_content]))
            
            self.current += 1
        
        return Node(type="ul", content=items)
    
    def _parse_numbered_list(self) -> Node:
        """番号付きリストをパース"""
        items = []
        
        while self.current < len(self.lines):
            line = self.lines[self.current]
            # 番号付きリストの行かチェック
            match = re.match(r'^\s*\d+\.\s+(.*)$', line)
            if not match:
                break
            
            item_content = match.group(1).strip()
            items.append(Node(type="li", content=[item_content]))
            self.current += 1
        
        return Node(type="ol", content=items)
    
    def _parse_paragraph(self) -> Node:
        """段落をパース（連続する行をまとめて1段落として処理）"""
        lines = []
        
        while self.current < len(self.lines):
            line = self.lines[self.current]
            
            # 空行またはマーカーの開始で段落終了
            if not line.strip() or line.strip().startswith(";;;") or line.strip().startswith("- ") or re.match(r'^\s*\d+\.\s+', line):
                break
            
            lines.append(line.strip())
            self.current += 1
        
        # 連続する行を<br>タグで結合
        content = "<br>".join(lines)
        parsed_content = [content]
        
        return Node(type="p", content=parsed_content)
    


def parse(text: str, config=None) -> List[Node]:
    """テキストをパースしてAST（抽象構文木）を返す"""
    parser = Parser(config)
    return parser.parse(text)