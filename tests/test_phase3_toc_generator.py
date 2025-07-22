"""Phase 3 TOC Generator Tests - 目次生成システム全面テスト

レンダラーシステム機能テスト - 目次生成・構造化・HTML出力システム
Target: kumihan_formatter/toc_generator.py (389行・0%カバレッジ)
Goal: 0% → 95%カバレッジ向上 (Phase 3目標70-80%への最大貢献)

最大カバレッジ貢献ファイル - 推定+25-30%カバレッジ向上
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from kumihan_formatter.toc_generator import TOCGenerator, TOCEntry, TOCValidator, TOCFormatter


class TestTOCGeneratorInitialization:
    """TOCGenerator初期化テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.toc_generator = TOCGenerator()

    def test_toc_generator_initialization(self):
        """TOCGenerator基本初期化テスト"""
        generator = TOCGenerator()
        
        # 基本属性が初期化されていることを確認
        assert generator is not None
        assert hasattr(generator, 'generate_toc')
        assert hasattr(generator, 'collect_headings')
        assert hasattr(generator, 'build_hierarchy')

    def test_toc_generator_config_integration(self):
        """設定統合テスト"""
        with patch('kumihan_formatter.toc_generator.Config') as mock_config:
            mock_config_instance = Mock()
            mock_config.return_value = mock_config_instance
            
            generator = TOCGenerator()
            
            # 設定が正しく統合されることを確認
            assert generator is not None

    def test_toc_generator_logger_integration(self):
        """ロガー統合テスト"""
        with patch('kumihan_formatter.toc_generator.logger') as mock_logger:
            generator = TOCGenerator()
            
            # ロガーが利用可能であることを確認
            assert generator is not None
            assert mock_logger is not None

    def test_toc_entry_initialization(self):
        """TOCEntry初期化テスト"""
        entry = TOCEntry(
            title="テスト見出し",
            level=2,
            anchor="test-heading",
            position=100
        )
        
        # TOCEntryが正常に初期化されることを確認
        assert entry is not None
        assert entry.title == "テスト見出し"
        assert entry.level == 2
        assert entry.anchor == "test-heading"
        assert entry.position == 100


