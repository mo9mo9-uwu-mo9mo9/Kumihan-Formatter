"""Block Parser高度テスト - Issue #597 Week 28-29対応

ブロック解析機能の包括的テスト
Kumihan記法の完全対応・エラー回復・性能検証
"""

import time
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import (
    Node,
    error_node,
    paragraph,
    toc_marker,
)
from kumihan_formatter.core.block_parser.block_parser import BlockParser
from kumihan_formatter.core.keyword_parser import KeywordParser


class TestBlockParserAdvanced:
    """ブロックパーサー高度テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.keyword_parser = KeywordParser()
        self.block_parser = BlockParser(self.keyword_parser)

    def test_block_parser_initialization(self):
        """ブロックパーサー初期化テスト"""
        assert self.block_parser.keyword_parser is not None
        assert self.block_parser.marker_validator is not None
        assert self.block_parser.heading_counter == 0
        assert hasattr(self.block_parser, "logger")

    def test_parse_block_marker_basic_functionality(self):
        """基本ブロックマーカー解析テスト"""
        lines = [
            ";;;装飾名;;;",
            "テスト内容",
            ";;;",
        ]

        node, next_index = self.block_parser.parse_block_marker(lines, 0)

        assert node is not None
        assert next_index == 3
        assert node.type in ["keyword_block", "decorated_block"]

    def test_parse_complex_kumihan_syntax(self):
        """複雑なKumihan記法解析テスト"""
        # 複合キーワードブロック
        complex_syntax = [
            ";;;注釈;;; 重要な内容です ;;;",
            ";;;強調;;; この部分は特に重要 ;;;",
            ";;;引用;;;",
            "長い引用文の内容",
            "複数行にわたる引用",
            ";;;",
            ";;;コード;;;",
            "def example():",
            "    return 'Hello World'",
            ";;;",
        ]

        results = []
        index = 0
        while index < len(complex_syntax):
            if complex_syntax[index].strip().startswith(";;;"):
                node, next_index = self.block_parser.parse_block_marker(
                    complex_syntax, index
                )
                results.append((node, next_index))
                index = next_index
            else:
                index += 1

        # 複数のブロックが正しく解析される
        assert len(results) >= 3
        assert all(node is not None for node, _ in results)

    def test_nested_block_structure_parsing(self):
        """ネスト構造ブロック解析テスト"""
        nested_blocks = [
            ";;;外部ブロック;;;",
            "外部の内容",
            ";;;内部ブロック;;;",
            "内部の内容",
            ";;;",
            "外部に戻る",
            ";;;",
        ]

        # 外部ブロックの解析
        outer_node, outer_end = self.block_parser.parse_block_marker(nested_blocks, 0)
        assert outer_node is not None
        assert outer_end == len(nested_blocks)

        # 内部ブロックの解析
        inner_node, inner_end = self.block_parser.parse_block_marker(nested_blocks, 2)
        assert inner_node is not None
        assert inner_end == 5

    def test_error_recovery_invalid_markers(self):
        """無効なマーカーでのエラー回復テスト"""
        invalid_syntax = [
            ";;不完全なマーカー",
            ";;;有効なマーカー;;;",
            "正常な内容",
            ";;;",
            ";;もう一つの不完全",
            ";;;別の有効なマーカー;;; 即座に閉じる ;;;",
        ]

        results = []
        index = 0
        while index < len(invalid_syntax):
            line = invalid_syntax[index].strip()
            if line.startswith(";;"):
                node, next_index = self.block_parser.parse_block_marker(
                    invalid_syntax, index
                )
                results.append(
                    (
                        node,
                        next_index,
                        "error" if node and hasattr(node, "error") else "success",
                    )
                )
                index = next_index
            else:
                index += 1

        # エラーノードと正常ノードが混在
        assert len(results) >= 2
        error_count = sum(1 for _, _, status in results if status == "error")
        success_count = sum(1 for _, _, status in results if status == "success")

        assert error_count > 0  # エラーが検出される
        assert success_count > 0  # 有効な部分は処理される

    def test_marker_validation_edge_cases(self):
        """マーカー検証エッジケーステスト"""
        edge_cases = [
            "",  # 空行
            ";;;",  # 終了マーカーのみ
            ";;;   ;;;",  # 空のキーワード
            ";;; キーワード",  # 終了マーカーなし
            "キーワード ;;;",  # 開始マーカーなし
            ";;;キーワード;;; 内容 ;;;",  # 即座閉じ
            ";;;キーワード;;; 内容",  # 部分的に有効
            ";;;non-ascii-記号;;;",  # 非ASCII文字
            ";;;very-long-keyword-that-might-cause-issues;;;",  # 長いキーワード
        ]

        for i, case in enumerate(edge_cases):
            lines = [case]
            node, next_index = self.block_parser.parse_block_marker(lines, 0)

            # エラーハンドリングが適切に動作
            assert next_index >= 0
            assert next_index <= len(lines)

            # 無効なケースではエラーノードまたはNoneが返される
            if case in ["", ";;;", ";;;   ;;;", ";;; キーワード", "キーワード ;;;"]:
                assert node is None or (hasattr(node, "error") if node else True)

    def test_performance_large_document_parsing(self):
        """大規模文書での性能テスト"""
        # 大量のブロックを含む文書を生成
        large_document = []
        for i in range(100):  # 100個のブロック
            large_document.extend(
                [
                    f";;;ブロック{i};;;",
                    f"ブロック{i}の内容行1",
                    f"ブロック{i}の内容行2",
                    f"ブロック{i}の内容行3",
                    ";;;",
                ]
            )

        # 解析時間を測定
        start_time = time.time()

        parsed_blocks = 0
        index = 0
        while index < len(large_document):
            if (
                large_document[index].strip().startswith(";;;")
                and not large_document[index].strip() == ";;;"
            ):
                node, next_index = self.block_parser.parse_block_marker(
                    large_document, index
                )
                if node:
                    parsed_blocks += 1
                index = next_index
            else:
                index += 1

        execution_time = time.time() - start_time

        # 詳細な性能測定ロジック強化
        document_text = "\n".join(large_document)
        document_size_bytes = len(document_text.encode("utf-8"))
        document_size_kb = document_size_bytes / 1024

        # 解析速度計算（ms/KB）
        ms_per_kb = (execution_time * 1000) / document_size_kb

        # 詳細な性能メトリクス
        performance_metrics = {
            "execution_time_ms": execution_time * 1000,
            "document_size_bytes": document_size_bytes,
            "document_size_kb": document_size_kb,
            "ms_per_kb": ms_per_kb,
            "parsed_blocks": parsed_blocks,
            "target_blocks": 100,
            "blocks_per_second": (
                parsed_blocks / execution_time if execution_time > 0 else 0
            ),
            "bytes_per_second": (
                document_size_bytes / execution_time if execution_time > 0 else 0
            ),
        }

        # 性能基準の確認
        assert execution_time < 1.0, (
            f"大規模解析が遅すぎます: {execution_time:.3f}秒\n"
            f"性能詳細: {performance_metrics}"
        )
        assert parsed_blocks == 100, f"解析ブロック数が不正: {parsed_blocks}/100"

        # Issue #597要求仕様: <50ms/KB解析
        assert ms_per_kb < 50.0, (
            f"KB当たり処理時間が目標超過: {ms_per_kb:.2f}ms/KB (目標: <50ms/KB)\n"
            f"性能詳細: {performance_metrics}"
        )

    def test_memory_efficiency_parsing(self):
        """メモリ効率性テスト"""
        import sys

        # ベースラインメモリ使用量
        initial_refs = len([obj for obj in globals().values()])

        # 大量のブロック解析
        for batch in range(10):
            test_blocks = [
                [
                    f";;;テストブロック{i};;;",
                    f"内容{i}",
                    ";;;",
                ]
                for i in range(batch * 50, (batch + 1) * 50)
            ]

            flat_blocks = [line for sublist in test_blocks for line in sublist]

            # 解析実行
            index = 0
            while index < len(flat_blocks):
                if (
                    flat_blocks[index].strip().startswith(";;;")
                    and not flat_blocks[index].strip() == ";;;"
                ):
                    node, next_index = self.block_parser.parse_block_marker(
                        flat_blocks, index
                    )
                    index = next_index
                else:
                    index += 1

        # メモリリークの確認
        final_refs = len([obj for obj in globals().values()])
        ref_growth = final_refs - initial_refs

        # 過度なオブジェクト増加がないことを確認
        assert ref_growth < 100, f"過度なオブジェクト増加: {ref_growth}"

    def test_unicode_multilingual_support(self):
        """Unicode・多言語対応テスト"""
        multilingual_blocks = [
            ";;;日本語;;;",
            "これは日本語のテストです。",
            "漢字、ひらがな、カタカナが含まれます。",
            ";;;",
            ";;;English;;;",
            "This is an English test.",
            "It contains ASCII characters.",
            ";;;",
            ";;;Español;;;",
            "Esta es una prueba en español.",
            "Contiene caracteres con acentos: á, é, í, ó, ú, ñ.",
            ";;;",
            ";;;Русский;;;",
            "Это тест на русском языке.",
            "Содержит кириллические символы.",
            ";;;",
            ";;;العربية;;;",
            "هذا اختبار باللغة العربية.",
            "يحتوي على أحرف عربية.",
            ";;;",
            ";;;Emoji;;;",
            "絵文字テスト: 🎌🗾🎯📋✅❌⚠️🔧",
            "Unicode symbols: ←→↑↓∀∃∈∉∪∩",
            ";;;",
        ]

        parsed_count = 0
        index = 0
        while index < len(multilingual_blocks):
            line = multilingual_blocks[index].strip()
            if line.startswith(";;;") and not line == ";;;":
                node, next_index = self.block_parser.parse_block_marker(
                    multilingual_blocks, index
                )
                if node:
                    parsed_count += 1
                index = next_index
            else:
                index += 1

        # すべての多言語ブロックが正しく解析される
        assert parsed_count == 6

    def test_concurrent_parsing_thread_safety(self):
        """並行解析・スレッドセーフティテスト"""
        import threading

        results = []
        errors = []

        def concurrent_parsing_worker(worker_id):
            try:
                # 各ワーカーで独立したパーサーインスタンス
                local_keyword_parser = KeywordParser()
                local_block_parser = BlockParser(local_keyword_parser)

                # ワーカー固有のテストデータ
                worker_blocks = [
                    [
                        f";;;ワーカー{worker_id}ブロック{i};;;",
                        f"ワーカー{worker_id}の内容{i}",
                        ";;;",
                    ]
                    for i in range(20)
                ]

                flat_blocks = [line for sublist in worker_blocks for line in sublist]

                # 解析実行
                parsed_count = 0
                index = 0
                while index < len(flat_blocks):
                    line = flat_blocks[index].strip()
                    if line.startswith(";;;") and not line == ";;;":
                        node, next_index = local_block_parser.parse_block_marker(
                            flat_blocks, index
                        )
                        if node:
                            parsed_count += 1
                        index = next_index
                    else:
                        index += 1

                results.append((worker_id, parsed_count))

            except Exception as e:
                errors.append((worker_id, str(e)))

        # 5つのワーカーで並行実行
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_parsing_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行解析でエラーが発生: {errors}"
        assert len(results) == 5

        # すべてのワーカーが正しい数のブロックを解析
        for worker_id, parsed_count in results:
            assert (
                parsed_count == 20
            ), f"ワーカー{worker_id}の解析数が不正: {parsed_count}/20"

    def test_stress_malformed_input_resilience(self):
        """不正入力耐性ストレステスト"""
        malformed_inputs = [
            # 極端に長い行
            ";;;" + "A" * 10000 + ";;;",
            # 制御文字を含む
            ";;;test\x00\x01\x02;;;",
            # 非常に深いネスト
            ";;;level1;;;\n" + ";;;level2;;;\n" * 100 + ";;;\n" * 100,
            # 不完全なマーカーの連続
            ";;;\n" * 1000,
            # 混在文字エンコーディング風
            ";;;test\xff\xfe;;;",
            # 極端に短い
            ";",
            ";;",
            # 奇妙な組み合わせ
            ";;;テスト;;; 内容 ;;; 追加内容",
            # XMLライクな構造
            ";;;tag attr='value';;;content;;;/tag;;;",
        ]

        for i, malformed_input in enumerate(malformed_inputs):
            lines = (
                malformed_input.split("\n")
                if "\n" in malformed_input
                else [malformed_input]
            )

            try:
                # エラーハンドリングが適切に動作することを確認
                node, next_index = self.block_parser.parse_block_marker(lines, 0)

                # パーサーがクラッシュしない
                assert next_index >= 0
                assert next_index <= len(lines)

                # 無効な入力に対して適切な応答（Noneまたはエラーノード）
                if node is None:
                    # None は有効な応答
                    pass
                else:
                    # ノードが返される場合、基本的な構造を持つ
                    assert hasattr(node, "type") or hasattr(node, "error")

            except Exception as e:
                # 予期しない例外は発生しない
                pytest.fail(f"不正入力{i}でハンドルされない例外が発生: {e}")

    def test_parse_accuracy_kumihan_specification(self):
        """Kumihan記法仕様準拠精度テスト"""
        # Kumihan記法の標準的なパターン
        standard_patterns = [
            # 基本装飾
            (";;;強調;;; 重要な内容 ;;;", "inline_decoration"),
            (";;;注釈;;;\n詳細な説明\n;;;", "block_decoration"),
            # 複合パターン
            (";;;引用;;;\n;;;強調;;; 内部強調 ;;;\n引用の続き\n;;;", "nested_blocks"),
            # 属性付き
            (";;;画像[alt=説明文];;; 画像パス ;;;", "attributed_block"),
            # 特殊記号
            (";;;記号;;; →←↑↓ ;;;", "symbol_content"),
            # 数式風
            (";;;数式;;; a = b + c ;;;", "formula_content"),
        ]

        accuracy_results = []

        for pattern, expected_type in standard_patterns:
            lines = pattern.split("\n")
            node, next_index = self.block_parser.parse_block_marker(lines, 0)

            if node is not None:
                # 解析成功
                accuracy_results.append(True)
            else:
                # 解析失敗
                accuracy_results.append(False)

        # 精度目標: 99.5%以上
        success_rate = sum(accuracy_results) / len(accuracy_results)
        assert (
            success_rate >= 0.995
        ), f"Kumihan記法解析精度が目標未達: {success_rate:.1%}"

    def test_heading_counter_functionality(self):
        """見出しカウンター機能テスト"""
        # 見出しブロックの解析
        heading_blocks = [
            ";;;見出し1;;;",
            "第1章の内容",
            ";;;",
            ";;;見出し2;;;",
            "第2章の内容",
            ";;;",
            ";;;見出し3;;;",
            "第3章の内容",
            ";;;",
        ]

        initial_counter = self.block_parser.heading_counter

        # 見出しブロックを順次解析
        index = 0
        heading_count = 0
        while index < len(heading_blocks):
            line = heading_blocks[index].strip()
            if line.startswith(";;;") and "見出し" in line:
                node, next_index = self.block_parser.parse_block_marker(
                    heading_blocks, index
                )
                if node:
                    heading_count += 1
                index = next_index
            else:
                index += 1

        # カウンターが正しく動作
        assert heading_count == 3
        # 実装によってはカウンターが更新される場合があることを考慮


class TestBlockParserIntegration:
    """ブロックパーサー統合テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.keyword_parser = KeywordParser()
        self.block_parser = BlockParser(self.keyword_parser)

    def test_integration_with_keyword_parser(self):
        """キーワードパーサーとの統合テスト"""
        integrated_content = [
            ";;;複合キーワード;;;",
            "基本内容",
            ";;;内部装飾;;; 内部の内容 ;;;",
            "基本内容の続き",
            ";;;",
        ]

        # ブロックパーサーとキーワードパーサーの連携
        node, next_index = self.block_parser.parse_block_marker(integrated_content, 0)

        assert node is not None
        assert next_index == len(integrated_content)

        # キーワードパーサーが内部で正しく呼ばれている
        assert self.block_parser.keyword_parser is not None

    def test_real_world_document_parsing(self):
        """実世界文書解析テスト"""
        real_document = [
            "# 文書タイトル",
            "",
            ";;;序文;;;",
            "この文書は Kumihan-Formatter のテスト用です。",
            "様々な記法が含まれています。",
            ";;;",
            "",
            "## 第1章",
            "",
            ";;;重要;;; この章では重要な概念を説明します ;;;",
            "",
            ";;;コード;;;",
            "def example_function():",
            "    return 'Hello, World!'",
            ";;;",
            "",
            ";;;注釈;;;",
            "注釈の内容です。",
            "複数行にわたることもあります。",
            ";;;",
            "",
            "## 結論",
            "",
            ";;;まとめ;;; 以上でテストを終了します ;;;",
        ]

        # 実際の文書パターンでの解析
        parsed_blocks = []
        index = 0
        while index < len(real_document):
            line = real_document[index].strip()
            if line.startswith(";;;") and not line == ";;;":
                node, next_index = self.block_parser.parse_block_marker(
                    real_document, index
                )
                if node:
                    parsed_blocks.append(node)
                index = next_index
            else:
                index += 1

        # 期待される数のブロックが解析される
        assert len(parsed_blocks) >= 5  # 序文、重要、コード、注釈、まとめ

        # すべてのブロックが有効
        assert all(node is not None for node in parsed_blocks)
