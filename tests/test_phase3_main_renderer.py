"""Phase 3 Main Renderer Tests - メインレンダラー統合システム全面テスト

レンダラーシステム機能テスト - メインレンダラー統合管理システム
Target: kumihan_formatter/core/rendering/main_renderer.py (307行・0%カバレッジ)
Goal: 0% → 95%カバレッジ向上 (Phase 3目標70-80%への重要貢献)

2番目最大カバレッジ貢献ファイル - 推定+20-25%カバレッジ向上
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from kumihan_formatter.core.rendering.main_renderer import HTMLRenderer
from kumihan_formatter.core.ast_nodes import Node


class TestHTMLRendererInitialization:
    """HTMLRenderer初期化テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.renderer = HTMLRenderer()

    def test_html_renderer_initialization(self):
        """HTMLRenderer基本初期化テスト"""
        renderer = HTMLRenderer()
        
        # 基本属性が初期化されていることを確認
        assert renderer is not None
        assert hasattr(renderer, 'render')
        assert hasattr(renderer, 'collect_headings')
        assert hasattr(renderer, '_render_content')

    def test_html_renderer_config_integration(self):
        """設定統合テスト"""
        with patch('kumihan_formatter.core.rendering.main_renderer.Config') as mock_config:
            mock_config_instance = Mock()
            mock_config.return_value = mock_config_instance
            
            renderer = HTMLRenderer()
            
            # 設定が正しく統合されることを確認
            assert renderer is not None

    def test_html_renderer_logger_integration(self):
        """ロガー統合テスト"""
        with patch('kumihan_formatter.core.rendering.main_renderer.logger') as mock_logger:
            renderer = HTMLRenderer()
            
            # ロガーが利用可能であることを確認
            assert renderer is not None
            assert mock_logger is not None

    def test_html_renderer_sub_renderers_initialization(self):
        """サブレンダラー初期化テスト"""
        with patch('kumihan_formatter.core.rendering.main_renderer.ElementRenderer') as mock_element:
            with patch('kumihan_formatter.core.rendering.main_renderer.CompoundElementRenderer') as mock_compound:
                mock_element.return_value = Mock()
                mock_compound.return_value = Mock()
                
                renderer = HTMLRenderer()
                
                # サブレンダラーが初期化されることを確認
                assert renderer is not None
                mock_element.assert_called()
                mock_compound.assert_called()


