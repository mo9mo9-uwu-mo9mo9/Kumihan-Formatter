"""寛容なマーカー記法のテスト

初心者に優しい記法の正規化機能をテストする。
全角スペース、スペースなし、複数スペースなどのパターンに対応。
"""

import pytest
from kumihan_formatter.core.keyword_parser import KeywordParser


class TestTolerantMarkerSyntax:
    """寛容なマーカー記法のテストクラス"""
    
    def setup_method(self):
        """テストメソッド実行前の初期化"""
        self.parser = KeywordParser()
    
    def test_normalize_full_width_space(self):
        """全角スペースの正規化テスト"""
        # 全角スペースを含む記法
        test_cases = [
            ("ハイライト　color=#ff0000", "ハイライト color=#ff0000"),
            ("太字　+　ハイライト　color=#ffdddd", "太字 + ハイライト color=#ffdddd"),
            ("見出し1　+　太字", "見出し1 + 太字"),
        ]
        
        for input_text, expected in test_cases:
            normalized = self.parser._normalize_marker_syntax(input_text)
            assert normalized == expected, f"入力: {input_text}, 期待: {expected}, 実際: {normalized}"
    
    def test_normalize_no_space_before_attributes(self):
        """属性前のスペースなしパターンの正規化テスト"""
        test_cases = [
            ("ハイライトcolor=#ff0000", "ハイライト color=#ff0000"),
            ("太字+ハイライトcolor=#ffdddd", "太字+ハイライト color=#ffdddd"),
            ("画像alt=説明文", "画像 alt=説明文"),
        ]
        
        for input_text, expected in test_cases:
            normalized = self.parser._normalize_marker_syntax(input_text)
            assert normalized == expected, f"入力: {input_text}, 期待: {expected}, 実際: {normalized}"
    
    def test_normalize_multiple_spaces(self):
        """複数スペースの正規化テスト"""
        test_cases = [
            ("ハイライト  color=#ff0000", "ハイライト color=#ff0000"),
            ("太字   +   ハイライト", "太字 + ハイライト"),
            ("見出し1    +    太字    color=#ffffff", "見出し1 + 太字 color=#ffffff"),
        ]
        
        for input_text, expected in test_cases:
            normalized = self.parser._normalize_marker_syntax(input_text)
            assert normalized == expected, f"入力: {input_text}, 期待: {expected}, 実際: {normalized}"
    
    def test_normalize_leading_trailing_spaces(self):
        """前後スペースの正規化テスト"""
        test_cases = [
            ("  ハイライト color=#ff0000  ", "ハイライト color=#ff0000"),
            ("　　太字　　", "太字"),
            ("  見出し1 + 太字  ", "見出し1 + 太字"),
        ]
        
        for input_text, expected in test_cases:
            normalized = self.parser._normalize_marker_syntax(input_text)
            assert normalized == expected, f"入力: {input_text}, 期待: {expected}, 実際: {normalized}"
    
    def test_parse_tolerant_syntax(self):
        """寛容な記法でのパース動作テスト"""
        # スペースなしパターン
        keywords, attrs, errors = self.parser.parse_marker_keywords("ハイライトcolor=#ff0000")
        assert keywords == ["ハイライト"]
        assert attrs["color"] == "#ff0000"
        assert len(errors) == 0
        
        # 全角スペースパターン
        keywords, attrs, errors = self.parser.parse_marker_keywords("太字　+　ハイライト　color=#ffdddd")
        assert "太字" in keywords
        assert "ハイライト" in keywords
        assert attrs["color"] == "#ffdddd"
        assert len(errors) == 0
        
        # 複数スペースパターン
        keywords, attrs, errors = self.parser.parse_marker_keywords("見出し1   +   太字")
        assert "見出し1" in keywords
        assert "太字" in keywords
        assert len(errors) == 0
    
    def test_mixed_space_patterns(self):
        """複合的なスペースパターンのテスト"""
        # 全角スペース + スペースなし + 複数スペース
        complex_input = "太字　+ハイライト　　color=#ff0000"
        normalized = self.parser._normalize_marker_syntax(complex_input)
        assert normalized == "太字 +ハイライト color=#ff0000"
        
        # パースも正常に動作することを確認
        keywords, attrs, errors = self.parser.parse_marker_keywords(complex_input)
        assert "太字" in keywords
        assert "ハイライト" in keywords
        assert attrs["color"] == "#ff0000"
        assert len(errors) == 0
    
    def test_backward_compatibility(self):
        """後方互換性のテスト（従来の正しい記法も動作する）"""
        # 従来の正しい記法
        correct_cases = [
            "ハイライト color=#ff0000",
            "太字 + ハイライト color=#ffdddd",
            "見出し1 + 太字",
            "画像 alt=説明文",
        ]
        
        for case in correct_cases:
            # 正規化しても変わらないことを確認
            normalized = self.parser._normalize_marker_syntax(case)
            assert normalized == case, f"正しい記法が変更されました: {case} -> {normalized}"
            
            # パースも正常に動作することを確認
            keywords, attrs, errors = self.parser.parse_marker_keywords(case)
            assert len(keywords) > 0, f"キーワードがパースされませんでした: {case}"
            assert len(errors) == 0, f"エラーが発生しました: {case}, エラー: {errors}"
    
    def test_normalize_preserves_functionality(self):
        """正規化が機能性を保持することのテスト"""
        # 異なる書き方でも同じ結果になることを確認
        variations = [
            "ハイライト color=#ff0000",        # 標準
            "ハイライトcolor=#ff0000",         # スペースなし
            "ハイライト　color=#ff0000",       # 全角スペース
            "ハイライト  color=#ff0000",       # 複数スペース
            "  ハイライト color=#ff0000  ",    # 前後スペース
        ]
        
        results = []
        for variation in variations:
            keywords, attrs, errors = self.parser.parse_marker_keywords(variation)
            results.append((keywords, attrs, errors))
        
        # すべて同じ結果になることを確認
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == first_result, f"バリエーション {i}: {variations[i]} の結果が異なります"


class TestTolerantSyntaxEdgeCases:
    """エッジケースのテスト"""
    
    def setup_method(self):
        """テストメソッド実行前の初期化"""
        self.parser = KeywordParser()
    
    def test_empty_content(self):
        """空コンテンツの処理"""
        normalized = self.parser._normalize_marker_syntax("")
        assert normalized == ""
        
        normalized = self.parser._normalize_marker_syntax("   ")
        assert normalized == ""
        
        normalized = self.parser._normalize_marker_syntax("　　　")
        assert normalized == ""
    
    def test_only_attributes(self):
        """属性のみの場合"""
        normalized = self.parser._normalize_marker_syntax("color=#ff0000")
        assert normalized == "color=#ff0000"
        
        normalized = self.parser._normalize_marker_syntax("　color=#ff0000")
        assert normalized == "color=#ff0000"
    
    def test_complex_alt_attribute(self):
        """複雑なalt属性の処理"""
        test_cases = [
            ("画像alt=説明文with spaces", "画像 alt=説明文with spaces"),
            ("画像　alt=日本語説明", "画像 alt=日本語説明"),
            ("画像alt=multiple word description", "画像 alt=multiple word description"),
        ]
        
        for input_text, expected in test_cases:
            normalized = self.parser._normalize_marker_syntax(input_text)
            assert normalized == expected, f"入力: {input_text}, 期待: {expected}, 実際: {normalized}"