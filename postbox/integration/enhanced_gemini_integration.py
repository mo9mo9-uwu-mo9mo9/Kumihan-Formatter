#!/usr/bin/env python3
"""
Enhanced Gemini Integration System - Complete Integration Test
全コンポーネント統合・DualAgentCoordinator連携システム
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from postbox.context.context_splitter import ContextSplitter, ContextChunk
    from postbox.context.inheritance_manager import ContextInheritanceManager
    from postbox.knowledge.knowledge_base import KnowledgeBase
    from postbox.templates.pattern_templates import PatternTemplateEngine
    from postbox.guidance.implementation_guidance import ImplementationGuidanceEngine
    from postbox.quality.quality_standards_manager import QualityStandardsManager
except ImportError as e:
    print(f"⚠️ Import error (expected during development): {e}")
    print("Continuing with mock implementation for testing...")


@dataclass
class EnhancedGeminiTask:
    """強化版Geminiタスク"""
    task_id: str
    original_task_data: Dict[str, Any]
    context_chunks: List[Any]  # ContextChunk
    inheritance_context: Dict[str, Any]
    knowledge_context: Dict[str, Any]
    implementation_guidance: Dict[str, Any]
    quality_requirements: Dict[str, Any]
    estimated_success_rate: float
    execution_plan: List[Dict[str, Any]]


class EnhancedGeminiIntegrator:
    """強化版Gemini統合システム"""
    
    def __init__(self):
        """初期化"""
        try:
            self.context_splitter = ContextSplitter(max_tokens_per_chunk=1800)
            self.inheritance_manager = ContextInheritanceManager()
            self.knowledge_base = KnowledgeBase()
            self.pattern_engine = PatternTemplateEngine()
            self.guidance_engine = ImplementationGuidanceEngine()
            self.quality_manager = QualityStandardsManager()
        except NameError:
            print("🔧 Running in mock mode - components not available")
            self._initialize_mocks()
        
        self.integration_stats = {
            "tasks_processed": 0,
            "chunks_generated": 0,
            "success_rate_improvements": [],
            "quality_improvements": [],
            "token_savings": 0
        }
    
    def _initialize_mocks(self):
        """モックコンポーネント初期化"""
        self.context_splitter = MockContextSplitter()
        self.inheritance_manager = MockInheritanceManager()
        self.knowledge_base = MockKnowledgeBase()
        self.pattern_engine = MockPatternEngine()
        self.guidance_engine = MockGuidanceEngine()
        self.quality_manager = MockQualityManager()
    
    def enhance_gemini_task(self, original_task_data: Dict[str, Any]) -> EnhancedGeminiTask:
        """
        Geminiタスク強化処理
        
        Args:
            original_task_data: 元のタスクデータ
            
        Returns:
            強化されたGeminiタスク
        """
        
        task_id = original_task_data.get('task_id', f"enhanced_{hash(str(original_task_data))}")
        task_type = original_task_data.get('type', 'modification')
        
        print(f"🚀 Geminiタスク強化開始: {task_id} ({task_type})")
        
        # Step 1: コンテキスト分割
        print("📋 Step 1: コンテキスト分割実行")
        context_chunks = self._split_task_context(original_task_data)
        
        # Step 2: 継承コンテキスト生成
        print("🔗 Step 2: 継承コンテキスト生成")
        inheritance_context = self._generate_inheritance_context(original_task_data, context_chunks)
        
        # Step 3: 知識ベース活用
        print("📚 Step 3: 知識ベース活用")
        knowledge_context = self._apply_knowledge_base(original_task_data, context_chunks)
        
        # Step 4: 実装ガイダンス生成
        print("🎯 Step 4: 実装ガイダンス生成")
        implementation_guidance = self._generate_implementation_guidance(original_task_data)
        
        # Step 5: 品質要件設定
        print("🔍 Step 5: 品質要件設定")
        quality_requirements = self._establish_quality_requirements(original_task_data)
        
        # Step 6: 成功率推定
        print("📊 Step 6: 成功率推定")
        estimated_success_rate = self._estimate_success_rate(
            original_task_data, context_chunks, knowledge_context, implementation_guidance
        )
        
        # Step 7: 実行計画生成
        print("⚡ Step 7: 実行計画生成")
        execution_plan = self._generate_execution_plan(
            context_chunks, inheritance_context, knowledge_context, implementation_guidance
        )
        
        enhanced_task = EnhancedGeminiTask(
            task_id=task_id,
            original_task_data=original_task_data,
            context_chunks=context_chunks,
            inheritance_context=inheritance_context,
            knowledge_context=knowledge_context,
            implementation_guidance=implementation_guidance,
            quality_requirements=quality_requirements,
            estimated_success_rate=estimated_success_rate,
            execution_plan=execution_plan
        )
        
        # 統計更新
        self.integration_stats["tasks_processed"] += 1
        self.integration_stats["chunks_generated"] += len(context_chunks)
        self.integration_stats["success_rate_improvements"].append(estimated_success_rate)
        
        print(f"✅ Geminiタスク強化完了: 成功率 {estimated_success_rate:.1%}")
        return enhanced_task
    
    def _split_task_context(self, task_data: Dict[str, Any]) -> List[Any]:
        """タスクコンテキスト分割"""
        
        task_type = task_data.get('type', 'modification')
        
        try:
            if task_type in ['new_implementation', 'hybrid_implementation', 'new_feature_development']:
                chunks = self.context_splitter.split_implementation_task(task_data)
            else:
                chunks = self.context_splitter.split_modification_task(task_data)
            
            print(f"   📦 {len(chunks)}チャンク生成完了")
            return chunks
            
        except Exception as e:
            print(f"   ⚠️ コンテキスト分割エラー: {e}")
            # フォールバック: 単一チャンクとして処理
            return [MockContextChunk(
                chunk_id="fallback_001",
                content=json.dumps(task_data, indent=2),
                estimated_tokens=500,
                dependencies=[],
                priority=5,
                chunk_type="fallback"
            )]
    
    def _generate_inheritance_context(self, task_data: Dict[str, Any], 
                                    chunks: List[Any]) -> Dict[str, Any]:
        """継承コンテキスト生成"""
        
        try:
            session_id = task_data.get('session_id', 'default_session')
            task_id = task_data.get('task_id', 'unknown_task')
            
            # セッションコンテキスト設定
            session_context = {
                "project_name": "Kumihan-Formatter",
                "session_type": task_data.get('type', 'modification'),
                "quality_standards": "mypy strict mode required",
                "coding_standards": "Black + isort formatting"
            }
            
            self.inheritance_manager.set_session_context(session_id, session_context)
            
            # タスクグループコンテキスト設定
            task_group_context = {
                "total_chunks": len(chunks),
                "task_complexity": self._assess_task_complexity(task_data),
                "target_files": task_data.get('target_files', [])
            }
            
            self.inheritance_manager.set_task_group_context(task_id, task_group_context)
            
            # 継承可能コンテキスト取得
            inherited_context = self.inheritance_manager.get_inherited_context(task_id, "TASK_GROUP")
            
            print(f"   🔗 継承コンテキスト生成: {len(inherited_context)}項目")
            return inherited_context
            
        except Exception as e:
            print(f"   ⚠️ 継承コンテキスト生成エラー: {e}")
            return {"error": str(e)}
    
    def _apply_knowledge_base(self, task_data: Dict[str, Any], chunks: List[Any]) -> Dict[str, Any]:
        """知識ベース活用"""
        
        try:
            task_type = task_data.get('type', 'modification')
            
            knowledge_context = {
                "project_context": self.knowledge_base.get_project_context(),
                "patterns": [],
                "guides": [],
                "solutions": []
            }
            
            # タスクタイプに応じた知識の活用
            if task_type in ['new_implementation', 'hybrid_implementation']:
                # 設計パターンの提案
                suggested_pattern = self._suggest_design_pattern(task_data)
                if suggested_pattern:
                    pattern_info = self.knowledge_base.get_design_pattern(suggested_pattern)
                    if pattern_info:
                        knowledge_context["patterns"].append(pattern_info)
                
                # パターンテンプレートの生成
                pattern_template = self._generate_pattern_template(task_data)
                if pattern_template:
                    knowledge_context["pattern_template"] = pattern_template
            
            # 実装ガイドの取得
            implementation_guides = self._get_implementation_guides(task_type)
            knowledge_context["guides"] = implementation_guides
            
            # エラー解決策の準備
            common_errors = self._get_common_error_solutions(task_type)
            knowledge_context["solutions"] = common_errors
            
            print(f"   📚 知識ベース活用: {len(knowledge_context['patterns'])}パターン, "
                  f"{len(knowledge_context['guides'])}ガイド, {len(knowledge_context['solutions'])}解決策")
            
            return knowledge_context
            
        except Exception as e:
            print(f"   ⚠️ 知識ベース活用エラー: {e}")
            return {"error": str(e)}
    
    def _generate_implementation_guidance(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """実装ガイダンス生成"""
        
        try:
            # 段階的ガイダンス生成
            step_by_step_guidance = self.guidance_engine.generate_step_by_step_guidance(task_data)
            
            # エラー回避ガイド生成
            error_avoidance_guide = self.guidance_engine.generate_error_avoidance_guide(task_data)
            
            # 品質ガイダンス生成
            quality_guidance = self.guidance_engine.generate_quality_guidance(task_data)
            
            guidance_data = {
                "step_by_step": [asdict(step) for step in step_by_step_guidance],
                "error_avoidance": error_avoidance_guide,
                "quality_guidance": quality_guidance,
                "total_steps": len(step_by_step_guidance)
            }
            
            print(f"   🎯 実装ガイダンス生成: {len(step_by_step_guidance)}ステップ")
            return guidance_data
            
        except Exception as e:
            print(f"   ⚠️ 実装ガイダンス生成エラー: {e}")
            return {"error": str(e)}
    
    def _establish_quality_requirements(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """品質要件設定"""
        
        try:
            # 基本品質要件
            base_requirements = {
                "syntax_accuracy": 1.0,
                "type_coverage": 0.95,
                "format_compliance": 1.0,
                "import_organization": 0.9,
                "minimum_overall_score": 0.85
            }
            
            # タスク複雑度に応じた調整
            complexity = self._assess_task_complexity(task_data)
            if complexity == "high":
                base_requirements["type_coverage"] = 0.9
                base_requirements["minimum_overall_score"] = 0.8
            elif complexity == "critical":
                base_requirements["type_coverage"] = 0.85
                base_requirements["minimum_overall_score"] = 0.75
            
            quality_requirements = {
                "standards": base_requirements,
                "validation_methods": [
                    "python -m py_compile",
                    "mypy --strict",
                    "black --check",
                    "isort --check-only"
                ],
                "complexity_level": complexity,
                "estimated_validation_time": 5  # minutes
            }
            
            print(f"   🔍 品質要件設定: {complexity}複雑度")
            return quality_requirements
            
        except Exception as e:
            print(f"   ⚠️ 品質要件設定エラー: {e}")
            return {"error": str(e)}
    
    def _estimate_success_rate(self, task_data: Dict[str, Any], chunks: List[Any],
                              knowledge_context: Dict[str, Any], guidance: Dict[str, Any]) -> float:
        """成功率推定"""
        
        base_rate = 0.30  # Flash 2.5基本成功率（30%と仮定）
        
        # 分割による改善
        chunk_improvement = min(0.25, len(chunks) * 0.05)  # チャンク分割効果
        
        # 知識ベース活用による改善
        knowledge_improvement = 0.15 if knowledge_context.get("patterns") else 0.1
        
        # ガイダンスによる改善
        guidance_improvement = 0.20 if guidance.get("step_by_step") else 0.1
        
        # エラー回避による改善
        error_avoidance_improvement = 0.10 if guidance.get("error_avoidance") else 0.05
        
        # 複雑度による調整
        complexity = self._assess_task_complexity(task_data)
        complexity_penalty = {"low": 0, "medium": -0.05, "high": -0.1, "critical": -0.15}.get(complexity, 0)
        
        estimated_rate = min(0.90, base_rate + chunk_improvement + knowledge_improvement + 
                           guidance_improvement + error_avoidance_improvement + complexity_penalty)
        
        return estimated_rate
    
    def _generate_execution_plan(self, chunks: List[Any], inheritance_context: Dict[str, Any],
                               knowledge_context: Dict[str, Any], guidance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """実行計画生成"""
        
        execution_plan = []
        
        # 1. 前処理ステップ
        execution_plan.append({
            "step_id": "preprocessing",
            "title": "前処理・環境確認",
            "actions": [
                "Import validation",
                "Syntax pre-check",
                "Context inheritance setup"
            ],
            "estimated_tokens": 200,
            "dependencies": []
        })
        
        # 2. チャンク実行ステップ
        for i, chunk in enumerate(chunks):
            if hasattr(chunk, 'chunk_id'):
                chunk_id = chunk.chunk_id
                estimated_tokens = getattr(chunk, 'estimated_tokens', 500)
            else:
                chunk_id = f"chunk_{i:03d}"
                estimated_tokens = 500
                
            execution_plan.append({
                "step_id": f"execute_{chunk_id}",
                "title": f"Chunk {i+1} 実行",
                "actions": [
                    f"Execute chunk: {chunk_id}",
                    "Apply knowledge context",
                    "Follow implementation guidance",
                    "Quality validation"
                ],
                "estimated_tokens": estimated_tokens,
                "dependencies": ["preprocessing"] if i == 0 else [f"execute_chunk_{i-1:03d}"]
            })
        
        # 3. 後処理ステップ
        execution_plan.append({
            "step_id": "postprocessing",
            "title": "後処理・品質確認",
            "actions": [
                "Overall quality assessment",
                "Integration testing",
                "Final validation",
                "Report generation"
            ],
            "estimated_tokens": 300,
            "dependencies": [f"execute_chunk_{len(chunks)-1:03d}"] if chunks else ["preprocessing"]
        })
        
        return execution_plan
    
    def generate_flash_optimized_instruction(self, enhanced_task: EnhancedGeminiTask) -> str:
        """Flash 2.5最適化指示生成"""
        
        task_data = enhanced_task.original_task_data
        chunks = enhanced_task.context_chunks
        guidance = enhanced_task.implementation_guidance
        
        # 最初のチャンクを取得（メイン実行用）
        primary_chunk = chunks[0] if chunks else None
        
        instruction = f"""