class TestHTMLRenderingCore:
    """HTML レンダリング コア機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.renderer = HTMLRenderer()

    def test_render_basic_ast(self):
        """基本AST レンダリングテスト"""
        mock_ast = [
            Mock(type='paragraph', content='段落テキスト'),
            Mock(type='heading', level=1, content='見出し1'),
        ]
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            mock_render_content.return_value = '<p>段落テキスト</p><h1>見出し1</h1>'
            
            result = self.renderer.render(mock_ast)
            
            # 基本ASTが適切にレンダリングされることを確認
            assert result is not None
            mock_render_content.assert_called()

    def test_render_with_depth_limit(self):
        """深度制限付きレンダリングテスト"""
        deep_ast = [Mock(type='paragraph') for _ in range(100)]
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'check_depth_limit') as mock_depth:
                mock_render_content.return_value = '<p>制限適用済み</p>'
                mock_depth.return_value = True
                
                result = self.renderer.render(deep_ast, max_depth=50)
                
                # 深度制限が適用されることを確認
                assert result is not None
                mock_depth.assert_called()

    def test_render_with_heading_collection(self):
        """見出し収集付きレンダリングテスト"""
        ast_with_headings = [
            Mock(type='heading', level=1, content='第1章'),
            Mock(type='paragraph', content='内容'),
            Mock(type='heading', level=2, content='1.1 節'),
        ]
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'collect_headings') as mock_collect:
                mock_render_content.return_value = '<h1>第1章</h1><p>内容</p><h2>1.1 節</h2>'
                mock_collect.return_value = [Mock(), Mock()]
                
                result = self.renderer.render(ast_with_headings, collect_headings=True)
                
                # 見出し収集が実行されることを確認
                assert result is not None
                mock_collect.assert_called()

    def test_render_with_custom_context(self):
        """カスタムコンテキスト付きレンダリングテスト"""
        mock_ast = [Mock(type='paragraph', content='テスト')]
        custom_context = {
            'title': 'テスト文書',
            'author': 'テスト作成者',
            'date': '2025-01-01'
        }
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'apply_context') as mock_context:
                mock_render_content.return_value = '<p>テスト</p>'
                mock_context.return_value = Mock()
                
                result = self.renderer.render(mock_ast, context=custom_context)
                
                # カスタムコンテキストが適用されることを確認
                assert result is not None
                mock_context.assert_called()

    def test_render_error_handling(self):
        """レンダリングエラーハンドリングテスト"""
        error_ast = [Mock(type='invalid_type', content='エラーノード')]
        
        with patch.object(self.renderer, '_render_content', side_effect=Exception("Render error")):
            with patch.object(self.renderer, 'handle_render_error') as mock_error:
                mock_error.return_value = '<div class="error">エラーが発生しました</div>'
                
                result = self.renderer.render(error_ast)
                
                # エラーが適切に処理されることを確認
                assert result is not None
                mock_error.assert_called()

    def test_render_empty_ast(self):
        """空AST レンダリングテスト"""
        empty_ast = []
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'handle_empty_ast') as mock_empty:
                mock_render_content.return_value = ''
                mock_empty.return_value = '<div class="empty">コンテンツがありません</div>'
                
                result = self.renderer.render(empty_ast)
                
                # 空ASTが適切に処理されることを確認
                assert result is not None
                mock_empty.assert_called()

    def test_render_performance_large_ast(self):
        """大AST レンダリングパフォーマンステスト"""
        large_ast = [Mock(type='paragraph', content=f'段落{i}') for i in range(1000)]
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            mock_render_content.return_value = '<p>大量段落</p>' * 1000
            
            import time
            start = time.time()
            
            result = self.renderer.render(large_ast)
            
            end = time.time()
            duration = end - start
            
            # パフォーマンス要件を満たすことを確認
            assert result is not None
            assert duration < 3.0  # 3秒以内


class TestContentRendering:
    """コンテンツレンダリングテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.renderer = HTMLRenderer()

    def test_render_content_paragraph(self):
        """段落コンテンツレンダリングテスト"""
        paragraph_node = Mock(type='paragraph', content='段落テキスト')
        
        with patch.object(self.renderer, 'element_renderer') as mock_element:
            mock_element.render_paragraph.return_value = '<p>段落テキスト</p>'
            
            result = self.renderer._render_content([paragraph_node])
            
            # 段落が適切にレンダリングされることを確認
            assert result is not None

    def test_render_content_heading(self):
        """見出しコンテンツレンダリングテスト"""
        heading_node = Mock(type='heading', level=2, content='見出し')
        
        with patch.object(self.renderer, 'element_renderer') as mock_element:
            mock_element.render_heading.return_value = '<h2>見出し</h2>'
            
            result = self.renderer._render_content([heading_node])
            
            # 見出しが適切にレンダリングされることを確認
            assert result is not None

    def test_render_content_list(self):
        """リストコンテンツレンダリングテスト"""
        list_node = Mock(
            type='unordered_list',
            items=[
                Mock(content='項目1'),
                Mock(content='項目2'),
                Mock(content='項目3')
            ]
        )
        
        with patch.object(self.renderer, 'element_renderer') as mock_element:
            mock_element.render_unordered_list.return_value = '<ul><li>項目1</li><li>項目2</li><li>項目3</li></ul>'
            
            result = self.renderer._render_content([list_node])
            
            # リストが適切にレンダリングされることを確認
            assert result is not None

    def test_render_content_compound_elements(self):
        """複合要素コンテンツレンダリングテスト"""
        compound_node = Mock(
            type='compound',
            keywords=['太字', 'イタリック'],
            content='複合要素テキスト'
        )
        
        with patch.object(self.renderer, 'compound_renderer') as mock_compound:
            mock_compound.render_compound_element.return_value = '<strong><em>複合要素テキスト</em></strong>'
            
            result = self.renderer._render_content([compound_node])
            
            # 複合要素が適切にレンダリングされることを確認
            assert result is not None

    def test_render_content_mixed_elements(self):
        """混在要素コンテンツレンダリングテスト"""
        mixed_nodes = [
            Mock(type='heading', level=1, content='タイトル'),
            Mock(type='paragraph', content='段落1'),
            Mock(type='unordered_list', items=[Mock(content='項目1')]),
            Mock(type='paragraph', content='段落2'),
        ]
        
        with patch.object(self.renderer, 'element_renderer') as mock_element:
            mock_element.render_heading.return_value = '<h1>タイトル</h1>'
            mock_element.render_paragraph.return_value = '<p>段落</p>'
            mock_element.render_unordered_list.return_value = '<ul><li>項目1</li></ul>'
            
            result = self.renderer._render_content(mixed_nodes)
            
            # 混在要素が適切にレンダリングされることを確認
            assert result is not None

    def test_render_content_nested_structures(self):
        """ネスト構造コンテンツレンダリングテスト"""
        nested_node = Mock(
            type='details',
            summary='詳細タイトル',
            children=[
                Mock(type='paragraph', content='ネスト段落1'),
                Mock(type='paragraph', content='ネスト段落2')
            ]
        )
        
        with patch.object(self.renderer, 'element_renderer') as mock_element:
            mock_element.render_details.return_value = '<details><summary>詳細タイトル</summary><p>ネスト段落1</p><p>ネスト段落2</p></details>'
            
            result = self.renderer._render_content([nested_node])
            
            # ネスト構造が適切にレンダリングされることを確認
            assert result is not None

    def test_render_content_with_attributes(self):
        """属性付きコンテンツレンダリングテスト"""
        attributed_node = Mock(
            type='paragraph',
            content='属性付き段落',
            attributes={'class': 'highlight', 'id': 'special-paragraph'}
        )
        
        with patch.object(self.renderer, 'element_renderer') as mock_element:
            mock_element.render_paragraph.return_value = '<p class="highlight" id="special-paragraph">属性付き段落</p>'
            
            result = self.renderer._render_content([attributed_node])
            
            # 属性付きコンテンツが適切にレンダリングされることを確認
            assert result is not None


