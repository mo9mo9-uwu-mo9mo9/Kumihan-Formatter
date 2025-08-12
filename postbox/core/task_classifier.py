#!/usr/bin/env python3
"""
Task Classifier for Postbox System
新規実装・修正・統合の自動分類システム
"""

import ast
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from enum import Enum
from dataclasses import dataclass


class TaskCategory(Enum):
    """タスクカテゴリ"""
    CODE_MODIFICATION = "code_modification"  # 既存コード修正
    NEW_IMPLEMENTATION = "new_implementation"  # 新規実装
    HYBRID_IMPLEMENTATION = "hybrid_implementation"  # ハイブリッド（既存+新規）
    FEATURE_DEVELOPMENT = "new_feature_development"  # 機能開発
    REFACTORING = "refactoring"  # リファクタリング
    TESTING = "testing"  # テスト関連
    DOCUMENTATION = "documentation"  # ドキュメント
    CONFIGURATION = "configuration"  # 設定変更


class ComplexityLevel(Enum):
    """複雑度レベル"""
    TRIVIAL = "trivial"      # 些細（5分以内）
    SIMPLE = "simple"        # 簡単（30分以内）
    MODERATE = "moderate"    # 中程度（2時間以内）
    COMPLEX = "complex"      # 複雑（半日以内）
    CRITICAL = "critical"    # 重要（1日以上）


@dataclass
class TaskClassification:
    """タスク分類結果"""
    category: TaskCategory
    complexity: ComplexityLevel
    confidence: float  # 0.0-1.0
    reasoning: str
    estimated_time: int  # 分
    risk_level: str  # low, medium, high
    recommended_approach: str
    dependencies: List[str]  # 依存ファイル・モジュール


