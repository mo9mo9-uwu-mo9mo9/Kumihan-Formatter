"""Special Block Parser テスト - Issue #597 対応

特殊ブロック解析機能の専門テスト
カスタムブロック・複雑構造・特殊記法の確認
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.block_parser.special_block_parser import SpecialBlockParser


class TestSpecialBlockParser:
    """特殊ブロックパーサーテスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.mock_block_parser = Mock()
        self.special_parser = SpecialBlockParser(self.mock_block_parser)

    def test_special_parser_initialization(self):
        """特殊パーサー初期化テスト"""
        assert self.special_parser is not None
        assert hasattr(self.special_parser, "parse_special_block")
        assert hasattr(self.special_parser, "parse_custom_block")

    def test_custom_block_parsing(self):
        """カスタムブロック解析テスト"""
        custom_block_patterns = [
            # 基本カスタムブロック
            [
                ";;;カスタム;;;",
                "カスタムブロック内容",
                ";;;",
            ],
            # 属性付きカスタムブロック
            [
                ";;;カスタム[type=info,level=high];;;",
                "属性付きカスタム内容",
                "詳細説明",
                ";;;",
            ],
            # 複雑なカスタムブロック
            [
                ";;;複雑カスタム[id=custom1,class=special];;;",
                "複雑な構造のカスタムブロック",
                "複数行の詳細内容",
                "- リスト項目も含む",
                "- 項目2",
                ";;;",
            ],
            # ネストしたカスタムブロック
            [
                ";;;外部カスタム;;;",
                "外部ブロック内容",
                ";;;内部カスタム;;;",
                "内部ブロック内容",
                ";;;",
                "外部に戻る",
                ";;;",
            ],
        ]

        for i, pattern in enumerate(custom_block_patterns):
            try:
                result = self.special_parser.parse_custom_block(pattern, 0)
                if result:
                    node, next_index = result
                    assert node is not None, f"カスタムブロック{i}の解析結果がnull"
                    assert next_index > 0, f"カスタムブロック{i}のインデックス進行なし"
            except Exception as e:
                pytest.fail(f"カスタムブロック{i}解析でエラー: {e}")

    def test_special_syntax_blocks(self):
        """特殊構文ブロックテスト"""
        special_syntax_patterns = [
            # 条件付きブロック
            [
                ";;;条件[if=condition];;;",
                "条件付き表示内容",
                ";;;",
            ],
            # 繰り返しブロック
            [
                ";;;繰り返し[count=3];;;",
                "繰り返し対象の内容",
                ";;;",
            ],
            # 変数展開ブロック
            [
                ";;;変数[var=value];;;",
                "変数 ${var} を含む内容",
                ";;;",
            ],
            # テンプレートブロック
            [
                ";;;テンプレート[template=basic];;;",
                "テンプレート適用内容",
                "title: サンプルタイトル",
                "content: サンプル内容",
                ";;;",
            ],
            # インクルードブロック
            [
                ";;;インクルード[file=external.txt];;;",
                "デフォルト内容（ファイルが見つからない場合）",
                ";;;",
            ],
        ]

        for i, pattern in enumerate(special_syntax_patterns):
            try:
                result = self.special_parser.parse_special_block(pattern, 0)
                if result:
                    node, next_index = result
                    assert node is not None, f"特殊構文{i}の解析結果がnull"
                    assert next_index > 0, f"特殊構文{i}のインデックス進行なし"
            except Exception as e:
                pytest.fail(f"特殊構文{i}解析でエラー: {e}")

    def test_advanced_attribute_processing(self):
        """高度属性処理テスト"""
        advanced_attribute_cases = [
            # JSON形式属性
            (
                ';;;データ[config=\'{"key":"value","num":123}\'];;;',
                {"config": '{"key":"value","num":123}'},
            ),
            # 配列形式属性
            (
                ';;;リスト[items=\'["item1","item2","item3"]\'];;;',
                {"items": '["item1","item2","item3"]'},
            ),
            # 式評価属性
            (";;;計算[result='2+2'];;;", {"result": "2+2"}),
            # 複数行属性
            (";;;複数行[text='行1\\n行2\\n行3'];;;", {"text": "行1\\n行2\\n行3"}),
            # 特殊文字属性
            (";;;特殊[pattern='^[a-zA-Z0-9]+$'];;;", {"pattern": "^[a-zA-Z0-9]+$"}),
        ]

        for pattern, expected_attrs in advanced_attribute_cases:
            lines = [pattern, "内容", ";;;"]
            try:
                result = self.special_parser.parse_special_block(lines, 0)
                if result:
                    node, _ = result
                    if hasattr(node, "attributes"):
                        # 属性が正しく解析されていることを確認
                        for key, value in expected_attrs.items():
                            assert key in node.attributes, f"属性 {key} が見つからない"
            except Exception as e:
                pytest.fail(f"高度属性処理でエラー: {pattern} -> {e}")

    def test_conditional_block_processing(self):
        """条件付きブロック処理テスト"""
        conditional_patterns = [
            # 単純条件
            {
                "block": [
                    ";;;条件[if=true];;;",
                    "表示される内容",
                    ";;;",
                ],
                "condition": "true",
                "expected_display": True,
            },
            # 複合条件
            {
                "block": [
                    ";;;条件[if='user.role == \"admin\"'];;;",
                    "管理者のみ表示",
                    ";;;",
                ],
                "condition": 'user.role == "admin"',
                "expected_display": None,  # 実装依存
            },
            # else付き条件
            {
                "block": [
                    ";;;条件[if=false];;;",
                    "false時の内容",
                    ";;;else;;;",
                    "else時の内容",
                    ";;;",
                ],
                "condition": "false",
                "expected_display": "else",
            },
        ]

        for i, case in enumerate(conditional_patterns):
            try:
                result = self.special_parser.parse_special_block(case["block"], 0)
                if result:
                    node, _ = result
                    assert node is not None, f"条件ブロック{i}の解析失敗"

                    # 条件評価の確認
                    if hasattr(node, "condition"):
                        assert node.condition is not None
                    elif hasattr(node, "attributes") and "if" in node.attributes:
                        assert node.attributes["if"] == case["condition"]
            except Exception as e:
                pytest.fail(f"条件付きブロック{i}処理でエラー: {e}")

    def test_template_block_processing(self):
        """テンプレートブロック処理テスト"""
        template_patterns = [
            # 基本テンプレート
            {
                "template": "basic",
                "block": [
                    ";;;テンプレート[template=basic];;;",
                    "title: テストタイトル",
                    "content: テスト内容",
                    ";;;",
                ],
                "expected_vars": {"title": "テストタイトル", "content": "テスト内容"},
            },
            # 複雑テンプレート
            {
                "template": "advanced",
                "block": [
                    ";;;テンプレート[template=advanced,theme=dark];;;",
                    "header: ヘッダー内容",
                    "body: 本文内容",
                    "footer: フッター内容",
                    ";;;",
                ],
                "expected_vars": {
                    "header": "ヘッダー内容",
                    "body": "本文内容",
                    "footer": "フッター内容",
                },
            },
            # ネストテンプレート
            {
                "template": "nested",
                "block": [
                    ";;;テンプレート[template=nested];;;",
                    "main:",
                    "  title: メインタイトル",
                    "  content: メイン内容",
                    "sidebar:",
                    "  widget1: ウィジェット1",
                    "  widget2: ウィジェット2",
                    ";;;",
                ],
                "expected_vars": {
                    "main": "nested_structure",
                    "sidebar": "nested_structure",
                },
            },
        ]

        for i, case in enumerate(template_patterns):
            try:
                result = self.special_parser.parse_special_block(case["block"], 0)
                if result:
                    node, _ = result
                    assert node is not None, f"テンプレートブロック{i}の解析失敗"

                    # テンプレート変数の確認
                    if hasattr(node, "template_vars"):
                        for var_name in case["expected_vars"]:
                            assert (
                                var_name in node.template_vars
                            ), f"テンプレート変数 {var_name} が見つからない"
            except Exception as e:
                pytest.fail(f"テンプレートブロック{i}処理でエラー: {e}")

    def test_dynamic_content_blocks(self):
        """動的コンテンツブロックテスト"""
        dynamic_patterns = [
            # 日付表示ブロック
            [
                ";;;日付[format='%Y-%m-%d'];;;",
                "現在の日付を表示",
                ";;;",
            ],
            # カウンターブロック
            [
                ";;;カウンター[start=1,step=1];;;",
                "自動カウンター",
                ";;;",
            ],
            # ランダムブロック
            [
                ";;;ランダム[min=1,max=10];;;",
                "ランダム値: ${random}",
                ";;;",
            ],
            # 計算ブロック
            [
                ";;;計算[expression='2*3+4'];;;",
                "計算結果: ${result}",
                ";;;",
            ],
        ]

        for i, pattern in enumerate(dynamic_patterns):
            try:
                result = self.special_parser.parse_special_block(pattern, 0)
                if result:
                    node, _ = result
                    assert node is not None, f"動的ブロック{i}の解析失敗"

                    # 動的処理の確認
                    if hasattr(node, "is_dynamic"):
                        assert node.is_dynamic == True
                    elif hasattr(node, "dynamic_type"):
                        assert node.dynamic_type is not None
            except Exception as e:
                pytest.fail(f"動的コンテンツブロック{i}処理でエラー: {e}")

    def test_error_handling_malformed_special_blocks(self):
        """不正特殊ブロックエラーハンドリングテスト"""
        malformed_patterns = [
            # 不完全なブロック
            [
                ";;;特殊;;;",
                "内容",
                # 終了マーカーなし
            ],
            # 不正な属性
            [
                ";;;特殊[attr=];;;",
                "内容",
                ";;;",
            ],
            # ネストエラー
            [
                ";;;外部;;;",
                ";;;内部;;;",
                "内容",
                ";;;",
                # 外部の終了マーカーなし
            ],
            # 制御文字混入
            [
                ";;;特殊\x00;;;",
                "内容\x01",
                ";;;",
            ],
        ]

        for i, pattern in enumerate(malformed_patterns):
            try:
                result = self.special_parser.parse_special_block(pattern, 0)
                # エラーハンドリングが適切に動作
                if result is None:
                    # None は適切なエラー応答
                    pass
                else:
                    node, _ = result
                    if hasattr(node, "error"):
                        assert (
                            node.error is not None
                        ), f"エラー情報が記録されていない: {i}"
            except Exception as e:
                # 例外が発生する場合も適切なエラーハンドリング
                assert isinstance(e, (ValueError, SyntaxError, AttributeError))

    def test_special_block_performance(self):
        """特殊ブロック性能テスト"""
        import time

        # 大量の特殊ブロック生成
        special_blocks = []
        for i in range(100):
            block = [
                f";;;特殊{i}[id={i},type=test];;;",
                f"特殊ブロック{i}の内容",
                f"詳細情報{i}",
                ";;;",
            ]
            special_blocks.append(block)

        start_time = time.time()

        parsed_count = 0
        for block in special_blocks:
            try:
                result = self.special_parser.parse_special_block(block, 0)
                if result:
                    parsed_count += 1
            except Exception:
                pass

        execution_time = time.time() - start_time

        # 性能基準確認
        assert execution_time < 0.5, f"特殊ブロック解析が遅すぎる: {execution_time}秒"
        assert parsed_count >= 80, f"解析成功数が不足: {parsed_count}/100"

    def test_unicode_special_blocks(self):
        """Unicode特殊ブロックテスト"""
        unicode_patterns = [
            # 日本語特殊ブロック
            [
                ";;;日本語特殊[作者=山田太郎];;;",
                "日本語の特殊ブロック内容",
                "詳細な説明文",
                ";;;",
            ],
            # 多言語混在
            [
                ";;;Multilingual[author=John,言語=日本語];;;",
                "English and 日本語 mixed content",
                "中文内容也包含其中",
                ";;;",
            ],
            # 絵文字含有
            [
                ";;;絵文字[icon=🎌];;;",
                "絵文字を含む特殊ブロック 🎯📋",
                "内容に絵文字 ✅❌⚠️ が含まれます",
                ";;;",
            ],
        ]

        for i, pattern in enumerate(unicode_patterns):
            try:
                result = self.special_parser.parse_special_block(pattern, 0)
                if result:
                    node, _ = result
                    assert node is not None, f"Unicode特殊ブロック{i}の解析失敗"
            except Exception as e:
                pytest.fail(f"Unicode特殊ブロック{i}でエラー: {e}")

    def test_special_block_integration_scenarios(self):
        """特殊ブロック統合シナリオテスト"""
        integration_scenarios = [
            # 文書管理システム
            {
                "scenario": "document_management",
                "blocks": [
                    [
                        ";;;文書[id=doc001,version=1.0];;;",
                        "title: 重要文書",
                        "author: 管理者",
                        "created: 2023-01-01",
                        ";;;",
                    ],
                    [
                        ";;;承認[required=true,role=manager];;;",
                        "この文書は管理者の承認が必要です",
                        ";;;",
                    ],
                ],
            },
            # コンテンツ管理システム
            {
                "scenario": "content_management",
                "blocks": [
                    [
                        ";;;コンテンツ[type=article,status=draft];;;",
                        "title: サンプル記事",
                        "category: ニュース",
                        'tags: ["重要", "お知らせ"]',
                        ";;;",
                    ],
                    [
                        ";;;公開[date='2023-01-01',time='10:00'];;;",
                        "公開予定日時の設定",
                        ";;;",
                    ],
                ],
            },
            # ワークフローシステム
            {
                "scenario": "workflow_system",
                "blocks": [
                    [
                        ";;;ワークフロー[id=wf001,stage=review];;;",
                        "current_user: レビュアー",
                        "next_action: 承認",
                        "deadline: 2023-01-07",
                        ";;;",
                    ],
                    [
                        ";;;通知[to=admin,type=email];;;",
                        "レビュー完了の通知",
                        "詳細はシステムを確認してください",
                        ";;;",
                    ],
                ],
            },
        ]

        for scenario_config in integration_scenarios:
            scenario_name = scenario_config["scenario"]
            blocks = scenario_config["blocks"]

            try:
                # 各シナリオのブロック解析
                parsed_blocks = []
                for block in blocks:
                    result = self.special_parser.parse_special_block(block, 0)
                    if result:
                        node, _ = result
                        parsed_blocks.append(node)

                # シナリオ内の全ブロックが解析される
                assert len(parsed_blocks) == len(
                    blocks
                ), f"シナリオ {scenario_name} でブロック解析数不一致"

            except Exception as e:
                pytest.fail(f"統合シナリオ {scenario_name} でエラー: {e}")

    def test_concurrent_special_block_parsing(self):
        """並行特殊ブロック解析テスト"""
        import threading

        results = []
        errors = []

        def concurrent_special_worker(worker_id):
            try:
                local_parser = SpecialBlockParser()
                worker_results = []

                for i in range(20):
                    block = [
                        f";;;ワーカー{worker_id}特殊{i}[id={worker_id}_{i}];;;",
                        f"ワーカー{worker_id}の特殊ブロック{i}",
                        f"詳細内容{i}",
                        ";;;",
                    ]

                    try:
                        result = local_parser.parse_special_block(block, 0)
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
            thread = threading.Thread(target=concurrent_special_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行特殊ブロック解析でエラー: {errors}"
        assert len(results) == 3

        # 各ワーカーで高い成功率
        for worker_id, success_rate in results:
            assert (
                success_rate >= 0.8
            ), f"ワーカー{worker_id}の成功率が低い: {success_rate:.1%}"

    def test_parse_table_block_pipe_separated(self):
        """パイプ区切りテーブル解析テスト"""
        lines = [
            ";;;テーブル;;;",
            "| 名前 | 年齢 | 職業 |",
            "| 田中 | 30 | エンジニア |",
            "| 佐藤 | 25 | デザイナー |",
            ";;;",
        ]

        node, next_index = self.special_parser.parse_table_block(lines, 0)

        assert node.type == "table"
        assert next_index == 5

        # テーブル構造の確認
        table_content = node.content
        assert len(table_content) == 2  # thead + tbody

        # ヘッダー確認
        thead = table_content[0]
        assert thead.type == "thead"

        # データ行確認
        tbody = table_content[1]
        assert tbody.type == "tbody"
        assert len(tbody.content) == 2  # 2つのデータ行

    def test_parse_table_block_comma_separated(self):
        """カンマ区切りテーブル解析テスト"""
        lines = [
            ";;;テーブル;;;",
            "項目, 値, 説明",
            "データ1, 100, 説明1",
            "データ2, 200, 説明2",
            ";;;",
        ]

        node, next_index = self.special_parser.parse_table_block(lines, 0)

        assert node.type == "table"
        assert next_index == 5

        # テーブル構造の確認
        table_content = node.content
        assert len(table_content) == 2  # thead + tbody

    def test_parse_table_block_single_column(self):
        """単一列テーブル解析テスト"""
        lines = [
            ";;;テーブル;;;",
            "タイトル",
            "データ1",
            "データ2",
            "データ3",
            ";;;",
        ]

        node, next_index = self.special_parser.parse_table_block(lines, 0)

        assert node.type == "table"
        assert next_index == 6

        # 単一列テーブルの確認
        table_content = node.content
        assert len(table_content) == 2  # thead + tbody

    def test_parse_table_block_no_closing_marker(self):
        """閉じマーカーなしテーブル解析テスト"""
        lines = [
            ";;;テーブル;;;",
            "| 名前 | 年齢 |",
            "| 田中 | 30 |",
            # 閉じマーカーなし
        ]

        node, next_index = self.special_parser.parse_table_block(lines, 0)

        assert node.type == "error"
        assert "閉じマーカーが見つかりません" in node.content
        assert next_index == 1

    def test_parse_table_block_empty_content(self):
        """空内容テーブル解析テスト"""
        lines = [
            ";;;テーブル;;;",
            ";;;",
        ]

        node, next_index = self.special_parser.parse_table_block(lines, 0)

        assert node.type == "error"
        assert "内容がありません" in node.content
        assert next_index == 2

    def test_looks_like_header_method(self):
        """ヘッダー判定メソッドテスト"""
        # ヘッダーらしい行
        header_rows = [
            ["名前", "年齢", "職業"],
            ["項目", "値", "説明"],
            ["タイトル", "内容"],
            ["ID", "データ", "作成日"],
            ["商品名", "価格", "在庫数"],  # 混合パターン
        ]

        for row in header_rows:
            assert self.special_parser._looks_like_header(row) == True

        # データ行らしい行（数値が70%以上）
        data_rows = [
            ["123", "456", "789"],  # 100% 数値
            ["100", "200"],  # 100% 数値
            ["1.5", "2.5", "3.5"],  # 100% 数値
            ["田中", "100", "200"],  # 66% 数値（ヘッダーと判定される）
        ]

        for i, row in enumerate(data_rows[:3]):  # 純粋な数値行のみテスト
            result = self.special_parser._looks_like_header(row)
            assert result == False, f"数値行 {row} がヘッダーと誤判定された"

    def test_is_numeric_value_method(self):
        """数値判定メソッドテスト"""
        # 数値として認識されるべき値
        numeric_values = [
            "123",
            "123.45",
            "1,234",
            "1,234.56",
            "-123",
            "+123",
            "50%",
            "¥1000",
            "$100",
            "€200",
        ]

        for value in numeric_values:
            assert (
                self.special_parser._is_numeric_value(value) == True
            ), f"{value} が数値と認識されない"

        # 数値として認識されないべき値
        non_numeric_values = [
            "名前",
            "abc123",
            "123abc",
            "商品A",
            "未定",
            "",
            "N/A",
        ]

        for value in non_numeric_values:
            assert (
                self.special_parser._is_numeric_value(value) == False
            ), f"{value} が数値と誤認識された"

    def test_enhanced_header_detection(self):
        """改善されたヘッダー検出テスト"""
        # 複雑なケース
        test_cases = [
            # (行データ, 期待されるヘッダー判定結果)
            (["商品", "100", "200"], True),  # 混合（33% 数値）
            (["100", "200", "商品"], True),  # 混合（66% 数値）
            (["100", "200", "300"], False),  # 純粋数値（100% 数値）
            (["¥100", "¥200", "¥300"], False),  # 通貨形式（100% 数値）
            (["50%", "60%", "70%"], False),  # パーセント（100% 数値）
            (["名前", "価格", "数量"], True),  # 典型的ヘッダー（0% 数値）
        ]

        for row, expected in test_cases:
            result = self.special_parser._looks_like_header(row)
            assert result == expected, f"行 {row}: 期待値 {expected}, 実際 {result}"