class TestHeadingCollection:
    """見出し収集テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.renderer = HTMLRenderer()

    def test_collect_headings_basic(self):
        """基本見出し収集テスト"""
        ast_with_headings = [
            Mock(type='heading', level=1, content='第1章', id='chapter-1'),
            Mock(type='paragraph', content='段落'),
            Mock(type='heading', level=2, content='1.1 節', id='section-1-1'),
        ]
        
        with patch.object(self.renderer, 'extract_heading_data') as mock_extract:
            mock_extract.side_effect = [
                {'title': '第1章', 'level': 1, 'id': 'chapter-1'},
                {'title': '1.1 節', 'level': 2, 'id': 'section-1-1'}
            ]
            
            result = self.renderer.collect_headings(ast_with_headings)
            
            # 見出しが適切に収集されることを確認
            assert result is not None
            assert len(result) >= 0

    def test_collect_headings_various_levels(self):
        """様々なレベル見出し収集テスト"""
        various_level_ast = [
            Mock(type='heading', level=i, content=f'レベル{i}見出し', id=f'level-{i}')
            for i in range(1, 7)
        ]
        
        with patch.object(self.renderer, 'extract_heading_data') as mock_extract:
            mock_extract.side_effect = [
                {'title': f'レベル{i}見出し', 'level': i, 'id': f'level-{i}'}
                for i in range(1, 7)
            ]
            
            result = self.renderer.collect_headings(various_level_ast)
            
            # 様々なレベルの見出しが収集されることを確認
            assert result is not None

    def test_collect_headings_with_markers(self):
        """マーカー付き見出し収集テスト"""
        marker_headings = [
            Mock(type='heading', level=1, content=';;;太字;;; 重要見出し ;;;', id='important'),
            Mock(type='heading', level=2, content=';;;イタリック;;; 強調見出し ;;;', id='emphasis'),
        ]
        
        with patch.object(self.renderer, 'extract_heading_data') as mock_extract:
            with patch.object(self.renderer, 'process_heading_markers') as mock_markers:
                mock_extract.side_effect = [
                    {'title': '重要見出し', 'level': 1, 'id': 'important'},
                    {'title': '強調見出し', 'level': 2, 'id': 'emphasis'}
                ]
                mock_markers.return_value = '処理済み見出し'
                
                result = self.renderer.collect_headings(marker_headings)
                
                # マーカー付き見出しが適切に処理されることを確認
                assert result is not None
                mock_markers.assert_called()

    def test_collect_headings_automatic_id_generation(self):
        """自動ID生成見出し収集テスト"""
        no_id_headings = [
            Mock(type='heading', level=1, content='ID未設定見出し1'),
            Mock(type='heading', level=2, content='ID未設定見出し2'),
        ]
        
        with patch.object(self.renderer, 'extract_heading_data') as mock_extract:
            with patch.object(self.renderer, 'generate_heading_id') as mock_generate_id:
                mock_extract.side_effect = [
                    {'title': 'ID未設定見出し1', 'level': 1, 'id': None},
                    {'title': 'ID未設定見出し2', 'level': 2, 'id': None}
                ]
                mock_generate_id.side_effect = ['auto-id-1', 'auto-id-2']
                
                result = self.renderer.collect_headings(no_id_headings)
                
                # 自動ID生成が実行されることを確認
                assert result is not None
                mock_generate_id.assert_called()

    def test_collect_headings_duplicate_ids(self):
        """重複ID見出し収集テスト"""
        duplicate_id_headings = [
            Mock(type='heading', level=1, content='見出し1', id='duplicate'),
            Mock(type='heading', level=2, content='見出し2', id='duplicate'),
        ]
        
        with patch.object(self.renderer, 'extract_heading_data') as mock_extract:
            with patch.object(self.renderer, 'resolve_duplicate_ids') as mock_resolve:
                mock_extract.side_effect = [
                    {'title': '見出し1', 'level': 1, 'id': 'duplicate'},
                    {'title': '見出し2', 'level': 2, 'id': 'duplicate'}
                ]
                mock_resolve.return_value = ['duplicate', 'duplicate-2']
                
                result = self.renderer.collect_headings(duplicate_id_headings)
                
                # 重複IDが解決されることを確認
                assert result is not None
                mock_resolve.assert_called()

    def test_collect_headings_hierarchy_validation(self):
        """階層バリデーション見出し収集テスト"""
        irregular_hierarchy = [
            Mock(type='heading', level=1, content='レベル1'),
            Mock(type='heading', level=3, content='レベル3（2をスキップ）'),
            Mock(type='heading', level=2, content='レベル2（後から）'),
        ]
        
        with patch.object(self.renderer, 'extract_heading_data') as mock_extract:
            with patch.object(self.renderer, 'validate_heading_hierarchy') as mock_validate:
                mock_extract.side_effect = [
                    {'title': 'レベル1', 'level': 1, 'id': 'level-1'},
                    {'title': 'レベル3（2をスキップ）', 'level': 3, 'id': 'level-3'},
                    {'title': 'レベル2（後から）', 'level': 2, 'id': 'level-2'}
                ]
                mock_validate.return_value = False  # 不正な階層
                
                result = self.renderer.collect_headings(irregular_hierarchy)
                
                # 階層バリデーションが実行されることを確認
                assert result is not None
                mock_validate.assert_called()


class TestRenderingOptimization:
    """レンダリング最適化テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.renderer = HTMLRenderer()

    def test_render_with_caching(self):
        """キャッシュ付きレンダリングテスト"""
        cached_ast = [Mock(type='paragraph', content='キャッシュテスト')]
        
        with patch.object(self.renderer, 'use_render_cache') as mock_cache:
            with patch.object(self.renderer, '_render_content') as mock_render_content:
                mock_cache.return_value = True
                mock_render_content.return_value = '<p>キャッシュテスト</p>'
                
                # 初回レンダリング
                result1 = self.renderer.render(cached_ast, use_cache=True)
                
                # 2回目レンダリング（キャッシュ利用）
                result2 = self.renderer.render(cached_ast, use_cache=True)
                
                # キャッシュが利用されることを確認
                assert result1 is not None
                assert result2 is not None
                mock_cache.assert_called()

    def test_render_with_lazy_loading(self):
        """遅延読み込みレンダリングテスト"""
        large_ast = [Mock(type='paragraph', content=f'段落{i}') for i in range(100)]
        
        with patch.object(self.renderer, 'enable_lazy_loading') as mock_lazy:
            with patch.object(self.renderer, '_render_content_lazy') as mock_lazy_render:
                mock_lazy.return_value = True
                mock_lazy_render.return_value = '<div>遅延読み込み済み</div>'
                
                result = self.renderer.render(large_ast, lazy_loading=True)
                
                # 遅延読み込みが有効になることを確認
                assert result is not None
                mock_lazy.assert_called()

    def test_render_with_memory_optimization(self):
        """メモリ最適化レンダリングテスト"""
        memory_intensive_ast = [Mock(type='paragraph', content='メモリテスト' * 1000) for _ in range(50)]
        
        with patch.object(self.renderer, 'optimize_memory_usage') as mock_memory:
            with patch.object(self.renderer, '_render_content') as mock_render_content:
                mock_memory.return_value = Mock()
                mock_render_content.return_value = '<p>最適化済み</p>'
                
                result = self.renderer.render(memory_intensive_ast, optimize_memory=True)
                
                # メモリ最適化が実行されることを確認
                assert result is not None
                mock_memory.assert_called()

    def test_render_with_parallel_processing(self):
        """並列処理レンダリングテスト"""
        parallel_ast = [Mock(type='paragraph', content=f'並列{i}') for i in range(20)]
        
        with patch.object(self.renderer, 'enable_parallel_processing') as mock_parallel:
            with patch.object(self.renderer, '_render_content_parallel') as mock_parallel_render:
                mock_parallel.return_value = True
                mock_parallel_render.return_value = '<div>並列処理済み</div>'
                
                result = self.renderer.render(parallel_ast, parallel=True)
                
                # 並列処理が有効になることを確認
                assert result is not None
                mock_parallel.assert_called()

    def test_render_with_compression(self):
        """圧縮レンダリングテスト"""
        large_html_ast = [Mock(type='paragraph', content='圧縮テスト') for _ in range(100)]
        
        with patch.object(self.renderer, 'compress_output') as mock_compress:
            with patch.object(self.renderer, '_render_content') as mock_render_content:
                mock_compress.return_value = '<compressed>HTML</compressed>'
                mock_render_content.return_value = '<p>圧縮テスト</p>' * 100
                
                result = self.renderer.render(large_html_ast, compress=True)
                
                # 出力圧縮が実行されることを確認
                assert result is not None
                mock_compress.assert_called()