class TaskClassifier:
    """タスク自動分類システム"""

    def __init__(self):
        self.classification_rules = {
            # コード修正パターン
            "error_patterns": {
                "no-untyped-def": TaskCategory.CODE_MODIFICATION,
                "no-untyped-call": TaskCategory.CODE_MODIFICATION,
                "type-arg": TaskCategory.CODE_MODIFICATION,
                "call-arg": TaskCategory.CODE_MODIFICATION,
                "attr-defined": TaskCategory.CODE_MODIFICATION,
            },
            
            # 新規実装パターン
            "implementation_keywords": {
                "新規作成", "新規実装", "create new", "implement new",
                "add class", "add function", "add module"
            },
            
            # 機能開発パターン
            "feature_keywords": {
                "機能追加", "機能開発", "feature", "functionality",
                "enhancement", "capability"
            },
            
            # リファクタリングパターン
            "refactoring_keywords": {
                "リファクタリング", "refactor", "restructure", "reorganize",
                "clean up", "improve structure"
            }
        }

    def classify_task(self, task_description: str, target_files: List[str],
                     context: Dict[str, Any] = None) -> TaskClassification:
        """タスクの自動分類"""

        print(f"🔍 タスク分類開始: {task_description}")
        
        context = context or {}
        
        # 1. 基本分類
        category = self._classify_basic_category(task_description, target_files, context)
        
        # 2. 複雑度分析
        complexity = self._analyze_complexity(task_description, target_files, category)
        
        # 3. 信頼度計算
        confidence = self._calculate_confidence(task_description, target_files, category)
        
        # 4. 推定時間計算
        estimated_time = self._estimate_time(complexity, len(target_files))
        
        # 5. リスク評価
        risk_level = self._assess_risk(category, complexity, target_files)
        
        # 6. 推奨アプローチ
        approach = self._recommend_approach(category, complexity, target_files)
        
        # 7. 依存関係分析
        dependencies = self._analyze_dependencies(target_files)
        
        # 8. 理由生成
        reasoning = self._generate_reasoning(
            category, complexity, confidence, task_description, target_files
        )
        
        classification = TaskClassification(
            category=category,
            complexity=complexity,
            confidence=confidence,
            reasoning=reasoning,
            estimated_time=estimated_time,
            risk_level=risk_level,
            recommended_approach=approach,
            dependencies=dependencies
        )
        
        print(f"📊 分類結果: {category.value} ({complexity.value}, 信頼度: {confidence:.2f})")
        
        return classification

    def _classify_basic_category(self, task_description: str, target_files: List[str],
                                context: Dict[str, Any]) -> TaskCategory:
        """基本カテゴリ分類"""

        desc_lower = task_description.lower()
        
        # 既存エラー修正パターンをチェック
        for error_pattern, category in self.classification_rules["error_patterns"].items():
            if error_pattern in desc_lower:
                return category
        
        # 新規実装キーワードをチェック
        for keyword in self.classification_rules["implementation_keywords"]:
            if keyword.lower() in desc_lower:
                # ファイル存在確認で細分化
                existing_files = [f for f in target_files if os.path.exists(f)]
                if len(existing_files) == 0:
                    return TaskCategory.NEW_IMPLEMENTATION
                elif len(existing_files) < len(target_files):
                    return TaskCategory.HYBRID_IMPLEMENTATION
                else:
                    return TaskCategory.CODE_MODIFICATION
        
        # 機能開発キーワードをチェック
        for keyword in self.classification_rules["feature_keywords"]:
            if keyword.lower() in desc_lower:
                return TaskCategory.FEATURE_DEVELOPMENT
        
        # リファクタリングキーワードをチェック
        for keyword in self.classification_rules["refactoring_keywords"]:
            if keyword.lower() in desc_lower:
                return TaskCategory.REFACTORING
        
        # テスト関連チェック
        if any(keyword in desc_lower for keyword in ["test", "テスト", "pytest", "unittest"]):
            return TaskCategory.TESTING
        
        # ドキュメント関連チェック
        if any(keyword in desc_lower for keyword in ["document", "ドキュメント", "readme", "doc"]):
            return TaskCategory.DOCUMENTATION
        
        # 設定関連チェック
        if any(keyword in desc_lower for keyword in ["config", "設定", "configuration", ".json", ".yaml"]):
            return TaskCategory.CONFIGURATION
        
        # ファイル存在状況で判定
        existing_files = [f for f in target_files if os.path.exists(f)]
        if len(existing_files) == 0:
            return TaskCategory.NEW_IMPLEMENTATION
        elif len(existing_files) < len(target_files):
            return TaskCategory.HYBRID_IMPLEMENTATION
        else:
            return TaskCategory.CODE_MODIFICATION

    def _analyze_complexity(self, task_description: str, target_files: List[str],
                           category: TaskCategory) -> ComplexityLevel:
        """複雑度分析"""

        complexity_score = 0
        
        # ファイル数による影響
        complexity_score += min(len(target_files) * 0.5, 3)
        
        # タスクカテゴリによる基本複雑度
        category_complexity = {
            TaskCategory.CODE_MODIFICATION: 1,
            TaskCategory.NEW_IMPLEMENTATION: 3,
            TaskCategory.HYBRID_IMPLEMENTATION: 4,
            TaskCategory.FEATURE_DEVELOPMENT: 5,
            TaskCategory.REFACTORING: 3,
            TaskCategory.TESTING: 2,
            TaskCategory.DOCUMENTATION: 1,
            TaskCategory.CONFIGURATION: 1
        }
        complexity_score += category_complexity.get(category, 2)
        
        # ファイルサイズ・内容による影響
        for file_path in target_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = len(content.split('\n'))
                    if lines > 500:
                        complexity_score += 1
                    if lines > 1000:
                        complexity_score += 1
                    
                    # 関数・クラス数
                    functions = content.count('def ')
                    classes = content.count('class ')
                    complexity_score += min(functions // 10, 2)
                    complexity_score += min(classes // 3, 2)
                    
                except Exception:
                    pass  # ファイル読み取りエラーは無視
        
        # 複雑なキーワード
        desc_lower = task_description.lower()
        complex_keywords = ["architecture", "integration", "migration", "refactor", "optimization"]
        for keyword in complex_keywords:
            if keyword in desc_lower:
                complexity_score += 2
                break
        
        # 複雑度レベル決定
        if complexity_score <= 2:
            return ComplexityLevel.TRIVIAL
        elif complexity_score <= 4:
            return ComplexityLevel.SIMPLE
        elif complexity_score <= 7:
            return ComplexityLevel.MODERATE
        elif complexity_score <= 10:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.CRITICAL

    def _calculate_confidence(self, task_description: str, target_files: List[str],
                             category: TaskCategory) -> float:
        """分類信頼度計算"""

        confidence = 0.7  # ベース信頼度
        
        # 明確なキーワードマッチがある場合
        desc_lower = task_description.lower()
        
        # カテゴリ固有キーワードの存在確認
        if category == TaskCategory.CODE_MODIFICATION:
            if any(pattern in desc_lower for pattern in self.classification_rules["error_patterns"]):
                confidence += 0.2
        elif category == TaskCategory.NEW_IMPLEMENTATION:
            if any(keyword.lower() in desc_lower for keyword in self.classification_rules["implementation_keywords"]):
                confidence += 0.2
        
        # ファイル状況の一貫性
        existing_files = [f for f in target_files if os.path.exists(f)]
        if category == TaskCategory.NEW_IMPLEMENTATION and len(existing_files) == 0:
            confidence += 0.1
        elif category == TaskCategory.CODE_MODIFICATION and len(existing_files) == len(target_files):
            confidence += 0.1
        
        # タスク記述の詳細度
        if len(task_description.split()) > 10:
            confidence += 0.05
        
        return min(confidence, 1.0)

    def _estimate_time(self, complexity: ComplexityLevel, file_count: int) -> int:
        """時間推定（分）"""

        base_times = {
            ComplexityLevel.TRIVIAL: 5,
            ComplexityLevel.SIMPLE: 20,
            ComplexityLevel.MODERATE: 60,
            ComplexityLevel.COMPLEX: 180,
            ComplexityLevel.CRITICAL: 480
        }
        
        base_time = base_times[complexity]
        
        # ファイル数による調整
        file_factor = min(file_count * 0.3, 2.0)
        
        return int(base_time * (1 + file_factor))

    def _assess_risk(self, category: TaskCategory, complexity: ComplexityLevel,
                    target_files: List[str]) -> str:
        """リスク評価"""

        risk_score = 0
        
        # カテゴリによるリスク
        category_risk = {
            TaskCategory.CODE_MODIFICATION: 1,
            TaskCategory.NEW_IMPLEMENTATION: 2,
            TaskCategory.HYBRID_IMPLEMENTATION: 3,
            TaskCategory.FEATURE_DEVELOPMENT: 3,
            TaskCategory.REFACTORING: 4,
            TaskCategory.TESTING: 1,
            TaskCategory.DOCUMENTATION: 0,
            TaskCategory.CONFIGURATION: 2
        }
        risk_score += category_risk.get(category, 2)
        
        # 複雑度によるリスク
        complexity_risk = {
            ComplexityLevel.TRIVIAL: 0,
            ComplexityLevel.SIMPLE: 1,
            ComplexityLevel.MODERATE: 2,
            ComplexityLevel.COMPLEX: 3,
            ComplexityLevel.CRITICAL: 4
        }
        risk_score += complexity_risk[complexity]
        
        # 重要ファイルの修正
        critical_paths = ["main", "core", "__init__", "config", "settings"]
        for file_path in target_files:
            if any(critical in file_path.lower() for critical in critical_paths):
                risk_score += 1
                break
        
        # リスクレベル決定
        if risk_score <= 2:
            return "low"
        elif risk_score <= 5:
            return "medium"
        else:
            return "high"

    def _recommend_approach(self, category: TaskCategory, complexity: ComplexityLevel,
                           target_files: List[str]) -> str:
        """推奨アプローチ"""

        approach = f"{category.value}向けアプローチ:\n"
        
        if category == TaskCategory.CODE_MODIFICATION:
            if complexity in [ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE]:
                approach += "- 直接修正・一括処理\n- 自動化ツールの活用"
            else:
                approach += "- 段階的修正\n- 詳細テスト・レビュー"
        
        elif category == TaskCategory.NEW_IMPLEMENTATION:
            approach += "- テンプレートベース実装\n- 段階的開発・テスト\n- 品質基準厳格適用"
        
        elif category == TaskCategory.HYBRID_IMPLEMENTATION:
            approach += "- 既存影響最小化\n- 新規部分の独立実装\n- 統合テスト重視"
        
        elif category == TaskCategory.FEATURE_DEVELOPMENT:
            approach += "- 要求仕様詳細化\n- プロトタイプ開発\n- 段階的機能実装"
        
        elif category == TaskCategory.REFACTORING:
            approach += "- 現状分析・設計\n- 安全なリファクタリング手法\n- 回帰テスト徹底"
        
        else:
            approach += "- カテゴリ固有のベストプラクティス適用"
        
        return approach

    def _analyze_dependencies(self, target_files: List[str]) -> List[str]:
        """依存関係分析"""

        dependencies = []
        
        for file_path in target_files:
            if not os.path.exists(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # import文の抽出
                import_lines = [line.strip() for line in content.split('\n')
                               if line.strip().startswith(('import ', 'from '))]
                
                for line in import_lines:
                    # プロジェクト内モジュールのみ抽出（簡易版）
                    if 'kumihan_formatter' in line or '.' in line:
                        dependencies.append(line)
                
            except Exception:
                pass  # ファイル読み取りエラーは無視
        
        return list(set(dependencies))  # 重複除去

    def _generate_reasoning(self, category: TaskCategory, complexity: ComplexityLevel,
                           confidence: float, task_description: str,
                           target_files: List[str]) -> str:
        """分類理由生成"""

        reasoning = f"タスク自動分類結果:\n"
        reasoning += f"カテゴリ: {category.value} (信頼度: {confidence:.2f})\n"
        reasoning += f"複雑度: {complexity.value}\n"
        reasoning += f"対象ファイル: {len(target_files)}件\n\n"
        
        reasoning += "分類根拠:\n"
        
        # カテゴリ分類根拠
        desc_lower = task_description.lower()
        
        if category == TaskCategory.CODE_MODIFICATION:
            for pattern in self.classification_rules["error_patterns"]:
                if pattern in desc_lower:
                    reasoning += f"- エラーパターン '{pattern}' を検出\n"
                    break
        
        elif category == TaskCategory.NEW_IMPLEMENTATION:
            for keyword in self.classification_rules["implementation_keywords"]:
                if keyword.lower() in desc_lower:
                    reasoning += f"- 新規実装キーワード '{keyword}' を検出\n"
                    break
            
            existing_files = [f for f in target_files if os.path.exists(f)]
            if len(existing_files) == 0:
                reasoning += "- 対象ファイルが全て未作成\n"
        
        # ファイル状況
        existing_count = len([f for f in target_files if os.path.exists(f)])
        reasoning += f"- 既存ファイル: {existing_count}/{len(target_files)}件\n"
        
        # 複雑度要因
        if complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.CRITICAL]:
            reasoning += f"- 高複雑度要因: 多数ファイル、大規模変更、またはリスク要因\n"
        
        return reasoning

    def get_classification_stats(self) -> Dict[str, Any]:
        """分類統計情報"""
        
        return {
            "available_categories": [cat.value for cat in TaskCategory],
            "complexity_levels": [level.value for level in ComplexityLevel],
            "classification_rules": {
                "error_patterns": len(self.classification_rules["error_patterns"]),
                "implementation_keywords": len(self.classification_rules["implementation_keywords"]),
                "feature_keywords": len(self.classification_rules["feature_keywords"]),
                "refactoring_keywords": len(self.classification_rules["refactoring_keywords"])
            }
        }


def main():
    """テスト実行"""
    classifier = TaskClassifier()
    
    # テストケース
    test_cases = [
        {
            "description": "no-untyped-def エラー修正",
            "files": ["kumihan_formatter/core/utilities/logger.py"],
        },
        {
            "description": "新規クラス UserManager を実装",
            "files": ["src/user_manager.py"],
        },
        {
            "description": "新機能：ログ分析システム開発",
            "files": ["src/analysis/log_analyzer.py", "tests/test_log_analyzer.py"],
        }
    ]
    
    print("🧪 TaskClassifier テスト実行\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"=== テストケース {i} ===")
        
        classification = classifier.classify_task(
            test_case["description"],
            test_case["files"]
        )
        
        print(f"分類結果:")
        print(f"  カテゴリ: {classification.category.value}")
        print(f"  複雑度: {classification.complexity.value}")
        print(f"  推定時間: {classification.estimated_time}分")
        print(f"  リスク: {classification.risk_level}")
        print(f"  信頼度: {classification.confidence:.2f}")
        print(f"  推奨アプローチ: {classification.recommended_approach}")
        print()


if __name__ == "__main__":
    main()