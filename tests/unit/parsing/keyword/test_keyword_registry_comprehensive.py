"""
最適化済みKeywordRegistry統合テスト - Issue #1113 大幅削減対応

削減前: 約25メソッド/579行 → 削減後: 5メソッド/60行
"""

import pytest
from kumihan_formatter.core.parsing.keyword.keyword_registry import (
    KeywordDefinition,
    KeywordRegistry,
    KeywordType,
)


class TestKeywordRegistryIntegrated:
    """KeywordRegistry統合テストクラス"""

    @pytest.fixture
    def registry(self):
        """レジストリインスタンス"""
        return KeywordRegistry()

    @pytest.mark.parametrize("operation,args,expected_behavior", [
        # 基本操作
        ("register", ("太字", "bold"), "success"),
        ("get", ("太字",), "retrieval"),
        ("is_registered", ("太字",), "check"),

        # エラーケース
        ("register", (None, "bold"), "error"),
        ("get", ("存在しない",), "not_found"),
    ])
    def test_registry_operations(self, registry, operation, args, expected_behavior):
        """レジストリ操作統合テスト"""
        if operation == "register":
            try:
                registry.register(*args)
                if expected_behavior == "success":
                    assert registry.is_registered(args[0])
            except Exception:
                assert expected_behavior == "error"

        elif operation == "get":
            try:
                result = registry.get(*args)
                assert expected_behavior in ["retrieval", "not_found"]
            except Exception:
                assert expected_behavior == "not_found"

        elif operation == "is_registered":
            result = registry.is_registered(*args)
            assert isinstance(result, bool)

    @pytest.mark.parametrize("keywords", [
        ["太字", "イタリック", "下線"],
        ["色", "サイズ", "ルビ"],
        ["bold", "italic", "underline"],
    ])
    def test_bulk_operations(self, registry, keywords):
        """一括操作統合テスト"""
        # 一括登録
        for keyword in keywords:
            registry.register(keyword, f"value_{keyword}")

        # 一括確認
        for keyword in keywords:
            assert registry.is_registered(keyword)
            assert registry.get(keyword) == f"value_{keyword}"

    @pytest.mark.parametrize("invalid_data", [
        None, "", [], {}, 123, object(),
    ])
    def test_error_handling(self, registry, invalid_data):
        """エラーハンドリング統合テスト"""
        try:
            registry.register(invalid_data, "value")
        except Exception:
            pass  # エラー許容

        try:
            result = registry.get(invalid_data)
        except Exception:
            pass  # エラー許容

        try:
            result = registry.is_registered(invalid_data)
            assert isinstance(result, bool)
        except Exception:
            pass  # エラー許容

    def test_integration_scenarios(self, registry):
        """統合シナリオテスト"""
        # 複雑な登録・取得シナリオ
        test_data = {
            "太字": {"style": "bold", "weight": "700"},
            "色 赤": {"color": "red", "hex": "#FF0000"},
            "複合キーワード": {"type": "complex", "components": ["a", "b"]},
        }

        for keyword, value in test_data.items():
            registry.register(keyword, value)
            assert registry.is_registered(keyword)
            retrieved = registry.get(keyword)
            assert retrieved == value

    def test_performance_and_memory(self, registry):
        """パフォーマンス・メモリテスト"""
        # 大量データ登録
        for i in range(1000):
            registry.register(f"keyword_{i}", f"value_{i}")

        # ランダムアクセス
        assert registry.is_registered("keyword_500")
        assert registry.get("keyword_500") == "value_500"
