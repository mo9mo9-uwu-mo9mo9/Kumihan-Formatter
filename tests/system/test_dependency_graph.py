"""依存関係グラフのシステム統合テスト

モジュール間の依存関係を可視化・検証し、
システムの健全性と保守性を確認する。
"""

import ast
import json
import tempfile
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pytest

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestDependencyGraph:
    """依存関係グラフのテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.project_root = Path(__file__).parent.parent.parent
        self.kumihan_root = self.project_root / "kumihan_formatter"
        self.temp_dir = Path(tempfile.mkdtemp())
        logger.info(f"プロジェクトルート: {self.project_root}")

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        import shutil

        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"一時ディレクトリを削除: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"一時ディレクトリの削除に失敗: {e}")

    def extract_imports(self, file_path: Path) -> List[Dict[str, Any]]:
        """ファイルからインポート情報を抽出"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(
                            {
                                "type": "import",
                                "module": alias.name,
                                "alias": alias.asname,
                                "line": node.lineno,
                            }
                        )

                elif isinstance(node, ast.ImportFrom):
                    imports.append(
                        {
                            "type": "from_import",
                            "module": node.module,
                            "names": [alias.name for alias in node.names],
                            "level": node.level,
                            "line": node.lineno,
                        }
                    )

            return imports

        except Exception as e:
            logger.error(f"インポート抽出エラー ({file_path}): {e}")
            return []

    def build_dependency_graph(self, module_paths: List[Path]) -> Dict[str, Any]:
        """依存関係グラフを構築"""
        graph = {"nodes": {}, "edges": [], "clusters": {}, "metrics": {}}

        # ノード情報収集
        for module_path in module_paths:
            module_name = self._path_to_module_name(module_path)
            imports = self.extract_imports(module_path)

            # 内部インポートのみ抽出
            internal_imports = []
            for imp in imports:
                if self._is_internal_import(imp):
                    internal_imports.append(imp)

            graph["nodes"][module_name] = {
                "path": str(module_path),
                "imports": internal_imports,
                "import_count": len(internal_imports),
                "cluster": self._determine_cluster(module_path),
            }

        # エッジ情報構築
        for source_module, node_info in graph["nodes"].items():
            for imp in node_info["imports"]:
                target_module = self._resolve_import_target(imp)
                if target_module and target_module in graph["nodes"]:
                    graph["edges"].append(
                        {
                            "source": source_module,
                            "target": target_module,
                            "type": imp["type"],
                            "line": imp.get("line", 0),
                        }
                    )

        # クラスター情報構築
        graph["clusters"] = self._build_clusters(graph["nodes"])

        # メトリクス計算
        graph["metrics"] = self._calculate_graph_metrics(graph)

        return graph

    def _path_to_module_name(self, path: Path) -> str:
        """パスをモジュール名に変換"""
        try:
            relative_path = path.relative_to(self.kumihan_root)
            module_name = str(relative_path).replace("/", ".").replace(".py", "")
            return f"kumihan_formatter.{module_name}"
        except ValueError:
            return str(path.stem)

    def _is_internal_import(self, imp: Dict[str, Any]) -> bool:
        """内部インポートかどうか判定"""
        if imp["type"] == "import":
            return imp["module"].startswith("kumihan_formatter")
        elif imp["type"] == "from_import":
            return imp["module"] and imp["module"].startswith("kumihan_formatter")
        return False

    def _resolve_import_target(self, imp: Dict[str, Any]) -> str:
        """インポート対象を解決"""
        if imp["type"] == "import":
            return imp["module"]
        elif imp["type"] == "from_import":
            return imp["module"]
        return ""

    def _determine_cluster(self, path: Path) -> str:
        """モジュールのクラスターを決定"""
        path_str = str(path)

        if "/core/parsing/" in path_str:
            return "parsing"
        elif "/core/rendering/" in path_str:
            return "rendering"
        elif "/core/utilities/" in path_str:
            return "utilities"
        elif "/core/config/" in path_str:
            return "config"
        elif "/core/" in path_str:
            return "core"
        elif "/cli" in path_str:
            return "cli"
        else:
            return "other"

    def _build_clusters(self, nodes: Dict[str, Any]) -> Dict[str, List[str]]:
        """クラスター情報を構築"""
        clusters = defaultdict(list)
        for module_name, node_info in nodes.items():
            cluster = node_info["cluster"]
            clusters[cluster].append(module_name)
        return dict(clusters)

    def _calculate_graph_metrics(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """グラフメトリクスを計算"""
        nodes = graph["nodes"]
        edges = graph["edges"]

        # 基本メトリクス
        node_count = len(nodes)
        edge_count = len(edges)

        # 入次数・出次数計算
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)

        for edge in edges:
            out_degree[edge["source"]] += 1
            in_degree[edge["target"]] += 1

        # 密度計算
        max_edges = node_count * (node_count - 1)
        density = edge_count / max_edges if max_edges > 0 else 0

        # 強結合成分解析
        strongly_connected = self._find_strongly_connected_components(graph)

        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "density": density,
            "max_in_degree": max(in_degree.values()) if in_degree else 0,
            "max_out_degree": max(out_degree.values()) if out_degree else 0,
            "avg_in_degree": (sum(in_degree.values()) / node_count if node_count > 0 else 0),
            "avg_out_degree": (sum(out_degree.values()) / node_count if node_count > 0 else 0),
            "strongly_connected_components": len(strongly_connected),
            "largest_scc_size": (
                max(len(scc) for scc in strongly_connected) if strongly_connected else 0
            ),
        }

    def _find_strongly_connected_components(self, graph: Dict[str, Any]) -> List[List[str]]:
        """強結合成分を検出（Kosaraju's algorithm）"""
        nodes = list(graph["nodes"].keys())
        edges = graph["edges"]

        # 隣接リスト構築
        adj_list = defaultdict(list)
        rev_adj_list = defaultdict(list)

        for edge in edges:
            adj_list[edge["source"]].append(edge["target"])
            rev_adj_list[edge["target"]].append(edge["source"])

        # 第1段階: DFSで完了時刻順にスタック
        visited = set()
        stack = []

        def dfs1(node: str) -> None:
            visited.add(node)
            for neighbor in adj_list[node]:
                if neighbor not in visited:
                    dfs1(neighbor)
            stack.append(node)

        for node in nodes:
            if node not in visited:
                dfs1(node)

        # 第2段階: 逆グラフでDFS
        visited = set()
        components = []

        def dfs2(node: str, component: List[str]) -> None:
            visited.add(node)
            component.append(node)
            for neighbor in rev_adj_list[node]:
                if neighbor not in visited:
                    dfs2(neighbor, component)

        while stack:
            node = stack.pop()
            if node not in visited:
                component = []
                dfs2(node, component)
                components.append(component)

        return components

    def detect_circular_dependencies(self, graph: Dict[str, Any]) -> List[List[str]]:
        """循環依存を検出"""
        strongly_connected = self._find_strongly_connected_components(graph)
        # サイズが2以上の強結合成分は循環依存
        return [scc for scc in strongly_connected if len(scc) > 1]

    def analyze_cluster_coupling(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """クラスター間結合度分析"""
        clusters = graph["clusters"]
        edges = graph["edges"]

        # クラスター間エッジ数
        inter_cluster_edges = 0
        intra_cluster_edges = 0
        cluster_connections = defaultdict(int)

        for edge in edges:
            source_cluster = None
            target_cluster = None

            # ソースのクラスター特定
            for cluster_name, modules in clusters.items():
                if edge["source"] in modules:
                    source_cluster = cluster_name
                if edge["target"] in modules:
                    target_cluster = cluster_name

            if source_cluster and target_cluster:
                if source_cluster == target_cluster:
                    intra_cluster_edges += 1
                else:
                    inter_cluster_edges += 1
                    cluster_connections[f"{source_cluster}->{target_cluster}"] += 1

        total_edges = inter_cluster_edges + intra_cluster_edges
        coupling_ratio = inter_cluster_edges / total_edges if total_edges > 0 else 0

        return {
            "inter_cluster_edges": inter_cluster_edges,
            "intra_cluster_edges": intra_cluster_edges,
            "coupling_ratio": coupling_ratio,
            "cluster_connections": dict(cluster_connections),
            "assessment": self._assess_coupling(coupling_ratio),
        }

    def _assess_coupling(self, ratio: float) -> str:
        """結合度の評価"""
        if ratio < 0.3:
            return "低結合（良好）"
        elif ratio < 0.6:
            return "中結合（普通）"
        else:
            return "高結合（要注意）"

    def export_graph_visualization(self, graph: Dict[str, Any], output_path: Path) -> None:
        """グラフ可視化用データをエクスポート"""
        # DOT形式でエクスポート
        dot_content = ["digraph DependencyGraph {"]
        dot_content.append("  rankdir=LR;")
        dot_content.append("  node [shape=box];")

        # クラスター定義
        for cluster_name, modules in graph["clusters"].items():
            dot_content.append(f"  subgraph cluster_{cluster_name} {{")
            dot_content.append(f'    label="{cluster_name}";')
            dot_content.append(f"    color=lightgrey;")
            for module in modules:
                module_id = module.replace(".", "_").replace("-", "_")
                module_label = module.split(".")[-1]
                dot_content.append(f'    {module_id} [label="{module_label}"];')
            dot_content.append("  }")

        # エッジ定義
        for edge in graph["edges"]:
            source_id = edge["source"].replace(".", "_").replace("-", "_")
            target_id = edge["target"].replace(".", "_").replace("-", "_")
            dot_content.append(f"  {source_id} -> {target_id};")

        dot_content.append("}")

        # DOTファイル出力
        dot_file = output_path / "dependency_graph.dot"
        with open(dot_file, "w", encoding="utf-8") as f:
            f.write("\n".join(dot_content))

        # JSONファイル出力
        json_file = output_path / "dependency_graph.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2, default=str)

        logger.info(f"依存関係グラフを出力: {dot_file}, {json_file}")

    @pytest.mark.system
    def test_依存関係グラフ_基本構造(self) -> None:
        """依存関係グラフ: 基本構造の確認"""
        # Given: プロジェクトモジュール
        if not self.kumihan_root.exists():
            pytest.skip(f"Kumihanルートディレクトリが見つかりません: {self.kumihan_root}")

        # 主要モジュールを取得（パフォーマンス考慮で制限）
        module_paths = []
        for py_file in self.kumihan_root.rglob("*.py"):
            if (
                py_file.name != "__init__.py"
                and not py_file.name.startswith("test_")
                and len(module_paths) < 30
            ):  # 最初の30モジュール
                module_paths.append(py_file)

        if not module_paths:
            pytest.skip("解析対象モジュールが見つかりません")

        # When: 依存関係グラフ構築
        graph = self.build_dependency_graph(module_paths)

        # Then: 基本構造確認
        assert graph["metrics"]["node_count"] > 0, "ノードが存在しません"
        assert len(graph["clusters"]) > 0, "クラスターが存在しません"

        # 基本的なクラスターの存在確認
        expected_clusters = ["core", "parsing", "rendering"]
        found_clusters = set(graph["clusters"].keys())
        cluster_coverage = len(set(expected_clusters) & found_clusters) / len(expected_clusters)
        assert cluster_coverage >= 0.5, f"必要なクラスターが不足: {found_clusters}"

        logger.info(
            f"依存関係グラフ基本構造確認完了: {graph['metrics']['node_count']}ノード、"
            f"{len(graph['clusters'])}クラスター"
        )

    @pytest.mark.system
    def test_依存関係グラフ_循環依存検出(self) -> None:
        """依存関係グラフ: 循環依存の検出"""
        # Given: プロジェクトモジュール
        module_paths = []
        for py_file in self.kumihan_root.rglob("*.py"):
            if (
                py_file.name != "__init__.py"
                and not py_file.name.startswith("test_")
                and len(module_paths) < 25
            ):
                module_paths.append(py_file)

        if not module_paths:
            pytest.skip("解析対象モジュールが見つかりません")

        # When: 依存関係グラフ構築と循環依存検出
        graph = self.build_dependency_graph(module_paths)
        circular_dependencies = self.detect_circular_dependencies(graph)

        # Then: 循環依存確認
        # 循環依存は設計上問題であるが、完全にゼロを要求するのは現実的でない
        max_allowed_cycles = 3
        assert (
            len(circular_dependencies) <= max_allowed_cycles
        ), f"循環依存が多すぎます: {len(circular_dependencies)}件"

        if circular_dependencies:
            logger.warning(f"循環依存検出: {len(circular_dependencies)}件")
            for i, cycle in enumerate(circular_dependencies[:3]):  # 最初の3件のみログ
                logger.warning(f"循環{i+1}: {' -> '.join(cycle)}")

        logger.info(f"循環依存検出完了: {len(circular_dependencies)}件の循環依存")

    @pytest.mark.system
    def test_依存関係グラフ_クラスター結合度(self) -> None:
        """依存関係グラフ: クラスター間結合度の分析"""
        # Given: プロジェクトモジュール
        module_paths = []
        for py_file in self.kumihan_root.rglob("*.py"):
            if (
                py_file.name != "__init__.py"
                and not py_file.name.startswith("test_")
                and len(module_paths) < 30
            ):
                module_paths.append(py_file)

        if not module_paths:
            pytest.skip("解析対象モジュールが見つかりません")

        # When: 依存関係グラフ構築とクラスター結合度分析
        graph = self.build_dependency_graph(module_paths)
        coupling_analysis = self.analyze_cluster_coupling(graph)

        # Then: 結合度確認
        coupling_ratio = coupling_analysis["coupling_ratio"]
        assert coupling_ratio < 0.8, f"クラスター間結合度が高すぎます: {coupling_ratio:.3f}"

        # 主要クラスター間の適切な分離確認
        inter_cluster = coupling_analysis["inter_cluster_edges"]
        intra_cluster = coupling_analysis["intra_cluster_edges"]

        if inter_cluster + intra_cluster > 0:
            cohesion_ratio = intra_cluster / (inter_cluster + intra_cluster)
            assert cohesion_ratio >= 0.3, f"クラスター凝集度が低い: {cohesion_ratio:.3f}"

        logger.info(
            f"クラスター結合度分析完了: 結合度{coupling_ratio:.3f}, "
            f"評価: {coupling_analysis['assessment']}"
        )

    @pytest.mark.system
    def test_依存関係グラフ_メトリクス確認(self) -> None:
        """依存関係グラフ: メトリクスの確認"""
        # Given: プロジェクトモジュール
        module_paths = []
        for py_file in self.kumihan_root.rglob("*.py"):
            if (
                py_file.name != "__init__.py"
                and not py_file.name.startswith("test_")
                and len(module_paths) < 25
            ):
                module_paths.append(py_file)

        if not module_paths:
            pytest.skip("解析対象モジュールが見つかりません")

        # When: 依存関係グラフ構築とメトリクス計算
        graph = self.build_dependency_graph(module_paths)
        metrics = graph["metrics"]

        # Then: メトリクス確認
        # 密度チェック（適度な結合度）
        assert 0.05 <= metrics["density"] <= 0.5, f"グラフ密度が異常: {metrics['density']:.3f}"

        # 入次数・出次数チェック
        assert metrics["max_in_degree"] <= 10, f"最大入次数が高すぎます: {metrics['max_in_degree']}"
        assert (
            metrics["max_out_degree"] <= 15
        ), f"最大出次数が高すぎます: {metrics['max_out_degree']}"

        # 強結合成分サイズチェック
        assert (
            metrics["largest_scc_size"] <= 5
        ), f"最大強結合成分が大きすぎます: {metrics['largest_scc_size']}"

        logger.info(
            f"依存関係メトリクス確認完了: 密度{metrics['density']:.3f}, "
            f"最大入次数{metrics['max_in_degree']}, "
            f"最大出次数{metrics['max_out_degree']}"
        )

    @pytest.mark.system
    def test_依存関係グラフ_可視化出力(self) -> None:
        """依存関係グラフ: 可視化データの出力"""
        # Given: プロジェクトモジュール
        module_paths = []
        for py_file in self.kumihan_root.rglob("*.py"):
            if (
                py_file.name != "__init__.py"
                and not py_file.name.startswith("test_")
                and len(module_paths) < 20
            ):
                module_paths.append(py_file)

        if not module_paths:
            pytest.skip("解析対象モジュールが見つかりません")

        # When: 依存関係グラフ構築と可視化出力
        graph = self.build_dependency_graph(module_paths)
        self.export_graph_visualization(graph, self.temp_dir)

        # Then: 出力ファイル確認
        dot_file = self.temp_dir / "dependency_graph.dot"
        json_file = self.temp_dir / "dependency_graph.json"

        assert dot_file.exists(), "DOTファイルが作成されていません"
        assert json_file.exists(), "JSONファイルが作成されていません"

        # DOTファイル内容確認
        dot_content = dot_file.read_text(encoding="utf-8")
        assert "digraph DependencyGraph" in dot_content, "DOT形式が正しくない"
        assert "subgraph cluster_" in dot_content, "クラスター定義がない"

        # JSONファイル内容確認
        json_content = json_file.read_text(encoding="utf-8")
        assert len(json_content) > 100, "JSON内容が少なすぎる"

        logger.info(f"依存関係グラフ可視化出力完了: {dot_file}, {json_file}")

    @pytest.mark.system
    def test_依存関係グラフ_階層構造確認(self) -> None:
        """依存関係グラフ: 階層構造の確認"""
        # Given: プロジェクトモジュール
        module_paths = []
        for py_file in self.kumihan_root.rglob("*.py"):
            if (
                py_file.name != "__init__.py"
                and not py_file.name.startswith("test_")
                and len(module_paths) < 25
            ):
                module_paths.append(py_file)

        if not module_paths:
            pytest.skip("解析対象モジュールが見つかりません")

        # When: 依存関係グラフ構築と階層分析
        graph = self.build_dependency_graph(module_paths)

        # 階層レベル計算（トポロジカルソートベース）
        hierarchy_levels = self._calculate_hierarchy_levels(graph)

        # Then: 階層構造確認
        max_level = max(hierarchy_levels.values()) if hierarchy_levels else 0
        assert max_level <= 8, f"階層が深すぎます: {max_level}レベル"

        # レベル分布確認
        level_distribution = {}
        for level in hierarchy_levels.values():
            level_distribution[level] = level_distribution.get(level, 0) + 1

        # 最下位レベルに過度に集中していないか確認
        if hierarchy_levels:
            bottom_level_ratio = level_distribution.get(max_level, 0) / len(hierarchy_levels)
            assert bottom_level_ratio < 0.7, f"最下位レベルに集中しすぎ: {bottom_level_ratio:.3f}"

        logger.info(f"階層構造確認完了: {max_level}レベル階層、" f"分布: {level_distribution}")

    def _calculate_hierarchy_levels(self, graph: Dict[str, Any]) -> Dict[str, int]:
        """階層レベルを計算"""
        nodes = set(graph["nodes"].keys())
        edges = graph["edges"]

        # 入次数計算
        in_degree = {node: 0 for node in nodes}
        for edge in edges:
            if edge["target"] in in_degree:
                in_degree[edge["target"]] += 1

        # トポロジカルソート
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        levels = {}
        current_level = 0

        while queue:
            level_size = len(queue)
            for _ in range(level_size):
                node = queue.popleft()
                levels[node] = current_level

                # 隣接ノードの入次数を減らす
                for edge in edges:
                    if edge["source"] == node and edge["target"] in in_degree:
                        in_degree[edge["target"]] -= 1
                        if in_degree[edge["target"]] == 0:
                            queue.append(edge["target"])

            current_level += 1

        return levels
