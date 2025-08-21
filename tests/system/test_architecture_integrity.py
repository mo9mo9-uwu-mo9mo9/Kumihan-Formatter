"""アーキテクチャ整合性のシステム統合テスト

新実装パターンの統合確認とシステム全体の構造的整合性をテストし、
設計原則の遵守を確認する。
"""

import ast
import importlib
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pytest

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestArchitectureIntegrity:
    """アーキテクチャ整合性のテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.project_root = Path(__file__).parent.parent.parent
        self.kumihan_root = self.project_root / "kumihan_formatter"
        logger.info(f"プロジェクトルート: {self.project_root}")

    def discover_modules(self, base_path: Path) -> List[Path]:
        """モジュールを発見"""
        python_files = []
        for py_file in base_path.rglob("*.py"):
            if py_file.name != "__init__.py" and not py_file.name.startswith("test_"):
                python_files.append(py_file)
        return python_files

    def analyze_module_structure(self, module_path: Path) -> Dict[str, Any]:
        """モジュール構造を解析"""
        try:
            with open(module_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            analysis = {
                "path": module_path,
                "classes": [],
                "functions": [],
                "imports": [],
                "docstring": ast.get_docstring(tree),
                "line_count": len(content.split("\n")),
                "complexity_indicators": {
                    "class_count": 0,
                    "function_count": 0,
                    "import_count": 0,
                    "nested_depth": 0,
                },
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis["classes"].append(
                        {
                            "name": node.name,
                            "methods": [
                                n.name
                                for n in node.body
                                if isinstance(n, ast.FunctionDef)
                            ],
                            "bases": [
                                b.id if isinstance(b, ast.Name) else str(b)
                                for b in node.bases
                            ],
                            "line_number": node.lineno,
                        }
                    )
                    analysis["complexity_indicators"]["class_count"] += 1

                elif isinstance(node, ast.FunctionDef):
                    if not any(
                        node.lineno >= cls["line_number"]
                        for cls in analysis["classes"]
                        if any(
                            node.lineno >= cls["line_number"]
                            for cls in analysis["classes"]
                        )
                    ):
                        analysis["functions"].append(
                            {
                                "name": node.name,
                                "args": [arg.arg for arg in node.args.args],
                                "line_number": node.lineno,
                                "is_async": isinstance(node, ast.AsyncFunctionDef),
                            }
                        )
                    analysis["complexity_indicators"]["function_count"] += 1

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(
                            {
                                "type": "import",
                                "module": alias.name,
                                "alias": alias.asname,
                            }
                        )
                    analysis["complexity_indicators"]["import_count"] += 1

                elif isinstance(node, ast.ImportFrom):
                    analysis["imports"].append(
                        {
                            "type": "from_import",
                            "module": node.module,
                            "names": [alias.name for alias in node.names],
                            "level": node.level,
                        }
                    )
                    analysis["complexity_indicators"]["import_count"] += 1

            return analysis

        except Exception as e:
            logger.error(f"モジュール解析エラー ({module_path}): {e}")
            return {
                "path": module_path,
                "error": str(e),
                "classes": [],
                "functions": [],
                "imports": [],
            }

    def check_naming_conventions(self, analysis: Dict[str, Any]) -> List[str]:
        """命名規則チェック"""
        violations = []

        # クラス名チェック（PascalCase）
        for cls in analysis["classes"]:
            if not cls["name"][0].isupper():
                violations.append(
                    f"クラス名 '{cls['name']}' はPascalCaseではありません"
                )

        # 関数名チェック（snake_case）
        for func in analysis["functions"]:
            if not func["name"].islower() or " " in func["name"]:
                if not func["name"].startswith("_"):  # プライベート関数は除外
                    violations.append(
                        f"関数名 '{func['name']}' はsnake_caseではありません"
                    )

        return violations

    def check_design_patterns(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """設計パターンの確認"""
        patterns = {
            "factory": [],
            "strategy": [],
            "observer": [],
            "singleton": [],
            "dependency_injection": [],
        }

        for cls in analysis["classes"]:
            class_name_lower = cls["name"].lower()

            # Factory パターン
            if "factory" in class_name_lower or "creator" in class_name_lower:
                patterns["factory"].append(cls["name"])

            # Strategy パターン
            if "strategy" in class_name_lower or "policy" in class_name_lower:
                patterns["strategy"].append(cls["name"])

            # Observer パターン
            if "observer" in class_name_lower or "listener" in class_name_lower:
                patterns["observer"].append(cls["name"])

            # Singleton パターン（メソッド名で推測）
            singleton_methods = ["instance", "get_instance", "__new__"]
            if any(method in cls["methods"] for method in singleton_methods):
                patterns["singleton"].append(cls["name"])

            # Dependency Injection パターン
            if "injector" in class_name_lower or "container" in class_name_lower:
                patterns["dependency_injection"].append(cls["name"])

        return patterns

    def check_module_cohesion(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """モジュール凝集度チェック"""
        complexity = analysis["complexity_indicators"]

        # 凝集度指標の計算
        cohesion_score = 1.0

        # 行数による減点
        if complexity.get("line_count", 0) > 200:
            cohesion_score -= 0.2
        if complexity.get("line_count", 0) > 500:
            cohesion_score -= 0.3

        # クラス数による減点
        if complexity["class_count"] > 3:
            cohesion_score -= 0.1
        if complexity["class_count"] > 5:
            cohesion_score -= 0.2

        # 関数数による減点
        if complexity["function_count"] > 10:
            cohesion_score -= 0.1
        if complexity["function_count"] > 20:
            cohesion_score -= 0.2

        cohesion_score = max(0.0, cohesion_score)

        return {
            "score": cohesion_score,
            "line_count": complexity.get("line_count", 0),
            "class_count": complexity["class_count"],
            "function_count": complexity["function_count"],
            "import_count": complexity["import_count"],
            "assessment": self._assess_cohesion(cohesion_score),
        }

    def _assess_cohesion(self, score: float) -> str:
        """凝集度の評価"""
        if score >= 0.8:
            return "優秀"
        elif score >= 0.6:
            return "良好"
        elif score >= 0.4:
            return "普通"
        else:
            return "要改善"

    def check_layer_separation(
        self, modules: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """レイヤー分離チェック"""
        layers = {
            "core": [],
            "parsing": [],
            "rendering": [],
            "cli": [],
            "utilities": [],
            "config": [],
            "other": [],
        }

        for module in modules:
            module_path = str(module["path"])

            if "/core/" in module_path:
                if "/parsing/" in module_path:
                    layers["parsing"].append(module_path)
                elif "/rendering/" in module_path:
                    layers["rendering"].append(module_path)
                elif "/utilities/" in module_path:
                    layers["utilities"].append(module_path)
                elif "/config/" in module_path:
                    layers["config"].append(module_path)
                else:
                    layers["core"].append(module_path)
            elif "/cli" in module_path:
                layers["cli"].append(module_path)
            else:
                layers["other"].append(module_path)

        return layers

    @pytest.mark.system
    def test_アーキテクチャ整合性_全体構造(self) -> None:
        """アーキテクチャ整合性: 全体構造の確認"""
        # Given: プロジェクト全体
        if not self.kumihan_root.exists():
            pytest.skip(
                f"Kumihanルートディレクトリが見つかりません: {self.kumihan_root}"
            )

        # When: モジュール発見と解析
        modules = self.discover_modules(self.kumihan_root)
        analyses = [self.analyze_module_structure(mod) for mod in modules]

        # Then: 構造確認
        assert len(modules) > 0, "プロジェクトモジュールが発見されていない"
        assert len(analyses) > 0, "モジュール解析結果がない"

        # エラーがないことを確認
        error_modules = [a for a in analyses if "error" in a]
        assert (
            len(error_modules) == 0
        ), f"解析エラーモジュール: {[a['path'] for a in error_modules]}"

        logger.info(f"アーキテクチャ整合性確認完了: {len(modules)}モジュール解析")

    @pytest.mark.system
    def test_アーキテクチャ整合性_命名規則(self) -> None:
        """アーキテクチャ整合性: 命名規則の確認"""
        # Given: 主要モジュール
        core_modules = self.discover_modules(self.kumihan_root / "core")

        if not core_modules:
            pytest.skip("coreモジュールが見つかりません")

        # When: 命名規則チェック
        total_violations = []
        for module in core_modules[:10]:  # 最初の10モジュールをチェック
            analysis = self.analyze_module_structure(module)
            violations = self.check_naming_conventions(analysis)
            total_violations.extend(violations)

        # Then: 命名規則確認
        violation_ratio = len(total_violations) / max(len(core_modules), 1)
        assert (
            violation_ratio < 0.3
        ), f"命名規則違反が多すぎます: {len(total_violations)}件"

        if total_violations:
            logger.warning(f"命名規則違反: {total_violations[:5]}")  # 最初の5件のみログ

        logger.info(f"命名規則確認完了: {len(total_violations)}件の違反")

    @pytest.mark.system
    def test_アーキテクチャ整合性_設計パターン(self) -> None:
        """アーキテクチャ整合性: 設計パターンの確認"""
        # Given: パターンディレクトリ
        patterns_dir = self.kumihan_root / "core" / "patterns"

        if not patterns_dir.exists():
            logger.info("patternsディレクトリが存在しないため、スキップ")
            pytest.skip("patternsディレクトリが見つかりません")

        # When: 設計パターン解析
        pattern_modules = self.discover_modules(patterns_dir)
        pattern_implementations = {}

        for module in pattern_modules:
            analysis = self.analyze_module_structure(module)
            patterns = self.check_design_patterns(analysis)
            for pattern_type, implementations in patterns.items():
                if implementations:
                    if pattern_type not in pattern_implementations:
                        pattern_implementations[pattern_type] = []
                    pattern_implementations[pattern_type].extend(implementations)

        # Then: 設計パターン確認
        expected_patterns = ["factory", "strategy", "dependency_injection"]
        found_patterns = list(pattern_implementations.keys())

        pattern_coverage = len(set(expected_patterns) & set(found_patterns)) / len(
            expected_patterns
        )
        assert (
            pattern_coverage >= 0.5
        ), f"設計パターンカバレッジが低い: {pattern_coverage:.2f}"

        logger.info(f"設計パターン確認完了: {len(found_patterns)}パターン実装")

    @pytest.mark.system
    def test_アーキテクチャ整合性_モジュール凝集度(self) -> None:
        """アーキテクチャ整合性: モジュール凝集度の確認"""
        # Given: 主要モジュール
        core_modules = self.discover_modules(self.kumihan_root / "core")[
            :15
        ]  # 最初の15モジュール

        if not core_modules:
            pytest.skip("coreモジュールが見つかりません")

        # When: 凝集度解析
        cohesion_results = []
        for module in core_modules:
            analysis = self.analyze_module_structure(module)
            cohesion = self.check_module_cohesion(analysis)
            cohesion_results.append(cohesion)

        # Then: 凝集度確認
        avg_score = sum(r["score"] for r in cohesion_results) / len(cohesion_results)
        assert avg_score >= 0.6, f"平均凝集度が低い: {avg_score:.3f}"

        # 低凝集度モジュールの確認
        low_cohesion = [r for r in cohesion_results if r["score"] < 0.5]
        assert (
            len(low_cohesion) <= len(cohesion_results) * 0.2
        ), f"低凝集度モジュールが多すぎます: {len(low_cohesion)}件"

        logger.info(f"モジュール凝集度確認完了: 平均スコア {avg_score:.3f}")

    @pytest.mark.system
    def test_アーキテクチャ整合性_レイヤー分離(self) -> None:
        """アーキテクチャ整合性: レイヤー分離の確認"""
        # Given: 全モジュール
        all_modules = self.discover_modules(self.kumihan_root)
        analyses = [self.analyze_module_structure(mod) for mod in all_modules]

        # When: レイヤー分離チェック
        layers = self.check_layer_separation(analyses)

        # Then: レイヤー分離確認
        # 主要レイヤーの存在確認
        essential_layers = ["core", "parsing", "rendering"]
        for layer in essential_layers:
            assert (
                len(layers[layer]) > 0
            ), f"必須レイヤー '{layer}' にモジュールがありません"

        # レイヤー分散の確認
        total_modules = sum(len(modules) for modules in layers.values())
        layer_distribution = {k: len(v) / total_modules for k, v in layers.items() if v}

        # コアレイヤーが支配的でないことを確認
        assert layer_distribution.get("core", 0) < 0.7, "coreレイヤーが支配的すぎます"

        logger.info(
            f"レイヤー分離確認完了: {len(layers)}レイヤー、{total_modules}モジュール"
        )

    @pytest.mark.system
    def test_アーキテクチャ整合性_依存関係循環(self) -> None:
        """アーキテクチャ整合性: 依存関係循環の確認"""
        # Given: 主要モジュール
        core_modules = self.discover_modules(self.kumihan_root / "core")[:10]

        if not core_modules:
            pytest.skip("coreモジュールが見つかりません")

        # When: インポート関係解析
        import_graph = {}
        for module in core_modules:
            analysis = self.analyze_module_structure(module)
            module_name = (
                str(module.relative_to(self.kumihan_root))
                .replace("/", ".")
                .replace(".py", "")
            )

            imports = []
            for imp in analysis["imports"]:
                if imp["type"] == "from_import" and imp["module"]:
                    if imp["module"].startswith("kumihan_formatter"):
                        imports.append(imp["module"])
                elif imp["type"] == "import":
                    if imp["module"].startswith("kumihan_formatter"):
                        imports.append(imp["module"])

            import_graph[module_name] = imports

        # Then: 循環依存チェック
        cycles = self._detect_cycles(import_graph)
        assert len(cycles) == 0, f"循環依存が検出されました: {cycles}"

        logger.info(f"依存関係循環確認完了: {len(import_graph)}モジュール、循環なし")

    def _detect_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """依存関係グラフから循環を検出"""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # 循環発見
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor in graph:  # グラフに存在するノードのみ
                    dfs(neighbor, path + [neighbor])

            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [node])

        return cycles

    @pytest.mark.system
    def test_アーキテクチャ整合性_コードメトリクス(self) -> None:
        """アーキテクチャ整合性: コードメトリクスの確認"""
        # Given: 全モジュール
        all_modules = self.discover_modules(self.kumihan_root)[
            :20
        ]  # 最初の20モジュール

        # When: メトリクス収集
        metrics = {
            "total_files": len(all_modules),
            "total_lines": 0,
            "total_classes": 0,
            "total_functions": 0,
            "large_files": [],
            "complex_files": [],
        }

        for module in all_modules:
            analysis = self.analyze_module_structure(module)
            if "error" not in analysis:
                line_count = analysis.get("line_count", 0)
                class_count = len(analysis["classes"])
                function_count = len(analysis["functions"])

                metrics["total_lines"] += line_count
                metrics["total_classes"] += class_count
                metrics["total_functions"] += function_count

                # 大きなファイルの検出
                if line_count > 300:
                    metrics["large_files"].append((str(module), line_count))

                # 複雑なファイルの検出
                if class_count > 5 or function_count > 15:
                    metrics["complex_files"].append(
                        (str(module), class_count, function_count)
                    )

        # Then: メトリクス確認
        avg_lines = (
            metrics["total_lines"] / metrics["total_files"]
            if metrics["total_files"] > 0
            else 0
        )
        assert avg_lines < 250, f"平均ファイルサイズが大きすぎます: {avg_lines:.1f}行"

        # 大きなファイルの割合確認
        large_file_ratio = len(metrics["large_files"]) / metrics["total_files"]
        assert (
            large_file_ratio < 0.2
        ), f"大きなファイルの割合が高い: {large_file_ratio:.2f}"

        # 複雑なファイルの割合確認
        complex_file_ratio = len(metrics["complex_files"]) / metrics["total_files"]
        assert (
            complex_file_ratio < 0.3
        ), f"複雑なファイルの割合が高い: {complex_file_ratio:.2f}"

        logger.info(
            f"コードメトリクス確認完了: {metrics['total_files']}ファイル、"
            f"平均{avg_lines:.1f}行、{len(metrics['large_files'])}大きなファイル"
        )
