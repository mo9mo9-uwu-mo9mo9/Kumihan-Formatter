"""
プロトコル適合性テスト (Issue #914 Phase 1)

統一パーサープロトコルへの適合性を検証
全UnifiedParserクラスがBaseParserProtocol/特化プロトコルに適合することを確認
"""

import pytest
from typing import Any, Dict, List
from unittest.mock import Mock

from kumihan_formatter.parsers import (
    MainParser,
    BlockParser, 
    KeywordParser,
    ListParser,
    ContentParser,
    MarkdownParser,
    StreamingParser
)
from kumihan_formatter.core.parsing.base.parser_protocols import (
    BaseParserProtocol,
    BlockParserProtocol,
    KeywordParserProtocol,
    ListParserProtocol,
    MarkdownParserProtocol,
    StreamingParserProtocol,
    ParseResult,
    ParseContext,
    validate_parser_implementation
)


class TestProtocolCompliance:
    """プロトコル適合性テスト"""

    @pytest.mark.unit
    def test_main_parser_protocol_compliance(self):
        """UnifiedMainParserのBaseParserProtocol適合性テスト"""
        parser = MainParser()
        
        # プロトコル適合性チェック
        assert isinstance(parser, BaseParserProtocol)
        
        # 必須メソッドの存在確認
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'validate')
        assert hasattr(parser, 'get_parser_info')
        assert hasattr(parser, 'supports_format')
        
        # メソッドが呼び出し可能
        assert callable(parser.parse)
        assert callable(parser.validate)
        assert callable(parser.get_parser_info)
        assert callable(parser.supports_format)

    @pytest.mark.unit
    def test_block_parser_protocol_compliance(self):
        """UnifiedBlockParserのBlockParserProtocol適合性テスト"""
        parser = BlockParser()
        
        # プロトコル適合性チェック
        assert isinstance(parser, BlockParserProtocol)
        assert isinstance(parser, BaseParserProtocol)
        
        # BlockParserProtocol特化メソッド
        assert hasattr(parser, 'parse_block')
        assert hasattr(parser, 'extract_blocks')
        assert hasattr(parser, 'detect_block_type')
        
        assert callable(parser.parse_block)
        assert callable(parser.extract_blocks)
        assert callable(parser.detect_block_type)

    @pytest.mark.unit
    def test_keyword_parser_protocol_compliance(self):
        """UnifiedKeywordParserのKeywordParserProtocol適合性テスト"""
        parser = KeywordParser()
        
        # プロトコル適合性チェック
        assert isinstance(parser, KeywordParserProtocol)
        assert isinstance(parser, BaseParserProtocol)
        
        # KeywordParserProtocol特化メソッド
        assert hasattr(parser, 'parse_keywords')
        assert hasattr(parser, 'parse_marker_keywords')
        assert hasattr(parser, 'validate_keyword')
        assert hasattr(parser, 'parse_new_format')
        assert hasattr(parser, 'get_node_factory')
        assert hasattr(parser, 'split_compound_keywords')

    @pytest.mark.unit
    def test_list_parser_protocol_compliance(self):
        """UnifiedListParserのListParserProtocol適合性テスト"""
        parser = ListParser()
        
        # プロトコル適合性チェック
        assert isinstance(parser, ListParserProtocol)
        assert isinstance(parser, BaseParserProtocol)
        
        # ListParserProtocol特化メソッド
        assert hasattr(parser, 'parse_list_items')
        assert hasattr(parser, 'parse_nested_list')
        assert hasattr(parser, 'detect_list_type')
        assert hasattr(parser, 'get_list_nesting_level')

    @pytest.mark.unit
    def test_markdown_parser_protocol_compliance(self):
        """UnifiedMarkdownParserのMarkdownParserProtocol適合性テスト"""
        parser = MarkdownParser()
        
        # プロトコル適合性チェック
        assert isinstance(parser, MarkdownParserProtocol)
        assert isinstance(parser, BaseParserProtocol)
        
        # MarkdownParserProtocol特化メソッド
        assert hasattr(parser, 'parse_markdown_elements')
        assert hasattr(parser, 'convert_to_kumihan')
        assert hasattr(parser, 'detect_markdown_elements')

    @pytest.mark.unit
    def test_content_parser_protocol_compliance(self):
        """UnifiedContentParserのBaseParserProtocol適合性テスト"""
        parser = ContentParser()
        
        # プロトコル適合性チェック
        assert isinstance(parser, BaseParserProtocol)

    @pytest.mark.unit
    def test_streaming_parser_protocol_compliance(self):
        """UnifiedStreamingParserのStreamingParserProtocol適合性テスト"""
        parser = StreamingParser()
        
        # プロトコル適合性チェック
        assert isinstance(parser, StreamingParserProtocol)
        
        # StreamingParserProtocol特化メソッド
        assert hasattr(parser, 'parse_streaming')
        assert hasattr(parser, 'process_chunk')
        assert hasattr(parser, 'get_chunk_size')
        assert hasattr(parser, 'supports_streaming')


