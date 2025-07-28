"""
Full Pipeline Integration Tests - テスト戦略v2.0

入力→解析→レンダリング→出力の全フローをテスト
実際のファイル操作とコマンド実行を含むエンドツーエンドテスト
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestFullConversionPipeline:
    """完全な変換パイプラインのテスト"""

    def setup_method(self):
        """各テスト前の共通セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        import shutil

        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)

    def test_basic_file_conversion_pipeline(self):
        """基本的なファイル変換パイプライン"""
        # Given: 基本的な入力ファイル
        input_file = self.temp_path / "input.txt"
        output_file = self.temp_path / "output.html"

        input_content = """;;;太字;;;重要なお知らせ;;;

この文書は基本的なテストです。

;;;見出し1;;;第一章;;;
本文の内容がここに入ります。

;;;画像;;;/path/to/test.jpg;;;"""

        input_file.write_text(input_content, encoding="utf-8")

        # When: 変換コマンド実行
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "kumihan_formatter",
                "convert",
                str(input_file),
                str(output_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Then: 変換が成功する
        assert result.returncode == 0, f"変換失敗: {result.stderr}"
        assert output_file.exists(), "出力ファイルが作成されない"

        # 出力内容の基本検証
        output_content = output_file.read_text(encoding="utf-8")
        assert "<html>" in output_content, "HTML構造が不正"
        assert "重要なお知らせ" in output_content, "コンテンツが保持されない"
        assert "第一章" in output_content, "見出しが保持されない"

    def test_japanese_content_pipeline(self):
        """日本語コンテンツの変換パイプライン"""
        # Given: 日本語専用コンテンツ
        input_file = self.temp_path / "japanese.txt"
        output_file = self.temp_path / "japanese.html"

        japanese_content = """;;;見出し1;;;クトゥルフ神話TRPGシナリオ;;;

;;;太字;;;導入;;;
探索者たちは古い図書館で奇妙な本を発見する。

;;;引用;;;
「この本を読む者は、永遠の知識を得るだろう」
;;;

;;;リスト;;;
・SAN値チェック
・知識ロール
・図書館利用技能
;;;"""

        input_file.write_text(japanese_content, encoding="utf-8")

        # When: 変換実行
        result = subprocess.run(
            [sys.executable, "-m", "kumihan_formatter", "convert", str(input_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Then: 日本語が正しく処理される
        assert result.returncode == 0, f"日本語変換失敗: {result.stderr}"

        # デフォルト出力ファイルの確認
        default_output = input_file.with_suffix(".html")
        assert default_output.exists(), "デフォルト出力が作成されない"

        content = default_output.read_text(encoding="utf-8")
        assert "クトゥルフ神話" in content, "日本語タイトル未保持"
        assert "探索者" in content, "日本語本文未保持"
        assert "SAN値" in content, "日本語リスト未保持"

    def test_error_handling_pipeline(self):
        """エラーハンドリングパイプライン"""
        # Given: 存在しない入力ファイル
        nonexistent_file = self.temp_path / "nonexistent.txt"

        # When: 変換試行
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "kumihan_formatter",
                "convert",
                str(nonexistent_file),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Then: 適切なエラーハンドリング
        assert result.returncode != 0, "エラーが検出されない"
        assert (
            "ファイル" in result.stderr or "file" in result.stderr.lower()
        ), "エラーメッセージが不適切"

    def test_malformed_syntax_pipeline(self):
        """不正構文の処理パイプライン"""
        # Given: 不正構文を含む入力
        input_file = self.temp_path / "malformed.txt"
        output_file = self.temp_path / "malformed.html"

        malformed_content = """正常なテキスト

;;;不完全な構文
これは正しくない構文です。

;;;正常;;;これは正常な構文;;;

;;;空のキーワード;;;コンテンツ;;;"""

        input_file.write_text(malformed_content, encoding="utf-8")

        # When: 変換実行
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "kumihan_formatter",
                "convert",
                str(input_file),
                str(output_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Then: 可能な部分は変換される（完全失敗しない）
        # エラーがあっても処理を継続することが重要
        if result.returncode == 0:
            # 成功した場合、出力ファイルが作成される
            assert output_file.exists()
            content = output_file.read_text(encoding="utf-8")
            assert "正常なテキスト" in content, "正常部分が失われる"
        else:
            # エラーがある場合、適切なエラーメッセージが出力される
            assert len(result.stderr) > 0, "エラー情報がない"


class TestCommandLineInterface:
    """CLI インターフェースの統合テスト"""

    def test_help_command(self):
        """ヘルプコマンドの動作確認"""
        # When: ヘルプ表示
        result = subprocess.run(
            [sys.executable, "-m", "kumihan_formatter", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Then: ヘルプが表示される
        assert result.returncode == 0
        assert "usage" in result.stdout.lower() or "使用法" in result.stdout

    def test_version_command(self):
        """バージョンコマンドの動作確認"""
        # When: バージョン表示
        result = subprocess.run(
            [sys.executable, "-m", "kumihan_formatter", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Then: バージョン情報が表示される
        # エラーでなければOK（実装によってはバージョンコマンドがない場合もある）
        assert result.returncode == 0 or "unrecognized arguments" in result.stderr


class TestPerformancePipeline:
    """パフォーマンス統合テスト"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        import shutil

        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)

    def test_medium_file_performance(self):
        """中程度ファイルの処理性能"""
        # Given: 中程度サイズのファイル（1000行程度）
        input_file = self.temp_path / "medium.txt"
        output_file = self.temp_path / "medium.html"

        # 1000行のコンテンツ生成
        lines = []
        for i in range(1000):
            if i % 10 == 0:
                lines.append(f";;;見出し1;;;セクション {i};;;")
            elif i % 5 == 0:
                lines.append(f";;;太字;;;重要事項 {i};;;")
            else:
                lines.append(f"通常のテキスト行 {i}")

        content = "\n".join(lines)
        input_file.write_text(content, encoding="utf-8")

        # When: 変換実行時間を測定
        import time

        start_time = time.time()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "kumihan_formatter",
                "convert",
                str(input_file),
                str(output_file),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        execution_time = time.time() - start_time

        # Then: 合理的な時間で完了
        assert result.returncode == 0, f"中程度ファイル変換失敗: {result.stderr}"
        assert execution_time < 60.0, f"処理時間が長すぎる: {execution_time}秒"
        assert output_file.exists()

        # 出力品質確認
        output_content = output_file.read_text(encoding="utf-8")
        assert "セクション 0" in output_content, "最初のセクションが未処理"
        assert "セクション 990" in output_content, "最後のセクションが未処理"


if __name__ == "__main__":
    # 直接実行時のテスト
    pytest.main([__file__, "-v"])