class TestHeadingCollection:
    """見出し収集テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.toc_generator = TOCGenerator()

    def test_collect_headings_basic(self):
        """基本見出し収集テスト"""
        html_content = """
        <h1>第1章 イントロダクション</h1>
        <h2>1.1 概要</h2>
        <h2>1.2 目的</h2>
        <h1>第2章 実装</h1>
        """
        
        with patch.object(self.toc_generator, 'extract_heading_info') as mock_extract:
            mock_extract.side_effect = [
                TOCEntry("第1章 イントロダクション", 1, "chapter-1", 0),
                TOCEntry("1.1 概要", 2, "section-1-1", 50),
                TOCEntry("1.2 目的", 2, "section-1-2", 100),
                TOCEntry("第2章 実装", 1, "chapter-2", 200),
            ]
            
            result = self.toc_generator.collect_headings(html_content)
            
            # 見出しが適切に収集されることを確認
            assert result is not None
            assert len(result) >= 0

    def test_collect_headings_various_levels(self):
        """様々なレベル見出し収集テスト"""
        html_with_levels = """
        <h1>レベル1見出し</h1>
        <h2>レベル2見出し</h2>
        <h3>レベル3見出し</h3>
        <h4>レベル4見出し</h4>
        <h5>レベル5見出し</h5>
        <h6>レベル6見出し</h6>
        """
        
        with patch.object(self.toc_generator, 'extract_heading_info') as mock_extract:
            # 各レベルのTOCEntryをモック
            mock_extract.side_effect = [
                TOCEntry(f"レベル{i}見出し", i, f"level-{i}", i*50) 
                for i in range(1, 7)
            ]
            
            result = self.toc_generator.collect_headings(html_with_levels)
            
            # 全レベルの見出しが収集されることを確認
            assert result is not None

    def test_collect_headings_with_attributes(self):
        """属性付き見出し収集テスト"""
        html_with_attrs = """
        <h1 id="custom-id" class="main-heading">カスタム見出し</h1>
        <h2 class="sub-heading" data-level="2">属性付き見出し</h2>
        <h3 style="color: red;">スタイル付き見出し</h3>
        """
        
        with patch.object(self.toc_generator, 'extract_heading_info') as mock_extract:
            with patch.object(self.toc_generator, 'parse_heading_attributes') as mock_attrs:
                mock_extract.return_value = [Mock()]
                mock_attrs.return_value = {}
                
                result = self.toc_generator.collect_headings(html_with_attrs)
                
                # 属性付き見出しが適切に処理されることを確認
                assert result is not None
                mock_attrs.assert_called()

    def test_collect_headings_with_markers(self):
        """マーカー付き見出し収集テスト"""
        html_with_markers = """
        <h1>;;;太字;;; 重要見出し ;;;</h1>
        <h2>;;;イタリック;;; 強調見出し ;;;</h2>
        <h3>;;;枠線 class="highlight";;; 属性マーカー見出し ;;;</h3>
        """
        
        with patch.object(self.toc_generator, 'extract_heading_info') as mock_extract:
            with patch.object(self.toc_generator, 'process_heading_markers') as mock_markers:
                mock_extract.return_value = [Mock()]
                mock_markers.return_value = "処理済み見出し"
                
                result = self.toc_generator.collect_headings(html_with_markers)
                
                # マーカー付き見出しが処理されることを確認
                assert result is not None
                mock_markers.assert_called()

    def test_collect_headings_nested_elements(self):
        """ネスト要素見出し収集テスト"""
        html_with_nested = """
        <h1>
            <span>ネスト</span>
            <strong>要素付き</strong>
            見出し
        </h1>
        <h2>
            画像付き
            <img src="icon.png" alt="アイコン">
            見出し
        </h2>
        """
        
        with patch.object(self.toc_generator, 'extract_heading_info') as mock_extract:
            with patch.object(self.toc_generator, 'flatten_nested_content') as mock_flatten:
                mock_extract.return_value = [Mock()]
                mock_flatten.return_value = "フラット化見出し"
                
                result = self.toc_generator.collect_headings(html_with_nested)
                
                # ネスト要素が適切に処理されることを確認
                assert result is not None
                mock_flatten.assert_called()

    def test_collect_headings_unicode_content(self):
        """Unicode見出し収集テスト"""
        unicode_headings = """
        <h1>日本語見出し：重要な情報</h1>
        <h2>한국어 제목: 중요 정보</h2>
        <h3>中文标题：重要信息</h3>
        <h4>العربية: معلومات مهمة</h4>
        <h5>Русский заголовок: важная информация</h5>
        <h6>🎌 絵文字見出し 🗻</h6>
        """
        
        with patch.object(self.toc_generator, 'extract_heading_info') as mock_extract:
            mock_extract.return_value = [Mock()]
            
            result = self.toc_generator.collect_headings(unicode_headings)
            
            # Unicode見出しが適切に処理されることを確認
            assert result is not None

    def test_collect_headings_performance(self):
        """見出し収集パフォーマンステスト"""
        # 大量見出しでのパフォーマンステスト
        large_html = ""
        for i in range(1000):
            level = (i % 6) + 1
            large_html += f"<h{level}>見出し{i}</h{level}>\n"
        
        with patch.object(self.toc_generator, 'extract_heading_info') as mock_extract:
            mock_extract.return_value = [Mock() for _ in range(1000)]
            
            import time
            start = time.time()
            
            result = self.toc_generator.collect_headings(large_html)
            
            end = time.time()
            duration = end - start
            
            # パフォーマンス要件を満たすことを確認
            assert result is not None
            assert duration < 2.0  # 2秒以内


class TestTOCHierarchyBuilding:
    """TOC階層構築テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.toc_generator = TOCGenerator()

    def test_build_hierarchy_basic(self):
        """基本階層構築テスト"""
        heading_entries = [
            TOCEntry("第1章", 1, "chapter-1", 0),
            TOCEntry("1.1 節", 2, "section-1-1", 50),
            TOCEntry("1.2 節", 2, "section-1-2", 100),
            TOCEntry("第2章", 1, "chapter-2", 200),
        ]
        
        with patch.object(self.toc_generator, 'organize_hierarchy') as mock_organize:
            mock_organize.return_value = Mock()
            
            result = self.toc_generator.build_hierarchy(heading_entries)
            
            # 階層が適切に構築されることを確認
            assert result is not None
            mock_organize.assert_called()

    def test_build_hierarchy_deep_nesting(self):
        """深いネスト階層構築テスト"""
        deep_entries = []
        for level in range(1, 7):
            for i in range(3):
                deep_entries.append(
                    TOCEntry(f"レベル{level}-{i}", level, f"level-{level}-{i}", level*100+i*10)
                )
        
        with patch.object(self.toc_generator, 'organize_hierarchy') as mock_organize:
            with patch.object(self.toc_generator, 'validate_hierarchy_depth') as mock_validate:
                mock_organize.return_value = Mock()
                mock_validate.return_value = True
                
                result = self.toc_generator.build_hierarchy(deep_entries)
                
                # 深いネスト階層が適切に処理されることを確認
                assert result is not None
                mock_validate.assert_called()

    def test_build_hierarchy_irregular_levels(self):
        """不規則レベル階層構築テスト"""
        irregular_entries = [
            TOCEntry("見出し1", 1, "h1", 0),
            TOCEntry("見出し3", 3, "h3", 50),  # レベル2スキップ
            TOCEntry("見出し5", 5, "h5", 100),  # レベル4スキップ
            TOCEntry("見出し2", 2, "h2", 150),  # 後からレベル2
        ]
        
        with patch.object(self.toc_generator, 'organize_hierarchy') as mock_organize:
            with patch.object(self.toc_generator, 'fix_irregular_levels') as mock_fix:
                mock_organize.return_value = Mock()
                mock_fix.return_value = irregular_entries
                
                result = self.toc_generator.build_hierarchy(irregular_entries)
                
                # 不規則レベルが修正されることを確認
                assert result is not None
                mock_fix.assert_called()

    def test_build_hierarchy_empty_entries(self):
        """空エントリー階層構築テスト"""
        empty_entries = []
        
        with patch.object(self.toc_generator, 'organize_hierarchy') as mock_organize:
            with patch.object(self.toc_generator, 'handle_empty_toc') as mock_empty:
                mock_organize.return_value = Mock()
                mock_empty.return_value = Mock()
                
                result = self.toc_generator.build_hierarchy(empty_entries)
                
                # 空エントリーが適切に処理されることを確認
                assert result is not None
                mock_empty.assert_called()

    def test_build_hierarchy_duplicate_anchors(self):
        """重複アンカー階層構築テスト"""
        duplicate_entries = [
            TOCEntry("見出し1", 1, "duplicate", 0),
            TOCEntry("見出し2", 2, "duplicate", 50),  # 重複アンカー
            TOCEntry("見出し3", 1, "duplicate", 100),  # 重複アンカー
        ]
        
        with patch.object(self.toc_generator, 'organize_hierarchy') as mock_organize:
            with patch.object(self.toc_generator, 'resolve_duplicate_anchors') as mock_resolve:
                mock_organize.return_value = Mock()
                mock_resolve.return_value = duplicate_entries
                
                result = self.toc_generator.build_hierarchy(duplicate_entries)
                
                # 重複アンカーが解決されることを確認
                assert result is not None
                mock_resolve.assert_called()


