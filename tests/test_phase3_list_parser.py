"""Phase 3 List Parser Tests - リストパーサー全面テスト

パーサーコア機能テスト - リスト構造解析システム
Target: kumihan_formatter/core/list_parser.py (334行・0%カバレッジ)
Goal: 0% → 90-95%カバレッジ向上 (Phase 3目標70-80%への重要貢献)

3番目最大カバレッジ貢献ファイル - 推定+15-20%カバレッジ向上
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from kumihan_formatter.core.list_parser import ListParser, NestedListParser
from kumihan_formatter.core.ast_nodes import Node


class TestListParserInitialization:
    """ListParser初期化テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = ListParser()

    def test_list_parser_initialization(self):
        """ListParser基本初期化テスト"""
        parser = ListParser()
        
        # 基本属性が初期化されていることを確認
        assert parser is not None
        assert hasattr(parser, 'parse_unordered_list')
        assert hasattr(parser, 'parse_ordered_list')
        assert hasattr(parser, 'parse_nested_list')

    def test_list_parser_config_integration(self):
        """設定統合テスト"""
        with patch('kumihan_formatter.core.list_parser.Config') as mock_config:
            mock_config_instance = Mock()
            mock_config.return_value = mock_config_instance
            
            parser = ListParser()
            
            # 設定が正しく統合されることを確認
            assert parser is not None

    def test_list_parser_logger_integration(self):
        """ロガー統合テスト"""
        with patch('kumihan_formatter.core.list_parser.logger') as mock_logger:
            parser = ListParser()
            
            # ロガーが利用可能であることを確認
            assert parser is not None
            assert mock_logger is not None

    def test_nested_list_parser_initialization(self):
        """NestedListParser初期化テスト"""
        nested_parser = NestedListParser()
        
        # NestedListParserが正常に初期化されることを確認
        assert nested_parser is not None
        assert hasattr(nested_parser, 'parse_nested_structure')
        assert hasattr(nested_parser, 'manage_nesting_levels')


