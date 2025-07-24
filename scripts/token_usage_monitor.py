#!/usr/bin/env python3
"""Token使用量の監視・可視化システム."""

import ast
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from kumihan_formatter.core.utilities.logger import get_logger


class TokenUsageMonitor:
    """Token使用量の監視・警告."""

    # Token使用量闾値
    WARNING_THRESHOLD = 1500
    ERROR_THRESHOLD = 2000

    def __init__(self) -> None:
        """初期化."""
        self.logger = get_logger(__name__)
        self.usage_log = Path(".token_usage.json")
        self.enable_logging = os.environ.get("KUMIHAN_DEV_LOG", "").lower() == "true"
        self.json_logging = os.environ.get("KUMIHAN_DEV_LOG_JSON", "").lower() == "true"

    def estimate_token_usage(self, files: List[str]) -> int:
        """Token使用量の推定.

        Args:
            files: 変更ファイルリスト

        Returns:
            推定Token数
        """
        total_tokens = 0

        for file_path in files:
            if not Path(file_path).exists():
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # ファイルタイプ別の精密Token推定
                if file_path.endswith(".py"):
                    tokens = self._estimate_python_tokens_advanced(content)
                elif file_path.endswith((".md", ".txt")):
                    tokens = self._estimate_text_tokens(content)
                elif file_path.endswith((".yml", ".yaml")):
                    tokens = self._estimate_yaml_tokens(content)
                else:
                    tokens = len(content) // 4  # フォールバック

                total_tokens += tokens

            except Exception as e:
                self.logger.warning(f"ファイル読み込みエラー {file_path}: {e}")
                continue

        return total_tokens

    def _estimate_python_tokens_advanced(self, content: str) -> int:
        """PythonファイルのToken数精密推定（AST解析使用）.

        Args:
            content: Pythonコード

        Returns:
            推定Token数
        """
        try:
            # AST解析で精密なトークン推定
            tree = ast.parse(content)
            return self._count_ast_tokens(tree, content)
        except SyntaxError:
            # 構文エラーの場合はフォールバック
            return self._estimate_python_tokens_fallback(content)

    def _count_ast_tokens(self, tree: ast.AST, content: str) -> int:
        """ASTノードからToken数を精密に推定.

        Args:
            tree: ASTルートノード
            content: 元のコード

        Returns:
            Token数
        """
        token_count = 0

        # ASTノードタイプ別のToken数推定
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                # 変数名、関数名など
                token_count += 1
            elif isinstance(node, ast.Constant):
                # 定数（文字列、数値など）
                if isinstance(node.value, str):
                    # 文字列は内容によってToken数が変わる
                    token_count += max(1, len(str(node.value)) // 4)
                else:
                    token_count += 1
            elif isinstance(node, ast.keyword):
                # キーワード引数
                token_count += 2  # キー + 値
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 関数定義: def/async def + 名前 + コロン
                token_count += 3
            elif isinstance(node, ast.ClassDef):
                # クラス定義: class + 名前 + コロン
                token_count += 3
            elif isinstance(node, ast.Import):
                # import文
                token_count += 1 + len(node.names)
            elif isinstance(node, ast.ImportFrom):
                # from import文
                token_count += 2 + len(node.names)  # from + module + import + names
            elif isinstance(node, (ast.If, ast.While, ast.For)):
                # 制御文: if/while/for + 条件 + コロン
                token_count += 2
            elif isinstance(node, ast.BinOp):
                # 二項演算子
                token_count += 1  # 演算子自体
            elif isinstance(node, ast.Call):
                # 関数呼び出し: 関数名 + 括弧
                token_count += 2

        # コメントやドキュメント文字列の処理
        comment_tokens = self._count_comments_and_docstrings(content)

        return token_count + comment_tokens

    def _count_comments_and_docstrings(self, content: str) -> int:
        """Pythonコメントとドキュメント文字列のToken数.

        Args:
            content: Pythonコード

        Returns:
            コメント系のToken数
        """
        lines = content.split("\\n")
        comment_tokens = 0

        in_multiline_string = False
        multiline_delimiter = None

        for line in lines:
            stripped = line.strip()

            # 単一行コメント
            if "#" in line and not in_multiline_string:
                comment_part = line.split("#", 1)[1]
                comment_tokens += max(1, len(comment_part.strip()) // 5)

            # ドキュメント文字列の検出
            if '"""' in stripped or "'''" in stripped:
                if not in_multiline_string:
                    # ドキュメント文字列開始
                    multiline_delimiter = '"""' if '"""' in stripped else "'''"
                    in_multiline_string = True
                    # 同一行で終了するかチェック
                    if stripped.count(multiline_delimiter) >= 2:
                        in_multiline_string = False
                        comment_tokens += max(1, len(stripped) // 4)
                elif multiline_delimiter in stripped:
                    # ドキュメント文字列終了
                    in_multiline_string = False
                    comment_tokens += max(1, len(stripped) // 4)
            elif in_multiline_string:
                # ドキュメント文字列内
                comment_tokens += max(1, len(stripped) // 4)

        return comment_tokens

    def _estimate_python_tokens_fallback(self, content: str) -> int:
        """AST解析失敗時のフォールバック推定.

        Args:
            content: Pythonコード

        Returns:
            推定Token数
        """
        # 既存の簡易推定メソッドを使用
        lines = content.split("\\n")
        token_count = 0

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # 文字列リテラルの検出
            string_content = self._extract_string_literals(line)
            code_content = line

            # 文字列部分はToken数が多い
            for string_literal in string_content:
                token_count += len(string_literal) // 3
                code_content = code_content.replace(string_literal, "", 1)

            # コード部分のトークン分割
            code_tokens = len(
                re.findall(r"\\b\\w+\\b|[+\\-*/=<>!&|(){}\\[\\],.;:]", code_content)
            )
            token_count += code_tokens

        return max(token_count, len(content) // 5)

    def _extract_string_literals(self, line: str) -> List[str]:
        """行から文字列リテラルを抽出.

        Args:
            line: Pythonコードの行

        Returns:
            文字列リテラルのリスト
        """
        # 簡単な文字列検出（エスケープ処理は簡略化）
        strings = []
        # ダブルクォート
        strings.extend(re.findall(r'"([^"\\\\]|\\\\.)*"', line))
        # シングルクォート
        strings.extend(re.findall(r"'([^'\\\\]|\\\\.)*'", line))
        # トリプルクォートは簡略化
        return strings

    def _estimate_text_tokens(self, content: str) -> int:
        """Text/MarkdownファイルのToken数推定.

        Args:
            content: テキスト内容

        Returns:
            推定Token数
        """
        # 英語と日本語の混在を考慮
        words = re.findall(r"\\b\\w+\\b", content)
        japanese_chars = len(
            re.findall(r"[\\u3040-\\u309f\\u30a0-\\u30ff\\u4e00-\\u9faf]", content)
        )

        # 英語単語は1単語=1Token、日本語は2文字=1Token程度
        return len(words) + japanese_chars // 2

    def _estimate_yaml_tokens(self, content: str) -> int:
        """YAMLファイルのToken数推定.

        Args:
            content: YAML内容

        Returns:
            推定Token数
        """
        # YAMLのキー、値、構造を考慮
        lines = [line.strip() for line in content.split("\\n") if line.strip()]
        token_count = 0

        for line in lines:
            if line.startswith("#"):
                continue  # コメントは無視

            # キー: 値 の形式
            if ":" in line:
                key_value = line.split(":", 1)
                token_count += len(key_value[0].strip()) // 4  # キー
                if len(key_value) > 1 and key_value[1].strip():
                    token_count += len(key_value[1].strip()) // 4  # 値
            else:
                token_count += len(line) // 4

        return max(token_count, len(content) // 6)

    def analyze_pr_diff(self) -> Dict[str, int]:
        """PR差分のToken使用量分析.

        Returns:
            分析結果
        """
        try:
            # PR差分の取得
            result = subprocess.run(
                ["git", "diff", "--name-only", "origin/main...HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            changed_files = result.stdout.strip().split("\n")

            # Pythonファイルのみ対象
            py_files = [f for f in changed_files if f.endswith(".py")]

            token_usage = self.estimate_token_usage(py_files)

            return {
                "total_tokens": token_usage,
                "file_count": len(py_files),
                "status": self._get_status(token_usage),
                "timestamp": datetime.now().isoformat(),
            }

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git差分取得失敗: {e}")
            return {"error": str(e)}

    def _get_status(self, tokens: int) -> str:
        """Token数に基づくステータス判定.

        Args:
            tokens: Token数

        Returns:
            ステータス
        """
        if tokens >= self.ERROR_THRESHOLD:
            return "error"
        elif tokens >= self.WARNING_THRESHOLD:
            return "warning"
        return "ok"

    def report_usage(self, analysis: Dict[str, int]) -> None:
        """使用量レポート.

        Args:
            analysis: 分析結果
        """
        if not self.enable_logging:
            return

        if self.json_logging:
            # JSON形式で出力
            print(json.dumps(analysis, indent=2, ensure_ascii=False))
        else:
            # ヒューマンリーダブル形式
            if "error" in analysis:
                print(f"\n❌ Token使用量分析エラー: {analysis['error']}")
                return

            tokens = analysis["total_tokens"]
            status = analysis["status"]

            print("\n" + "=" * 60)
            print("📊 Token使用量レポート")
            print("=" * 60)
            print(f"\u5408計Token数: {tokens:,}")
            print(f"\u5909更ファイル数: {analysis['file_count']}")

            if status == "error":
                print(
                    f"\n❌ エラー: Token使用量が上限({self.ERROR_THRESHOLD:,})を超えました"
                )
                print("💡 ファイル分割を検討してください")
            elif status == "warning":
                print(
                    f"\n⚠️  警告: Token使用量が警告闾値({self.WARNING_THRESHOLD:,})に近づいています"
                )
            else:
                print("\n✅ Token使用量は適切な範囲内です")

            print("=" * 60)

    def save_history(
        self, analysis: Dict[str, Union[int, str, Dict[str, int]]]
    ) -> None:
        """履歴保存.

        Args:
            analysis: 分析結果
        """
        history = []
        if self.usage_log.exists():
            with open(self.usage_log, "r") as f:
                history = json.load(f)

        history.append(analysis)

        # 最新30件保持
        if len(history) > 30:
            history = history[-30:]

        with open(self.usage_log, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)


def main() -> None:
    """メインエントリーポイント."""
    monitor = TokenUsageMonitor()
    analysis = monitor.analyze_pr_diff()
    monitor.report_usage(analysis)

    if "total_tokens" in analysis:
        monitor.save_history(analysis)

        # CI/CD用の終了コード
        if analysis["status"] == "error":
            exit(1)


if __name__ == "__main__":
    main()
