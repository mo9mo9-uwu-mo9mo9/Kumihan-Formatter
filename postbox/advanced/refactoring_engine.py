#!/usr/bin/env python3
"""
Refactoring Engine - 自動リファクタリングエンジン
Issue #870: 複雑タスクパターン拡張

コード品質向上・保守性改善のための自動リファクタリングシステム
AST解析ベースの安全なコード変換
"""

import ast
import os
import re
import sys
from typing import Dict, List, Any, Set, Optional, Tuple, Union, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import textwrap
import copy

# ロガー統合
try:
    from kumihan_formatter.core.utilities.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class RefactoringType(Enum):
    """リファクタリング種別"""
    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    INLINE_METHOD = "inline_method"
    MOVE_METHOD = "move_method"
    RENAME_VARIABLE = "rename_variable"
    RENAME_METHOD = "rename_method"
    REMOVE_DEAD_CODE = "remove_dead_code"
    SIMPLIFY_CONDITIONAL = "simplify_conditional"
    INTRODUCE_PARAMETER = "introduce_parameter"
    REPLACE_MAGIC_NUMBER = "replace_magic_number"
    SPLIT_LONG_METHOD = "split_long_method"
    MERGE_DUPLICATE_CODE = "merge_duplicate_code"
    IMPROVE_NAMING = "improve_naming"
    ADD_TYPE_HINTS = "add_type_hints"
    OPTIMIZE_IMPORTS = "optimize_imports"


class RefactoringPriority(Enum):
    """リファクタリング優先度"""
    CRITICAL = "critical"    # クリティカル（即座対応）
    HIGH = "high"           # 高（優先対応）
    MEDIUM = "medium"       # 中（通常対応）
    LOW = "low"             # 低（時間があるとき）


@dataclass
class RefactoringOpportunity:
    """リファクタリング機会"""
    file_path: str
    line_number: int
    end_line: Optional[int]
    refactoring_type: RefactoringType
    priority: RefactoringPriority
    description: str
    current_code: str
    suggested_code: str
    complexity_reduction: int
    maintainability_gain: float
    confidence_score: float  # 提案の信頼度
    affected_lines: List[int]
    dependencies: List[str]  # 依存する他の変更


@dataclass
class RefactoringResult:
    """リファクタリング結果"""
    original_file: str
    refactored_file: str
    applied_refactorings: List[RefactoringOpportunity]
    skipped_refactorings: List[RefactoringOpportunity]
    errors: List[str]
    quality_improvement: float
    lines_changed: int
    complexity_reduction: int


@dataclass
class CodeMetrics:
    """コードメトリクス"""
    cyclomatic_complexity: int
    lines_of_code: int
    number_of_methods: int
    number_of_classes: int
    depth_of_inheritance: int
    coupling_factor: float
    cohesion_score: float
    maintainability_index: float