class TestParserMethodSignatures:
    """パーサーメソッドシグネチャテスト"""

    @pytest.mark.unit
    def test_parse_method_signatures(self):
        """parseメソッドのシグネチャ統一性テスト"""
        parsers = [
            MainParser(),
            BlockParser(),
            KeywordParser(),
            ListParser(),
            ContentParser(),
            MarkdownParser(),
            StreamingParser()
        ]
        
        for parser in parsers:
            # parseメソッドの戻り値型テスト
            result = parser.parse("test content")
            assert isinstance(result, ParseResult), f"{parser.__class__.__name__}.parse() must return ParseResult"
            
            # ParseResultの必須フィールド確認
            assert hasattr(result, 'success')
            assert hasattr(result, 'nodes')
            assert hasattr(result, 'errors')
            assert hasattr(result, 'warnings')
            assert hasattr(result, 'metadata')

    @pytest.mark.unit
    def test_validate_method_signatures(self):
        """validateメソッドのシグネチャ統一性テスト"""
        parsers = [
            MainParser(),
            BlockParser(),
            KeywordParser(),
            ListParser(),
            ContentParser(),
            MarkdownParser(),
            StreamingParser()
        ]
        
        for parser in parsers:
            # validateメソッドの戻り値型テスト
            result = parser.validate("test content")
            assert isinstance(result, list), f"{parser.__class__.__name__}.validate() must return List[str]"
            
            # エラーリストの要素型確認
            for error in result:
                assert isinstance(error, str), "Validation errors must be strings"

    @pytest.mark.unit
    def test_get_parser_info_signatures(self):
        """get_parser_infoメソッドのシグネチャ統一性テスト"""
        parsers = [
            MainParser(),
            BlockParser(),
            KeywordParser(),
            ListParser(),
            ContentParser(),
            MarkdownParser(),
            StreamingParser()
        ]
        
        required_keys = ["name", "version", "supported_formats", "capabilities"]
        
        for parser in parsers:
            info = parser.get_parser_info()
            assert isinstance(info, dict), f"{parser.__class__.__name__}.get_parser_info() must return dict"
            
            # 必須キーの存在確認
            for key in required_keys:
                assert key in info, f"{parser.__class__.__name__}.get_parser_info() missing key: {key}"
            
            # データ型の確認
            assert isinstance(info["name"], str)
            assert isinstance(info["version"], str)
            assert isinstance(info["supported_formats"], list)
            assert isinstance(info["capabilities"], list)


