"""
テストモジュール: Phase 1 混在禁止ルールの検証

このモジュールでは Issue #679 で実装された混在禁止ルールを包括的にテストします。
- 半角・全角マーカー混在の検出
- color属性大文字小文字混在の検出
- 適切なエラーメッセージの生成
"""

import pytest

from kumihan_formatter.core.syntax.syntax_errors import ErrorSeverity
from kumihan_formatter.core.syntax.syntax_rules import SyntaxRules
from kumihan_formatter.core.syntax.syntax_validator import KumihanSyntaxValidator


@pytest.mark.unit
@pytest.mark.core
class TestMarkerMixingRules:
    """半角・全角マーカー混在禁止ルールのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.validator = KumihanSyntaxValidator()

    def test_valid_half_width_markers_only(self):
        """半角マーカーのみの場合は問題なし"""
        valid_texts = [
            "#太字 重要な情報# と #下線 強調情報#",
            "#見出し1\n内容\n##",
            "#太字 A##下線 B##斜体 C#",
        ]

        for text in valid_texts:
            violations = SyntaxRules.check_marker_mixing(text)
            assert len(violations) == 0, f"半角マーカーのみでエラー: {text}"

    def test_valid_full_width_markers_only(self):
        """全角マーカーのみの場合は問題なし"""
        valid_texts = [
            "＃太字 重要な情報＃ と ＃下線 強調情報＃",
            "＃見出し1\n内容\n＃＃",
            "＃太字 A＃＃下線 B＃＃斜体 C＃",
        ]

        for text in valid_texts:
            violations = SyntaxRules.check_marker_mixing(text)
            assert len(violations) == 0, f"全角マーカーのみでエラー: {text}"

    def test_invalid_marker_mixing(self):
        """半角・全角マーカー混在の検出"""
        invalid_texts = [
            "#太字 重要な情報# と ＃下線 強調情報＃",
            "＃見出し1\n内容\n##",
            "#太字 A＃＃下線 B##斜体 C#",
            "＃太字 重要＃テキスト#下線 強調#",
        ]

        for text in invalid_texts:
            violations = SyntaxRules.check_marker_mixing(text)
            assert len(violations) > 0, f"混在を検出できませんでした: {text}"
            assert (
                "半角マーカー（#）と全角マーカー（＃）の混在は禁止されています"
                in violations[0]
            )

    def test_marker_mixing_validator_integration(self):
        """バリデーターとの統合テスト"""
        mixed_text = "#太字 重要な情報# と ＃下線 強調情報＃が混在。"

        errors = self.validator.validate_text(mixed_text)

        # エラーが検出されることを確認
        assert len(errors) > 0

        # 適切なエラーメッセージとレベルを確認
        mixing_errors = [e for e in errors if "混在" in str(e.message)]
        assert len(mixing_errors) > 0

        # エラーレベルが適切であることを確認
        for error in mixing_errors:
            assert error.severity == ErrorSeverity.ERROR

    def test_edge_cases(self):
        """エッジケース: マーカーが含まれない場合など"""
        edge_cases = [
            "",  # 空文字
            "マーカーなしのテキスト",
            "HTMLタグ<p>テスト</p>",
            "数式 x # y = z",  # 数学記号としての#
        ]

        for text in edge_cases:
            violations = SyntaxRules.check_marker_mixing(text)
            assert len(violations) == 0, f"エッジケースでエラー: {text}"


@pytest.mark.unit
@pytest.mark.core
class TestColorCaseMixingRules:
    """color属性大文字小文字混在禁止ルールのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.validator = KumihanSyntaxValidator()

    def test_valid_lowercase_colors_only(self):
        """小文字色名のみの場合は問題なし"""
        valid_texts = [
            "#太字 color=red テキスト# と #下線 color=blue 内容#",
            "#見出し1 color=green\n内容\n##",
            "#太字 color=yellow##下線 color=purple#",
        ]

        for text in valid_texts:
            violations = SyntaxRules.check_color_case_mixing(text)
            assert len(violations) == 0, f"小文字のみでエラー: {text}"

    def test_valid_uppercase_colors_only(self):
        """大文字色名のみの場合は問題なし"""
        valid_texts = [
            "#太字 color=RED テキスト# と #下線 color=BLUE 内容#",
            "#見出し1 color=GREEN\n内容\n##",
            "#太字 color=YELLOW##下線 color=PURPLE#",
        ]

        for text in valid_texts:
            violations = SyntaxRules.check_color_case_mixing(text)
            assert len(violations) == 0, f"大文字のみでエラー: {text}"

    def test_valid_mixed_case_colors_only(self):
        """混在表記（頭文字大文字など）のみの場合は問題なし"""
        valid_texts = [
            "#太字 color=Red テキスト# と #下線 color=Blue 内容#",
            "#見出し1 color=Green\n内容\n##",
            "#太字 color=Yellow##下線 color=Purple#",
        ]

        for text in valid_texts:
            violations = SyntaxRules.check_color_case_mixing(text)
            assert len(violations) == 0, f"混在表記のみでエラー: {text}"

    def test_invalid_color_case_mixing(self):
        """大文字小文字混在の検出"""
        invalid_texts = [
            "#太字 color=red テキスト# と #下線 color=BLUE 内容#",  # 小文字 + 大文字
            "#太字 color=RED テキスト# と #下線 color=green 内容#",  # 大文字 + 小文字
            "#太字 color=Red テキスト# と #下線 color=blue 内容#",  # 混在 + 小文字
            "#太字 color=red テキスト# と #下線 color=Blue 内容#",  # 小文字 + 混在
            "#太字 color=RED テキスト# と #下線 color=Blue 内容#",  # 大文字 + 混在
        ]

        for text in invalid_texts:
            violations = SyntaxRules.check_color_case_mixing(text)
            assert len(violations) > 0, f"色名混在を検出できませんでした: {text}"
            assert (
                "color属性で大文字・小文字・混在表記の混用は禁止されています"
                in violations[0]
            )

    def test_hex_colors_not_affected(self):
        """16進数カラーコードは大文字小文字混在チェック対象外"""
        hex_color_texts = [
            "#太字 color=#ff0000 テキスト# と #下線 color=#00FF00 内容#",
            "#太字 color=#AbCdEf テキスト#",
        ]

        for text in hex_color_texts:
            violations = SyntaxRules.check_color_case_mixing(text)
            assert len(violations) == 0, f"16進数カラーでエラー: {text}"

    def test_color_mixing_validator_integration(self):
        """バリデーターとの統合テスト"""
        mixed_text = "#太字 color=red 小文字# と #下線 color=BLUE 大文字#が混在。"

        errors = self.validator.validate_text(mixed_text)

        # エラーが検出されることを確認
        assert len(errors) > 0

        # 適切なエラーメッセージとレベルを確認
        color_errors = [e for e in errors if "color属性" in str(e.message)]
        assert len(color_errors) > 0

        # エラーレベルが適切であることを確認
        for error in color_errors:
            assert error.severity == ErrorSeverity.ERROR

    def test_no_color_attributes(self):
        """color属性がない場合は問題なし"""
        no_color_texts = [
            "#太字 重要な情報##下線 強調内容#",
            "#見出し1\n内容\n##",
            "通常のテキスト",
        ]

        for text in no_color_texts:
            violations = SyntaxRules.check_color_case_mixing(text)
            assert len(violations) == 0, f"color属性なしでエラー: {text}"


