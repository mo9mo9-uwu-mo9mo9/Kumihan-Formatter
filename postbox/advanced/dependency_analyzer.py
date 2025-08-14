#!/usr/bin/env python3
"""
Dependency Analyzer - 依存関係解析エンジン
Issue #870: 複雑タスクパターン拡張

ファイル間依存関係の自動検出・解析システム
"""

import ast
import os
import sys
import importlib.util
from typing import Dict, List, Any, Set, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict, deque
# NetworkX統合（オプション）
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

# ロガー統合
try:
    from kumihan_formatter.core.utilities.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class ImportInfo:
    """インポート情報"""
    module_name: str
    alias: Optional[str]
    imported_names: List[str]
    import_type: str  # 'import', 'from_import', 'relative_import'
    line_number: int
    is_standard_library: bool
    is_third_party: bool
    is_local: bool


@dataclass
class DependencyNode:
    """依存関係ノード"""
    file_path: str
    module_name: str
    imports: List[ImportInfo]
    exports: List[str]  # 公開される関数・クラス名
    complexity_score: int
    cyclomatic_complexity: int
    dependency_count: int


@dataclass
class DependencyGraph:
    """依存関係グラフ"""
    nodes: Dict[str, DependencyNode]
    edges: List[Tuple[str, str]]  # (from_file, to_file)
    cycles: List[List[str]]  # 循環依存パス
    levels: Dict[str, int]  # 実装順序レベル
    clusters: List[List[str]]  # 関連ファイルクラスター


