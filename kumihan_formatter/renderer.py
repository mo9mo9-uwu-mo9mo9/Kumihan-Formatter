"""HTMLレンダラー"""

import re
from pathlib import Path
from typing import List, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .parser import Node


class Renderer:
    """ASTをHTMLに変換するレンダラー"""
    
    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
    def render(self, ast: List[Node], config=None) -> str:
        """ASTをHTMLに変換"""
        # 見出しノードを収集
        headings = self._collect_headings(ast)
        
        # 目次が必要かチェック
        has_toc = any(node.type == "toc" for node in ast)
        
        # ASTをHTMLに変換（目次マーカーは除去）
        filtered_ast = [node for node in ast if node.type != "toc"]
        body_content = self._render_nodes(filtered_ast)
        
        # 目次HTMLを生成
        toc_html = ""
        if has_toc:
            toc_html = self._generate_toc_html(headings)
        
        # テンプレートを使用してHTMLを生成
        template = self.env.get_template("base.html.j2")
        
        # 設定からCSS変数を取得
        css_vars = {}
        theme_name = "デフォルト"
        if config:
            css_vars = config.get_css_variables()
            theme_name = config.get_theme_name()
        
        return template.render(
            title="組版結果",
            body_content=body_content,
            css_vars=css_vars,
            theme_name=theme_name,
            has_toc=has_toc,
            toc_html=toc_html
        )
    
    def _render_nodes(self, nodes: List[Node]) -> str:
        """ノードリストをHTMLに変換"""
        html_parts = []
        
        for node in nodes:
            html = self._render_node(node)
            if html:
                html_parts.append(html)
        
        return "\n".join(html_parts)
    
    def _render_node(self, node: Node) -> str:
        """単一ノードをHTMLに変換"""
        if node.type == "error":
            return self._render_error(node)
        
        # 画像ノードの特別処理
        if node.type == "image":
            return self._render_image(node)
        
        # ブロック内リストの特別処理
        if node.attributes and node.attributes.get("contains_list"):
            return self._render_block_with_list(node)
        
        # タグの生成
        tag = node.type
        attributes = self._format_attributes(node.attributes)
        
        # コンテンツのレンダリング
        content = self._render_content(node.content)
        
        # 自己完結型タグのチェック
        if tag in ["br", "hr", "img"]:
            return f"<{tag}{attributes} />"
        
        return f"<{tag}{attributes}>{content}</{tag}>"
    
    def _render_image(self, node: Node) -> str:
        """画像ノードをHTMLに変換"""
        filename = node.content
        alt_text = node.attributes.get("alt", filename)
        
        # 画像ファイルパスは images/filename に固定
        img_path = f"images/{filename}"
        
        return f'<img src="{img_path}" alt="{alt_text}" />'
    
    def _render_error(self, node: Node) -> str:
        """エラーノードをHTMLに変換"""
        message = node.attributes.get("message", "不明なエラー")
        line = node.attributes.get("line", "")
        
        error_text = f"[ERROR: {message}]"
        if line:
            error_text += f" (行: {line})"
        
        content = self._render_content(node.content)
        
        return f'<div style="background-color:#ffe6e6; padding: 10px; margin: 5px 0;">{error_text}\n{content}</div>'
    
    def _render_block_with_list(self, node: Node) -> str:
        """ブロック内にリストが含まれる場合の特別レンダリング"""
        # ブロックタグ情報を取得
        tag = node.type
        attributes = self._format_attributes(node.attributes, exclude_keys=['contains_list'])
        
        # デバッグ用：ブロック内リスト処理が呼ばれていることを確認
        # print(f"DEBUG: Block with list - tag: {tag}, content: {node.content[:50]}")
        
        # コンテンツをリスト形式でレンダリング
        content = self._render_list_content(node.content)
        
        return f"<{tag}{attributes}>{content}</{tag}>"
    
    def _render_list_content(self, content) -> str:
        """ブロック内のコンテンツをリスト形式でレンダリング"""
        # コンテンツがリストの場合、最初の要素を文字列として取得
        if isinstance(content, list) and len(content) > 0:
            content_str = content[0]
            if isinstance(content_str, str):
                content = content_str
            else:
                # Nodeオブジェクトの場合は通常のレンダリングに委譲
                return self._render_content(content)
        
        # コンテンツが文字列でない場合は通常のレンダリングに委譲
        if not isinstance(content, str):
            return self._render_content(content)
            
        lines = content.split('\n')
        list_items = []
        non_list_content = []
        result_parts = []
        
        current_list_type = None
        bullet_items = []
        numbered_items = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- '):
                # 箇条書きリスト項目
                if current_list_type == 'numbered':
                    # 番号付きリストから箇条書きリストに切り替わった
                    if numbered_items:
                        list_html = f"<ol>{''.join(numbered_items)}</ol>"
                        result_parts.append(list_html)
                        numbered_items = []
                
                current_list_type = 'bullet'
                item_content = stripped[2:].strip()  # '- 'を除去
                bullet_items.append(f"<li>{item_content}</li>")
            elif re.match(r'^\d+\.\s+', stripped):
                # 番号付きリスト項目
                if current_list_type == 'bullet':
                    # 箇条書きリストから番号付きリストに切り替わった
                    if bullet_items:
                        list_html = f"<ul>{''.join(bullet_items)}</ul>"
                        result_parts.append(list_html)
                        bullet_items = []
                
                current_list_type = 'numbered'
                match = re.match(r'^\d+\.\s+(.*)$', stripped)
                if match:
                    item_content = match.group(1).strip()
                    numbered_items.append(f"<li>{item_content}</li>")
            elif stripped:
                # 非リスト内容 - 現在のリストを閉じる
                if current_list_type == 'bullet' and bullet_items:
                    list_html = f"<ul>{''.join(bullet_items)}</ul>"
                    result_parts.append(list_html)
                    bullet_items = []
                elif current_list_type == 'numbered' and numbered_items:
                    list_html = f"<ol>{''.join(numbered_items)}</ol>"
                    result_parts.append(list_html)
                    numbered_items = []
                
                current_list_type = None
                non_list_content.append(stripped)
        
        # 最後に残ったリストがあれば追加
        if current_list_type == 'bullet' and bullet_items:
            list_html = f"<ul>{''.join(bullet_items)}</ul>"
            result_parts.append(list_html)
        elif current_list_type == 'numbered' and numbered_items:
            list_html = f"<ol>{''.join(numbered_items)}</ol>"
            result_parts.append(list_html)
        
        # 非リスト内容があれば追加
        if non_list_content:
            result_parts.append('\n'.join(non_list_content))
        
        return '\n'.join(result_parts)
    
    def _render_content(self, content: Any) -> str:
        """コンテンツをHTMLに変換"""
        if isinstance(content, str):
            return content
        
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, Node):
                    parts.append(self._render_node(item))
                else:
                    parts.append(str(item))
            return "".join(parts)
        
        if isinstance(content, Node):
            return self._render_node(content)
        
        return str(content)
    
    def _format_attributes(self, attributes: dict, exclude_keys: list = None) -> str:
        """属性を HTML 属性文字列に変換"""
        if not attributes:
            return ""
        
        if exclude_keys is None:
            exclude_keys = []
        
        attr_parts = []
        
        for key, value in attributes.items():
            if key in exclude_keys:
                continue
                
            if key == "color" and "style" not in attributes:
                # color属性をstyle属性に変換
                attr_parts.append(f'style="background-color:{value}"')
            elif key == "class":
                attr_parts.append(f'class="{value}"')
            elif key == "style":
                attr_parts.append(f'style="{value}"')
            elif key == "id":
                attr_parts.append(f'id="{value}"')
        
        return " " + " ".join(attr_parts) if attr_parts else ""
    
    def _collect_headings(self, nodes: List[Node], collected=None) -> List[dict]:
        """ASTから見出しノードを収集"""
        if collected is None:
            collected = []
        
        for node in nodes:
            if node.type in ["h1", "h2", "h3", "h4", "h5"]:
                # テキスト内容を抽出
                text_content = self._extract_text_content(node.content)
                collected.append({
                    "level": int(node.type[1]),  # h1 -> 1, h2 -> 2, etc.
                    "text": text_content,
                    "id": node.attributes.get("id", "")
                })
            
            # ネストされたコンテンツも検索
            if isinstance(node.content, list):
                for item in node.content:
                    if isinstance(item, Node):
                        self._collect_headings([item], collected)
        
        return collected
    
    def _extract_text_content(self, content: Any) -> str:
        """コンテンツからテキストのみを抽出"""
        if isinstance(content, str):
            return content
        
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, Node):
                    parts.append(self._extract_text_content(item.content))
            return "".join(parts)
        
        if isinstance(content, Node):
            return self._extract_text_content(content.content)
        
        return str(content)
    
    def _generate_toc_html(self, headings: List[dict]) -> str:
        """見出しリストから目次HTMLを生成"""
        if not headings:
            return '<ul class="toc-list"></ul>'
        
        toc_lines = ['<ul class="toc-list">']
        current_level = 0
        
        for heading in headings:
            level = heading["level"]
            
            # レベル調整
            while current_level < level:
                toc_lines.append('<ul>')
                current_level += 1
            
            while current_level > level:
                toc_lines.append('</ul>')
                current_level -= 1
            
            # リスト項目追加
            toc_lines.append(
                f'<li><a href="#{heading["id"]}">{heading["text"]}</a></li>'
            )
        
        # 残りのリストを閉じる
        while current_level > 0:
            toc_lines.append('</ul>')
            current_level -= 1
        
        toc_lines.append('</ul>')
        
        return '\n'.join(toc_lines)


def render(ast: List[Node], config=None) -> str:
    """ASTをHTMLに変換する"""
    renderer = Renderer()
    return renderer.render(ast, config)