@pytest.mark.unit
@pytest.mark.core
class TestMixingRulesComprehensive:
    """混在禁止ルール全体の包括的テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.validator = KumihanSyntaxValidator()

    def test_multiple_violations(self):
        """複数の違反が同時に発生する場合"""
        complex_text = "＃太字 color=red 内容＃ と #下線 color=BLUE 内容#"

        errors = self.validator.validate_text(complex_text)

        # マーカー混在とcolor混在の両方が検出されることを確認
        marker_errors = [
            e
            for e in errors
            if "マーカー" in str(e.message) and "混在" in str(e.message)
        ]
        color_errors = [e for e in errors if "color属性" in str(e.message)]

        assert len(marker_errors) > 0, "マーカー混在エラーが検出されませんでした"
        assert len(color_errors) > 0, "color属性混在エラーが検出されませんでした"

    def test_complex_document_structure(self):
        """複雑なドキュメント構造での混在チェック"""
        complex_document = """
#見出し1
メインコンテンツ
##

段落テキストに#太字 color=red 重要##下線 color=BLUE 強調#が含まれます。

＃見出し2
サブコンテンツ
＃＃

最後の段落も#太字 最終情報#で終了。
        """

        errors = self.validator.validate_text(complex_document)

        # 混在エラーが適切に検出されることを確認
        mixing_errors = [e for e in errors if "混在" in str(e.message)]
        assert len(mixing_errors) > 0, "複雑な構造での混在が検出されませんでした"

    def test_performance_with_large_text(self):
        """大きなテキストでの性能確認"""
        # 1000行のテキストを生成
        large_text_lines = []
        for i in range(1000):
            if i % 2 == 0:
                large_text_lines.append(f"#太字 行{i}の内容#")
            else:
                large_text_lines.append(f"通常テキスト 行{i}")

        large_text = "\n".join(large_text_lines)

        # パフォーマンステスト（タイムアウトしないことを確認）
        import time

        start_time = time.time()

        errors = self.validator.validate_text(large_text)

        end_time = time.time()
        processing_time = end_time - start_time

        # 5秒以内に処理が完了することを確認
        assert (
            processing_time < 5.0
        ), f"処理に{processing_time:.2f}秒かかりました（目標: 5秒以内）"

        # エラーが適切に処理されることを確認
        assert isinstance(errors, list), "エラーリストが返されませんでした"
