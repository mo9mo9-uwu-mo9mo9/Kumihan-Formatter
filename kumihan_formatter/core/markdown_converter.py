"""Simple Markdown to HTML Converter

シンプルなMarkdown→HTML変換機能
Issue #118対応: エンドユーザー向け文書の読みやすさ向上
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Tuple


class SimpleMarkdownConverter:
    """シンプルなMarkdown→HTML変換器

    基本的なMarkdown記法のみサポート:
    - 見出し (# ## ###)
    - リスト (- * +, 1. 2. 3.)
    - リンク [text](url)
    - 強調 **bold** *italic*
    - コードブロック ```
    - 水平線 ---
    """

    def __init__(self) -> None:
        """変換器を初期化"""
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, Pattern[str]]:
        """正規表現パターンをコンパイル"""
        return {
            # 見出し
            "h1": re.compile(r"^# (.+)$", re.MULTILINE),
            "h2": re.compile(r"^## (.+)$", re.MULTILINE),
            "h3": re.compile(r"^### (.+)$", re.MULTILINE),
            "h4": re.compile(r"^#### (.+)$", re.MULTILINE),
            "h5": re.compile(r"^##### (.+)$", re.MULTILINE),
            "h6": re.compile(r"^###### (.+)$", re.MULTILINE),
            # 強調
            "strong": re.compile(r"\*\*(.+?)\*\*"),
            "em": re.compile(r"\*(.+?)\*"),
            "strong_alt": re.compile(r"__(.+?)__"),
            "em_alt": re.compile(r"_(.+?)_"),
            # リンク
            "link": re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),
            # コード（インライン）
            "code": re.compile(r"`([^`]+)`"),
            # 水平線
            "hr": re.compile(r"^---+$", re.MULTILINE),
            # 番号付きリスト
            "ol_item": re.compile(r"^\d+\.\s+(.+)$", re.MULTILINE),
            # 番号なしリスト
            "ul_item": re.compile(r"^[-*+]\s+(.+)$", re.MULTILINE),
        }

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
        text = markdown_text.replace("\r\n", "\n").replace("\r", "\n")

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

    def _extract_title_from_content(self, content: str) -> Optional[str]:
        """コンテンツから最初のH1見出しを抽出"""
        match = self.patterns["h1"].search(content)
        return match.group(1).strip() if match else None

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

    def _convert_headings(self, text: str) -> str:
        """見出しを変換"""
        for level in range(1, 7):  # h1からh6まで
            pattern_name = f"h{level}"
            if pattern_name in self.patterns:

                def make_heading_replacer(h_level: int) -> Any:
                    def replace_heading(match: Any) -> str:
                        heading_text = match.group(1).strip()
                        # ID生成（リンク用）
                        heading_id = self._generate_heading_id(heading_text)
                        return (
                            f'<h{h_level} id="{heading_id}">{heading_text}</h{h_level}>'
                        )

                    return replace_heading

                text = self.patterns[pattern_name].sub(
                    make_heading_replacer(level), text
                )
        return text

    def _generate_heading_id(self, heading_text: str) -> str:
        """見出しからIDを生成"""
        # 英数字以外を除去してIDを生成
        clean_text = re.sub(r"[^\w\s-]", "", heading_text.lower())
        clean_text = re.sub(r"[-\s]+", "-", clean_text)
        return clean_text.strip("-")

    def _convert_lists(self, text: str) -> str:
        """リストを変換"""
        lines = text.split("\n")
        result = []
        in_ul = False
        in_ol = False

        for line in lines:
            ul_match = self.patterns["ul_item"].match(line)
            ol_match = self.patterns["ol_item"].match(line)

            if ul_match:
                if not in_ul:
                    if in_ol:
                        result.append("</ol>")
                        in_ol = False
                    result.append("<ul>")
                    in_ul = True
                result.append(f"<li>{ul_match.group(1)}</li>")
            elif ol_match:
                if not in_ol:
                    if in_ul:
                        result.append("</ul>")
                        in_ul = False
                    result.append("<ol>")
                    in_ol = True
                result.append(f"<li>{ol_match.group(1)}</li>")
            else:
                if in_ul:
                    result.append("</ul>")
                    in_ul = False
                if in_ol:
                    result.append("</ol>")
                    in_ol = False
                result.append(line)

        # 最後のリストを閉じる
        if in_ul:
            result.append("</ul>")
        if in_ol:
            result.append("</ol>")

        return "\n".join(result)

    def _convert_inline_elements(self, text: str) -> str:
        """インライン要素を変換"""
        # リンク
        text = self.patterns["link"].sub(r'<a href="\2">\1</a>', text)

        # 強調（太字）
        text = self.patterns["strong"].sub(r"<strong>\1</strong>", text)
        text = self.patterns["strong_alt"].sub(r"<strong>\1</strong>", text)

        # 強調（イタリック）
        text = self.patterns["em"].sub(r"<em>\1</em>", text)
        text = self.patterns["em_alt"].sub(r"<em>\1</em>", text)

        # インラインコード
        text = self.patterns["code"].sub(r"<code>\1</code>", text)

        # 水平線
        text = self.patterns["hr"].sub("<hr>", text)

        return text

    def _convert_paragraphs(self, text: str) -> str:
        """段落を作成"""
        lines = text.split("\n")
        result = []
        current_paragraph: List[str] = []

        for line in lines:
            line = line.strip()

            # HTMLタグが含まれる行はそのまま追加
            if (
                line.startswith("<")
                or line == ""
                or line.startswith("---")
                or "</pre>" in line
                or "<pre>" in line
            ):

                # 現在の段落を終了
                if current_paragraph:
                    para_text = " ".join(current_paragraph).strip()
                    if para_text:
                        result.append(f"<p>{para_text}</p>")
                    current_paragraph = []

                # HTMLタグの行をそのまま追加
                if line:
                    result.append(line)
            else:
                # 通常のテキスト行
                if line:
                    current_paragraph.append(line)
                else:
                    # 空行で段落を区切る
                    if current_paragraph:
                        para_text = " ".join(current_paragraph).strip()
                        if para_text:
                            result.append(f"<p>{para_text}</p>")
                        current_paragraph = []

        # 最後の段落を処理
        if current_paragraph:
            para_text = " ".join(current_paragraph).strip()
            if para_text:
                result.append(f"<p>{para_text}</p>")

        return "\n".join(result)

    def _create_full_html(self, title: str, content: str, source_filename: str) -> str:
        """完全なHTMLページを作成"""
        generation_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Kumihan-Formatter</title>
    <style>
        body {{
            font-family: 'Hiragino Kaku Gothic Pro', 'ヒラギノ角ゴ Pro', 'Yu Gothic', 'メイリオ', Meiryo, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fafafa;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #333;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        h1 {{
            border-bottom: 3px solid #4a90e2;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }}
        ul, ol {{
            margin-left: 1.5em;
        }}
        li {{
            margin-bottom: 0.5em;
        }}
        code {{
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #4a90e2;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        a {{
            color: #4a90e2;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .document-info {{
            margin-top: 2em;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            color: #666;
            font-size: 0.9em;
            border-left: 4px solid #28a745;
        }}
        hr {{
            border: none;
            border-top: 2px solid #ddd;
            margin: 2em 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}

        <div class="document-info">
            <strong>📄 文書情報</strong><br>
            元ファイル: {source_filename}<br>
            変換日時: {generation_time}<br>
            変換ツール: Kumihan-Formatter
        </div>
    </div>
</body>
</html>"""
        return html_template


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
