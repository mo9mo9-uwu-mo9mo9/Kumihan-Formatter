"""
KeywordRegistry包括的テストスイート - Issue #929対応

カバレッジ向上目標: 19% → 60%
多言語対応、キーワード登録・検索・管理、型システムの完全テスト
"""

import pytest
from typing import Dict, List, Optional
from unittest.mock import Mock, patch

from kumihan_formatter.core.parsing.keyword.keyword_registry import (
    KeywordDefinition,
    KeywordRegistry,
    KeywordType,
)


class TestKeywordTypeEnum:
    """KeywordType列挙型テスト"""

    def test_キーワードタイプ値(self):
        """KeywordType列挙値の確認"""
        assert KeywordType.DECORATION.value == "decoration"
        assert KeywordType.LAYOUT.value == "layout"
        assert KeywordType.STRUCTURE.value == "structure"
        assert KeywordType.CONTENT.value == "content"

    def test_すべてのタイプ列挙(self):
        """すべてのKeywordTypeが定義されていることを確認"""
        expected_types = ["DECORATION", "LAYOUT", "STRUCTURE", "CONTENT"]
        actual_types = [item.name for item in KeywordType]
        
        for expected in expected_types:
            assert expected in actual_types


class TestKeywordDefinition:
    """KeywordDefinition データクラステスト"""

    def test_基本定義作成(self):
        """基本的なKeywordDefinition作成テスト"""
        definition = KeywordDefinition(
            keyword_id="test_keyword",
            display_names={"ja": "テスト", "en": "test"},
            tag="div",
            keyword_type=KeywordType.DECORATION
        )
        
        assert definition.keyword_id == "test_keyword"
        assert definition.display_names["ja"] == "テスト"
        assert definition.display_names["en"] == "test"
        assert definition.tag == "div"
        assert definition.keyword_type == KeywordType.DECORATION

    def test_完全定義作成(self):
        """全フィールドを含むKeywordDefinition作成テスト"""
        definition = KeywordDefinition(
            keyword_id="full_keyword",
            display_names={"ja": "完全", "en": "full"},
            tag="span",
            keyword_type=KeywordType.LAYOUT,
            attributes={"class": "test-class"},
            special_options={"wrap": True},
            css_requirements=["test-css", "another-css"],
            description={"ja": "テスト説明", "en": "test description"}
        )
        
        assert definition.attributes == {"class": "test-class"}
        assert definition.special_options == {"wrap": True}
        assert definition.css_requirements == ["test-css", "another-css"]
        assert definition.description["ja"] == "テスト説明"

    def test_デフォルト値(self):
        """Optional フィールドのデフォルト値テスト"""
        definition = KeywordDefinition(
            keyword_id="minimal",
            display_names={"ja": "最小"},
            tag="p",
            keyword_type=KeywordType.CONTENT
        )
        
        assert definition.attributes is None
        assert definition.special_options is None
        assert definition.css_requirements is None
        assert definition.description is None


class TestKeywordRegistryCore:
    """KeywordRegistry コア機能テスト"""

    def test_初期化_デフォルト言語(self):
        """デフォルト言語での初期化テスト"""
        registry = KeywordRegistry()
        
        assert registry.default_language == "ja"
        assert isinstance(registry.keywords, dict)
        assert isinstance(registry._language_mappings, dict)

    def test_初期化_カスタム言語(self):
        """カスタム言語での初期化テスト"""
        registry = KeywordRegistry(default_language="en")
        
        assert registry.default_language == "en"

    def test_事前登録キーワード確認(self):
        """事前登録されたキーワードの確認"""
        registry = KeywordRegistry()
        
        # 高度なキーワードが登録されていることを確認
        assert "underline" in registry.keywords
        assert "strikethrough" in registry.keywords
        assert "inline_code" in registry.keywords
        assert "blockquote" in registry.keywords

    def test_既存キーワード確認(self):
        """既存（後方互換）キーワードの確認"""
        registry = KeywordRegistry()
        
        # 既存キーワードが登録されていることを確認
        assert "bold" in registry.keywords
        assert "italic" in registry.keywords
        assert "heading1" in registry.keywords


