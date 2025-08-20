"""
インポート最適化

インポート文の分析・最適化による
起動時間短縮システム
"""

import ast
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class ImportAnalyzer:
    """インポート分析・最適化クラス"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.import_stats: Dict[str, Dict[str, Any]] = {}
        self.unused_imports: Dict[str, List[str]] = {}
        self.circular_imports: List[Tuple[str, str]] = []

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """単一ファイルのインポート分析"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))

            analysis = {
                "file_path": str(file_path),
                "imports": self._extract_imports(tree),
                "used_names": self._extract_used_names(tree),
                "import_order_issues": self._check_import_order(tree),
                "optimization_suggestions": [],
            }

            # 未使用インポート検出
            unused = self._find_unused_imports(
                analysis["imports"], analysis["used_names"]
            )
            if unused:
                analysis["unused_imports"] = unused
                analysis["optimization_suggestions"].append(
                    f"未使用インポート {len(unused)}個を削除可能"
                )

            # インポート順序チェック
            if analysis["import_order_issues"]:
                analysis["optimization_suggestions"].append(
                    "PEP8準拠のインポート順序への修正を推奨"
                )

            self.import_stats[str(file_path)] = analysis
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return {"error": str(e), "file_path": str(file_path)}

    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """インポート文抽出"""
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
                            "level": 0,
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                level = node.level or 0

                for alias in node.names:
                    imports.append(
                        {
                            "type": "from_import",
                            "module": module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                            "level": level,
                        }
                    )

        return imports

    def _extract_used_names(self, tree: ast.AST) -> Set[str]:
        """使用されている名前を抽出"""
        used_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # a.b の形式で使用されている場合
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        return used_names

    def _find_unused_imports(
        self, imports: List[Dict[str, Any]], used_names: Set[str]
    ) -> List[str]:
        """未使用インポート検出"""
        unused = []

        for imp in imports:
            if imp["type"] == "import":
                # import module_name [as alias]
                name = imp["alias"] or imp["module"].split(".")[0]
                if name not in used_names:
                    unused.append(f"import {imp['module']}")

            elif imp["type"] == "from_import":
                # from module import name [as alias]
                name = imp["alias"] or imp["name"]
                if name not in used_names and imp["name"] != "*":
                    unused.append(f"from {imp['module']} import {imp['name']}")

        return unused

    def _check_import_order(self, tree: ast.AST) -> List[str]:
        """インポート順序チェック（PEP8準拠）"""
        imports = []
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append((node.lineno, node))

        imports.sort(key=lambda x: x[0])  # 行番号順

        # PEP8順序: 標準ライブラリ → サードパーティ → ローカル
        current_group = 0
        prev_line = 0

        for line_no, node in imports:
            group = self._get_import_group(node)

            if group < current_group:
                issues.append(f"Line {line_no}: インポート順序が正しくありません")

            current_group = max(current_group, group)

            # 連続するインポート間の空行チェック
            if prev_line > 0 and line_no - prev_line > 2:
                issues.append(f"Line {line_no}: インポート間の空行が多すぎます")

            prev_line = line_no

        return issues

    def _get_import_group(self, node: ast.AST) -> int:
        """インポートグループ判定 (0:標準, 1:サードパーティ, 2:ローカル)"""
        if isinstance(node, ast.Import):
            module = node.names[0].name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level > 0:  # 相対インポート
                return 2
        else:
            return 1

        # 標準ライブラリ判定（簡易版）
        stdlib_modules = {
            "os",
            "sys",
            "json",
            "time",
            "datetime",
            "pathlib",
            "typing",
            "collections",
            "functools",
            "itertools",
            "re",
            "urllib",
            "xml",
            "ast",
            "importlib",
            "argparse",
            "logging",
            "unittest",
            "threading",
        }

        root_module = module.split(".")[0]

        if root_module in stdlib_modules:
            return 0  # 標準ライブラリ
        elif module.startswith(str(self.project_root.name)) or module.startswith("."):
            return 2  # ローカル
        else:
            return 1  # サードパーティ

    def analyze_project(self, file_patterns: List[str] = None) -> Dict[str, Any]:
        """プロジェクト全体のインポート分析"""
        if file_patterns is None:
            file_patterns = ["**/*.py"]

        all_files = []
        for pattern in file_patterns:
            all_files.extend(self.project_root.glob(pattern))

        analyzed_files = 0
        total_imports = 0
        total_unused = 0

        start_time = time.time()

        for file_path in all_files:
            if file_path.is_file() and not self._should_skip_file(file_path):
                analysis = self.analyze_file(file_path)
                if "imports" in analysis:
                    analyzed_files += 1
                    total_imports += len(analysis["imports"])
                    total_unused += len(analysis.get("unused_imports", []))

        analysis_time = time.time() - start_time

        return {
            "project_root": str(self.project_root),
            "analyzed_files": analyzed_files,
            "total_imports": total_imports,
            "total_unused_imports": total_unused,
            "analysis_time": analysis_time,
            "optimization_potential": self._calculate_optimization_potential(),
            "recommendations": self._generate_recommendations(),
        }

    def _should_skip_file(self, file_path: Path) -> bool:
        """スキップすべきファイル判定"""
        skip_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache",
            "node_modules",
            "venv",
            ".venv",
            "env",
            ".env",
            "build",
            "dist",
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _calculate_optimization_potential(self) -> Dict[str, Any]:
        """最適化効果予測"""
        total_files = len(self.import_stats)
        files_with_unused = sum(
            1 for stats in self.import_stats.values() if stats.get("unused_imports")
        )

        total_unused = sum(
            len(stats.get("unused_imports", [])) for stats in self.import_stats.values()
        )

        # 簡易的な時間削減予測
        estimated_time_saving = total_unused * 0.001  # 1ms per unused import

        return {
            "files_with_optimization": files_with_unused,
            "total_files": total_files,
            "optimization_ratio": (
                files_with_unused / total_files if total_files > 0 else 0
            ),
            "unused_imports_count": total_unused,
            "estimated_time_saving_seconds": estimated_time_saving,
            "estimated_startup_improvement": f"{estimated_time_saving * 100:.1f}ms",
        }

    def _generate_recommendations(self) -> List[str]:
        """最適化推奨事項生成"""
        recommendations = []

        potential = self._calculate_optimization_potential()

        if potential["unused_imports_count"] > 0:
            recommendations.append(
                f"{potential['unused_imports_count']}個の未使用インポートを削除することで、"
                f"起動時間を約{potential['estimated_startup_improvement']}短縮可能"
            )

        order_issues = sum(
            len(stats.get("import_order_issues", []))
            for stats in self.import_stats.values()
        )

        if order_issues > 0:
            recommendations.append(
                f"{order_issues}個のインポート順序問題を修正することで、"
                "コード可読性と保守性が向上"
            )

        if potential["optimization_ratio"] > 0.3:
            recommendations.append(
                "プロジェクト全体でインポート最適化を実施することを強く推奨"
            )

        return recommendations

    def generate_optimization_script(self, output_path: Path) -> None:
        """最適化スクリプト生成"""
        try:
            os.makedirs("tmp", exist_ok=True)

            script_content = []
            script_content.append("#!/usr/bin/env python3")
            script_content.append('"""自動生成されたインポート最適化スクリプト"""')
            script_content.append("")
            script_content.append("import os")
            script_content.append("import re")
            script_content.append("from pathlib import Path")
            script_content.append("")

            for file_path, stats in self.import_stats.items():
                unused_imports = stats.get("unused_imports", [])
                if unused_imports:
                    script_content.append(f"# {file_path}")
                    script_content.append(f"def optimize_{hash(file_path) % 10000}():")
                    script_content.append(f'    """Optimize {file_path}"""')
                    script_content.append(f'    file_path = Path("{file_path}")')
                    script_content.append("    if not file_path.exists():")
                    script_content.append("        return")
                    script_content.append("    ")
                    script_content.append('    with open(file_path, "r") as f:')
                    script_content.append("        content = f.read()")
                    script_content.append("    ")

                    for unused in unused_imports:
                        # エスケープ処理
                        escaped = unused.replace("\\", "\\\\").replace('"', '\\"')
                        script_content.append(f"    # Remove: {escaped}")
                        pattern = (
                            unused.replace("(", "\\(")
                            .replace(")", "\\)")
                            .replace(".", "\\.")
                        )
                        script_content.append(
                            f'    content = re.sub(r"^{pattern}\\n", "", content, '
                            f"flags=re.MULTILINE)"
                        )

                    script_content.append("    ")
                    script_content.append('    with open(file_path, "w") as f:')
                    script_content.append("        f.write(content)")
                    script_content.append('    print(f"Optimized {file_path}")')
                    script_content.append("")

            script_content.append("def main():")
            script_content.append('    """Execute all optimizations"""')
            for file_path in self.import_stats.keys():
                if self.import_stats[file_path].get("unused_imports"):
                    script_content.append(f"    optimize_{hash(file_path) % 10000}()")
            script_content.append("")
            script_content.append('if __name__ == "__main__":')
            script_content.append("    main()")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(script_content))

            logger.info(f"Optimization script generated: {output_path}")

        except Exception as e:
            logger.error(f"Failed to generate optimization script: {e}")
            raise


