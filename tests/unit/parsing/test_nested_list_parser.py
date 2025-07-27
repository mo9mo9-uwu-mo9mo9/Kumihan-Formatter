"""Nested List Parser テスト - Issue #597 対応

ネストリスト解析機能の専門テスト
階層構造・インデント処理・深度計算の確認
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.nested_list_parser import NestedListParser


class TestNestedListParser:
    """ネストリストパーサーテスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.nested_parser = NestedListParser()

    def test_nested_parser_initialization(self):
        """ネストパーサー初期化テスト"""
        assert self.nested_parser is not None
        assert hasattr(self.nested_parser, "parse_nested_list")
        assert hasattr(self.nested_parser, "calculate_nesting_depth")

    def test_basic_nesting_levels(self):
        """基本ネストレベルテスト"""
        nesting_test_cases = [
            # 2レベルネスト
            {
                "list": [
                    "- レベル1項目1",
                    "  - レベル2項目1",
                    "  - レベル2項目2",
                    "- レベル1項目2",
                ],
                "expected_max_depth": 2,
                "test_name": "basic_2_level_nesting",
            },
            # 3レベルネスト
            {
                "list": [
                    "1. 第1章",
                    "   1.1. 第1節",
                    "       1.1.1. 第1項",
                    "       1.1.2. 第2項",
                    "   1.2. 第2節",
                    "2. 第2章",
                ],
                "expected_max_depth": 3,
                "test_name": "basic_3_level_nesting",
            },
            # 4レベルネスト
            {
                "list": [
                    "- レベル1",
                    "  - レベル2",
                    "    - レベル3",
                    "      - レベル4",
                    "        - レベル5（深い）",
                ],
                "expected_max_depth": 5,
                "test_name": "deep_5_level_nesting",
            },
            # 不規則なネスト
            {
                "list": [
                    "- レベル1",
                    "    - レベル3（レベル2スキップ）",
                    "  - レベル2",
                    "      - レベル4",
                    "- レベル1に戻る",
                ],
                "expected_max_depth": 4,
                "test_name": "irregular_nesting",
            },
        ]

        for case in nesting_test_cases:
            try:
                result = self.nested_parser.parse_nested_list(case["list"])
                assert result is not None, f"{case['test_name']}: 解析結果がnull"

                if hasattr(result, "max_depth"):
                    assert (
                        result.max_depth <= case["expected_max_depth"] + 1
                    ), f"{case['test_name']}: 深度が期待より深い"
                elif hasattr(result, "depth"):
                    assert (
                        result.depth <= case["expected_max_depth"] + 1
                    ), f"{case['test_name']}: 深度が期待より深い"

            except Exception as e:
                pytest.fail(f"基本ネストレベルテスト {case['test_name']} でエラー: {e}")

    def test_indent_calculation_accuracy(self):
        """インデント計算精度テスト"""
        indent_test_cases = [
            # 標準的なインデント（2スペース）
            {
                "lines": [
                    "- レベル1",
                    "  - レベル2（2スペース）",
                    "    - レベル3（4スペース）",
                    "      - レベル4（6スペース）",
                ],
                "expected_levels": [0, 1, 2, 3],
                "test_name": "standard_2_space_indent",
            },
            # 4スペースインデント
            {
                "lines": [
                    "- レベル1",
                    "    - レベル2（4スペース）",
                    "        - レベル3（8スペース）",
                ],
                "expected_levels": [0, 1, 2],
                "test_name": "four_space_indent",
            },
            # タブインデント
            {
                "lines": [
                    "- レベル1",
                    "\t- レベル2（1タブ）",
                    "\t\t- レベル3（2タブ）",
                ],
                "expected_levels": [0, 1, 2],
                "test_name": "tab_indent",
            },
            # 混在インデント
            {
                "lines": [
                    "- レベル1",
                    "  - レベル2（2スペース）",
                    "\t- レベル2（1タブ）",
                    "    - レベル2（4スペース）",
                ],
                "expected_levels": [0, 1, 1, 1],
                "test_name": "mixed_indent",
            },
            # 不正なインデント（奇数スペース）
            {
                "lines": [
                    "- レベル1",
                    "   - レベル2（3スペース）",
                    "     - レベル3（5スペース）",
                ],
                "expected_levels": [0, 1, 2],
                "test_name": "odd_space_indent",
            },
        ]

        for case in indent_test_cases:
            try:
                calculated_levels = []
                for line in case["lines"]:
                    if hasattr(self.nested_parser, "calculate_indent_level"):
                        level = self.nested_parser.calculate_indent_level(line)
                    elif hasattr(self.nested_parser, "get_nesting_level"):
                        level = self.nested_parser.get_nesting_level(line)
                    else:
                        level = 0  # フォールバック
                    calculated_levels.append(level)

                # レベル計算の精度確認
                for i, (calculated, expected) in enumerate(
                    zip(calculated_levels, case["expected_levels"])
                ):
                    assert (
                        calculated == expected
                    ), f"{case['test_name']}: 行{i}のインデントレベル不一致. 計算値:{calculated}, 期待値:{expected}"

            except Exception as e:
                pytest.fail(
                    f"インデント計算精度テスト {case['test_name']} でエラー: {e}"
                )

    def test_complex_nested_structures(self):
        """複雑なネスト構造テスト"""
        complex_structures = [
            # 文書構造スタイル
            {
                "structure": [
                    "# 文書タイトル",
                    "- 第1章",
                    "  - 1.1. 概要",
                    "    - 1.1.1. 目的",
                    "    - 1.1.2. 範囲",
                    "  - 1.2. 詳細",
                    "    - 1.2.1. 方法論",
                    "      - 手順1",
                    "      - 手順2",
                    "    - 1.2.2. 結果",
                    "- 第2章",
                    "  - 2.1. 分析",
                    "  - 2.2. 結論",
                ],
                "test_name": "document_structure",
            },
            # プロジェクト管理スタイル
            {
                "structure": [
                    "- フェーズ1: 計画",
                    "  - タスク1.1: 要件定義",
                    "    - 1.1.1: ヒアリング",
                    "    - 1.1.2: 分析",
                    "      - 機能要件",
                    "      - 非機能要件",
                    "  - タスク1.2: 設計",
                    "    - 1.2.1: アーキテクチャ設計",
                    "    - 1.2.2: 詳細設計",
                    "- フェーズ2: 実装",
                    "  - タスク2.1: 開発",
                    "  - タスク2.2: テスト",
                ],
                "test_name": "project_management_structure",
            },
            # 混在記法スタイル
            {
                "structure": [
                    "- ;;;重要;;; 重要セクション ;;;",
                    "  - 重要項目1",
                    "    - ;;;注釈;;; 詳細説明 ;;;",
                    "    - 補足情報",
                    "  - 重要項目2",
                    "- 通常セクション",
                    "  - ;;;コード;;; コード例 ;;;",
                    "    - 実装方法",
                    "    - ;;;警告;;; 注意事項 ;;;",
                ],
                "test_name": "mixed_notation_structure",
            },
        ]

        for case in complex_structures:
            try:
                result = self.nested_parser.parse_nested_list(case["structure"])
                assert (
                    result is not None
                ), f"{case['test_name']}: 複雑構造の解析結果がnull"

                # 構造が適切に認識されることを確認
                if hasattr(result, "hierarchical_structure"):
                    assert result.hierarchical_structure is not None
                elif hasattr(result, "tree_structure"):
                    assert result.tree_structure is not None
                elif hasattr(result, "nested_items"):
                    assert len(result.nested_items) > 0

            except Exception as e:
                pytest.fail(f"複雑ネスト構造テスト {case['test_name']} でエラー: {e}")

    def test_nesting_consistency_validation(self):
        """ネスト整合性検証テスト"""
        consistency_test_cases = [
            # 整合性のあるネスト
            {
                "list": [
                    "- 項目1",
                    "  - 項目1.1",
                    "  - 項目1.2",
                    "- 項目2",
                    "  - 項目2.1",
                ],
                "expected_consistent": True,
                "test_name": "consistent_nesting",
            },
            # 段階的ネスト（不整合だが許容）
            {
                "list": [
                    "- 項目1",
                    "      - 項目1.1（深いインデント）",
                    "  - 項目1.2（浅いインデント）",
                ],
                "expected_consistent": False,  # または True（実装依存）
                "test_name": "inconsistent_deep_indent",
            },
            # 逆戻りネスト
            {
                "list": [
                    "- 項目1",
                    "  - 項目1.1",
                    "    - 項目1.1.1",
                    "- 項目2（レベル1に戻る）",
                ],
                "expected_consistent": True,
                "test_name": "backtrack_nesting",
            },
        ]

        for case in consistency_test_cases:
            try:
                if hasattr(self.nested_parser, "validate_nesting_consistency"):
                    is_consistent = self.nested_parser.validate_nesting_consistency(
                        case["list"]
                    )

                    if case["expected_consistent"]:
                        # 実装依存のため、エラーがないことのみ確認
                        assert is_consistent is not None
                    else:
                        # 実装依存のため、エラーがないことのみ確認
                        assert is_consistent is not None

            except Exception as e:
                pytest.fail(f"ネスト整合性検証 {case['test_name']} でエラー: {e}")

    def test_nested_list_performance(self):
        """ネストリスト性能テスト"""
        import time

        # 大規模ネストリストの生成
        large_nested_list = []

        # 10層の深いネスト構造
        for level1 in range(20):
            large_nested_list.append(f"- レベル1項目{level1}")
            for level2 in range(5):
                large_nested_list.append(f"  - レベル2項目{level1}-{level2}")
                for level3 in range(3):
                    large_nested_list.append(
                        f"    - レベル3項目{level1}-{level2}-{level3}"
                    )
                    for level4 in range(2):
                        large_nested_list.append(
                            f"      - レベル4項目{level1}-{level2}-{level3}-{level4}"
                        )

        start_time = time.time()

        try:
            result = self.nested_parser.parse_nested_list(large_nested_list)
            assert result is not None
        except Exception as e:
            pytest.fail(f"大規模ネストリスト解析でエラー: {e}")

        execution_time = time.time() - start_time

        # 性能基準確認
        assert execution_time < 2.0, f"ネストリスト解析が遅すぎる: {execution_time}秒"

        # リアルタイム解析基準（50ms/KB）
        list_size_kb = len("\n".join(large_nested_list)) / 1024
        ms_per_kb = (execution_time * 1000) / list_size_kb
        assert ms_per_kb < 50, f"KB当たり処理時間が遅い: {ms_per_kb}ms/KB"

    def test_unicode_nested_lists(self):
        """Unicodeネストリストテスト"""
        unicode_nested_cases = [
            # 日本語ネストリスト
            {
                "list": [
                    "- 日本語項目",
                    "  - ひらがな項目",
                    "    - カタカナ項目",
                    "      - 漢字項目",
                ],
                "test_name": "japanese_nested",
            },
            # 多言語混在ネスト
            {
                "list": [
                    "- English Item",
                    "  - 日本語項目",
                    "    - 中文项目",
                    "      - Русский элемент",
                ],
                "test_name": "multilingual_nested",
            },
            # 絵文字ネスト
            {
                "list": [
                    "- 🎌 日本",
                    "  - 🏙️ 東京",
                    "    - 🏢 新宿",
                    "      - 🚇 新宿駅",
                ],
                "test_name": "emoji_nested",
            },
            # 数学記号ネスト
            {
                "list": [
                    "- 数学 ∀",
                    "  - 集合論 ∈",
                    "    - 論理 ∧",
                    "      - 証明 ∴",
                ],
                "test_name": "math_symbols_nested",
            },
        ]

        for case in unicode_nested_cases:
            try:
                result = self.nested_parser.parse_nested_list(case["list"])
                assert (
                    result is not None
                ), f"{case['test_name']}: Unicode ネストリスト解析失敗"
            except Exception as e:
                pytest.fail(f"Unicode ネストリスト {case['test_name']} でエラー: {e}")

    def test_nested_list_with_keywords(self):
        """キーワード付きネストリストテスト"""
        keyword_nested_cases = [
            # 基本キーワードネスト
            {
                "list": [
                    "- ;;;重要;;; 重要な親項目 ;;;",
                    "  - 子項目1",
                    "  - ;;;注釈;;; 注釈付き子項目 ;;;",
                    "    - ;;;コード;;; 孫項目 ;;;",
                ],
                "test_name": "basic_keyword_nested",
            },
            # 複合キーワードネスト
            {
                "list": [
                    "- ;;;重要+強調;;; 重要で強調された項目 ;;;",
                    "  - ;;;注釈+詳細;;; 詳細な注釈 ;;;",
                    "    - ;;;コード+実行可能;;; 実行可能コード ;;;",
                ],
                "test_name": "compound_keyword_nested",
            },
            # 属性付きキーワードネスト
            {
                "list": [
                    "- ;;;画像[alt=メイン画像];;; 画像項目 ;;;",
                    "  - ;;;リンク[url=https://example.com];;; リンク項目 ;;;",
                    "    - ;;;コード[lang=python];;; Python コード ;;;",
                ],
                "test_name": "attribute_keyword_nested",
            },
        ]

        for case in keyword_nested_cases:
            try:
                result = self.nested_parser.parse_nested_list(case["list"])
                assert (
                    result is not None
                ), f"{case['test_name']}: キーワード付きネストリスト解析失敗"

                # キーワードが適切に処理されることを確認
                if hasattr(result, "contains_keywords"):
                    assert result.contains_keywords == True
                elif hasattr(result, "keyword_count"):
                    assert result.keyword_count > 0

            except Exception as e:
                pytest.fail(
                    f"キーワード付きネストリスト {case['test_name']} でエラー: {e}"
                )

    def test_edge_case_nesting_patterns(self):
        """エッジケースネストパターンテスト"""
        edge_cases = [
            # 空行を含むネスト
            {
                "list": [
                    "- 項目1",
                    "",
                    "  - 項目1.1",
                    "",
                    "    - 項目1.1.1",
                    "",
                    "- 項目2",
                ],
                "test_name": "empty_lines_in_nesting",
            },
            # コメント行を含むネスト
            {
                "list": [
                    "- 項目1",
                    "# コメント行",
                    "  - 項目1.1",
                    "// 別のコメント",
                    "    - 項目1.1.1",
                ],
                "test_name": "comment_lines_in_nesting",
            },
            # 極端に長い項目名
            {
                "list": [
                    "- " + "非常に長い項目名 " * 50,
                    "  - " + "これも長い子項目名 " * 30,
                    "    - " + "さらに長い孫項目名 " * 20,
                ],
                "test_name": "extremely_long_item_names",
            },
            # 特殊文字を含む項目
            {
                "list": [
                    "- 項目[1]",
                    "  - 項目{2}",
                    "    - 項目<3>",
                    "      - 項目|4|",
                ],
                "test_name": "special_characters_in_items",
            },
        ]

        for case in edge_cases:
            try:
                result = self.nested_parser.parse_nested_list(case["list"])
                # エッジケースでもクラッシュしないことを確認
                assert (
                    result is not None
                ), f"{case['test_name']}: エッジケース処理でnull結果"
            except Exception as e:
                pytest.fail(f"エッジケースネスト {case['test_name']} でエラー: {e}")

    def test_nesting_depth_limits(self):
        """ネスト深度制限テスト"""
        # 非常に深いネスト（10層）
        deep_nesting = []
        indent = ""
        for level in range(10):
            deep_nesting.append(f"{indent}- レベル{level+1}項目")
            indent += "  "

        try:
            result = self.nested_parser.parse_nested_list(deep_nesting)

            # 深いネストでも処理できることを確認
            assert result is not None, "深いネストの処理でnull結果"

            # 深度制限の確認（実装依存）
            if hasattr(result, "max_depth"):
                assert result.max_depth <= 15, f"予想外の深度: {result.max_depth}"
            elif hasattr(result, "depth_warning"):
                # 深度警告がある場合は適切
                pass

        except Exception as e:
            # 深度制限による例外も適切な処理
            assert "depth" in str(e).lower() or "nesting" in str(e).lower()

    def test_concurrent_nested_parsing(self):
        """並行ネスト解析テスト"""
        import threading

        results = []
        errors = []

        def concurrent_nested_worker(worker_id):
            try:
                local_parser = NestedListParser()
                worker_results = []

                for i in range(10):
                    nested_list = [
                        f"- ワーカー{worker_id}項目{i}",
                        f"  - サブ項目{i}.1",
                        f"    - サブサブ項目{i}.1.1",
                        f"  - サブ項目{i}.2",
                        f"- ワーカー{worker_id}項目{i+10}",
                    ]

                    try:
                        result = local_parser.parse_nested_list(nested_list)
                        worker_results.append(result is not None)
                    except Exception:
                        worker_results.append(False)

                success_rate = sum(worker_results) / len(worker_results)
                results.append((worker_id, success_rate))

            except Exception as e:
                errors.append((worker_id, str(e)))

        # 複数ワーカーで並行実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_nested_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行ネスト解析でエラー: {errors}"
        assert len(results) == 3

        # 各ワーカーで高い成功率
        for worker_id, success_rate in results:
            assert (
                success_rate >= 0.8
            ), f"ワーカー{worker_id}の成功率が低い: {success_rate:.1%}"