🚀 Flash 2.5 Enhanced Task Execution

## Task Overview
- Task ID: {enhanced_task.task_id}
- Type: {task_data.get('type', 'modification')}
- Target Files: {len(task_data.get('target_files', []))} files
- Estimated Success Rate: {enhanced_task.estimated_success_rate:.1%}

## Context Split Strategy
- Total Chunks: {len(chunks)}
- Current Chunk: {getattr(primary_chunk, 'chunk_id', 'N/A')}
- Token Limit: <1800 tokens per execution

## Knowledge Integration
"""
        
        # 知識ベース情報の追加
        knowledge = enhanced_task.knowledge_context
        if knowledge.get("patterns"):
            instruction += f"- Design Patterns Available: {len(knowledge['patterns'])}\n"
        if knowledge.get("guides"):
            instruction += f"- Implementation Guides: {len(knowledge['guides'])}\n"
        if knowledge.get("solutions"):
            instruction += f"- Error Solutions Prepared: {len(knowledge['solutions'])}\n"
        
        # 品質要件の追加
        quality_req = enhanced_task.quality_requirements
        if quality_req.get("standards"):
            instruction += f"\n## Quality Requirements\n"
            for standard, target in quality_req["standards"].items():
                instruction += f"- {standard}: {target}\n"
        
        # 実行ガイダンスの追加
        if guidance.get("step_by_step"):
            steps = guidance["step_by_step"]
            instruction += f"\n## Step-by-Step Guidance ({len(steps)} steps)\n"
            for i, step in enumerate(steps[:3]):  # 最初の3ステップのみ表示
                instruction += f"{i+1}. {step.get('title', 'Step')}: {step.get('description', '')}\n"
            if len(steps) > 3:
                instruction += f"... and {len(steps) - 3} more steps\n"
        
        # エラー回避情報の追加
        error_guide = guidance.get("error_avoidance", {})
        if error_guide.get("common_pitfalls"):
            instruction += f"\n## Error Avoidance (Top Pitfalls)\n"
            for pitfall in error_guide["common_pitfalls"][:2]:
                instruction += f"❌ Avoid: {pitfall}\n"
        
        # 実行指示
        instruction += f"""
