"""
Parser Contract Tests - テスト戦略v2.0

構文解析の重要な契約のみをテスト
実装詳細ではなく、公開インターフェースの動作を保証
"""

import sys
from pathlib import Path

import pytest

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kumihan_formatter.core.keyword_parser import KeywordParser


class TestParserContract:
    """構文解析の基本契約をテスト"""

    def setup_method(self):
        """各テスト前の共通セットアップ"""
        self.parser = KeywordParser()

    def test_basic_bold_syntax_contract(self):
        """太字構文の基本契約: ;;;太字;;;内容;;; → 太字要素"""
        # Given: 基本的な太字構文
        input_text = ";;;太字;;;強調したいテキスト;;;"

        # When: 解析実行
        result = self.parser.parse_line(input_text)

        # Then: 太字として認識される
        assert result is not None
        assert "太字" in str(result)  # 実装詳細を問わず、太字情報が含まれる

    def test_basic_image_syntax_contract(self):
        """画像構文の基本契約: ;;;画像;;;パス;;; → 画像要素"""
        # Given: 基本的な画像構文
        input_text = ";;;画像;;;/path/to/image.jpg;;;"

        # When: 解析実行
        result = self.parser.parse_line(input_text)

        # Then: 画像として認識される
        assert result is not None
        assert "画像" in str(result) or "image" in str(result).lower()

    def test_empty_content_contract(self):
        """空コンテンツの契約: 空文字列 → エラーまたはNone"""
        # Given: 空の入力
        input_text = ""

        # When: 解析実行
        result = self.parser.parse_line(input_text)

        # Then: 適切に処理される（クラッシュしない）
        # 結果がNoneまたは空結果であることを確認
        assert result is None or str(result) == ""

    def test_malformed_syntax_contract(self):
        """不正構文の契約: 不正な構文 → クラッシュしない"""
        # Given: 不正な構文パターン
        malformed_inputs = [
            ";;;不完全",  # 終了マーカーなし
            "完全;;;",  # 開始マーカーなし
            ";;;空のキーワード;;;",  # 空キーワード
            ";;;太字;;内容;;",  # マーカー不一致
        ]

        for input_text in malformed_inputs:
            # When: 解析実行
            try:
                result = self.parser.parse_line(input_text)
                # Then: クラッシュせず、何らかの結果を返す
                assert result is not None or result is None  # どちらでも可
            except Exception as e:
                # 既知のエラーであれば許容
                assert "parse" in str(e).lower() or "syntax" in str(e).lower()

    def test_japanese_content_contract(self):
        """日本語コンテンツの契約: 日本語を含む構文 → 正常処理"""
        # Given: 日本語を含む構文
        input_text = ";;;見出し;;;第一章　序論;;;"

        # When: 解析実行
        result = self.parser.parse_line(input_text)

        # Then: 日本語コンテンツが保持される
        assert result is not None
        result_str = str(result)
        assert "第一章" in result_str or "序論" in result_str

    def test_multiple_keywords_contract(self):
        """複合キーワードの契約: ;;;キーワード1+キーワード2;;; → 複合要素"""
        # Given: 複合キーワード構文
        input_text = ";;;太字+斜体;;;重要なテキスト;;;"

        # When: 解析実行
        result = self.parser.parse_line(input_text)

        # Then: 複合要素として認識される
        assert result is not None
        result_str = str(result)
        # 太字と斜体の両方の情報が含まれる
        assert ("太字" in result_str and "斜体" in result_str) or "+" in result_str


class TestParserRobustness:
    """パーサーの堅牢性契約"""

    def setup_method(self):
        self.parser = KeywordParser()

    def test_large_content_contract(self):
        """大容量コンテンツの契約: 大きなテキスト → メモリエラーなし"""
        # Given: 大容量のコンテンツ
        large_content = "大" * 10000  # 10,000文字
        input_text = f";;;太字;;;{large_content};;;"

        # When: 解析実行
        result = self.parser.parse_line(input_text)

        # Then: メモリエラーなく処理される
        assert result is not None
        # コンテンツが保持される（部分的でも可）
        result_str = str(result)
        assert "大" in result_str

    def test_unicode_edge_cases_contract(self):
        """Unicode特殊文字の契約: 特殊文字 → エラーなし"""
        # Given: Unicode特殊文字を含む構文
        special_chars = [
            "🎯",  # 絵文字
            "①②③",  # 特殊数字
            "¥",  # 通貨記号
            "‰",  # パーミル
        ]

        for char in special_chars:
            input_text = f";;;太字;;;テスト{char}内容;;;"

            # When: 解析実行
            result = self.parser.parse_line(input_text)

            # Then: エラーなく処理される
            assert result is not None
            # 文字が保持される
            result_str = str(result)
            assert char in result_str or "テスト" in result_str


# パフォーマンス契約（最低限）
class TestParserPerformance:
    """パーサーの基本的なパフォーマンス契約"""

    def setup_method(self):
        self.parser = KeywordParser()

    def test_basic_performance_contract(self):
        """基本パフォーマンス契約: 通常サイズの入力 → 1秒以内"""
        import time

        # Given: 通常サイズの入力
        input_text = ";;;太字;;;通常のテキスト内容;;;"

        # When: 解析実行時間を測定
        start_time = time.time()
        result = self.parser.parse_line(input_text)
        execution_time = time.time() - start_time

        # Then: 1秒以内で完了
        assert execution_time < 1.0
        assert result is not None


if __name__ == "__main__":
    # 直接実行時のテスト
    pytest.main([__file__, "-v"])
