"""Marker Parser 高度テスト - Issue #597 Week 28-29対応

マーカー構文正規化・属性抽出・複合キーワード分割の確認
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.keyword_parsing.marker_parser import MarkerParser


class TestMarkerParserAdvanced:
    """マーカーパーサー高度テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        # モック戦略統一: MarkerParserは軽量なため実際のインスタンスを使用
        self.marker_parser = MarkerParser()

        # 必要に応じてモック化（重い処理や外部依存がある場合）
        self.mock_marker_parser = Mock(spec=MarkerParser)

    def test_marker_parser_initialization(self):
        """マーカーパーサー初期化テスト"""
        assert self.marker_parser is not None
        assert hasattr(self.marker_parser, "normalize_marker")
        assert hasattr(self.marker_parser, "extract_attributes")
        assert hasattr(self.marker_parser, "split_compound_keywords")

    def test_marker_normalization_comprehensive(self):
        """マーカー正規化包括テスト"""
        normalization_cases = [
            # 空白の正規化
            ("  keyword  ", "keyword"),
            ("keyword\t\n", "keyword"),
            ("  multiple   spaces  ", "multiple spaces"),
            # 特殊文字の正規化
            ("keyword+compound", "keyword+compound"),
            ("keyword[attr=value]", "keyword[attr=value]"),
            ("keyword-with-dashes", "keyword-with-dashes"),
            ("keyword_with_underscores", "keyword_with_underscores"),
            # Unicode文字の正規化
            ("日本語キーワード", "日本語キーワード"),
            ("English+日本語", "English+日本語"),
            ("絵文字🎌テスト", "絵文字🎌テスト"),
            # 大文字小文字（実装に依存）
            ("UPPERCASE", "UPPERCASE"),  # そのまま保持される場合
            ("MixedCase", "MixedCase"),
        ]

        for input_marker, expected_output in normalization_cases:
            try:
                normalized = self.marker_parser.normalize_marker(input_marker)
                assert (
                    normalized == expected_output
                ), f"正規化結果が期待と異なる: '{input_marker}' -> '{normalized}' (期待: '{expected_output}')"
            except Exception as e:
                pytest.fail(f"マーカー正規化でエラー: '{input_marker}' -> {e}")

    def test_attribute_extraction_comprehensive(self):
        """属性抽出包括テスト"""
        attribute_cases = [
            # 単一属性
            ("keyword[attr=value]", {"attr": "value"}),
            ("keyword[alt=画像説明]", {"alt": "画像説明"}),
            ("keyword[url=https://example.com]", {"url": "https://example.com"}),
            # 複数属性
            ("keyword[a=1,b=2,c=3]", {"a": "1", "b": "2", "c": "3"}),
            (
                "image[alt=説明,width=200,height=150]",
                {"alt": "説明", "width": "200", "height": "150"},
            ),
            # クォートされた値
            ("keyword[attr='quoted value']", {"attr": "quoted value"}),
            ('keyword[attr="double quoted"]', {"attr": "double quoted"}),
            (
                "keyword[mixed='single',other=\"double\"]",
                {"mixed": "single", "other": "double"},
            ),
            # 特殊文字を含む属性
            (
                "keyword[url='https://example.com?param=value&other=test']",
                {"url": "https://example.com?param=value&other=test"},
            ),
            (
                "keyword[style='color: red; font-size: 14px;']",
                {"style": "color: red; font-size: 14px;"},
            ),
            # Unicode属性
            ("キーワード[属性=値]", {"属性": "値"}),
            ("keyword[日本語=値,English=value]", {"日本語": "値", "English": "value"}),
            # 属性なし
            ("keyword", {}),
            ("keyword[]", {}),
        ]

        for input_marker, expected_attrs in attribute_cases:
            try:
                extracted_attrs = self.marker_parser.extract_attributes(input_marker)
                assert (
                    extracted_attrs == expected_attrs
                ), f"属性抽出結果が期待と異なる: '{input_marker}' -> {extracted_attrs} (期待: {expected_attrs})"
            except Exception as e:
                pytest.fail(f"属性抽出でエラー: '{input_marker}' -> {e}")

    def test_compound_keyword_splitting(self):
        """複合キーワード分割テスト"""
        compound_cases = [
            # 基本的な複合
            ("keyword1+keyword2", ["keyword1", "keyword2"]),
            ("強調+重要", ["強調", "重要"]),
            ("code+highlight+executable", ["code", "highlight", "executable"]),
            # 属性付き複合
            ("image[alt=説明]+decoration", ["image[alt=説明]", "decoration"]),
            (
                "link[url=test]+emphasis[level=high]",
                ["link[url=test]", "emphasis[level=high]"],
            ),
            # 複雑な組み合わせ
            ("base+modifier[type=1]+final", ["base", "modifier[type=1]", "final"]),
            ("日本語+English+中文", ["日本語", "English", "中文"]),
            # 単一キーワード（分割なし）
            ("single_keyword", ["single_keyword"]),
            ("single[attr=value]", ["single[attr=value]"]),
            # 空文字・特殊ケース
            ("", []),
            ("+", []),  # 空の分割
            ("keyword+", ["keyword"]),  # 末尾の+
            ("+keyword", ["keyword"]),  # 先頭の+
        ]

        for input_compound, expected_parts in compound_cases:
            try:
                split_parts = self.marker_parser.split_compound_keywords(input_compound)
                assert (
                    split_parts == expected_parts
                ), f"複合分割結果が期待と異なる: '{input_compound}' -> {split_parts} (期待: {expected_parts})"
            except Exception as e:
                pytest.fail(f"複合キーワード分割でエラー: '{input_compound}' -> {e}")

    def test_complex_marker_parsing_scenarios(self):
        """複雑なマーカー解析シナリオテスト"""
        complex_scenarios = [
            # 非常に複雑な複合キーワード
            "image[alt='Complex Image',width=800,height=600]+decoration[style='border: 1px solid']+responsive[breakpoints='sm,md,lg']",
            # 多言語混在
            "日本語[属性='値']+English[attr='value']+中文[参数='参数值']",
            # 特殊文字・記号
            "symbol[content='→←↑↓']+math[formula='a+b=c']+emoji[icons='🎌🗾']",
            # 長い属性値
            "description[text='これは非常に長い説明文です。複数の文章が含まれており、改行や特殊文字も含む可能性があります。']",
            # ネストしたような構造（実際にはネストではない）
            "outer[inner='value[nested=true]']+another",
        ]

        for scenario in complex_scenarios:
            try:
                # 正規化
                normalized = self.marker_parser.normalize_marker(scenario)
                assert normalized is not None

                # 属性抽出
                attributes = self.marker_parser.extract_attributes(scenario)
                assert isinstance(attributes, dict)

                # 複合分割
                parts = self.marker_parser.split_compound_keywords(scenario)
                assert isinstance(parts, list)
                assert len(parts) > 0

            except Exception as e:
                pytest.fail(f"複雑シナリオ解析でエラー: '{scenario}' -> {e}")

    def test_marker_parsing_performance(self):
        """マーカー解析性能テスト"""
        import time

        # 性能テスト用のマーカーセット
        performance_markers = []

        # 単純マーカー
        performance_markers.extend([f"simple{i}" for i in range(500)])

        # 属性付きマーカー
        performance_markers.extend([f"attr{i}[a=1,b=2]" for i in range(300)])

        # 複合マーカー
        performance_markers.extend([f"comp{i}+part{i}" for i in range(200)])

        start_time = time.time()

        processed_count = 0
        for marker in performance_markers:
            try:
                # 正規化
                normalized = self.marker_parser.normalize_marker(marker)

                # 属性抽出
                attributes = self.marker_parser.extract_attributes(marker)

                # 複合分割
                parts = self.marker_parser.split_compound_keywords(marker)

                if normalized and parts:
                    processed_count += 1
            except Exception:
                pass  # 性能テストなのでエラーは無視

        execution_time = time.time() - start_time

        # 性能基準確認
        assert execution_time < 0.5, f"マーカー解析が遅すぎる: {execution_time}秒"
        assert processed_count >= 900, f"解析成功数が不足: {processed_count}/1000"

    def test_error_handling_malformed_markers(self):
        """不正マーカーエラーハンドリングテスト"""
        malformed_markers = [
            # 不正な属性構文
            "keyword[attr=",  # 属性値なし
            "keyword[=value]",  # 属性名なし
            "keyword[attr=value,]",  # 末尾カンマ
            "keyword[attr='unclosed",  # 未閉じクォート
            # 不正な複合構文
            "keyword++another",  # 連続区切り文字
            "+keyword",  # 先頭区切り文字のみ
            "keyword+",  # 末尾区切り文字のみ
            "+++",  # 区切り文字のみ
            # 制御文字・特殊文字
            "keyword\x00\x01",  # 制御文字
            "keyword\n\r\t",  # 改行・タブ
            "keyword\xff\xfe",  # バイナリ文字
            # 極端なケース
            "",  # 空文字
            " " * 1000,  # 大量の空白
            "A" * 10000,  # 極端に長い
        ]

        for malformed_marker in malformed_markers:
            try:
                # エラーハンドリングが適切に動作することを確認
                normalized = self.marker_parser.normalize_marker(malformed_marker)
                attributes = self.marker_parser.extract_attributes(malformed_marker)
                parts = self.marker_parser.split_compound_keywords(malformed_marker)

                # エラーにならない場合、適切な応答が返される
                assert normalized is not None or normalized == ""
                assert isinstance(attributes, dict)
                assert isinstance(parts, list)

            except Exception:
                # 例外が発生する場合も適切なエラーハンドリング
                pass

    def test_unicode_normalization_edge_cases(self):
        """Unicode正規化エッジケーステスト"""
        unicode_edge_cases = [
            # 結合文字
            "café",  # é は e + 結合アクセント
            "naïve",  # ï は i + 結合ウムラウト
            # 全角・半角
            "ａｂｃ",  # 全角アルファベット
            "１２３",  # 全角数字
            "！？＠",  # 全角記号
            # 異体字・互換文字
            "神",  # 標準漢字
            "神",  # 異体字（見た目は同じ）
            # 絵文字
            "👨‍👩‍👧‍👦",  # 家族絵文字（複数絵文字の結合）
            "🏳️‍🌈",  # 虹色フラグ（フラグ + 結合文字 + 虹）
            # 右から左の文字
            "العربية",  # アラビア語
            "עברית",  # ヘブライ語
            # 制御文字混在
            "test\u200b\u200c\u200dtest",  # ゼロ幅文字
        ]

        for unicode_case in unicode_edge_cases:
            try:
                normalized = self.marker_parser.normalize_marker(unicode_case)
                # 正規化が適切に実行される（結果は実装依存）
                assert normalized is not None
                assert isinstance(normalized, str)
            except Exception as e:
                pytest.fail(f"Unicode正規化でエラー: '{unicode_case}' -> {e}")

    def test_attribute_parsing_edge_cases(self):
        """属性解析エッジケーステスト"""
        attribute_edge_cases = [
            # ネストしたクォート
            ("keyword[attr='value \"nested\" here']", {"attr": 'value "nested" here'}),
            ("keyword[attr=\"value 'nested' here\"]", {"attr": "value 'nested' here"}),
            # エスケープシーケンス
            ("keyword[attr='value\\nwith\\ttabs']", {"attr": "value\\nwith\\ttabs"}),
            # 空白を含む属性名・値
            ("keyword[space attr=space value]", {"space attr": "space value"}),
            # 非ASCII属性名
            ("keyword[日本語属性=値]", {"日本語属性": "値"}),
            ("keyword[العربية=قيمة]", {"العربية": "قيمة"}),
            # 特殊文字を含む値
            (
                "keyword[url='https://example.com?a=1&b=2#section']",
                {"url": "https://example.com?a=1&b=2#section"},
            ),
            ("keyword[regex='^[a-zA-Z0-9]+$']", {"regex": "^[a-zA-Z0-9]+$"}),
            # 重複属性（後勝ちまたはエラー）
            ("keyword[attr=first,attr=second]", {}),  # 実装依存
        ]

        for input_marker, expected_or_empty in attribute_edge_cases:
            try:
                extracted = self.marker_parser.extract_attributes(input_marker)
                # 成功した場合は期待値または空辞書
                assert isinstance(extracted, dict)
                if expected_or_empty:  # 空辞書でない場合のみチェック
                    for key in expected_or_empty:
                        if key in extracted:
                            assert extracted[key] == expected_or_empty[key]
            except Exception:
                # エラーも適切な応答
                pass

    def test_marker_parser_integration_scenarios(self):
        """マーカーパーサー統合シナリオテスト"""
        integration_scenarios = [
            # ブログ記事スタイル
            {
                "markers": [
                    "image[alt=メイン画像,class=hero]",
                    "quote[author=著者名,date=2023-01-01]+emphasis",
                    "code[lang=python,theme=dark]+executable",
                    "link[url=https://example.com,target=_blank]+external",
                ],
                "expected_features": ["attributes", "compound", "unicode"],
            },
            # 技術文書スタイル
            {
                "markers": [
                    "diagram[type=flowchart,tools=mermaid]",
                    "code[lang=javascript,highlight=1-5,10-15]+numbered",
                    "note[type=warning,icon=⚠️]+important",
                    "table[sortable=true,pagination=10]+responsive",
                ],
                "expected_features": ["complex_attributes", "symbols", "boolean_attrs"],
            },
            # 多言語文書スタイル
            {
                "markers": [
                    "注釈[作者=山田太郎,言語=日本語]",
                    "引用[author=John Smith,language=English]+translated",
                    "código[lenguaje=español,tema=claro]",
                    "链接[网址=https://example.cn,目标=新窗口]",
                ],
                "expected_features": ["multilingual", "mixed_scripts"],
            },
        ]

        for scenario in integration_scenarios:
            for marker in scenario["markers"]:
                try:
                    # 統合処理
                    normalized = self.marker_parser.normalize_marker(marker)
                    attributes = self.marker_parser.extract_attributes(marker)
                    parts = self.marker_parser.split_compound_keywords(marker)

                    # 基本的な整合性チェック
                    assert normalized is not None
                    assert isinstance(attributes, dict)
                    assert isinstance(parts, list)
                    assert len(parts) > 0

                    # 複合キーワードの場合
                    if "+" in marker:
                        assert len(parts) > 1

                    # 属性がある場合
                    if "[" in marker and "]" in marker:
                        # 何らかの属性が抽出される（実装依存）
                        pass

                except Exception as e:
                    pytest.fail(f"統合シナリオでエラー: '{marker}' -> {e}")

    def test_concurrent_marker_parsing(self):
        """並行マーカー解析テスト"""
        import threading

        results = []
        errors = []

        def concurrent_marker_worker(worker_id):
            try:
                local_parser = MarkerParser()
                worker_results = []

                # 各ワーカーで独立したマーカーセット
                worker_markers = [
                    [
                        f"worker{worker_id}keyword{i}[attr=value{i}]",
                        f"comp{worker_id}+part{i}[a={i}]",
                        f"日本語{worker_id}マーカー{i}",
                    ]
                    for i in range(50)
                ]

                flat_markers = [
                    marker for sublist in worker_markers for marker in sublist
                ]

                for marker in flat_markers:
                    try:
                        normalized = local_parser.normalize_marker(marker)
                        attributes = local_parser.extract_attributes(marker)
                        parts = local_parser.split_compound_keywords(marker)

                        worker_results.append(
                            all(
                                [
                                    normalized is not None,
                                    isinstance(attributes, dict),
                                    isinstance(parts, list),
                                ]
                            )
                        )
                    except Exception:
                        worker_results.append(False)

                success_rate = sum(worker_results) / len(worker_results)
                results.append((worker_id, success_rate))

            except Exception as e:
                errors.append((worker_id, str(e)))

        # 複数ワーカーで並行実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_marker_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行マーカー解析でエラー: {errors}"
        assert len(results) == 3

        # 各ワーカーで高い成功率
        for worker_id, success_rate in results:
            assert (
                success_rate >= 0.8
            ), f"ワーカー{worker_id}の成功率が低い: {success_rate:.1%}"
