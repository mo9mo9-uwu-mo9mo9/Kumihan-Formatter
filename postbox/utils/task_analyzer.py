#!/usr/bin/env python3
"""
Task Analyzer for Flash 2.5 Optimization
ファイル→関数単位のタスク微分化・Flash 2.5向け指示生成
"""

import ast
import re
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json

class TaskAnalyzer:
    """Flash 2.5向けタスク微分化・分析エンジン"""

    def __init__(self):
        self.error_patterns = {
            "no-untyped-def": {
                "description": "関数の戻り値型注釈不足",
                "flash_instruction": "関数に -> 戻り値型 を追加してください",
                "complexity": "low",
                "example": "def func() -> str:"
            },
            "no-untyped-call": {
                "description": "型注釈なし関数の呼び出し",
                "flash_instruction": "# type: ignore[no-untyped-call] コメント追加",
                "complexity": "medium",
                "example": "result = untyped_func()  # type: ignore[no-untyped-call]"
            },
            "type-arg": {
                "description": "ジェネリック型引数不足",
                "flash_instruction": "List[str], Dict[str, int] など具体的な型を指定",
                "complexity": "medium",
                "example": "items: List[str] = []"
            }
        }

    def analyze_file_for_micro_tasks(self, file_path: str, error_type: str) -> List[Dict[str, Any]]:
        """ファイルを分析して関数レベルの微細タスクを生成"""

        print(f"🔍 ファイル分析開始: {file_path}")

        micro_tasks = []

        try:
            # 1. ファイル内容とAST解析
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # 2. mypy エラー詳細取得
            mypy_errors = self._get_detailed_mypy_errors(file_path, error_type)

            # 3. 関数レベルでのエラー特定
            function_errors = self._map_errors_to_functions(tree, mypy_errors, content)

            # 4. 微細タスク生成
            for func_name, errors in function_errors.items():
                if errors:  # エラーがある関数のみ
                    micro_task = self._create_micro_task(
                        file_path, func_name, errors, error_type, content
                    )
                    micro_tasks.append(micro_task)

            print(f"📋 生成された微細タスク: {len(micro_tasks)}件")

        except Exception as e:
            print(f"⚠️ ファイル分析エラー: {e}")
            # フォールバック: ファイル全体を1タスクとして処理
            micro_tasks = [self._create_fallback_task(file_path, error_type)]

        return micro_tasks

    def _get_detailed_mypy_errors(self, file_path: str, error_type: str) -> List[Dict[str, Any]]:
        """mypy実行による詳細エラー情報取得"""

        try:
            result = subprocess.run(
                ["python3", "-m", "mypy", "--strict", file_path],
                capture_output=True,
                text=True
            )

            errors = []
            for line in result.stdout.split('\n'):
                if error_type in line and 'error:' in line:
                    # mypy出力解析: file.py:line: error: message [error-code]
                    match = re.match(r'(.+):(\d+): error: (.+) \[(.+)\]', line.strip())
                    if match:
                        errors.append({
                            "file": match.group(1),
                            "line": int(match.group(2)),
                            "message": match.group(3),
                            "error_code": match.group(4)
                        })

            return errors

        except Exception as e:
            print(f"⚠️ mypy実行エラー: {e}")
            return []

    def _map_errors_to_functions(self, tree: ast.AST, errors: List[Dict], content: str) -> Dict[str, List[Dict]]:
        """エラーを関数ごとにマッピング"""

        # 関数の定義位置を取得
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions[node.name] = {
                    "start_line": node.lineno,
                    "end_line": node.end_lineno or node.lineno + 10,
                    "node": node
                }

        # エラーを関数にマッピング
        function_errors = {func_name: [] for func_name in functions.keys()}
        function_errors["_module_level"] = []  # モジュールレベルエラー

        for error in errors:
            error_line = error["line"]
            mapped = False

            for func_name, func_info in functions.items():
                if func_info["start_line"] <= error_line <= func_info["end_line"]:
                    function_errors[func_name].append(error)
                    mapped = True
                    break

            if not mapped:
                function_errors["_module_level"].append(error)

        return function_errors

    def _create_micro_task(self, file_path: str, func_name: str,
                          errors: List[Dict], error_type: str, content: str) -> Dict[str, Any]:
        """関数レベルの微細タスク作成"""

        error_pattern = self.error_patterns.get(error_type, {})

        # 関数のコード抽出
        lines = content.split('\n')
        func_code_lines = []
        in_function = False
        indent_level = 0

        for i, line in enumerate(lines, 1):
            if any(f"def {func_name}(" in line for error in errors if error["line"] == i):
                in_function = True
                indent_level = len(line) - len(line.lstrip())
                func_code_lines.append(f"{i}: {line}")
            elif in_function:
                current_indent = len(line) - len(line.lstrip()) if line.strip() else indent_level + 1
                if line.strip() and current_indent <= indent_level:
                    break
                func_code_lines.append(f"{i}: {line}")
                if len(func_code_lines) > 30:  # 長すぎる場合は切り取り
                    func_code_lines.append("... (truncated)")
                    break

        # Flash 2.5向け簡潔な指示生成
        flash_instruction = self._generate_flash_instruction(
            func_name, errors, error_type, error_pattern
        )

        return {
            "type": "micro_fix",
            "target_file": file_path,
            "target_function": func_name,
            "error_type": error_type,
            "error_count": len(errors),
            "errors": errors,
            "function_code": func_code_lines,
            "flash_instruction": flash_instruction,
            "complexity": error_pattern.get("complexity", "medium"),
            "estimated_time": len(errors) * 2  # 分
        }

    def _generate_flash_instruction(self, func_name: str, errors: List[Dict],
                                   error_type: str, error_pattern: Dict) -> str:
        """Flash 2.5向け具体的で簡潔な修正指示生成"""

        base_instruction = error_pattern.get("flash_instruction", "エラーを修正してください")
        example = error_pattern.get("example", "")

        instruction = f"""
🎯 修正対象: {func_name}関数
🔧 修正内容: {base_instruction}
📊 エラー数: {len(errors)}件

📝 具体的手順:
1. {func_name}関数を見つける
2. {base_instruction}
3. 修正例: {example}

⚠️ 注意:
- 既存のロジックは変更しない
- インポート文が必要な場合は追加
- 修正後の形式を正確に確認
"""

        # エラー詳細追加（最大3件まで）
        if errors:
            instruction += "\n🐛 修正対象エラー:\n"
            for i, error in enumerate(errors[:3], 1):
                instruction += f"{i}. Line {error['line']}: {error['message']}\n"

            if len(errors) > 3:
                instruction += f"   ... 他{len(errors) - 3}件\n"

        return instruction.strip()

    def _create_fallback_task(self, file_path: str, error_type: str) -> Dict[str, Any]:
        """フォールバック: ファイル全体タスク"""

        return {
            "type": "file_fix",
            "target_file": file_path,
            "target_function": "_whole_file",
            "error_type": error_type,
            "error_count": 1,
            "flash_instruction": f"ファイル全体の{error_type}エラーを修正してください",
            "complexity": "high",
            "estimated_time": 15
        }

    def create_step_by_step_plan(self, micro_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """微細タスク群から段階的実行計画を作成"""

        # 複雑度・所要時間でソート
        complexity_order = {"low": 1, "medium": 2, "high": 3}
        sorted_tasks = sorted(micro_tasks, key=lambda x: (
            complexity_order.get(x.get("complexity", "medium"), 2),
            x.get("estimated_time", 10)
        ))

        total_time = sum(task.get("estimated_time", 10) for task in sorted_tasks)

        plan = {
            "total_tasks": len(micro_tasks),
            "total_estimated_time": total_time,
            "execution_order": sorted_tasks,
            "batch_recommendations": self._create_batch_recommendations(sorted_tasks),
            "flash25_optimization": {
                "max_context_per_task": 2000,  # トークン制限
                "simple_instruction_style": True,
                "concrete_examples": True,
                "step_by_step": True
            }
        }

        return plan

    def _create_batch_recommendations(self, sorted_tasks: List[Dict]) -> List[Dict]:
        """バッチ処理推奨グループ作成"""

        batches = []
        current_batch = []
        current_time = 0

        for task in sorted_tasks:
            task_time = task.get("estimated_time", 10)

            # バッチサイズ制限（Flash 2.5のコンテキスト制限考慮）
            if current_time + task_time <= 20 and len(current_batch) < 3:
                current_batch.append(task)
                current_time += task_time
            else:
                if current_batch:
                    batches.append({
                        "batch_id": len(batches) + 1,
                        "tasks": current_batch,
                        "estimated_time": current_time,
                        "complexity": max(t.get("complexity", "medium") for t in current_batch)
                    })
                current_batch = [task]
                current_time = task_time

        # 最後のバッチ
        if current_batch:
            batches.append({
                "batch_id": len(batches) + 1,
                "tasks": current_batch,
                "estimated_time": current_time,
                "complexity": max(t.get("complexity", "medium") for t in current_batch)
            })

        return batches

def main():
    """テスト実行"""
    analyzer = TaskAnalyzer()

    # テストファイル分析
    test_file = "kumihan_formatter/core/utilities/logger.py"
    micro_tasks = analyzer.analyze_file_for_micro_tasks(test_file, "no-untyped-def")

    print(f"\n📊 分析結果:")
    print(f"微細タスク数: {len(micro_tasks)}")

    for task in micro_tasks:
        print(f"\n🎯 タスク: {task.get('target_function', 'unknown')}")
        print(f"   エラー数: {task.get('error_count', 0)}")
        print(f"   複雑度: {task.get('complexity', 'medium')}")
        print(f"   所要時間: {task.get('estimated_time', 10)}分")

    # 実行計画作成
    if micro_tasks:
        plan = analyzer.create_step_by_step_plan(micro_tasks)
        print(f"\n📋 実行計画:")
        print(f"総タスク数: {plan['total_tasks']}")
        print(f"総所要時間: {plan['total_estimated_time']}分")
        print(f"バッチ数: {len(plan['batch_recommendations'])}")

if __name__ == "__main__":
    main()
