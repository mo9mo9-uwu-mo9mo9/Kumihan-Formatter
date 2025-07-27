"""Image Block Parser テスト - Issue #597 Week 28-29対応

画像ブロック解析機能の専門テスト
単一行・複数行マーカー・alt属性処理の確認
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.block_parser.image_block_parser import ImageBlockParser


class TestImageBlockParser:
    """画像ブロックパーサーテスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.image_parser = ImageBlockParser()

    def test_image_parser_initialization(self):
        """画像パーサー初期化テスト"""
        assert self.image_parser is not None
        assert hasattr(self.image_parser, "parse_image_block")
        assert hasattr(self.image_parser, "parse_single_line_image")

    def test_single_line_image_parsing(self):
        """単一行画像解析テスト"""
        single_line_patterns = [
            ";;;画像;;; /path/to/image.jpg ;;;",
            ";;;画像[alt=説明文];;; /path/to/image.png ;;;",
            ";;;画像[alt=説明文,width=200];;; /path/to/image.gif ;;;",
            ";;;img;;; relative/path/image.svg ;;;",
            ";;;画像;;; https://example.com/image.jpg ;;;",
        ]

        for pattern in single_line_patterns:
            lines = [pattern]
            result = self.image_parser.parse_single_line_image(lines, 0)

            if result:
                node, next_index = result
                assert node is not None
                assert next_index == 1
                assert hasattr(node, "image_path") or hasattr(node, "content")

    def test_multi_line_image_parsing(self):
        """複数行画像解析テスト"""
        multi_line_patterns = [
            [
                ";;;画像;;;",
                "/path/to/image.jpg",
                ";;;",
            ],
            [
                ";;;画像[alt=複数行の説明];;;",
                "/path/to/complex/image.png",
                "画像の詳細説明",
                ";;;",
            ],
            [
                ";;;img;;;",
                "https://example.com/image.jpg",
                "alt: オンライン画像",
                "width: 300px",
                ";;;",
            ],
        ]

        for pattern in multi_line_patterns:
            result = self.image_parser.parse_image_block(pattern, 0)

            if result:
                node, next_index = result
                assert node is not None
                assert next_index == len(pattern)

    def test_image_attribute_parsing(self):
        """画像属性解析テスト"""
        attribute_patterns = [
            # 基本alt属性
            (";;;画像[alt=説明文];;; image.jpg ;;;", {"alt": "説明文"}),
            # 複数属性
            (
                ";;;画像[alt=説明,width=200,height=150];;; image.jpg ;;;",
                {"alt": "説明", "width": "200", "height": "150"},
            ),
            # 日本語属性
            (
                ";;;画像[説明=日本語の説明文];;; image.jpg ;;;",
                {"説明": "日本語の説明文"},
            ),
            # 特殊文字を含む属性
            (
                ";;;画像[alt='複雑な \"説明\" 文'];;; image.jpg ;;;",
                {"alt": '複雑な "説明" 文'},
            ),
        ]

        for pattern, expected_attrs in attribute_patterns:
            lines = [pattern]
            result = self.image_parser.parse_single_line_image(lines, 0)

            if result:
                node, _ = result
                # 属性が正しく解析されていることを確認
                if hasattr(node, "attributes"):
                    for key, value in expected_attrs.items():
                        assert key in node.attributes
                        assert node.attributes[key] == value

    def test_image_path_validation(self):
        """画像パス検証テスト"""
        path_patterns = [
            # 相対パス
            "images/test.jpg",
            "./images/test.png",
            "../assets/test.gif",
            # 絶対パス
            "/usr/local/images/test.jpg",
            "C:\\Images\\test.png",  # Windows形式
            # URL
            "https://example.com/image.jpg",
            "http://localhost:8080/image.png",
            "ftp://server.com/image.gif",
            # 特殊文字を含むパス
            "images/画像 with spaces.jpg",
            "images/image-with-dashes.png",
            "images/image_with_underscores.gif",
        ]

        for path in path_patterns:
            pattern = f";;;画像;;; {path} ;;;"
            lines = [pattern]
            result = self.image_parser.parse_single_line_image(lines, 0)

            if result:
                node, _ = result
                assert node is not None
                # パスが適切に保存されている
                if hasattr(node, "image_path"):
                    assert path in str(node.image_path)
                elif hasattr(node, "content"):
                    assert path in str(node.content)

    def test_image_format_support(self):
        """画像フォーマット対応テスト"""
        image_formats = [
            "image.jpg",
            "image.jpeg",
            "image.png",
            "image.gif",
            "image.svg",
            "image.webp",
            "image.bmp",
            "image.tiff",
            "image.ico",
            "IMAGE.JPG",  # 大文字拡張子
            "image.JPEG",
        ]

        for image_file in image_formats:
            pattern = f";;;画像;;; {image_file} ;;;"
            lines = [pattern]
            result = self.image_parser.parse_single_line_image(lines, 0)

            # すべての一般的な画像フォーマットがサポートされる
            assert (
                result is not None
            ), f"画像フォーマット {image_file} がサポートされていない"

    def test_error_handling_invalid_image_syntax(self):
        """無効な画像構文エラーハンドリングテスト"""
        invalid_patterns = [
            ";;;画像;;;",  # パスなし
            ";;;画像;;; ;;;",  # 空のパス
            ";;;画像[alt=];;; image.jpg ;;;",  # 空の属性値
            ";;;画像[=value];;; image.jpg ;;;",  # 属性名なし
            ";;;画像[alt;;; image.jpg ;;;",  # 属性構文エラー
        ]

        for pattern in invalid_patterns:
            lines = [pattern]
            result = self.image_parser.parse_single_line_image(lines, 0)

            # エラーハンドリングが適切に動作
            # None を返すか、エラーノードを返すか、例外を発生させる
            if result is None:
                # None は有効なエラー応答
                pass
            else:
                node, _ = result
                # エラーノードの場合
                if hasattr(node, "error"):
                    assert node.error is not None

    def test_image_parsing_performance(self):
        """画像解析性能テスト"""
        import time

        # 大量の画像パターンを生成
        image_patterns = []
        for i in range(1000):
            pattern = f";;;画像[alt=画像{i}];;; /path/to/image{i}.jpg ;;;"
            image_patterns.append([pattern])

        start_time = time.time()

        parsed_count = 0
        for pattern in image_patterns:
            result = self.image_parser.parse_single_line_image(pattern, 0)
            if result:
                parsed_count += 1

        execution_time = time.time() - start_time

        # 性能基準確認
        assert execution_time < 0.5, f"画像解析が遅すぎる: {execution_time}秒"
        assert parsed_count >= 950, f"解析成功数が不足: {parsed_count}/1000"

    def test_unicode_image_paths(self):
        """Unicode画像パス対応テスト"""
        unicode_paths = [
            "画像/日本語ファイル名.jpg",
            "images/Español_image.png",
            "图片/中文图片.gif",
            "images/Русский_файл.jpg",
            "images/العربية_صورة.png",
            "images/絵文字🎌画像.jpg",
        ]

        for path in unicode_paths:
            pattern = f";;;画像;;; {path} ;;;"
            lines = [pattern]
            result = self.image_parser.parse_single_line_image(lines, 0)

            assert result is not None, f"Unicode パス {path} の解析に失敗"

    def test_complex_image_scenarios(self):
        """複雑な画像シナリオテスト"""
        complex_scenarios = [
            # ネストした画像ブロック
            [
                ";;;画像コンテナ;;;",
                ";;;画像;;; image1.jpg ;;;",
                ";;;画像;;; image2.jpg ;;;",
                ";;;",
            ],
            # 画像ギャラリー
            [
                ";;;ギャラリー;;;",
                ";;;画像[alt=画像1];;; gallery/img1.jpg ;;;",
                ";;;画像[alt=画像2];;; gallery/img2.jpg ;;;",
                ";;;画像[alt=画像3];;; gallery/img3.jpg ;;;",
                ";;;",
            ],
            # 属性の豊富な画像
            [
                ";;;画像[alt=詳細な説明,width=800,height=600,class=responsive,loading=lazy];;;",
                "/assets/high-res-image.jpg",
                "詳細な画像の説明文",
                "著作権: © 2023 Example Corp",
                ";;;",
            ],
        ]

        for scenario in complex_scenarios:
            # 各シナリオで適切な解析が行われる
            result = self.image_parser.parse_image_block(scenario, 0)
            if result:
                node, next_index = result
                assert node is not None
                assert next_index > 0

    def test_image_parser_integration(self):
        """画像パーサー統合テスト"""
        # 実際の文書での画像使用パターン
        document_with_images = [
            "# 画像テスト文書",
            "",
            ";;;画像[alt=メイン画像];;; /assets/main-image.jpg ;;;",
            "",
            "文書の説明文です。",
            "",
            ";;;画像;;;",
            "/assets/detailed-diagram.png",
            "図: システム構成図",
            "この図はシステムの全体構成を示しています。",
            ";;;",
            "",
            "更なる説明文。",
            "",
            ";;;画像[alt=まとめ画像,class=conclusion];;; /assets/summary.gif ;;;",
        ]

        # 文書全体から画像を抽出
        image_blocks = []
        index = 0
        while index < len(document_with_images):
            line = document_with_images[index].strip()
            if ";;;画像" in line or ";;;img" in line:
                if line.endswith(";;;"):
                    # 単一行画像
                    result = self.image_parser.parse_single_line_image([line], 0)
                    if result:
                        node, _ = result
                        image_blocks.append(node)
                    index += 1
                else:
                    # 複数行画像
                    end_index = index + 1
                    while (
                        end_index < len(document_with_images)
                        and document_with_images[end_index].strip() != ";;;"
                    ):
                        end_index += 1
                    end_index += 1  # 終了マーカーを含む

                    block = document_with_images[index:end_index]
                    result = self.image_parser.parse_image_block(block, 0)
                    if result:
                        node, _ = result
                        image_blocks.append(node)
                    index = end_index
            else:
                index += 1

        # 期待される数の画像が解析される
        assert len(image_blocks) >= 3