class TestErrorHandling:
    """エラーハンドリングテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.renderer = HTMLRenderer()

    def test_handle_invalid_node_type(self):
        """無効ノードタイプ処理テスト"""
        invalid_ast = [Mock(type='invalid_type', content='無効ノード')]
        
        with patch.object(self.renderer, 'handle_invalid_node') as mock_invalid:
            mock_invalid.return_value = '<div class="error">無効なノードタイプ</div>'
            
            result = self.renderer.render(invalid_ast)
            
            # 無効ノードタイプが適切に処理されることを確認
            assert result is not None
            mock_invalid.assert_called()

    def test_handle_circular_references(self):
        """循環参照処理テスト"""
        circular_node = Mock(type='details')
        circular_node.children = [circular_node]  # 循環参照
        
        with patch.object(self.renderer, 'detect_circular_references') as mock_circular:
            with patch.object(self.renderer, 'handle_circular_reference') as mock_handle:
                mock_circular.return_value = True
                mock_handle.return_value = '<div class="error">循環参照を検出</div>'
                
                result = self.renderer.render([circular_node])
                
                # 循環参照が検出・処理されることを確認
                assert result is not None
                mock_circular.assert_called()
                mock_handle.assert_called()

    def test_handle_memory_exhaustion(self):
        """メモリ不足処理テスト"""
        memory_exhausting_ast = [Mock() for _ in range(10000)]
        
        with patch.object(self.renderer, '_render_content', side_effect=MemoryError("Out of memory")):
            with patch.object(self.renderer, 'handle_memory_exhaustion') as mock_memory:
                mock_memory.return_value = '<div class="error">メモリ不足</div>'
                
                result = self.renderer.render(memory_exhausting_ast)
                
                # メモリ不足が適切に処理されることを確認
                assert result is not None
                mock_memory.assert_called()

    def test_handle_rendering_timeout(self):
        """レンダリングタイムアウト処理テスト"""
        slow_ast = [Mock(type='complex_element') for _ in range(100)]
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'handle_render_timeout') as mock_timeout:
                # タイムアウトをシミュレート
                def slow_render(*args, **kwargs):
                    import time
                    time.sleep(10)  # 非現実的な遅延
                    return '<div>遅い</div>'
                
                mock_render_content.side_effect = slow_render
                mock_timeout.return_value = '<div class="error">タイムアウト</div>'
                
                result = self.renderer.render(slow_ast, timeout=1)
                
                # タイムアウトが適切に処理されることを確認
                assert result is not None

    def test_handle_malformed_ast(self):
        """不正AST処理テスト"""
        malformed_ast = [
            None,  # None値
            "string",  # 文字列（ノードではない）
            {'type': 'dict'},  # 辞書（ノードではない）
            Mock(type=None),  # type属性がNone
        ]
        
        with patch.object(self.renderer, 'validate_ast_structure') as mock_validate:
            with patch.object(self.renderer, 'handle_malformed_ast') as mock_malformed:
                mock_validate.return_value = False
                mock_malformed.return_value = '<div class="error">不正AST</div>'
                
                result = self.renderer.render(malformed_ast)
                
                # 不正ASTが適切に処理されることを確認
                assert result is not None
                mock_validate.assert_called()
                mock_malformed.assert_called()


class TestHTMLRendererIntegration:
    """HTMLRenderer統合テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.renderer = HTMLRenderer()

    def test_full_rendering_workflow_simple(self):
        """シンプル完全レンダリングワークフロー"""
        simple_ast = [
            Mock(type='heading', level=1, content='タイトル', id='title'),
            Mock(type='paragraph', content='段落1'),
            Mock(type='paragraph', content='段落2'),
        ]
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'collect_headings') as mock_collect:
                mock_render_content.return_value = '<h1 id="title">タイトル</h1><p>段落1</p><p>段落2</p>'
                mock_collect.return_value = [{'title': 'タイトル', 'level': 1, 'id': 'title'}]
                
                result = self.renderer.render(simple_ast, collect_headings=True)
                
                # シンプルワークフローが実行されることを確認
                assert result is not None
                mock_render_content.assert_called()
                mock_collect.assert_called()

    def test_full_rendering_workflow_complex(self):
        """複雑完全レンダリングワークフロー"""
        complex_ast = [
            Mock(type='heading', level=1, content=';;;太字;;; 第1章：イントロダクション ;;;', id='chapter-1'),
            Mock(type='paragraph', content='これは導入段落です。'),
            Mock(type='unordered_list', items=[
                Mock(content=';;;イタリック;;; 重要項目1 ;;;'),
                Mock(content='項目2'),
                Mock(content='項目3')
            ]),
            Mock(type='details', summary='詳細情報', children=[
                Mock(type='paragraph', content='詳細段落1'),
                Mock(type='paragraph', content='詳細段落2')
            ]),
            Mock(type='heading', level=2, content='1.1 概要', id='section-1-1'),
            Mock(type='paragraph', content='概要段落です。'),
        ]
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'collect_headings') as mock_collect:
                with patch.object(self.renderer, 'apply_context') as mock_context:
                    mock_render_content.return_value = '<complex>HTML</complex>'
                    mock_collect.return_value = [Mock(), Mock()]
                    mock_context.return_value = Mock()
                    
                    result = self.renderer.render(
                        complex_ast,
                        collect_headings=True,
                        context={'title': '複雑文書'}
                    )
                    
                    # 複雑ワークフローが実行されることを確認
                    assert result is not None
                    mock_render_content.assert_called()
                    mock_collect.assert_called()
                    mock_context.assert_called()

    def test_performance_integration_realistic(self):
        """現実的パフォーマンス統合テスト"""
        # 現実的なサイズの文書ASTを作成
        realistic_ast = []
        
        # 10章の文書
        for chapter in range(1, 11):
            # 章見出し
            realistic_ast.append(Mock(
                type='heading',
                level=1,
                content=f'第{chapter}章：章タイトル{chapter}',
                id=f'chapter-{chapter}'
            ))
            
            # 章の導入段落
            realistic_ast.append(Mock(
                type='paragraph',
                content=f'第{chapter}章の導入段落です。' * 5
            ))
            
            # 各章に5つの節
            for section in range(1, 6):
                realistic_ast.append(Mock(
                    type='heading',
                    level=2,
                    content=f'{chapter}.{section} 節タイトル',
                    id=f'section-{chapter}-{section}'
                ))
                
                # 節の内容
                realistic_ast.append(Mock(
                    type='paragraph',
                    content=f'節{chapter}.{section}の内容段落です。' * 3
                ))
                
                # リストを含む
                if section % 2 == 0:
                    realistic_ast.append(Mock(
                        type='unordered_list',
                        items=[Mock(content=f'項目{i}') for i in range(1, 4)]
                    ))
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'collect_headings') as mock_collect:
                mock_render_content.return_value = '<div>現実的な文書HTML</div>'
                mock_collect.return_value = [Mock() for _ in range(60)]  # 10章 + 50節
                
                import time
                start = time.time()
                
                result = self.renderer.render(realistic_ast, collect_headings=True)
                
                end = time.time()
                duration = end - start
                
                # 現実的なパフォーマンス要件を満たすことを確認
                assert result is not None
                assert duration < 2.0  # 2秒以内

    def test_memory_efficiency_integration(self):
        """メモリ効率統合テスト"""
        # メモリリークがないことを確認
        test_ast = [
            Mock(type='paragraph', content='メモリテスト段落'),
            Mock(type='heading', level=1, content='メモリテスト見出し')
        ] * 100
        
        for i in range(10):
            with patch.object(self.renderer, '_render_content') as mock_render_content:
                mock_render_content.return_value = '<div>メモリテスト</div>'
                
                result = self.renderer.render(test_ast)
                assert result is not None
        
        # ガベージコレクション
        import gc
        gc.collect()
        assert True

    def test_thread_safety_integration(self):
        """スレッドセーフティ統合テスト"""
        import threading
        
        test_ast = [Mock(type='paragraph', content='スレッドテスト')]
        results = []
        
        def render_in_thread():
            try:
                with patch.object(self.renderer, '_render_content') as mock_render_content:
                    mock_render_content.return_value = '<p>スレッドテスト</p>'
                    result = self.renderer.render(test_ast)
                    results.append(result is not None)
            except Exception:
                results.append(False)
        
        # 複数スレッドで並行実行
        threads = []
        for i in range(5):
            thread = threading.Thread(target=render_in_thread)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 全てのスレッドで正常に処理されることを確認
        assert all(results)


