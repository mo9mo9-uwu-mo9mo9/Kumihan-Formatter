#!/usr/bin/env python3
"""
循環依存分析ツール
モジュール間の依存関係を分析し、循環依存を検出する
"""

import ast
import os
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Set, Tuple


class CircularDependencyAnalyzer:
    """循環依存分析器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.circular_deps: List[List[str]] = []

    def analyze_file(self, filepath: Path) -> Set[str]:
        """単一ファイルの依存関係を分析"""
        dependencies = set()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('kumihan_formatter'):
                            dependencies.add(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith('kumihan_formatter'):
                        dependencies.add(node.module)
                        
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
            
        return dependencies

    def build_dependency_graph(self) -> None:
        """依存関係グラフを構築"""
        # kumihan_formatter内の全Pythonファイルを解析
        for py_file in self.project_root.rglob("kumihan_formatter/**/*.py"):
            if py_file.name == "__init__.py":
                continue
                
            # モジュール名を生成
            rel_path = py_file.relative_to(self.project_root)
            module_parts = rel_path.parts[:-1]  # kumihan_formatter以下のパス
            if py_file.stem != "__init__":
                module_parts += (py_file.stem,)
            
            module_name = ".".join(module_parts)
            
            # 依存関係を分析
            deps = self.analyze_file(py_file)
            self.dependencies[module_name] = deps

    def find_cycles_dfs(self) -> List[List[str]]:
        """DFSを使用して循環依存を検出"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # 循環発見
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
                
            if node in visited:
                return
                
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependencies.get(node, set()):
                dfs(neighbor, path.copy())
                
            rec_stack.remove(node)
        
        for module in self.dependencies:
            if module not in visited:
                dfs(module, [])
                
        return cycles

    def analyze_circular_dependencies(self) -> Dict[str, any]:
        """循環依存の全体分析"""
        self.build_dependency_graph()
        cycles = self.find_cycles_dfs()
        
        # 統計情報
        stats = {
            'total_modules': len(self.dependencies),
            'total_dependencies': sum(len(deps) for deps in self.dependencies.values()),
            'cycles_found': len(cycles),
            'cycles': cycles,
            'top_dependent_modules': [],
            'dependency_graph': dict(self.dependencies)
        }
        
        # 最も依存の多いモジュール Top 10
        dep_counts = [(module, len(deps)) for module, deps in self.dependencies.items()]
        dep_counts.sort(key=lambda x: x[1], reverse=True)
        stats['top_dependent_modules'] = dep_counts[:10]
        
        return stats

    def generate_report(self) -> str:
        """分析レポートを生成"""
        stats = self.analyze_circular_dependencies()
        
        report = []
        report.append("=" * 60)
        report.append("CIRCULAR DEPENDENCY ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"総モジュール数: {stats['total_modules']}")
        report.append(f"総依存関係数: {stats['total_dependencies']}")
        report.append(f"循環依存の数: {stats['cycles_found']}")
        report.append("")
        
        if stats['cycles']:
            report.append("🔴 検出された循環依存:")
            report.append("-" * 40)
            for i, cycle in enumerate(stats['cycles'], 1):
                report.append(f"{i}. {' → '.join(cycle)}")
            report.append("")
        else:
            report.append("✅ 循環依存は検出されませんでした")
            report.append("")
        
        report.append("📊 依存関係の多いモジュール Top 10:")
        report.append("-" * 40)
        for module, count in stats['top_dependent_modules']:
            report.append(f"{count:3d} dependencies: {module}")
        
        return "\n".join(report)


if __name__ == "__main__":
    analyzer = CircularDependencyAnalyzer("/Users/m2_macbookair_3911/GitHub/Kumihan-Formatter")
    print(analyzer.generate_report())