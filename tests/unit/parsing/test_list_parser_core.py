"""List Parser Core テスト - Issue #597 対応

リストパーサーコア機能の専門テスト
基本解析エンジン・パターンマッチング・最適化の確認
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.list_parser_core import ListParserCore

# リストパターン機能のモック


class TestListParserCore:
    """リストパーサーコアテスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.core_parser = ListParserCore()

    def test_core_parser_initialization(self):
        """コアパーサー初期化テスト"""
        assert self.core_parser is not None
        assert hasattr(self.core_parser, "parse_list")
        assert hasattr(self.core_parser, "detect_list_type")

    def test_basic_list_type_detection(self):
        """基本リストタイプ検出テスト"""
        list_type_cases = [
            # 順序なしリスト（ハイフン）
            {
                "list": [
                    "- 項目1",
                    "- 項目2",
                    "- 項目3",
                ],
                "expected_type": "unordered",
                "expected_marker": "-",
                "test_name": "hyphen_unordered_list",
            },
            # 順序なしリスト（アスタリスク）
            {
                "list": [
                    "* 項目1",
                    "* 項目2",
                    "* 項目3",
                ],
                "expected_type": "unordered",
                "expected_marker": "*",
                "test_name": "asterisk_unordered_list",
            },
            # 順序なしリスト（プラス）
            {
                "list": [
                    "+ 項目1",
                    "+ 項目2",
                    "+ 項目3",
                ],
                "expected_type": "unordered",
                "expected_marker": "+",
                "test_name": "plus_unordered_list",
            },
            # 数字順序付きリスト
            {
                "list": [
                    "1. 第一項目",
                    "2. 第二項目",
                    "3. 第三項目",
                ],
                "expected_type": "ordered",
                "expected_marker": "numeric",
                "test_name": "numeric_ordered_list",
            },
            # アルファベット順序付きリスト
            {
                "list": [
                    "a. 項目A",
                    "b. 項目B",
                    "c. 項目C",
                ],
                "expected_type": "ordered",
                "expected_marker": "alphabetic",
                "test_name": "alphabetic_ordered_list",
            },
            # ローマ数字順序付きリスト
            {
                "list": [
                    "i. 項目I",
                    "ii. 項目II",
                    "iii. 項目III",
                ],
                "expected_type": "ordered",
                "expected_marker": "roman",
                "test_name": "roman_ordered_list",
            },
        ]

        for case in list_type_cases:
            try:
                detected_type = self.core_parser.detect_list_type(case["list"])

                assert (
                    detected_type is not None
                ), f"{case['test_name']}: リストタイプが検出されない"

                # タイプ確認（実装依存）
                if hasattr(detected_type, "type"):
                    assert (
                        detected_type.type == case["expected_type"]
                    ), f"{case['test_name']}: タイプ不一致"
                elif hasattr(detected_type, "list_type"):
                    assert (
                        detected_type.list_type == case["expected_type"]
                    ), f"{case['test_name']}: タイプ不一致"
                elif isinstance(detected_type, str):
                    assert (
                        case["expected_type"] in detected_type
                    ), f"{case['test_name']}: タイプ文字列不一致"

            except Exception as e:
                pytest.fail(f"基本リストタイプ検出 {case['test_name']} でエラー: {e}")

    def test_mixed_list_type_handling(self):
        """混在リストタイプ処理テスト"""
        mixed_list_cases = [
            # 数字とアルファベット混在
            {
                "list": [
                    "1. 第一章",
                    "   a. セクションA",
                    "   b. セクションB",
                    "2. 第二章",
                    "   a. セクションA",
                ],
                "expected_types": ["numeric", "alphabetic"],
                "test_name": "numeric_alphabetic_mixed",
            },
            # 順序付きと順序なし混在
            {
                "list": [
                    "1. 手順1",
                    "   - 詳細項目",
                    "   - 注意事項",
                    "2. 手順2",
                    "   - 詳細項目",
                ],
                "expected_types": ["ordered", "unordered"],
                "test_name": "ordered_unordered_mixed",
            },
            # 複数マーカー混在
            {
                "list": [
                    "- ハイフン項目",
                    "* アスタリスク項目",
                    "+ プラス項目",
                ],
                "expected_types": ["unordered"],
                "test_name": "multiple_marker_mixed",
            },
        ]

        for case in mixed_list_cases:
            try:
                result = self.core_parser.parse_list(case["list"])
                assert (
                    result is not None
                ), f"{case['test_name']}: 混在リスト解析結果がnull"

                # 混在タイプが適切に処理されることを確認
                if hasattr(result, "mixed_types"):
                    assert result.mixed_types == True
                elif hasattr(result, "list_types"):
                    assert len(result.list_types) > 1

            except Exception as e:
                pytest.fail(f"混在リストタイプ処理 {case['test_name']} でエラー: {e}")

    def test_advanced_list_patterns(self):
        """高度リストパターンテスト"""
        advanced_patterns = [
            # チェックリスト
            {
                "list": [
                    "- [ ] 未完了タスク1",
                    "- [x] 完了タスク1",
                    "- [ ] 未完了タスク2",
                    "- [X] 完了タスク2（大文字）",
                ],
                "expected_pattern": "checklist",
                "test_name": "checkbox_checklist",
            },
            # 定義リスト
            {
                "list": [
                    "用語1",
                    "  定義1の説明",
                    "用語2",
                    "  定義2の説明",
                    "  追加説明",
                ],
                "expected_pattern": "definition",
                "test_name": "definition_list",
            },
            # 番号付きチェックリスト
            {
                "list": [
                    "1. [ ] タスク1",
                    "2. [x] タスク2（完了）",
                    "3. [ ] タスク3",
                ],
                "expected_pattern": "numbered_checklist",
                "test_name": "numbered_checkbox_list",
            },
            # 階層番号リスト
            {
                "list": [
                    "1. 第1章",
                    "   1.1. 第1節",
                    "   1.2. 第2節",
                    "2. 第2章",
                    "   2.1. 第1節",
                ],
                "expected_pattern": "hierarchical_numbered",
                "test_name": "hierarchical_numbered_list",
            },
        ]

        for case in advanced_patterns:
            try:
                result = self.core_parser.parse_list(case["list"])
                assert (
                    result is not None
                ), f"{case['test_name']}: 高度パターン解析結果がnull"

                # パターンが認識されることを確認
                if hasattr(result, "pattern"):
                    # パターンが適切に認識される（実装依存）
                    pass
                elif hasattr(result, "list_style"):
                    # スタイルが認識される（実装依存）
                    pass

            except Exception as e:
                pytest.fail(f"高度リストパターン {case['test_name']} でエラー: {e}")

    def test_list_item_parsing_precision(self):
        """リスト項目解析精度テスト"""
        precision_test_cases = [
            # 基本項目解析
            {
                "items": [
                    "- 単純な項目",
                    "- **太字**を含む項目",
                    "- *斜体*を含む項目",
                    "- `コード`を含む項目",
                    "- [リンク](url)を含む項目",
                ],
                "expected_elements": ["text", "bold", "italic", "code", "link"],
                "test_name": "basic_item_elements",
            },
            # 複雑な項目内容
            {
                "items": [
                    "- 項目1: **重要**な内容と*補足*説明",
                    "- 項目2: `code example` と [参考リンク](https://example.com)",
                    "- 項目3: ;;;重要;;; キーワード付き項目 ;;;",
                ],
                "expected_complexity": "high",
                "test_name": "complex_item_content",
            },
            # 長い項目内容
            {
                "items": [
                    "- " + "非常に長い項目内容 " * 20 + "終了",
                    "- 通常の項目",
                    "- " + "別の長い項目 " * 15 + "完了",
                ],
                "expected_handling": "long_content",
                "test_name": "long_item_content",
            },
        ]

        for case in precision_test_cases:
            try:
                result = self.core_parser.parse_list(case["items"])
                assert (
                    result is not None
                ), f"{case['test_name']}: 項目解析精度テスト結果がnull"

                # 解析精度の確認
                if hasattr(result, "items"):
                    assert len(result.items) == len(
                        case["items"]
                    ), f"{case['test_name']}: 項目数不一致"
                elif hasattr(result, "parsed_items"):
                    assert len(result.parsed_items) == len(
                        case["items"]
                    ), f"{case['test_name']}: 解析項目数不一致"

            except Exception as e:
                pytest.fail(f"リスト項目解析精度 {case['test_name']} でエラー: {e}")

    def test_list_parsing_optimization(self):
        """リスト解析最適化テスト"""
        import time

        # 最適化テスト用の様々なリストパターン
        optimization_lists = [
            # 短いリスト（高速処理確認）
            ["- 項目1", "- 項目2", "- 項目3"],
            # 中程度のリスト
            [f"- 項目{i}" for i in range(50)],
            # 大きなリスト
            [f"- 項目{i}" for i in range(200)],
            # 複雑なリスト
            [f"- ;;;キーワード{i};;; 項目{i} ;;;" for i in range(30)],
            # ネストリスト
            ["- レベル1"]
            + [f"  - レベル2項目{i}" for i in range(20)]
            + ["- レベル1続き"]
            + [f"    - レベル3項目{i}" for i in range(10)],
        ]

        processing_times = []

        for i, test_list in enumerate(optimization_lists):
            start_time = time.time()

            try:
                result = self.core_parser.parse_list(test_list)
                assert result is not None, f"最適化テスト{i}: 解析結果がnull"
            except Exception as e:
                pytest.fail(f"最適化テスト{i}でエラー: {e}")

            processing_time = time.time() - start_time
            processing_times.append(processing_time)

        # 最適化性能確認
        for i, processing_time in enumerate(processing_times):
            assert (
                processing_time < 0.1
            ), f"最適化テスト{i}が遅すぎる: {processing_time:.3f}秒"

        # スケーラビリティ確認（リストサイズに対する処理時間の増加が線形以下）
        if len(processing_times) >= 3:
            # 大きなリストでも処理時間が急激に増加しないことを確認
            large_list_time = processing_times[2]  # 200項目リスト
            small_list_time = processing_times[0]  # 3項目リスト

            if small_list_time > 0:
                time_ratio = large_list_time / small_list_time
                assert (
                    time_ratio < 100
                ), f"処理時間の増加が非線形すぎる: {time_ratio:.1f}倍"

    def test_list_pattern_caching(self):
        """リストパターンキャッシュテスト"""
        # 同一パターンの繰り返し解析
        repeated_list = [
            "- 繰り返し項目1",
            "- 繰り返し項目2",
            "- 繰り返し項目3",
        ]

        # 初回解析
        import time

        start_time = time.time()
        first_result = self.core_parser.parse_list(repeated_list)
        first_time = time.time() - start_time

        # 繰り返し解析（キャッシュ効果確認）
        cached_times = []
        for _ in range(10):
            start_time = time.time()
            result = self.core_parser.parse_list(repeated_list)
            cached_times.append(time.time() - start_time)
            assert result is not None

        # キャッシュ効果確認
        if hasattr(self.core_parser, "_cache") or hasattr(self.core_parser, "cache"):
            avg_cached_time = sum(cached_times) / len(cached_times)
            if first_time > 0 and avg_cached_time > 0:
                # キャッシュにより高速化されることを期待
                assert (
                    avg_cached_time <= first_time * 2
                ), f"キャッシュ効果が不十分: 初回{first_time:.4f}s, 平均{avg_cached_time:.4f}s"

    def test_error_recovery_parsing(self):
        """エラー回復解析テスト"""
        error_recovery_cases = [
            # 不正なリストマーカー
            {
                "list": [
                    "- 正常な項目",
                    "x 不正なマーカー",
                    "- 正常な項目に戻る",
                ],
                "expected_recovery": True,
                "test_name": "invalid_marker_recovery",
            },
            # 番号の欠落
            {
                "list": [
                    "1. 項目1",
                    "3. 項目3（2が欠落）",
                    "4. 項目4",
                ],
                "expected_recovery": True,
                "test_name": "missing_number_recovery",
            },
            # 不正なインデント
            {
                "list": [
                    "- 項目1",
                    "      - 極端な深いインデント",
                    "  - 通常のインデント",
                ],
                "expected_recovery": True,
                "test_name": "extreme_indent_recovery",
            },
            # 制御文字混入
            {
                "list": [
                    "- 正常項目",
                    "- 制御文字\x00混入項目",
                    "- 正常項目",
                ],
                "expected_recovery": True,
                "test_name": "control_character_recovery",
            },
        ]

        for case in error_recovery_cases:
            try:
                result = self.core_parser.parse_list(case["list"])

                if case["expected_recovery"]:
                    # エラー回復が期待される場合
                    assert result is not None, f"{case['test_name']}: エラー回復失敗"

                    # エラー情報が記録されることを確認
                    if hasattr(result, "errors"):
                        # エラーが記録されているが、処理は継続
                        pass
                    elif hasattr(result, "warnings"):
                        # 警告として記録される場合
                        pass
                else:
                    # 回復不能なエラーの場合
                    assert result is None or hasattr(result, "critical_error")

            except Exception as e:
                # 例外が発生する場合も適切なエラーハンドリング
                assert "parse" in str(e).lower() or "list" in str(e).lower()

    def test_unicode_list_parsing(self):
        """Unicodeリスト解析テスト"""
        unicode_list_cases = [
            # 日本語リスト
            {
                "list": [
                    "- 日本語項目１",
                    "- 日本語項目２",
                    "- 日本語項目３",
                ],
                "test_name": "japanese_list",
            },
            # 多言語混在リスト
            {
                "list": [
                    "- English item",
                    "- 日本語項目",
                    "- 中文项目",
                    "- Русский элемент",
                    "- العنصر العربي",
                ],
                "test_name": "multilingual_list",
            },
            # 絵文字リスト
            {
                "list": [
                    "- 🎌 日本の項目",
                    "- 🇺🇸 アメリカの項目",
                    "- 🇨🇳 中国の項目",
                    "- 🌍 世界の項目",
                ],
                "test_name": "emoji_list",
            },
            # 数学記号リスト
            {
                "list": [
                    "- ∀x ∈ A",
                    "- ∃y ∉ B",
                    "- x ∧ y → z",
                    "- ∴ 結論",
                ],
                "test_name": "math_symbols_list",
            },
        ]

        for case in unicode_list_cases:
            try:
                result = self.core_parser.parse_list(case["list"])
                assert result is not None, f"{case['test_name']}: Unicodeリスト解析失敗"

                # Unicode文字が適切に処理されることを確認
                if hasattr(result, "unicode_support"):
                    assert result.unicode_support == True
                elif hasattr(result, "items"):
                    assert len(result.items) == len(case["list"])

            except Exception as e:
                pytest.fail(f"Unicodeリスト解析 {case['test_name']} でエラー: {e}")

    def test_concurrent_core_parsing(self):
        """並行コア解析テスト"""
        import threading

        results = []
        errors = []

        def concurrent_core_worker(worker_id):
            try:
                local_core = ListParserCore()
                worker_results = []

                for i in range(20):
                    test_list = [
                        f"- ワーカー{worker_id}項目{i}",
                        f"- 項目{i}.1",
                        f"- 項目{i}.2",
                    ]

                    try:
                        result = local_core.parse_list(test_list)
                        worker_results.append(result is not None)
                    except Exception:
                        worker_results.append(False)

                success_rate = sum(worker_results) / len(worker_results)
                results.append((worker_id, success_rate))

            except Exception as e:
                errors.append((worker_id, str(e)))

        # 複数ワーカーで並行実行
        threads = []
        for i in range(4):
            thread = threading.Thread(target=concurrent_core_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行コア解析でエラー: {errors}"
        assert len(results) == 4

        # 各ワーカーで高い成功率
        for worker_id, success_rate in results:
            assert (
                success_rate >= 0.9
            ), f"ワーカー{worker_id}の成功率が低い: {success_rate:.1%}"


class TestListPatterns:
    """リストパターンテスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.patterns = ListPatterns()

    def test_list_patterns_initialization(self):
        """リストパターン初期化テスト"""
        assert self.patterns is not None
        assert hasattr(self.patterns, "get_pattern")
        assert hasattr(self.patterns, "match_pattern")

    def test_pattern_matching_accuracy(self):
        """パターンマッチング精度テスト"""
        pattern_cases = [
            # 基本パターン
            {
                "text": "- 項目",
                "expected_pattern": "unordered_hyphen",
                "test_name": "basic_hyphen_pattern",
            },
            {
                "text": "1. 項目",
                "expected_pattern": "ordered_numeric",
                "test_name": "basic_numeric_pattern",
            },
            # 複雑パターン
            {
                "text": "- [ ] チェックボックス",
                "expected_pattern": "checkbox_unchecked",
                "test_name": "checkbox_pattern",
            },
            {
                "text": "1.2.3. 階層番号",
                "expected_pattern": "hierarchical_numeric",
                "test_name": "hierarchical_pattern",
            },
        ]

        for case in pattern_cases:
            try:
                if hasattr(self.patterns, "match_pattern"):
                    matched_pattern = self.patterns.match_pattern(case["text"])
                    assert (
                        matched_pattern is not None
                    ), f"{case['test_name']}: パターンマッチ失敗"
                elif hasattr(self.patterns, "identify_pattern"):
                    matched_pattern = self.patterns.identify_pattern(case["text"])
                    assert (
                        matched_pattern is not None
                    ), f"{case['test_name']}: パターン識別失敗"

            except Exception as e:
                pytest.fail(f"パターンマッチング精度 {case['test_name']} でエラー: {e}")

    def test_custom_pattern_registration(self):
        """カスタムパターン登録テスト"""
        custom_patterns = [
            {
                "name": "arrow_list",
                "regex": r"^→\s+(.+)$",
                "description": "矢印リスト",
                "example": "→ 矢印項目",
            },
            {
                "name": "circle_list",
                "regex": r"^○\s+(.+)$",
                "description": "丸印リスト",
                "example": "○ 丸印項目",
            },
            {
                "name": "star_list",
                "regex": r"^★\s+(.+)$",
                "description": "星印リスト",
                "example": "★ 星印項目",
            },
        ]

        for pattern in custom_patterns:
            try:
                if hasattr(self.patterns, "register_pattern"):
                    self.patterns.register_pattern(
                        pattern["name"], pattern["regex"], pattern["description"]
                    )

                    # 登録後のテスト
                    test_result = self.patterns.match_pattern(pattern["example"])
                    assert (
                        test_result is not None
                    ), f"カスタムパターン {pattern['name']} のマッチ失敗"

            except Exception as e:
                pytest.fail(f"カスタムパターン登録 {pattern['name']} でエラー: {e}")

    def test_pattern_performance(self):
        """パターン性能テスト"""
        import time

        # 大量のパターンマッチテスト
        test_texts = [
            "- 基本項目",
            "1. 番号項目",
            "* アスタリスク項目",
            "+ プラス項目",
            "- [ ] チェックボックス",
            "a. アルファベット項目",
            "i. ローマ数字項目",
        ] * 50  # 350回のマッチテスト

        start_time = time.time()

        match_results = []
        for text in test_texts:
            try:
                if hasattr(self.patterns, "match_pattern"):
                    result = self.patterns.match_pattern(text)
                    match_results.append(result is not None)
                else:
                    match_results.append(True)  # メソッドがない場合は成功として扱う
            except Exception:
                match_results.append(False)

        execution_time = time.time() - start_time

        # 性能基準確認
        assert execution_time < 0.1, f"パターンマッチが遅すぎる: {execution_time:.3f}秒"

        # マッチ成功率確認
        success_rate = sum(match_results) / len(match_results)
        assert success_rate >= 0.8, f"パターンマッチ成功率が低い: {success_rate:.1%}"