def benchmark_import_performance(module_names: List[str]) -> Dict[str, Any]:
    """インポートパフォーマンスベンチマーク"""
    results = {}

    for module_name in module_names:
        times = []

        for _ in range(5):
            # キャッシュクリア
            if module_name in sys.modules:
                del sys.modules[module_name]

            start_time = time.time()
            try:
                __import__(module_name)
                import_time = time.time() - start_time
                times.append(import_time)
            except ImportError as e:
                results[module_name] = {"error": str(e)}
                continue

        if times:
            results[module_name] = {
                "avg_time": sum(times) / len(times),
                "min_time": min(times),
                "max_time": max(times),
                "total_time": sum(times),
            }

    return results


def main():
    """CLI エントリーポイント"""
    import argparse
    import json

    os.makedirs("tmp", exist_ok=True)

    parser = argparse.ArgumentParser(description="Import optimizer")
    parser.add_argument("--analyze", type=str, help="Analyze file or directory")
    parser.add_argument("--project", action="store_true", help="Analyze entire project")
    parser.add_argument(
        "--generate-script", action="store_true", help="Generate optimization script"
    )
    parser.add_argument("--benchmark", nargs="+", help="Benchmark import performance")

    args = parser.parse_args()

    analyzer = ImportAnalyzer()

    if args.benchmark:
        print("Benchmarking import performance...")
        results = benchmark_import_performance(args.benchmark)

        benchmark_path = "tmp/import_benchmark.json"
        with open(benchmark_path, "w") as f:
            json.dump(results, f, indent=2)

        print(f"Benchmark results saved: {benchmark_path}")

        for module, stats in results.items():
            if "error" in stats:
                print(f"{module}: Error - {stats['error']}")
            else:
                print(f"{module}: {stats['avg_time']:.4f}s (avg)")

    elif args.project:
        print("Analyzing entire project...")
        results = analyzer.analyze_project()

        report_path = "tmp/import_analysis_report.json"
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"Analysis report saved: {report_path}")
        print(f"Analyzed files: {results['analyzed_files']}")
        print(f"Total imports: {results['total_imports']}")
        print(f"Unused imports: {results['total_unused_imports']}")
        print(
            f"Estimated improvement: "
            f"{results['optimization_potential']['estimated_startup_improvement']}"
        )

        if args.generate_script:
            script_path = Path("tmp/optimize_imports.py")
            analyzer.generate_optimization_script(script_path)
            print(f"Optimization script generated: {script_path}")

    elif args.analyze:
        target_path = Path(args.analyze)
        if target_path.is_file():
            results = analyzer.analyze_file(target_path)
        else:
            print(f"File not found: {target_path}")
            return 1

        analysis_path = f"tmp/import_analysis_{target_path.stem}.json"
        with open(analysis_path, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"Analysis saved: {analysis_path}")

        if "unused_imports" in results:
            print(f"Unused imports found: {len(results['unused_imports'])}")
            for unused in results["unused_imports"]:
                print(f"  - {unused}")

    else:
        print("No action specified. Use --help for usage information.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
