"""
統合API - Issue #1146 アーキテクチャ簡素化
==========================================

従来の複雑なManager/Parserクラス群を統合し、
シンプルで直感的なAPIを提供します。

使用例:
    from kumihan_formatter.unified_api import KumihanFormatter

    formatter = KumihanFormatter()
    result = formatter.convert("input.txt", "output.html")
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import logging
from pathlib import Path
from .simple_parser import SimpleKumihanParser
from .simple_renderer import SimpleHTMLRenderer


class KumihanFormatter:
    """統合Kumihan-Formatterクラス - 全機能へのシンプルなエントリーポイント"""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path

        # 実用的なパーサー・レンダラーを初期化
        self.parser = SimpleKumihanParser()
        self.renderer = SimpleHTMLRenderer()

        self.logger.info("KumihanFormatter initialized - 動作版")

    def convert(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
        template: str = "default",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """簡素化された変換メソッド"""
        try:
            # ファイル読み込み
            input_path = Path(input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_file}")

            content = input_path.read_text(encoding="utf-8")

            # 解析
            parsed_result = self.parser.parse(content)

            # レンダリング
            if not output_file:
                output_file = Path(input_file).with_suffix(".html")

            rendered_content = self.renderer.render(parsed_result)

            # ファイル出力
            output_path = Path(output_file)
            output_path.write_text(rendered_content, encoding="utf-8")

            return {
                "status": "success",
                "input_file": str(input_file),
                "output_file": str(output_file),
                "template": template,
                "elements_count": parsed_result.get("total_elements", 0),
            }

        except Exception as e:
            self.logger.error(f"Conversion error: {e}")
            return {"status": "error", "error": str(e), "input_file": str(input_file)}

    def convert_text(self, text: str, template: str = "default") -> str:
        """テキスト→HTML変換 (APIドキュメント対応)"""
        try:
            # テキスト解析
            parsed_result = self.parser.parse(text)
            
            # HTML生成
            html_content = self.renderer.render(parsed_result)
            
            self.logger.debug(f"Text conversion completed: {len(text)} chars → {len(html_content)} chars")
            return html_content
            
        except Exception as e:
            self.logger.error(f"Text conversion error: {e}")
            return f"<p>Conversion Error: {e}</p>"

    def parse_text(self, text: str, parser_type: str = "auto") -> Dict[str, Any]:
        """テキスト解析"""
        try:
            result = self.parser.parse(text)
            return result
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            return {"status": "error", "error": str(e)}

    def validate_syntax(self, text: str) -> Dict[str, Any]:
        """構文検証"""
        try:
            errors = self.parser.validate(text)
            return {
                "status": "valid" if not errors else "invalid",
                "errors": errors,
                "total_errors": len(errors),
            }
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return {"status": "error", "error": str(e), "errors": []}

    def parse_file(
        self, file_path: Union[str, Path], parser_type: str = "auto"
    ) -> Dict[str, Any]:
        """ファイル解析"""
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            result = self.parser.parse(content)
            result["file_path"] = str(file_path)
            return result
        except Exception as e:
            self.logger.error(f"File parsing error: {e}")
            return {"status": "error", "error": str(e), "file_path": str(file_path)}

    def get_available_templates(self) -> List[str]:
        """一時的にスタブ実装"""
        return ["default", "minimal"]  # 固定値

    def get_system_info(self) -> Dict[str, Any]:
        """システム情報"""
        return {
            "architecture": "working_system",
            "components": {
                "parser": "SimpleKumihanParser",
                "renderer": "SimpleHTMLRenderer",
            },
            "version": "4.0.0-working",
            "status": "functional",
        }

    def close(self) -> None:
        """システムのリソース解放"""
        self.logger.info("KumihanFormatter closed successfully - working system")

    def __enter__(self) -> "KumihanFormatter":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


# 便利関数
def quick_convert(
    input_file: Union[str, Path], output_file: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """クイック変換関数"""
    with KumihanFormatter() as formatter:
        return formatter.convert(input_file, output_file)


def quick_parse(text: str) -> Dict[str, Any]:
    """クイック解析関数"""
    with KumihanFormatter() as formatter:
        return formatter.parse_text(text)


def unified_parse(text: str, parser_type: str = "auto") -> Dict[str, Any]:
    """統合パーサーシステムによる高速解析"""
    with KumihanFormatter() as formatter:
        return formatter.parse_text(text, parser_type)


def validate_kumihan_syntax(text: str) -> Dict[str, Any]:
    """Kumihan記法構文の詳細検証"""
    with KumihanFormatter() as formatter:
        return formatter.validate_syntax(text)


def get_parser_system_info() -> Dict[str, Any]:
    """統合パーサーシステムの詳細情報取得"""
    with KumihanFormatter() as formatter:
        return formatter.get_system_info()


# 後方互換性のためのエイリアス
parse = unified_parse
validate = validate_kumihan_syntax


def main() -> None:
    """CLI エントリーポイント - シンプル実装"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: kumihan <入力ファイル> [出力ファイル]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = quick_convert(input_file, output_file)
        if result["status"] == "success":
            print(f"変換完了: {result['output_file']}")
        else:
            print(f"変換エラー: {result['error']}")
            sys.exit(1)
    except Exception as e:
        print(f"実行エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
