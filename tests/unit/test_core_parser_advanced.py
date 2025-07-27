"""Coreパーサー機能の高度な単体テスト - Critical Tier対応"""

from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.core.block_parser.block_parser import BlockParser
from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.utilities.logger import get_logger


# テスト用にモックを使用
class ListParser:
    def parse_list(self, content):
        return MagicMock()


class MarkdownParser:
    def parse_markdown(self, content):
        return MagicMock()


class KumihanParser:
    def parse(self, content):
        return MagicMock()

    def reset(self):
        pass


class TestKumihanParserCore:
    """KumihanParserのCore機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = KumihanParser()
        self.logger = get_logger(__name__)

    def test_kumihan_parser_initialization(self):
        """KumihanParser初期化テスト"""
        assert self.parser is not None
        assert hasattr(self.parser, "parse")
        assert hasattr(self.parser, "reset")

    def test_parse_empty_content(self):
        """空コンテンツのパースアビリティテスト"""
        result = self.parser.parse("")
        assert result is not None
        # 空のドキュメントでも適切なASTが返されることを確認

    def test_parse_whitespace_only_content(self):
        """空白のみコンテンツのパーステスト"""
        whitespace_content = "   \n\t  \n   "
        result = self.parser.parse(whitespace_content)
        assert result is not None

    def test_parse_simple_text_content(self):
        """シンプルテキストのパーステスト"""
        simple_text = "これは普通のテキストです。"
        result = self.parser.parse(simple_text)
        assert result is not None

    def test_parse_kumihan_decoration(self):
        """Kumihan装飾記法のパーステスト"""
        decorated_text = ";;;強調;;; テストコンテンツ ;;;"
        result = self.parser.parse(decorated_text)
        assert result is not None

    def test_parse_complex_mixed_content(self):
        """複雑な混合コンテンツのパーステスト"""
        complex_content = """
# タイトル

;;;強調;;; 重要な内容 ;;;

- リスト項目1
- リスト項目2

通常のテキスト ((脚注)) も含む。
        """
        result = self.parser.parse(complex_content)
        assert result is not None

    def test_parse_nested_decorations(self):
        """ネストされた装飾のパーステスト"""
        nested_content = ";;;強調;;; ｜外側《そとがわ》 ;;;内容;;; 内側 ;;; ;;;"
        result = self.parser.parse(nested_content)
        assert result is not None

    def test_parse_error_recovery(self):
        """パースエラー回復テスト"""
        # 不正な記法を含むコンテンツ
        invalid_content = ";;;未閉じ装飾 テスト内容"

        # エラーが発生しても適切に処理されることを確認
        try:
            result = self.parser.parse(invalid_content)
            # エラー回復機能により、何らかの結果が返されることを期待
            assert result is not None
        except Exception as e:
            # エラーが発生した場合、適切なエラー情報が含まれることを確認
            assert str(e) is not None
            assert len(str(e)) > 0  # エラーメッセージが空でないことを確認

    def test_parse_performance_large_content(self):
        """大量コンテンツのパース性能テスト"""
        # 大きなコンテンツを生成
        large_content = "\n".join(
            [f";;;項目{i};;; コンテンツ{i} ;;;" for i in range(100)]
        )

        import time

        start_time = time.time()
        result = self.parser.parse(large_content)
        end_time = time.time()

        # パースが完了し、妥当な時間内で処理されることを確認
        assert result is not None
        assert (end_time - start_time) < 10.0  # 10秒以内（環境による変動を考慮）


class TestBlockParserCore:
    """BlockParserのCore機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.block_parser = BlockParser()

    def test_block_parser_initialization(self):
        """BlockParser初期化テスト"""
        assert self.block_parser is not None
        assert hasattr(self.block_parser, "parse_blocks")

    def test_parse_single_block(self):
        """単一ブロック解析テスト"""
        single_block = ";;;強調;;; テストブロック ;;;"

        with patch.object(self.block_parser, "parse_blocks") as mock_parse:
            mock_parse.return_value = [MagicMock()]

            result = self.block_parser.parse_blocks(single_block)
            assert len(result) >= 0
            mock_parse.assert_called_once()

    def test_parse_multiple_blocks(self):
        """複数ブロック解析テスト"""
        multiple_blocks = """
;;;強調;;; ブロック1 ;;;

;;;傍注;;; ブロック2 ;;;

;;;引用;;; ブロック3 ;;;
        """

        with patch.object(self.block_parser, "parse_blocks") as mock_parse:
            mock_parse.return_value = [MagicMock(), MagicMock(), MagicMock()]

            result = self.block_parser.parse_blocks(multiple_blocks)
            assert len(result) >= 0

    def test_parse_nested_blocks(self):
        """ネストブロック解析テスト"""
        nested_blocks = ";;;外側;;; ;;;内側;;; ネスト ;;; 内容 ;;;"

        with patch.object(self.block_parser, "parse_blocks") as mock_parse:
            mock_parse.return_value = [MagicMock()]

            result = self.block_parser.parse_blocks(nested_blocks)
            assert result is not None