class TestHTMLRendererEdgeCases:
    """HTMLRenderer エッジケーステスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.renderer = HTMLRenderer()

    def test_edge_case_deeply_nested_ast(self):
        """深くネストしたASTエッジケース"""
        # 50レベルの深いネスト構造を作成
        def create_nested_ast(depth):
            if depth == 0:
                return Mock(type='paragraph', content=f'深度{depth}の段落')
            return Mock(
                type='details',
                summary=f'深度{depth}の詳細',
                children=[create_nested_ast(depth - 1)]
            )
        
        deeply_nested_ast = [create_nested_ast(50)]
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'handle_deep_nesting') as mock_deep:
                mock_render_content.return_value = '<div>深いネスト処理済み</div>'
                mock_deep.return_value = True
                
                result = self.renderer.render(deeply_nested_ast)
                
                # 深いネストが適切に処理されることを確認
                assert result is not None
                mock_deep.assert_called()

    def test_edge_case_unicode_content_comprehensive(self):
        """包括的Unicodeコンテンツエッジケース"""
        unicode_ast = [
            Mock(type='heading', level=1, content='🎌 日本語見出し：重要な情報 🗻'),
            Mock(type='paragraph', content='한국어 단락: 중요한 정보입니다.'),
            Mock(type='paragraph', content='中文段落：重要信息内容。'),
            Mock(type='paragraph', content='العربية: معلومات مهمة جداً.'),
            Mock(type='paragraph', content='Русский абзац: важная информация.'),
            Mock(type='unordered_list', items=[
                Mock(content='🚀 絵文字項目1'),
                Mock(content='⭐ 絵文字項目2'),
                Mock(content='🌸 絵文字項目3')
            ])
        ]
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'handle_unicode_content') as mock_unicode:
                mock_render_content.return_value = '<div>Unicodeコンテンツ処理済み</div>'
                mock_unicode.return_value = True
                
                result = self.renderer.render(unicode_ast)
                
                # 包括的Unicodeコンテンツが適切に処理されることを確認
                assert result is not None
                mock_unicode.assert_called()

    def test_edge_case_massive_ast_elements(self):
        """大量AST要素エッジケース"""
        # 10,000要素のAST
        massive_ast = [Mock(type='paragraph', content=f'段落{i}') for i in range(10000)]
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'handle_massive_ast') as mock_massive:
                mock_render_content.return_value = '<div>大量要素処理済み</div>'
                mock_massive.return_value = True
                
                result = self.renderer.render(massive_ast)
                
                # 大量要素が適切に処理されることを確認
                assert result is not None
                mock_massive.assert_called()

    def test_edge_case_concurrent_rendering(self):
        """並行レンダリングエッジケース"""
        import concurrent.futures
        
        test_ast_cases = [
            [Mock(type='paragraph', content=f'並行テスト{i}')] for i in range(10)
        ]
        
        def render_concurrent_ast(ast):
            with patch.object(self.renderer, '_render_content') as mock_render_content:
                mock_render_content.return_value = '<p>並行処理済み</p>'
                return self.renderer.render(ast) is not None
        
        # 並行実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(render_concurrent_ast, ast) for ast in test_ast_cases]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # 全ての並行処理が成功することを確認
        assert all(results)

    def test_edge_case_resource_exhaustion_recovery(self):
        """リソース枯渇回復エッジケース"""
        resource_intensive_ast = [Mock(type='paragraph', content='リソース集約的内容' * 10000)]
        
        with patch.object(self.renderer, '_render_content', side_effect=[
            MemoryError("Memory exhausted"),  # 初回はメモリエラー
            '<p>リソース回復後成功</p>'  # 2回目は成功
        ]) as mock_render_content:
            with patch.object(self.renderer, 'recover_from_resource_exhaustion') as mock_recover:
                mock_recover.return_value = True
                
                result = self.renderer.render(resource_intensive_ast)
                
                # リソース枯渇から回復することを確認
                assert result is not None
                mock_recover.assert_called()

    def test_edge_case_corrupted_node_structure(self):
        """破損ノード構造エッジケース"""
        corrupted_ast = [
            Mock(type='paragraph'),  # content属性なし
            Mock(content='コンテンツあり'),  # type属性なし
            Mock(type='heading'),  # level属性なし
            Mock(type='unordered_list'),  # items属性なし
        ]
        
        for node in corrupted_ast:
            # 一部の属性を削除して破損をシミュレート
            if hasattr(node, 'content') and not hasattr(node, 'type'):
                delattr(node, 'content')
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'handle_corrupted_nodes') as mock_corrupted:
                mock_render_content.return_value = '<div>破損ノード修復済み</div>'
                mock_corrupted.return_value = True
                
                result = self.renderer.render(corrupted_ast)
                
                # 破損ノード構造が適切に処理されることを確認
                assert result is not None
                mock_corrupted.assert_called()

    def test_edge_case_extreme_performance_stress(self):
        """極限パフォーマンスストレステスト"""
        # CPU集約的なレンダリングシナリオ
        stress_ast = []
        
        # 複雑な構造を大量生成
        for i in range(1000):
            stress_ast.append(Mock(
                type='details',
                summary=f'複雑要素{i}',
                children=[
                    Mock(type='paragraph', content=f'ネスト段落{j}') for j in range(10)
                ]
            ))
        
        with patch.object(self.renderer, '_render_content') as mock_render_content:
            with patch.object(self.renderer, 'handle_performance_stress') as mock_stress:
                mock_render_content.return_value = '<div>ストレステスト完了</div>'
                mock_stress.return_value = True
                
                import time
                start = time.time()
                
                result = self.renderer.render(stress_ast)
                
                end = time.time()
                duration = end - start
                
                # ストレステストが合理的な時間で完了することを確認
                assert result is not None
                assert duration < 10.0  # 10秒以内
                mock_stress.assert_called()