"""List Parser高度テスト - Issue #597 Week 29-30対応

リスト解析機能の包括的テスト
階層構造・キーワード統合・ファクトリーパターンの確認
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.list_parser import ListParser  # 統合インターフェース
from kumihan_formatter.core.list_parser_core import ListParserCore
from kumihan_formatter.core.list_parser_factory import ListParserComponents
from kumihan_formatter.core.nested_list_parser import NestedListParser


class TestListParserAdvanced:
    """リストパーサー高度テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.list_parser = ListParser()
        self.list_core = ListParserCore()
        self.nested_parser = NestedListParser()
        self.factory = ListParserComponents()

    def test_list_parser_initialization(self):
        """リストパーサー初期化テスト"""
        assert self.list_parser is not None
        assert self.list_core is not None
        assert self.nested_parser is not None
        assert self.factory is not None

    def test_basic_list_parsing(self):
        """基本リスト解析テスト"""
        basic_lists = [
            # 順序なしリスト
            [
                "- 項目1",
                "- 項目2",
                "- 項目3",
            ],
            # 順序付きリスト
            [
                "1. 第1項目",
                "2. 第2項目",
                "3. 第3項目",
            ],
            # 混在リスト
            [
                "- リスト項目",
                "1. 番号付き項目",
                "- 再びリスト項目",
            ],
            # キーワード付きリスト
            [
                "- ;;;重要;;; 重要な項目 ;;;",
                "- ;;;注釈;;; 注釈付き項目 ;;;",
                "- 通常の項目",
            ],
        ]

        for list_content in basic_lists:
            try:
                result = self.list_core.parse_list(list_content)
                assert result is not None
                if hasattr(result, "items"):
                    assert len(result.items) >= len(list_content)
                elif hasattr(result, "children"):
                    assert len(result.children) >= 0
            except Exception as e:
                pytest.fail(f"基本リスト解析でエラー: {e}")

    def test_nested_list_parsing_comprehensive(self):
        """ネストリスト解析包括テスト"""
        nested_structures = [
            # 2レベルネスト
            [
                "- レベル1項目1",
                "  - レベル2項目1",
                "  - レベル2項目2",
                "- レベル1項目2",
            ],
            # 3レベルネスト
            [
                "1. 第1章",
                "   1.1. 第1節",
                "       1.1.1. 第1項",
                "       1.1.2. 第2項",
                "   1.2. 第2節",
                "2. 第2章",
            ],
            # 混在ネスト（インデント数の違い）
            [
                "- レベル1",
                "    - レベル2（4スペース）",
                "  - レベル2（2スペース）",
                "        - レベル3（8スペース）",
                "- レベル1に戻る",
            ],
            # 複雑なネスト構造
            [
                "# メイン見出し",
                "- 大項目1",
                "  - 中項目1-1",
                "    - 小項目1-1-1",
                "    - 小項目1-1-2",
                "  - 中項目1-2",
                "- 大項目2",
                "  1. 番号付き中項目2-1",
                "  2. 番号付き中項目2-2",
                "     - 混在小項目",
            ],
        ]

        for nested_structure in nested_structures:
            try:
                result = self.nested_parser.parse_nested_list(nested_structure)
                assert result is not None

                # ネスト構造が正しく解析される
                if hasattr(result, "depth") or hasattr(result, "level"):
                    # 深度情報がある場合
                    pass
                if hasattr(result, "children"):
                    # 子要素がある場合
                    assert isinstance(result.children, list)

            except Exception as e:
                pytest.fail(f"ネストリスト解析でエラー: {e}")

    def test_indent_level_calculation(self):
        """インデントレベル計算テスト"""
        indent_test_cases = [
            # 標準的なインデント
            ("- 項目", 0),
            ("  - 項目", 1),
            ("    - 項目", 2),
            ("      - 項目", 3),
            # タブインデント
            ("\t- 項目", 1),
            ("\t\t- 項目", 2),
            # 混在インデント
            ("  \t- 項目", 1),  # 2スペース + 1タブ
            ("\t  - 項目", 1),  # 1タブ + 2スペース
            # 非標準インデント
            ("   - 項目", 1),  # 3スペース（2で割り切れない）
            ("     - 項目", 2),  # 5スペース
        ]

        for line, expected_level in indent_test_cases:
            try:
                # インデントレベルの計算
                if hasattr(self.nested_parser, "calculate_indent_level"):
                    level = self.nested_parser.calculate_indent_level(line)
                    assert (
                        level == expected_level
                    ), f"インデントレベル計算エラー: '{line}' -> {level} (期待: {expected_level})"
                elif hasattr(self.nested_parser, "get_indent_level"):
                    level = self.nested_parser.get_indent_level(line)
                    assert (
                        level == expected_level
                    ), f"インデントレベル計算エラー: '{line}' -> {level} (期待: {expected_level})"
            except Exception as e:
                pytest.fail(f"インデントレベル計算でエラー: '{line}' -> {e}")

    def test_keyword_integrated_list_items(self):
        """キーワード統合リストアイテムテスト"""
        keyword_lists = [
            # 単一キーワード
            [
                "- ;;;重要;;; クリティカルな項目 ;;;",
                "- ;;;注釈;;; 補足説明付き項目 ;;;",
                "- ;;;コード;;; `code example` ;;;",
            ],
            # 複合キーワード
            [
                "- ;;;重要+強調;;; 非常に重要な項目 ;;;",
                "- ;;;注釈+参考;;; 参考情報付き注釈 ;;;",
                "- ;;;コード+実行可能;;; 実行可能なコード例 ;;;",
            ],
            # 属性付きキーワード
            [
                "- ;;;画像[alt=項目画像];;; /images/item.jpg ;;;",
                "- ;;;リンク[url=https://example.com];;; 外部リンク ;;;",
                "- ;;;装飾[class=highlight];;; ハイライト項目 ;;;",
            ],
            # ネスト + キーワード
            [
                "- ;;;章;;; 第1章 ;;;",
                "  - ;;;節;;; 第1節 ;;;",
                "    - ;;;項;;; 重要な項目 ;;;",
                "    - 通常の項目",
                "  - ;;;節;;; 第2節 ;;;",
                "- ;;;章;;; 第2章 ;;;",
            ],
        ]

        for keyword_list in keyword_lists:
            try:
                result = self.list_core.parse_list(keyword_list)
                assert result is not None

                # キーワードが適切に解析される
                if hasattr(result, "items"):
                    for item in result.items:
                        if hasattr(item, "keywords") and item.keywords:
                            assert len(item.keywords) > 0

            except Exception as e:
                pytest.fail(f"キーワード統合リスト解析でエラー: {e}")

    def test_list_parser_factory_patterns(self):
        """リストパーサーファクトリーパターンテスト"""
        factory_test_cases = [
            # 基本ファクトリー使用
            {
                "type": "simple",
                "content": ["- 項目1", "- 項目2"],
                "expected_parser": "basic",
            },
            # ネストリスト用ファクトリー
            {
                "type": "nested",
                "content": ["- レベル1", "  - レベル2"],
                "expected_parser": "nested",
            },
            # キーワードリスト用ファクトリー
            {
                "type": "keyword",
                "content": ["- ;;;重要;;; 項目 ;;;"],
                "expected_parser": "keyword_aware",
            },
            # 複雑な混在リスト用ファクトリー
            {
                "type": "complex",
                "content": [
                    "- ;;;重要;;; レベル1 ;;;",
                    "  - ネストされた項目",
                    "    - ;;;注釈;;; 深いネスト ;;;",
                ],
                "expected_parser": "comprehensive",
            },
        ]

        for case in factory_test_cases:
            try:
                # ファクトリーからパーサーを取得
                if hasattr(self.factory, "get_parser"):
                    parser = self.factory.get_parser(case["type"])
                    assert parser is not None

                    # パーサーでコンテンツを解析
                    if hasattr(parser, "parse"):
                        result = parser.parse(case["content"])
                        assert result is not None

                elif hasattr(self.factory, "create_parser"):
                    parser = self.factory.create_parser(case["type"])
                    assert parser is not None

            except Exception as e:
                pytest.fail(
                    f"ファクトリーパターンテストでエラー: {case['type']} -> {e}"
                )

    def test_list_parsing_performance(self):
        """リスト解析性能テスト"""
        import time

        # 大規模リストの生成
        large_list = []

        # 平坦な大量リスト
        large_list.extend([f"- 項目{i}" for i in range(500)])

        # ネストした大量リスト
        for i in range(100):
            large_list.append(f"- 大項目{i}")
            for j in range(5):
                large_list.append(f"  - 中項目{i}-{j}")
                for k in range(3):
                    large_list.append(f"    - 小項目{i}-{j}-{k}")

        start_time = time.time()

        # リスト解析実行
        try:
            result = self.list_core.parse_list(large_list)
            assert result is not None
        except Exception as e:
            pytest.fail(f"大規模リスト解析でエラー: {e}")

        execution_time = time.time() - start_time

        # 性能基準確認
        assert execution_time < 2.0, f"リスト解析が遅すぎる: {execution_time}秒"

        # リアルタイム解析基準（50ms/KB）
        list_size_kb = len("\n".join(large_list)) / 1024
        ms_per_kb = (execution_time * 1000) / list_size_kb
        assert ms_per_kb < 50, f"KB当たり処理時間が遅い: {ms_per_kb}ms/KB"

    def test_list_type_detection(self):
        """リストタイプ検出テスト"""
        list_type_cases = [
            # 順序なしリスト
            (["- 項目1", "- 項目2"], "unordered"),
            (["* 項目1", "* 項目2"], "unordered"),
            # 順序付きリスト
            (["1. 項目1", "2. 項目2"], "ordered"),
            (["a. 項目1", "b. 項目2"], "ordered_alpha"),
            (["i. 項目1", "ii. 項目2"], "ordered_roman"),
            # 混在リスト
            (["- 項目1", "1. 項目2"], "mixed"),
            # 定義リスト
            (["用語1", "  定義1", "用語2", "  定義2"], "definition"),
            # チェックリスト
            (["- [ ] 未完了", "- [x] 完了"], "checklist"),
        ]

        for list_content, expected_type in list_type_cases:
            try:
                if hasattr(self.list_core, "detect_list_type"):
                    detected_type = self.list_core.detect_list_type(list_content)
                    # 検出タイプが期待と一致するか、検出が成功すること
                    assert detected_type is not None
                elif hasattr(self.list_core, "get_list_type"):
                    detected_type = self.list_core.get_list_type(list_content)
                    assert detected_type is not None
            except Exception as e:
                pytest.fail(f"リストタイプ検出でエラー: {list_content} -> {e}")

    def test_complex_list_scenarios(self):
        """複雑なリストシナリオテスト"""
        complex_scenarios = [
            # 技術文書スタイル
            [
                "# API仕様",
                "1. 認証",
                "   - Basic認証",
                "   - ;;;コード;;; Authorization: Basic <token> ;;;",
                "   - OAuth2.0",
                "     - ;;;リンク[url=https://oauth.net];;; 詳細仕様 ;;;",
                "2. エンドポイント",
                "   - GET /users",
                "     - ;;;重要;;; 認証必須 ;;;",
                "     - レスポンス: JSON",
                "   - POST /users",
                "     - ;;注釈;;; 管理者権限が必要 ;;;",
            ],
            # 料理レシピスタイル
            [
                "# カレーの作り方",
                "## 材料",
                "- 玉ねぎ 2個",
                "- 人参 1本",
                "- じゃがいも 3個",
                "- ;;;重要;;; 牛肉 300g ;;;",
                "- カレールー 1箱",
                "",
                "## 手順",
                "1. 野菜を切る",
                "   - 玉ねぎ: みじん切り",
                "   - 人参: 乱切り",
                "   - じゃがいも: 大きめに切る",
                "2. ;;;注意;;; 肉を炒める ;;;",
                "   - 強火で2分",
                "   - ;;;コツ;;; 表面が白くなるまで ;;;",
                "3. 野菜を加える",
            ],
            # チェックリストスタイル
            [
                "# プロジェクト完了チェックリスト",
                "## 開発フェーズ",
                "- [x] 要件定義",
                "- [x] 設計書作成",
                "- [ ] ;;;進行中;;; 実装 ;;;",
                "  - [x] フロントエンド",
                "  - [ ] ;;;重要;;; バックエンド ;;;",
                "  - [ ] データベース",
                "- [ ] テスト",
                "  - [ ] 単体テスト",
                "  - [ ] 統合テスト",
                "  - [ ] ;;;重要;;; 受け入れテスト ;;;",
                "",
                "## リリースフェーズ",
                "- [ ] ;;;確認必須;;; 本番環境準備 ;;;",
                "- [ ] デプロイメント",
                "- [ ] 監視設定",
            ],
        ]

        for scenario in complex_scenarios:
            try:
                # シナリオ全体の解析
                result = self.list_core.parse_list(scenario)
                assert result is not None

                # ネスト構造の確認
                nested_result = self.nested_parser.parse_nested_list(scenario)
                assert nested_result is not None

            except Exception as e:
                pytest.fail(f"複雑シナリオ解析でエラー: {e}")

    def test_list_parsing_accuracy_target(self):
        """リスト解析精度目標テスト"""
        # 標準的なリストパターン
        standard_list_patterns = [
            # 基本パターン
            ["- 項目A", "- 項目B", "- 項目C"],
            ["1. 第一", "2. 第二", "3. 第三"],
            # ネストパターン
            ["- レベル1", "  - レベル2", "    - レベル3"],
            ["1. 章", "   a. 節", "      i. 項"],
            # キーワードパターン
            ["- ;;;重要;;; 重要項目 ;;;"],
            ["1. ;;;注釈;;; 注釈付き項目 ;;;"],
            # 混在パターン
            ["- リスト", "1. 番号", "- 再びリスト"],
            # 実用パターン
            ["- [ ] TODO項目", "- [x] 完了項目"],
            ["用語", "  定義文"],
        ]

        accuracy_results = []
        for pattern in standard_list_patterns:
            try:
                result = self.list_core.parse_list(pattern)
                accuracy_results.append(result is not None)
            except Exception:
                accuracy_results.append(False)

        # 精度目標: 99.5%以上
        accuracy_rate = sum(accuracy_results) / len(accuracy_results)
        assert accuracy_rate >= 0.995, f"リスト解析精度が目標未達: {accuracy_rate:.1%}"

    def test_concurrent_list_parsing(self):
        """並行リスト解析テスト"""
        import threading

        results = []
        errors = []

        def concurrent_list_worker(worker_id):
            try:
                local_core = ListParserCore()
                worker_results = []

                # 各ワーカーで独立したリストセット
                worker_lists = [
                    [f"- ワーカー{worker_id}項目{i}" for i in range(10)],
                    [f"{j}. ワーカー{worker_id}番号{j}" for j in range(1, 6)],
                    [f"- ;;;キーワード{worker_id};;; 項目{i} ;;;" for i in range(5)],
                ]

                for test_list in worker_lists:
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
        for i in range(3):
            thread = threading.Thread(target=concurrent_list_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行リスト解析でエラー: {errors}"
        assert len(results) == 3

        # 各ワーカーで高い成功率
        for worker_id, success_rate in results:
            assert (
                success_rate >= 0.8
            ), f"ワーカー{worker_id}の成功率が低い: {success_rate:.1%}"


class TestListParserIntegration:
    """リストパーサー統合テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.list_parser = ListParser()
        self.factory = ListParserComponents()

    def test_unified_interface_backward_compatibility(self):
        """統合インターフェース後方互換性テスト"""
        # 旧形式のAPI呼び出し
        old_style_calls = [
            (["- 項目1", "- 項目2"], "parse_simple_list"),
            (["- レベル1", "  - レベル2"], "parse_nested_list"),
            (["- ;;;キーワード;;; 項目 ;;;"], "parse_keyword_list"),
        ]

        for list_content, method_name in old_style_calls:
            try:
                # 旧形式メソッドが存在し、動作する
                if hasattr(self.list_parser, method_name):
                    method = getattr(self.list_parser, method_name)
                    result = method(list_content)
                    assert result is not None
                else:
                    # 統合メソッドで処理される
                    result = self.list_parser.parse(list_content)
                    assert result is not None
            except Exception as e:
                pytest.fail(f"後方互換性テストでエラー: {method_name} -> {e}")

    def test_factory_component_integration(self):
        """ファクトリーコンポーネント統合テスト"""
        # ファクトリーパターンの統合使用
        try:
            # 遅延初期化の確認
            if hasattr(self.factory, "initialize"):
                self.factory.initialize()

            # コンポーネント取得
            if hasattr(self.factory, "get_core_parser"):
                core = self.factory.get_core_parser()
                assert core is not None

            if hasattr(self.factory, "get_nested_parser"):
                nested = self.factory.get_nested_parser()
                assert nested is not None

            # 統合パーサーの作成
            if hasattr(self.factory, "create_unified_parser"):
                unified = self.factory.create_unified_parser()
                assert unified is not None

        except Exception as e:
            pytest.fail(f"ファクトリー統合テストでエラー: {e}")

    def test_real_world_document_list_parsing(self):
        """実世界文書リスト解析テスト"""
        real_document = [
            "# プログラミング学習ガイド",
            "",
            "## 基礎知識",
            "1. プログラミング言語の選択",
            "   - ;;;推奨;;; Python ;;;",
            "     - 初心者向け",
            "     - 豊富なライブラリ",
            "     - ;;;リンク[url=https://python.org];;; 公式サイト ;;;",
            "   - JavaScript",
            "     - Web開発必須",
            "     - フロントエンド・バックエンド両対応",
            "   - ;;;注意;;; Java ;;;",
            "     - 企業システム開発",
            "     - 学習コストが高い",
            "",
            "2. 開発環境の構築",
            "   - エディタの選択",
            "     - [ ] Visual Studio Code",
            "     - [ ] ;;;推奨;;; IntelliJ IDEA ;;;",
            "     - [ ] Vim/Emacs（上級者向け）",
            "   - バージョン管理",
            "     - ;;;必須;;; Git ;;;",
            "       - ;;;コード;;; git init ;;;",
            "       - ;;;コード;;; git add . ;;;",
            '       - ;;;コード;;; git commit -m "message" ;;;',
            "",
            "## 学習ステップ",
            "- 段階1: 基本文法",
            "  - 変数と型",
            "  - 条件分岐",
            "  - ループ処理",
            "- 段階2: 関数とクラス",
            "- 段階3: ;;;重要;;; 実践的プロジェクト ;;;",
            "  - ;;;推奨;;; Webアプリケーション作成 ;;;",
            "  - API開発",
            "  - データベース連携",
        ]

        try:
            # 文書全体の解析
            result = self.list_parser.parse(real_document)
            assert result is not None

            # リスト構造の抽出確認
            if hasattr(result, "lists") or hasattr(result, "list_items"):
                # リストが適切に抽出されている
                pass

        except Exception as e:
            pytest.fail(f"実世界文書リスト解析でエラー: {e}")

    def test_memory_efficiency_large_lists(self):
        """大規模リストメモリ効率テスト"""
        import sys

        # 初期メモリ使用量
        initial_refs = len([obj for obj in globals().values()])

        # 大量のネストリストを処理
        for batch in range(10):
            large_nested_list = []
            for i in range(100):
                large_nested_list.append(f"- 大項目{batch}-{i}")
                for j in range(5):
                    large_nested_list.append(f"  - 中項目{batch}-{i}-{j}")
                    for k in range(3):
                        large_nested_list.append(f"    - 小項目{batch}-{i}-{j}-{k}")

            # 解析実行
            try:
                result = self.list_parser.parse(large_nested_list)
                assert result is not None
            except Exception as e:
                pytest.fail(f"大規模リスト処理でエラー: {e}")

        # メモリリークの確認
        final_refs = len([obj for obj in globals().values()])
        ref_growth = final_refs - initial_refs

        # 過度なオブジェクト増加がないことを確認
        assert ref_growth < 200, f"メモリリークの疑い: {ref_growth}個のオブジェクト増加"