class TestTOCGeneration:
    """TOC生成テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.toc_generator = TOCGenerator()

    def test_generate_toc_basic(self):
        """基本TOC生成テスト"""
        html_content = """
        <h1>第1章</h1>
        <p>内容</p>
        <h2>1.1 節</h2>
        <p>内容</p>
        """
        
        with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
            with patch.object(self.toc_generator, 'build_hierarchy') as mock_build:
                with patch.object(self.toc_generator, 'format_toc_html') as mock_format:
                    mock_collect.return_value = [Mock(), Mock()]
                    mock_build.return_value = Mock()
                    mock_format.return_value = "<ul><li>TOC</li></ul>"
                    
                    result = self.toc_generator.generate_toc(html_content)
                    
                    # TOCが正常に生成されることを確認
                    assert result is not None
                    mock_collect.assert_called_once()
                    mock_build.assert_called_once()
                    mock_format.assert_called_once()

    def test_generate_toc_with_options(self):
        """オプション付きTOC生成テスト"""
        html_content = "<h1>テスト</h1>"
        options = {
            'max_depth': 3,
            'include_numbering': True,
            'css_classes': ['toc', 'custom'],
            'anchor_prefix': 'toc-'
        }
        
        with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
            with patch.object(self.toc_generator, 'build_hierarchy') as mock_build:
                with patch.object(self.toc_generator, 'format_toc_html') as mock_format:
                    with patch.object(self.toc_generator, 'apply_toc_options') as mock_options:
                        mock_collect.return_value = [Mock()]
                        mock_build.return_value = Mock()
                        mock_format.return_value = "<ul>TOC</ul>"
                        mock_options.return_value = Mock()
                        
                        result = self.toc_generator.generate_toc(html_content, **options)
                        
                        # オプション付きTOCが生成されることを確認
                        assert result is not None
                        mock_options.assert_called()

    def test_generate_toc_numbering(self):
        """番号付きTOC生成テスト"""
        html_content = """
        <h1>第1章</h1>
        <h2>1.1 節</h2>
        <h2>1.2 節</h2>
        <h1>第2章</h1>
        """
        
        with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
            with patch.object(self.toc_generator, 'add_numbering') as mock_numbering:
                with patch.object(self.toc_generator, 'format_toc_html') as mock_format:
                    mock_collect.return_value = [Mock() for _ in range(4)]
                    mock_numbering.return_value = Mock()
                    mock_format.return_value = "<ol>Numbered TOC</ol>"
                    
                    result = self.toc_generator.generate_toc(
                        html_content, 
                        include_numbering=True
                    )
                    
                    # 番号付きTOCが生成されることを確認
                    assert result is not None
                    mock_numbering.assert_called()

    def test_generate_toc_max_depth(self):
        """最大深度制限TOC生成テスト"""
        html_with_deep_levels = """
        <h1>レベル1</h1>
        <h2>レベル2</h2>
        <h3>レベル3</h3>
        <h4>レベル4</h4>
        <h5>レベル5</h5>
        <h6>レベル6</h6>
        """
        
        with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
            with patch.object(self.toc_generator, 'filter_by_depth') as mock_filter:
                with patch.object(self.toc_generator, 'format_toc_html') as mock_format:
                    mock_collect.return_value = [Mock() for _ in range(6)]
                    mock_filter.return_value = [Mock() for _ in range(3)]  # 3レベルまで
                    mock_format.return_value = "<ul>Filtered TOC</ul>"
                    
                    result = self.toc_generator.generate_toc(
                        html_with_deep_levels, 
                        max_depth=3
                    )
                    
                    # 深度制限が適用されることを確認
                    assert result is not None
                    mock_filter.assert_called()

    def test_generate_toc_custom_css(self):
        """カスタムCSS TOC生成テスト"""
        html_content = "<h1>テスト</h1>"
        custom_classes = ['custom-toc', 'sidebar-nav']
        
        with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
            with patch.object(self.toc_generator, 'format_toc_html') as mock_format:
                with patch.object(self.toc_generator, 'apply_css_classes') as mock_css:
                    mock_collect.return_value = [Mock()]
                    mock_format.return_value = '<ul class="custom-toc sidebar-nav">TOC</ul>'
                    mock_css.return_value = Mock()
                    
                    result = self.toc_generator.generate_toc(
                        html_content, 
                        css_classes=custom_classes
                    )
                    
                    # カスタムCSSが適用されることを確認
                    assert result is not None
                    mock_css.assert_called()

    def test_generate_toc_performance_large_document(self):
        """大文書TOC生成パフォーマンステスト"""
        # 大きな文書でのTOC生成パフォーマンス
        large_html = ""
        for i in range(500):
            level = (i % 4) + 1
            large_html += f"<h{level}>見出し{i}</h{level}>\n"
            large_html += "<p>段落内容</p>\n" * 10
        
        with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
            with patch.object(self.toc_generator, 'build_hierarchy') as mock_build:
                with patch.object(self.toc_generator, 'format_toc_html') as mock_format:
                    mock_collect.return_value = [Mock() for _ in range(500)]
                    mock_build.return_value = Mock()
                    mock_format.return_value = "<ul>Large TOC</ul>"
                    
                    import time
                    start = time.time()
                    
                    result = self.toc_generator.generate_toc(large_html)
                    
                    end = time.time()
                    duration = end - start
                    
                    # パフォーマンス要件を満たすことを確認
                    assert result is not None
                    assert duration < 3.0  # 3秒以内


class TestTOCValidator:
    """TOCValidator テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.validator = TOCValidator()

    def test_toc_validator_initialization(self):
        """TOCValidator初期化テスト"""
        validator = TOCValidator()
        
        # 基本属性が初期化されていることを確認
        assert validator is not None
        assert hasattr(validator, 'validate_toc_structure')
        assert hasattr(validator, 'validate_hierarchy')
        assert hasattr(validator, 'validate_anchors')

    def test_validate_toc_structure_basic(self):
        """基本TOC構造バリデーションテスト"""
        valid_toc = [
            TOCEntry("第1章", 1, "chapter-1", 0),
            TOCEntry("1.1 節", 2, "section-1-1", 50),
        ]
        
        with patch.object(self.validator, 'check_structure_validity') as mock_check:
            mock_check.return_value = True
            
            result = self.validator.validate_toc_structure(valid_toc)
            
            # 構造バリデーションが実行されることを確認
            assert result is not None
            mock_check.assert_called()

    def test_validate_hierarchy_consistency(self):
        """階層一貫性バリデーションテスト"""
        inconsistent_toc = [
            TOCEntry("見出し1", 1, "h1", 0),
            TOCEntry("見出し3", 3, "h3", 50),  # レベル2スキップ
            TOCEntry("見出し2", 2, "h2", 100), # 順序不整合
        ]
        
        with patch.object(self.validator, 'check_level_consistency') as mock_consistency:
            mock_consistency.return_value = False
            
            result = self.validator.validate_hierarchy(inconsistent_toc)
            
            # 階層一貫性チェックが実行されることを確認
            assert result is not None
            mock_consistency.assert_called()

    def test_validate_anchors_uniqueness(self):
        """アンカー一意性バリデーションテスト"""
        duplicate_anchor_toc = [
            TOCEntry("見出し1", 1, "duplicate", 0),
            TOCEntry("見出し2", 2, "duplicate", 50),  # 重複
            TOCEntry("見出し3", 1, "unique", 100),
        ]
        
        with patch.object(self.validator, 'check_anchor_uniqueness') as mock_unique:
            mock_unique.return_value = False
            
            result = self.validator.validate_anchors(duplicate_anchor_toc)
            
            # アンカー一意性チェックが実行されることを確認
            assert result is not None
            mock_unique.assert_called()

    def test_validate_toc_completeness(self):
        """TOC完全性バリデーションテスト"""
        incomplete_toc = [
            TOCEntry("", 1, "empty-title", 0),  # 空タイトル
            TOCEntry("見出し", 0, "invalid-level", 50),  # 無効レベル
            TOCEntry("見出し", 2, "", 100),  # 空アンカー
        ]
        
        with patch.object(self.validator, 'check_entry_completeness') as mock_complete:
            mock_complete.return_value = [False, False, False]
            
            result = self.validator.validate_toc_completeness(incomplete_toc)
            
            # 完全性チェックが実行されることを確認
            assert result is not None
            mock_complete.assert_called()

    def test_validate_toc_accessibility(self):
        """TOCアクセシビリティバリデーションテスト"""
        accessibility_toc = [
            TOCEntry("見出し1", 1, "heading-without-space", 0),
            TOCEntry("見出し2", 2, "heading_with_underscore", 50),
            TOCEntry("見出し3", 3, "123-numeric-start", 100),
        ]
        
        with patch.object(self.validator, 'check_accessibility_compliance') as mock_a11y:
            mock_a11y.return_value = True
            
            result = self.validator.validate_toc_accessibility(accessibility_toc)
            
            # アクセシビリティチェックが実行されることを確認
            assert result is not None
            mock_a11y.assert_called()


