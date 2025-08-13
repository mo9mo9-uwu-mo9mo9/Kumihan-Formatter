#!/usr/bin/env python3
"""
Task Pre-Validation System
タスク事前検証システム - 不要タスクの事前排除による効率化
"""

import os
import json
import subprocess
import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class ValidationResult(Enum):
    """検証結果"""
    VALID = "valid"                 # 実行すべき
    SKIP_NOT_NEEDED = "skip_not_needed"     # 修正不要によりスキップ
    SKIP_FILE_MISSING = "skip_file_missing" # ファイル不存在によりスキップ
    SKIP_ALREADY_FIXED = "skip_already_fixed"   # 既に修正済み
    SKIP_INVALID_TARGET = "skip_invalid_target" # 無効なターゲット
    DEFER_HIGH_RISK = "defer_high_risk"     # 高リスクにより延期


@dataclass
class PreValidationReport:
    """事前検証レポート"""
    task_id: str
    original_task: Dict[str, Any]
    validation_result: ValidationResult
    reason: str
    estimated_fix_count: int
    current_error_count: int
    file_states: Dict[str, str]
    risk_assessment: str
    recommendations: List[str]
    skip_reason_details: Optional[Dict[str, Any]] = None


class TaskPreValidator:
    """タスク事前検証システム"""

    def __init__(self) -> None:
        self.validation_cache: Dict[str, Any] = {}
        self.mypy_cache: Dict[str, Dict[str, int]] = {}
        self.file_state_cache: Dict[str, str] = {}

        # 検証基準設定
        self.validation_criteria: Dict[str, Any] = {
            "min_error_count_threshold": 1,  # 最小エラー数閾値
            "max_file_size_mb": 10,         # 最大ファイルサイズ
            "supported_extensions": [".py"], # 対応拡張子
            "skip_test_files": True,        # テストファイルをスキップ
            "max_file_count_per_task": 20   # タスクあたり最大ファイル数
        }

        print("🔍 TaskPreValidator 初期化完了")

    def validate_task(self, task_data: Dict[str, Any]) -> PreValidationReport:
        """
        タスクの事前検証実行

        Args:
            task_data: 検証対象タスクデータ

        Returns:
            PreValidationReport: 検証結果レポート
        """

        task_id = task_data.get("task_id", "unknown")
        task_type = task_data.get("type", "unknown")
        target_files = task_data.get("target_files", [])

        print(f"🔍 タスク事前検証開始: {task_id} ({task_type})")

        # Step 1: 基本的な妥当性チェック
        basic_validation = self._validate_basic_requirements(task_data)
        if basic_validation.validation_result != ValidationResult.VALID:
            return basic_validation

        # Step 2: ファイル存在・状態チェック
        file_validation = self._validate_file_states(task_data)
        if file_validation.validation_result != ValidationResult.VALID:
            return file_validation

        # Step 3: エラー現況チェック（mypy/flake8）
        error_validation = self._validate_current_errors(task_data)
        if error_validation.validation_result != ValidationResult.VALID:
            return error_validation

        # Step 4: 修正可能性評価
        fixability_validation = self._validate_fixability(task_data)
        if fixability_validation.validation_result != ValidationResult.VALID:
            return fixability_validation

        # Step 5: リスク評価
        risk_assessment = self._assess_task_risk(task_data)

        # 最終検証レポート生成
        return PreValidationReport(
            task_id=task_id,
            original_task=task_data,
            validation_result=ValidationResult.VALID,
            reason="すべての検証をクリア - 実行推奨",
            estimated_fix_count=self._estimate_fix_count(task_data),
            current_error_count=self._count_current_errors(target_files, task_data.get("requirements", {}).get("error_type", "")),
            file_states=self._get_file_states(target_files),
            risk_assessment=risk_assessment,
            recommendations=self._generate_execution_recommendations(task_data)
        )

    def _validate_basic_requirements(self, task_data: Dict[str, Any]) -> PreValidationReport:
        """基本要件検証"""

        task_id = task_data.get("task_id", "unknown")
        task_type = task_data.get("type", "")
        target_files = task_data.get("target_files", [])

        # ファイル数チェック
        if len(target_files) > self.validation_criteria["max_file_count_per_task"]:
            return PreValidationReport(
                task_id=task_id,
                original_task=task_data,
                validation_result=ValidationResult.SKIP_INVALID_TARGET,
                reason=f"ファイル数過多: {len(target_files)}件 > {self.validation_criteria['max_file_count_per_task']}件",
                estimated_fix_count=0,
                current_error_count=0,
                file_states={},
                risk_assessment="high",
                recommendations=["タスクを複数に分割してください"]
            )

        # ターゲットファイルが空
        if not target_files:
            return PreValidationReport(
                task_id=task_id,
                original_task=task_data,
                validation_result=ValidationResult.SKIP_INVALID_TARGET,
                reason="対象ファイルが指定されていません",
                estimated_fix_count=0,
                current_error_count=0,
                file_states={},
                risk_assessment="high",
                recommendations=["target_filesを指定してください"]
            )

        # 拡張子チェック
        invalid_files = []
        for file_path in target_files:
            if not any(file_path.endswith(ext) for ext in self.validation_criteria["supported_extensions"]):
                invalid_files.append(file_path)

        if invalid_files:
            return PreValidationReport(
                task_id=task_id,
                original_task=task_data,
                validation_result=ValidationResult.SKIP_INVALID_TARGET,
                reason=f"サポートされていない拡張子のファイル: {invalid_files}",
                estimated_fix_count=0,
                current_error_count=0,
                file_states={},
                risk_assessment="medium",
                recommendations=["Pythonファイル（.py）のみを指定してください"]
            )

        # テストファイルスキップ
        if self.validation_criteria["skip_test_files"]:
            test_files = [f for f in target_files if "test" in f.lower() or f.endswith("_test.py")]
            if test_files:
                return PreValidationReport(
                    task_id=task_id,
                    original_task=task_data,
                    validation_result=ValidationResult.SKIP_NOT_NEEDED,
                    reason=f"テストファイルのため自動スキップ: {test_files}",
                    estimated_fix_count=0,
                    current_error_count=0,
                    file_states={f: "test_file" for f in test_files},
                    risk_assessment="low",
                    recommendations=["テストファイルの修正は手動で行ってください"]
                )

        # 基本要件クリア
        return PreValidationReport(
            task_id=task_id,
            original_task=task_data,
            validation_result=ValidationResult.VALID,
            reason="基本要件チェック通過",
            estimated_fix_count=0,
            current_error_count=0,
            file_states={},
            risk_assessment="low",
            recommendations=[]
        )

    def _validate_file_states(self, task_data: Dict[str, Any]) -> PreValidationReport:
        """ファイル状態検証"""

        task_id = task_data.get("task_id", "unknown")
        target_files = task_data.get("target_files", [])

        file_states = {}
        missing_files = []
        oversized_files = []

        for file_path in target_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
                file_states[file_path] = "missing"
                continue

            # ファイルサイズチェック
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self.validation_criteria["max_file_size_mb"]:
                oversized_files.append(file_path)
                file_states[file_path] = f"oversized_{file_size_mb:.1f}MB"
                continue

            # 読み込み可能性チェック
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if not content.strip():
                    file_states[file_path] = "empty"
                else:
                    file_states[file_path] = "valid"
            except UnicodeDecodeError:
                file_states[file_path] = "encoding_error"
            except PermissionError:
                file_states[file_path] = "permission_denied"
            except Exception as e:
                file_states[file_path] = f"read_error_{str(e)[:20]}"

        # 不存在ファイルがある場合
        if missing_files:
            return PreValidationReport(
                task_id=task_id,
                original_task=task_data,
                validation_result=ValidationResult.SKIP_FILE_MISSING,
                reason=f"対象ファイルが存在しません: {missing_files}",
                estimated_fix_count=0,
                current_error_count=0,
                file_states=file_states,
                risk_assessment="medium",
                recommendations=["ファイルパスを確認してください", "新規実装タスクに変更を検討"]
            )

        # サイズ過大ファイルがある場合
        if oversized_files:
            return PreValidationReport(
                task_id=task_id,
                original_task=task_data,
                validation_result=ValidationResult.DEFER_HIGH_RISK,
                reason=f"ファイルサイズ過大: {oversized_files}",
                estimated_fix_count=0,
                current_error_count=0,
                file_states=file_states,
                risk_assessment="high",
                recommendations=["大きなファイルは手動修正を推奨", "部分的な修正タスクに分割"]
            )

        # ファイル状態チェック通過
        return PreValidationReport(
            task_id=task_id,
            original_task=task_data,
            validation_result=ValidationResult.VALID,
            reason="ファイル状態チェック通過",
            estimated_fix_count=0,
            current_error_count=0,
            file_states=file_states,
            risk_assessment="low",
            recommendations=[]
        )

    def _validate_current_errors(self, task_data: Dict[str, Any]) -> PreValidationReport:
        """現在のエラー状況検証"""

        task_id = task_data.get("task_id", "unknown")
        target_files = task_data.get("target_files", [])
        error_type = task_data.get("requirements", {}).get("error_type", "")

        current_error_count = 0
        file_error_details = {}

        for file_path in target_files:
            if not os.path.exists(file_path):
                continue

            # mypyエラーカウント
            file_errors = self._count_file_errors(file_path, error_type)
            current_error_count += file_errors
            file_error_details[file_path] = file_errors

        # エラーが存在しない場合
        if current_error_count == 0:
            return PreValidationReport(
                task_id=task_id,
                original_task=task_data,
                validation_result=ValidationResult.SKIP_ALREADY_FIXED,
                reason=f"対象エラー（{error_type}）が存在しません",
                estimated_fix_count=0,
                current_error_count=0,
                file_states={f: f"no_errors" for f in target_files},
                risk_assessment="low",
                recommendations=["このタスクは不要です"],
                skip_reason_details={"file_error_details": file_error_details}
            )

        # 最小閾値未満の場合
        if current_error_count < self.validation_criteria["min_error_count_threshold"]:
            return PreValidationReport(
                task_id=task_id,
                original_task=task_data,
                validation_result=ValidationResult.SKIP_NOT_NEEDED,
                reason=f"エラー数が最小閾値未満: {current_error_count}件",
                estimated_fix_count=current_error_count,
                current_error_count=current_error_count,
                file_states={f: f"{file_error_details[f]}_errors" for f in target_files if f in file_error_details},
                risk_assessment="low",
                recommendations=["手動修正で十分です"]
            )

        # エラー検証通過
        return PreValidationReport(
            task_id=task_id,
            original_task=task_data,
            validation_result=ValidationResult.VALID,
            reason=f"修正対象エラー {current_error_count}件を確認",
            estimated_fix_count=current_error_count,
            current_error_count=current_error_count,
            file_states={f: f"{file_error_details[f]}_errors" for f in target_files if f in file_error_details},
            risk_assessment="low",
            recommendations=[]
        )

    def _validate_fixability(self, task_data: Dict[str, Any]) -> PreValidationReport:
        """修正可能性評価"""

        task_id = task_data.get("task_id", "unknown")
        target_files = task_data.get("target_files", [])
        error_type = task_data.get("requirements", {}).get("error_type", "")

        fixability_score = 0.0
        fixable_files = []
        unfixable_files = []

        for file_path in target_files:
            if not os.path.exists(file_path):
                continue

            # ファイル固有の修正可能性評価
            file_fixability = self._assess_file_fixability(file_path, error_type)

            if file_fixability >= 0.6:
                fixable_files.append((file_path, file_fixability))
                fixability_score += file_fixability
            else:
                unfixable_files.append((file_path, file_fixability))

        average_fixability = fixability_score / len(fixable_files) if fixable_files else 0.0

        # 修正可能ファイルが少ない場合
        if len(fixable_files) == 0:
            return PreValidationReport(
                task_id=task_id,
                original_task=task_data,
                validation_result=ValidationResult.DEFER_HIGH_RISK,
                reason="修正可能なファイルがありません",
                estimated_fix_count=0,
                current_error_count=self._count_current_errors(target_files, error_type),
                file_states={f: f"unfixable_{score:.2f}" for f, score in unfixable_files},
                risk_assessment="high",
                recommendations=["手動修正を推奨", "タスクを再設計"]
            )

        # 修正可能性が低い場合
        if average_fixability < 0.4:
            return PreValidationReport(
                task_id=task_id,
                original_task=task_data,
                validation_result=ValidationResult.DEFER_HIGH_RISK,
                reason=f"修正可能性が低い: {average_fixability:.2f}",
                estimated_fix_count=len(fixable_files),
                current_error_count=self._count_current_errors(target_files, error_type),
                file_states={f: f"low_fixability_{score:.2f}" for f, score in fixable_files},
                risk_assessment="high",
                recommendations=["部分的な手動修正を検討", "複雑度を下げるためのリファクタリング"]
            )

        # 修正可能性評価通過
        return PreValidationReport(
            task_id=task_id,
            original_task=task_data,
            validation_result=ValidationResult.VALID,
            reason=f"修正可能性良好: {average_fixability:.2f} ({len(fixable_files)}件)",
            estimated_fix_count=len(fixable_files),
            current_error_count=self._count_current_errors(target_files, error_type),
            file_states={f: f"fixable_{score:.2f}" for f, score in fixable_files},
            risk_assessment="low" if average_fixability > 0.7 else "medium",
            recommendations=[]
        )

    def _count_file_errors(self, file_path: str, error_type: str) -> int:
        """ファイル内の特定エラーをカウント"""

        if file_path in self.mypy_cache:
            return self.mypy_cache[file_path].get(error_type, 0)

        try:
            # mypy実行
            result = subprocess.run(
                ["python3", "-m", "mypy", "--strict", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            # エラー数カウント
            error_count = 0
            if error_type:
                error_count = result.stdout.count(f"[{error_type}]")
            else:
                error_count = result.stdout.count("error:")

            # キャッシュ更新
            if file_path not in self.mypy_cache:
                self.mypy_cache[file_path] = {}
            self.mypy_cache[file_path][error_type] = error_count

            return error_count

        except subprocess.TimeoutExpired:
            print(f"⚠️ mypy timeout for {file_path}")
            return 0
        except FileNotFoundError:
            print(f"⚠️ mypy not found")
            return 0
        except Exception as e:
            print(f"⚠️ mypy error for {file_path}: {e}")
            return 0

    def _count_current_errors(self, target_files: List[str], error_type: str) -> int:
        """現在の全エラー数をカウント"""

        total_errors = 0
        for file_path in target_files:
            if os.path.exists(file_path):
                total_errors += self._count_file_errors(file_path, error_type)
        return total_errors

    def _assess_file_fixability(self, file_path: str, error_type: str) -> float:
        """ファイルの修正可能性を評価（0.0-1.0）"""

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            line_count = len(lines)

            fixability_factors = {
                # ポジティブ要因
                "simple_function_defs": content.count('def ') * 0.1,
                "basic_imports": len([l for l in lines if l.strip().startswith('import ')]) * 0.05,
                "type_hints_present": content.count(':') * 0.02,

                # ネガティブ要因
                "complex_decorators": content.count('@') * -0.05,
                "lambda_expressions": content.count('lambda') * -0.08,
                "eval_statements": content.count('eval(') * -0.2,
                "dynamic_imports": content.count('__import__') * -0.15,
                "excessive_length": max(0, (line_count - 200) / 100) * -0.1,
            }

            base_fixability = 0.7  # 基本修正可能性

            # 要因による調整
            for factor, impact in fixability_factors.items():
                base_fixability += impact

            # エラータイプ固有の調整
            error_type_adjustments = {
                "no-untyped-def": 0.15,      # 比較的修正しやすい
                "no-untyped-call": -0.1,     # やや困難
                "type-arg": 0.05,            # 中程度
                "call-arg": -0.15,           # 困難
                "attr-defined": -0.2,        # 最も困難
            }

            base_fixability += error_type_adjustments.get(error_type, 0.0)

            return max(0.0, min(1.0, base_fixability))

        except Exception:
            return 0.3  # エラーの場合は低い修正可能性

    def _assess_task_risk(self, task_data: Dict[str, Any]) -> str:
        """タスクリスク評価"""

        target_files = task_data.get("target_files", [])
        task_type = task_data.get("type", "")

        risk_score = 0

        # ファイル数によるリスク
        risk_score += min(len(target_files) * 0.5, 3)

        # タスクタイプによるリスク
        type_risks = {
            "new_implementation": 3,
            "hybrid_implementation": 4,
            "new_feature_development": 5,
            "code_modification": 1,
            "file_code_modification": 1,
            "micro_code_modification": 0.5
        }
        risk_score += type_risks.get(task_type, 2)

        # 重要ファイルの修正
        critical_paths = ["main", "core", "__init__", "config"]
        if any(critical in file_path.lower() for file_path in target_files for critical in critical_paths):
            risk_score += 2

        # リスクレベル決定
        if risk_score <= 2:
            return "low"
        elif risk_score <= 5:
            return "medium"
        else:
            return "high"

    def _estimate_fix_count(self, task_data: Dict[str, Any]) -> int:
        """修正予想件数を推定"""

        target_files = task_data.get("target_files", [])
        error_type = task_data.get("requirements", {}).get("error_type", "")

        return self._count_current_errors(target_files, error_type)

    def _get_file_states(self, target_files: List[str]) -> Dict[str, str]:
        """ファイル状態取得"""

        states = {}
        for file_path in target_files:
            if file_path in self.file_state_cache:
                states[file_path] = self.file_state_cache[file_path]
            elif os.path.exists(file_path):
                states[file_path] = "exists"
                self.file_state_cache[file_path] = "exists"
            else:
                states[file_path] = "missing"
                self.file_state_cache[file_path] = "missing"

        return states

    def _generate_execution_recommendations(self, task_data: Dict[str, Any]) -> List[str]:
        """実行推奨事項生成"""

        task_type = task_data.get("type", "")
        target_files = task_data.get("target_files", [])
        error_type = task_data.get("requirements", {}).get("error_type", "")

        recommendations = []

        # 基本推奨事項
        recommendations.append("実行前にファイルのバックアップを作成")
        recommendations.append("段階的修正と各段階での品質チェック実行")

        # エラータイプ固有の推奨事項
        if error_type == "no-untyped-def":
            recommendations.append("戻り値型注釈の推論を慎重に実施")
            recommendations.append("既存の型注釈との整合性確認")
        elif error_type == "call-arg":
            recommendations.append("引数型変換の安全性確認")
            recommendations.append("実行時エラーの可能性を考慮")

        # ファイル数に応じた推奨事項
        if len(target_files) > 5:
            recommendations.append("ファイル単位での順次実行を推奨")
            recommendations.append("各ファイル修正後にテスト実行")

        return recommendations

    def batch_validate_tasks(self, task_list: List[Dict[str, Any]]) -> Dict[str, PreValidationReport]:
        """タスクのバッチ検証"""

        print(f"📋 バッチ検証開始: {len(task_list)}タスク")

        validation_results = {}

        for task_data in task_list:
            task_id = task_data.get("task_id", "unknown")
            try:
                validation_result = self.validate_task(task_data)
                validation_results[task_id] = validation_result

                print(f"  ✅ {task_id}: {validation_result.validation_result.value}")

            except Exception as e:
                # エラー時のフォールバック
                error_report = PreValidationReport(
                    task_id=task_id,
                    original_task=task_data,
                    validation_result=ValidationResult.DEFER_HIGH_RISK,
                    reason=f"検証エラー: {str(e)}",
                    estimated_fix_count=0,
                    current_error_count=0,
                    file_states={},
                    risk_assessment="high",
                    recommendations=["手動で検証してください"]
                )
                validation_results[task_id] = error_report
                print(f"  ❌ {task_id}: 検証エラー")

        print(f"📊 バッチ検証完了: {len(validation_results)}件")
        return validation_results

    def generate_validation_summary(self, validation_results: Dict[str, PreValidationReport]) -> Dict[str, Any]:
        """検証サマリー生成"""

        summary = {
            "total_tasks": len(validation_results),
            "validation_counts": {},
            "estimated_workload": {
                "valid_tasks": 0,
                "total_estimated_fixes": 0,
                "total_current_errors": 0
            },
            "risk_distribution": {"low": 0, "medium": 0, "high": 0},
            "skip_reasons": {},
            "recommendations": {
                "immediate_execution": [],
                "defer_execution": [],
                "skip_permanently": []
            }
        }

        for task_id, report in validation_results.items():
            # 検証結果の集計
            result_type = report.validation_result.value
            summary["validation_counts"][result_type] = summary["validation_counts"].get(result_type, 0) + 1

            # ワークロード集計
            if report.validation_result == ValidationResult.VALID:
                summary["estimated_workload"]["valid_tasks"] += 1
                summary["estimated_workload"]["total_estimated_fixes"] += report.estimated_fix_count
                summary["estimated_workload"]["total_current_errors"] += report.current_error_count
                summary["recommendations"]["immediate_execution"].append(task_id)
            elif report.validation_result == ValidationResult.DEFER_HIGH_RISK:
                summary["recommendations"]["defer_execution"].append(task_id)
            else:
                summary["recommendations"]["skip_permanently"].append(task_id)

            # リスク分散
            summary["risk_distribution"][report.risk_assessment] += 1

            # スキップ理由集計
            if report.validation_result != ValidationResult.VALID:
                skip_category = report.validation_result.value
                if skip_category not in summary["skip_reasons"]:
                    summary["skip_reasons"][skip_category] = []
                summary["skip_reasons"][skip_category].append(task_id)

        return summary

    def save_validation_report(self, validation_results: Dict[str, PreValidationReport],
                             output_path: str = "tmp/task_validation_report.json") -> str:
        """検証レポート保存"""

        # 出力ディレクトリ作成
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # サマリー生成
        summary = self.generate_validation_summary(validation_results)

        # レポートデータ構築
        report_data = {
            "validation_timestamp": datetime.datetime.now().isoformat(),
            "validation_summary": summary,
            "detailed_results": {}
        }

        # 詳細結果を辞書形式に変換
        for task_id, report in validation_results.items():
            report_data["detailed_results"][task_id] = {
                "task_id": report.task_id,
                "validation_result": report.validation_result.value,
                "reason": report.reason,
                "estimated_fix_count": report.estimated_fix_count,
                "current_error_count": report.current_error_count,
                "file_states": report.file_states,
                "risk_assessment": report.risk_assessment,
                "recommendations": report.recommendations,
                "skip_reason_details": report.skip_reason_details
            }

        # JSON保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"📊 検証レポート保存完了: {output_path}")
        return output_path


def main():
    """テスト実行"""

    print("🧪 TaskPreValidator テスト実行")

    validator = TaskPreValidator()

    # テストタスクデータ
    test_tasks = [
        {
            "task_id": "test_task_001",
            "type": "file_code_modification",
            "target_files": ["postbox/utils/task_manager.py"],
            "requirements": {
                "error_type": "no-untyped-def",
                "fix_pattern": "add_return_type_annotations"
            }
        },
        {
            "task_id": "test_task_002",
            "type": "file_code_modification",
            "target_files": ["nonexistent_file.py"],
            "requirements": {
                "error_type": "no-untyped-def"
            }
        },
        {
            "task_id": "test_task_003",
            "type": "file_code_modification",
            "target_files": ["test_example.py"],
            "requirements": {
                "error_type": "no-untyped-def"
            }
        }
    ]

    # バッチ検証実行
    results = validator.batch_validate_tasks(test_tasks)

    # サマリー表示
    summary = validator.generate_validation_summary(results)
    print(f"\n📊 検証サマリー:")
    print(f"総タスク数: {summary['total_tasks']}")
    print(f"有効タスク数: {summary['estimated_workload']['valid_tasks']}")
    print(f"推定修正件数: {summary['estimated_workload']['total_estimated_fixes']}")

    # レポート保存
    validator.save_validation_report(results)

    print("\n✅ TaskPreValidator テスト完了")


if __name__ == "__main__":
    main()