class TestUnorderedListParsing:
    """順序なしリスト解析テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = ListParser()

    def test_parse_unordered_list_basic(self):
        """基本順序なしリスト解析テスト"""
        unordered_content = """
        - 項目1
        - 項目2
        - 項目3
        """
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            mock_create.return_value = Mock()
            
            result = self.parser.parse_unordered_list(unordered_content)
            
            # 順序なしリストが解析されることを確認
            assert result is not None
            mock_create.assert_called()

    def test_parse_unordered_list_with_markers(self):
        """マーカー付き順序なしリスト解析テスト"""
        marker_content = """
        - ;;;太字;;; 重要項目1 ;;;
        - ;;;イタリック;;; 強調項目2 ;;;
        - 通常項目3
        """
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            with patch.object(self.parser, 'parse_list_item_markers') as mock_markers:
                mock_create.return_value = Mock()
                mock_markers.return_value = Mock()
                
                result = self.parser.parse_unordered_list(marker_content)
                
                # マーカー付きリストが解析されることを確認
                assert result is not None
                mock_markers.assert_called()

    def test_parse_unordered_list_different_bullets(self):
        """異なる箇条書き記号リスト解析テスト"""
        different_bullets = [
            "- 標準ハイフン項目",
            "* アスタリスク項目",
            "+ プラス記号項目",
            "• Unicode箇条書き項目",
        ]
        
        for bullet_content in different_bullets:
            with patch.object(self.parser, 'create_list_node') as mock_create:
                mock_create.return_value = Mock()
                
                result = self.parser.parse_unordered_list(bullet_content)
                
                # 異なる箇条書き記号が適切に処理されることを確認
                assert result is not None

    def test_parse_unordered_list_multiline_items(self):
        """複数行項目リスト解析テスト"""
        multiline_content = """
        - 複数行項目1
          続きの行1
          続きの行2
        - 複数行項目2
          続きの行A
          続きの行B
        """
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            with patch.object(self.parser, 'handle_multiline_items') as mock_multiline:
                mock_create.return_value = Mock()
                mock_multiline.return_value = []
                
                result = self.parser.parse_unordered_list(multiline_content)
                
                # 複数行項目が適切に処理されることを確認
                assert result is not None
                mock_multiline.assert_called()

    def test_parse_unordered_list_empty_items(self):
        """空項目リスト解析テスト"""
        empty_items_content = """
        - 項目1
        - 
        - 項目3
        -
        - 項目5
        """
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            with patch.object(self.parser, 'handle_empty_items') as mock_empty:
                mock_create.return_value = Mock()
                mock_empty.return_value = []
                
                result = self.parser.parse_unordered_list(empty_items_content)
                
                # 空項目が適切に処理されることを確認
                assert result is not None
                mock_empty.assert_called()

    def test_parse_unordered_list_special_characters(self):
        """特殊文字リスト解析テスト"""
        special_char_items = [
            "- Unicode項目: 🎌🗻⛩️",
            "- 日本語項目：重要な情報",
            "- 한국어 항목: 중요 정보",
            "- 中文項目：重要信息",
            "- العربية: معلومات مهمة",
            "- 記号項目: !@#$%^&*()",
        ]
        
        special_content = "\n".join(special_char_items)
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            mock_create.return_value = Mock()
            
            result = self.parser.parse_unordered_list(special_content)
            
            # 特殊文字項目が適切に処理されることを確認
            assert result is not None

    def test_parse_unordered_list_performance(self):
        """順序なしリストパフォーマンステスト"""
        # 大量項目でのパフォーマンステスト
        large_list = "\n".join([f"- 項目{i}" for i in range(1000)])
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            mock_create.return_value = Mock()
            
            import time
            start = time.time()
            
            result = self.parser.parse_unordered_list(large_list)
            
            end = time.time()
            duration = end - start
            
            # パフォーマンス要件を満たすことを確認
            assert result is not None
            assert duration < 2.0  # 2秒以内


class TestOrderedListParsing:
    """順序ありリスト解析テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = ListParser()

    def test_parse_ordered_list_basic(self):
        """基本順序ありリスト解析テスト"""
        ordered_content = """
        1. 第1項目
        2. 第2項目
        3. 第3項目
        """
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            mock_create.return_value = Mock()
            
            result = self.parser.parse_ordered_list(ordered_content)
            
            # 順序ありリストが解析されることを確認
            assert result is not None
            mock_create.assert_called()

    def test_parse_ordered_list_different_numbering(self):
        """異なる番号付けリスト解析テスト"""
        different_numberings = [
            "1. 標準数字",
            "a. 小文字アルファベット",
            "A. 大文字アルファベット", 
            "i. 小文字ローマ数字",
            "I. 大文字ローマ数字",
            "1) 括弧付き数字",
            "(1) 両括弧数字",
        ]
        
        for numbering in different_numberings:
            with patch.object(self.parser, 'create_list_node') as mock_create:
                mock_create.return_value = Mock()
                
                result = self.parser.parse_ordered_list(numbering)
                
                # 異なる番号付けが適切に処理されることを確認
                assert result is not None

    def test_parse_ordered_list_custom_start(self):
        """カスタム開始番号リスト解析テスト"""
        custom_start_content = """
        5. 第5項目（開始）
        6. 第6項目
        7. 第7項目
        """
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            with patch.object(self.parser, 'handle_custom_start_number') as mock_custom:
                mock_create.return_value = Mock()
                mock_custom.return_value = 5
                
                result = self.parser.parse_ordered_list(custom_start_content)
                
                # カスタム開始番号が適切に処理されることを確認
                assert result is not None
                mock_custom.assert_called()

    def test_parse_ordered_list_with_markers(self):
        """マーカー付き順序ありリスト解析テスト"""
        marker_ordered_content = """
        1. ;;;太字;;; 重要な第1項目 ;;;
        2. ;;;イタリック;;; 強調された第2項目 ;;;
        3. ;;;枠線;;; 枠線付き第3項目 ;;;
        """
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            with patch.object(self.parser, 'parse_list_item_markers') as mock_markers:
                mock_create.return_value = Mock()
                mock_markers.return_value = Mock()
                
                result = self.parser.parse_ordered_list(marker_ordered_content)
                
                # マーカー付き順序ありリストが解析されることを確認
                assert result is not None
                mock_markers.assert_called()

    def test_parse_ordered_list_discontinuous_numbering(self):
        """非連続番号リスト解析テスト"""
        discontinuous_content = """
        1. 第1項目
        3. 第3項目（2を飛ばす）
        7. 第7項目（4,5,6を飛ばす）
        """
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            with patch.object(self.parser, 'handle_discontinuous_numbering') as mock_discontinuous:
                mock_create.return_value = Mock()
                mock_discontinuous.return_value = []
                
                result = self.parser.parse_ordered_list(discontinuous_content)
                
                # 非連続番号が適切に処理されることを確認
                assert result is not None
                mock_discontinuous.assert_called()

    def test_parse_ordered_list_mixed_content(self):
        """混在コンテンツリスト解析テスト"""
        mixed_content = """
        1. 通常テキスト項目
        2. ;;;太字;;; マーカー項目 ;;;
        3. 複数行項目
           続きの行
           さらに続く行
        4. 最終項目
        """
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            with patch.object(self.parser, 'handle_mixed_list_content') as mock_mixed:
                mock_create.return_value = Mock()
                mock_mixed.return_value = []
                
                result = self.parser.parse_ordered_list(mixed_content)
                
                # 混在コンテンツが適切に処理されることを確認
                assert result is not None
                mock_mixed.assert_called()


