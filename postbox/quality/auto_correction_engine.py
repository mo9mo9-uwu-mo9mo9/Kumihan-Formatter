#!/usr/bin/env python3
"""
AutoCorrection Engine
自動修正提案・適用システム - 既存Gemini協業システムとの統合
パターン認識による修正エンジン・段階的品質改善システム
"""

import os
import json
import re
import ast
import time
import subprocess
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

class CorrectionType(Enum):
    """修正タイプ"""
    SYNTAX_FIX = "syntax_fix"           # 構文修正
    TYPE_ANNOTATION = "type_annotation" # 型注釈追加
    FORMAT_FIX = "format_fix"          # フォーマット修正
    IMPORT_OPTIMIZATION = "import_opt"  # インポート最適化
    SECURITY_FIX = "security_fix"      # セキュリティ修正
    PERFORMANCE_OPT = "performance_opt" # パフォーマンス最適化
    STYLE_IMPROVEMENT = "style_improve" # スタイル改善

class CorrectionComplexity(Enum):
    """修正複雑度"""
    SIMPLE = "simple"        # 簡単（自動適用可能）
    MODERATE = "moderate"    # 中程度（確認後適用）
    COMPLEX = "complex"      # 複雑（手動修正推奨）
    CRITICAL = "critical"    # 重要（慎重な確認必要）

class CorrectionConfidence(Enum):
    """修正信頼度"""
    HIGH = "high"        # 高（95%以上）
    MEDIUM = "medium"    # 中（80-94%）
    LOW = "low"         # 低（60-79%）
    UNCERTAIN = "uncertain" # 不確実（60%未満）

@dataclass
class CorrectionSuggestion:
    """修正提案"""
    suggestion_id: str
    file_path: str
    line_number: int
    correction_type: CorrectionType
    complexity: CorrectionComplexity
    confidence: CorrectionConfidence
    
    original_code: str
    suggested_code: str
    explanation: str
    reasoning: str
    
    estimated_time: float  # 推定修正時間（分）
    risk_level: str       # リスクレベル
    prerequisites: List[str] # 前提条件
    
    pattern_id: Optional[str] = None
    auto_applicable: bool = False
    gemini_recommended: bool = False

@dataclass
class CorrectionResult:
    """修正結果"""
    suggestion_id: str
    file_path: str
    applied: bool
    success: bool
    
    execution_time: float
    error_message: Optional[str] = None
    quality_improvement: Optional[float] = None
    
    before_metrics: Optional[Dict[str, float]] = None
    after_metrics: Optional[Dict[str, float]] = None