class DependencyAnalyzer:
    """依存関係解析エンジン"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.graph = None
        self.standard_modules = self._get_standard_modules()

        logger.info("🔍 Dependency Analyzer 初期化完了")
        logger.info(f"📁 プロジェクトルート: {self.project_root}")

    def analyze_project_dependencies(
        self, target_paths: List[str] = None
    ) -> DependencyGraph:
        """プロジェクト全体の依存関係解析"""

        logger.info("🔍 プロジェクト依存関係解析開始")

        if target_paths is None:
            target_paths = self._find_python_files()

        # 1. 各ファイルの分析
        nodes = {}
        for file_path in target_paths:
            try:
                node = self._analyze_file(file_path)
                if node:
                    nodes[file_path] = node
            except Exception as e:
                logger.warning(f"ファイル解析エラー {file_path}: {e}")

        # 2. 依存関係エッジ構築
        edges = self._build_dependency_edges(nodes)

        # 3. 循環依存検出
        cycles = self._detect_cycles(nodes, edges)

        # 4. 実装順序レベル計算
        levels = self._calculate_implementation_levels(nodes, edges)

        # 5. クラスター分析
        clusters = self._analyze_clusters(nodes, edges)

        self.graph = DependencyGraph(
            nodes=nodes,
            edges=edges,
            cycles=cycles,
            levels=levels,
            clusters=clusters
        )

        logger.info(f"✅ 依存関係解析完了:")
        logger.info(f"  - ファイル数: {len(nodes)}")
        logger.info(f"  - 依存関係数: {len(edges)}")
        logger.info(f"  - 循環依存: {len(cycles)}件")
        logger.info(f"  - 実装レベル: {max(levels.values()) if levels else 0}")

        return self.graph

    def get_implementation_order(self) -> List[List[str]]:
        """実装順序の取得（依存関係を考慮）"""

        if not self.graph:
            raise ValueError("依存関係解析が実行されていません")

        # レベル別にグループ化
        level_groups = defaultdict(list)
        for file_path, level in self.graph.levels.items():
            level_groups[level].append(file_path)

        # レベル順にソート
        implementation_order = []
        for level in sorted(level_groups.keys()):
            implementation_order.append(level_groups[level])

        logger.info(f"📋 実装順序決定: {len(implementation_order)}レベル")
        return implementation_order

    def detect_circular_dependencies(self) -> List[List[str]]:
        """循環依存の検出"""

        if not self.graph:
            raise ValueError("依存関係解析が実行されていません")

        if self.graph.cycles:
            logger.warning(f"🔄 循環依存検出: {len(self.graph.cycles)}件")
            for i, cycle in enumerate(self.graph.cycles):
                logger.warning(f"  サイクル{i+1}: {' -> '.join(cycle)}")

        return self.graph.cycles

    def get_parallel_implementation_groups(self) -> List[List[str]]:
        """並列実装可能グループの取得"""

        if not self.graph:
            raise ValueError("依存関係解析が実行されていません")

        parallel_groups = []

        # 同一レベルのファイルは並列実装可能
        level_groups = defaultdict(list)
        for file_path, level in self.graph.levels.items():
            level_groups[level].append(file_path)

        for level, files in level_groups.items():
            if len(files) > 1:
                parallel_groups.append(files)

        logger.info(f"⚡ 並列実装可能グループ: {len(parallel_groups)}グループ")
        return parallel_groups

    def analyze_file_complexity(self, file_path: str) -> Dict[str, Any]:
        """ファイル複雑度の詳細分析"""

        if not self.graph or file_path not in self.graph.nodes:
            return {"error": "ファイルが解析されていません"}

        node = self.graph.nodes[file_path]

        complexity_analysis = {
            "file_path": file_path,
            "complexity_score": node.complexity_score,
            "cyclomatic_complexity": node.cyclomatic_complexity,
            "dependency_count": node.dependency_count,
            "import_count": len(node.imports),
            "export_count": len(node.exports),
            "third_party_imports": len([
                imp for imp in node.imports if imp.is_third_party
            ]),
            "local_imports": len([
                imp for imp in node.imports if imp.is_local
            ]),
            "complexity_level": self._classify_complexity(node.complexity_score)
        }

        return complexity_analysis

    def _analyze_file(self, file_path: str) -> Optional[DependencyNode]:
        """単一ファイルの依存関係解析"""

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)

            # インポート解析
            imports = self._extract_imports(tree)

            # エクスポート解析
            exports = self._extract_exports(tree)

            # 複雑度計算
            complexity_score = self._calculate_complexity_score(tree)
            cyclomatic_complexity = self._calculate_cyclomatic_complexity(tree)

            # モジュール名推定
            module_name = self._path_to_module_name(file_path)

            return DependencyNode(
                file_path=file_path,
                module_name=module_name,
                imports=imports,
                exports=exports,
                complexity_score=complexity_score,
                cyclomatic_complexity=cyclomatic_complexity,
                dependency_count=len(imports)
            )

        except Exception as e:
            logger.error(f"ファイル解析エラー {file_path}: {e}")
            return None

    def _extract_imports(self, tree: ast.AST) -> List[ImportInfo]:
        """インポート文の抽出"""

        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_info = ImportInfo(
                        module_name=alias.name,
                        alias=alias.asname,
                        imported_names=[],
                        import_type='import',
                        line_number=node.lineno,
                        is_standard_library=self._is_standard_library(alias.name),
                        is_third_party=self._is_third_party(alias.name),
                        is_local=self._is_local_import(alias.name)
                    )
                    imports.append(import_info)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_names = [alias.name for alias in node.names]
                    import_info = ImportInfo(
                        module_name=node.module,
                        alias=None,
                        imported_names=imported_names,
                        import_type='from_import' if node.level == 0 else 'relative_import',
                        line_number=node.lineno,
                        is_standard_library=self._is_standard_library(node.module),
                        is_third_party=self._is_third_party(node.module),
                        is_local=self._is_local_import(node.module)
                    )
                    imports.append(import_info)

        return imports

    def _extract_exports(self, tree: ast.AST) -> List[str]:
        """エクスポート（公開要素）の抽出"""

        exports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):
                    exports.append(node.name)
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith('_'):
                    exports.append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith('_'):
                        exports.append(target.id)

        return exports

    def _calculate_complexity_score(self, tree: ast.AST) -> int:
        """複雑度スコア計算"""

        score = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                score += 2
            elif isinstance(node, ast.ClassDef):
                score += 3
            elif isinstance(node, (ast.If, ast.While, ast.For)):
                score += 1
            elif isinstance(node, ast.Try):
                score += 2

        return score

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """循環的複雑度計算"""

        complexity = 1  # 基準値

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def _build_dependency_edges(
        self, nodes: Dict[str, DependencyNode]
    ) -> List[Tuple[str, str]]:
        """依存関係エッジの構築"""

        edges = []

        for file_path, node in nodes.items():
            for import_info in node.imports:
                if import_info.is_local:
                    # ローカルインポートの場合、対応するファイルを探す
                    target_file = self._resolve_import_to_file(
                        import_info.module_name, file_path
                    )
                    if target_file and target_file in nodes:
                        edges.append((file_path, target_file))

        return edges

    def _detect_cycles(
        self, nodes: Dict[str, DependencyNode], edges: List[Tuple[str, str]]
    ) -> List[List[str]]:
        """循環依存の検出"""

        if NETWORKX_AVAILABLE and nx:
            # NetworkXを使用してグラフ構築
            G = nx.DiGraph()
            G.add_nodes_from(nodes.keys())
            G.add_edges_from(edges)

            # 循環依存検出
            try:
                cycles = list(nx.simple_cycles(G))
                return cycles
            except Exception:
                return []
        else:
            # 簡易実装（NetworkX未使用）
            return self._detect_cycles_simple(nodes, edges)

    def _detect_cycles_simple(
        self, nodes: Dict[str, DependencyNode], edges: List[Tuple[str, str]]
    ) -> List[List[str]]:
        """簡易循環依存検出（NetworkX未使用）"""

        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # 循環検出
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            # 隣接ノードを探索
            for edge_from, edge_to in edges:
                if edge_from == node:
                    dfs(edge_to, path + [node])

            rec_stack.remove(node)

        for node in nodes.keys():
            if node not in visited:
                dfs(node, [])

        return cycles

    def _calculate_implementation_levels(
        self, nodes: Dict[str, DependencyNode], edges: List[Tuple[str, str]]
    ) -> Dict[str, int]:
        """実装順序レベルの計算"""

        # トポロジカルソートベースの実装
        in_degree = {file_path: 0 for file_path in nodes.keys()}

        # 入次数計算
        for _, target in edges:
            if target in in_degree:
                in_degree[target] += 1

        # レベル計算
        levels = {}
        queue = deque([file for file, degree in in_degree.items() if degree == 0])
        current_level = 0

        while queue:
            level_size = len(queue)
            for _ in range(level_size):
                file_path = queue.popleft()
                levels[file_path] = current_level

                # 依存先のファイルの入次数を減少
                for edge_from, edge_to in edges:
                    if edge_from == file_path and edge_to in in_degree:
                        in_degree[edge_to] -= 1
                        if in_degree[edge_to] == 0:
                            queue.append(edge_to)

            current_level += 1

        return levels

    def _analyze_clusters(
        self, nodes: Dict[str, DependencyNode], edges: List[Tuple[str, str]]
    ) -> List[List[str]]:
        """関連ファイルクラスターの分析"""

        # 単純なクラスタリング（共通のインポートパターンベース）
        clusters = []

        # モジュールレベルでのグループ化
        module_groups = defaultdict(list)
        for file_path, node in nodes.items():
            module_prefix = node.module_name.split('.')[0] if '.' in node.module_name else node.module_name
            module_groups[module_prefix].append(file_path)

        for group_files in module_groups.values():
            if len(group_files) > 1:
                clusters.append(group_files)

        return clusters

    def _find_python_files(self) -> List[str]:
        """Pythonファイルの検索"""

        python_files = []

        for root, dirs, files in os.walk(self.project_root):
            # 除外ディレクトリ
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)

        return python_files

    def _get_standard_modules(self) -> Set[str]:
        """標準ライブラリモジュール一覧取得"""

        standard_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 'pathlib', 'typing',
            'collections', 'itertools', 'functools', 'operator', 'copy',
            'pickle', 're', 'math', 'random', 'statistics', 'decimal',
            'fractions', 'sqlite3', 'csv', 'configparser', 'logging',
            'unittest', 'doctest', 'argparse', 'subprocess', 'threading',
            'multiprocessing', 'asyncio', 'concurrent', 'queue', 'socket',
            'urllib', 'http', 'ftplib', 'smtplib', 'email', 'html', 'xml',
            'hashlib', 'hmac', 'secrets', 'ssl', 'gzip', 'bz2', 'lzma',
            'zipfile', 'tarfile', 'tempfile', 'shutil', 'glob', 'fnmatch'
        }

        return standard_modules

    def _is_standard_library(self, module_name: str) -> bool:
        """標準ライブラリかどうかの判定"""
        return module_name.split('.')[0] in self.standard_modules

    def _is_third_party(self, module_name: str) -> bool:
        """サードパーティライブラリかどうかの判定"""
        return not self._is_standard_library(module_name) and not self._is_local_import(module_name)

    def _is_local_import(self, module_name: str) -> bool:
        """ローカルインポートかどうかの判定"""
        # プロジェクト固有のモジュール名パターンで判定
        project_patterns = ['kumihan_formatter', 'postbox']
        return any(module_name.startswith(pattern) for pattern in project_patterns)

    def _path_to_module_name(self, file_path: str) -> str:
        """ファイルパスからモジュール名への変換"""

        rel_path = os.path.relpath(file_path, self.project_root)
        module_parts = rel_path.replace(os.sep, '.').replace('.py', '').split('.')

        # __init__.pyの場合は親ディレクトリ名を使用
        if module_parts[-1] == '__init__':
            module_parts = module_parts[:-1]

        return '.'.join(module_parts)

    def _resolve_import_to_file(self, module_name: str, current_file: str) -> Optional[str]:
        """インポート名からファイルパスへの解決"""

        try:
            # 基本的な解決ロジック
            module_parts = module_name.split('.')

            # プロジェクトルートからの相対パス構築
            potential_paths = [
                self.project_root / (os.sep.join(module_parts) + '.py'),
                self.project_root / os.sep.join(module_parts) / '__init__.py'
            ]

            for path in potential_paths:
                if path.exists():
                    return str(path)

            return None

        except Exception:
            return None

    def _classify_complexity(self, score: int) -> str:
        """複雑度レベルの分類"""

        if score <= 10:
            return "simple"
        elif score <= 25:
            return "moderate"
        elif score <= 50:
            return "complex"
        else:
            return "very_complex"


if __name__ == "__main__":
    """簡単なテスト実行"""

    analyzer = DependencyAnalyzer()

    # プロジェクト全体の依存関係解析
    graph = analyzer.analyze_project_dependencies()

    # 実装順序の表示
    implementation_order = analyzer.get_implementation_order()
    print(f"\n📋 実装順序:")
    for level, files in enumerate(implementation_order):
        print(f"  レベル {level}: {len(files)}ファイル")
        for file in files[:3]:  # 最初の3ファイルのみ表示
            print(f"    - {file}")
        if len(files) > 3:
            print(f"    ... 他 {len(files)-3}ファイル")

    # 循環依存の確認
    cycles = analyzer.detect_circular_dependencies()
    if cycles:
        print(f"\n🔄 循環依存検出: {len(cycles)}件")
    else:
        print(f"\n✅ 循環依存なし")

    # 並列実装可能グループ
    parallel_groups = analyzer.get_parallel_implementation_groups()
    if parallel_groups:
        print(f"\n⚡ 並列実装可能: {len(parallel_groups)}グループ")
