#!/usr/bin/env python3
"""
Kumihan記法自動抽出ツール

parser.pyの実装から対応記法を自動抽出し、
ドキュメント用のマークダウンテーブルを生成する。

実装とドキュメントの乖離を防ぐためのツール。
"""

import sys
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kumihan_formatter.parser import Parser


class SyntaxExtractor:
    """記法自動抽出クラス"""
    
    def __init__(self):
        self.parser = Parser()
        self.extracted_syntax = {}
        
    def extract_block_keywords(self) -> Dict[str, dict]:
        """ブロックキーワード定義を抽出"""
        return self.parser.DEFAULT_BLOCK_KEYWORDS.copy()
    
    def extract_special_syntax(self) -> List[dict]:
        """特別な記法を抽出（画像、目次、エスケープ等）"""
        special_syntax = []
        
        # 目次記法
        special_syntax.append({
            "syntax": ";;;目次;;;",
            "description": "目次マーカー（見出しが2つ以上あると自動生成）",
            "output": "自動生成される目次",
            "category": "自動生成"
        })
        
        # 画像記法
        special_syntax.append({
            "syntax": ";;;filename.ext;;;",
            "description": "画像埋め込み（対応拡張子: png, jpg, jpeg, gif, webp, svg）",
            "output": '<img src="images/filename.ext" alt="filename.ext" />',
            "category": "メディア"
        })
        
        # エスケープ記法
        special_syntax.append({
            "syntax": "###",
            "description": "行頭の ### は ;;; に変換される（エスケープ記法）",
            "output": ";;; として表示",
            "category": "エスケープ"
        })
        
        # リスト記法
        special_syntax.append({
            "syntax": "- 項目",
            "description": "箇条書きリスト",
            "output": "<ul><li>項目</li></ul>",
            "category": "リスト"
        })
        
        special_syntax.append({
            "syntax": "1. 項目",
            "description": "番号付きリスト",
            "output": "<ol><li>項目</li></ol>",
            "category": "リスト"
        })
        
        # キーワード付きリスト記法
        special_syntax.append({
            "syntax": "- ;;;キーワード;;; テキスト",
            "description": "キーワード付きリスト項目",
            "output": "<ul><li><keyword-tag>テキスト</keyword-tag></li></ul>",
            "category": "リスト"
        })
        
        return special_syntax
    
    def extract_compound_syntax(self) -> List[dict]:
        """複合記法を抽出"""
        compound_syntax = []
        
        # 複合キーワード記法
        compound_syntax.append({
            "syntax": ";;;キーワード1+キーワード2;;;",
            "description": "複合キーワード（+ または ＋ で連結）",
            "output": "ネストしたHTMLタグ",
            "category": "複合記法",
            "example": ";;;太字+枠線\n内容\n;;;"
        })
        
        # 色付きハイライト記法
        compound_syntax.append({
            "syntax": ";;;ハイライト color=#hex;;;",
            "description": "色指定付きハイライト",
            "output": '<div class="highlight" style="background-color:#hex">',
            "category": "複合記法",
            "example": ";;;ハイライト color=#ffe6e6\n内容\n;;;"
        })
        
        return compound_syntax
    
    def generate_markdown_table(self, title: str, data: List[dict], columns: List[str]) -> str:
        """マークダウンテーブルを生成"""
        lines = [f"## {title}", ""]
        
        # ヘッダー行
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join("---" for _ in columns) + " |"
        lines.extend([header, separator])
        
        # データ行
        for item in data:
            row_values = []
            for col in columns:
                value = item.get(col.lower().replace(" ", "_"), "")
                # マークダウンでのエスケープ
                if isinstance(value, str):
                    value = value.replace("|", "\\|")
                row_values.append(str(value))
            
            row = "| " + " | ".join(row_values) + " |"
            lines.append(row)
        
        lines.append("")  # 空行
        return "\n".join(lines)
    
    def generate_block_keywords_table(self) -> str:
        """ブロックキーワードテーブルを生成"""
        block_keywords = self.extract_block_keywords()
        
        table_data = []
        for keyword, definition in block_keywords.items():
            tag = definition["tag"]
            css_class = definition.get("class", "")
            
            # 使用例を生成
            example = f";;;{keyword}\\n内容\\n;;;"
            
            # 出力HTMLを生成
            if css_class:
                output = f'<{tag} class="{css_class}">内容</{tag}>'
            else:
                output = f'<{tag}>内容</{tag}>'
            
            table_data.append({
                "kumihan記法": f"`{example}`",
                "説明": keyword,
                "出力html": f"`{output}`",
                "カテゴリ": "基本記法"
            })
        
        return self.generate_markdown_table(
            "基本ブロック記法",
            table_data,
            ["Kumihan記法", "説明", "出力HTML", "カテゴリ"]
        )
    
    def generate_special_syntax_table(self) -> str:
        """特別記法テーブルを生成"""
        special_syntax = self.extract_special_syntax()
        
        table_data = []
        for syntax in special_syntax:
            table_data.append({
                "kumihan記法": f"`{syntax['syntax']}`",
                "説明": syntax["description"],
                "出力html": f"`{syntax['output']}`",
                "カテゴリ": syntax["category"]
            })
        
        return self.generate_markdown_table(
            "特別記法",
            table_data,
            ["Kumihan記法", "説明", "出力HTML", "カテゴリ"]
        )
    
    def generate_compound_syntax_table(self) -> str:
        """複合記法テーブルを生成"""
        compound_syntax = self.extract_compound_syntax()
        
        table_data = []
        for syntax in compound_syntax:
            example = syntax.get("example", syntax["syntax"])
            table_data.append({
                "kumihan記法": f"`{example}`",
                "説明": syntax["description"],
                "出力html": f"`{syntax['output']}`",
                "カテゴリ": syntax["category"]
            })
        
        return self.generate_markdown_table(
            "複合記法",
            table_data,
            ["Kumihan記法", "説明", "出力HTML", "カテゴリ"]
        )
    
    def generate_full_syntax_reference(self) -> str:
        """完全な記法リファレンスを生成"""
        content = [
            "# Kumihan記法 完全リファレンス",
            "",
            "> **自動生成**：このドキュメントは `dev/tools/extract_syntax.py` により",
            "> `kumihan_formatter/parser.py` の実装から自動生成されています。",
            "> 手動編集せず、実装変更時に自動更新してください。",
            "",
            f"**生成日時**：{self._get_current_datetime()}",
            "",
            "---",
            "",
        ]
        
        # 各テーブルを追加
        content.append(self.generate_block_keywords_table())
        content.append(self.generate_special_syntax_table())
        content.append(self.generate_compound_syntax_table())
        
        # ネスト順序の説明
        content.extend([
            "## ネスト順序ルール",
            "",
            "複合キーワードは以下の順序で外側から内側にネストされます：",
            "",
            "1. **div系**（`枠線`, `ハイライト`） - 最外側",
            "2. **見出し**（`見出し1`〜`見出し5`）", 
            "3. **太字**（`太字`）",
            "4. **イタリック**（`イタリック`） - 最内側",
            "",
            "**例**：`;;;見出し2+太字+ハイライト color=#ffe6e6;;;`",
            "```html",
            '<div class="highlight" style="background-color:#ffe6e6">',
            "  <h2><strong>内容</strong></h2>",
            "</div>",
            "```",
            "",
        ])
        
        return "\n".join(content)
    
    def _get_current_datetime(self) -> str:
        """現在日時を取得"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def save_syntax_reference(self, output_path: Path) -> None:
        """記法リファレンスをファイルに保存"""
        content = self.generate_full_syntax_reference()
        output_path.write_text(content, encoding="utf-8")
        print(f"✅ 記法リファレンスを生成しました: {output_path}")
    
    def compare_with_existing_docs(self, docs_dir: Path) -> Dict[str, List[str]]:
        """既存ドキュメントとの差異を確認"""
        differences = {}
        
        # SYNTAX_REFERENCE.mdとの比較
        syntax_ref_path = docs_dir / "SYNTAX_REFERENCE.md"
        if syntax_ref_path.exists():
            current_content = syntax_ref_path.read_text(encoding="utf-8")
            generated_content = self.generate_full_syntax_reference()
            
            # 簡単な差異チェック（行数比較）
            current_lines = len(current_content.split('\n'))
            generated_lines = len(generated_content.split('\n'))
            
            if abs(current_lines - generated_lines) > 5:  # 5行以上の差異
                differences["SYNTAX_REFERENCE.md"] = [
                    f"行数差異: 現在 {current_lines} 行 → 生成 {generated_lines} 行"
                ]
        
        return differences


def main():
    """メイン処理"""
    extractor = SyntaxExtractor()
    
    # 出力ディレクトリ
    output_dir = project_root / "docs" / "generated"
    output_dir.mkdir(exist_ok=True)
    
    # 記法リファレンスを生成
    output_path = output_dir / "SYNTAX_REFERENCE_AUTO.md"
    extractor.save_syntax_reference(output_path)
    
    # 既存ドキュメントとの差異チェック
    docs_dir = project_root / "docs"
    differences = extractor.compare_with_existing_docs(docs_dir)
    
    if differences:
        print("\n⚠️  既存ドキュメントとの差異を検出:")
        for file_name, diff_list in differences.items():
            print(f"  📄 {file_name}:")
            for diff in diff_list:
                print(f"    - {diff}")
        print("\n💡 手動ドキュメントの更新を検討してください。")
    else:
        print("\n✅ 既存ドキュメントとの重大な差異は検出されませんでした。")
    
    print(f"\n🚀 自動生成されたリファレンス: {output_path}")
    print("📋 このファイルを参照して、手動ドキュメントを更新できます。")


if __name__ == "__main__":
    main()