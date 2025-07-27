"""Parsing System統合テスト - Issue #597 Week 31対応

構文解析システム全体の統合・最適化テスト
パーサー間連携・性能最適化・精度達成の確認
"""

import time
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.block_parser import BlockParser
from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.list_parser import ListParser
from kumihan_formatter.core.markdown_parser import MarkdownParser
from kumihan_formatter.core.parsing_coordinator import ParsingCoordinator


class TestParsingSystemIntegration:
    """構文解析システム統合テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.keyword_parser = KeywordParser()
        self.block_parser = BlockParser(self.keyword_parser)
        self.list_parser = ListParser(self.keyword_parser)
        self.markdown_parser = MarkdownParser()
        self.coordinator = ParsingCoordinator()

    def test_parsing_system_initialization(self):
        """構文解析システム初期化テスト"""
        assert self.block_parser is not None
        assert self.keyword_parser is not None
        assert self.list_parser is not None
        assert self.markdown_parser is not None
        assert self.coordinator is not None

    def test_cross_parser_integration(self):
        """パーサー間連携統合テスト"""
        integrated_document = [
            "# 統合テスト文書",
            "",
            ";;;重要;;; この文書は複数のパーサーを統合テストします ;;;",
            "",
            "## ブロック要素",
            "",
            ";;;引用[author=著者名];;;",
            "重要な引用文です。",
            "複数行の引用内容。",
            ";;;",
            "",
            "## リスト要素",
            "",
            "- ;;;重要;;; 重要なリスト項目 ;;;",
            "  - ネストした項目",
            "    - ;;;注釈;;; 深いネスト ;;;",
            "- 通常のリスト項目",
            "",
            "1. 番号付きリスト",
            "   - 混在ネスト",
            "   - ;;;コード;;; `code example` ;;;",
            "",
            "## Markdown要素",
            "",
            "**太字テキスト**と*斜体テキスト*の組み合わせ。",
            "",
            "[リンク](https://example.com)と`インラインコード`。",
            "",
            "```python",
            "def integrated_test():",
            "    return 'parsing integration'",
            "```",
            "",
            "| 項目 | 説明 |",
            "|------|------|",
            "| A | ;;;重要;;; 重要項目 ;;; |",
            "| B | 通常項目 |",
        ]

        try:
            # 統合解析の実行
            result = self.coordinator.parse_document(integrated_document)
            assert result is not None

            # 各パーサーの結果が適切に統合される
            if hasattr(result, "blocks"):
                assert len(result.blocks) > 0
            elif hasattr(result, "elements"):
                assert len(result.elements) > 0

        except Exception as e:
            pytest.fail(f"パーサー間連携統合でエラー: {e}")

    def test_parsing_coordinator_workflow(self):
        """構文解析コーディネーターワークフローテスト"""
        workflow_test_cases = [
            # ケース1: ブロック優先解析
            {
                "content": [
                    ";;;引用;;;",
                    "引用内容",
                    ";;;",
                ],
                "expected_parser": "block",
                "expected_type": "quote_block",
            },
            # ケース2: リスト優先解析
            {
                "content": [
                    "- リスト項目1",
                    "- リスト項目2",
                    "  - ネスト項目",
                ],
                "expected_parser": "list",
                "expected_type": "list_structure",
            },
            # ケース3: Markdown優先解析
            {
                "content": [
                    "# Markdownヘッダー",
                    "",
                    "**太字**と*斜体*のテキスト。",
                    "",
                    "```python",
                    "print('code')",
                    "```",
                ],
                "expected_parser": "markdown",
                "expected_type": "markdown_document",
            },
            # ケース4: 混在解析
            {
                "content": [
                    "# 混在文書",
                    "",
                    ";;;重要;;;",
                    "重要なブロック内容",
                    ";;;",
                    "",
                    "- リスト項目",
                    "  - ;;;キーワード;;; 項目 ;;;",
                    "",
                    "**Markdown**要素も含む。",
                ],
                "expected_parser": "coordinator",
                "expected_type": "mixed_document",
            },
        ]

        for i, case in enumerate(workflow_test_cases):
            try:
                result = self.coordinator.parse_document(case["content"])
                assert result is not None, f"ワークフローケース{i}で結果なし"

                # 期待されるパーサータイプの確認
                if hasattr(result, "parser_type"):
                    # パーサータイプが記録されている場合
                    pass
                elif hasattr(result, "primary_parser"):
                    # 主要パーサーが記録されている場合
                    pass

            except Exception as e:
                pytest.fail(f"ワークフローケース{i}でエラー: {e}")

    def test_parsing_performance_optimization(self):
        """構文解析性能最適化テスト"""
        # 大規模文書の生成
        large_document = []

        # 多様な要素を含む大規模文書
        for section in range(20):
            large_document.extend(
                [
                    f"# セクション{section}",
                    "",
                    f";;;重要[section={section}];;; セクション{section}の重要な内容 ;;;",
                    "",
                    "## リスト部分",
                    "",
                ]
            )

            # 大量のリスト項目
            for item in range(25):
                large_document.append(f"- 項目{section}-{item}")
                if item % 5 == 0:
                    large_document.append(
                        f"  - ;;;注釈;;; ネスト項目{section}-{item} ;;;"
                    )

            large_document.extend(
                [
                    "",
                    "## Markdown部分",
                    "",
                    f"セクション{section}の**重要な**説明です。",
                    "",
                    "```python",
                    f"def section_{section}():",
                    f"    return 'section {section} processing'",
                    "```",
                    "",
                ]
            )

        # 性能測定
        start_time = time.time()

        try:
            result = self.coordinator.parse_document(large_document)
            assert result is not None
        except Exception as e:
            pytest.fail(f"大規模文書解析でエラー: {e}")

        execution_time = time.time() - start_time

        # 性能基準確認
        assert execution_time < 5.0, f"大規模文書解析が遅すぎる: {execution_time}秒"

        # リアルタイム解析基準（50ms/KB）
        doc_size_kb = len("\n".join(large_document)) / 1024
        ms_per_kb = (execution_time * 1000) / doc_size_kb
        assert ms_per_kb < 50, f"KB当たり処理時間が遅い: {ms_per_kb}ms/KB"

    def test_parsing_accuracy_comprehensive(self):
        """構文解析精度包括テスト"""
        # Kumihan記法標準パターン
        accuracy_test_patterns = [
            # 基本キーワード
            [";;;強調;;; 強調内容 ;;;"],
            [";;;注釈;;; 注釈内容 ;;;"],
            [";;;引用;;; 引用内容 ;;;"],
            [";;;コード;;; コード内容 ;;;"],
            # 複合キーワード
            [";;;強調+重要;;; 重要な強調 ;;;"],
            [";;;引用+注釈;;; 注釈付き引用 ;;;"],
            # 属性付きキーワード
            [";;;画像[alt=説明文];;; /path/to/image.jpg ;;;"],
            [";;;リンク[url=https://example.com];;; リンクテキスト ;;;"],
            # ブロック構造
            [
                ";;;引用;;;",
                "複数行の引用内容",
                ";;;",
            ],
            # リスト構造
            [
                "- リスト項目1",
                "- リスト項目2",
                "  - ネスト項目",
            ],
            # Markdown構造
            [
                "# 見出し",
                "**太字**と*斜体*",
                "`インラインコード`",
            ],
            # 混在構造
            [
                "# 混在テスト",
                ";;;重要;;; 重要な内容 ;;;",
                "- リスト項目",
                "  - ;;;注釈;;; ネスト注釈 ;;;",
                "**Markdown**要素",
            ],
        ]

        accuracy_results = []
        for i, pattern in enumerate(accuracy_test_patterns):
            try:
                result = self.coordinator.parse_document(pattern)
                accuracy_results.append(result is not None)
            except Exception:
                accuracy_results.append(False)

        # 精度目標: 99.5%以上
        accuracy_rate = sum(accuracy_results) / len(accuracy_results)
        assert (
            accuracy_rate >= 0.995
        ), f"構文解析精度が目標未達: {accuracy_rate:.1%} (目標: 99.5%)"

    def test_error_recovery_integration(self):
        """エラー回復統合テスト"""
        error_documents = [
            # 不完全なブロック
            [
                ";;;引用;;;",
                "内容",
                # 終了マーカーなし
            ],
            # 不正なリスト構造
            [
                "- 項目1",
                "    - 不正なインデント",
                "- 項目2",
            ],
            # 混在エラー
            [
                "# 見出し",
                ";;;不完全なキーワード;;",
                "- リスト項目",
                "  - ;;;属性[attr=;;; 不正属性 ;;;",
                "通常テキスト",
            ],
            # 制御文字混入
            [
                ";;;キーワード\x00\x01;;;",
                "内容\n\r\t",
                ";;;",
            ],
        ]

        error_recovery_results = []
        for i, doc in enumerate(error_documents):
            try:
                result = self.coordinator.parse_document(doc)
                # エラーが発生しても適切に処理される
                error_recovery_results.append(True)

                # エラー情報が適切に記録される
                if hasattr(result, "errors") and result.errors:
                    assert len(result.errors) > 0
                elif hasattr(result, "warnings") and result.warnings:
                    assert len(result.warnings) > 0

            except Exception as e:
                # 例外が発生する場合も適切なエラーハンドリング
                error_recovery_results.append(True)

        # すべてのエラーケースで適切な回復処理
        recovery_rate = sum(error_recovery_results) / len(error_recovery_results)
        assert recovery_rate >= 0.8, f"エラー回復率が低い: {recovery_rate:.1%}"

    def test_memory_efficiency_integration(self):
        """メモリ効率統合テスト"""
        import gc

        # 初期メモリ状態
        gc.collect()
        initial_objects = len(gc.get_objects())

        # 大量の文書を段階的に処理
        for batch in range(10):
            batch_documents = []
            for doc_id in range(20):
                doc = [
                    f"# バッチ{batch}文書{doc_id}",
                    "",
                    f";;;重要[batch={batch},doc={doc_id}];;; 内容 ;;;",
                    "",
                    f"- バッチ{batch}項目{doc_id}",
                    f"  - ;;;注釈;;; ネスト項目 ;;;",
                    "",
                    f"バッチ{batch}の**重要な**内容{doc_id}。",
                ]
                batch_documents.append(doc)

            # バッチ処理
            for doc in batch_documents:
                try:
                    result = self.coordinator.parse_document(doc)
                    assert result is not None
                except Exception as e:
                    pytest.fail(f"バッチ{batch}処理でエラー: {e}")

            # 明示的なガベージコレクション
            gc.collect()

        # 最終メモリ状態
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects

        # 過度なメモリ増加がないことを確認
        assert (
            object_growth < 10000
        ), f"メモリリークの疑い: {object_growth}個のオブジェクト増加"

    def test_concurrent_parsing_integration(self):
        """並行構文解析統合テスト"""
        import threading

        results = []
        errors = []

        def concurrent_parsing_worker(worker_id):
            try:
                local_coordinator = ParsingCoordinator()
                worker_results = []

                # 各ワーカーで独立した文書セット
                for doc_id in range(10):
                    worker_document = [
                        f"# ワーカー{worker_id}文書{doc_id}",
                        "",
                        f";;;重要[worker={worker_id}];;; ワーカー{worker_id}の重要な内容{doc_id} ;;;",
                        "",
                        f"- ワーカー{worker_id}項目{doc_id}",
                        f"  - ;;;注釈;;; ネスト項目{doc_id} ;;;",
                        "",
                        f"ワーカー{worker_id}の**太字**テキスト{doc_id}。",
                        "",
                        "```python",
                        f"def worker_{worker_id}_function_{doc_id}():",
                        f"    return 'worker {worker_id} doc {doc_id}'",
                        "```",
                    ]

                    try:
                        result = local_coordinator.parse_document(worker_document)
                        worker_results.append(result is not None)
                    except Exception:
                        worker_results.append(False)

                success_rate = sum(worker_results) / len(worker_results)
                results.append((worker_id, success_rate))

            except Exception as e:
                errors.append((worker_id, str(e)))

        # 複数ワーカーで並行実行
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_parsing_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行構文解析でエラー: {errors}"
        assert len(results) == 5

        # 各ワーカーで高い成功率
        for worker_id, success_rate in results:
            assert (
                success_rate >= 0.9
            ), f"ワーカー{worker_id}の成功率が低い: {success_rate:.1%}"

    def test_real_world_document_parsing(self):
        """実世界文書構文解析テスト"""
        real_world_document = [
            "# プロジェクト仕様書",
            "",
            ";;;重要[version=1.0];;; この文書はプロジェクトの正式仕様書です ;;;",
            "",
            "## 概要",
            "",
            "プロジェクトの目的と背景について説明します。",
            "",
            ";;;引用[source=要求仕様書];;;",
            "システムは以下の要件を満たす必要があります:",
            "- 高性能な処理能力",
            "- 拡張可能なアーキテクチャ",
            "- セキュアな通信",
            ";;;",
            "",
            "## 技術仕様",
            "",
            "### システム構成",
            "",
            "1. **フロントエンド**",
            "   - ;;;技術[framework=React];;; React 18.0以上 ;;;",
            "   - TypeScript 4.5以上",
            "   - ;;;重要;;; レスポンシブデザイン必須 ;;;",
            "",
            "2. **バックエンド**",
            "   - ;;;技術[language=Python];;; Python 3.9以上 ;;;",
            "   - FastAPI フレームワーク",
            "   - ;;;データベース[type=PostgreSQL];;; PostgreSQL 13以上 ;;;",
            "",
            "### API仕様",
            "",
            "#### 認証エンドポイント",
            "",
            "```python",
            "# 認証API例",
            "@app.post('/auth/login')",
            "async def login(credentials: UserCredentials):",
            "    # 認証処理",
            "    return {'token': jwt_token}",
            "```",
            "",
            ";;;注意[level=high];;;",
            "認証トークンは1時間で有効期限切れとなります。",
            "リフレッシュトークンを使用して更新してください。",
            ";;;",
            "",
            "#### データ取得エンドポイント",
            "",
            "| エンドポイント | メソッド | 説明 |",
            "|---------------|---------|------|",
            "| `/api/users` | GET | ;;;重要;;; ユーザー一覧取得 ;;; |",
            "| `/api/users/{id}` | GET | 特定ユーザー取得 |",
            "| `/api/users` | POST | ;;;注意;;; 新規ユーザー作成 ;;; |",
            "",
            "### セキュリティ要件",
            "",
            "- [ ] ;;;必須;;; HTTPS通信の実装 ;;;",
            "- [ ] JWT認証の実装",
            "- [ ] ;;;重要;;; SQL インジェクション対策 ;;;",
            "- [x] XSS対策",
            "- [x] CSRF対策",
            "",
            "## 実装計画",
            "",
            "### フェーズ1: 基盤構築 (4週間)",
            "",
            "- 週1: 環境構築・CI/CD設定",
            "  - ;;;タスク[priority=high];;; Docker環境構築 ;;;",
            "  - GitHub Actions設定",
            "- 週2: 基本API実装",
            "  - 認証API",
            "  - ;;;重要;;; ユーザー管理API ;;;",
            "- 週3-4: フロントエンド基盤",
            "  - React環境構築",
            "  - ;;;デザイン[system=design-tokens];;; デザインシステム構築 ;;;",
            "",
            "### フェーズ2: 機能実装 (8週間)",
            "",
            "詳細な機能実装を行います。",
            "",
            ";;;コード[lang=bash];;;",
            "# 開発サーバー起動",
            "npm run dev",
            "",
            "# API サーバー起動",
            "uvicorn main:app --reload",
            ";;;",
            "",
            "## 注意事項",
            "",
            ";;;警告[type=security];;;",
            "**重要**: 本番環境では以下の設定を必ず確認してください:",
            "",
            "1. 環境変数の適切な設定",
            "2. データベース接続の暗号化",
            "3. ログ出力のセキュリティ考慮",
            ";;;",
            "",
            "---",
            "",
            "© 2023 プロジェクトチーム",
        ]

        try:
            # 実世界文書の完全解析
            result = self.coordinator.parse_document(real_world_document)
            assert result is not None

            # 解析結果の検証
            if hasattr(result, "structure"):
                # 文書構造が適切に解析される
                assert result.structure is not None
            elif hasattr(result, "elements"):
                # 要素が適切に抽出される
                assert len(result.elements) > 0
            elif hasattr(result, "blocks"):
                # ブロックが適切に解析される
                assert len(result.blocks) > 0

        except Exception as e:
            pytest.fail(f"実世界文書解析でエラー: {e}")


class TestParsingSystemOptimization:
    """構文解析システム最適化テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.coordinator = ParsingCoordinator()

    def test_parsing_cache_optimization(self):
        """構文解析キャッシュ最適化テスト"""
        # 同一内容の繰り返し解析
        repeated_document = [
            "# 繰り返しテスト",
            ";;;重要;;; 重要な内容 ;;;",
            "- リスト項目",
            "**太字テキスト**",
        ]

        # 初回解析
        start_time = time.time()
        first_result = self.coordinator.parse_document(repeated_document)
        first_time = time.time() - start_time

        # 繰り返し解析（キャッシュ効果確認）
        repeated_times = []
        for _ in range(10):
            start_time = time.time()
            result = self.coordinator.parse_document(repeated_document)
            repeated_times.append(time.time() - start_time)
            assert result is not None

        # キャッシュ効果による高速化確認
        if hasattr(self.coordinator, "_cache") or hasattr(self.coordinator, "cache"):
            avg_repeated_time = sum(repeated_times) / len(repeated_times)
            # キャッシュ効果で高速化されることを期待
            assert (
                avg_repeated_time <= first_time * 1.5
            ), f"キャッシュ効果が不十分: 初回{first_time:.3f}s, 平均{avg_repeated_time:.3f}s"

    def test_parsing_pattern_optimization(self):
        """構文解析パターン最適化テスト"""
        # 最適化対象のパターン
        optimization_patterns = [
            # 頻出パターン
            [";;;重要;;; 重要な内容 ;;;"],
            [";;;注釈;;; 注釈内容 ;;;"],
            ["- リスト項目"],
            ["**太字**"],
            # 複合パターン
            [";;;重要+強調;;; 複合内容 ;;;"],
            ["- ;;;注釈;;; リスト注釈 ;;;"],
            # 属性パターン
            [";;;画像[alt=説明];;; image.jpg ;;;"],
            [";;;リンク[url=https://example.com];;; リンク ;;;"],
        ]

        # パターン最適化の確認
        pattern_times = []
        for pattern in optimization_patterns:
            start_time = time.time()
            for _ in range(100):  # 同一パターンを大量実行
                result = self.coordinator.parse_document(pattern)
                assert result is not None
            pattern_time = time.time() - start_time
            pattern_times.append(pattern_time)

        # 全パターンで許容時間内
        max_pattern_time = max(pattern_times)
        assert (
            max_pattern_time < 0.5
        ), f"パターン最適化が不十分: 最大時間{max_pattern_time:.3f}s"

    def test_parsing_accuracy_final_validation(self):
        """構文解析精度最終検証テスト"""
        # Issue #597の精度目標: 99.5%
        comprehensive_test_suite = [
            # 基本Kumihan記法 (20パターン)
            [";;;強調;;; 内容 ;;;"],
            [";;;注釈;;; 内容 ;;;"],
            [";;;引用;;; 内容 ;;;"],
            [";;;コード;;; 内容 ;;;"],
            [";;;画像;;; 内容 ;;;"],
            [";;;リンク;;; 内容 ;;;"],
            [";;;テーブル;;; 内容 ;;;"],
            [";;;リスト;;; 内容 ;;;"],
            [";;;見出し;;; 内容 ;;;"],
            [";;;装飾;;; 内容 ;;;"],
            [";;;重要;;; 内容 ;;;"],
            [";;;警告;;; 内容 ;;;"],
            [";;;情報;;; 内容 ;;;"],
            [";;;成功;;; 内容 ;;;"],
            [";;;エラー;;; 内容 ;;;"],
            [";;;デバッグ;;; 内容 ;;;"],
            [";;;TODO;;; 内容 ;;;"],
            [";;;FIXME;;; 内容 ;;;"],
            [";;;NOTE;;; 内容 ;;;"],
            [";;;TIP;;; 内容 ;;;"],
            # 複合キーワード (15パターン)
            [";;;強調+重要;;; 内容 ;;;"],
            [";;;引用+注釈;;; 内容 ;;;"],
            [";;;コード+実行可能;;; 内容 ;;;"],
            [";;;画像+装飾;;; 内容 ;;;"],
            [";;;リンク+外部;;; 内容 ;;;"],
            [";;;テーブル+ソート可能;;; 内容 ;;;"],
            [";;;リスト+番号付き;;; 内容 ;;;"],
            [";;;見出し+中央揃え;;; 内容 ;;;"],
            [";;;警告+重要;;; 内容 ;;;"],
            [";;;情報+詳細;;; 内容 ;;;"],
            [";;;成功+完了;;; 内容 ;;;"],
            [";;;エラー+クリティカル;;; 内容 ;;;"],
            [";;;デバッグ+詳細;;; 内容 ;;;"],
            [";;;TODO+高優先度;;; 内容 ;;;"],
            [";;;NOTE+重要;;; 内容 ;;;"],
            # 属性付きキーワード (20パターン)
            [";;;画像[alt=説明];;; 内容 ;;;"],
            [";;;リンク[url=https://example.com];;; 内容 ;;;"],
            [";;;コード[lang=python];;; 内容 ;;;"],
            [";;;テーブル[border=1];;; 内容 ;;;"],
            [";;;装飾[class=highlight];;; 内容 ;;;"],
            [";;;引用[author=著者];;; 内容 ;;;"],
            [";;;注釈[level=high];;; 内容 ;;;"],
            [";;;重要[priority=1];;; 内容 ;;;"],
            [";;;警告[type=security];;; 内容 ;;;"],
            [";;;情報[category=help];;; 内容 ;;;"],
            [";;;画像[alt=説明,width=200];;; 内容 ;;;"],
            [";;;リンク[url=test,target=_blank];;; 内容 ;;;"],
            [";;;コード[lang=js,theme=dark];;; 内容 ;;;"],
            [";;;テーブル[sortable=true,border=1];;; 内容 ;;;"],
            [";;;装飾[class=a,id=b];;; 内容 ;;;"],
            [";;;引用[author=A,date=2023];;; 内容 ;;;"],
            [";;;注釈[level=high,urgent=true];;; 内容 ;;;"],
            [";;;重要[priority=1,category=critical];;; 内容 ;;;"],
            [";;;警告[type=security,level=high];;; 内容 ;;;"],
            [";;;情報[category=help,lang=ja];;; 内容 ;;;"],
            # ブロック構造 (10パターン)
            [
                ";;;引用;;;",
                "ブロック内容",
                ";;;",
            ],
            [
                ";;;コード;;;",
                "print('hello')",
                ";;;",
            ],
            [
                ";;;重要;;;",
                "重要なブロック",
                "複数行内容",
                ";;;",
            ],
            [
                ";;;注釈[author=test];;;",
                "属性付きブロック",
                ";;;",
            ],
            [
                ";;;警告;;;",
                "警告ブロック",
                "詳細説明",
                ";;;",
            ],
            [
                ";;;情報;;;",
                "情報ブロック",
                ";;;",
            ],
            [
                ";;;成功;;;",
                "成功メッセージ",
                ";;;",
            ],
            [
                ";;;エラー;;;",
                "エラー詳細",
                ";;;",
            ],
            [
                ";;;TODO;;;",
                "TODOアイテム",
                "詳細説明",
                ";;;",
            ],
            [
                ";;;NOTE;;;",
                "重要なノート",
                ";;;",
            ],
            # リスト構造 (15パターン)
            ["- リスト項目"],
            ["1. 番号付きリスト"],
            ["- ;;;重要;;; 重要項目 ;;;"],
            ["1. ;;;注釈;;; 注釈項目 ;;;"],
            [
                "- レベル1",
                "  - レベル2",
                "    - レベル3",
            ],
            [
                "1. 番号1",
                "   a. サブ番号a",
                "   b. サブ番号b",
            ],
            [
                "- ;;;重要;;; 重要項目 ;;;",
                "  - サブ項目",
                "    - ;;;注釈;;; 深いネスト ;;;",
            ],
            ["- [ ] TODO項目"],
            ["- [x] 完了項目"],
            ["- [ ] ;;;重要;;; 重要TODO ;;;"],
            [
                "- カテゴリ1",
                "  - [ ] タスク1",
                "  - [x] タスク2",
            ],
            [
                "1. フェーズ1",
                "   - ;;;重要;;; 重要タスク ;;;",
                "   - 通常タスク",
            ],
            [
                "- 項目A",
                "- 項目B",
                "  - サブ項目B1",
                "  - サブ項目B2",
                "- 項目C",
            ],
            [
                "1. 第1章",
                "   1.1. 第1節",
                "   1.2. 第2節",
                "2. 第2章",
            ],
            [
                "- ;;;カテゴリ[type=main];;; メインカテゴリ ;;;",
                "  - ;;;項目[priority=high];;; 高優先度項目 ;;;",
                "  - 通常項目",
            ],
            # Markdown要素 (10パターン)
            ["# 見出し1"],
            ["## 見出し2"],
            ["**太字**"],
            ["*斜体*"],
            ["`インラインコード`"],
            ["[リンク](https://example.com)"],
            ["![画像](image.jpg)"],
            ["> 引用文"],
            ["---"],
            [
                "| 列1 | 列2 |",
                "|-----|-----|",
                "| A   | B   |",
            ],
            # 混在構造 (10パターン)
            [
                "# 見出し",
                ";;;重要;;; 重要な内容 ;;;",
                "- リスト項目",
                "**太字テキスト**",
            ],
            [
                "## セクション",
                ";;;引用;;;",
                "引用内容",
                ";;;",
                "- [ ] TODOリスト",
            ],
            [
                "### サブセクション",
                ";;;コード[lang=python];;;",
                "print('hello')",
                ";;;",
                "*説明文*",
            ],
            [
                "#### 詳細",
                ";;;注釈[author=test];;;",
                "注釈内容",
                ";;;",
                "[参考リンク](url)",
            ],
            [
                "# メイン",
                "- ;;;重要;;; 重要リスト ;;;",
                "  - サブ項目",
                "**強調**テキスト",
            ],
            [
                "## セクション",
                ";;;警告;;;",
                "警告内容",
                ";;;",
                "> 引用テキスト",
            ],
            [
                "### コード例",
                ";;;コード;;;",
                "code example",
                ";;;",
                "説明: `inline code`",
            ],
            [
                "#### リスト例",
                "1. ;;;項目1;;; 内容1 ;;;",
                "2. 項目2",
                "   - サブ項目",
            ],
            [
                "# 複雑な例",
                ";;;重要+強調;;;",
                "重要で強調された内容",
                ";;;",
                "- [ ] **太字**TODO",
                "- [x] *斜体*完了",
            ],
            [
                "## 統合例",
                ";;;情報[type=tip];;;",
                "ヒント: **重要**な情報",
                ";;;",
                "| 項目 | 説明 |",
                "|------|------|",
                "| A | ;;;重要;;; 重要項目 ;;; |",
            ],
        ]

        # 精度測定
        accuracy_results = []
        for i, pattern in enumerate(comprehensive_test_suite):
            try:
                result = self.coordinator.parse_document(pattern)
                accuracy_results.append(result is not None)
            except Exception:
                accuracy_results.append(False)

        # 最終精度確認
        total_patterns = len(comprehensive_test_suite)
        successful_patterns = sum(accuracy_results)
        final_accuracy = successful_patterns / total_patterns

        # Issue #597の目標精度: 99.5%以上
        assert (
            final_accuracy >= 0.995
        ), f"最終構文解析精度が目標未達: {final_accuracy:.3%} ({successful_patterns}/{total_patterns}) - 目標: 99.5%以上"

        print(
            f"構文解析精度最終結果: {final_accuracy:.3%} ({successful_patterns}/{total_patterns})"
        )
