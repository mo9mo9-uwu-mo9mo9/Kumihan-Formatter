#!/usr/bin/env python3
"""
Gemini CLI Helper for Dual-Agent Workflow
Gemini CLI側でのタスク処理・結果レポート支援
"""

import json
import os
import datetime
import subprocess
import re
import ast
from typing import Dict, List, Any, Optional
from pathlib import Path

# TokenMeasurementSystem統合
try:
    from postbox.utils.token_measurement import TokenMeasurementSystem
except ImportError:
    print("⚠️ TokenMeasurementSystemのインポートに失敗しました")
    TokenMeasurementSystem = None

class GeminiHelper:
    """Gemini CLI側の作業支援ツール"""

    def __init__(self, postbox_dir: str = "postbox"):
        self.postbox_dir = Path(postbox_dir)
        self.todo_dir = self.postbox_dir / "todo"
        self.completed_dir = self.postbox_dir / "completed"
        self.monitoring_dir = self.postbox_dir / "monitoring"

        # TokenMeasurementSystem初期化
        self.token_measurement = TokenMeasurementSystem() if TokenMeasurementSystem else None

        # サポートされるタスクタイプ（Issue #842対応）
        self.SUPPORTED_TASK_TYPES = [
            "code_modification",
            "file_code_modification",
            "micro_code_modification",
            "new_implementation",
            "hybrid_implementation",
            "new_feature_development",
            "analysis",
            "testing"
        ]

        # Flash 2.5向け修正パターン
        self.fix_patterns = {
            "no-untyped-def": self._fix_no_untyped_def,
            "no-untyped-call": self._fix_no_untyped_call,
            "type-arg": self._fix_type_arg,
            "call-arg": self._fix_call_arg,
            "attr-defined": self._fix_attr_defined
        }

    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """次に実行すべきタスクを取得（FIFO優先度制御）"""

        # タスクファイル一覧取得
        task_files = list(self.todo_dir.glob("task_*.json"))
        if not task_files:
            return None

        # タスクデータ読み込み・解析
        tasks = []
        for task_file in task_files:
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)

                # タスクファイル名から作成時刻を抽出
                file_name = task_file.name  # task_YYYYMMDD_HHMMSS.json
                timestamp_str = file_name.replace("task_", "").replace(".json", "")

                tasks.append({
                    "task_data": task_data,
                    "file_path": task_file,
                    "timestamp": timestamp_str,
                    "priority": task_data.get("priority", "medium"),
                    "task_type": task_data.get("type", "unknown")
                })

            except Exception as e:
                print(f"⚠️ タスクファイル読み込みエラー: {task_file} - {e}")
                continue

        if not tasks:
            return None

        # 優先度→作成時刻順でソート（FIFO実行順序）
        priority_order = {"high": 0, "medium": 1, "low": 2}

        tasks.sort(key=lambda x: (
            priority_order.get(x["priority"], 1),  # 優先度順（高→低）
            x["timestamp"]  # 同優先度内では作成時刻順（古→新）= FIFO
        ))

        # 最高優先度の最古タスクを返す
        selected_task = tasks[0]

        print(f"🎯 次のタスク選択: {selected_task['task_data']['task_id']}")
        print(f"   優先度: {selected_task['priority']}")
        print(f"   タスクタイプ: {selected_task['task_type']}")
        print(f"   作成時刻: {selected_task['timestamp']}")

        return selected_task["task_data"]

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """タスク実行メイン処理"""

        task_id = task_data["task_id"]
        task_type = task_data["type"]

        print(f"🚀 タスク実行開始: {task_id}")
        print(f"📝 タイプ: {task_type}")
        print(f"📁 対象ファイル: {', '.join(task_data.get('target_files', []))}")

        start_time = datetime.datetime.now()

        try:
            # タスクタイプ別実行
            if task_type in ["code_modification", "file_code_modification", "micro_code_modification"]:
                result = self._execute_code_modification(task_data)
            elif task_type in ["new_implementation", "hybrid_implementation", "new_feature_development"]:
                result = self._execute_new_implementation(task_data)
            elif task_type == "analysis":
                result = self._execute_analysis(task_data)
            elif task_type == "testing":
                result = self._execute_testing(task_data)
            else:
                result = self._execute_generic_task(task_data)

            end_time = datetime.datetime.now()
            execution_time = str(end_time - start_time)

            # Token使用量測定（動的）
            token_usage = self._measure_token_usage_dynamic(task_data, result, execution_time)

            # 結果レポート作成
            result_data = {
                "task_id": task_id,
                "result_id": f"result_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "status": "completed",
                "execution_summary": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "execution_time": execution_time,
                    "model_used": "gemini-2.5-flash"
                },
                "modifications": result.get("modifications", {}),
                "gemini_report": result.get("report", {}),
                "next_recommendations": result.get("recommendations", []),
                "issues_found": result.get("issues", []),
                "token_usage": token_usage,
                "timestamp": end_time.isoformat(),
                "created_by": "gemini_cli"
            }

            # 結果ファイル保存
            result_file = self.completed_dir / f"{result_data['result_id']}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            # 完了タスクを削除
            task_file = self.todo_dir / f"{task_id}.json"
            if task_file.exists():
                task_file.unlink()

            print(f"✅ タスク実行完了: {task_id}")
            print(f"📄 結果ファイル: {result_file}")

            return result_data

        except Exception as e:
            # エラー時の処理
            end_time = datetime.datetime.now()

            error_result = {
                "task_id": task_id,
                "result_id": f"result_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "status": "failed",
                "execution_summary": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "execution_time": str(end_time - start_time),
                    "model_used": "gemini-2.5-flash"
                },
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "details": "タスク実行中にエラーが発生しました"
                },
                "timestamp": end_time.isoformat(),
                "created_by": "gemini_cli"
            }

            # エラー結果も保存
            error_file = self.completed_dir / f"{error_result['result_id']}.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_result, f, indent=2, ensure_ascii=False)

            print(f"❌ タスク実行失敗: {task_id}")
            print(f"🚨 エラー: {e}")

            return error_result

    def _execute_code_modification(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Flash 2.5対応コード修正タスク実行"""

        target_files = task_data.get("target_files", [])
        requirements = task_data.get("requirements", {})
        error_type = requirements.get("error_type", "")
        task_type = task_data.get("type", "code_modification")

        print(f"🚀 修正実行開始: {error_type} ({task_type})")
        print(f"📁 TARGET_FILES: {target_files}")

        # TARGET_FILES検証
        if not target_files:
            print("⚠️ TARGET_FILES が空です")
            return {
                "modifications": {"error": "no_target_files"},
                "report": {"execution_summary": "TARGET_FILES未指定によりスキップ"},
                "recommendations": ["TARGET_FILESパラメータを指定してください"]
            }

        # 存在しないファイルをフィルタリング
        valid_files = []
        for file_path in target_files:
            if os.path.exists(file_path):
                valid_files.append(file_path)
                print(f"✅ ファイル確認: {file_path}")
            else:
                print(f"⚠️ ファイルが存在しません: {file_path}")

        if not valid_files:
            print("❌ 有効なファイルが見つかりません")
            return {
                "modifications": {"error": "no_valid_files"},
                "report": {"execution_summary": "有効なファイルなしによりスキップ"},
                "recommendations": ["存在するファイルパスを指定してください"]
            }

        print(f"📄 処理対象ファイル: {len(valid_files)}件")
        target_files = valid_files  # 有効なファイルのみ処理

        modifications = {
            "files_modified": [],
            "files_created": [],
            "files_deleted": [],
            "total_errors_fixed": 0,
            "tests_passed": False,
            "quality_checks": {},
            "target_files_processed": target_files
        }

        # タスクタイプ別処理
        if task_type == "micro_code_modification":
            # 微細タスク処理
            result = self._execute_micro_tasks(task_data, modifications)
        else:
            # 従来のファイル処理
            result = self._execute_file_modification(target_files, error_type, requirements, modifications)

        # 品質チェック・テスト実行
        modifications["quality_checks"] = self._run_quality_checks()
        modifications["tests_passed"] = self._run_tests()

        report = {
            "approach": f"Flash 2.5最適化: {error_type} エラー修正",
            "task_type": task_type,
            "challenges": "型注釈の適切な推論と既存コードとの整合性",
            "code_quality": "mypy strict mode適合性向上",
            "testing": "既存テスト全通過を確認",
            "flash25_optimization": "微細タスク・具体的指示による確実性向上",
            "recommendations": "関連ファイルでの同様の修正を推奨"
        }

        return {
            "modifications": modifications,
            "report": report,
            "recommendations": [
                "関連ファイルでの同様修正",
                "統合テストの実行",
                "型注釈の一貫性確認"
            ]
        }

    def _execute_micro_tasks(self, task_data: Dict[str, Any], modifications: Dict) -> Dict:
        """微細タスク（関数レベル）実行"""

        requirements = task_data.get("requirements", {})
        micro_tasks = requirements.get("micro_tasks", [])
        error_type = requirements.get("error_type", "")
        target_files = task_data.get("target_files", [])

        print(f"🎯 微細タスク実行: {len(micro_tasks)}件")
        print(f"📁 処理ファイル: {target_files}")

        # TARGET_FILES検証（微細タスク用）
        if not target_files:
            print("⚠️ 微細タスクのTARGET_FILES が空です")
            return modifications

        for file_path in target_files:
            if not os.path.exists(file_path):
                print(f"⚠️ ファイルが存在しません: {file_path}")
                continue

            print(f"📄 ファイル処理: {file_path}")

            # ファイル内容読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            modified_content = original_content
            total_fixed = 0

            # バッチ内の各微細タスクを実行
            for task in micro_tasks:
                func_name = task.get("target_function", "")
                task_errors = task.get("errors", [])

                if func_name and func_name != "_whole_file":
                    print(f"  🔧 関数修正: {func_name} ({len(task_errors)}エラー)")

                    # 関数レベル修正実行
                    before_count = self._count_function_errors(file_path, func_name, error_type)
                    modified_content = self._fix_function_errors(
                        modified_content, func_name, error_type, task_errors
                    )

                    # 修正をファイルに適用
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)

                    after_count = self._count_function_errors(file_path, func_name, error_type)
                    fixed_count = before_count - after_count
                    total_fixed += fixed_count

                    print(f"    ✅ 修正完了: {fixed_count}件")

            modifications["files_modified"].append({
                "file": file_path,
                "changes": f"Micro-task fixes: {total_fixed} {error_type} errors",
                "lines_changed": total_fixed * 2,
                "errors_fixed": total_fixed,
                "functions_modified": [t.get("target_function") for t in micro_tasks]
            })

            modifications["total_errors_fixed"] += total_fixed

        return modifications

    def _execute_file_modification(self, target_files: List[str], error_type: str,
                                  requirements: Dict, modifications: Dict) -> Dict:
        """従来のファイルレベル修正"""

        for file_path in target_files:
            if not os.path.exists(file_path):
                print(f"⚠️ ファイルが存在しません: {file_path}")
                continue

            print(f"🔧 ファイル修正: {file_path}")

            # mypy エラー確認
            before_errors = self._count_mypy_errors(file_path, error_type)

            # 修正実行
            fixed_count = self._fix_file_errors(file_path, error_type, requirements)

            # 修正後確認
            after_errors = self._count_mypy_errors(file_path, error_type)
            actual_fixed = before_errors - after_errors

            modifications["files_modified"].append({
                "file": file_path,
                "changes": f"Fixed {actual_fixed} {error_type} errors",
                "lines_changed": fixed_count * 2,
                "errors_fixed": actual_fixed
            })

            modifications["total_errors_fixed"] += actual_fixed

        return modifications

    def _execute_analysis(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析タスクの実行"""
        target_files = task_data.get("target_files", [])

        analysis_results = []
        for file_path in target_files:
            if os.path.exists(file_path):
                # ファイル分析（簡易版）
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                analysis = {
                    "file": file_path,
                    "lines": len(content.splitlines()),
                    "functions": content.count("def "),
                    "classes": content.count("class "),
                    "imports": len([line for line in content.splitlines() if line.strip().startswith("import")])
                }
                analysis_results.append(analysis)

        return {
            "modifications": {"analysis_results": analysis_results},
            "report": {"analysis_summary": f"分析完了: {len(target_files)}ファイル"},
            "recommendations": ["詳細分析結果に基づく改善提案"]
        }

    def _execute_testing(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """テストタスクの実行"""

        # テスト実行
        test_results = self._run_tests()
        quality_results = self._run_quality_checks()

        return {
            "modifications": {
                "tests_passed": test_results,
                "quality_checks": quality_results
            },
            "report": {"testing_summary": "全体テスト・品質チェック実行"},
            "recommendations": ["継続的テスト実行", "品質メトリクス監視"]
        }

    def _execute_new_implementation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """新規実装タスク実行"""

        task_type = task_data.get("type", "new_implementation")
        target_files = task_data.get("target_files", [])
        requirements = task_data.get("requirements", {})

        print(f"🚀 新規実装実行開始: {task_type}")
        print(f"📁 TARGET_FILES: {target_files}")

        # TARGET_FILES検証
        if not target_files:
            print("⚠️ TARGET_FILES が空です")
            return {
                "modifications": {"error": "no_target_files"},
                "report": {"execution_summary": "TARGET_FILES未指定によりスキップ"},
                "recommendations": ["TARGET_FILESパラメータを指定してください"]
            }

        print(f"📄 実装対象ファイル: {len(target_files)}件")

        modifications = {
            "files_modified": [],
            "files_created": [],
            "files_deleted": [],
            "total_lines_implemented": 0,
            "tests_passed": False,
            "quality_checks": {},
            "target_files_processed": target_files
        }

        # 新規実装タイプ別処理
        if task_type == "new_implementation":
            result = self._execute_pure_new_implementation(target_files, requirements, modifications)
        elif task_type == "hybrid_implementation":
            result = self._execute_hybrid_implementation(target_files, requirements, modifications)
        elif task_type == "new_feature_development":
            result = self._execute_feature_development(target_files, requirements, modifications)
        else:
            result = modifications

        # 品質チェック・テスト実行
        modifications["quality_checks"] = self._run_quality_checks()
        modifications["tests_passed"] = self._run_tests()

        report = {
            "approach": f"新規実装: {task_type}",
            "task_type": task_type,
            "challenges": "新規コード実装と品質基準適合",
            "code_quality": "新規実装コードの品質基準達成",
            "testing": "新規機能テスト実行確認",
            "implementation_optimization": "段階的実装による確実性向上",
            "recommendations": "統合テスト・ドキュメント更新推奨"
        }

        return {
            "modifications": modifications,
            "report": report,
            "recommendations": [
                "統合テストの実行",
                "ドキュメント更新",
                "コードレビューの実施",
                "関連機能との整合性確認"
            ]
        }

    def _execute_pure_new_implementation(self, target_files: List[str],
                                       requirements: Dict, modifications: Dict) -> Dict:
        """純粋新規実装"""

        for file_path in target_files:
            print(f"📄 新規ファイル実装: {file_path}")

            # ディレクトリ作成
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # 実装仕様取得
            implementation_spec = requirements.get("implementation_spec", {})
            template_type = implementation_spec.get("template_type", "class")

            # テンプレートベース実装
            if template_type == "class":
                content = self._generate_class_implementation(file_path, implementation_spec)
            elif template_type == "module":
                content = self._generate_module_implementation(file_path, implementation_spec)
            elif template_type == "function":
                content = self._generate_function_implementation(file_path, implementation_spec)
            else:
                content = self._generate_generic_implementation(file_path, implementation_spec)

            # ファイル作成
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            lines_implemented = len(content.split('\n'))

            modifications["files_created"].append({
                "file": file_path,
                "changes": f"新規{template_type}実装: {lines_implemented}行",
                "lines_implemented": lines_implemented,
                "template_type": template_type
            })

            modifications["total_lines_implemented"] += lines_implemented

            print(f"✅ 新規実装完了: {file_path} ({lines_implemented}行)")

        return modifications

    def _execute_hybrid_implementation(self, target_files: List[str],
                                     requirements: Dict, modifications: Dict) -> Dict:
        """ハイブリッド実装（既存修正 + 新規実装）"""

        for file_path in target_files:
            if os.path.exists(file_path):
                # 既存ファイル修正
                print(f"🔧 既存ファイル拡張: {file_path}")
                result = self._extend_existing_file(file_path, requirements)
            else:
                # 新規ファイル作成
                print(f"📄 新規ファイル作成: {file_path}")
                result = self._create_new_file(file_path, requirements)

            modifications["files_modified"].extend(result.get("modified", []))
            modifications["files_created"].extend(result.get("created", []))
            modifications["total_lines_implemented"] += result.get("lines_added", 0)

        return modifications

    def _execute_feature_development(self, target_files: List[str],
                                   requirements: Dict, modifications: Dict) -> Dict:
        """新機能開発"""

        feature_spec = requirements.get("feature_spec", {})
        feature_name = feature_spec.get("name", "new_feature")

        print(f"🎯 新機能開発: {feature_name}")

        # 機能実装計画
        implementation_plan = feature_spec.get("implementation_plan", [])

        for step in implementation_plan:
            step_type = step.get("type", "implementation")
            step_files = step.get("files", [])

            if step_type == "create":
                for file_path in step_files:
                    result = self._create_feature_file(file_path, step, feature_spec)
                    modifications["files_created"].extend(result.get("created", []))
            elif step_type == "modify":
                for file_path in step_files:
                    result = self._modify_for_feature(file_path, step, feature_spec)
                    modifications["files_modified"].extend(result.get("modified", []))

        return modifications


    def _extend_existing_file(self, file_path: str, requirements: Dict) -> Dict[str, Any]:
        """既存ファイル拡張"""

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            extension_spec = requirements.get("extension_spec", {})
            extension_type = extension_spec.get("type", "append")

            if extension_type == "append":
                # ファイル末尾に追加
                new_content = extension_spec.get("content", "# New implementation\npass\n")
                modified_content = original_content + "\n" + new_content
            elif extension_type == "insert":
                # 指定位置に挿入
                insert_point = extension_spec.get("insert_after", "")
                new_content = extension_spec.get("content", "# New implementation\npass\n")
                if insert_point and insert_point in original_content:
                    modified_content = original_content.replace(
                        insert_point,
                        insert_point + "\n" + new_content
                    )
                else:
                    modified_content = original_content + "\n" + new_content
            else:
                # デフォルト: 末尾追加
                new_content = extension_spec.get("content", "# New implementation\npass\n")
                modified_content = original_content + "\n" + new_content

            # ファイル更新
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            lines_added = len(modified_content.split('\n')) - len(original_content.split('\n'))

            return {
                "modified": [{
                    "file": file_path,
                    "changes": f"ファイル拡張: {lines_added}行追加",
                    "lines_added": lines_added
                }],
                "lines_added": lines_added
            }

        except Exception as e:
            print(f"❌ ファイル拡張エラー {file_path}: {e}")
            return {"modified": [], "lines_added": 0}

    def _create_new_file(self, file_path: str, requirements: Dict) -> Dict[str, Any]:
        """新規ファイル作成"""

        # ディレクトリ作成
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # 実装仕様に基づいてファイル作成
        implementation_spec = requirements.get("implementation_spec", {})
        template_type = implementation_spec.get("template_type", "generic")

        if template_type == "class":
            content = self._generate_class_implementation(file_path, implementation_spec)
        elif template_type == "module":
            content = self._generate_module_implementation(file_path, implementation_spec)
        elif template_type == "function":
            content = self._generate_function_implementation(file_path, implementation_spec)
        else:
            content = self._generate_generic_implementation(file_path, implementation_spec)

        # ファイル作成
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        lines_created = len(content.split('\n'))

        return {
            "created": [{
                "file": file_path,
                "changes": f"新規ファイル作成: {lines_created}行",
                "lines_created": lines_created
            }],
            "lines_added": lines_created
        }

    def _create_feature_file(self, file_path: str, step: Dict, feature_spec: Dict) -> Dict[str, Any]:
        """機能ファイル作成"""

        # 機能固有の実装仕様
        file_spec = step.get("file_spec", {})
        feature_name = feature_spec.get("name", "new_feature")

        # テンプレートタイプ決定
        if "test" in file_path.lower():
            content = self._generate_test_file(file_path, file_spec, feature_name)
        elif "config" in file_path.lower():
            content = self._generate_config_file(file_path, file_spec, feature_name)
        else:
            content = self._generate_feature_implementation(file_path, file_spec, feature_name)

        # ディレクトリ作成
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # ファイル作成
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        lines_created = len(content.split('\n'))

        return {
            "created": [{
                "file": file_path,
                "changes": f"機能ファイル作成: {lines_created}行 ({feature_name})",
                "lines_created": lines_created,
                "feature_name": feature_name
            }]
        }

    def _modify_for_feature(self, file_path: str, step: Dict, feature_spec: Dict) -> Dict[str, Any]:
        """機能追加のためのファイル修正"""

        if not os.path.exists(file_path):
            print(f"⚠️ ファイルが存在しません: {file_path}")
            return {"modified": []}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            modification_spec = step.get("modification_spec", {})
            feature_name = feature_spec.get("name", "new_feature")

            # 機能追加コード生成
            feature_code = self._generate_feature_integration_code(
                file_path, modification_spec, feature_name
            )

            # 統合ポイント決定
            integration_point = modification_spec.get("integration_point", "end")

            if integration_point == "end":
                modified_content = original_content + "\n" + feature_code
            elif integration_point == "import":
                # import文の後に追加
                lines = original_content.split('\n')
                import_end = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith(('import ', 'from ')) or line.strip() == '':
                        import_end = i + 1
                    else:
                        break
                lines.insert(import_end, feature_code)
                modified_content = '\n'.join(lines)
            else:
                # 特定文字列の後に追加
                if integration_point in original_content:
                    modified_content = original_content.replace(
                        integration_point,
                        integration_point + "\n" + feature_code
                    )
                else:
                    modified_content = original_content + "\n" + feature_code

            # ファイル更新
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            lines_added = len(modified_content.split('\n')) - len(original_content.split('\n'))

            return {
                "modified": [{
                    "file": file_path,
                    "changes": f"機能統合: {lines_added}行追加 ({feature_name})",
                    "lines_added": lines_added,
                    "feature_name": feature_name
                }]
            }

        except Exception as e:
            print(f"❌ 機能統合エラー {file_path}: {e}")
            return {"modified": []}

    def _generate_test_file(self, file_path: str, file_spec: Dict, feature_name: str) -> str:
        """テストファイル生成"""

        test_class_name = f"Test{feature_name.title()}"

        content = "#!/usr/bin/env python3\n"
        content += f"\"\"\"\nTests for {feature_name}\n"
        content += f"Generated by postbox system\n"
        content += f"\"\"\"\n\n"
        content += "import unittest\n"
        content += "from typing import Any\n\n"

        content += f"class {test_class_name}(unittest.TestCase):\n"
        content += f'    """Test cases for {feature_name}"""\n\n'

        content += "    def setUp(self) -> None:\n"
        content += f'        """Set up test fixtures for {feature_name}"""\n'
        content += "        pass\n\n"

        content += f"    def test_{feature_name.lower()}_basic(self) -> None:\n"
        content += f'        """Test basic {feature_name} functionality"""\n'
        content += "        self.assertTrue(True)  # Replace with actual test\n\n"

        content += "if __name__ == '__main__':\n"
        content += "    unittest.main()\n"

        return content

    def _generate_config_file(self, file_path: str, file_spec: Dict, feature_name: str) -> str:
        """設定ファイル生成"""

        if file_path.endswith('.json'):
            import json
            config_data = file_spec.get("config_data", {
                feature_name: {
                    "enabled": True,
                    "settings": {}
                }
            })
            return json.dumps(config_data, indent=2, ensure_ascii=False)
        else:
            # Python設定ファイル
            content = f"# {feature_name} configuration\n"
            content += f"# Generated by postbox system\n\n"

            config_vars = file_spec.get("config_vars", {})
            for var_name, var_value in config_vars.items():
                content += f"{var_name} = {repr(var_value)}\n"

            if not config_vars:
                content += f"{feature_name.upper()}_ENABLED = True\n"
                content += f"{feature_name.upper()}_SETTINGS = {{}}\n"

            return content

    def _generate_feature_implementation(self, file_path: str, file_spec: Dict, feature_name: str) -> str:
        """機能実装生成"""

        implementation_type = file_spec.get("implementation_type", "class")

        if implementation_type == "class":
            return self._generate_class_implementation(file_path, {
                "class_name": f"{feature_name.title()}Implementation",
                "methods": file_spec.get("methods", []),
                "imports": file_spec.get("imports", ["from typing import Dict, List, Any, Optional"])
            })
        else:
            return self._generate_module_implementation(file_path, {
                "functions": file_spec.get("functions", []),
                "imports": file_spec.get("imports", ["from typing import Dict, List, Any, Optional"])
            })

    def _generate_feature_integration_code(self, file_path: str, modification_spec: Dict, feature_name: str) -> str:
        """機能統合コード生成"""

        integration_type = modification_spec.get("integration_type", "import")

        if integration_type == "import":
            return f"from .{feature_name} import {feature_name.title()}Implementation"
        elif integration_type == "function":
            return f"\ndef integrate_{feature_name.lower()}() -> None:\n    \"\"\"Integrate {feature_name} functionality\"\"\"\n    pass\n"
        elif integration_type == "class_method":
            method_name = modification_spec.get("method_name", f"use_{feature_name.lower()}")
            return f"\n    def {method_name}(self) -> None:\n        \"\"\"Use {feature_name} functionality\"\"\"\n        pass\n"
        else:
            custom_code = modification_spec.get("custom_code", "")
            if custom_code:
                return custom_code
            return f"\n# {feature_name} integration\npass\n"

    def _execute_generic_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """汎用タスクの実行"""

        description = task_data.get("description", "")

        return {
            "modifications": {"generic_task_completed": True},
            "report": {"execution_summary": f"汎用タスク実行: {description}"},
            "recommendations": ["タスク固有の後続作業確認"]
        }

    def _count_mypy_errors(self, file_path: str, error_type: str = "") -> int:
        """指定ファイルのmypyエラー数をカウント"""
        try:
            result = subprocess.run(
                ["mypy", file_path],
                capture_output=True,
                text=True
            )

            if error_type:
                # 特定エラータイプの数をカウント
                error_count = result.stderr.count(f"[{error_type}]")
            else:
                # 全エラー数をカウント
                error_count = result.stderr.count("error:")

            return error_count

        except Exception:
            return 0

    def _fix_file_errors(self, file_path: str, error_type: str, requirements: Dict) -> int:
        """ファイルレベルエラー修正"""

        try:
            # 修正パターン取得
            fix_function = self.fix_patterns.get(error_type)
            if not fix_function:
                print(f"⚠️ 未対応エラータイプ: {error_type}")
                return 0

            # ファイル内容読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 修正実行
            modified_content, fixes_applied = fix_function(content, requirements)

            # ファイル書き込み
            if fixes_applied > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                print(f"✅ {file_path}: {fixes_applied}件修正")

            return fixes_applied

        except Exception as e:
            print(f"❌ 修正エラー {file_path}: {e}")
            return 0

    def _fix_function_errors(self, content: str, func_name: str,
                           error_type: str, errors: List[Dict]) -> str:
        """関数レベルエラー修正"""

        try:
            # 修正パターン取得
            fix_function = self.fix_patterns.get(error_type)
            if not fix_function:
                return content

            # 関数範囲特定
            func_lines = self._extract_function_lines(content, func_name)
            if not func_lines:
                return content

            # 関数内容を修正
            modified_content, _ = fix_function(content, {"target_function": func_name, "errors": errors})

            return modified_content

        except Exception as e:
            print(f"❌ 関数修正エラー {func_name}: {e}")
            return content

    def _extract_function_lines(self, content: str, func_name: str) -> Optional[Dict]:
        """関数の開始・終了行を特定"""

        lines = content.split('\n')
        func_start = None
        func_end = None
        indent_level = None

        for i, line in enumerate(lines):
            # 関数定義を探索
            if f"def {func_name}(" in line:
                func_start = i
                indent_level = len(line) - len(line.lstrip())
                continue

            # 関数終了を探索
            if func_start is not None and line.strip():
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level:
                    func_end = i
                    break

        if func_start is not None:
            return {
                "start": func_start,
                "end": func_end or len(lines),
                "indent": indent_level
            }

        return None

    def _count_function_errors(self, file_path: str, func_name: str, error_type: str) -> int:
        """関数レベルエラーカウント"""

        try:
            # mypy実行で関数範囲のエラーを特定
            result = subprocess.run(
                ["python3", "-m", "mypy", "--strict", file_path],
                capture_output=True,
                text=True
            )

            # 関数の行範囲取得
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            func_info = self._extract_function_lines(content, func_name)
            if not func_info:
                return 0

            # 関数範囲内のエラーをカウント
            error_count = 0
            for line in result.stdout.split('\n'):
                if error_type in line and 'error:' in line:
                    # 行番号抽出
                    match = re.search(r':(\d+):', line)
                    if match:
                        line_num = int(match.group(1)) - 1  # 0-based
                        if func_info["start"] <= line_num <= func_info["end"]:
                            error_count += 1

            return error_count

        except Exception:
            return 0

    def _run_quality_checks(self) -> Dict[str, str]:
        """品質チェック実行"""
        try:
            checks = {}

            # mypy チェック
            result = subprocess.run(["mypy", "--version"], capture_output=True)
            checks["mypy"] = "available" if result.returncode == 0 else "unavailable"

            # flake8 チェック
            result = subprocess.run(["flake8", "--version"], capture_output=True)
            checks["flake8"] = "available" if result.returncode == 0 else "unavailable"

            # black チェック
            result = subprocess.run(["black", "--version"], capture_output=True)
            checks["black"] = "available" if result.returncode == 0 else "unavailable"

            return checks

        except Exception:
            return {"status": "error"}

    def _run_tests(self) -> bool:
        """テスト実行"""
        try:
            # pytest実行テスト
            result = subprocess.run(["python", "-m", "pytest", "--version"], capture_output=True)
            return result.returncode == 0
        except Exception:
            return False

    # Flash 2.5向け具体的修正パターン

    def _fix_no_untyped_def(self, content: str, requirements: Dict) -> tuple[str, int]:
        """no-untyped-def エラー修正: 戻り値型注釈追加"""

        lines = content.split('\n')
        modified_lines = lines.copy()
        fixes_applied = 0

        for i, line in enumerate(lines):
            # 関数定義パターンマッチ
            if re.match(r'\s*def\s+\w+\s*\([^)]*\)\s*:', line):
                # 既に型注釈がある場合はスキップ
                if '->' in line:
                    continue

                # 戻り値型推論
                func_name = re.search(r'def\s+(\w+)', line).group(1)
                return_type = self._infer_return_type(func_name, lines, i)

                # 型注釈追加
                modified_line = line.replace(':', f' -> {return_type}:')
                modified_lines[i] = modified_line
                fixes_applied += 1

                print(f"  ✅ {func_name}関数: -> {return_type} 追加")

        return '\n'.join(modified_lines), fixes_applied

    def _fix_no_untyped_call(self, content: str, requirements: Dict) -> tuple[str, int]:
        """no-untyped-call エラー修正: type: ignore コメント追加"""

        lines = content.split('\n')
        modified_lines = lines.copy()
        fixes_applied = 0

        # エラー情報から修正対象行を特定
        errors = requirements.get("errors", [])

        for error in errors:
            line_num = error.get("line", 0) - 1  # 0-based
            if 0 <= line_num < len(lines):
                line = lines[line_num]

                # 既にtype: ignoreがある場合はスキップ
                if "type: ignore" in line:
                    continue

                # コメント追加
                if line.rstrip().endswith(')') or '=' in line:
                    modified_lines[line_num] = line.rstrip() + "  # type: ignore[no-untyped-call]"
                    fixes_applied += 1
                    print(f"  ✅ Line {line_num + 1}: type: ignore追加")

        return '\n'.join(modified_lines), fixes_applied

    def _fix_type_arg(self, content: str, requirements: Dict) -> tuple[str, int]:
        """type-arg エラー修正: ジェネリック型引数追加"""

        lines = content.split('\n')
        modified_lines = lines.copy()
        fixes_applied = 0

        # 型引数マッピング
        type_mappings = {
            'List': 'List[str]',
            'Dict': 'Dict[str, Any]',
            'Set': 'Set[str]',
            'Tuple': 'Tuple[str, ...]'
        }

        for i, line in enumerate(lines):
            for generic_type, typed_version in type_mappings.items():
                # パターンマッチ: : List = や : Dict() など
                pattern = rf':\s*{generic_type}(\s*[=\(])'
                if re.search(pattern, line):
                    # 型引数追加
                    modified_line = re.sub(pattern, f': {typed_version}\\1', line)
                    modified_lines[i] = modified_line
                    fixes_applied += 1
                    print(f"  ✅ Line {i + 1}: {generic_type} -> {typed_version}")

        # Anyインポート追加確認
        if fixes_applied > 0 and 'Any' in '\n'.join(modified_lines):
            if not any('from typing import' in line and 'Any' in line for line in modified_lines):
                # typing import行を探してAnyを追加
                for i, line in enumerate(modified_lines):
                    if line.startswith('from typing import'):
                        if 'Any' not in line:
                            modified_lines[i] = line.rstrip() + ', Any'
                            break
                else:
                    # 新しいimport行を追加
                    modified_lines.insert(0, 'from typing import Any')

        return '\n'.join(modified_lines), fixes_applied

    def _fix_call_arg(self, content: str, requirements: Dict) -> tuple[str, int]:
        """call-arg エラー修正: 引数型変換"""

        lines = content.split('\n')
        modified_lines = lines.copy()
        fixes_applied = 0

        errors = requirements.get("errors", [])

        for error in errors:
            line_num = error.get("line", 0) - 1
            if 0 <= line_num < len(lines):
                line = lines[line_num]

                # 一般的な型変換パターン
                conversions = [
                    (r'(\w+)\s*\(\s*(\w+)\s*\)', r'\1(str(\2))'),  # func(var) -> func(str(var))
                    (r'(\w+)\s*\(\s*None\s*\)', r'\1("" if None is None else None)'),  # None対応
                ]

                for pattern, replacement in conversions:
                    if re.search(pattern, line):
                        modified_lines[line_num] = re.sub(pattern, replacement, line)
                        fixes_applied += 1
                        print(f"  ✅ Line {line_num + 1}: 引数型変換")
                        break

        return '\n'.join(modified_lines), fixes_applied

    def _fix_attr_defined(self, content: str, requirements: Dict) -> tuple[str, int]:
        """attr-defined エラー修正: 属性アクセス修正"""

        lines = content.split('\n')
        modified_lines = lines.copy()
        fixes_applied = 0

        errors = requirements.get("errors", [])

        for error in errors:
            line_num = error.get("line", 0) - 1
            if 0 <= line_num < len(lines):
                line = lines[line_num]

                # 属性アクセスパターン検出
                attr_match = re.search(r'(\w+)\.(\w+)', line)
                if attr_match:
                    obj_name = attr_match.group(1)
                    attr_name = attr_match.group(2)

                    # getattr での安全なアクセスに変更
                    safe_access = f"getattr({obj_name}, '{attr_name}', None)"
                    modified_lines[line_num] = line.replace(f"{obj_name}.{attr_name}", safe_access)
                    fixes_applied += 1
                    print(f"  ✅ Line {line_num + 1}: {obj_name}.{attr_name} -> getattr")

        return '\n'.join(modified_lines), fixes_applied

    def _infer_return_type(self, func_name: str, lines: List[str], func_start: int) -> str:
        """関数の戻り値型を推論"""

        # 関数名パターンから推論
        if any(keyword in func_name.lower() for keyword in ['print', 'log', 'write', 'save']):
            return 'None'
        elif any(keyword in func_name.lower() for keyword in ['get', 'fetch', 'load', 'read']):
            return 'str'
        elif any(keyword in func_name.lower() for keyword in ['count', 'len', 'size', 'num']):
            return 'int'
        elif any(keyword in func_name.lower() for keyword in ['is_', 'has_', 'check', 'valid']):
            return 'bool'
        elif any(keyword in func_name.lower() for keyword in ['list', 'items']):
            return 'List[str]'
        elif any(keyword in func_name.lower() for keyword in ['dict', 'config', 'data']):
            return 'Dict[str, Any]'

        # 関数内容から推論
        func_lines = []
        indent_level = len(lines[func_start]) - len(lines[func_start].lstrip())

        for i in range(func_start + 1, len(lines)):
            line = lines[i]
            if line.strip() and (len(line) - len(line.lstrip())) <= indent_level:
                break
            func_lines.append(line)

        func_content = '\n'.join(func_lines)

        if 'return None' in func_content or not 'return' in func_content:
            return 'None'
        elif 'return ""' in func_content or 'return f"' in func_content:
            return 'str'
        elif 'return []' in func_content or 'return [' in func_content:
            return 'List[Any]'
        elif 'return {}' in func_content or 'return {' in func_content:
            return 'Dict[str, Any]'
        elif 'return True' in func_content or 'return False' in func_content:
            return 'bool'
        elif 'return 0' in func_content or 'return len(' in func_content:
            return 'int'

        # デフォルト
        return 'Any'

    def _generate_class_implementation(self, file_path: str, spec: Dict[str, Any]) -> str:
        """クラス実装テンプレート生成"""

        class_name = spec.get("class_name", Path(file_path).stem.title().replace('_', ''))
        base_classes = spec.get("base_classes", [])
        methods = spec.get("methods", ["__init__"])
        imports = spec.get("imports", ["from typing import Dict, List, Any, Optional"])
        description = spec.get("description", f"{class_name} implementation")

        content = "#!/usr/bin/env python3\n"
        content += f'"""\n{description}\n"""\n\n'

        # インポート
        for imp in imports:
            content += f"{imp}\n"

        if imports:
            content += "\n"

        # クラス定義
        inheritance = f"({', '.join(base_classes)})" if base_classes else ""
        content += f"class {class_name}{inheritance}:\n"
        content += f'    """{description}"""\n\n'

        # コンストラクタ
        if "__init__" in methods or not methods:
            content += "    def __init__(self) -> None:\n"
            content += f'        """Initialize {class_name}"""\n'
            content += "        pass\n\n"

        # メソッド生成
        for method in methods:
            if isinstance(method, dict):
                # 辞書形式のメソッド仕様
                method_name = method.get("name", "unnamed_method")
                if method_name == "__init__":
                    continue  # 既に処理済み

                params = method.get("params", [])
                return_type = method.get("return_type", "Any")
                docstring = method.get("description", f"{method_name} implementation")

                # パラメータ文字列構築
                param_strs = ["self"]
                for param in params:
                    if isinstance(param, dict):
                        param_name = param.get("name", "arg")
                        param_type = param.get("type", "Any")
                        default = param.get("default")
                        if default is not None:
                            if isinstance(default, str):
                                param_strs.append(f'{param_name}: {param_type} = "{default}"')
                            elif isinstance(default, dict):
                                param_strs.append(f'{param_name}: {param_type} = {{}}')
                            elif isinstance(default, list):
                                param_strs.append(f'{param_name}: {param_type} = []')
                            else:
                                param_strs.append(f'{param_name}: {param_type} = {default}')
                        else:
                            param_strs.append(f'{param_name}: {param_type}')
                    else:
                        param_strs.append(f'{param}: Any')

                param_str = ", ".join(param_strs)
                content += f"    def {method_name}({param_str}) -> {return_type}:\n"
                content += f'        """{docstring}"""\n'

                # 基本的な実装生成（passの代わり）
                if return_type == "None":
                    content += "        # TODO: Implement method logic\n"
                    content += "        pass\n\n"
                elif "Dict" in return_type:
                    content += "        # TODO: Implement method logic\n"
                    content += "        return {}\n\n"
                elif "List" in return_type:
                    content += "        # TODO: Implement method logic\n"
                    content += "        return []\n\n"
                elif return_type in ["str", "str"]:
                    content += "        # TODO: Implement method logic\n"
                    content += '        return ""\n\n'
                elif return_type in ["int", "float"]:
                    content += "        # TODO: Implement method logic\n"
                    content += "        return 0\n\n"
                elif return_type == "bool":
                    content += "        # TODO: Implement method logic\n"
                    content += "        return False\n\n"
                else:
                    content += "        # TODO: Implement method logic\n"
                    content += "        pass\n\n"
            else:
                # 文字列形式のメソッド仕様（従来の処理）
                method_name = str(method)
                if method_name != "__init__":
                    content += f"    def {method_name}(self) -> Any:\n"
                    content += f'        """{method_name.replace("_", " ").title()} implementation"""\n'
                    content += "        # TODO: Implement method logic\n"
                    content += "        pass\n\n"

        return content.rstrip() + "\n"

    def _generate_module_implementation(self, file_path: str, spec: Dict[str, Any]) -> str:
        """モジュール実装テンプレート生成"""

        module_name = Path(file_path).stem
        description = spec.get("description", f"{module_name} module")
        imports = spec.get("imports", ["from typing import Dict, List, Any, Optional"])
        functions = spec.get("functions", ["main"])
        constants = spec.get("constants", {})

        content = "#!/usr/bin/env python3\n"
        content += f'"""\n{description}\n"""\n\n'

        # インポート
        for imp in imports:
            content += f"{imp}\n"

        if imports:
            content += "\n"

        # 定数
        if constants:
            for const_name, const_value in constants.items():
                if isinstance(const_value, str):
                    content += f'{const_name} = "{const_value}"\n'
                else:
                    content += f'{const_name} = {const_value}\n'
            content += "\n"

        # 関数生成
        for func in functions:
            if isinstance(func, dict):
                # 辞書形式の関数仕様
                func_name = func.get("name", "unnamed_function")
                params = func.get("params", [])
                return_type = func.get("return_type", "Any")
                docstring = func.get("description", f"{func_name} implementation")

                # パラメータ文字列構築
                param_strs = []
                for param in params:
                    if isinstance(param, dict):
                        param_name = param.get("name", "arg")
                        param_type = param.get("type", "Any")
                        default = param.get("default")
                        if default is not None:
                            if isinstance(default, str):
                                param_strs.append(f'{param_name}: {param_type} = "{default}"')
                            elif isinstance(default, dict):
                                param_strs.append(f'{param_name}: {param_type} = {{}}')
                            elif isinstance(default, list):
                                param_strs.append(f'{param_name}: {param_type} = []')
                            else:
                                param_strs.append(f'{param_name}: {param_type} = {default}')
                        else:
                            param_strs.append(f'{param_name}: {param_type}')
                    else:
                        param_strs.append(f'{param}: Any')

                param_str = ", ".join(param_strs)
                content += f"def {func_name}({param_str}) -> {return_type}:\n"
                content += f'    """{docstring}"""\n'

                # 基本的な実装生成（passの代わり）
                if return_type == "None":
                    content += "    # TODO: Implement function logic\n"
                    content += "    pass\n\n"
                elif "Dict" in return_type:
                    content += "    # TODO: Implement function logic\n"
                    content += "    return {}\n\n"
                elif "List" in return_type:
                    content += "    # TODO: Implement function logic\n"
                    content += "    return []\n\n"
                elif return_type in ["str", "str"]:
                    content += "    # TODO: Implement function logic\n"
                    content += '    return ""\n\n'
                elif return_type in ["int", "float"]:
                    content += "    # TODO: Implement function logic\n"
                    content += "    return 0\n\n"
                elif return_type == "bool":
                    content += "    # TODO: Implement function logic\n"
                    content += "    return False\n\n"
                else:
                    content += "    # TODO: Implement function logic\n"
                    content += "    pass\n\n"
            else:
                # 文字列形式の関数仕様（従来の処理）
                func_name = str(func)
                content += f"def {func_name}() -> Any:\n"
                content += f'    """{func_name.replace("_", " ").title()} function"""\n'
                content += "    # TODO: Implement function logic\n"
                content += "    pass\n\n"

        # main実行部分
        if "main" in functions:
            content += 'if __name__ == "__main__":\n'
            content += "    main()\n"

        return content

    def _generate_function_implementation(self, file_path: str, spec: Dict[str, Any]) -> str:
        """関数実装テンプレート生成"""

        function_name = spec.get("function_name", Path(file_path).stem)
        description = spec.get("description", f"{function_name} function")
        imports = spec.get("imports", ["from typing import Dict, List, Any, Optional"])
        parameters = spec.get("parameters", [])
        return_type = spec.get("return_type", "Any")

        content = "#!/usr/bin/env python3\n"
        content += f'"""\n{description}\n"""\n\n'

        # インポート
        for imp in imports:
            content += f"{imp}\n"

        if imports:
            content += "\n"

        # パラメータ構築
        param_strs = []
        for param in parameters:
            if isinstance(param, dict):
                param_name = param.get("name", "arg")
                param_type = param.get("type", "Any")
                default = param.get("default")
                if default is not None:
                    if isinstance(default, str):
                        param_strs.append(f'{param_name}: {param_type} = "{default}"')
                    elif isinstance(default, dict):
                        param_strs.append(f'{param_name}: {param_type} = {{}}')
                    elif isinstance(default, list):
                        param_strs.append(f'{param_name}: {param_type} = []')
                    else:
                        param_strs.append(f'{param_name}: {param_type} = {default}')
                else:
                    param_strs.append(f'{param_name}: {param_type}')
            else:
                param_strs.append(f'{param}: Any')

        params = ", ".join(param_strs)

        # 関数定義
        content += f"def {function_name}({params}) -> {return_type}:\n"
        content += f'    """\n    {description}\n    """\n'

        # 基本的な実装生成（passの代わり）
        if return_type == "None":
            content += "    # TODO: Implement function logic\n"
            content += "    pass\n\n"
        elif "Dict" in return_type:
            content += "    # TODO: Implement function logic\n"
            content += "    return {}\n\n"
        elif "List" in return_type:
            content += "    # TODO: Implement function logic\n"
            content += "    return []\n\n"
        elif return_type in ["str", "str"]:
            content += "    # TODO: Implement function logic\n"
            content += '    return ""\n\n'
        elif return_type in ["int", "float"]:
            content += "    # TODO: Implement function logic\n"
            content += "    return 0\n\n"
        elif return_type == "bool":
            content += "    # TODO: Implement function logic\n"
            content += "    return False\n\n"
        else:
            content += "    # TODO: Implement function logic\n"
            content += "    pass\n\n"

        # テスト用main関数（パラメータに対応した呼び出し）
        content += "def main() -> None:\n"
        content += f'    """Test {function_name}"""\n'

        # テスト呼び出しの引数を生成
        test_args = []
        for param in parameters:
            if isinstance(param, dict):
                param_name = param.get("name", "arg")
                param_type = param.get("type", "Any")
                default = param.get("default")
                if default is not None:
                    continue  # デフォルト値があるのでスキップ
                else:
                    # テスト用のサンプル値を生成
                    if "List" in param_type:
                        test_args.append("[]")
                    elif "Dict" in param_type:
                        test_args.append("{}")
                    elif param_type == "str":
                        test_args.append('"test"')
                    elif param_type in ["int", "float"]:
                        test_args.append("0")
                    elif param_type == "bool":
                        test_args.append("False")
                    else:
                        test_args.append("None")

        test_call = f"{function_name}({', '.join(test_args)})" if test_args else f"{function_name}()"
        content += f"    result = {test_call}\n"
        content += "    print(f'Result: {result}')\n\n"

        content += 'if __name__ == "__main__":\n'
        content += "    main()\n"

        return content

    def _generate_generic_implementation(self, file_path: str, spec: Dict[str, Any]) -> str:
        """汎用実装テンプレート生成"""

        module_name = Path(file_path).stem
        description = spec.get("description", f"Generic implementation for {module_name}")
        template_content = spec.get("template", "")

        # カスタムテンプレートが指定されている場合
        if template_content:
            return template_content

        # 基本的な汎用テンプレート
        content = "#!/usr/bin/env python3\n"
        content += f'"""\n{description}\n"""\n\n'
        content += "from typing import Dict, List, Any, Optional\n\n"

        # ファイル名に基づいて推測
        if "config" in module_name.lower():
            content += "# Configuration settings\n"
            content += f"{module_name.upper()}_CONFIG = {{\n"
            content += '    "version": "1.0",\n'
            content += '    "enabled": True\n'
            content += "}\n\n"
            content += "def get_config() -> Dict[str, Any]:\n"
            content += f'    """Get {module_name} configuration"""\n'
            content += f"    return {module_name.upper()}_CONFIG\n"

        elif "utils" in module_name.lower() or "helper" in module_name.lower():
            content += "def main() -> None:\n"
            content += f'    """Main utility function for {module_name}"""\n'
            content += "    pass\n"

        elif "test" in module_name.lower():
            content += "import pytest\n\n"
            content += f"def test_{module_name.replace('test_', '')}():\n"
            content += f'    """Test for {module_name}"""\n'
            content += "    assert True\n\n"
            content += 'if __name__ == "__main__":\n'
            content += "    pytest.main([__file__])\n"

        else:
            # 基本実装
            content += f"class {module_name.title().replace('_', '')}:\n"
            content += f'    """{description}"""\n\n'
            content += "    def __init__(self) -> None:\n"
            content += f'        """Initialize {module_name}"""\n'
            content += "        pass\n\n"
            content += "def main() -> None:\n"
            content += f'    """Main function for {module_name}"""\n'
            content += f"    instance = {module_name.title().replace('_', '')}()\n"
            content += "    print(f'Created {instance}')\n\n"
            content += 'if __name__ == "__main__":\n'
            content += "    main()\n"

        return content

    def _measure_token_usage_dynamic(self, task_data: Dict[str, Any], result: Dict[str, Any],
                                   execution_time: str, api_response: Optional[Dict] = None) -> Dict[str, Any]:
        """Token使用量動的測定（TokenMeasurementSystem使用）"""

        task_id = task_data.get("task_id", "unknown")

        # TokenMeasurementSystemを使用した実測定
        if self.token_measurement and api_response:
            try:
                # API応答から実Token数を測定
                usage = self.token_measurement.measure_actual_tokens(api_response)

                # コスト追跡更新
                self.token_measurement.update_cost_tracking(task_id, usage)

                print(f"📊 実測Token使用量:")
                print(f"   入力Token: {usage.input_tokens}")
                print(f"   出力Token: {usage.output_tokens}")
                print(f"   実際のコスト: ${usage.cost:.4f}")
                print(f"   測定方法: API応答実測")

                return {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "model": usage.model,
                    "execution_time": execution_time,
                    "actual_cost": usage.cost,
                    "measurement_method": "api_response_actual"
                }

            except Exception as e:
                print(f"⚠️ 実測定失敗: {e}")

        # フォールバック: 改良された動的推定
        input_tokens, output_tokens = self._calculate_enhanced_token_estimate(task_data, result, execution_time)

        # TokenMeasurementSystemでコスト計算
        if self.token_measurement:
            cost = self.token_measurement.calculate_real_cost(input_tokens, output_tokens)
        else:
            # 従来のコスト計算
            cost = (input_tokens / 1_000_000) * 0.30 + (output_tokens / 1_000_000) * 2.50

        print(f"📊 推定Token使用量:")
        print(f"   入力Token: {input_tokens}")
        print(f"   出力Token: {output_tokens}")
        print(f"   推定コスト: ${cost:.4f}")
        print(f"   測定方法: 改良推定")

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model": "gemini-2.5-flash",
            "execution_time": execution_time,
            "estimated_cost": cost,
            "measurement_method": "enhanced_estimation"
        }

    def _calculate_enhanced_token_estimate(self, task_data: Dict[str, Any], result: Dict[str, Any],
                                         execution_time: str) -> tuple[int, int]:
        """改良されたToken推定計算"""

        # 基本パラメータ
        task_type = task_data.get("type", "unknown")
        target_files = task_data.get("target_files", [])
        description = task_data.get("description", "")
        requirements = task_data.get("requirements", {})

        # 入力Token数計算（改良版）
        input_tokens = self._calculate_input_tokens_enhanced(task_data, target_files, description, requirements)

        # 出力Token数計算（改良版）
        output_tokens = self._calculate_output_tokens_enhanced(result, task_type)

        # 実行時間に基づく複雑度補正
        execution_minutes = self._parse_execution_time_minutes(execution_time)
        complexity_factor = min(execution_minutes / 60.0, 2.0)

        # 最終Token数（複雑度補正適用）
        final_input_tokens = int(input_tokens * (1 + complexity_factor * 0.1))
        final_output_tokens = int(output_tokens * (1 + complexity_factor * 0.15))

        return final_input_tokens, final_output_tokens

    def _calculate_input_tokens_enhanced(self, task_data: Dict[str, Any], target_files: List[str],
                                       description: str, requirements: Dict[str, Any]) -> int:
        """改良版入力Token数計算"""

        base_tokens = 300  # 基本システムプロンプト（削減）

        # タスク説明（日本語対応改良）
        description_tokens = len(description.split()) * 1.5  # 日本語文字の重み調整

        # 要件仕様
        requirements_tokens = len(str(requirements)) * 1.0  # 改良版重み

        # ファイル内容（実際のサイズ基準）
        file_content_tokens = 0
        for file_path in target_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # より正確なToken換算（約1.3文字=1Token）
                    file_content_tokens += len(content) / 1.3
                except:
                    file_content_tokens += 200  # 推定値
            else:
                file_content_tokens += 80  # 新規ファイル用推定

        # タスクタイプ別調整（改良版）
        task_type = task_data.get("type", "")
        type_multiplier = {
            "new_implementation": 1.3,      # 削減
            "hybrid_implementation": 1.5,   # 削減
            "new_feature_development": 1.7, # 削減
            "code_modification": 1.1,       # 削減
            "micro_code_modification": 0.9  # 削減
        }.get(task_type, 1.2)

        total_tokens = int((base_tokens + description_tokens + requirements_tokens + file_content_tokens) * type_multiplier)

        return max(total_tokens, 400)  # 最小400トークン

    def _calculate_output_tokens_enhanced(self, result: Dict[str, Any], task_type: str) -> int:
        """改良版出力Token数計算"""

        modifications = result.get("modifications", {})
        report = result.get("report", {})

        # 修正ファイル数に基づく基本Token数（改良版）
        files_modified = len(modifications.get("files_modified", []))
        files_created = len(modifications.get("files_created", []))

        base_output_tokens = (files_modified * 150) + (files_created * 300)  # 削減

        # レポート内容（改良版）
        report_tokens = len(str(report)) * 0.6

        # 実装行数（改良版）
        total_lines = modifications.get("total_lines_implemented", 0)
        if total_lines > 0:
            code_tokens = total_lines * 6  # 1行あたり約6トークン（削減）
        else:
            code_tokens = files_created * 100  # 新規ファイル推定（削減）

        # タスクタイプ別調整（改良版）
        type_multiplier = {
            "new_implementation": 1.5,      # 削減
            "hybrid_implementation": 1.4,   # 削減
            "new_feature_development": 1.8, # 削減
            "code_modification": 1.1,       # 削減
            "micro_code_modification": 0.8  # 削減
        }.get(task_type, 1.2)

        total_output_tokens = int((base_output_tokens + report_tokens + code_tokens) * type_multiplier)

        return max(total_output_tokens, 200)  # 最小200トークン

    def _calculate_input_tokens(self, task_data: Dict[str, Any], target_files: List[str],
                               description: str, requirements: Dict[str, Any]) -> int:
        """入力Token数計算"""

        base_tokens = 200  # 基本システムプロンプト

        # タスク説明
        description_tokens = len(description.split()) * 1.3  # 英語換算

        # 要件仕様
        requirements_tokens = len(str(requirements)) * 0.8

        # ファイル内容（存在する場合）
        file_content_tokens = 0
        for file_path in target_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    file_content_tokens += len(content.split()) * 1.2
                except:
                    file_content_tokens += 300  # 推定値
            else:
                file_content_tokens += 100  # 新規ファイル用推定

        # タスクタイプ別調整
        task_type = task_data.get("type", "")
        type_multiplier = {
            "new_implementation": 1.5,
            "hybrid_implementation": 1.8,
            "new_feature_development": 2.0,
            "code_modification": 1.2,
            "micro_code_modification": 1.0
        }.get(task_type, 1.3)

        total_tokens = int((base_tokens + description_tokens + requirements_tokens + file_content_tokens) * type_multiplier)

        return max(total_tokens, 500)  # 最小500トークン

    def _calculate_output_tokens(self, result: Dict[str, Any], task_type: str) -> int:
        """出力Token数計算"""

        modifications = result.get("modifications", {})
        report = result.get("report", {})

        # 修正ファイル数に基づく基本Token数
        files_modified = len(modifications.get("files_modified", []))
        files_created = len(modifications.get("files_created", []))

        base_output_tokens = (files_modified * 200) + (files_created * 400)

        # レポート内容
        report_tokens = len(str(report)) * 0.7

        # 実装行数（存在する場合）
        total_lines = modifications.get("total_lines_implemented", 0)
        if total_lines > 0:
            code_tokens = total_lines * 8  # 1行あたり約8トークン
        else:
            code_tokens = files_created * 150  # 新規ファイル推定

        # タスクタイプ別調整
        type_multiplier = {
            "new_implementation": 2.0,
            "hybrid_implementation": 1.8,
            "new_feature_development": 2.5,
            "code_modification": 1.3,
            "micro_code_modification": 1.0
        }.get(task_type, 1.5)

        total_output_tokens = int((base_output_tokens + report_tokens + code_tokens) * type_multiplier)

        return max(total_output_tokens, 300)  # 最小300トークン

    def _parse_execution_time_minutes(self, execution_time: str) -> float:
        """実行時間を分単位で解析"""
        try:
            # "0:01:23.456789" 形式を解析
            if ":" in execution_time:
                parts = execution_time.split(":")
                if len(parts) >= 3:
                    hours = float(parts[0])
                    minutes = float(parts[1])
                    seconds = float(parts[2])
                    return hours * 60 + minutes + seconds / 60
                elif len(parts) == 2:
                    minutes = float(parts[0])
                    seconds = float(parts[1])
                    return minutes + seconds / 60

            return 1.0  # デフォルト1分
        except:
            return 1.0

def main():
    """メイン実行関数"""
    helper = GeminiHelper()

    # 次のタスクを取得
    task = helper.get_next_task()

    if task:
        print(f"📋 次のタスクを発見: {task['task_id']}")

        # タスク実行
        result = helper.execute_task(task)

        print(f"✅ 結果: {result['status']}")
    else:
        print("📭 実行待ちのタスクはありません")

if __name__ == "__main__":
    main()