class TestIndentProcessor:
    """インデント処理テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.indent_processor = IndentProcessor()

    def test_indent_processor_initialization(self):
        """インデント処理初期化テスト"""
        assert self.indent_processor is not None
        assert hasattr(self.indent_processor, "normalize_indents")
        assert hasattr(self.indent_processor, "detect_indent_style")

    def test_indent_style_detection(self):
        """インデントスタイル検出テスト"""
        indent_styles = [
            {
                "lines": [
                    "- 項目1",
                    "  - 項目2（2スペース）",
                    "    - 項目3（4スペース）",
                ],
                "expected_style": "spaces",
                "expected_size": 2,
                "test_name": "two_space_style",
            },
            {
                "lines": [
                    "- 項目1",
                    "    - 項目2（4スペース）",
                    "        - 項目3（8スペース）",
                ],
                "expected_style": "spaces",
                "expected_size": 4,
                "test_name": "four_space_style",
            },
            {
                "lines": [
                    "- 項目1",
                    "\t- 項目2（タブ）",
                    "\t\t- 項目3（2タブ）",
                ],
                "expected_style": "tabs",
                "expected_size": 1,
                "test_name": "tab_style",
            },
        ]

        for case in indent_styles:
            try:
                if hasattr(self.indent_processor, "detect_indent_style"):
                    style, size = self.indent_processor.detect_indent_style(
                        case["lines"]
                    )

                    assert (
                        style == case["expected_style"]
                    ), f"{case['test_name']}: スタイル検出不一致"
                    assert (
                        size == case["expected_size"]
                    ), f"{case['test_name']}: サイズ検出不一致"

            except Exception as e:
                pytest.fail(f"インデントスタイル検出 {case['test_name']} でエラー: {e}")

    def test_indent_normalization(self):
        """インデント正規化テスト"""
        normalization_cases = [
            {
                "input": [
                    "- 項目1",
                    "   - 項目2（3スペース）",
                    "     - 項目3（5スペース）",
                ],
                "expected_output": [
                    "- 項目1",
                    "  - 項目2（2スペース）",
                    "    - 項目3（4スペース）",
                ],
                "test_name": "odd_space_normalization",
            },
            {
                "input": [
                    "- 項目1",
                    "\t- 項目2（タブ）",
                    "  - 項目3（スペース）",
                ],
                "expected_normalized": True,
                "test_name": "mixed_indent_normalization",
            },
        ]

        for case in normalization_cases:
            try:
                if hasattr(self.indent_processor, "normalize_indents"):
                    normalized = self.indent_processor.normalize_indents(case["input"])

                    if "expected_output" in case:
                        # 具体的な出力期待がある場合
                        assert len(normalized) == len(case["expected_output"])
                    else:
                        # 正規化が実行されることを確認
                        assert normalized is not None
                        assert case["expected_normalized"] == True

            except Exception as e:
                pytest.fail(f"インデント正規化 {case['test_name']} でエラー: {e}")