class PatternMatcher:
    """パターンマッチング・認識システム"""
    
    def __init__(self):
        self.patterns = self._load_correction_patterns()
        self.statistics = {
            "patterns_matched": 0,
            "corrections_suggested": 0,
            "success_rate": 0.0
        }
    
    def _load_correction_patterns(self) -> Dict[str, Dict]:
        """修正パターン読み込み"""
        
        # 基本的な修正パターン定義
        patterns = {
            "no_untyped_def": {
                "regex": r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*:",
                "type": CorrectionType.TYPE_ANNOTATION,
                "complexity": CorrectionComplexity.SIMPLE,
                "confidence": CorrectionConfidence.HIGH,
                "template": "def {func_name}({params}) -> {return_type}:",
                "auto_applicable": True
            },
            
            "missing_import": {
                "regex": r"from\s+typing\s+import",
                "type": CorrectionType.IMPORT_OPTIMIZATION,
                "complexity": CorrectionComplexity.SIMPLE,
                "confidence": CorrectionConfidence.HIGH,
                "template": "from typing import Any, Dict, List, Optional",
                "auto_applicable": True
            },
            
            "unused_import": {
                "regex": r"^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)",
                "type": CorrectionType.IMPORT_OPTIMIZATION,
                "complexity": CorrectionComplexity.SIMPLE,
                "confidence": CorrectionConfidence.MEDIUM,
                "auto_applicable": True
            },
            
            "format_violation": {
                "regex": r"\s+$",  # 行末空白
                "type": CorrectionType.FORMAT_FIX,
                "complexity": CorrectionComplexity.SIMPLE,
                "confidence": CorrectionConfidence.HIGH,
                "template": "",
                "auto_applicable": True
            },
            
            "security_eval": {
                "regex": r"\beval\s*\(",
                "type": CorrectionType.SECURITY_FIX,
                "complexity": CorrectionComplexity.CRITICAL,
                "confidence": CorrectionConfidence.HIGH,
                "template": "# TODO: Replace eval() with safer alternative",
                "auto_applicable": False
            },
            
            "performance_loop": {
                "regex": r"for\s+\w+\s+in\s+range\(len\(",
                "type": CorrectionType.PERFORMANCE_OPT,
                "complexity": CorrectionComplexity.MODERATE,
                "confidence": CorrectionConfidence.MEDIUM,
                "template": "for i, item in enumerate({iterable}):",
                "auto_applicable": False
            }
        }
        
        return patterns
    
    def match_patterns(self, file_content: str, file_path: str) -> List[CorrectionSuggestion]:
        """パターンマッチング実行"""
        suggestions = []
        lines = file_content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_id, pattern in self.patterns.items():
                match = re.search(pattern["regex"], line)
                if match:
                    suggestion = self._create_suggestion_from_pattern(
                        pattern_id, pattern, file_path, line_num, line, match
                    )
                    if suggestion:
                        suggestions.append(suggestion)
                        self.statistics["patterns_matched"] += 1
        
        self.statistics["corrections_suggested"] = len(suggestions)
        return suggestions
    
    def _create_suggestion_from_pattern(self, pattern_id: str, pattern: Dict, 
                                      file_path: str, line_num: int, 
                                      original_line: str, match: re.Match) -> Optional[CorrectionSuggestion]:
        """パターンから修正提案作成"""
        
        try:
            suggestion_id = f"{pattern_id}_{file_path}_{line_num}_{int(time.time())}"
            
            # 修正コード生成
            suggested_code = self._generate_suggested_code(pattern, original_line, match)
            
            # 説明・推論生成
            explanation, reasoning = self._generate_explanation(pattern_id, pattern)
            
            return CorrectionSuggestion(
                suggestion_id=suggestion_id,
                file_path=file_path,
                line_number=line_num,
                correction_type=pattern["type"],
                complexity=pattern["complexity"],
                confidence=pattern["confidence"],
                original_code=original_line.strip(),
                suggested_code=suggested_code,
                explanation=explanation,
                reasoning=reasoning,
                estimated_time=self._estimate_correction_time(pattern),
                risk_level=self._assess_risk_level(pattern),
                prerequisites=self._get_prerequisites(pattern),
                pattern_id=pattern_id,
                auto_applicable=pattern.get("auto_applicable", False),
                gemini_recommended=self._should_recommend_gemini(pattern)
            )
            
        except Exception as e:
            print(f"⚠️ 修正提案作成エラー: {e}")
            return None
    
    def _generate_suggested_code(self, pattern: Dict, original_line: str, match: re.Match) -> str:
        """修正コード生成"""
        
        template = pattern.get("template", original_line)
        
        # パターン固有の修正
        if pattern["type"] == CorrectionType.TYPE_ANNOTATION:
            return self._fix_type_annotation(original_line, match)
        elif pattern["type"] == CorrectionType.FORMAT_FIX:
            return original_line.rstrip()  # 行末空白除去
        elif pattern["type"] == CorrectionType.IMPORT_OPTIMIZATION:
            return self._optimize_import(original_line, match)
        else:
            return template
    
    def _fix_type_annotation(self, original_line: str, match: re.Match) -> str:
        """型注釈修正"""
        
        # 関数定義パターン解析
        func_match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*:", original_line)
        if not func_match:
            return original_line
        
        func_name = func_match.group(1)
        params = func_match.group(2).strip()
        
        # 戻り値型の推定
        return_type = "None"  # デフォルト
        if "return" in original_line.lower() or any(keyword in func_name.lower() for keyword in ["get", "create", "generate"]):
            return_type = "Any"
        
        # パラメータ型注釈追加
        if params and ":" not in params:
            # 簡単なパラメータ型推定
            typed_params = []
            for param in params.split(','):
                param = param.strip()
                if param and not param.startswith('*'):
                    typed_params.append(f"{param}: Any")
                else:
                    typed_params.append(param)
            params = ", ".join(typed_params)
        
        return f"def {func_name}({params}) -> {return_type}:"
    
    def _optimize_import(self, original_line: str, match: re.Match) -> str:
        """インポート最適化"""
        
        # 未使用インポート検出は複雑なので、基本的な整理のみ
        if original_line.strip().startswith("import ") and "," in original_line:
            # 複数インポートを分割
            imports = [imp.strip() for imp in original_line.replace("import ", "").split(",")]
            return "\n".join([f"import {imp}" for imp in imports if imp])
        
        return original_line
    
    def _generate_explanation(self, pattern_id: str, pattern: Dict) -> Tuple[str, str]:
        """説明・推論生成"""
        
        explanations = {
            "no_untyped_def": (
                "型注釈が不足している関数を検出しました。",
                "mypy strict modeでは全ての関数に型注釈が必要です。"
            ),
            "missing_import": (
                "typing モジュールからの必要なインポートが不足しています。",
                "型注釈を使用するためには適切なインポートが必要です。"
            ),
            "unused_import": (
                "使用されていないインポートが検出されました。",
                "不要なインポートはコードの可読性とパフォーマンスに影響します。"
            ),
            "format_violation": (
                "フォーマット違反（行末空白）が検出されました。",
                "一貫したコードフォーマットは保守性を向上させます。"
            ),
            "security_eval": (
                "セキュリティリスク（eval使用）が検出されました。",
                "eval()の使用はセキュリティ脆弱性を引き起こす可能性があります。"
            ),
            "performance_loop": (
                "パフォーマンス改善可能なループパターンを検出しました。",
                "enumerate()の使用により効率性と可読性が向上します。"
            )
        }
        
        return explanations.get(pattern_id, ("修正が必要です。", "品質改善のため修正を推奨します。"))
    
    def _estimate_correction_time(self, pattern: Dict) -> float:
        """修正時間推定（分）"""
        
        complexity_times = {
            CorrectionComplexity.SIMPLE: 0.5,
            CorrectionComplexity.MODERATE: 2.0,
            CorrectionComplexity.COMPLEX: 10.0,
            CorrectionComplexity.CRITICAL: 30.0
        }
        
        return complexity_times.get(pattern["complexity"], 5.0)
    
    def _assess_risk_level(self, pattern: Dict) -> str:
        """リスクレベル評価"""
        
        if pattern["complexity"] == CorrectionComplexity.CRITICAL:
            return "high"
        elif pattern["complexity"] == CorrectionComplexity.COMPLEX:
            return "medium"
        else:
            return "low"
    
    def _get_prerequisites(self, pattern: Dict) -> List[str]:
        """前提条件取得"""
        
        prerequisites = {
            CorrectionType.TYPE_ANNOTATION: ["typing モジュールのインポート"],
            CorrectionType.SECURITY_FIX: ["セキュリティレビュー", "代替実装の検討"],
            CorrectionType.PERFORMANCE_OPT: ["パフォーマンステスト", "ベンチマーク"],
        }
        
        return prerequisites.get(pattern["type"], [])
    
    def _should_recommend_gemini(self, pattern: Dict) -> bool:
        """Gemini推奨判定"""
        
        # 簡単で自動適用可能なパターンはGemini推奨
        return (pattern["complexity"] in [CorrectionComplexity.SIMPLE, CorrectionComplexity.MODERATE] and
                pattern["confidence"] in [CorrectionConfidence.HIGH, CorrectionConfidence.MEDIUM])