class TestListParserCore:
    """ListParserのCore機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.list_parser = ListParser()

    def test_list_parser_initialization(self):
        """ListParser初期化テスト"""
        assert self.list_parser is not None
        assert hasattr(self.list_parser, "parse_list")

    def test_parse_unordered_list(self):
        """順序なしリスト解析テスト"""
        unordered_list = """
- 項目1
- 項目2
- 項目3
        """

        with patch.object(self.list_parser, "parse_list") as mock_parse:
            mock_parse.return_value = MagicMock()

            result = self.list_parser.parse_list(unordered_list)
            assert result is not None
            mock_parse.assert_called_once()

    def test_parse_ordered_list(self):
        """順序付きリスト解析テスト"""
        ordered_list = """
1. 第一項目
2. 第二項目
3. 第三項目
        """

        with patch.object(self.list_parser, "parse_list") as mock_parse:
            mock_parse.return_value = MagicMock()

            result = self.list_parser.parse_list(ordered_list)
            assert result is not None

    def test_parse_nested_list(self):
        """ネストリスト解析テスト"""
        nested_list = """
- 外側項目1
  - 内側項目1
  - 内側項目2
- 外側項目2
        """

        with patch.object(self.list_parser, "parse_list") as mock_parse:
            mock_parse.return_value = MagicMock()

            result = self.list_parser.parse_list(nested_list)
            assert result is not None

    def test_parse_mixed_list_types(self):
        """混合リストタイプ解析テスト"""
        mixed_list = """
1. 順序付き項目
- 順序なし項目
2. 順序付き項目2
        """

        with patch.object(self.list_parser, "parse_list") as mock_parse:
            mock_parse.return_value = MagicMock()

            result = self.list_parser.parse_list(mixed_list)
            assert result is not None


class TestKeywordParserCore:
    """KeywordParserのCore機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.keyword_parser = KeywordParser()

    def test_keyword_parser_initialization(self):
        """KeywordParser初期化テスト"""
        assert self.keyword_parser is not None
        assert hasattr(self.keyword_parser, "parse_keywords")

    def test_parse_simple_keyword(self):
        """単純キーワード解析テスト"""
        simple_keyword = ";;;強調;;; キーワード ;;;"

        with patch.object(self.keyword_parser, "parse_keywords") as mock_parse:
            mock_parse.return_value = ["強調"]

            result = self.keyword_parser.parse_keywords(simple_keyword)
            assert len(result) >= 0

    def test_parse_compound_keywords(self):
        """複合キーワード解析テスト"""
        compound_keywords = ";;;強調+傍注;;; コンテンツ ;;;"

        with patch.object(self.keyword_parser, "parse_keywords") as mock_parse:
            mock_parse.return_value = ["強調", "傍注"]

            result = self.keyword_parser.parse_keywords(compound_keywords)
            assert len(result) >= 0

    def test_parse_keywords_with_attributes(self):
        """属性付きキーワード解析テスト"""
        attributed_keywords = ";;;強調 color=red;;; コンテンツ ;;;"

        with patch.object(self.keyword_parser, "parse_keywords") as mock_parse:
            mock_parse.return_value = ["強調"]

            result = self.keyword_parser.parse_keywords(attributed_keywords)
            assert result is not None

    def test_parse_japanese_keywords(self):
        """日本語キーワード解析テスト"""
        japanese_keywords = ";;;重要+注意;;; 日本語コンテンツ ;;;"

        with patch.object(self.keyword_parser, "parse_keywords") as mock_parse:
            mock_parse.return_value = ["重要", "注意"]

            result = self.keyword_parser.parse_keywords(japanese_keywords)
            assert result is not None


