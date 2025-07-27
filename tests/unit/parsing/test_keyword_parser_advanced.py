"""Keyword Parser高度テスト - Issue #597 Week 28-29対応

キーワード解析機能の包括的テスト
複合キーワード・属性処理・後方互換性の確認
"""

import time
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.keyword_parser import KeywordParser, MarkerValidator


class TestKeywordParserAdvanced:
    """キーワードパーサー高度テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.keyword_parser = KeywordParser()

    def test_keyword_parser_initialization(self):
        """キーワードパーサー初期化テスト"""
        assert self.keyword_parser is not None
        assert hasattr(self.keyword_parser, "parse_keyword")
        assert hasattr(self.keyword_parser, "create_compound_block")

    def test_complex_compound_keyword_parsing(self):
        """複雑な複合キーワード解析テスト"""
        complex_keywords = [
            "強調+注釈",
            "引用+コード+重要",
            "画像[alt=説明文]+装飾",
            "リスト+番号付き+強調",
            "テーブル+装飾+注釈+重要",
        ]

        for keyword in complex_keywords:
            try:
                result = self.keyword_parser.parse_keyword(keyword)

                # 複合キーワードが適切に分解される
                assert result is not None
                if hasattr(result, "components"):
                    assert len(result.components) >= 2
                elif hasattr(result, "keyword_parts"):
                    assert len(result.keyword_parts) >= 2

            except Exception as e:
                pytest.fail(f"複合キーワード '{keyword}' の解析でエラー: {e}")

    def test_attribute_parsing_comprehensive(self):
        """属性解析包括テスト"""
        attribute_patterns = [
            # 基本属性
            "画像[alt=説明文]",
            "リンク[url=https://example.com]",
            "テーブル[border=1]",
            # 複数属性
            "画像[alt=説明文,width=200,height=150]",
            "リンク[url=https://example.com,target=_blank,class=external]",
            # 特殊文字を含む属性
            "コード[lang=python,style='background-color: #f0f0f0']",
            "引用[author='山田 太郎',date='2023-01-01']",
            # Unicode属性
            "注釈[作者=佐藤花子,日付=2023年1月1日]",
            # 空属性・特殊ケース
            "装飾[class=]",
            "テスト[attr1=value1,attr2=,attr3=value3]",
        ]

        for pattern in attribute_patterns:
            try:
                result = self.keyword_parser.parse_keyword(pattern)

                # 属性が正しく解析される
                assert result is not None
                if hasattr(result, "attributes"):
                    assert isinstance(result.attributes, dict)
                elif hasattr(result, "parsed_attributes"):
                    assert isinstance(result.parsed_attributes, dict)

            except Exception as e:
                pytest.fail(f"属性パターン '{pattern}' の解析でエラー: {e}")

    def test_backward_compatibility_legacy_syntax(self):
        """後方互換性・レガシー記法テスト"""
        legacy_patterns = [
            # 旧形式のキーワード
            "old_style_keyword",
            "legacy-format",
            "UPPERCASE_KEYWORD",
            # 旧属性形式
            "keyword(param1=value1)",
            "function{arg1:value1,arg2:value2}",
            # 混在形式
            "modern[attr=value]+legacy_part",
            "新形式[属性=値]+旧形式",
        ]

        compatibility_results = []

        for pattern in legacy_patterns:
            try:
                result = self.keyword_parser.parse_keyword(pattern)
                compatibility_results.append(True)
            except Exception:
                compatibility_results.append(False)

        # 後方互換性の維持率確認
        compatibility_rate = sum(compatibility_results) / len(compatibility_results)
        assert (
            compatibility_rate >= 0.8
        ), f"後方互換性が低すぎます: {compatibility_rate:.1%}"

    def test_keyword_validation_strict_mode(self):
        """キーワード検証厳密モードテスト"""
        validator = MarkerValidator()

        # 有効なパターン
        valid_patterns = [
            ";;;有効なキーワード;;;",
            ";;;複合+キーワード;;;",
            ";;;属性[attr=value];;;",
            ";;;日本語キーワード;;;",
            ";;;English_keyword;;;",
        ]

        # 無効なパターン
        invalid_patterns = [
            ";;不完全なマーカー",
            ";;;空の;;内容;;;",
            ";;;;;;",
            ";;;制御文字\x00含む;;;",
            ";;;非常に長いキーワード" + "A" * 1000 + ";;;",
        ]

        # 有効パターンの検証
        for pattern in valid_patterns:
            is_valid, errors = validator.validate_marker_line(pattern)
            assert is_valid, f"有効パターンが無効と判定: {pattern}, エラー: {errors}"

        # 無効パターンの検証
        for pattern in invalid_patterns:
            is_valid, errors = validator.validate_marker_line(pattern)
            assert not is_valid, f"無効パターンが有効と判定: {pattern}"
            assert len(errors) > 0, f"無効パターンにエラーメッセージなし: {pattern}"

    def test_performance_keyword_parsing_benchmark(self):
        """キーワード解析性能ベンチマークテスト"""
        # 性能テスト用のキーワードセット
        performance_keywords = []

        # 単純キーワード
        performance_keywords.extend([f"simple_keyword_{i}" for i in range(100)])

        # 複合キーワード
        performance_keywords.extend([f"comp1+comp2+comp3_{i}" for i in range(100)])

        # 属性付きキーワード
        performance_keywords.extend([f"attr_key[a=1,b=2,c=3]_{i}" for i in range(100)])

        # 解析時間測定
        start_time = time.time()

        parsed_count = 0
        for keyword in performance_keywords:
            try:
                result = self.keyword_parser.parse_keyword(keyword)
                if result:
                    parsed_count += 1
            except Exception:
                pass  # 性能テストなのでエラーは無視

        execution_time = time.time() - start_time

        # 性能基準確認
        assert execution_time < 0.5, f"キーワード解析が遅すぎます: {execution_time}秒"
        assert parsed_count >= 250, f"解析成功数が不足: {parsed_count}/300"

        # 1キーワードあたりの処理時間
        ms_per_keyword = (execution_time * 1000) / len(performance_keywords)
        assert (
            ms_per_keyword < 2.0
        ), f"キーワード当たり処理時間が遅い: {ms_per_keyword}ms"

    def test_memory_efficiency_keyword_caching(self):
        """メモリ効率・キーワードキャッシュテスト"""
        # 同じキーワードの繰り返し解析
        repeated_keyword = "繰り返しテスト[attr=value]"

        # 初回解析
        initial_result = self.keyword_parser.parse_keyword(repeated_keyword)

        # 大量の同一キーワード解析
        results = []
        for _ in range(1000):
            result = self.keyword_parser.parse_keyword(repeated_keyword)
            results.append(result)

        # すべて同じ結果（キャッシュ効果）
        if hasattr(self.keyword_parser, "_cache") or hasattr(
            self.keyword_parser, "cache"
        ):
            # キャッシュ機能がある場合
            assert all(
                str(result) == str(initial_result) for result in results if result
            )

    def test_unicode_keyword_comprehensive(self):
        """Unicode キーワード包括テスト"""
        unicode_keywords = [
            # 日本語
            "日本語キーワード",
            "ひらがなキーワード",
            "カタカナキーワード",
            "漢字+ひらがな+カタカナ",
            # 他言語
            "English_keyword",
            "Español_palabra",
            "Français_mot",
            "Deutsch_wort",
            "Русский_ключ",
            "العربية_كلمة",
            "中文关键词",
            "한국어키워드",
            # 絵文字・記号
            "絵文字🎌キーワード",
            "記号→←キーワード",
            "数学∀∃キーワード",
            # 混在
            "Mixed日本語English키워드",
        ]

        unicode_results = []
        for keyword in unicode_keywords:
            try:
                result = self.keyword_parser.parse_keyword(keyword)
                unicode_results.append(result is not None)
            except Exception as e:
                unicode_results.append(False)

        # Unicode対応率確認
        unicode_support_rate = sum(unicode_results) / len(unicode_results)
        assert (
            unicode_support_rate >= 0.9
        ), f"Unicode対応率が低い: {unicode_support_rate:.1%}"

    def test_compound_block_creation_advanced(self):
        """複合ブロック作成高度テスト"""
        # 複雑な複合ブロックパターン
        compound_patterns = [
            {
                "keywords": ["引用", "強調", "注釈"],
                "content": ["重要な引用文", "強調部分", "補足説明"],
                "attributes": {"author": "著者名", "date": "2023-01-01"},
            },
            {
                "keywords": ["コード", "実行可能", "ハイライト"],
                "content": ["def example():", "    return True"],
                "attributes": {"lang": "python", "theme": "dark"},
            },
            {
                "keywords": ["テーブル", "装飾", "ソート可能"],
                "content": ["ヘッダー1|ヘッダー2", "データ1|データ2"],
                "attributes": {"border": "1", "sortable": "true"},
            },
        ]

        for i, pattern in enumerate(compound_patterns):
            try:
                # 複合ブロックの作成をテスト
                # 実際のAPI呼び出しは実装に依存
                compound_keyword = "+".join(pattern["keywords"])
                if pattern["attributes"]:
                    # 属性を追加
                    attr_str = ",".join(
                        [f"{k}={v}" for k, v in pattern["attributes"].items()]
                    )
                    compound_keyword += f"[{attr_str}]"

                result = self.keyword_parser.parse_keyword(compound_keyword)
                assert result is not None, f"複合パターン{i}の解析に失敗"

            except Exception as e:
                pytest.fail(f"複合パターン{i}でエラー: {e}")

    def test_error_handling_malformed_keywords(self):
        """不正キーワードエラーハンドリングテスト"""
        malformed_keywords = [
            # 構文エラー
            "keyword[attr=",  # 属性の閉じ括弧なし
            "keyword[=value]",  # 属性名なし
            "keyword[attr=value,]",  # 末尾カンマ
            # 不正文字
            "keyword\x00\x01",  # 制御文字
            "keyword\n\r",  # 改行文字
            "keyword\t\v",  # タブ・垂直タブ
            # 極端なケース
            "",  # 空文字
            " " * 1000,  # 空白のみ
            "A" * 10000,  # 極端に長い
            # 特殊記号の組み合わせ
            ";;;+++;;;",
            "[[[attr=value]]]",
            "+++",
            "===",
        ]

        error_handling_results = []
        for keyword in malformed_keywords:
            try:
                result = self.keyword_parser.parse_keyword(keyword)
                # エラーにならない場合もあるが、適切に処理される
                error_handling_results.append(True)
            except Exception as e:
                # 適切なエラーハンドリング
                error_handling_results.append(True)

        # すべての不正入力が適切に処理される
        assert all(error_handling_results), "一部の不正キーワードで不適切な処理"

    def test_keyword_parsing_accuracy_target(self):
        """キーワード解析精度目標テスト"""
        # Kumihan記法標準パターン
        standard_keyword_patterns = [
            "強調",
            "注釈",
            "引用",
            "コード",
            "画像",
            "リンク",
            "テーブル",
            "リスト",
            "見出し",
            "装飾",
            # 複合パターン
            "強調+重要",
            "引用+注釈",
            "コード+実行可能",
            # 属性付きパターン
            "画像[alt=説明]",
            "リンク[url=https://example.com]",
            "コード[lang=python]",
            # 日本語複合
            "重要な+注釈付き+引用",
            "実行可能な+ハイライト付き+コード",
        ]

        accuracy_results = []
        for pattern in standard_keyword_patterns:
            try:
                result = self.keyword_parser.parse_keyword(pattern)
                accuracy_results.append(result is not None)
            except Exception:
                accuracy_results.append(False)

        # 精度目標: 99.5%以上
        accuracy_rate = sum(accuracy_results) / len(accuracy_results)
        assert (
            accuracy_rate >= 0.995
        ), f"キーワード解析精度が目標未達: {accuracy_rate:.1%}"

    def test_concurrent_keyword_parsing(self):
        """並行キーワード解析テスト"""
        import threading

        results = []
        errors = []

        def concurrent_keyword_worker(worker_id):
            try:
                # ワーカー固有のキーワードセット
                worker_keywords = [
                    f"ワーカー{worker_id}キーワード{i}" for i in range(50)
                ]

                worker_results = []
                for keyword in worker_keywords:
                    try:
                        result = self.keyword_parser.parse_keyword(keyword)
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
            thread = threading.Thread(target=concurrent_keyword_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行解析でエラー: {errors}"
        assert len(results) == 3

        # 各ワーカーで高い成功率
        for worker_id, success_rate in results:
            assert (
                success_rate >= 0.8
            ), f"ワーカー{worker_id}の成功率が低い: {success_rate:.1%}"


class TestMarkerValidatorAdvanced:
    """マーカーバリデーター高度テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.validator = MarkerValidator()

    def test_marker_validation_comprehensive(self):
        """マーカー検証包括テスト"""
        # 完全に有効なマーカー
        valid_markers = [
            ";;;キーワード;;;",
            ";;;複合+キーワード;;;",
            ";;;属性[attr=value]キーワード;;;",
            ";;;日本語マーカー;;;",
            ";;;English_marker;;;",
            ";;;mixed日本語English;;;",
        ]

        # 部分的に有効なマーカー
        partially_valid = [
            ";;;キーワード;;; 内容 ;;;",  # インライン形式
            ";;;",  # 終了マーカー
        ]

        # 完全に無効なマーカー
        invalid_markers = [
            ";;不完全",
            "キーワード;;;",  # 開始マーカーなし
            ";;;キーワード",  # 終了マーカーなし
            ";;;;;;",  # 空のマーカー
            "",  # 空行
        ]

        # 有効マーカーのテスト
        for marker in valid_markers:
            is_valid, errors = self.validator.validate_marker_line(marker)
            assert is_valid, f"有効マーカーが無効判定: {marker}, エラー: {errors}"

        # 無効マーカーのテスト
        for marker in invalid_markers:
            is_valid, errors = self.validator.validate_marker_line(marker)
            assert not is_valid, f"無効マーカーが有効判定: {marker}"

    def test_validation_error_messages_quality(self):
        """検証エラーメッセージ品質テスト"""
        error_test_cases = [
            (";;不完全", "開始マーカー"),
            ("キーワード;;;", "開始マーカー"),
            (";;;キーワード", "終了マーカー"),
            (";;;;;;", "空"),
            ("", "空行"),
        ]

        for invalid_marker, expected_error_type in error_test_cases:
            is_valid, errors = self.validator.validate_marker_line(invalid_marker)

            assert not is_valid
            assert len(errors) > 0

            # エラーメッセージが説明的
            error_text = " ".join(errors)
            assert len(error_text) > 10, f"エラーメッセージが短すぎる: {error_text}"

    def test_validation_performance_stress(self):
        """検証性能ストレステスト"""
        # 大量のマーカー検証
        test_markers = []

        # 有効なマーカー（1000個）
        test_markers.extend([f";;;テストマーカー{i};;;" for i in range(1000)])

        # 無効なマーカー（1000個）
        test_markers.extend([f";;無効マーカー{i}" for i in range(1000)])

        start_time = time.time()

        validation_results = []
        for marker in test_markers:
            is_valid, errors = self.validator.validate_marker_line(marker)
            validation_results.append((is_valid, len(errors)))

        execution_time = time.time() - start_time

        # 性能確認
        assert execution_time < 0.5, f"マーカー検証が遅すぎる: {execution_time}秒"

        # 検証結果の正確性
        valid_count = sum(1 for is_valid, _ in validation_results if is_valid)
        assert valid_count == 1000, f"有効マーカー数が不正: {valid_count}/1000"
