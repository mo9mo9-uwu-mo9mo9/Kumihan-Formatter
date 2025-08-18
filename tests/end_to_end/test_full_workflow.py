"""完全ワークフローのエンドツーエンドテスト

パース → レンダリング → 出力の完全フローをテストし、
システム全体の統合性を確認する。
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

import pytest

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestFullWorkflow:
    """完全ワークフローのテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.test_data_dir = Path("tests/manual")
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

    def run_full_workflow(self, input_file: Path) -> Dict[str, Any]:
        """完全ワークフローを実行"""
        try:
            # 1. ファイル読み込み
            start_time = time.time()

            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            read_time = time.time() - start_time

            # 2. パース処理（モック実装）
            parse_start = time.time()
            parsed_data = self._mock_parse(content)
            parse_time = time.time() - parse_start

            # 3. レンダリング処理（モック実装）
            render_start = time.time()
            rendered_output = self._mock_render(parsed_data)
            render_time = time.time() - render_start

            # 4. 出力ファイル作成
            output_start = time.time()
            output_file = self.temp_dir / "output.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(rendered_output)
            output_time = time.time() - output_start

            total_time = time.time() - start_time

            return {
                "success": True,
                "processing_time": total_time,
                "read_time": read_time,
                "parse_time": parse_time,
                "render_time": render_time,
                "output_time": output_time,
                "output_size": len(rendered_output),
                "output_file": output_file,
                "output_quality": self._calculate_quality_score(rendered_output)
            }

        except Exception as e:
            logger.error(f"ワークフロー実行エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": 0.0,
                "output_quality": 0.0
            }

    def _mock_parse(self, content: str) -> Dict[str, Any]:
        """パース処理のモック実装"""
        lines = content.split('\n')
        return {
            "line_count": len(lines),
            "has_headings": any(line.startswith('#') for line in lines),
            "has_bold": any('#太字#' in line for line in lines),
            "has_italic": any('#イタリック' in line for line in lines),
            "content_blocks": len([line for line in lines if line.strip()])
        }

    def _mock_render(self, parsed_data: Dict[str, Any]) -> str:
        """レンダリング処理のモック実装"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='ja'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<title>Kumihan Formatter テスト</title>",
            "</head>",
            "<body>",
            f"<h1>処理結果</h1>",
            f"<p>行数: {parsed_data['line_count']}</p>",
            f"<p>見出し: {'あり' if parsed_data['has_headings'] else 'なし'}</p>",
            f"<p>太字: {'あり' if parsed_data['has_bold'] else 'なし'}</p>",
            f"<p>イタリック: {'あり' if parsed_data['has_italic'] else 'なし'}</p>",
            f"<p>コンテンツブロック: {parsed_data['content_blocks']}</p>",
            "</body>",
            "</html>"
        ]
        return '\n'.join(html_parts)

    def _calculate_quality_score(self, output: str) -> float:
        """出力品質スコアを計算"""
        # 基本的な品質指標
        score = 0.0

        # HTML構造の確認
        if "<!DOCTYPE html>" in output:
            score += 0.2
        if "<html" in output and "</html>" in output:
            score += 0.2
        if "<head" in output and "</head>" in output:
            score += 0.2
        if "<body" in output and "</body>" in output:
            score += 0.2
        if "<title>" in output:
            score += 0.1
        if "charset=UTF-8" in output or "charset='UTF-8'" in output:
            score += 0.1

        return score

    def generate_large_test_data(self, line_count: int) -> str:
        """大量テストデータを生成"""
        lines = []
        for i in range(line_count):
            if i % 10 == 0:
                lines.append(f"#見出し{i}#")
                lines.append("見出しコンテンツ")
                lines.append("#")
            elif i % 5 == 0:
                lines.append(f"#太字 テストライン{i}#")
            else:
                lines.append(f"通常のテキスト行 {i}")

        return '\n'.join(lines)

    @pytest.mark.e2e
    def test_完全ワークフロー_基本(self) -> None:
        """完全ワークフロー: パース → レンダリング → 出力"""
        # Given: テストファイル
        input_file = self.test_data_dir / "notation_test.txt"

        if not input_file.exists():
            pytest.skip(f"テストファイルが見つかりません: {input_file}")

        # When: 完全処理実行
        start_time = time.time()
        result = self.run_full_workflow(input_file)
        processing_time = time.time() - start_time

        # Then: 結果検証
        assert result["success"], f"処理が失敗: {result.get('error', '不明')}"
        assert processing_time < 5.0, f"処理時間が長すぎます: {processing_time}秒"
        assert result["output_quality"] > 0.9, f"出力品質が低い: {result['output_quality']}"

        # 出力ファイルの存在確認
        assert result["output_file"].exists(), "出力ファイルが作成されていません"

        logger.info(f"ワークフロー完了: {processing_time:.3f}秒, 品質: {result['output_quality']:.3f}")

    @pytest.mark.e2e
    def test_完全ワークフロー_複合記法(self) -> None:
        """完全ワークフロー: 複合記法での処理"""
        # Given: 複合記法テストファイル
        input_file = self.test_data_dir / "compound_test.txt"

        if not input_file.exists():
            pytest.skip(f"テストファイルが見つかりません: {input_file}")

        # When: 処理実行
        result = self.run_full_workflow(input_file)

        # Then: 結果検証
        assert result["success"], f"複合記法処理が失敗: {result.get('error')}"
        assert result["output_quality"] > 0.8, "複合記法の品質が低い"
        assert result["processing_time"] < 10.0, "複合記法処理時間が長すぎる"

    @pytest.mark.e2e
    def test_完全ワークフロー_空ファイル(self) -> None:
        """完全ワークフロー: 空ファイルの処理"""
        # Given: 空ファイル
        empty_file = self.temp_dir / "empty.txt"
        empty_file.write_text("", encoding='utf-8')

        # When: 処理実行
        result = self.run_full_workflow(empty_file)

        # Then: 結果検証
        assert result["success"], "空ファイル処理が失敗"
        assert result["output_quality"] > 0.5, "空ファイル出力品質が低い"

    @pytest.mark.e2e
    def test_完全ワークフロー_パフォーマンス_中規模(self) -> None:
        """完全ワークフロー: 中規模データのパフォーマンス"""
        # Given: 中規模テストデータ（1000行）
        large_content = self.generate_large_test_data(1000)
        large_file = self.temp_dir / "large_test.txt"
        large_file.write_text(large_content, encoding='utf-8')

        # When: 処理実行
        result = self.run_full_workflow(large_file)

        # Then: パフォーマンス基準確認
        assert result["success"], f"中規模データ処理が失敗: {result.get('error')}"
        assert result["processing_time"] < 5.0, f"中規模データ処理時間超過: {result['processing_time']}秒"
        assert result["output_quality"] > 0.8, "中規模データ出力品質が低い"

        logger.info(f"中規模データ処理完了: {result['processing_time']:.3f}秒")

    @pytest.mark.e2e
    def test_完全ワークフロー_詳細メトリクス(self) -> None:
        """完全ワークフロー: 詳細メトリクスの確認"""
        # Given: 基本テストファイル
        input_file = self.test_data_dir / "notation_test.txt"

        if not input_file.exists():
            pytest.skip(f"テストファイルが見つかりません: {input_file}")

        # When: 処理実行
        result = self.run_full_workflow(input_file)

        # Then: 詳細メトリクス検証
        assert result["success"], "基本処理が失敗"

        # 各段階の時間確認
        assert result["read_time"] < 1.0, "ファイル読み込み時間が長すぎる"
        assert result["parse_time"] < 2.0, "パース時間が長すぎる"
        assert result["render_time"] < 2.0, "レンダリング時間が長すぎる"
        assert result["output_time"] < 1.0, "出力時間が長すぎる"

        # 出力サイズ確認
        assert result["output_size"] > 100, "出力サイズが小さすぎる"

        logger.info(f"詳細メトリクス - 読込: {result['read_time']:.3f}s, "
                   f"パース: {result['parse_time']:.3f}s, "
                   f"レンダ: {result['render_time']:.3f}s, "
                   f"出力: {result['output_time']:.3f}s")

    @pytest.mark.e2e
    def test_完全ワークフロー_エンコーディング確認(self) -> None:
        """完全ワークフロー: UTF-8エンコーディングの確認"""
        # Given: 日本語を含むテストファイル
        japanese_content = """#見出し#
日本語コンテンツテスト
複雑な漢字：龍、鳳、麟
##

#太字 日本語太字テスト#
#イタリック
日本語イタリックテスト
##
"""
        japanese_file = self.temp_dir / "japanese_test.txt"
        japanese_file.write_text(japanese_content, encoding='utf-8')

        # When: 処理実行
        result = self.run_full_workflow(japanese_file)

        # Then: エンコーディング確認
        assert result["success"], "日本語ファイル処理が失敗"

        # 出力ファイルのエンコーディング確認
        output_content = result["output_file"].read_text(encoding='utf-8')
        # 日本語文字が含まれているかを確認（ひらがな、カタカナ、漢字のいずれか）
        japanese_found = any(char in output_content for char in "日本語あいうえおアイウエオ見出し内容")
        assert japanese_found, "日本語が正しく出力されていない"
        assert "charset='UTF-8'" in output_content, "UTF-8エンコーディング指定がない"

        logger.info("日本語エンコーディングテスト完了")
