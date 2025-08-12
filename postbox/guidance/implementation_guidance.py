#!/usr/bin/env python3
"""
Implementation Guidance System for Gemini Capability Enhancement
段階的実装ガイドライン・エラーパターン回避システム
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import re


class GuidanceLevel(Enum):
    """ガイダンスレベル"""
    BASIC = "basic"           # 基本的な実装ガイド
    INTERMEDIATE = "intermediate"  # 中級者向けガイド
    ADVANCED = "advanced"     # 上級者向けガイド
    EXPERT = "expert"         # エキスパート向けガイド


class TaskComplexity(Enum):
    """タスク複雑度"""
    SIMPLE = "simple"         # 単純 (関数1個、基本的な修正)
    MODERATE = "moderate"     # 中程度 (複数関数、クラス修正)
    COMPLEX = "complex"       # 複雑 (モジュール全体、新機能)
    CRITICAL = "critical"     # 重要 (アーキテクチャレベル)


@dataclass
class ImplementationStep:
    """実装ステップ"""
    step_id: str
    title: str
    description: str
    code_example: str
    validation_criteria: List[str]
    common_errors: List[str]
    error_solutions: List[str]
    estimated_tokens: int
    dependencies: List[str]
    quality_checks: List[str]


@dataclass
class ErrorPattern:
    """エラーパターン"""
    pattern_id: str
    error_type: str
    description: str
    incorrect_examples: List[str]
    correct_examples: List[str]
    prevention_tips: List[str]
    detection_regex: List[str]
    severity: str


@dataclass
class QualityStandard:
    """品質基準"""
    standard_id: str
    name: str
    description: str
    criteria: List[str]
    validation_method: str
    acceptance_threshold: float


class ImplementationGuidanceEngine:
    """実装ガイダンスエンジン"""
    
    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.quality_standards = self._initialize_quality_standards()
        self.implementation_templates = self._initialize_implementation_templates()
        
    def generate_step_by_step_guidance(self, task_data: Dict[str, Any]) -> List[ImplementationStep]:
        """
        段階的実装ガイダンス生成
        
        Args:
            task_data: タスクデータ
            
        Returns:
            実装ステップのリスト
        """
        
        task_type = task_data.get('type', 'modification')
        complexity = self._analyze_task_complexity(task_data)
        target_files = task_data.get('target_files', [])
        
        print(f"🎯 実装ガイダンス生成: {task_type} (複雑度: {complexity.value})")
        
        steps = []
        
        # タスクタイプ別ステップ生成
        if task_type == 'new_implementation':
            steps = self._generate_new_implementation_steps(task_data, complexity)
        elif task_type == 'hybrid_implementation':
            steps = self._generate_hybrid_implementation_steps(task_data, complexity)
        elif task_type == 'modification':
            steps = self._generate_modification_steps(task_data, complexity)
        elif task_type == 'no-untyped-def':
            steps = self._generate_type_annotation_steps(task_data, complexity)
        else:
            steps = self._generate_generic_steps(task_data, complexity)
        
        # 品質チェックステップの追加
        steps.extend(self._generate_quality_assurance_steps(task_data, complexity))
        
        print(f"✅ ガイダンス生成完了: {len(steps)}ステップ")
        return steps
    
    def generate_error_avoidance_guide(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        エラー回避ガイド生成
        
        Args:
            task_data: タスクデータ
            
        Returns:
            エラー回避ガイド
        """
        
        task_type = task_data.get('type', 'modification')
        target_files = task_data.get('target_files', [])
        
        relevant_patterns = self._get_relevant_error_patterns(task_type, target_files)
        
        guide = {
            "task_type": task_type,
            "common_pitfalls": [],
            "prevention_strategies": [],
            "validation_checklist": [],
            "emergency_fixes": [],
            "pattern_specific_guidance": {}
        }
        
        for pattern in relevant_patterns:
            guide["common_pitfalls"].extend(pattern.incorrect_examples)
            guide["prevention_strategies"].extend(pattern.prevention_tips)
            guide["pattern_specific_guidance"][pattern.pattern_id] = {
                "description": pattern.description,
                "correct_examples": pattern.correct_examples,
                "detection_patterns": pattern.detection_regex,
                "severity": pattern.severity
            }
        
        # 汎用的な検証チェックリスト
        guide["validation_checklist"] = self._generate_validation_checklist(task_type)
        guide["emergency_fixes"] = self._generate_emergency_fixes(task_type)
        
        return guide
    
    def generate_quality_guidance(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        品質ガイダンス生成
        
        Args:
            task_data: タスクデータ
            
        Returns:
            品質ガイダンス
        """
        
        complexity = self._analyze_task_complexity(task_data)
        applicable_standards = self._get_applicable_quality_standards(task_data, complexity)
        
        guidance = {
            "complexity_level": complexity.value,
            "quality_targets": {},
            "validation_methods": [],
            "acceptance_criteria": [],
            "improvement_suggestions": []
        }
        
        for standard in applicable_standards:
            guidance["quality_targets"][standard.standard_id] = {
                "name": standard.name,
                "description": standard.description,
                "criteria": standard.criteria,
                "threshold": standard.acceptance_threshold
            }
            guidance["validation_methods"].append(standard.validation_method)
        
        guidance["acceptance_criteria"] = self._generate_acceptance_criteria(task_data, complexity)
        guidance["improvement_suggestions"] = self._generate_improvement_suggestions(task_data, complexity)
        
        return guidance
    
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """エラーパターン初期化"""
        
        patterns = [
            ErrorPattern(
                pattern_id="type_annotation_syntax",
                error_type="no-untyped-def",
                description="型注釈の構文エラー",
                incorrect_examples=[
                    "def function(param -> None: Type):",
                    "def function(param -> Type: None):",
                    "def function(param: -> Type):",
                    "def function(param) -> None: Type:",
                ],
                correct_examples=[
                    "def function(param: Any) -> None:",
                    "def function(param: Type) -> ReturnType:",
                    "def __init__(self, param: Any) -> None:",
                ],
                prevention_tips=[
                    "引数の型注釈は ': Type' の形式",
                    "返り値の型注釈は '-> Type:' の形式",
                    "わからない型は 'Any' を使用",
                    "必要に応じて 'from typing import Any' を追加"
                ],
                detection_regex=[
                    r"def\s+\w+\([^)]*->.*?:",
                    r"def\s+\w+\([^)]*:\s*->.*?:",
                    r"param\s*->\s*None\s*:",
                ],
                severity="high"
            ),
            
            ErrorPattern(
                pattern_id="import_missing",
                error_type="import-error",
                description="必要なimport文の欠如",
                incorrect_examples=[
                    "# typing.Any を使用しているが import していない",
                    "def function(param: Any) -> None:  # ImportError!",
                ],
                correct_examples=[
                    "from typing import Any\n\ndef function(param: Any) -> None:",
                    "from typing import Dict, List, Any",
                ],
                prevention_tips=[
                    "型注釈を追加した際は対応するimport文を確認",
                    "typing モジュールの適切なインポート",
                    "未使用のimport文は削除"
                ],
                detection_regex=[
                    r":\s*(Any|Dict|List|Optional|Union)\b",
                    r"->\s*(Any|Dict|List|Optional|Union)\b",
                ],
                severity="medium"
            ),
            
            ErrorPattern(
                pattern_id="indentation_error",
                error_type="syntax-error",
                description="インデンテーションエラー",
                incorrect_examples=[
                    "def function():\nreturn None  # インデント不足",
                    "    def function():\n  return None  # 不統一",
                ],
                correct_examples=[
                    "def function():\n    return None",
                    "class Example:\n    def method(self):\n        return None",
                ],
                prevention_tips=[
                    "一貫した4スペースインデント",
                    "タブと空白の混在を避ける",
                    "エディタの設定確認"
                ],
                detection_regex=[
                    r"\n[^\n\s]",  # 改行直後の非空白文字
                    r"\n\t",       # タブ文字
                ],
                severity="high"
            ),
            
            ErrorPattern(
                pattern_id="return_type_mismatch",
                error_type="type-error",
                description="返り値型の不一致",
                incorrect_examples=[
                    "def get_data() -> str:\n    return 42",
                    "def process() -> None:\n    return 'done'",
                ],
                correct_examples=[
                    "def get_data() -> str:\n    return 'data'",
                    "def process() -> None:\n    print('done')",
                    "def get_value() -> Any:\n    return 42",
                ],
                prevention_tips=[
                    "返り値の型と実際の戻り値を一致させる",
                    "不明な場合は Any を使用",
                    "None を返す関数は -> None を明記"
                ],
                detection_regex=[
                    r"->\s*None:.*?return\s+[^N]",
                    r"->\s*str:.*?return\s+\d",
                ],
                severity="medium"
            ),
        ]
        
        return patterns
    
    def _initialize_quality_standards(self) -> List[QualityStandard]:
        """品質基準初期化"""
        
        standards = [
            QualityStandard(
                standard_id="type_annotation_coverage",
                name="型注釈カバレッジ",
                description="全ての関数・メソッドに適切な型注釈が付与されている",
                criteria=[
                    "全ての関数定義に返り値型注釈がある",
                    "全ての引数に型注釈がある",
                    "適切な typing モジュールのインポート",
                ],
                validation_method="mypy --strict",
                acceptance_threshold=1.0
            ),
            
            QualityStandard(
                standard_id="syntax_correctness",
                name="構文正確性",
                description="Python構文エラーが存在しない",
                criteria=[
                    "Python構文解析が成功する",
                    "インデンテーションが正しい",
                    "括弧・引用符の対応が正しい",
                ],
                validation_method="python -m py_compile",
                acceptance_threshold=1.0
            ),
            
            QualityStandard(
                standard_id="import_organization",
                name="インポート整理",
                description="インポート文が適切に整理されている",
                criteria=[
                    "標準ライブラリ・サードパーティ・ローカルの順序",
                    "未使用インポートの除去",
                    "重複インポートの除去",
                ],
                validation_method="isort --check-only",
                acceptance_threshold=1.0
            ),
            
            QualityStandard(
                standard_id="code_formatting",
                name="コードフォーマット",
                description="一貫したコードフォーマットが適用されている",
                criteria=[
                    "Black フォーマッタに適合",
                    "行長制限の遵守（88文字）",
                    "一貫した引用符使用",
                ],
                validation_method="black --check",
                acceptance_threshold=1.0
            ),
            
            QualityStandard(
                standard_id="docstring_presence",
                name="ドキュメント文字列",
                description="適切なドキュメント文字列が存在する",
                criteria=[
                    "パブリック関数にdocstringがある",
                    "パブリッククラスにdocstringがある",
                    "モジュールレベルのdocstringがある",
                ],
                validation_method="pydocstyle",
                acceptance_threshold=0.8
            ),
        ]
        
        return standards
    
    def _initialize_implementation_templates(self) -> Dict[str, Any]:
        """実装テンプレート初期化"""
        
        return {
            "function_template": {
                "basic": '''
def {function_name}({parameters}) -> {return_type}:
    """{docstring}"""
    {implementation}
''',
                "with_error_handling": '''
def {function_name}({parameters}) -> {return_type}:
    """{docstring}"""
    try:
        {implementation}
    except Exception as e:
        logger.error(f"Error in {function_name}: {e}")
        raise
''',
            },
            
            "class_template": {
                "basic": '''
class {class_name}:
    """{docstring}"""
    
    def __init__(self{init_parameters}) -> None:
        """{init_docstring}"""
        {init_implementation}
    
    {methods}
''',
                "with_inheritance": '''
class {class_name}({base_classes}):
    """{docstring}"""
    
    def __init__(self{init_parameters}) -> None:
        """{init_docstring}"""
        super().__init__({super_parameters})
        {init_implementation}
    
    {methods}
''',
            },
            
            "type_annotation_fixes": {
                "no_args_no_return": "def {name}() -> None:",
                "args_no_return": "def {name}({args}: Any) -> None:",
                "no_args_return": "def {name}() -> Any:",
                "args_return": "def {name}({args}: Any) -> Any:",
            }
        }
    
    def _analyze_task_complexity(self, task_data: Dict[str, Any]) -> TaskComplexity:
        """タスク複雑度分析"""
        
        target_files = task_data.get('target_files', [])
        task_type = task_data.get('type', 'modification')
        error_count = task_data.get('requirements', {}).get('error_count', 0)
        
        # ファイル数による複雑度判定
        file_count = len(target_files)
        
        # エラー数による複雑度判定
        if error_count > 50:
            return TaskComplexity.CRITICAL
        elif error_count > 20:
            return TaskComplexity.COMPLEX
        elif error_count > 5:
            return TaskComplexity.MODERATE
        
        # ファイル数による複雑度判定
        if file_count > 10:
            return TaskComplexity.CRITICAL
        elif file_count > 5:
            return TaskComplexity.COMPLEX
        elif file_count > 2:
            return TaskComplexity.MODERATE
        
        # タスクタイプによる複雑度判定
        if task_type in ['new_feature_development', 'architecture_change']:
            return TaskComplexity.CRITICAL
        elif task_type in ['hybrid_implementation', 'new_implementation']:
            return TaskComplexity.COMPLEX
        elif task_type in ['modification', 'no-untyped-def']:
            return TaskComplexity.MODERATE
        
        return TaskComplexity.SIMPLE
    
    def _generate_new_implementation_steps(self, task_data: Dict[str, Any], 
                                         complexity: TaskComplexity) -> List[ImplementationStep]:
        """新規実装ステップ生成"""
        
        steps = []
        target_files = task_data.get('target_files', [])
        implementation_spec = task_data.get('requirements', {}).get('implementation_spec', {})
        
        # Step 1: 基本構造設計
        steps.append(ImplementationStep(
            step_id="design_structure",
            title="基本構造設計",
            description="実装すべきクラス・関数の基本構造を設計",
            code_example="""
# 設計例
class ExampleClass:
    \"\"\"クラスの説明\"\"\"
    
    def __init__(self, param: Any) -> None:
        \"\"\"初期化メソッド\"\"\"
        self.param = param
    
    def main_method(self, data: Any) -> Any:
        \"\"\"メイン処理メソッド\"\"\"
        return self._process_data(data)
    
    def _process_data(self, data: Any) -> Any:
        \"\"\"データ処理（内部メソッド）\"\"\"
        pass
""",
            validation_criteria=[
                "クラス・関数の責任が明確",
                "適切な命名規則の使用",
                "パブリック・プライベートメソッドの分離"
            ],
            common_errors=[
                "責任範囲の曖昧さ",
                "命名規則の不統一",
                "設計の過度な複雑化"
            ],
            error_solutions=[
                "Single Responsibility Principleに従う",
                "PEP8命名規則を遵守",
                "YAGNI原則でシンプル設計"
            ],
            estimated_tokens=200,
            dependencies=[],
            quality_checks=["設計レビュー", "命名規則チェック"]
        ))
        
        # Step 2: 型注釈・インポート設定
        steps.append(ImplementationStep(
            step_id="setup_imports_types",
            title="型注釈・インポート設定",
            description="必要なインポート文と基本的な型注釈を設定",
            code_example="""
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import json
import os

# 型注釈例
def process_data(data: Dict[str, Any]) -> Optional[List[Any]]:
    \"\"\"データ処理\"\"\"
    if not data:
        return None
    return [item for item in data.values()]
""",
            validation_criteria=[
                "必要なインポート文が全て存在",
                "全ての関数に型注釈が存在",
                "適切な型の選択"
            ],
            common_errors=[
                "インポート文の欠如",
                "型注釈の構文エラー",
                "不適切な型の選択"
            ],
            error_solutions=[
                "typing モジュールを適切にインポート",
                "引数: param: Type, 返り値: -> Type の形式",
                "不明な型は Any を使用"
            ],
            estimated_tokens=150,
            dependencies=["design_structure"],
            quality_checks=["mypy strict mode", "import整理"]
        ))
        
        # Step 3: 実装（コアロジック）
        steps.append(ImplementationStep(
            step_id="implement_core_logic",
            title="コアロジック実装",
            description="基本的なビジネスロジックを実装",
            code_example="""
def main_process(self, input_data: Any) -> Any:
    \"\"\"メイン処理実装\"\"\"
    # 1. データ検証
    if not self._validate_input(input_data):
        raise ValueError("Invalid input data")
    
    # 2. データ処理
    processed = self._process_data(input_data)
    
    # 3. 結果生成
    result = self._generate_result(processed)
    
    return result

def _validate_input(self, data: Any) -> bool:
    \"\"\"入力データ検証\"\"\"
    return data is not None

def _process_data(self, data: Any) -> Any:
    \"\"\"データ処理\"\"\"
    # 処理ロジック実装
    return data

def _generate_result(self, processed_data: Any) -> Any:
    \"\"\"結果生成\"\"\"
    return {"result": processed_data}
""",
            validation_criteria=[
                "ロジックが正常に動作",
                "エラーハンドリングが適切",
                "処理フローが明確"
            ],
            common_errors=[
                "エラーハンドリングの欠如",
                "処理フローの不明確さ",
                "境界条件の未考慮"
            ],
            error_solutions=[
                "try-except文の適切な配置",
                "ステップバイステップの処理",
                "None, 空リスト等の境界条件チェック"
            ],
            estimated_tokens=300,
            dependencies=["setup_imports_types"],
            quality_checks=["単体テスト", "エラーハンドリングチェック"]
        ))
        
        return steps
    
    def _generate_type_annotation_steps(self, task_data: Dict[str, Any], 
                                      complexity: TaskComplexity) -> List[ImplementationStep]:
        """型注釈修正ステップ生成"""
        
        steps = []
        target_files = task_data.get('target_files', [])
        error_count = task_data.get('requirements', {}).get('error_count', 0)
        
        # Step 1: インポート文確認・追加
        steps.append(ImplementationStep(
            step_id="check_imports",
            title="インポート文確認・追加",
            description="typing モジュールのインポートを確認し、必要に応じて追加",
            code_example="""
# 修正前
import os
import json

# 修正後
import os
import json
from typing import Any, Dict, List, Optional

# または必要な型のみ
from typing import Any
""",
            validation_criteria=[
                "typing モジュールが適切にインポートされている",
                "未使用インポートがない",
                "インポート順序が正しい"
            ],
            common_errors=[
                "typing のインポート忘れ",
                "不要なインポートの残存",
                "インポート順序の誤り"
            ],
            error_solutions=[
                "型注釈使用前に適切なインポートを追加",
                "isort でインポート整理",
                "未使用インポートの削除"
            ],
            estimated_tokens=100,
            dependencies=[],
            quality_checks=["isort チェック", "未使用インポート確認"]
        ))
        
        # Step 2: 関数シグネチャ修正
        steps.append(ImplementationStep(
            step_id="fix_function_signatures",
            title="関数シグネチャ修正",
            description="関数の引数と返り値に型注釈を追加",
            code_example="""
# 修正前
def __init__(self, validator):
    pass

def process_data(self, data, options):
    return result

# 修正後
def __init__(self, validator: Any) -> None:
    pass

def process_data(self, data: Any, options: Any) -> Any:
    return result
""",
            validation_criteria=[
                "全ての引数に型注釈が存在",
                "返り値型注釈が存在",
                "構文エラーがない"
            ],
            common_errors=[
                "def function(param -> None: Type): のような構文エラー",
                "型注釈の位置間違い",
                "返り値型の省略"
            ],
            error_solutions=[
                "引数: param: Type の形式",
                "返り値: ) -> Type: の形式",
                "不明な型は Any を使用"
            ],
            estimated_tokens=200,
            dependencies=["check_imports"],
            quality_checks=["構文チェック", "mypy validation"]
        ))
        
        # Step 3: メソッド修正
        steps.append(ImplementationStep(
            step_id="fix_method_signatures",
            title="メソッドシグネチャ修正",
            description="クラスメソッドの型注釈を追加・修正",
            code_example="""
# 修正前
class ExampleClass:
    def __init__(self, param):
        self.param = param
    
    def process(self, data):
        return self._helper(data)
    
    def _helper(self, item):
        return item * 2

# 修正後
class ExampleClass:
    def __init__(self, param: Any) -> None:
        self.param = param
    
    def process(self, data: Any) -> Any:
        return self._helper(data)
    
    def _helper(self, item: Any) -> Any:
        return item * 2
""",
            validation_criteria=[
                "全てのメソッドに型注釈が存在",
                "__init__ メソッドの返り値が -> None",
                "self 引数の型注釈がない（正常）"
            ],
            common_errors=[
                "self に型注釈を付ける",
                "__init__ の返り値型を省略",
                "プライベートメソッドの型注釈省略"
            ],
            error_solutions=[
                "self は型注釈不要",
                "__init__ は必ず -> None",
                "プライベートメソッドも型注釈必須"
            ],
            estimated_tokens=300,
            dependencies=["fix_function_signatures"],
            quality_checks=["クラス構造チェック", "メソッド型注釈確認"]
        ))
        
        return steps
    
    def _generate_quality_assurance_steps(self, task_data: Dict[str, Any], 
                                        complexity: TaskComplexity) -> List[ImplementationStep]:
        """品質保証ステップ生成"""
        
        steps = []
        
        # Step 1: 構文チェック
        steps.append(ImplementationStep(
            step_id="syntax_check",
            title="構文チェック",
            description="Python構文エラーがないことを確認",
            code_example="""
# コマンド実行例
python -m py_compile target_file.py

# または
python -c "import ast; ast.parse(open('target_file.py').read())"
""",
            validation_criteria=[
                "構文解析が成功する",
                "インデンテーションエラーがない",
                "括弧・引用符の対応が正しい"
            ],
            common_errors=[
                "インデンテーションエラー",
                "括弧の不一致",
                "引用符の不一致"
            ],
            error_solutions=[
                "一貫した4スペースインデント",
                "括弧の対応確認",
                "引用符の統一"
            ],
            estimated_tokens=100,
            dependencies=["implement_core_logic", "fix_method_signatures"],
            quality_checks=["python -m py_compile", "AST解析"]
        ))
        
        # Step 2: 型チェック
        steps.append(ImplementationStep(
            step_id="type_check",
            title="型チェック",
            description="mypy strict mode での型チェックを実行",
            code_example="""
# mypy チェック実行
mypy --strict target_file.py

# または個別オプション
mypy --disallow-untyped-defs --disallow-any-generics target_file.py
""",
            validation_criteria=[
                "mypy --strict が成功",
                "型注釈エラーがない",
                "型の一貫性が保たれている"
            ],
            common_errors=[
                "型注釈の不足",
                "型の不一致",
                "Any の過度な使用"
            ],
            error_solutions=[
                "全ての関数に型注釈を追加",
                "返り値型と実際の戻り値を一致",
                "必要に応じてより具体的な型を使用"
            ],
            estimated_tokens=150,
            dependencies=["syntax_check"],
            quality_checks=["mypy --strict", "型整合性チェック"]
        ))
        
        # Step 3: フォーマットチェック
        steps.append(ImplementationStep(
            step_id="format_check",
            title="フォーマットチェック",
            description="コードフォーマットが基準に適合していることを確認",
            code_example="""
# Black フォーマットチェック
black --check target_file.py

# isort インポート整理チェック
isort --check-only target_file.py

# 必要に応じて自動修正
black target_file.py
isort target_file.py
""",
            validation_criteria=[
                "Black フォーマットに適合",
                "インポート順序が正しい",
                "行長制限を遵守"
            ],
            common_errors=[
                "フォーマットの不統一",
                "インポート順序の誤り",
                "行長制限違反"
            ],
            error_solutions=[
                "black で自動フォーマット",
                "isort で自動インポート整理",
                "長い行の適切な分割"
            ],
            estimated_tokens=100,
            dependencies=["type_check"],
            quality_checks=["black --check", "isort --check-only"]
        ))
        
        return steps
    
    def _get_relevant_error_patterns(self, task_type: str, target_files: List[str]) -> List[ErrorPattern]:
        """関連エラーパターン取得"""
        
        relevant_patterns = []
        
        # タスクタイプ別のパターン選択
        if task_type in ['no-untyped-def', 'type_annotation']:
            relevant_patterns.extend([p for p in self.error_patterns 
                                    if p.error_type in ['no-untyped-def', 'import-error']])
        
        if task_type in ['new_implementation', 'modification']:
            relevant_patterns.extend([p for p in self.error_patterns 
                                    if p.error_type in ['syntax-error', 'type-error']])
        
        # ファイル拡張子による追加パターン
        py_files = [f for f in target_files if f.endswith('.py')]
        if py_files:
            relevant_patterns.extend([p for p in self.error_patterns 
                                    if p.pattern_id in ['indentation_error', 'import_missing']])
        
        return list(set(relevant_patterns))  # 重複除去
    
    def _generate_validation_checklist(self, task_type: str) -> List[str]:
        """検証チェックリスト生成"""
        
        base_checklist = [
            "構文エラーがない",
            "インデンテーションが正しい",
            "インポート文が適切",
        ]
        
        if task_type in ['no-untyped-def', 'type_annotation']:
            base_checklist.extend([
                "全ての関数に返り値型注釈がある",
                "全ての引数に型注釈がある",
                "typing モジュールが適切にインポートされている",
                "mypy --strict でエラーがない"
            ])
        
        if task_type in ['new_implementation']:
            base_checklist.extend([
                "クラス・関数の設計が適切",
                "適切なドキュメント文字列がある",
                "エラーハンドリングが実装されている"
            ])
        
        return base_checklist
    
    def save_guidance_to_file(self, guidance_data: Dict[str, Any], 
                            output_path: str = "tmp/implementation_guidance.json") -> str:
        """ガイダンスをファイルに保存"""
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(guidance_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 実装ガイダンスを {output_path} に保存しました")
        return output_path


def main():
    """テスト実行"""
    
    guidance_engine = ImplementationGuidanceEngine()
    
    # テストタスク
    test_task = {
        'task_id': 'test_guidance_001',
        'type': 'no-untyped-def',
        'target_files': [
            'postbox/context/context_splitter.py',
            'postbox/utils/gemini_helper.py'
        ],
        'requirements': {
            'error_type': 'no-untyped-def',
            'error_count': 15,
        }
    }
    
    print("🧪 ImplementationGuidance テスト実行")
    
    # Step-by-step ガイダンス生成テスト
    print("\n=== 段階的実装ガイダンス ===")
    steps = guidance_engine.generate_step_by_step_guidance(test_task)
    
    for i, step in enumerate(steps, 1):
        print(f"\n{i}. {step.title}")
        print(f"   説明: {step.description}")
        print(f"   推定トークン: {step.estimated_tokens}")
        print(f"   検証基準: {len(step.validation_criteria)}項目")
        print(f"   一般的エラー: {len(step.common_errors)}種類")
    
    # エラー回避ガイド生成テスト
    print("\n=== エラー回避ガイド ===")
    error_guide = guidance_engine.generate_error_avoidance_guide(test_task)
    print(f"関連エラーパターン: {len(error_guide['pattern_specific_guidance'])}種類")
    print(f"防止戦略: {len(error_guide['prevention_strategies'])}項目")
    print(f"検証チェックリスト: {len(error_guide['validation_checklist'])}項目")
    
    # 品質ガイダンス生成テスト
    print("\n=== 品質ガイダンス ===")
    quality_guide = guidance_engine.generate_quality_guidance(test_task)
    print(f"複雑度レベル: {quality_guide['complexity_level']}")
    print(f"品質目標: {len(quality_guide['quality_targets'])}項目")
    print(f"受入基準: {len(quality_guide['acceptance_criteria'])}項目")
    
    # 総合ガイダンス生成
    comprehensive_guidance = {
        "task_info": test_task,
        "implementation_steps": [asdict(step) for step in steps],
        "error_avoidance": error_guide,
        "quality_guidance": quality_guide
    }
    
    # ファイル保存テスト
    saved_path = guidance_engine.save_guidance_to_file(comprehensive_guidance)
    print(f"\n💾 総合ガイダンス保存: {saved_path}")


if __name__ == "__main__":
    main()