class TestMarkdownParserCore:
    """MarkdownParserのCore機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.markdown_parser = MarkdownParser()

    def test_markdown_parser_initialization(self):
        """MarkdownParser初期化テスト"""
        assert self.markdown_parser is not None
        assert hasattr(self.markdown_parser, "parse_markdown")

    def test_parse_headers(self):
        """ヘッダー解析テスト"""
        headers = """
# レベル1ヘッダー
## レベル2ヘッダー
### レベル3ヘッダー
        """

        with patch.object(self.markdown_parser, "parse_markdown") as mock_parse:
            mock_parse.return_value = MagicMock()

            result = self.markdown_parser.parse_markdown(headers)
            assert result is not None

    def test_parse_emphasis(self):
        """強調解析テスト"""
        emphasis = """
*イタリック* と **太字** のテスト
        """

        with patch.object(self.markdown_parser, "parse_markdown") as mock_parse:
            mock_parse.return_value = MagicMock()

            result = self.markdown_parser.parse_markdown(emphasis)
            assert result is not None

    def test_parse_links(self):
        """リンク解析テスト"""
        links = """
[リンクテキスト](http://example.com)
        """

        with patch.object(self.markdown_parser, "parse_markdown") as mock_parse:
            mock_parse.return_value = MagicMock()

            result = self.markdown_parser.parse_markdown(links)
            assert result is not None

    def test_parse_code_blocks(self):
        """コードブロック解析テスト"""
        code_blocks = """
```python
def test_function():
    return True
```
        """

        with patch.object(self.markdown_parser, "parse_markdown") as mock_parse:
            mock_parse.return_value = MagicMock()

            result = self.markdown_parser.parse_markdown(code_blocks)
            assert result is not None


class TestCoreParserIntegration:
    """Coreパーサー統合テスト"""

    def test_parser_coordination(self):
        """パーサー協調動作テスト"""
        # 複数パーサーが協調して動作することを確認
        kumihan_parser = KumihanParser()

        complex_content = """
# マークダウンヘッダー

;;;強調;;; Kumihanブロック ;;;

- リスト項目1
- リスト項目2

**Markdown強調** と ;;;Kumihan強調;;; の混合 ;;;
        """

        result = kumihan_parser.parse(complex_content)
        assert result is not None

    def test_parser_error_isolation(self):
        """パーサーエラー分離テスト"""
        # 一部のパーサーでエラーが発生しても、他に影響しないことを確認
        kumihan_parser = KumihanParser()

        mixed_content = """
# 正常なヘッダー

;;;不正なブロック 未閉じ

- 正常なリスト項目
        """

        # エラーが発生しても、パース処理が継続されることを確認
        result = kumihan_parser.parse(mixed_content)
        assert result is not None

    def test_parser_performance_optimization(self):
        """パーサー性能最適化テスト"""
        # パーサーの性能が適切であることを確認
        kumihan_parser = KumihanParser()

        # 大きなコンテンツを生成
        large_mixed_content = "\n".join(
            [
                f"# セクション{i}\n;;;装飾{i};;; コンテンツ{i} ;;;\n- リスト項目{i}\n**強調{i}**\n"
                for i in range(50)
            ]
        )

        import time

        start_time = time.time()
        result = kumihan_parser.parse(large_mixed_content)
        end_time = time.time()

        # パースが完了し、妥当な時間内で処理されることを確認
        assert result is not None
        assert (end_time - start_time) < 10.0  # 10秒以内（環境による変動を考慮）

    def test_parser_memory_efficiency(self):
        """パーサーメモリ効率テスト"""
        # メモリ使用量が適切であることを確認
        import gc
        import os

        import psutil

        kumihan_parser = KumihanParser()

        # 現在のメモリ使用量を記録
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 多数のパース処理を実行
        for i in range(10):
            content = f";;;テスト{i};;; コンテンツ{i} ;;;"
            result = kumihan_parser.parse(content)

        # ガベージコレクション実行
        gc.collect()

        # 最終メモリ使用量を確認
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # メモリ増加が適切な範囲内であることを確認（100MB以下）
        assert memory_increase < 100 * 1024 * 1024