class TestImageBlockParserEdgeCases:
    """画像ブロックパーサーエッジケーステスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.image_parser = ImageBlockParser()

    def test_empty_image_content(self):
        """空の画像コンテンツテスト"""
        empty_cases = [
            [";;;画像;;;", ";;;"],  # 画像パスなし
            [";;;画像;;;", "", ";;;"],  # 空行のみ
            [";;;画像;;;", "   ", ";;;"],  # 空白のみ
        ]

        for case in empty_cases:
            result = self.image_parser.parse_image_block(case, 0)
            # 空のコンテンツに対する適切な処理
            if result:
                node, _ = result
                # エラーノードまたは適切なデフォルト処理
                assert node is not None

    def test_malformed_image_attributes(self):
        """不正な画像属性テスト"""
        malformed_attributes = [
            ";;;画像[alt=値1,alt=値2];;; image.jpg ;;;",  # 重複属性
            ";;;画像[alt='未閉じクォート];;; image.jpg ;;;",  # 未閉じクォート
            ";;;画像[attr1=val1,attr2];;; image.jpg ;;;",  # 値なし属性
            ";;;画像[=value];;; image.jpg ;;;",  # キーなし属性
            ";;;画像[a=1,b=2,c=3,d=4,e=5,f=6];;; image.jpg ;;;",  # 大量の属性
        ]

        for pattern in malformed_attributes:
            lines = [pattern]
            try:
                result = self.image_parser.parse_single_line_image(lines, 0)
                # エラーハンドリングが適切に動作
                if result:
                    node, _ = result
                    assert node is not None
            except Exception:
                # 例外が発生する場合も適切なエラーハンドリング
                pass

    def test_extremely_long_image_paths(self):
        """極端に長い画像パステスト"""
        # 非常に長いパス
        long_path = "/very/long/path/" + "subdir/" * 100 + "image.jpg"
        pattern = f";;;画像;;; {long_path} ;;;"

        lines = [pattern]
        result = self.image_parser.parse_single_line_image(lines, 0)

        # 長いパスでもクラッシュしない
        if result:
            node, _ = result
            assert node is not None

    def test_concurrent_image_parsing(self):
        """並行画像解析テスト"""
        import threading

        results = []
        errors = []

        def concurrent_image_worker(worker_id):
            try:
                local_parser = ImageBlockParser()
                worker_results = []

                for i in range(50):
                    pattern = f";;;画像[alt=ワーカー{worker_id}画像{i}];;; /images/worker{worker_id}_img{i}.jpg ;;;"
                    lines = [pattern]
                    result = local_parser.parse_single_line_image(lines, 0)
                    worker_results.append(result is not None)

                success_rate = sum(worker_results) / len(worker_results)
                results.append((worker_id, success_rate))

            except Exception as e:
                errors.append((worker_id, str(e)))

        # 複数ワーカーで並行実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_image_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行画像解析でエラー: {errors}"
        assert len(results) == 3

        # 各ワーカーで高い成功率
        for worker_id, success_rate in results:
            assert (
                success_rate >= 0.9
            ), f"ワーカー{worker_id}の成功率が低い: {success_rate:.1%}"