class TestParserValidationFramework:
    """パーサー検証フレームワークテスト"""

    @pytest.mark.unit
    def test_validate_parser_implementation_function(self):
        """validate_parser_implementation関数のテスト"""
        parser = MainParser()
        
        # 検証実行
        issues = validate_parser_implementation(parser)
        
        # 戻り値型確認
        assert isinstance(issues, list)
        
        # 問題がない場合は空リスト
        assert len(issues) == 0, f"Parser implementation issues found: {issues}"

    @pytest.mark.unit
    def test_invalid_parser_detection(self):
        """不正なパーサー実装の検出テスト"""
        # 不正なパーサーモック
        class InvalidParser:
            def parse(self, content: str) -> str:  # 間違った戻り値型
                return "invalid"
            
            def get_parser_info(self) -> str:  # 間違った戻り値型
                return "invalid"
        
        invalid_parser = InvalidParser()
        issues = validate_parser_implementation(invalid_parser)
        
        # 問題が検出されること
        assert len(issues) > 0
        assert any("get_parser_info() must return dict" in issue for issue in issues)


class TestParseResultAndContext:
    """ParseResultとParseContextのテスト"""

    @pytest.mark.unit
    def test_parse_result_creation(self):
        """ParseResult作成テスト"""
        from kumihan_formatter.core.parsing.base.parser_protocols import create_parse_result
        
        result = create_parse_result(nodes=[], success=True)
        
        assert isinstance(result, ParseResult)
        assert result.success is True
        assert isinstance(result.nodes, list)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.metadata, dict)

    @pytest.mark.unit
    def test_parse_context_creation(self):
        """ParseContext作成テスト"""
        from kumihan_formatter.core.parsing.base.parser_protocols import create_parse_context
        
        context = create_parse_context(source_file="test.md", line_number=10)
        
        assert isinstance(context, ParseContext)
        assert context.source_file == "test.md"
        assert context.line_number == 10
        assert isinstance(context.config, dict)
        assert isinstance(context.parser_state, dict)

    @pytest.mark.unit
    def test_parse_result_error_handling(self):
        """ParseResultエラーハンドリングテスト"""
        result = ParseResult(
            success=True,
            nodes=[],
            errors=[],
            warnings=[],
            metadata={}
        )
        
        # エラー追加テスト
        result.add_error("Test error")
        assert result.success is False
        assert "Test error" in result.errors
        
        # 警告追加テスト
        result.add_warning("Test warning")
        assert "Test warning" in result.warnings
        
        # has_issues テスト
        assert result.has_issues() is True


class TestProtocolInheritance:
    """プロトコル継承テスト"""

    @pytest.mark.unit
    def test_specialized_protocols_inherit_base(self):
        """特化プロトコルがBaseParserProtocolを継承することを確認"""
        # BlockParserProtocol
        assert issubclass(BlockParserProtocol, BaseParserProtocol)
        
        # KeywordParserProtocol
        assert issubclass(KeywordParserProtocol, BaseParserProtocol)
        
        # ListParserProtocol
        assert issubclass(ListParserProtocol, BaseParserProtocol)
        
        # MarkdownParserProtocol
        assert issubclass(MarkdownParserProtocol, BaseParserProtocol)

    @pytest.mark.unit
    def test_parser_implementations_follow_hierarchy(self):
        """パーサー実装がプロトコル階層に従うことを確認"""
        # BlockParser
        block_parser = BlockParser()
        assert isinstance(block_parser, BaseParserProtocol)
        assert isinstance(block_parser, BlockParserProtocol)
        
        # KeywordParser
        keyword_parser = KeywordParser()
        assert isinstance(keyword_parser, BaseParserProtocol)
        assert isinstance(keyword_parser, KeywordParserProtocol)
        
        # ListParser
        list_parser = ListParser()
        assert isinstance(list_parser, BaseParserProtocol)
        assert isinstance(list_parser, ListParserProtocol)
        
        # MarkdownParser
        markdown_parser = MarkdownParser()
        assert isinstance(markdown_parser, BaseParserProtocol)
        assert isinstance(markdown_parser, MarkdownParserProtocol)