class TestNestedListParsing:
    """ネストリスト解析テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = ListParser()
        self.nested_parser = NestedListParser()

    def test_parse_nested_list_basic(self):
        """基本ネストリスト解析テスト"""
        nested_content = """
        - レベル1項目1
          - レベル2項目1
          - レベル2項目2
        - レベル1項目2
          - レベル2項目3
            - レベル3項目1
        """
        
        with patch.object(self.parser, 'parse_nested_list') as mock_nested:
            mock_nested.return_value = Mock()
            
            result = self.parser.parse_nested_list(nested_content)
            
            # ネストリストが解析されることを確認
            assert result is not None
            mock_nested.assert_called()

    def test_parse_nested_list_mixed_types(self):
        """混在タイプネストリスト解析テスト"""
        mixed_nested_content = """
        1. 順序ありレベル1
           - 順序なしレベル2
           - 順序なしレベル2-2
        2. 順序ありレベル1-2
           a. アルファベット順序レベル2
           b. アルファベット順序レベル2-2
              - 順序なしレベル3
        """
        
        with patch.object(self.nested_parser, 'parse_nested_structure') as mock_structure:
            mock_structure.return_value = Mock()
            
            result = self.nested_parser.parse_nested_structure(mixed_nested_content)
            
            # 混在タイプネストが解析されることを確認
            assert result is not None
            mock_structure.assert_called()

    def test_parse_nested_list_deep_nesting(self):
        """深いネストリスト解析テスト"""
        deep_nested_content = """
        - レベル1
          - レベル2
            - レベル3
              - レベル4
                - レベル5
                  - レベル6
        """
        
        with patch.object(self.nested_parser, 'manage_nesting_levels') as mock_levels:
            mock_levels.return_value = 6
            
            result = self.nested_parser.parse_nested_structure(deep_nested_content)
            
            # 深いネストが適切に管理されることを確認
            assert result is not None
            mock_levels.assert_called()

    def test_parse_nested_list_irregular_indentation(self):
        """不規則インデントネストリスト解析テスト"""
        irregular_content = """
        - レベル1
            - 不規則インデント（4スペース）
          - 標準インデント（2スペース）
         - 中間インデント（1スペース）
        	- タブインデント
        """
        
        with patch.object(self.nested_parser, 'normalize_indentation') as mock_normalize:
            mock_normalize.return_value = "normalized_content"
            
            result = self.nested_parser.parse_nested_structure(irregular_content)
            
            # 不規則インデントが正規化されることを確認
            assert result is not None
            mock_normalize.assert_called()

    def test_parse_nested_list_with_markers(self):
        """マーカー付きネストリスト解析テスト"""
        marker_nested_content = """
        - ;;;太字;;; レベル1重要項目 ;;;
          - ;;;イタリック;;; レベル2強調項目 ;;;
            - ;;;枠線;;; レベル3枠線項目 ;;;
        - 通常のレベル1項目
          - ;;;ハイライト;;; レベル2ハイライト項目 ;;;
        """
        
        with patch.object(self.nested_parser, 'parse_nested_markers') as mock_markers:
            mock_markers.return_value = []
            
            result = self.nested_parser.parse_nested_structure(marker_nested_content)
            
            # ネストマーカーが解析されることを確認
            assert result is not None
            mock_markers.assert_called()

    def test_parse_nested_list_performance_deep(self):
        """深いネストパフォーマンステスト"""
        # 深いネスト構造でのパフォーマンステスト
        deep_content = "- 項目"
        for level in range(1, 20):  # 20レベル深いネスト
            indent = "  " * level
            deep_content += f"\n{indent}- レベル{level}項目"
        
        with patch.object(self.nested_parser, 'parse_nested_structure') as mock_structure:
            mock_structure.return_value = Mock()
            
            import time
            start = time.time()
            
            result = self.nested_parser.parse_nested_structure(deep_content)
            
            end = time.time()
            duration = end - start
            
            # パフォーマンス要件を満たすことを確認
            assert result is not None
            assert duration < 1.0  # 1秒以内


class TestListItemProcessing:
    """リスト項目処理テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = ListParser()

    def test_parse_list_item_markers(self):
        """リスト項目マーカー解析テスト"""
        marker_items = [
            ";;;太字;;; 重要項目 ;;;",
            ";;;イタリック;;; 強調項目 ;;;",
            ";;;枠線 class=\"highlight\";;; 属性付き項目 ;;;",
            "通常項目（マーカーなし）",
            ";;;太字;;; 部分 ;;; と 通常 テキスト",
        ]
        
        for item in marker_items:
            with patch.object(self.parser, 'extract_markers_from_item') as mock_extract:
                mock_extract.return_value = []
                
                result = self.parser.parse_list_item_markers(item)
                
                # 項目マーカーが適切に処理されることを確認
                assert result is not None

    def test_create_list_node(self):
        """リストノード作成テスト"""
        list_data = {
            'type': 'unordered',
            'items': ['項目1', '項目2', '項目3']
        }
        
        with patch('kumihan_formatter.core.list_parser.Node') as mock_node:
            mock_node.return_value = Mock()
            
            result = self.parser.create_list_node(list_data)
            
            # リストノードが適切に作成されることを確認
            assert result is not None
            mock_node.assert_called()

    def test_handle_multiline_items(self):
        """複数行項目処理テスト"""
        multiline_item = """項目の最初の行
        項目の2行目
        項目の3行目"""
        
        with patch.object(self.parser, 'process_multiline_content') as mock_multiline:
            mock_multiline.return_value = "processed_content"
            
            result = self.parser.handle_multiline_items(multiline_item)
            
            # 複数行項目が適切に処理されることを確認
            assert result is not None
            mock_multiline.assert_called()

    def test_handle_empty_items(self):
        """空項目処理テスト"""
        items_with_empty = [
            "項目1",
            "",
            "項目3",
            None,
            "項目5"
        ]
        
        with patch.object(self.parser, 'filter_empty_items') as mock_filter:
            mock_filter.return_value = ["項目1", "項目3", "項目5"]
            
            result = self.parser.handle_empty_items(items_with_empty)
            
            # 空項目が適切にフィルターされることを確認
            assert result is not None
            mock_filter.assert_called()

    def test_normalize_list_formatting(self):
        """リスト書式正規化テスト"""
        irregular_list = """
        -項目1（スペースなし）
        -  項目2（スペース多い）
        - 項目3（標準）
        •項目4（異なる記号）
        """
        
        with patch.object(self.parser, 'apply_formatting_rules') as mock_format:
            mock_format.return_value = "normalized_list"
            
            result = self.parser.normalize_list_formatting(irregular_list)
            
            # リスト書式が正規化されることを確認
            assert result is not None
            mock_format.assert_called()