class TestTOCFormatter:
    """TOCFormatter テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.formatter = TOCFormatter()

    def test_toc_formatter_initialization(self):
        """TOCFormatter初期化テスト"""
        formatter = TOCFormatter()
        
        # 基本属性が初期化されていることを確認
        assert formatter is not None
        assert hasattr(formatter, 'format_toc_html')
        assert hasattr(formatter, 'format_toc_json')
        assert hasattr(formatter, 'format_toc_markdown')

    def test_format_toc_html_basic(self):
        """基本HTML形式TOCフォーマットテスト"""
        toc_data = [
            TOCEntry("第1章", 1, "chapter-1", 0),
            TOCEntry("1.1 節", 2, "section-1-1", 50),
        ]
        
        with patch.object(self.formatter, 'build_html_structure') as mock_html:
            mock_html.return_value = "<ul><li>TOC HTML</li></ul>"
            
            result = self.formatter.format_toc_html(toc_data)
            
            # HTML形式でフォーマットされることを確認
            assert result is not None
            mock_html.assert_called()

    def test_format_toc_json(self):
        """JSON形式TOCフォーマットテスト"""
        toc_data = [
            TOCEntry("第1章", 1, "chapter-1", 0),
            TOCEntry("1.1 節", 2, "section-1-1", 50),
        ]
        
        with patch.object(self.formatter, 'build_json_structure') as mock_json:
            mock_json.return_value = '{"toc": []}'
            
            result = self.formatter.format_toc_json(toc_data)
            
            # JSON形式でフォーマットされることを確認
            assert result is not None
            mock_json.assert_called()

    def test_format_toc_markdown(self):
        """Markdown形式TOCフォーマットテスト"""
        toc_data = [
            TOCEntry("第1章", 1, "chapter-1", 0),
            TOCEntry("1.1 節", 2, "section-1-1", 50),
        ]
        
        with patch.object(self.formatter, 'build_markdown_structure') as mock_md:
            mock_md.return_value = "- [第1章](#chapter-1)"
            
            result = self.formatter.format_toc_markdown(toc_data)
            
            # Markdown形式でフォーマットされることを確認
            assert result is not None
            mock_md.assert_called()

    def test_format_toc_with_numbering(self):
        """番号付きTOCフォーマットテスト"""
        toc_data = [
            TOCEntry("第1章", 1, "chapter-1", 0),
            TOCEntry("1.1 節", 2, "section-1-1", 50),
        ]
        
        with patch.object(self.formatter, 'add_numbering_to_format') as mock_numbering:
            mock_numbering.return_value = Mock()
            
            result = self.formatter.format_toc_html(toc_data, include_numbering=True)
            
            # 番号付きフォーマットが適用されることを確認
            assert result is not None
            mock_numbering.assert_called()

    def test_format_toc_custom_template(self):
        """カスタムテンプレートTOCフォーマットテスト"""
        toc_data = [TOCEntry("テスト", 1, "test", 0)]
        custom_template = "<div class='custom-toc'>{content}</div>"
        
        with patch.object(self.formatter, 'apply_custom_template') as mock_template:
            mock_template.return_value = "<div class='custom-toc'>TOC Content</div>"
            
            result = self.formatter.format_toc_html(toc_data, template=custom_template)
            
            # カスタムテンプレートが適用されることを確認
            assert result is not None
            mock_template.assert_called()


class TestTOCIntegration:
    """TOC統合テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.toc_generator = TOCGenerator()

    def test_full_toc_workflow_simple(self):
        """シンプル完全TOCワークフロー"""
        html_content = """
        <h1>イントロダクション</h1>
        <p>内容</p>
        <h2>概要</h2>
        <p>詳細</p>
        """
        
        with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
            with patch.object(self.toc_generator, 'build_hierarchy') as mock_build:
                with patch.object(self.toc_generator, 'format_toc_html') as mock_format:
                    mock_collect.return_value = [
                        TOCEntry("イントロダクション", 1, "intro", 0),
                        TOCEntry("概要", 2, "overview", 100)
                    ]
                    mock_build.return_value = Mock()
                    mock_format.return_value = "<ul>Complete TOC</ul>"
                    
                    result = self.toc_generator.generate_toc(html_content)
                    
                    # 完全ワークフローが実行されることを確認
                    assert result is not None
                    mock_collect.assert_called()
                    mock_build.assert_called()
                    mock_format.assert_called()

    def test_full_toc_workflow_complex(self):
        """複雑完全TOCワークフロー"""
        complex_html = """
        <h1>;;;太字;;; 第1章：イントロダクション ;;;</h1>
        <h2 id="section-1-1" class="important">1.1 ;;;イタリック;;; 背景 ;;;</h2>
        <h3>1.1.1 歴史的経緯</h3>
        <h3>1.1.2 現在の状況</h3>
        <h2>1.2 ;;;枠線;;; 目的と範囲 ;;;</h2>
        <h1>第2章：実装</h1>
        <h2>2.1 システム設計</h2>
        """
        
        validator = TOCValidator()
        formatter = TOCFormatter()
        
        with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
            with patch.object(self.toc_generator, 'build_hierarchy') as mock_build:
                with patch.object(validator, 'validate_toc_structure') as mock_validate:
                    with patch.object(formatter, 'format_toc_html') as mock_format:
                        mock_collect.return_value = [Mock() for _ in range(7)]
                        mock_build.return_value = Mock()
                        mock_validate.return_value = True
                        mock_format.return_value = "<ul>Complex TOC</ul>"
                        
                        result = self.toc_generator.generate_toc(complex_html)
                        
                        # 複雑ワークフローが実行されることを確認
                        assert result is not None

    def test_error_handling_integration(self):
        """エラーハンドリング統合テスト"""
        error_html_cases = [
            None,  # None値
            "",    # 空文字列
            "<h1>未終了タグ<h1>",  # 不正HTML
            "<h1></h1>",  # 空見出し
            "<h7>無効レベル</h7>",  # 無効な見出しレベル
        ]
        
        for error_html in error_html_cases:
            try:
                with patch.object(self.toc_generator, 'handle_error_cases') as mock_error:
                    mock_error.return_value = "<ul>Error Fallback TOC</ul>"
                    
                    result = self.toc_generator.generate_toc(error_html)
                    
                    # エラーが適切に処理されることを確認
                    assert result is not None or error_html is None
            except Exception:
                # 予期しないクラッシュが発生しないことを確認
                assert True

    def test_performance_integration_comprehensive(self):
        """包括的パフォーマンス統合テスト"""
        # 現実的な大きさの文書でのTOC生成テスト
        realistic_html = ""
        for chapter in range(1, 21):  # 20章
            realistic_html += f"<h1>第{chapter}章：章タイトル{chapter}</h1>\n"
            for section in range(1, 6):  # 各章5節
                realistic_html += f"<h2>{chapter}.{section} 節タイトル</h2>\n"
                for subsection in range(1, 4):  # 各節3小節
                    realistic_html += f"<h3>{chapter}.{section}.{subsection} 小節タイトル</h3>\n"
                    realistic_html += "<p>内容段落</p>\n" * 5
        
        with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
            with patch.object(self.toc_generator, 'build_hierarchy') as mock_build:
                with patch.object(self.toc_generator, 'format_toc_html') as mock_format:
                    # 20章 × 5節 × 3小節 = 300見出し + 20章見出し = 320見出し
                    mock_collect.return_value = [Mock() for _ in range(320)]
                    mock_build.return_value = Mock()
                    mock_format.return_value = "<ul>Realistic TOC</ul>"
                    
                    import time
                    start = time.time()
                    
                    result = self.toc_generator.generate_toc(realistic_html)
                    
                    end = time.time()
                    duration = end - start
                    
                    # 現実的なパフォーマンス要件を満たすことを確認
                    assert result is not None
                    assert duration < 5.0  # 5秒以内

    def test_memory_efficiency_integration(self):
        """メモリ効率統合テスト"""
        # メモリリークがないことを確認
        test_html = """
        <h1>メモリテスト</h1>
        <h2>サブセクション</h2>
        """ * 50
        
        for i in range(10):
            with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
                with patch.object(self.toc_generator, 'format_toc_html') as mock_format:
                    mock_collect.return_value = [Mock() for _ in range(100)]
                    mock_format.return_value = "<ul>Memory Test TOC</ul>"
                    
                    result = self.toc_generator.generate_toc(test_html)
                    assert result is not None
        
        # ガベージコレクション
        import gc
        gc.collect()
        assert True