class TestKeywordRegistryOperations:
    """KeywordRegistry 操作機能テスト"""

    def test_キーワード登録(self):
        """register_keyword メソッドのテスト"""
        registry = KeywordRegistry()
        
        new_definition = KeywordDefinition(
            keyword_id="custom_test",
            display_names={"ja": "カスタム", "en": "custom"},
            tag="div",
            keyword_type=KeywordType.DECORATION
        )
        
        registry.register_keyword(new_definition)
        
        assert "custom_test" in registry.keywords
        assert registry.keywords["custom_test"] == new_definition

    def test_キーワード登録_言語マッピング更新(self):
        """キーワード登録時の言語マッピング更新テスト"""
        registry = KeywordRegistry()
        
        new_definition = KeywordDefinition(
            keyword_id="mapping_test",
            display_names={"ja": "マッピング", "en": "mapping", "fr": "cartographie"},
            tag="span",
            keyword_type=KeywordType.LAYOUT
        )
        
        registry.register_keyword(new_definition)
        
        # 日本語マッピングの確認
        assert "マッピング" in registry._language_mappings["ja"]
        assert registry._language_mappings["ja"]["マッピング"] == "mapping_test"
        
        # 英語マッピングの確認
        assert "mapping" in registry._language_mappings["en"]
        assert registry._language_mappings["en"]["mapping"] == "mapping_test"
        
        # フランス語マッピングの確認
        assert "cartographie" in registry._language_mappings["fr"]
        assert registry._language_mappings["fr"]["cartographie"] == "mapping_test"

    def test_表示名によるキーワード取得_デフォルト言語(self):
        """get_keyword_by_display_name デフォルト言語テスト"""
        registry = KeywordRegistry()
        
        result = registry.get_keyword_by_display_name("下線")
        
        assert result is not None
        assert result.keyword_id == "underline"

    def test_表示名によるキーワード取得_指定言語(self):
        """get_keyword_by_display_name 指定言語テスト"""
        registry = KeywordRegistry()
        
        result = registry.get_keyword_by_display_name("underline", language="en")
        
        assert result is not None
        assert result.keyword_id == "underline"

    def test_表示名によるキーワード取得_存在しない(self):
        """get_keyword_by_display_name 存在しないキーワードテスト"""
        registry = KeywordRegistry()
        
        result = registry.get_keyword_by_display_name("存在しないキーワード")
        
        assert result is None

    def test_IDによるキーワード取得(self):
        """get_keyword_by_id メソッドのテスト"""
        registry = KeywordRegistry()
        
        result = registry.get_keyword_by_id("underline")
        
        assert result is not None
        assert result.keyword_id == "underline"
        assert result.display_names["ja"] == "下線"

    def test_IDによるキーワード取得_存在しない(self):
        """get_keyword_by_id 存在しないIDテスト"""
        registry = KeywordRegistry()
        
        result = registry.get_keyword_by_id("nonexistent_id")
        
        assert result is None


class TestKeywordRegistryLanguageSupport:
    """KeywordRegistry 多言語サポートテスト"""

    def test_全表示名取得_デフォルト言語(self):
        """get_all_display_names デフォルト言語テスト"""
        registry = KeywordRegistry()
        
        display_names = registry.get_all_display_names()
        
        assert isinstance(display_names, list)
        assert "下線" in display_names
        assert "太字" in display_names

    def test_全表示名取得_英語(self):
        """get_all_display_names 英語テスト"""
        registry = KeywordRegistry()
        
        display_names = registry.get_all_display_names(language="en")
        
        assert isinstance(display_names, list)
        assert "underline" in display_names
        assert "bold" in display_names

    def test_サポート言語取得(self):
        """get_supported_languages メソッドのテスト"""
        registry = KeywordRegistry()
        
        languages = registry.get_supported_languages()
        
        assert isinstance(languages, list)
        assert "ja" in languages
        assert "en" in languages

    def test_言語切り替え_成功(self):
        """switch_language 成功テスト"""
        registry = KeywordRegistry()
        
        result = registry.switch_language("en")
        
        assert result is True
        assert registry.default_language == "en"

    def test_言語切り替え_失敗(self):
        """switch_language 失敗テスト"""
        registry = KeywordRegistry()
        
        result = registry.switch_language("xx")  # 存在しない言語コード
        
        assert result is False
        assert registry.default_language == "ja"  # 元のまま


class TestKeywordRegistryTypeBased:
    """KeywordRegistry タイプベース機能テスト"""

    def test_タイプ別キーワード取得_DECORATION(self):
        """get_keywords_by_type DECORATION テスト"""
        registry = KeywordRegistry()
        
        decoration_keywords = registry.get_keywords_by_type(KeywordType.DECORATION)
        
        assert isinstance(decoration_keywords, list)
        assert len(decoration_keywords) > 0
        
        # すべてがDECORATIONタイプであることを確認
        for keyword in decoration_keywords:
            assert keyword.keyword_type == KeywordType.DECORATION

    def test_タイプ別キーワード取得_LAYOUT(self):
        """get_keywords_by_type LAYOUT テスト"""
        registry = KeywordRegistry()
        
        layout_keywords = registry.get_keywords_by_type(KeywordType.LAYOUT)
        
        assert isinstance(layout_keywords, list)
        assert len(layout_keywords) > 0
        
        for keyword in layout_keywords:
            assert keyword.keyword_type == KeywordType.LAYOUT

    def test_タイプ別キーワード取得_STRUCTURE(self):
        """get_keywords_by_type STRUCTURE テスト"""
        registry = KeywordRegistry()
        
        structure_keywords = registry.get_keywords_by_type(KeywordType.STRUCTURE)
        
        assert isinstance(structure_keywords, list)
        assert len(structure_keywords) > 0
        
        for keyword in structure_keywords:
            assert keyword.keyword_type == KeywordType.STRUCTURE

    def test_タイプ別キーワード取得_CONTENT(self):
        """get_keywords_by_type CONTENT テスト"""
        registry = KeywordRegistry()
        
        content_keywords = registry.get_keywords_by_type(KeywordType.CONTENT)
        
        assert isinstance(content_keywords, list)
        assert len(content_keywords) > 0
        
        for keyword in content_keywords:
            assert keyword.keyword_type == KeywordType.CONTENT


