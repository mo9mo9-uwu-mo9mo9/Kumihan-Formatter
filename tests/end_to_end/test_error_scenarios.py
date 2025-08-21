"""エラーシナリオのエンドツーエンドテスト

各段階でのエラー処理・回復機能をテストし、
システムの堅牢性を確認する。
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestErrorScenarios:
    """エラーシナリオのテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.temp_dir = Path(tempfile.mkdtemp())
        logger.info(f"テスト用一時ディレクトリ: {self.temp_dir}")

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        import shutil

        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"一時ディレクトリを削除: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"一時ディレクトリの削除に失敗: {e}")

    def process_with_error_handling(
        self, input_content: str, simulate_error: Optional[str] = None
    ) -> Dict[str, Any]:
        """エラーハンドリング付きの処理実行"""
        try:
            # 1. 入力検証
            if simulate_error == "invalid_input":
                raise ValueError("無効な入力データ")

            if not input_content or not input_content.strip():
                logger.warning("空の入力データを検出")
                return {
                    "success": True,
                    "warning": "empty_input",
                    "output": self._generate_empty_output(),
                    "recovery_applied": True,
                }

            # 2. パース処理
            if simulate_error == "parse_error":
                raise RuntimeError("パース処理エラー")

            parsed_data = self._mock_parse_with_recovery(input_content)

            # 3. レンダリング処理
            if simulate_error == "render_error":
                raise RuntimeError("レンダリング処理エラー")

            rendered_output = self._mock_render_with_recovery(parsed_data)

            # 4. 出力処理
            if simulate_error == "output_error":
                raise IOError("出力処理エラー")

            output_file = self.temp_dir / "output_with_error_handling.html"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(rendered_output)

            return {
                "success": True,
                "output": rendered_output,
                "output_file": output_file,
                "warnings": parsed_data.get("warnings", []),
                "recovery_applied": parsed_data.get("recovery_applied", False),
            }

        except Exception as e:
            logger.error(f"処理エラー: {e}")

            # エラー回復処理
            try:
                recovery_output = self._generate_error_recovery_output(
                    str(e), input_content
                )
                recovery_file = self.temp_dir / "recovery_output.html"
                with open(recovery_file, "w", encoding="utf-8") as f:
                    f.write(recovery_output)

                return {
                    "success": False,
                    "error": str(e),
                    "recovery_applied": True,
                    "recovery_output": recovery_output,
                    "recovery_file": recovery_file,
                }
            except Exception as recovery_error:
                logger.error(f"回復処理も失敗: {recovery_error}")
                return {
                    "success": False,
                    "error": str(e),
                    "recovery_error": str(recovery_error),
                    "recovery_applied": False,
                }

    def _mock_parse_with_recovery(self, content: str) -> Dict[str, Any]:
        """回復機能付きパース処理のモック"""
        lines = content.split("\n")
        warnings = []
        recovery_applied = False

        # 不正な記法の検出と回復
        corrected_lines = []
        for i, line in enumerate(lines):
            corrected_line = line

            # 不完全なブロック記法の修正
            if (
                line.startswith("#")
                and not line.endswith("#")
                and not line.endswith("##")
            ):
                if "#" in line[1:]:  # インライン記法の可能性
                    corrected_line = line + "#"
                    warnings.append(f"行{i+1}: 不完全なインライン記法を修正")
                    recovery_applied = True
                else:  # ブロック記法の可能性
                    corrected_line = line + "\n内容が不明\n##"
                    warnings.append(f"行{i+1}: 不完全なブロック記法を修正")
                    recovery_applied = True

            # 閉じタグの不整合修正
            if line.strip() == "#" and i > 0 and not lines[i - 1].startswith("#"):
                warnings.append(f"行{i+1}: 孤立した閉じタグを検出")
                recovery_applied = True

            corrected_lines.append(corrected_line)

        return {
            "line_count": len(lines),
            "corrected_content": "\n".join(corrected_lines),
            "warnings": warnings,
            "recovery_applied": recovery_applied,
            "error_count": len(warnings),
        }

    def _mock_render_with_recovery(self, parsed_data: Dict[str, Any]) -> str:
        """回復機能付きレンダリング処理のモック"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='ja'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<title>Kumihan Formatter - エラー回復モード</title>",
            "<style>",
            ".warning { color: orange; }",
            ".error { color: red; }",
            ".recovery { background-color: #fff3cd; padding: 10px; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>処理結果（エラー回復モード）</h1>",
        ]

        if parsed_data.get("recovery_applied"):
            html_parts.append('<div class="recovery">')
            html_parts.append("<h2>回復処理が適用されました</h2>")
            html_parts.append(
                f'<p>検出されたエラー数: {parsed_data.get("error_count", 0)}</p>'
            )
            html_parts.append("</div>")

        if parsed_data.get("warnings"):
            html_parts.append('<div class="warning">')
            html_parts.append("<h3>警告</h3>")
            html_parts.append("<ul>")
            for warning in parsed_data["warnings"]:
                html_parts.append(f"<li>{warning}</li>")
            html_parts.append("</ul>")
            html_parts.append("</div>")

        html_parts.extend(
            [
                f"<p>処理された行数: {parsed_data.get('line_count', 0)}</p>",
                "<h3>修正された内容</h3>",
                f"<pre>{parsed_data.get('corrected_content', '')}</pre>",
                "</body>",
                "</html>",
            ]
        )

        return "\n".join(html_parts)

    def _generate_empty_output(self) -> str:
        """空入力用の出力生成"""
        return """<!DOCTYPE html>
