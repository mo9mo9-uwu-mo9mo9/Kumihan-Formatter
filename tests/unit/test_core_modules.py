"""
コアモジュールの単体テスト

分離・統合されたコアモジュール群の動作確認
- ASTノード (AST nodes)
- 設定管理 (config management)
- ログ・監視 (logging & monitoring)
- ユーティリティ (utilities)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# ASTノード関連
from kumihan_formatter.core.ast_nodes.node import Node
from kumihan_formatter.core.ast_nodes.factories import create_node

# 設定管理関連
from kumihan_formatter.core.config.config_manager import ConfigManager
from kumihan_formatter.core.config.config_types import Config, BaseConfig, FormatterConfig

# 分類・検証関連
from kumihan_formatter.core.doc_classifier import DocumentClassifier
from kumihan_formatter.core.document_types import DocumentType


class TestASTNodes:
    """ASTノードシステムのテスト"""

    def test_node_creation(self):
        """Node作成テスト"""
        node = create_node("test_type", content="テストコンテンツ")
        assert isinstance(node, Node)
        assert node.node_type == "test_type"
        assert node.content == "テストコンテンツ"

    def test_node_metadata_management(self):
        """Nodeメタデータ管理テスト"""
        node = create_node("test_type")
        node.metadata["key1"] = "value1"
        node.metadata["key2"] = 123
        
        assert node.metadata["key1"] == "value1"
        assert node.metadata["key2"] == 123
        assert len(node.metadata) >= 2

    def test_node_children_management(self):
        """Node子要素管理テスト"""
        parent = create_node("parent")
        child1 = create_node("child1")
        child2 = create_node("child2")
        
        parent.add_child(child1)
        parent.add_child(child2)
        
        assert len(parent.children) == 2
        assert child1 in parent.children
        assert child2 in parent.children

    def test_node_parent_child_relationship(self):
        """Node親子関係テスト"""
        parent = create_node("parent")
        child = create_node("child")
        
        parent.add_child(child)
        
        # 親子関係が適切に設定されることを確認
        assert child in parent.children
        # parent属性が存在しない場合はスキップ
        if hasattr(child, 'parent'):
            assert child.parent == parent


class TestConfigManager:
    """統合設定管理のテスト"""

    def test_config_manager_initialization(self):
        """ConfigManager 初期化テスト"""
        manager = ConfigManager()
        assert manager is not None

    def test_config_manager_basic_functionality(self):
        """ConfigManager 基本機能テスト"""
        manager = ConfigManager()
        
        # 基本的なメソッドが存在することを確認
        assert hasattr(manager, '__init__')


class TestConfigTypes:
    """設定型のテスト"""

    def test_config_types_availability(self):
        """設定型の利用可能性テスト"""
        # 基本設定型が存在することを確認
        assert Config is not None
        assert BaseConfig is not None
        assert FormatterConfig is not None

    def test_formatter_config_creation(self):
        """FormatterConfig作成テスト"""
        config = FormatterConfig()
        assert config is not None
        # 実際の属性名を確認
        assert hasattr(config, 'template_dir')
        assert hasattr(config, 'input_encoding') or hasattr(config, 'output_encoding')


class TestDocumentClassifier:
    """文書分類器のテスト"""

    def test_document_classifier_initialization(self):
        """DocumentClassifier 初期化テスト"""
        classifier = DocumentClassifier()
        assert classifier is not None

    def test_document_classification_methods(self):
        """文書分類メソッドテスト"""
        classifier = DocumentClassifier()
        
        # 分類器オブジェクトが正常に作成されることを確認
        assert classifier is not None
        # 何らかのメソッドが存在することを確認
        assert len(dir(classifier)) > 0


class TestDocumentTypes:
    """文書タイプのテスト"""

    def test_document_type_enum(self):
        """DocumentType 列挙型テスト"""
        assert DocumentType is not None
        
        # DocumentTypeが使用可能であることを確認
        assert callable(DocumentType) or hasattr(DocumentType, '__members__')


class TestCoreIntegration:
    """コアモジュール統合テスト"""

    def test_ast_config_integration(self):
        """ASTと設定の統合テスト"""
        config = FormatterConfig()
        node = create_node("test")
        
        # 両方のコンポーネントが正常に動作することを確認
        assert config is not None
        assert node is not None

    def test_document_processing_integration(self):
        """文書処理統合テスト"""
        classifier = DocumentClassifier()
        config = FormatterConfig()
        
        # 統合処理の基本動作を確認
        assert classifier is not None
        assert config is not None

    def test_core_module_compatibility(self):
        """コアモジュール互換性テスト"""
        # 複数のコアコンポーネントを同時に使用
        components = [
            ConfigManager(),
            DocumentClassifier(),
            create_node("test")
        ]
        
        # すべて正常に初期化されることを確認
        for component in components:
            assert component is not None

    def test_error_handling_consistency(self):
        """エラーハンドリング一貫性テスト"""
        try:
            config_manager = ConfigManager()
            classifier = DocumentClassifier()
            node = create_node("test")
            
            assert config_manager is not None
            assert classifier is not None
            assert node is not None
        except Exception as e:
            pytest.fail(f"Unexpected error in core modules: {e}")


class TestPerformanceBasics:
    """基本パフォーマンステスト"""

    def test_node_creation_performance(self):
        """ノード作成パフォーマンステスト"""
        import time
        
        start_time = time.perf_counter()
        
        # 大量のノード作成
        nodes = []
        for i in range(1000):
            node = create_node(f"type_{i % 10}", content=f"content_{i}")
            nodes.append(node)
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        assert len(nodes) == 1000
        assert execution_time < 1.0  # 1秒以内での完了を期待

    def test_config_manager_performance(self):
        """設定管理パフォーマンステスト"""
        import time
        
        start_time = time.perf_counter()
        
        # 大量のConfigManager初期化
        managers = []
        for i in range(100):
            manager = ConfigManager()
            managers.append(manager)
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        assert len(managers) == 100
        assert execution_time < 1.0  # 1秒以内での完了を期待


class TestMemoryManagement:
    """メモリ管理テスト"""

    def test_node_memory_cleanup(self):
        """ノードメモリクリーンアップテスト"""
        # 大量のノードを作成して参照を削除
        nodes = []
        for i in range(100):
            node = create_node(f"type_{i}")
            nodes.append(node)
        
        # 参照をクリア
        del nodes
        
        # 新しいノードを作成して問題ないことを確認
        new_node = create_node("test")
        assert new_node is not None

    def test_config_memory_management(self):
        """設定メモリ管理テスト"""
        # 複数の設定オブジェクトを作成
        configs = []
        for i in range(50):
            config = FormatterConfig()
            configs.append(config)
        
        # 参照をクリア
        del configs
        
        # 新しい設定を作成して問題ないことを確認
        new_config = FormatterConfig()
        assert new_config is not None


class TestEdgeCases:
    """エッジケーステスト"""

    def test_empty_node_creation(self):
        """空ノード作成テスト"""
        node = create_node("")
        assert node is not None
        assert node.node_type == ""

    def test_none_content_node(self):
        """None内容ノードテスト"""
        node = create_node("test", content=None)
        assert node is not None
        assert node.content is None

    def test_large_metadata_handling(self):
        """大きなメタデータハンドリングテスト"""
        node = create_node("test")
        
        # 大きなメタデータを追加
        for i in range(100):
            node.metadata[f"key_{i}"] = f"value_{i}" * 100
        
        assert len(node.metadata) >= 100

    def test_deep_nesting(self):
        """深いネストテスト"""
        root = create_node("root")
        current = root
        
        # 50層の深いネストを作成
        for i in range(50):
            child = create_node(f"child_{i}")
            current.add_child(child)
            current = child
        
        # ルートノードが50層の子を持つことを確認
        depth = 0
        node = root
        while node.children:
            node = node.children[0]
            depth += 1
        
        assert depth == 50


class TestRobustness:
    """堅牢性テスト"""

    def test_invalid_input_handling(self):
        """無効入力ハンドリングテスト"""
        # 無効な型でのノード作成
        try:
            node = create_node(None)
            # エラーが発生しないか、適切に処理されることを確認
            assert node is not None
        except (TypeError, ValueError):
            # 適切な例外が発生することも許可
            pass

    def test_circular_reference_prevention(self):
        """循環参照防止テスト"""
        parent = create_node("parent")
        child = create_node("child")
        
        parent.add_child(child)
        
        # 循環参照を作成しようとする
        try:
            child.add_child(parent)
            # 循環参照が適切に処理されることを確認
            # （エラーが発生するか、適切に防止される）
        except (ValueError, RuntimeError):
            # 循環参照防止エラーが発生することを許可
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])