class TestKeywordRegistryLegacyCompatibility:
    """KeywordRegistry 従来形式互換性テスト"""

    def test_従来形式変換_デフォルト言語(self):
        """convert_to_legacy_format デフォルト言語テスト"""
        registry = KeywordRegistry()
        
        legacy_dict = registry.convert_to_legacy_format()
        
        assert isinstance(legacy_dict, dict)
        assert "下線" in legacy_dict
        assert legacy_dict["下線"]["tag"] == "u"

    def test_従来形式変換_英語(self):
        """convert_to_legacy_format 英語テスト"""
        registry = KeywordRegistry()
        
        legacy_dict = registry.convert_to_legacy_format(language="en")
        
        assert isinstance(legacy_dict, dict)
        assert "underline" in legacy_dict
        assert legacy_dict["underline"]["tag"] == "u"

    def test_従来形式変換_属性含む(self):
        """convert_to_legacy_format 属性を含むキーワードテスト"""
        registry = KeywordRegistry()
        
        legacy_dict = registry.convert_to_legacy_format()
        
        # 属性を持つキーワードの確認（center_align等）
        assert "中央寄せ" in legacy_dict
        center_entry = legacy_dict["中央寄せ"]
        assert center_entry["tag"] == "div"
        assert "style" in center_entry

    def test_従来形式変換_特殊オプション含む(self):
        """convert_to_legacy_format 特殊オプションを含むキーワードテスト"""
        registry = KeywordRegistry()
        
        legacy_dict = registry.convert_to_legacy_format()
        
        # 特殊オプションを持つキーワードの確認
        assert "コードブロック" in legacy_dict
        code_entry = legacy_dict["コードブロック"]
        assert code_entry["tag"] == "pre"


class TestKeywordRegistryAdvancedFeatures:
    """KeywordRegistry 高度機能テスト"""

    def test_CSS要件キーワード確認(self):
        """CSS要件を持つキーワードの確認"""
        registry = KeywordRegistry()
        
        warning_keyword = registry.get_keyword_by_display_name("注意")
        
        assert warning_keyword is not None
        assert warning_keyword.css_requirements is not None
        assert "alert" in warning_keyword.css_requirements
        assert "warning" in warning_keyword.css_requirements

    def test_特殊オプションキーワード確認(self):
        """特殊オプションを持つキーワードの確認"""
        registry = KeywordRegistry()
        
        code_block_keyword = registry.get_keyword_by_display_name("コードブロック")
        
        assert code_block_keyword is not None
        assert code_block_keyword.special_options is not None
        assert code_block_keyword.special_options.get("wrap_with_code") is True

    def test_説明フィールドキーワード確認(self):
        """説明フィールドを持つキーワードの確認"""
        registry = KeywordRegistry()
        
        underline_keyword = registry.get_keyword_by_display_name("下線")
        
        assert underline_keyword is not None
        assert underline_keyword.description is not None
        assert underline_keyword.description["ja"] == "テキストに下線を追加"
        assert underline_keyword.description["en"] == "Add underline to text"


class TestKeywordRegistryEdgeCases:
    """KeywordRegistry エッジケーステスト"""

    def test_空の表示名辞書(self):
        """空の表示名辞書を持つキーワード登録テスト"""
        registry = KeywordRegistry()
        
        empty_definition = KeywordDefinition(
            keyword_id="empty_names",
            display_names={},
            tag="div",
            keyword_type=KeywordType.DECORATION
        )
        
        registry.register_keyword(empty_definition)
        
        # 従来形式変換時に表示されないことを確認
        legacy_dict = registry.convert_to_legacy_format()
        assert "empty_names" not in legacy_dict.values()

    def test_存在しない言語での表示名取得(self):
        """存在しない言語での表示名取得テスト"""
        registry = KeywordRegistry()
        
        display_names = registry.get_all_display_names(language="nonexistent")
        
        assert display_names == []

    def test_None言語での表示名取得(self):
        """None言語での表示名取得テスト（デフォルト使用）"""
        registry = KeywordRegistry()
        
        display_names = registry.get_all_display_names(language=None)
        
        # デフォルト言語(ja)での取得と同じ結果になることを確認
        default_names = registry.get_all_display_names()
        assert display_names == default_names

    def test_重複キーワード登録(self):
        """重複するキーワードIDの登録テスト"""
        registry = KeywordRegistry()
        
        # 既存のunderlineキーワードと同じIDで新しい定義を作成
        duplicate_definition = KeywordDefinition(
            keyword_id="underline",
            display_names={"ja": "新下線", "en": "new_underline"},
            tag="span",
            keyword_type=KeywordType.LAYOUT
        )
        
        registry.register_keyword(duplicate_definition)
        
        # 新しい定義で上書きされることを確認
        retrieved = registry.get_keyword_by_id("underline")
        assert retrieved.display_names["ja"] == "新下線"
        assert retrieved.tag == "span"


