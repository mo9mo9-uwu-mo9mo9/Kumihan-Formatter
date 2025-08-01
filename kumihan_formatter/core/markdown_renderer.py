"""
マークダウン レンダラー

HTML生成・段落変換・テンプレート機能
Issue #492 Phase 5A - markdown_converter.py分割
"""

from datetime import datetime
from typing import Any, Optional


class MarkdownRenderer:
    """Markdown rendering functionality

    Handles HTML generation, paragraph creation,
    and full HTML template rendering.
    """

    def __init__(self) -> None:
        """Initialize renderer"""
        pass

    def _extract_title_from_content(
        self, content: str, patterns: dict[str, Any]
    ) -> Optional[str]:
        """コンテンツから最初のH1見出しを抽出"""
        match = patterns["h1"].search(content)
        return match.group(1).strip() if match else None

    def _convert_paragraphs(self, text: str) -> str:
        """段落を作成"""
        lines = text.split("\n")
        result = []
        current_paragraph: list[str] = []

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
                    para_text = "<br>\n".join(current_paragraph).strip()
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
                        para_text = "<br>\n".join(current_paragraph).strip()
                        if para_text:
                            result.append(f"<p>{para_text}</p>")
                        current_paragraph = []

        # 最後の段落を処理
        if current_paragraph:
            para_text = "<br>\n".join(current_paragraph).strip()
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