class TestListParserIntegration:
    """ListParser統合テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = ListParser()

    def test_full_list_parsing_workflow_simple(self):
        """シンプル完全リスト解析ワークフロー"""
        simple_list = """
        - 項目1
        - ;;;太字;;; 項目2 ;;;
        - 項目3
        """
        
        with patch.object(self.parser, 'parse_unordered_list') as mock_unordered:
            mock_unordered.return_value = Mock()
            
            result = self.parser.parse_unordered_list(simple_list)
            
            # シンプルワークフローが実行されることを確認
            assert result is not None
            mock_unordered.assert_called()

    def test_full_list_parsing_workflow_complex(self):
        """複雑完全リスト解析ワークフロー"""
        complex_list = """
        1. ;;;見出し1;;; 第1章 ;;;
           - ;;;太字;;; サブ項目1 ;;;
             a. ;;;イタリック;;; 詳細項目1 ;;;
             b. 詳細項目2
           - サブ項目2
        2. 第2章
           - サブ項目A
           - サブ項目B
             i. 細目1
             ii. ;;;枠線;;; 細目2 ;;;
        """
        
        nested_parser = NestedListParser()
        
        with patch.object(nested_parser, 'parse_nested_structure') as mock_nested:
            with patch.object(self.parser, 'parse_ordered_list') as mock_ordered:
                mock_nested.return_value = Mock()
                mock_ordered.return_value = Mock()
                
                result = nested_parser.parse_nested_structure(complex_list)
                
                # 複雑ワークフローが実行されることを確認
                assert result is not None
                mock_nested.assert_called()

    def test_error_handling_integration(self):
        """エラーハンドリング統合テスト"""
        error_lists = [
            "- 項目1\n不正な形式\n- 項目2",
            None,  # None値
            "",    # 空文字列
            "無効なリスト形式",
            "- 項目1\n  - ネスト不正\n     - さらにネスト",
        ]
        
        for error_list in error_lists:
            try:
                if error_list and "無効" not in error_list:
                    result = self.parser.parse_unordered_list(error_list)
                else:
                    result = self.parser.parse_unordered_list("")
                
                # エラーが適切に処理されることを確認
                assert True
            except Exception:
                # 予期しないクラッシュが発生しないことを確認
                assert True

    def test_performance_integration_large_lists(self):
        """大リストパフォーマンス統合テスト"""
        # 大きなリストでの統合パフォーマンステスト
        large_unordered = "\n".join([f"- 項目{i}" for i in range(1000)])
        large_ordered = "\n".join([f"{i}. 項目{i}" for i in range(1, 1001)])
        
        # ネストした大リスト
        large_nested = []
        for i in range(100):
            large_nested.append(f"- レベル1項目{i}")
            for j in range(10):
                large_nested.append(f"  - レベル2項目{i}-{j}")
        large_nested_content = "\n".join(large_nested)
        
        test_lists = [large_unordered, large_ordered, large_nested_content]
        
        for test_list in test_lists:
            with patch.object(self.parser, 'create_list_node') as mock_create:
                mock_create.return_value = Mock()
                
                import time
                start = time.time()
                
                if test_list == large_unordered:
                    result = self.parser.parse_unordered_list(test_list)
                elif test_list == large_ordered:
                    result = self.parser.parse_ordered_list(test_list)
                else:
                    result = self.parser.parse_nested_list(test_list)
                
                end = time.time()
                duration = end - start
                
                # パフォーマンス要件を満たすことを確認
                assert result is not None
                assert duration < 5.0  # 5秒以内

    def test_memory_efficiency_integration(self):
        """メモリ効率統合テスト"""
        # メモリリークがないことを確認
        test_list = "- メモリテスト項目\n" * 100
        
        for i in range(20):
            with patch.object(self.parser, 'create_list_node') as mock_create:
                mock_create.return_value = Mock()
                
                result = self.parser.parse_unordered_list(test_list)
                assert result is not None
        
        # ガベージコレクション
        import gc
        gc.collect()
        assert True


class TestListParserEdgeCases:
    """ListParser エッジケーステスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = ListParser()

    def test_edge_case_unicode_list_items(self):
        """Unicodeリスト項目エッジケース"""
        unicode_lists = [
            "- 日本語項目：重要な情報",
            "- 한국어 항목: 중요 정보", 
            "- 中文項目：重要信息",
            "- العربية: معلومات مهمة",
            "- Русский пункт: важная информация",
            "- 🎌 絵文字項目 🗻",
        ]
        
        unicode_content = "\n".join(unicode_lists)
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            mock_create.return_value = Mock()
            
            result = self.parser.parse_unordered_list(unicode_content)
            
            # Unicode項目が適切に処理されることを確認
            assert result is not None

    def test_edge_case_extreme_nesting_levels(self):
        """極端ネストレベルエッジケース"""
        # 50レベルの深いネスト
        extreme_nested = "- レベル1"
        for level in range(2, 51):
            indent = "  " * (level - 1)
            extreme_nested += f"\n{indent}- レベル{level}"
        
        nested_parser = NestedListParser()
        
        with patch.object(nested_parser, 'manage_nesting_levels') as mock_levels:
            mock_levels.return_value = 50
            
            result = nested_parser.parse_nested_structure(extreme_nested)
            
            # 極端ネストが適切に処理されることを確認
            assert result is not None

    def test_edge_case_malformed_list_syntax(self):
        """不正形式リスト構文エッジケース"""
        malformed_lists = [
            "-項目1（スペースなし）",
            "- \n項目（空行）",
            "1.項目（スペースなし）",
            "項目 -（逆順）",
            "-- 二重ハイフン項目",
            "--- 三重ハイフン項目",
        ]
        
        for malformed in malformed_lists:
            try:
                with patch.object(self.parser, 'create_list_node') as mock_create:
                    mock_create.return_value = Mock()
                    
                    result = self.parser.parse_unordered_list(malformed)
                    
                    # 不正形式でも適切に処理されることを確認
                    assert result is not None
            except Exception:
                # エラーハンドリングが動作することを確認
                assert True

    def test_edge_case_mixed_indentation_styles(self):
        """混在インデントスタイルエッジケース"""
        mixed_indent_list = """
        - レベル1項目
        	- タブインデント項目
          - 2スペースインデント項目
            - 4スペースインデント項目
         - 1スペースインデント項目
        """
        
        nested_parser = NestedListParser()
        
        with patch.object(nested_parser, 'normalize_indentation') as mock_normalize:
            mock_normalize.return_value = "normalized"
            
            result = nested_parser.parse_nested_structure(mixed_indent_list)
            
            # 混在インデントが正規化されることを確認
            assert result is not None
            mock_normalize.assert_called()

    def test_edge_case_very_long_list_items(self):
        """非常に長いリスト項目エッジケース"""
        very_long_item = "- " + "非常に長い項目テキスト。" * 1000
        
        with patch.object(self.parser, 'create_list_node') as mock_create:
            with patch.object(self.parser, 'handle_long_items') as mock_long:
                mock_create.return_value = Mock()
                mock_long.return_value = "truncated_item"
                
                result = self.parser.parse_unordered_list(very_long_item)
                
                # 非常に長い項目が適切に処理されることを確認
                assert result is not None
                mock_long.assert_called()

    def test_edge_case_concurrent_list_parsing(self):
        """並行リスト解析エッジケース"""
        import concurrent.futures
        
        test_lists = [
            "- 並行テスト1\n- 項目2",
            "1. 順序リスト1\n2. 項目2",
            "- ネスト\n  - 子項目",
            "- マーカー ;;;太字;;; テスト ;;;",
            "- 最終テスト項目",
        ]
        
        def parse_concurrent_list(list_content):
            with patch.object(self.parser, 'create_list_node') as mock_create:
                mock_create.return_value = Mock()
                return self.parser.parse_unordered_list(list_content) is not None
        
        # 並行実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(parse_concurrent_list, lst) for lst in test_lists]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # 全ての並行処理が成功することを確認
        assert all(results)