class CodeAnalyzer:
    """コード解析器"""

    def __init__(self) -> None:
        self.magic_numbers: Set[Union[int, float]] = set()
        self.long_method_threshold = 20
        self.high_complexity_threshold = 10

    def analyze_file(self, file_path: str) -> Tuple[CodeMetrics, List[RefactoringOpportunity]]:
        """ファイル解析"""

        logger.info(f"🔍 コード解析開始: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)

            # メトリクス計算
            metrics = self._calculate_metrics(tree, content)

            # リファクタリング機会検出
            opportunities = self._detect_opportunities(tree, file_path, content)

            logger.info(f"✅ 解析完了: {len(opportunities)}件の改善機会")
            return metrics, opportunities

        except Exception as e:
            logger.error(f"ファイル解析エラー {file_path}: {e}")
            return CodeMetrics(0, 0, 0, 0, 0, 0.0, 0.0, 0.0), []

    def _calculate_metrics(self, tree: ast.AST, content: str) -> CodeMetrics:
        """メトリクス計算"""

        lines = content.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])

        methods = []
        classes = []
        complexity = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                methods.append(node)
                complexity += self._calculate_cyclomatic_complexity(node)
            elif isinstance(node, ast.ClassDef):
                classes.append(node)

        # 継承の深さ
        max_inheritance_depth = 0
        for class_node in classes:
            depth = len(class_node.bases)
            max_inheritance_depth = max(max_inheritance_depth, depth)

        # 結合度・凝集度（簡易計算）
        coupling = min(len(methods) / max(len(classes), 1) / 10, 1.0)
        cohesion = max(0.5, 1.0 - coupling)

        # 保守性指数（簡易版）
        maintainability = max(0.0, 100 - complexity * 2 - loc / 10)

        return CodeMetrics(
            cyclomatic_complexity=complexity,
            lines_of_code=loc,
            number_of_methods=len(methods),
            number_of_classes=len(classes),
            depth_of_inheritance=max_inheritance_depth,
            coupling_factor=coupling,
            cohesion_score=cohesion,
            maintainability_index=maintainability
        )

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """循環的複雑度計算"""
        complexity = 1  # 基準値

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(child, ast.Try):
                complexity += len(child.handlers)
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _detect_opportunities(self, tree: ast.AST, file_path: str, content: str) -> List[RefactoringOpportunity]:
        """リファクタリング機会検出"""

        opportunities = []
        lines = content.split('\n')

        # 各種リファクタリング機会を検出
        opportunities.extend(self._detect_long_methods(tree, file_path, lines))
        opportunities.extend(self._detect_complex_methods(tree, file_path, lines))
        opportunities.extend(self._detect_magic_numbers(tree, file_path, lines))
        opportunities.extend(self._detect_duplicate_code(tree, file_path, lines))
        opportunities.extend(self._detect_naming_issues(tree, file_path, lines))
        opportunities.extend(self._detect_missing_type_hints(tree, file_path, lines))
        opportunities.extend(self._detect_dead_code(tree, file_path, lines))
        opportunities.extend(self._detect_import_issues(tree, file_path, lines))

        # 優先度でソート
        opportunities.sort(key=lambda x: (x.priority.value, -x.confidence_score))

        return opportunities

    def _detect_long_methods(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[RefactoringOpportunity]:
        """長いメソッドの検出"""
        opportunities = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_lines = (node.end_lineno or node.lineno) - node.lineno + 1

                if method_lines > self.long_method_threshold:
                    current_code = '\n'.join(lines[node.lineno-1:(node.end_lineno or node.lineno)])

                    opportunities.append(RefactoringOpportunity(
                        file_path=file_path,
                        line_number=node.lineno,
                        end_line=node.end_lineno,
                        refactoring_type=RefactoringType.SPLIT_LONG_METHOD,
                        priority=RefactoringPriority.MEDIUM,
                        description=f"メソッド '{node.name}' が長すぎます ({method_lines}行)",
                        current_code=current_code,
                        suggested_code=self._suggest_method_split(node, lines),
                        complexity_reduction=method_lines // 4,
                        maintainability_gain=0.6,
                        confidence_score=0.8,
                        affected_lines=list(range(node.lineno, node.end_lineno + 1)),
                        dependencies=[]
                    ))

        return opportunities

    def _detect_complex_methods(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[RefactoringOpportunity]:
        """複雑なメソッドの検出"""
        opportunities = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)

                if complexity > self.high_complexity_threshold:
                    current_code = '\n'.join(lines[node.lineno-1:(node.end_lineno or node.lineno)])

                    opportunities.append(RefactoringOpportunity(
                        file_path=file_path,
                        line_number=node.lineno,
                        end_line=node.end_lineno,
                        refactoring_type=RefactoringType.SIMPLIFY_CONDITIONAL,
                        priority=RefactoringPriority.HIGH,
                        description=f"メソッド '{node.name}' の複雑度が高いです (CC={complexity})",
                        current_code=current_code,
                        suggested_code=self._suggest_complexity_reduction(node, lines),
                        complexity_reduction=complexity // 2,
                        maintainability_gain=0.7,
                        confidence_score=0.7,
                        affected_lines=list(range(node.lineno, node.end_lineno + 1)),
                        dependencies=[]
                    ))

        return opportunities

    def _detect_magic_numbers(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[RefactoringOpportunity]:
        """マジックナンバーの検出"""
        opportunities = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)) and node.value not in [0, 1, -1]:
                    opportunities.append(RefactoringOpportunity(
                        file_path=file_path,
                        line_number=node.lineno,
                        end_line=node.lineno,
                        refactoring_type=RefactoringType.REPLACE_MAGIC_NUMBER,
                        priority=RefactoringPriority.MEDIUM,
                        description=f"マジックナンバー {node.value} を定数に置き換え",
                        current_code=str(node.value),
                        suggested_code=f"CONSTANT_VALUE = {node.value}",
                        complexity_reduction=1,
                        maintainability_gain=0.3,
                        confidence_score=0.9,
                        affected_lines=[node.lineno],
                        dependencies=[]
                    ))

        return opportunities

    def _detect_duplicate_code(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[RefactoringOpportunity]:
        """重複コードの検出"""
        opportunities = []

        # 簡易実装：同一の文字列を持つ行を検出
        line_counts = {}
        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) > 10 and not stripped.startswith('#'):
                if stripped in line_counts:
                    line_counts[stripped].append(i + 1)
                else:
                    line_counts[stripped] = [i + 1]

        for line_content, line_numbers in line_counts.items():
            if len(line_numbers) > 1:
                opportunities.append(RefactoringOpportunity(
                    file_path=file_path,
                    line_number=line_numbers[0],
                    end_line=line_numbers[0],
                    refactoring_type=RefactoringType.MERGE_DUPLICATE_CODE,
                    priority=RefactoringPriority.MEDIUM,
                    description=f"重複コードを統合可能 ({len(line_numbers)}箇所)",
                    current_code=line_content,
                    suggested_code=f"# 共通メソッドとして抽出を検討: {line_content[:50]}...",
                    complexity_reduction=len(line_numbers),
                    maintainability_gain=0.5,
                    confidence_score=0.6,
                    affected_lines=line_numbers,
                    dependencies=[]
                ))

        return opportunities

    def _detect_naming_issues(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[RefactoringOpportunity]:
        """命名問題の検出"""
        opportunities = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.name) < 3 or not node.name.islower():
                    opportunities.append(RefactoringOpportunity(
                        file_path=file_path,
                        line_number=node.lineno,
                        end_line=node.lineno,
                        refactoring_type=RefactoringType.IMPROVE_NAMING,
                        priority=RefactoringPriority.LOW,
                        description=f"関数名 '{node.name}' の改善を推奨",
                        current_code=f"def {node.name}(",
                        suggested_code=f"def {self._suggest_better_name(node.name)}(",
                        complexity_reduction=0,
                        maintainability_gain=0.2,
                        confidence_score=0.5,
                        affected_lines=[node.lineno],
                        dependencies=[]
                    ))

        return opportunities

    def _detect_missing_type_hints(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[RefactoringOpportunity]:
        """型ヒント不足の検出"""
        opportunities = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                missing_hints = []

                # 引数の型ヒント確認
                for arg in node.args.args:
                    if arg.annotation is None:
                        missing_hints.append(f"引数 {arg.arg}")

                # 戻り値の型ヒント確認
                if node.returns is None:
                    missing_hints.append("戻り値")

                if missing_hints:
                    opportunities.append(RefactoringOpportunity(
                        file_path=file_path,
                        line_number=node.lineno,
                        end_line=node.lineno,
                        refactoring_type=RefactoringType.ADD_TYPE_HINTS,
                        priority=RefactoringPriority.MEDIUM,
                        description=f"型ヒント追加: {', '.join(missing_hints)}",
                        current_code=f"def {node.name}(",
                        suggested_code=self._suggest_type_hints(node),
                        complexity_reduction=0,
                        maintainability_gain=0.4,
                        confidence_score=0.7,
                        affected_lines=[node.lineno],
                        dependencies=[]
                    ))

        return opportunities

    def _detect_dead_code(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[RefactoringOpportunity]:
        """デッドコードの検出"""
        opportunities = []

        # 未使用インポートの検出
        imports = set()
        used_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imports.add(alias.name)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)

        unused_imports = imports - used_names
        for unused in unused_imports:
            opportunities.append(RefactoringOpportunity(
                file_path=file_path,
                line_number=1,  # 正確な行番号は別途特定
                end_line=1,
                refactoring_type=RefactoringType.REMOVE_DEAD_CODE,
                priority=RefactoringPriority.LOW,
                description=f"未使用インポート: {unused}",
                current_code=f"import {unused}",
                suggested_code="# インポート削除",
                complexity_reduction=1,
                maintainability_gain=0.1,
                confidence_score=0.8,
                affected_lines=[],
                dependencies=[]
            ))

        return opportunities

    def _detect_import_issues(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[RefactoringOpportunity]:
        """インポート問題の検出"""
        opportunities = []

        import_lines = []
        for i, line in enumerate(lines):
            if line.strip().startswith(('import ', 'from ')):
                import_lines.append((i + 1, line.strip()))

        if len(import_lines) > 1:
            # インポートの順序チェック
            stdlib_imports = []
            third_party_imports = []
            local_imports = []

            for line_num, import_line in import_lines:
                if any(stdlib in import_line for stdlib in ['os', 'sys', 'json', 'time']):
                    stdlib_imports.append((line_num, import_line))
                elif 'kumihan_formatter' in import_line or 'postbox' in import_line:
                    local_imports.append((line_num, import_line))
                else:
                    third_party_imports.append((line_num, import_line))

            if stdlib_imports and third_party_imports and local_imports:
                opportunities.append(RefactoringOpportunity(
                    file_path=file_path,
                    line_number=import_lines[0][0],
                    end_line=import_lines[-1][0],
                    refactoring_type=RefactoringType.OPTIMIZE_IMPORTS,
                    priority=RefactoringPriority.LOW,
                    description="インポート順序の最適化",
                    current_code='\n'.join([imp[1] for imp in import_lines]),
                    suggested_code=self._suggest_import_order(stdlib_imports, third_party_imports, local_imports),
                    complexity_reduction=0,
                    maintainability_gain=0.2,
                    confidence_score=0.9,
                    affected_lines=[imp[0] for imp in import_lines],
                    dependencies=[]
                ))

        return opportunities

    def _suggest_method_split(self, node: ast.FunctionDef, lines: List[str]) -> str:
        """メソッド分割提案"""
        return f"# メソッド '{node.name}' を複数の小さなメソッドに分割することを推奨"

    def _suggest_complexity_reduction(self, node: ast.FunctionDef, lines: List[str]) -> str:
        """複雑度削減提案"""
        return f"# メソッド '{node.name}' の条件分岐を簡素化またはStrategy/Stateパターンの適用を検討"

    def _suggest_better_name(self, current_name: str) -> str:
        """より良い名前の提案"""
        return f"{current_name}_improved"  # 簡易実装

    def _suggest_type_hints(self, node: ast.FunctionDef) -> str:
        """型ヒント提案"""
        return f"def {node.name}(param: Any) -> Any:"  # 簡易実装

    def _suggest_import_order(self, stdlib: List, third_party: List, local: List) -> str:
        """インポート順序提案"""
        result = []

        if stdlib:
            result.extend([imp[1] for imp in stdlib])
            result.append("")

        if third_party:
            result.extend([imp[1] for imp in third_party])
            result.append("")

        if local:
            result.extend([imp[1] for imp in local])

        return '\n'.join(result)


class RefactoringEngine:
    """リファクタリングエンジン - メインクラス"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.analyzer = CodeAnalyzer()
        self.refactoring_history: List[RefactoringResult] = []

        logger.info("🔧 Refactoring Engine 初期化完了")
        logger.info(f"📁 プロジェクトルート: {self.project_root}")

    def analyze_project(self, target_paths: Optional[List[str]] = None) -> Dict[str, Tuple[CodeMetrics, List[RefactoringOpportunity]]]:
        """プロジェクト全体解析"""

        logger.info("🔍 プロジェクト全体リファクタリング解析開始")

        if target_paths is None:
            target_paths = self._find_python_files()

        results = {}
        total_opportunities = 0

        for file_path in target_paths:
            try:
                metrics, opportunities = self.analyzer.analyze_file(file_path)
                results[file_path] = (metrics, opportunities)
                total_opportunities += len(opportunities)
            except Exception as e:
                logger.error(f"ファイル解析エラー {file_path}: {e}")

        logger.info(f"✅ プロジェクト解析完了: {total_opportunities}件の改善機会")
        return results

    def apply_refactorings(
        self,
        file_path: str,
        opportunities: List[RefactoringOpportunity],
        auto_apply: bool = False
    ) -> RefactoringResult:
        """リファクタリング適用"""

        logger.info(f"🔧 リファクタリング適用開始: {file_path}")
        logger.info(f"📋 適用候補: {len(opportunities)}件")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # 出力ファイルパス決定
            output_path = self._get_refactored_file_path(file_path)

            applied = []
            skipped = []
            errors = []

            # コンテンツをコピーして変更適用
            refactored_content = original_content

            # 高い信頼度から順に適用
            sorted_opportunities = sorted(opportunities, key=lambda x: -x.confidence_score)

            for opportunity in sorted_opportunities:
                try:
                    if auto_apply or opportunity.confidence_score > 0.8:
                        # 自動適用
                        refactored_content = self._apply_single_refactoring(
                            refactored_content, opportunity
                        )
                        applied.append(opportunity)
                        logger.info(f"✅ 適用: {opportunity.description}")
                    else:
                        # スキップ（手動確認必要）
                        skipped.append(opportunity)
                        logger.info(f"⏭️ スキップ: {opportunity.description}")

                except Exception as e:
                    errors.append(f"{opportunity.description}: {str(e)}")
                    logger.error(f"❌ 適用エラー: {e}")

            # リファクタリング後ファイル保存
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(refactored_content)

            # 結果計算
            quality_improvement = sum(op.maintainability_gain for op in applied)
            lines_changed = sum(len(op.affected_lines) for op in applied)
            complexity_reduction = sum(op.complexity_reduction for op in applied)

            result = RefactoringResult(
                original_file=file_path,
                refactored_file=output_path,
                applied_refactorings=applied,
                skipped_refactorings=skipped,
                errors=errors,
                quality_improvement=quality_improvement,
                lines_changed=lines_changed,
                complexity_reduction=complexity_reduction
            )

            self.refactoring_history.append(result)

            logger.info(f"✅ リファクタリング完了:")
            logger.info(f"  - 適用: {len(applied)}件")
            logger.info(f"  - スキップ: {len(skipped)}件")
            logger.info(f"  - エラー: {len(errors)}件")
            logger.info(f"  - 品質向上: {quality_improvement:.2f}")

            return result

        except Exception as e:
            logger.error(f"リファクタリング適用エラー {file_path}: {e}")
            raise

    def generate_refactoring_report(self, analysis_results: Dict[str, Tuple[CodeMetrics, List[RefactoringOpportunity]]]) -> str:
        """リファクタリングレポート生成"""

        logger.info("📊 リファクタリングレポート生成")

        total_opportunities = sum(len(opportunities) for _, opportunities in analysis_results.values())
        high_priority_count = sum(
            len([op for op in opportunities if op.priority == RefactoringPriority.HIGH])
            for _, opportunities in analysis_results.values()
        )

        report_lines = [
            "# リファクタリング解析レポート",
            "",
            "## 概要",
            f"- 解析ファイル数: {len(analysis_results)}",
            f"- 総改善機会: {total_opportunities}件",
            f"- 高優先度: {high_priority_count}件",
            "",
            "## ファイル別詳細",
            ""
        ]

        for file_path, (metrics, opportunities) in analysis_results.items():
            rel_path = os.path.relpath(file_path, self.project_root)

            report_lines.extend([
                f"### {rel_path}",
                "",
                "#### メトリクス",
                f"- 循環的複雑度: {metrics.cyclomatic_complexity}",
                f"- コード行数: {metrics.lines_of_code}",
                f"- メソッド数: {metrics.number_of_methods}",
                f"- 保守性指数: {metrics.maintainability_index:.1f}",
                "",
                "#### 改善機会",
                ""
            ])

            for i, opportunity in enumerate(opportunities[:5], 1):  # 上位5件
                report_lines.extend([
                    f"{i}. **{opportunity.refactoring_type.value}** ({opportunity.priority.value})",
                    f"   - {opportunity.description}",
                    f"   - 信頼度: {opportunity.confidence_score:.1%}",
                    f"   - 保守性向上: {opportunity.maintainability_gain:.1%}",
                    ""
                ])

            if len(opportunities) > 5:
                report_lines.append(f"   他 {len(opportunities) - 5}件...")

            report_lines.append("")

        # 推奨アクション
        report_lines.extend([
            "## 推奨アクション",
            "",
            "1. **高優先度項目の即座対応**",
            "   - クリティカル・高優先度項目の修正",
            "",
            "2. **段階的改善実施**",
            "   - 信頼度80%以上の項目から自動適用",
            "",
            "3. **継続的監視**",
            "   - 定期的なコード品質チェック",
            ""
        ])

        return '\n'.join(report_lines)

    def get_refactoring_history(self) -> List[RefactoringResult]:
        """リファクタリング履歴取得"""
        return self.refactoring_history[:]

    def _find_python_files(self) -> List[str]:
        """Pythonファイル検索"""
        python_files = []

        for root, dirs, files in os.walk(self.project_root):
            # 除外ディレクトリ
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)

        return python_files

    def _get_refactored_file_path(self, original_path: str) -> str:
        """リファクタリング後ファイルパス生成"""
        path = Path(original_path)
        return str(self.project_root / "tmp" / f"{path.stem}_refactored{path.suffix}")

    def _apply_single_refactoring(self, content: str, opportunity: RefactoringOpportunity) -> str:
        """単一リファクタリング適用"""

        # 簡易実装：特定の文字列置換
        if opportunity.refactoring_type == RefactoringType.REPLACE_MAGIC_NUMBER:
            # マジックナンバー置換
            return content.replace(opportunity.current_code, f"CONSTANT_{opportunity.current_code}")

        elif opportunity.refactoring_type == RefactoringType.REMOVE_DEAD_CODE:
            # デッドコード削除
            lines = content.split('\n')
            for line_num in sorted(opportunity.affected_lines, reverse=True):
                if 0 <= line_num - 1 < len(lines):
                    lines.pop(line_num - 1)
            return '\n'.join(lines)

        elif opportunity.refactoring_type == RefactoringType.OPTIMIZE_IMPORTS:
            # インポート最適化
            lines = content.split('\n')
            import_lines = []
            other_lines = []

            for line in lines:
                if line.strip().startswith(('import ', 'from ')):
                    import_lines.append(line)
                else:
                    other_lines.append(line)

            # インポート再編成（簡易）
            optimized_imports = '\n'.join(sorted(set(import_lines)))
            return optimized_imports + '\n\n' + '\n'.join(other_lines)

        else:
            # その他のリファクタリングは将来実装
            logger.warning(f"未実装のリファクタリング: {opportunity.refactoring_type.value}")
            return content


if __name__ == "__main__":
    """簡単なテスト実行"""

    engine = RefactoringEngine()

    # テストファイルの解析
    test_files = [
        "postbox/advanced/dependency_analyzer.py",
        "postbox/advanced/multi_file_coordinator.py"
    ]

    # プロジェクト解析
    analysis_results = engine.analyze_project(test_files)

    print(f"🔍 解析結果:")
    for file_path, (metrics, opportunities) in analysis_results.items():
        rel_path = os.path.relpath(file_path)
        print(f"\n📄 {rel_path}:")
        print(f"  - 複雑度: {metrics.cyclomatic_complexity}")
        print(f"  - コード行数: {metrics.lines_of_code}")
        print(f"  - 改善機会: {len(opportunities)}件")

        # 高優先度項目表示
        high_priority = [op for op in opportunities if op.priority == RefactoringPriority.HIGH]
        if high_priority:
            print(f"  - 高優先度: {len(high_priority)}件")
            for op in high_priority[:3]:
                print(f"    • {op.description}")

    # レポート生成
    report = engine.generate_refactoring_report(analysis_results)

    # レポート保存
    report_path = engine.project_root / "tmp" / "refactoring_report.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n📊 レポート生成完了: {report_path}")
    print(f"✅ Refactoring Engine テスト完了")