class TestKeywordRegistryPerformance:
    """KeywordRegistry パフォーマンステスト"""

    def test_大量キーワード登録(self):
        """大量キーワード登録のパフォーマンステスト"""
        registry = KeywordRegistry()
        
        # 100個のテストキーワードを登録
        for i in range(100):
            definition = KeywordDefinition(
                keyword_id=f"test_{i}",
                display_names={"ja": f"テスト{i}", "en": f"test{i}"},
                tag="div",
                keyword_type=KeywordType.DECORATION
            )
            registry.register_keyword(definition)
        
        # すべて正常に登録されたことを確認
        assert len(registry.keywords) >= 100
        
        # 言語マッピングも正常に更新されていることを確認
        ja_names = registry.get_all_display_names()
        en_names = registry.get_all_display_names(language="en")
        
        assert len(ja_names) >= 100
        assert len(en_names) >= 100

    def test_大量検索操作(self):
        """大量検索操作のパフォーマンステスト"""
        registry = KeywordRegistry()
        
        # 既存のキーワードに対して大量検索を実行
        existing_names = registry.get_all_display_names()
        
        # すべてのキーワードを ID で検索
        for name in existing_names:
            result = registry.get_keyword_by_display_name(name)
            assert result is not None

        # すべてのキーワード ID で検索
        for keyword_id in registry.keywords.keys():
            result = registry.get_keyword_by_id(keyword_id)
            assert result is not None


class TestKeywordRegistryIntegration:
    """KeywordRegistry 統合テスト"""

    def test_複数言語での完全ワークフロー(self):
        """複数言語での完全ワークフローテスト"""
        registry = KeywordRegistry()
        
        # 多言語キーワードを登録
        multilang_definition = KeywordDefinition(
            keyword_id="multilang_test",
            display_names={
                "ja": "多言語テスト",
                "en": "multilang_test",
                "fr": "test_multilingue",
                "de": "mehrsprachiger_test"
            },
            tag="div",
            keyword_type=KeywordType.CONTENT,
            description={
                "ja": "多言語対応テスト",
                "en": "Multilingual support test",
                "fr": "Test de support multilingue",
                "de": "Mehrsprachiger Support-Test"
            }
        )
        
        registry.register_keyword(multilang_definition)
        
        # 各言語での検索テスト
        languages = ["ja", "en", "fr", "de"]
        expected_names = ["多言語テスト", "multilang_test", "test_multilingue", "mehrsprachiger_test"]
        
        for lang, expected_name in zip(languages, expected_names):
            # 表示名での検索
            result = registry.get_keyword_by_display_name(expected_name, language=lang)
            assert result is not None
            assert result.keyword_id == "multilang_test"
            
            # 説明の確認
            assert result.description[lang] is not None
            
            # 言語切り替えテスト
            assert registry.switch_language(lang) is True
            
            # 従来形式変換テスト
            legacy = registry.convert_to_legacy_format(language=lang)
            assert expected_name in legacy

    def test_タイプ別フィルタリング統合(self):
        """タイプ別フィルタリングの統合テスト"""
        registry = KeywordRegistry()
        
        # 全タイプのキーワード数を確認
        all_keywords = list(registry.keywords.values())
        decoration_count = len(registry.get_keywords_by_type(KeywordType.DECORATION))
        layout_count = len(registry.get_keywords_by_type(KeywordType.LAYOUT))
        structure_count = len(registry.get_keywords_by_type(KeywordType.STRUCTURE))
        content_count = len(registry.get_keywords_by_type(KeywordType.CONTENT))
        
        # 全体数がタイプ別の合計と一致することを確認
        total_by_type = decoration_count + layout_count + structure_count + content_count
        assert total_by_type == len(all_keywords)
        
        # 各タイプに少なくとも1つのキーワードがあることを確認
        assert decoration_count > 0
        assert layout_count > 0
        assert structure_count > 0
        assert content_count > 0