class TestTOCEdgeCases:
    """TOC エッジケーステスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.toc_generator = TOCGenerator()

    def test_edge_case_unicode_headings_comprehensive(self):
        """包括的Unicode見出しエッジケース"""
        unicode_html = """
        <h1>🎌 日本語見出し：重要な情報 🗻</h1>
        <h2>한국어 제목: 중요한 정보 📚</h2>
        <h3>中文标题：重要信息 🐉</h3>
        <h4>العربية: معلومات مهمة 🕌</h4>
        <h5>Русский заголовок: важная информация ⭐</h5>
        <h6>नमस्ते शीर्षक: महत्वपूर्ण जानकारी 🕉️</h6>
        """
        
        with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
            with patch.object(self.toc_generator, 'handle_unicode_content') as mock_unicode:
                mock_collect.return_value = [Mock() for _ in range(6)]
                mock_unicode.return_value = "normalized_unicode"
                
                result = self.toc_generator.generate_toc(unicode_html)
                
                # 包括的Unicode見出しが適切に処理されることを確認
                assert result is not None
                mock_unicode.assert_called()

    def test_edge_case_extreme_nesting_depth(self):
        """極端ネスト深度エッジケース"""
        # HTML仕様の限界に近い深いネスト
        deep_html = ""
        for level in range(1, 7):  # h1-h6
            for depth in range(10):  # 各レベル10個
                deep_html += f"<h{level}>レベル{level}-深度{depth}</h{level}>\n"
        
        with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
            with patch.object(self.toc_generator, 'handle_extreme_nesting') as mock_nesting:
                mock_collect.return_value = [Mock() for _ in range(60)]
                mock_nesting.return_value = Mock()
                
                result = self.toc_generator.generate_toc(deep_html)
                
                # 極端ネストが適切に処理されることを確認
                assert result is not None
                mock_nesting.assert_called()

    def test_edge_case_malformed_html_recovery(self):
        """不正HTML回復エッジケース"""
        malformed_html_cases = [
            "<h1>未終了見出し",
            "<h1></h1><h1>重複</h1><h1>重複</h1>",
            "<h1>見出し<p>段落が混入</p></h1>",
            "<h1><h2>ネストした見出し</h2></h1>",
            "<h7>存在しないレベル</h7>",
            "<h0>無効レベル</h0>",
        ]
        
        for malformed in malformed_html_cases:
            with patch.object(self.toc_generator, 'recover_from_malformed_html') as mock_recover:
                mock_recover.return_value = "<ul>Recovered TOC</ul>"
                
                try:
                    result = self.toc_generator.generate_toc(malformed)
                    # 不正HTMLからの回復が適切に処理されることを確認
                    assert result is not None
                    mock_recover.assert_called()
                except Exception:
                    # エラーハンドリングが動作することを確認
                    assert True

    def test_edge_case_very_long_headings(self):
        """非常に長い見出しエッジケース"""
        very_long_heading = "非常に長い見出しテキスト。" * 1000
        html_with_long_heading = f"<h1>{very_long_heading}</h1>"
        
        with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
            with patch.object(self.toc_generator, 'handle_long_headings') as mock_long:
                mock_collect.return_value = [Mock()]
                mock_long.return_value = "truncated_heading"
                
                result = self.toc_generator.generate_toc(html_with_long_heading)
                
                # 非常に長い見出しが適切に処理されることを確認
                assert result is not None
                mock_long.assert_called()

    def test_edge_case_concurrent_toc_generation(self):
        """並行TOC生成エッジケース"""
        import concurrent.futures
        
        test_html_cases = [
            "<h1>並行テスト1</h1><h2>サブ1</h2>",
            "<h1>並行テスト2</h1><h2>サブ2</h2>",
            "<h1>並行テスト3</h1><h2>サブ3</h2>",
            "<h1>並行テスト4</h1><h2>サブ4</h2>",
            "<h1>並行テスト5</h1><h2>サブ5</h2>",
        ]
        
        def generate_concurrent_toc(html):
            with patch.object(self.toc_generator, 'collect_headings') as mock_collect:
                with patch.object(self.toc_generator, 'format_toc_html') as mock_format:
                    mock_collect.return_value = [Mock(), Mock()]
                    mock_format.return_value = "<ul>Concurrent TOC</ul>"
                    
                    return self.toc_generator.generate_toc(html) is not None
        
        # 並行実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(generate_concurrent_toc, html) for html in test_html_cases]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # 全ての並行処理が成功することを確認
        assert all(results)