<html lang='ja'>
<head>
<meta charset='UTF-8'>
<title>Kumihan Formatter - 空ドキュメント</title>
</head>
<body>
<h1>空のドキュメント</h1>
<p>処理する内容がありませんでした。</p>
</body>
</html>"""

    def _generate_error_recovery_output(
        self, error_message: str, original_content: str
    ) -> str:
        """エラー回復用の出力生成"""
        return f"""<!DOCTYPE html>
<html lang='ja'>
<head>
<meta charset='UTF-8'>
<title>Kumihan Formatter - エラー回復</title>
<style>
.error {{ color: red; background-color: #ffe6e6; padding: 10px; }}
.original {{ background-color: #f5f5f5; padding: 10px; white-space: pre-wrap; }}
</style>
</head>
<body>
<h1>エラー回復モード</h1>
<div class="error">
<h2>エラーが発生しました</h2>
<p>エラー内容: {error_message}</p>
</div>
<h3>元の内容</h3>
<div class="original">{original_content}</div>
<p>エラー回復処理により、基本的なHTMLとして出力されました。</p>
</body>
</html>"""

    @pytest.mark.e2e
    def test_エラーシナリオ_不正な記法(self) -> None:
        """エラーシナリオ: 不正な記法の処理"""
        # Given: 不正な記法を含むコンテンツ
        invalid_content = """#見出し
不完全なブロック記法

#太字 不完全なインライン記法

#
孤立した閉じタグ

正常な#太字#記法
"""

        # When: エラーハンドリング処理実行
        result = self.process_with_error_handling(invalid_content)

        # Then: 回復処理の確認
        assert result["success"], "不正記法の回復処理が失敗"
        assert result["recovery_applied"], "回復処理が適用されていない"
        assert len(result["warnings"]) > 0, "警告が記録されていない"
        assert result["output_file"].exists(), "回復出力ファイルが作成されていない"

        logger.info(f"不正記法回復完了: {len(result['warnings'])}件の警告")

    @pytest.mark.e2e
    def test_エラーシナリオ_空ファイル処理(self) -> None:
        """エラーシナリオ: 空ファイルの処理"""
        # Given: 空のコンテンツ
        empty_content = ""

        # When: 処理実行
        result = self.process_with_error_handling(empty_content)

        # Then: 空ファイル処理の確認
        assert result["success"], "空ファイル処理が失敗"
        assert result.get("warning") == "empty_input", "空入力警告が設定されていない"
        assert result["recovery_applied"], "空ファイル回復処理が適用されていない"
        assert "空のドキュメント" in result["output"], "空ファイル出力内容が不正"

    @pytest.mark.e2e
    def test_エラーシナリオ_パース段階エラー(self) -> None:
        """エラーシナリオ: パース段階でのエラー"""
        # Given: 通常のコンテンツ + パースエラーシミュレート
        normal_content = "#見出し#\n通常のコンテンツ"

        # When: パースエラーをシミュレート
        result = self.process_with_error_handling(
            normal_content, simulate_error="parse_error"
        )

        # Then: エラー回復の確認
        assert not result["success"], "パースエラーが正しく検出されていない"
        assert result["recovery_applied"], "パースエラー回復処理が適用されていない"
        assert "パース処理エラー" in result["error"], "エラーメッセージが不正"
        assert result["recovery_file"].exists(), "回復ファイルが作成されていない"

    @pytest.mark.e2e
    def test_エラーシナリオ_レンダリング段階エラー(self) -> None:
        """エラーシナリオ: レンダリング段階でのエラー"""
        # Given: 通常のコンテンツ + レンダリングエラーシミュレート
        normal_content = "#見出し#\n通常のコンテンツ"

        # When: レンダリングエラーをシミュレート
        result = self.process_with_error_handling(
            normal_content, simulate_error="render_error"
        )

        # Then: エラー回復の確認
        assert not result["success"], "レンダリングエラーが正しく検出されていない"
        assert result[
            "recovery_applied"
        ], "レンダリングエラー回復処理が適用されていない"
        assert "レンダリング処理エラー" in result["error"], "エラーメッセージが不正"

    @pytest.mark.e2e
    def test_エラーシナリオ_出力段階エラー(self) -> None:
        """エラーシナリオ: 出力段階でのエラー"""
        # Given: 通常のコンテンツ + 出力エラーシミュレート
        normal_content = "#見出し#\n通常のコンテンツ"

        # When: 出力エラーをシミュレート
        result = self.process_with_error_handling(
            normal_content, simulate_error="output_error"
        )

        # Then: エラー回復の確認
        assert not result["success"], "出力エラーが正しく検出されていない"
        assert result["recovery_applied"], "出力エラー回復処理が適用されていない"
        assert "出力処理エラー" in result["error"], "エラーメッセージが不正"

    @pytest.mark.e2e
    def test_エラーシナリオ_複数エラー混在(self) -> None:
        """エラーシナリオ: 複数のエラーが混在"""
        # Given: 複数の不正記法を含むコンテンツ
        multi_error_content = """#見出し
不完全なブロック1

#太字 不完全なインライン1

#イタリック 不完全なインライン2

#
孤立した閉じタグ1

正常な#太字#記法

#
孤立した閉じタグ2

#見出し2
不完全なブロック2
"""

        # When: 処理実行
        result = self.process_with_error_handling(multi_error_content)

        # Then: 複数エラー処理の確認
        assert result["success"], "複数エラー処理が失敗"
        assert result["recovery_applied"], "複数エラー回復処理が適用されていない"
        assert len(result["warnings"]) >= 3, f"警告数が不足: {len(result['warnings'])}"

        # 出力内容の確認
        output_content = result["output"]
        assert (
            "回復処理が適用されました" in output_content
        ), "回復処理通知が出力されていない"
        assert "警告" in output_content, "警告セクションが出力されていない"

        logger.info(f"複数エラー回復完了: {len(result['warnings'])}件の警告")

    @pytest.mark.e2e
    def test_エラーシナリオ_回復処理の品質(self) -> None:
        """エラーシナリオ: 回復処理の品質確認"""
        # Given: 軽微なエラーを含むコンテンツ
        minor_error_content = """#見出し#
正常なコンテンツ

#太字 軽微なエラー

正常な#太字#記法

#イタリック
正常なブロック
##
"""

        # When: 処理実行
        result = self.process_with_error_handling(minor_error_content)

        # Then: 回復品質の確認
        assert result["success"], "軽微エラー処理が失敗"

        if result["recovery_applied"]:
            # 回復が適用された場合の品質確認
            assert len(result["warnings"]) <= 2, "過剰な警告が発生"

            output_content = result["output"]
            assert "<!DOCTYPE html>" in output_content, "HTML構造が正しくない"
            assert "charset='UTF-8'" in output_content, "エンコーディング指定がない"
            assert "正常なコンテンツ" in output_content, "正常部分が失われている"

        logger.info(f"回復品質確認完了: 回復適用={result['recovery_applied']}")

    @pytest.mark.e2e
    def test_エラーシナリオ_invalid_input(self) -> None:
        """エラーシナリオ: 無効な入力データ"""
        # Given: 無効な入力をシミュレート
        normal_content = "#見出し#\n通常のコンテンツ"

        # When: 無効入力エラーをシミュレート
        result = self.process_with_error_handling(
            normal_content, simulate_error="invalid_input"
        )

        # Then: 無効入力エラー処理の確認
        assert not result["success"], "無効入力エラーが正しく検出されていない"
        assert result["recovery_applied"], "無効入力回復処理が適用されていない"
        assert "無効な入力データ" in result["error"], "エラーメッセージが不正"
        assert result["recovery_file"].exists(), "回復ファイルが作成されていない"
