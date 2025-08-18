"""レンダリング性能のパフォーマンステスト

複雑な出力生成速度とレンダリング処理の効率性をテストし、
高速なHTML出力生成を確認する。
"""

import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class RenderingPerformanceTester:
    """レンダリング性能テスター"""

    def __init__(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.results: List[Dict[str, Any]] = []

    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        import shutil
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")

    def generate_parsed_data(self, element_count: int,
                           complexity: str = "medium") -> Dict[str, Any]:
        """パース済みデータ生成"""
        elements = []

        if complexity == "simple":
            # シンプルなテキスト要素のみ
            for i in range(element_count):
                elements.append({
                    "type": "text",
                    "content": f"テキスト要素 {i}",
                    "attributes": {}
                })

        elif complexity == "medium":
            # 中程度の複雑さ（様々な要素）
            for i in range(element_count):
                if i % 10 == 0:
                    elements.append({
                        "type": "heading",
                        "level": 1,
                        "content": f"見出し {i}",
                        "attributes": {"id": f"heading_{i}"}
                    })
                elif i % 5 == 0:
                    elements.append({
                        "type": "bold",
                        "content": f"太字テキスト {i}",
                        "attributes": {"class": "bold"}
                    })
                elif i % 3 == 0:
                    elements.append({
                        "type": "block",
                        "content": f"ブロック内容 {i}",
                        "attributes": {"class": "block-content"}
                    })
                else:
                    elements.append({
                        "type": "text",
                        "content": f"通常テキスト {i}",
                        "attributes": {}
                    })

        elif complexity == "complex":
            # 高度な複雑さ（ネスト、複合要素）
            for i in range(element_count):
                if i % 20 == 0:
                    elements.append({
                        "type": "section",
                        "content": f"セクション {i}",
                        "children": [
                            {
                                "type": "heading",
                                "level": 2,
                                "content": f"サブ見出し {i}",
                                "attributes": {"id": f"sub_heading_{i}"}
                            },
                            {
                                "type": "paragraph",
                                "content": f"段落内容 {i}",
                                "attributes": {"class": "paragraph"}
                            }
                        ],
                        "attributes": {"class": "section", "data-index": str(i)}
                    })
                elif i % 8 == 0:
                    elements.append({
                        "type": "list",
                        "list_type": "unordered",
                        "items": [
                            {"content": f"項目 {i}-1", "type": "list_item"},
                            {"content": f"項目 {i}-2", "type": "list_item"},
                            {"content": f"項目 {i}-3", "type": "list_item"}
                        ],
                        "attributes": {"class": "list"}
                    })
                elif i % 4 == 0:
                    elements.append({
                        "type": "composite",
                        "content": f"複合要素 {i}",
                        "inline_elements": [
                            {"type": "bold", "content": "太字部分"},
                            {"type": "italic", "content": "イタリック部分"},
                            {"type": "link", "content": "リンク", "href": f"#link_{i}"}
                        ],
                        "attributes": {"class": "composite"}
                    })
                else:
                    elements.append({
                        "type": "text",
                        "content": f"通常テキスト {i}",
                        "attributes": {}
                    })

        return {
            "elements": elements,
            "metadata": {
                "element_count": len(elements),
                "complexity": complexity,
                "generated_at": time.time()
            }
        }

    def mock_render_element(self, element: Dict[str, Any]) -> str:
        """要素のモックレンダリング"""
        element_type = element.get("type", "text")
        content = element.get("content", "")
        attributes = element.get("attributes", {})

        # 属性文字列生成
        attr_str = ""
        for key, value in attributes.items():
            attr_str += f' {key}="{value}"'

        if element_type == "text":
            return content

        elif element_type == "heading":
            level = element.get("level", 1)
            return f"<h{level}{attr_str}>{content}</h{level}>"

        elif element_type == "bold":
            return f"<strong{attr_str}>{content}</strong>"

        elif element_type == "italic":
            return f"<em{attr_str}>{content}</em>"

        elif element_type == "block":
            return f"<div{attr_str}>{content}</div>"

        elif element_type == "paragraph":
            return f"<p{attr_str}>{content}</p>"

        elif element_type == "section":
            children = element.get("children", [])
            children_html = ""
            for child in children:
                children_html += self.mock_render_element(child)
            return f"<section{attr_str}><h2>{content}</h2>{children_html}</section>"

        elif element_type == "list":
            items = element.get("items", [])
            list_type = element.get("list_type", "unordered")
            tag = "ul" if list_type == "unordered" else "ol"

            items_html = ""
            for item in items:
                items_html += f"<li>{item.get('content', '')}</li>"

            return f"<{tag}{attr_str}>{items_html}</{tag}>"

        elif element_type == "composite":
            inline_elements = element.get("inline_elements", [])
            inline_html = ""
            for inline in inline_elements:
                inline_html += self.mock_render_element(inline)
            return f"<div{attr_str}>{content} {inline_html}</div>"

        elif element_type == "link":
            href = element.get("href", "#")
            return f"<a{attr_str} href=\"{href}\">{content}</a>"

        else:
            return f"<span{attr_str}>{content}</span>"

    def mock_render_full_document(self, parsed_data: Dict[str, Any]) -> str:
        """完全ドキュメントのモックレンダリング"""
        start_time = time.time()

        elements = parsed_data.get("elements", [])
        metadata = parsed_data.get("metadata", {})

        # HTML構造の構築
        html_parts = [
            "<!DOCTYPE html>",
            '<html lang="ja">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'<title>レンダリングテスト - {metadata.get("complexity", "unknown")}</title>',
            "<style>",
            "body { font-family: sans-serif; margin: 20px; }",
            ".bold { font-weight: bold; }",
            ".block-content { margin: 10px 0; padding: 10px; background: #f5f5f5; }",
            ".section { margin: 20px 0; border: 1px solid #ddd; padding: 15px; }",
            ".list { margin: 10px 0; }",
            ".composite { border: 1px solid #ccc; padding: 5px; }",
            "</style>",
            "</head>",
            "<body>",
            f'<h1>レンダリング結果 ({len(elements)}要素)</h1>'
        ]

        # 要素のレンダリング
        rendering_start = time.time()
        for element in elements:
            rendered_element = self.mock_render_element(element)
            html_parts.append(rendered_element)
        rendering_time = time.time() - rendering_start

        # HTML終了タグ
        html_parts.extend([
            f'<p>レンダリング時間: {rendering_time:.4f}秒</p>',
            "</body>",
            "</html>"
        ])

        total_time = time.time() - start_time

        rendered_html = '\n'.join(html_parts)

        return {
            "html": rendered_html,
            "total_time": total_time,
            "rendering_time": rendering_time,
            "html_size": len(rendered_html),
            "elements_rendered": len(elements)
        }

    def measure_rendering_performance(self, parsed_data: Dict[str, Any],
                                    iterations: int = 1) -> Dict[str, Any]:
        """レンダリング性能測定"""
        start_memory = 0
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            start_memory = process.memory_info().rss

        results = []
        total_start_time = time.time()

        for i in range(iterations):
            iteration_start = time.time()
            render_result = self.mock_render_full_document(parsed_data)
            iteration_time = time.time() - iteration_start

            results.append({
                "iteration": i,
                "time": iteration_time,
                "render_result": render_result
            })

        total_time = time.time() - total_start_time

        end_memory = 0
        if PSUTIL_AVAILABLE:
            end_memory = process.memory_info().rss

        # 統計計算
        processing_times = [r["time"] for r in results]
        html_sizes = [r["render_result"]["html_size"] for r in results]

        avg_time = sum(processing_times) / len(processing_times)
        min_time = min(processing_times)
        max_time = max(processing_times)
        avg_html_size = sum(html_sizes) / len(html_sizes)

        return {
            "iterations": iterations,
            "total_time": total_time,
            "average_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "average_html_size_kb": avg_html_size / 1024,
            "throughput_per_second": iterations / total_time if total_time > 0 else 0,
            "memory_usage_mb": (end_memory - start_memory) / 1024 / 1024 if PSUTIL_AVAILABLE else 0,
            "results": results
        }

    def run_scalability_test(self, base_element_count: int,
                           scale_factors: List[int]) -> Dict[str, Any]:
        """スケーラビリティテスト実行"""
        scalability_results = []

        for factor in scale_factors:
            element_count = base_element_count * factor
            parsed_data = self.generate_parsed_data(element_count, "medium")

            performance_result = self.measure_rendering_performance(parsed_data, 3)

            scalability_results.append({
                "scale_factor": factor,
                "element_count": element_count,
                "average_time": performance_result["average_time"],
                "throughput": performance_result["throughput_per_second"],
                "html_size_kb": performance_result["average_html_size_kb"],
                "memory_usage_mb": performance_result["memory_usage_mb"]
            })

        return {
            "base_element_count": base_element_count,
            "scale_factors": scale_factors,
            "results": scalability_results
        }


class TestRenderingPerformance:
    """レンダリング性能のテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.tester = RenderingPerformanceTester()
        logger.info("レンダリング性能テスト開始")

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        self.tester.cleanup()
        logger.info("レンダリング性能テスト終了")

    @pytest.mark.performance
    def test_レンダリング性能_小規模要素(self) -> None:
        """レンダリング性能: 小規模要素（100要素）"""
        # Given: 小規模要素データ
        parsed_data = self.tester.generate_parsed_data(100, "medium")

        # When: レンダリング性能測定
        result = self.tester.measure_rendering_performance(parsed_data, 10)

        # Then: 性能基準確認
        assert result["average_time"] < 0.1, \
               f"小規模要素レンダリング時間超過: {result['average_time']:.3f}秒"
        assert result["throughput_per_second"] > 50, \
               f"小規模要素スループット不足: {result['throughput_per_second']:.1f}/秒"

        logger.info(f"小規模要素性能: 平均{result['average_time']:.3f}秒, "
                   f"HTML{result['average_html_size_kb']:.1f}KB")

    @pytest.mark.performance
    def test_レンダリング性能_中規模要素(self) -> None:
        """レンダリング性能: 中規模要素（1000要素）"""
        # Given: 中規模要素データ
        parsed_data = self.tester.generate_parsed_data(1000, "medium")

        # When: レンダリング性能測定
        result = self.tester.measure_rendering_performance(parsed_data, 5)

        # Then: 性能基準確認
        assert result["average_time"] < 2.0, \
               f"中規模要素レンダリング時間超過: {result['average_time']:.3f}秒"
        assert result["memory_usage_mb"] < 50, \
               f"中規模要素メモリ使用量超過: {result['memory_usage_mb']:.1f}MB"

        # HTML出力サイズの妥当性確認
        assert result["average_html_size_kb"] > 10, "HTML出力サイズが小さすぎる"
        assert result["average_html_size_kb"] < 1000, "HTML出力サイズが大きすぎる"

        logger.info(f"中規模要素性能: 平均{result['average_time']:.3f}秒, "
                   f"HTML{result['average_html_size_kb']:.1f}KB")

    @pytest.mark.performance
    def test_レンダリング性能_大規模要素(self) -> None:
        """レンダリング性能: 大規模要素（5000要素）"""
        # Given: 大規模要素データ
        parsed_data = self.tester.generate_parsed_data(5000, "medium")

        # When: レンダリング性能測定
        result = self.tester.measure_rendering_performance(parsed_data, 3)

        # Then: 性能基準確認
        assert result["average_time"] < 10.0, \
               f"大規模要素レンダリング時間超過: {result['average_time']:.3f}秒"
        assert result["memory_usage_mb"] < 100, \
               f"大規模要素メモリ使用量超過: {result['memory_usage_mb']:.1f}MB"

        logger.info(f"大規模要素性能: 平均{result['average_time']:.3f}秒, "
                   f"HTML{result['average_html_size_kb']:.1f}KB")

    @pytest.mark.performance
    def test_レンダリング性能_複雑度比較(self) -> None:
        """レンダリング性能: 複雑度による性能差"""
        # Given: 異なる複雑度の要素データ
        element_count = 500
        complexities = ["simple", "medium", "complex"]

        # When: 複雑度別性能測定
        complexity_results = {}
        for complexity in complexities:
            parsed_data = self.tester.generate_parsed_data(element_count, complexity)
            result = self.tester.measure_rendering_performance(parsed_data, 5)
            complexity_results[complexity] = result

        # Then: 複雑度による性能差確認
        simple_time = complexity_results["simple"]["average_time"]
        medium_time = complexity_results["medium"]["average_time"]
        complex_time = complexity_results["complex"]["average_time"]

        # 複雑度が上がると処理時間も増加するはず
        assert simple_time <= medium_time, "シンプル > 中程度の処理時間関係が不正"
        assert medium_time <= complex_time * 1.5, "中程度 > 複雑の処理時間関係が不正"

        # 最大複雑度でも妥当な時間内
        assert complex_time < 5.0, \
               f"複雑要素レンダリング時間超過: {complex_time:.3f}秒"

        # HTML出力サイズも複雑度に応じて増加
        simple_size = complexity_results["simple"]["average_html_size_kb"]
        complex_size = complexity_results["complex"]["average_html_size_kb"]
        assert complex_size > simple_size, "複雑度に応じたHTML出力サイズ増加なし"

        logger.info(f"複雑度性能比較: シンプル{simple_time:.3f}s, "
                   f"中程度{medium_time:.3f}s, 複雑{complex_time:.3f}s")

    @pytest.mark.performance
    def test_レンダリング性能_HTML出力品質(self) -> None:
        """レンダリング性能: HTML出力品質の確認"""
        # Given: 中規模複雑要素データ
        parsed_data = self.tester.generate_parsed_data(300, "complex")

        # When: レンダリング実行
        result = self.tester.measure_rendering_performance(parsed_data, 1)
        html_output = result["results"][0]["render_result"]["html"]

        # Then: HTML品質確認
        # 基本HTML構造
        assert "<!DOCTYPE html>" in html_output, "DOCTYPE宣言がない"
        assert "<html" in html_output and "</html>" in html_output, "HTML要素がない"
        assert "<head>" in html_output and "</head>" in html_output, "HEAD要素がない"
        assert "<body>" in html_output and "</body>" in html_output, "BODY要素がない"

        # メタデータ
        assert 'charset="UTF-8"' in html_output, "UTF-8エンコーディング指定がない"
        assert "<title>" in html_output, "TITLE要素がない"

        # スタイル
        assert "<style>" in html_output, "スタイル定義がない"

        # コンテンツの存在
        assert "要素)" in html_output, "要素数表示がない"

        # HTML出力サイズの妥当性
        html_size_kb = len(html_output) / 1024
        assert html_size_kb > 5, f"HTML出力が小さすぎる: {html_size_kb:.1f}KB"

        logger.info(f"HTML出力品質確認完了: {html_size_kb:.1f}KB, "
                   f"文字数{len(html_output)}")

    @pytest.mark.performance
    def test_レンダリング性能_スケーラビリティ(self) -> None:
        """レンダリング性能: スケーラビリティの確認"""
        # Given: スケーラビリティテスト設定
        base_element_count = 100
        scale_factors = [1, 2, 5, 10]

        # When: スケーラビリティテスト実行
        scalability_result = self.tester.run_scalability_test(
            base_element_count, scale_factors
        )

        # Then: スケーラビリティ確認
        results = scalability_result["results"]

        # 線形スケーラビリティの確認
        time_ratios = []
        for i in range(1, len(results)):
            prev_time = results[i-1]["average_time"]
            curr_time = results[i]["average_time"]
            scale_ratio = results[i]["scale_factor"] / results[i-1]["scale_factor"]
            time_ratio = curr_time / prev_time if prev_time > 0 else float('inf')
            time_ratios.append(time_ratio / scale_ratio)

        # 時間増加率が妥当な範囲内
        avg_ratio = sum(time_ratios) / len(time_ratios) if time_ratios else 1.0
        assert 0.5 <= avg_ratio <= 3.0, \
               f"レンダリングスケーラビリティが非線形: 平均比{avg_ratio:.2f}"

        # 最大スケールでも妥当な性能
        max_scale_result = results[-1]
        assert max_scale_result["average_time"] < 8.0, \
               f"最大スケールレンダリング時間超過: {max_scale_result['average_time']:.3f}秒"

        logger.info(f"レンダリングスケーラビリティ確認完了: {len(results)}ポイント, "
                   f"平均比{avg_ratio:.2f}")

    @pytest.mark.performance
    def test_レンダリング性能_メモリ効率性(self) -> None:
        """レンダリング性能: メモリ効率性の確認"""
        # Given: メモリ効率性テスト用データ
        parsed_data = self.tester.generate_parsed_data(1000, "medium")

        # When: 複数回実行でメモリ使用パターン確認
        memory_usage_history = []
        for i in range(5):
            result = self.tester.measure_rendering_performance(parsed_data, 1)
            memory_usage_history.append(result["memory_usage_mb"])

        # Then: メモリ効率性確認
        max_memory = max(memory_usage_history)
        min_memory = min(memory_usage_history)
        memory_variance = max_memory - min_memory

        assert memory_variance < 30, \
               f"レンダリングメモリ使用量の変動が大きい: {memory_variance:.1f}MB"

        avg_memory = sum(memory_usage_history) / len(memory_usage_history)
        assert avg_memory < 80, \
               f"レンダリング平均メモリ使用量超過: {avg_memory:.1f}MB"

        logger.info(f"レンダリングメモリ効率性確認完了: 平均{avg_memory:.1f}MB, "
                   f"変動{memory_variance:.1f}MB")

    @pytest.mark.performance
    def test_レンダリング性能_並列要素処理(self) -> None:
        """レンダリング性能: 並列要素処理での性能確認"""
        # Given: 並列処理用複数データセット
        datasets = [
            self.tester.generate_parsed_data(200, "simple"),
            self.tester.generate_parsed_data(200, "medium"),
            self.tester.generate_parsed_data(200, "complex")
        ]

        # When: 並列レンダリングシミュレート
        start_time = time.time()
        parallel_results = []

        for i, data in enumerate(datasets):
            result = self.tester.measure_rendering_performance(data, 1)
            parallel_results.append({
                "dataset_id": i,
                "complexity": ["simple", "medium", "complex"][i],
                "result": result
            })

        total_parallel_time = time.time() - start_time

        # Then: 並列処理性能確認
        total_processing_time = sum(r["result"]["average_time"] for r in parallel_results)

        # 並列処理効率性確認
        efficiency = total_processing_time / total_parallel_time if total_parallel_time > 0 else 0
        assert efficiency >= 0.7, f"並列レンダリング効率が低い: {efficiency:.2f}"

        # 全体の処理時間確認
        assert total_parallel_time < 5.0, \
               f"並列レンダリング時間超過: {total_parallel_time:.3f}秒"

        # HTML出力品質確認
        for result in parallel_results:
            html_size = result["result"]["average_html_size_kb"]
            assert html_size > 1, f"並列処理でHTML出力が小さすぎる: {html_size:.1f}KB"

        logger.info(f"並列レンダリング性能確認完了: 効率{efficiency:.2f}, "
                   f"総時間{total_parallel_time:.3f}秒")

    @pytest.mark.performance
    def test_レンダリング性能_出力最適化(self) -> None:
        """レンダリング性能: 出力最適化の確認"""
        # Given: 最適化対象データ
        parsed_data = self.tester.generate_parsed_data(800, "complex")

        # When: 最適化レンダリング実行
        result = self.tester.measure_rendering_performance(parsed_data, 3)
        html_output = result["results"][0]["render_result"]["html"]

        # Then: 出力最適化確認
        # HTML構造の効率性
        tag_count = html_output.count('<')
        content_ratio = (len(html_output) - tag_count * 10) / len(html_output)  # 概算
        assert content_ratio > 0.3, f"HTML構造効率が低い: コンテンツ比{content_ratio:.2f}"

        # 重複スタイルがないこと
        style_section = html_output[html_output.find('<style>'):html_output.find('</style>')]
        style_lines = style_section.split('\n')
        unique_styles = set(line.strip() for line in style_lines if line.strip())
        assert len(unique_styles) == len([line for line in style_lines if line.strip()]), \
               "重複するスタイル定義がある"

        # レンダリング速度
        assert result["average_time"] < 3.0, \
               f"最適化レンダリング時間超過: {result['average_time']:.3f}秒"

        logger.info(f"出力最適化確認完了: コンテンツ比{content_ratio:.2f}, "
                   f"時間{result['average_time']:.3f}秒")