## Execution Instructions
1. Focus on the primary chunk ({getattr(primary_chunk, 'chunk_id', 'main')})
2. Apply context inheritance from previous tasks
3. Follow implementation guidance step-by-step
4. Validate quality requirements continuously
5. Use provided error solutions when needed

## Success Criteria
- All syntax errors resolved
- Type annotations complete
- Quality thresholds met
- Integration with existing code maintained

Token Budget: ~{getattr(primary_chunk, 'estimated_tokens', 1500)} tokens for this execution
"""
        
        return instruction
    
    def _assess_task_complexity(self, task_data: Dict[str, Any]) -> str:
        """タスク複雑度評価"""
        
        file_count = len(task_data.get('target_files', []))
        task_type = task_data.get('type', 'modification')
        error_count = task_data.get('requirements', {}).get('error_count', 0)
        
        if error_count > 50 or file_count > 10 or task_type in ['new_feature_development']:
            return "critical"
        elif error_count > 20 or file_count > 5 or task_type in ['new_implementation', 'hybrid_implementation']:
            return "high"
        elif error_count > 5 or file_count > 2:
            return "medium"
        else:
            return "low"
    
    def _suggest_design_pattern(self, task_data: Dict[str, Any]) -> Optional[str]:
        """設計パターン提案"""
        
        task_type = task_data.get('type', '')
        
        patterns = {
            'new_implementation': 'Factory',
            'hybrid_implementation': 'Strategy', 
            'new_feature_development': 'Observer'
        }
        
        return patterns.get(task_type)
    
    def save_integration_report(self, enhanced_task: EnhancedGeminiTask, 
                              output_path: str = "tmp/integration_report.json") -> str:
        """統合レポート保存"""
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        report_data = {
            "task_summary": {
                "task_id": enhanced_task.task_id,
                "original_type": enhanced_task.original_task_data.get('type'),
                "estimated_success_rate": enhanced_task.estimated_success_rate,
                "chunks_generated": len(enhanced_task.context_chunks),
                "execution_steps": len(enhanced_task.execution_plan)
            },
            "enhancement_details": {
                "context_chunks": len(enhanced_task.context_chunks),
                "inheritance_context": len(enhanced_task.inheritance_context),
                "knowledge_patterns": len(enhanced_task.knowledge_context.get('patterns', [])),
                "implementation_steps": len(enhanced_task.implementation_guidance.get('step_by_step', [])),
                "quality_standards": len(enhanced_task.quality_requirements.get('standards', {}))
            },
            "integration_stats": self.integration_stats,
            "flash_instruction": self.generate_flash_optimized_instruction(enhanced_task)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 統合レポート保存: {output_path}")
        return output_path


# Mock implementations for testing when components aren't available
class MockContextChunk:
    def __init__(self, chunk_id, content, estimated_tokens, dependencies, priority, chunk_type):
        self.chunk_id = chunk_id
        self.content = content
        self.estimated_tokens = estimated_tokens
        self.dependencies = dependencies
        self.priority = priority
        self.chunk_type = chunk_type

class MockContextSplitter:
    def split_implementation_task(self, task_data):
        return [MockContextChunk(f"impl_{i:03d}", f"Implementation chunk {i}", 800, [], 5, "implementation") 
                for i in range(2)]
    
    def split_modification_task(self, task_data):
        return [MockContextChunk(f"mod_{i:03d}", f"Modification chunk {i}", 600, [], 5, "modification") 
                for i in range(3)]

class MockInheritanceManager:
    def set_session_context(self, session_id, context): pass
    def set_task_group_context(self, task_id, context): pass
    def get_inherited_context(self, task_id, scope): return {"mock": "inheritance_context"}

class MockKnowledgeBase:
    def get_project_context(self): return {"project": "Kumihan-Formatter"}
    def get_design_pattern(self, pattern): return {"pattern": pattern, "description": "Mock pattern"}

class MockPatternEngine:
    def generate_pattern(self, pattern_type, config, context): return "Mock pattern template"

class MockGuidanceEngine:
    def generate_step_by_step_guidance(self, task_data): 
        return [{"title": "Mock Step", "description": "Mock guidance"}]
    def generate_error_avoidance_guide(self, task_data): 
        return {"common_pitfalls": ["Mock pitfall"]}
    def generate_quality_guidance(self, task_data): 
        return {"complexity_level": "medium"}

class MockQualityManager:
    def evaluate_file_quality(self, file_path): 
        return {"overall_score": 0.8, "quality_level": "good"}


def main():
    """テスト実行"""
    
    print("🧪 Enhanced Gemini Integration System テスト開始")
    
    integrator = EnhancedGeminiIntegrator()
    
    # テストタスク1: 型注釈修正
    print("\n=== テスト1: 型注釈修正タスク ===")
    test_task_1 = {
        'task_id': 'type_annotation_001',
        'type': 'no-untyped-def',
        'target_files': [
            'postbox/context/context_splitter.py',
            'postbox/utils/gemini_helper.py'
        ],
        'requirements': {
            'error_type': 'no-untyped-def',
            'error_count': 15,
        },
        'session_id': 'test_session_001'
    }
    
    enhanced_task_1 = integrator.enhance_gemini_task(test_task_1)
    print(f"✅ 強化完了: 成功率 {enhanced_task_1.estimated_success_rate:.1%}")
    
    # Flash最適化指示生成テスト
    print("\n=== Flash 2.5最適化指示生成 ===")
    flash_instruction = integrator.generate_flash_optimized_instruction(enhanced_task_1)
    print("Flash指示の一部:")
    print(flash_instruction[:500] + "...\n")
    
    # テストタスク2: 新規実装
    print("=== テスト2: 新規実装タスク ===")
    test_task_2 = {
        'task_id': 'new_impl_001',
        'type': 'new_implementation',
        'target_files': [
            'postbox/new_module/data_processor.py',
            'postbox/new_module/config_manager.py'
        ],
        'requirements': {
            'implementation_spec': {
                'template_type': 'class',
                'class_name': 'DataProcessor',
                'methods': ['__init__', 'process', 'validate']
            }
        },
        'session_id': 'test_session_002'
    }
    
    enhanced_task_2 = integrator.enhance_gemini_task(test_task_2)
    print(f"✅ 強化完了: 成功率 {enhanced_task_2.estimated_success_rate:.1%}")
    
    # 統合レポート生成・保存
    print("\n=== 統合レポート生成 ===")
    report_path_1 = integrator.save_integration_report(enhanced_task_1, "tmp/integration_report_task1.json")
    report_path_2 = integrator.save_integration_report(enhanced_task_2, "tmp/integration_report_task2.json")
    
    # 統計サマリー
    print("\n=== 統合統計サマリー ===")
    stats = integrator.integration_stats
    print(f"処理タスク数: {stats['tasks_processed']}")
    print(f"生成チャンク数: {stats['chunks_generated']}")
    print(f"平均成功率向上: {sum(stats['success_rate_improvements'])/len(stats['success_rate_improvements']):.1%}")
    
    # DualAgentCoordinator連携テスト（模擬）
    print("\n=== DualAgentCoordinator連携テスト ===")
    print("📋 連携ポイント:")
    print("1. TaskAnalysis → Enhanced Task Analysis")
    print("2. Context Generation → Multi-Component Context")
    print("3. Quality Assessment → Integrated Quality Management")
    print("4. Execution Planning → Token-Optimized Planning")
    print("5. Success Rate Estimation → Predictive Enhancement")
    
    print("\n🎉 Enhanced Gemini Integration System テスト完了")
    print(f"📊 詳細レポート: {report_path_1}, {report_path_2}")


if __name__ == "__main__":
    main()