class AutoCorrectionEngine:
    """自動修正エンジン"""
    
    def __init__(self):
        self.data_dir = Path("postbox/quality/corrections")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.suggestions_path = self.data_dir / "suggestions.json"
        self.results_path = self.data_dir / "results.json"
        self.statistics_path = self.data_dir / "statistics.json"
        
        self.pattern_matcher = PatternMatcher()
        
        # 統計情報
        self.statistics = {
            "total_suggestions": 0,
            "auto_applied": 0,
            "manual_applied": 0,
            "rejected": 0,
            "success_rate": 0.0,
            "gemini_delegated": 0,
            "quality_improvements": []
        }
        
        # Gemini協業設定
        self.gemini_integration = self._initialize_gemini_integration()
        
        print("🔧 AutoCorrectionEngine 初期化完了")
    
    def _initialize_gemini_integration(self):
        """Gemini協業システム初期化"""
        try:
            # 既存のDualAgentCoordinatorを使用
            import sys
            sys.path.append('postbox')
            from workflow.dual_agent_coordinator import DualAgentCoordinator
            return DualAgentCoordinator()
        except ImportError:
            print("⚠️ Gemini協業システムが見つかりません。スタンドアロンモードで動作します。")
            return None
    
    def analyze_file(self, file_path: str) -> List[CorrectionSuggestion]:
        """ファイル解析・修正提案生成"""
        
        print(f"🔍 ファイル解析開始: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ ファイル読み込みエラー: {e}")
            return []
        
        # パターンマッチングによる提案生成
        suggestions = self.pattern_matcher.match_patterns(content, file_path)
        
        # 提案の優先度付け・フィルタリング
        suggestions = self._prioritize_suggestions(suggestions)
        
        # 統計更新
        self.statistics["total_suggestions"] += len(suggestions)
        
        # 提案保存
        self._save_suggestions(suggestions)
        
        print(f"✅ 解析完了: {len(suggestions)}件の修正提案")
        
        return suggestions
    
    def apply_corrections(self, suggestions: List[CorrectionSuggestion], 
                         auto_apply: bool = False, 
                         use_gemini: bool = True) -> List[CorrectionResult]:
        """修正適用"""
        
        results = []
        
        for suggestion in suggestions:
            print(f"🔧 修正適用: {suggestion.suggestion_id}")
            
            # 適用方法決定
            if suggestion.auto_applicable and auto_apply:
                # 自動適用
                result = self._apply_correction_direct(suggestion)
                if result.success:
                    self.statistics["auto_applied"] += 1
            elif suggestion.gemini_recommended and use_gemini and self.gemini_integration:
                # Gemini適用
                result = self._apply_correction_gemini(suggestion)
                if result.success:
                    self.statistics["gemini_delegated"] += 1
            else:
                # 手動適用推奨
                result = self._create_manual_correction_guide(suggestion)
                self.statistics["manual_applied"] += 1
            
            results.append(result)
            
            # 品質改善測定
            if result.success and result.quality_improvement:
                self.statistics["quality_improvements"].append(result.quality_improvement)
        
        # 結果保存
        self._save_results(results)
        
        # 統計更新
        self._update_statistics(results)
        
        return results
    
    def _apply_correction_direct(self, suggestion: CorrectionSuggestion) -> CorrectionResult:
        """直接修正適用"""
        
        start_time = time.time()
        
        try:
            # ファイル読み込み
            with open(suggestion.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 修正適用
            if suggestion.line_number <= len(lines):
                original_line = lines[suggestion.line_number - 1]
                lines[suggestion.line_number - 1] = suggestion.suggested_code + '\n'
                
                # ファイル書き込み
                with open(suggestion.file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                execution_time = time.time() - start_time
                
                print(f"✅ 直接修正完了: {suggestion.file_path}:{suggestion.line_number}")
                
                return CorrectionResult(
                    suggestion_id=suggestion.suggestion_id,
                    file_path=suggestion.file_path,
                    applied=True,
                    success=True,
                    execution_time=execution_time
                )
            else:
                raise ValueError(f"行番号が範囲外: {suggestion.line_number}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ 直接修正エラー: {e}")
            
            return CorrectionResult(
                suggestion_id=suggestion.suggestion_id,
                file_path=suggestion.file_path,
                applied=False,
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _apply_correction_gemini(self, suggestion: CorrectionSuggestion) -> CorrectionResult:
        """Gemini修正適用"""
        
        start_time = time.time()
        
        try:
            if not self.gemini_integration:
                raise ValueError("Gemini協業システムが利用できません")
            
            # Geminiタスク作成
            task_data = {
                'task_id': f"correction_{suggestion.suggestion_id}",
                'type': suggestion.correction_type.value,
                'target_files': [suggestion.file_path],
                'requirements': {
                    'line_number': suggestion.line_number,
                    'original_code': suggestion.original_code,
                    'suggested_code': suggestion.suggested_code,
                    'explanation': suggestion.explanation,
                    'complexity': suggestion.complexity.value
                }
            }
            
            # Gemini実行
            task_ids = self.gemini_integration.create_mypy_fix_task(
                [suggestion.file_path], 
                suggestion.correction_type.value, 
                auto_execute=True
            )
            
            execution_time = time.time() - start_time
            
            if task_ids:
                print(f"✅ Gemini修正完了: {suggestion.suggestion_id}")
                return CorrectionResult(
                    suggestion_id=suggestion.suggestion_id,
                    file_path=suggestion.file_path,
                    applied=True,
                    success=True,
                    execution_time=execution_time
                )
            else:
                raise ValueError("Gemini実行失敗")
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ Gemini修正エラー: {e}")
            
            return CorrectionResult(
                suggestion_id=suggestion.suggestion_id,
                file_path=suggestion.file_path,
                applied=False,
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _create_manual_correction_guide(self, suggestion: CorrectionSuggestion) -> CorrectionResult:
        """手動修正ガイド作成"""
        
        guide_path = self.data_dir / f"manual_guide_{suggestion.suggestion_id}.md"
        
        guide_content = f"""# 手動修正ガイド: {suggestion.suggestion_id}

## ファイル情報
- **ファイルパス**: {suggestion.file_path}
- **行番号**: {suggestion.line_number}
- **修正タイプ**: {suggestion.correction_type.value}
- **複雑度**: {suggestion.complexity.value}
- **信頼度**: {suggestion.confidence.value}

## 修正内容

### 修正前
```python
{suggestion.original_code}
```

### 修正後
```python
{suggestion.suggested_code}
```

## 説明
{suggestion.explanation}

## 推論
{suggestion.reasoning}

## 前提条件
{chr(10).join(f"- {prereq}" for prereq in suggestion.prerequisites)}

## 推定時間
約 {suggestion.estimated_time} 分

## リスクレベル
{suggestion.risk_level}

## 修正手順
1. ファイルを開く: `{suggestion.file_path}`
2. {suggestion.line_number}行目を確認
3. 上記の修正を適用
4. 構文チェック実行: `python3 -m py_compile {suggestion.file_path}`
5. 品質チェック実行: `make lint`

---
Generated by AutoCorrectionEngine at {datetime.datetime.now().isoformat()}
"""
        
        try:
            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write(guide_content)
            
            print(f"📝 手動修正ガイド作成: {guide_path}")
            
            return CorrectionResult(
                suggestion_id=suggestion.suggestion_id,
                file_path=suggestion.file_path,
                applied=False,
                success=True,
                execution_time=0.0
            )
            
        except Exception as e:
            print(f"❌ 手動修正ガイド作成エラー: {e}")
            return CorrectionResult(
                suggestion_id=suggestion.suggestion_id,
                file_path=suggestion.file_path,
                applied=False,
                success=False,
                execution_time=0.0,
                error_message=str(e)
            )
    
    def _prioritize_suggestions(self, suggestions: List[CorrectionSuggestion]) -> List[CorrectionSuggestion]:
        """修正提案優先度付け"""
        
        def priority_score(suggestion: CorrectionSuggestion) -> float:
            score = 0.0
            
            # 信頼度による重み
            confidence_weights = {
                CorrectionConfidence.HIGH: 1.0,
                CorrectionConfidence.MEDIUM: 0.8,
                CorrectionConfidence.LOW: 0.6,
                CorrectionConfidence.UNCERTAIN: 0.3
            }
            score += confidence_weights.get(suggestion.confidence, 0.5)
            
            # 複雑度による重み（簡単なものを優先）
            complexity_weights = {
                CorrectionComplexity.SIMPLE: 1.0,
                CorrectionComplexity.MODERATE: 0.7,
                CorrectionComplexity.COMPLEX: 0.4,
                CorrectionComplexity.CRITICAL: 0.2
            }
            score += complexity_weights.get(suggestion.complexity, 0.5)
            
            # 修正タイプによる重み
            type_weights = {
                CorrectionType.SYNTAX_FIX: 1.0,
                CorrectionType.SECURITY_FIX: 0.9,
                CorrectionType.TYPE_ANNOTATION: 0.8,
                CorrectionType.FORMAT_FIX: 0.7,
                CorrectionType.IMPORT_OPTIMIZATION: 0.6,
                CorrectionType.PERFORMANCE_OPT: 0.5,
                CorrectionType.STYLE_IMPROVEMENT: 0.4
            }
            score += type_weights.get(suggestion.correction_type, 0.5)
            
            return score
        
        # 優先度順にソート
        return sorted(suggestions, key=priority_score, reverse=True)
    
    def _save_suggestions(self, suggestions: List[CorrectionSuggestion]) -> None:
        """修正提案保存"""
        try:
            suggestions_data = [asdict(suggestion) for suggestion in suggestions]
            
            with open(self.suggestions_path, 'w', encoding='utf-8') as f:
                json.dump(suggestions_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 提案保存エラー: {e}")
    
    def _save_results(self, results: List[CorrectionResult]) -> None:
        """修正結果保存"""
        try:
            # 既存結果読み込み
            existing_results = []
            if self.results_path.exists():
                with open(self.results_path, 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
            
            # 新しい結果追加
            new_results_data = [asdict(result) for result in results]
            existing_results.extend(new_results_data)
            
            # サイズ制限（最新1000件）
            if len(existing_results) > 1000:
                existing_results = existing_results[-1000:]
            
            with open(self.results_path, 'w', encoding='utf-8') as f:
                json.dump(existing_results, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 結果保存エラー: {e}")
    
    def _update_statistics(self, results: List[CorrectionResult]) -> None:
        """統計更新"""
        
        successful_results = [r for r in results if r.success]
        self.statistics["success_rate"] = len(successful_results) / len(results) if results else 0.0
        
        # 統計保存
        try:
            stats_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "statistics": self.statistics,
                "pattern_matcher_stats": self.pattern_matcher.statistics
            }
            
            with open(self.statistics_path, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 統計保存エラー: {e}")
    
    def get_correction_summary(self) -> Dict[str, Any]:
        """修正サマリー取得"""
        
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "statistics": self.statistics,
            "pattern_matcher_stats": self.pattern_matcher.statistics,
            "gemini_available": self.gemini_integration is not None,
            "data_files": {
                "suggestions": self.suggestions_path.exists(),
                "results": self.results_path.exists(),
                "statistics": self.statistics_path.exists()
            }
        }

def main():
    """テスト実行"""
    print("🧪 AutoCorrectionEngine テスト開始")
    
    engine = AutoCorrectionEngine()
    
    # テストファイル解析
    test_file = "kumihan_formatter/core/utilities/logger.py"
    if os.path.exists(test_file):
        print(f"🔍 テストファイル解析: {test_file}")
        
        suggestions = engine.analyze_file(test_file)
        
        if suggestions:
            print(f"📋 修正提案: {len(suggestions)}件")
            
            for suggestion in suggestions[:3]:  # 最初の3件表示
                print(f"  - {suggestion.correction_type.value}: {suggestion.explanation}")
            
            # 修正適用テスト（手動ガイドのみ）
            print("\n🔧 修正適用テスト...")
            results = engine.apply_corrections(suggestions[:1], auto_apply=False, use_gemini=False)
            
            print(f"📊 適用結果: {len([r for r in results if r.success])}件成功")
        else:
            print("📋 修正提案なし")
    else:
        print(f"⚠️ テストファイルが見つかりません: {test_file}")
    
    # サマリー表示
    summary = engine.get_correction_summary()
    print(f"\n📊 AutoCorrectionEngine サマリー:")
    print(f"   総提案数: {summary['statistics']['total_suggestions']}")
    print(f"   成功率: {summary['statistics']['success_rate']:.1%}")
    print(f"   Gemini利用可能: {summary['gemini_available']}")
    
    print("✅ AutoCorrectionEngine テスト完了")

if __name__ == "__main__":
    main()