#!/usr/bin/env python3
"""
Task Deduplication System
タスク重複排除システム - 重複・類似タスクの統合による効率化
"""

import json
import hashlib
import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class DuplicationLevel(Enum):
    """重複レベル"""
    IDENTICAL = "identical"         # 完全一致
    HIGHLY_SIMILAR = "highly_similar"   # 高度類似（90%以上）
    SIMILAR = "similar"            # 類似（70-89%）
    RELATED = "related"           # 関連（50-69%）
    DIFFERENT = "different"        # 異なる（50%未満）


class MergeStrategy(Enum):
    """マージ戦略"""
    KEEP_NEWEST = "keep_newest"     # 最新を保持
    KEEP_HIGHEST_PRIORITY = "keep_highest_priority"  # 高優先度を保持
    MERGE_TARGETS = "merge_targets" # ターゲットファイルを統合
    MERGE_REQUIREMENTS = "merge_requirements"  # 要件を統合
    MANUAL_REVIEW = "manual_review" # 手動確認が必要


@dataclass
class TaskHash:
    """タスクハッシュ情報"""
    task_id: str
    content_hash: str
    targets_hash: str
    requirements_hash: str
    combined_hash: str
    hash_components: Dict[str, str]


@dataclass
class DuplicationGroup:
    """重複グループ"""
    group_id: str
    duplication_level: DuplicationLevel
    similarity_score: float
    tasks: List[Dict[str, Any]]
    merge_strategy: MergeStrategy
    recommended_action: str
    merged_task: Optional[Dict[str, Any]]
    savings_estimate: Dict[str, Any]


@dataclass
class DeduplicationReport:
    """重複排除レポート"""
    original_task_count: int
    duplicate_groups_found: int
    tasks_removed: int
    tasks_merged: int
    estimated_time_saved: float
    estimated_token_saved: int
    duplication_groups: List[DuplicationGroup]
    action_summary: Dict[str, int]


class TaskDeduplicator:
    """タスク重複排除システム"""

    def __init__(self) -> None:
        self.task_hashes = {}
        self.similarity_cache = {}

        # 重複判定設定
        self.duplication_thresholds = {
            "identical": 1.0,
            "highly_similar": 0.90,
            "similar": 0.70,
            "related": 0.50
        }

        # マージルール設定
        self.merge_rules = {
            "identical": MergeStrategy.KEEP_NEWEST,
            "highly_similar": MergeStrategy.MERGE_TARGETS,
            "similar": MergeStrategy.MERGE_REQUIREMENTS,
            "related": MergeStrategy.MANUAL_REVIEW
        }

        print("🔄 TaskDeduplicator 初期化完了")

    def deduplicate_tasks(self, task_list: List[Dict[str, Any]]) -> DeduplicationReport:
        """
        タスクの重複排除実行

        Args:
            task_list: 対象タスクリスト

        Returns:
            DeduplicationReport: 重複排除レポート
        """

        print(f"🔄 タスク重複排除開始: {len(task_list)}タスク")

        # Step 1: タスクハッシュ生成
        task_hashes = self._generate_task_hashes(task_list)

        # Step 2: 重複グループ検出
        duplicate_groups = self._detect_duplicate_groups(task_list, task_hashes)

        # Step 3: マージ戦略決定
        for group in duplicate_groups:
            self._determine_merge_strategy(group)

        # Step 4: タスク統合実行
        deduplicated_tasks, action_summary = self._execute_deduplication(task_list, duplicate_groups)

        # Step 5: レポート生成
        report = DeduplicationReport(
            original_task_count=len(task_list),
            duplicate_groups_found=len(duplicate_groups),
            tasks_removed=action_summary.get("removed", 0),
            tasks_merged=action_summary.get("merged", 0),
            estimated_time_saved=self._estimate_time_savings(duplicate_groups),
            estimated_token_saved=self._estimate_token_savings(duplicate_groups),
            duplication_groups=duplicate_groups,
            action_summary=action_summary
        )

        print(f"✅ 重複排除完了: {report.tasks_removed}件削除, {report.tasks_merged}件統合")
        return report

    def _generate_task_hashes(self, task_list: List[Dict[str, Any]]) -> Dict[str, TaskHash]:
        """タスクハッシュ生成"""

        task_hashes = {}

        for task_data in task_list:
            task_id = task_data.get("task_id", "unknown")

            # 各要素のハッシュ計算
            content_elements = {
                "type": task_data.get("type", ""),
                "description": task_data.get("description", ""),
                "priority": task_data.get("priority", "")
            }
            content_hash = self._calculate_hash(json.dumps(content_elements, sort_keys=True))

            targets_hash = self._calculate_hash(json.dumps(sorted(task_data.get("target_files", []))))

            requirements = task_data.get("requirements", {})
            requirements_hash = self._calculate_hash(json.dumps(requirements, sort_keys=True))

            # 統合ハッシュ
            combined_data = f"{content_hash}:{targets_hash}:{requirements_hash}"
            combined_hash = self._calculate_hash(combined_data)

            task_hash = TaskHash(
                task_id=task_id,
                content_hash=content_hash,
                targets_hash=targets_hash,
                requirements_hash=requirements_hash,
                combined_hash=combined_hash,
                hash_components={
                    "content": content_hash,
                    "targets": targets_hash,
                    "requirements": requirements_hash
                }
            )

            task_hashes[task_id] = task_hash

        print(f"🔢 タスクハッシュ生成完了: {len(task_hashes)}件")
        return task_hashes

    def _detect_duplicate_groups(self, task_list: List[Dict[str, Any]],
                               task_hashes: Dict[str, TaskHash]) -> List[DuplicationGroup]:
        """重複グループ検出"""

        duplicate_groups = []
        processed_tasks = set()

        for i, task_a in enumerate(task_list):
            task_id_a = task_a.get("task_id", "unknown")

            if task_id_a in processed_tasks:
                continue

            # 類似タスクを検索
            similar_tasks = [task_a]
            hash_a = task_hashes.get(task_id_a)

            for j, task_b in enumerate(task_list[i+1:], i+1):
                task_id_b = task_b.get("task_id", "unknown")

                if task_id_b in processed_tasks:
                    continue

                hash_b = task_hashes.get(task_id_b)
                if not hash_a or not hash_b:
                    continue

                # 類似度計算
                similarity_score = self._calculate_similarity(task_a, task_b, hash_a, hash_b)

                if similarity_score >= self.duplication_thresholds["related"]:
                    similar_tasks.append(task_b)
                    processed_tasks.add(task_id_b)

            # 重複グループが見つかった場合
            if len(similar_tasks) > 1:
                # 類似度レベル決定
                avg_similarity = self._calculate_group_similarity(similar_tasks, task_hashes)
                duplication_level = self._determine_duplication_level(avg_similarity)

                group = DuplicationGroup(
                    group_id=f"dup_group_{len(duplicate_groups):03d}",
                    duplication_level=duplication_level,
                    similarity_score=avg_similarity,
                    tasks=similar_tasks,
                    merge_strategy=self.merge_rules.get(duplication_level.value, MergeStrategy.MANUAL_REVIEW),
                    recommended_action="",
                    merged_task=None,
                    savings_estimate={}
                )

                duplicate_groups.append(group)
                processed_tasks.add(task_id_a)

        print(f"🔍 重複グループ検出: {len(duplicate_groups)}グループ")
        return duplicate_groups

    def _calculate_similarity(self, task_a: Dict[str, Any], task_b: Dict[str, Any],
                            hash_a: TaskHash, hash_b: TaskHash) -> float:
        """タスク類似度計算"""

        # キャッシュチェック
        cache_key = f"{hash_a.task_id}:{hash_b.task_id}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]

        # 各要素の類似度を重み付き計算
        similarities = {
            "content": 0.4,     # タイプ・説明・優先度
            "targets": 0.4,     # 対象ファイル
            "requirements": 0.2  # 要件
        }

        total_similarity = 0.0

        for component, weight in similarities.items():
            component_similarity = self._calculate_component_similarity(
                task_a, task_b, component
            )
            total_similarity += component_similarity * weight

        # キャッシュ保存
        self.similarity_cache[cache_key] = total_similarity
        self.similarity_cache[f"{hash_b.task_id}:{hash_a.task_id}"] = total_similarity

        return total_similarity

    def _calculate_component_similarity(self, task_a: Dict[str, Any],
                                     task_b: Dict[str, Any], component: str) -> float:
        """コンポーネント類似度計算"""

        if component == "content":
            # タスクタイプ
            type_match = 1.0 if task_a.get("type") == task_b.get("type") else 0.0

            # 説明文の類似度（簡易版）
            desc_a = task_a.get("description", "").lower()
            desc_b = task_b.get("description", "").lower()
            desc_similarity = self._text_similarity(desc_a, desc_b)

            # 優先度
            priority_match = 1.0 if task_a.get("priority") == task_b.get("priority") else 0.5

            return (type_match * 0.5 + desc_similarity * 0.3 + priority_match * 0.2)

        elif component == "targets":
            targets_a = set(task_a.get("target_files", []))
            targets_b = set(task_b.get("target_files", []))

            if not targets_a and not targets_b:
                return 1.0

            intersection = targets_a & targets_b
            union = targets_a | targets_b

            return len(intersection) / len(union) if union else 0.0

        elif component == "requirements":
            req_a = task_a.get("requirements", {})
            req_b = task_b.get("requirements", {})

            if not req_a and not req_b:
                return 1.0

            # エラータイプの比較
            error_type_match = 1.0 if req_a.get("error_type") == req_b.get("error_type") else 0.0

            # 修正パターンの比較
            fix_pattern_match = 1.0 if req_a.get("fix_pattern") == req_b.get("fix_pattern") else 0.0

            return (error_type_match * 0.7 + fix_pattern_match * 0.3)

        return 0.0

    def _text_similarity(self, text_a: str, text_b: str) -> float:
        """テキスト類似度計算（簡易版）"""

        if not text_a and not text_b:
            return 1.0

        if not text_a or not text_b:
            return 0.0

        # 単語ベースの類似度
        words_a = set(text_a.split())
        words_b = set(text_b.split())

        intersection = words_a & words_b
        union = words_a | words_b

        return len(intersection) / len(union) if union else 0.0

    def _calculate_group_similarity(self, tasks: List[Dict[str, Any]],
                                  task_hashes: Dict[str, TaskHash]) -> float:
        """グループ内平均類似度計算"""

        if len(tasks) < 2:
            return 1.0

        total_similarity = 0.0
        comparison_count = 0

        for i in range(len(tasks)):
            for j in range(i+1, len(tasks)):
                task_id_a = tasks[i].get("task_id", "unknown")
                task_id_b = tasks[j].get("task_id", "unknown")

                hash_a = task_hashes.get(task_id_a)
                hash_b = task_hashes.get(task_id_b)

                if hash_a and hash_b:
                    similarity = self._calculate_similarity(tasks[i], tasks[j], hash_a, hash_b)
                    total_similarity += similarity
                    comparison_count += 1

        return total_similarity / comparison_count if comparison_count > 0 else 0.0

    def _determine_duplication_level(self, similarity_score: float) -> DuplicationLevel:
        """重複レベル決定"""

        if similarity_score >= self.duplication_thresholds["identical"]:
            return DuplicationLevel.IDENTICAL
        elif similarity_score >= self.duplication_thresholds["highly_similar"]:
            return DuplicationLevel.HIGHLY_SIMILAR
        elif similarity_score >= self.duplication_thresholds["similar"]:
            return DuplicationLevel.SIMILAR
        elif similarity_score >= self.duplication_thresholds["related"]:
            return DuplicationLevel.RELATED
        else:
            return DuplicationLevel.DIFFERENT

    def _determine_merge_strategy(self, group: DuplicationGroup) -> None:
        """マージ戦略決定"""

        # 基本戦略
        base_strategy = self.merge_rules.get(
            group.duplication_level.value,
            MergeStrategy.MANUAL_REVIEW
        )

        # タスク特性による調整
        task_types = set(task.get("type", "") for task in group.tasks)
        priorities = set(task.get("priority", "") for task in group.tasks)

        # 全て同じタイプの場合は積極的にマージ
        if len(task_types) == 1 and group.similarity_score > 0.85:
            if base_strategy == MergeStrategy.MANUAL_REVIEW:
                base_strategy = MergeStrategy.MERGE_TARGETS

        # 優先度が混在している場合は高優先度保持
        if len(priorities) > 1:
            base_strategy = MergeStrategy.KEEP_HIGHEST_PRIORITY

        group.merge_strategy = base_strategy

        # 推奨アクション設定
        action_descriptions = {
            MergeStrategy.KEEP_NEWEST: "最新のタスクを保持し、古いタスクを削除",
            MergeStrategy.KEEP_HIGHEST_PRIORITY: "最高優先度のタスクを保持",
            MergeStrategy.MERGE_TARGETS: "対象ファイルを統合した新しいタスクを作成",
            MergeStrategy.MERGE_REQUIREMENTS: "要件を統合した新しいタスクを作成",
            MergeStrategy.MANUAL_REVIEW: "手動確認が必要"
        }

        group.recommended_action = action_descriptions.get(
            base_strategy,
            "手動確認が必要"
        )

    def _execute_deduplication(self, task_list: List[Dict[str, Any]],
                             duplicate_groups: List[DuplicationGroup]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """重複排除実行"""

        action_summary = {
            "removed": 0,
            "merged": 0,
            "kept": 0,
            "manual_review": 0
        }

        # 処理対象タスクIDの収集
        processed_task_ids = set()
        for group in duplicate_groups:
            for task in group.tasks:
                processed_task_ids.add(task.get("task_id", "unknown"))

        # 重複排除されたタスクリスト
        deduplicated_tasks = []

        # 重複していないタスクはそのまま保持
        for task in task_list:
            if task.get("task_id") not in processed_task_ids:
                deduplicated_tasks.append(task)
                action_summary["kept"] += 1

        # 各重複グループの処理
        for group in duplicate_groups:
            if group.merge_strategy == MergeStrategy.KEEP_NEWEST:
                # 最新タスクを保持
                newest_task = max(group.tasks, key=lambda t: t.get("timestamp", ""))
                deduplicated_tasks.append(newest_task)
                action_summary["removed"] += len(group.tasks) - 1
                action_summary["kept"] += 1

            elif group.merge_strategy == MergeStrategy.KEEP_HIGHEST_PRIORITY:
                # 最高優先度タスクを保持
                priority_order = {"high": 0, "medium": 1, "low": 2}
                highest_priority_task = min(
                    group.tasks,
                    key=lambda t: priority_order.get(t.get("priority", "medium"), 1)
                )
                deduplicated_tasks.append(highest_priority_task)
                action_summary["removed"] += len(group.tasks) - 1
                action_summary["kept"] += 1

            elif group.merge_strategy == MergeStrategy.MERGE_TARGETS:
                # 対象ファイルをマージした新しいタスクを作成
                merged_task = self._create_merged_task(group, "targets")
                if merged_task:
                    deduplicated_tasks.append(merged_task)
                    group.merged_task = merged_task
                    action_summary["merged"] += 1
                    action_summary["removed"] += len(group.tasks)

            elif group.merge_strategy == MergeStrategy.MERGE_REQUIREMENTS:
                # 要件をマージした新しいタスクを作成
                merged_task = self._create_merged_task(group, "requirements")
                if merged_task:
                    deduplicated_tasks.append(merged_task)
                    group.merged_task = merged_task
                    action_summary["merged"] += 1
                    action_summary["removed"] += len(group.tasks)

            else:
                # 手動確認が必要 - 全て保持
                deduplicated_tasks.extend(group.tasks)
                action_summary["manual_review"] += len(group.tasks)

        return deduplicated_tasks, action_summary

    def _create_merged_task(self, group: DuplicationGroup, merge_type: str) -> Optional[Dict[str, Any]]:
        """統合タスクの作成"""

        base_task = group.tasks[0].copy()  # 最初のタスクをベースにする

        # 新しいタスクID生成
        base_task["task_id"] = f"merged_{group.group_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if merge_type == "targets":
            # 対象ファイルの統合
            all_targets = set()
            for task in group.tasks:
                all_targets.update(task.get("target_files", []))

            base_task["target_files"] = sorted(list(all_targets))
            base_task["description"] = f"統合タスク: {len(all_targets)}ファイルの一括処理"

        elif merge_type == "requirements":
            # 要件の統合（簡易版）
            all_requirements = {}
            for task in group.tasks:
                task_req = task.get("requirements", {})
                for key, value in task_req.items():
                    if key not in all_requirements:
                        all_requirements[key] = value
                    elif isinstance(value, list) and isinstance(all_requirements[key], list):
                        all_requirements[key].extend(value)

            base_task["requirements"] = all_requirements
            base_task["description"] = f"統合タスク: 複数要件の一括処理"

        # メタデータ更新
        base_task["merged_from"] = [task.get("task_id") for task in group.tasks]
        base_task["merge_timestamp"] = datetime.datetime.now().isoformat()
        base_task["created_by"] = "task_deduplicator"

        return base_task

    def _estimate_time_savings(self, duplicate_groups: List[DuplicationGroup]) -> float:
        """時間節約量推定（分）"""

        total_savings = 0.0

        for group in duplicate_groups:
            if group.merge_strategy in [MergeStrategy.KEEP_NEWEST, MergeStrategy.KEEP_HIGHEST_PRIORITY]:
                # 重複タスクの実行時間を節約
                duplicate_count = len(group.tasks) - 1
                estimated_time_per_task = 5.0  # 5分と仮定
                total_savings += duplicate_count * estimated_time_per_task

            elif group.merge_strategy in [MergeStrategy.MERGE_TARGETS, MergeStrategy.MERGE_REQUIREMENTS]:
                # マージによる効率化
                original_time = len(group.tasks) * 5.0
                merged_time = 8.0  # マージタスクは若干時間がかかる
                total_savings += max(0, original_time - merged_time)

        return total_savings

    def _estimate_token_savings(self, duplicate_groups: List[DuplicationGroup]) -> int:
        """トークン節約量推定"""

        total_token_savings = 0

        for group in duplicate_groups:
            if group.merge_strategy in [MergeStrategy.KEEP_NEWEST, MergeStrategy.KEEP_HIGHEST_PRIORITY]:
                # 重複タスクの実行トークンを節約
                duplicate_count = len(group.tasks) - 1
                estimated_tokens_per_task = 1500  # 1500トークンと仮定
                total_token_savings += duplicate_count * estimated_tokens_per_task

            elif group.merge_strategy in [MergeStrategy.MERGE_TARGETS, MergeStrategy.MERGE_REQUIREMENTS]:
                # マージによる効率化（コンテキスト共有）
                original_tokens = len(group.tasks) * 1500
                merged_tokens = 2200  # マージタスクは多少増える
                total_token_savings += max(0, original_tokens - merged_tokens)

        return total_token_savings

    def _calculate_hash(self, data: str) -> str:
        """データハッシュ計算"""
        return hashlib.md5(data.encode('utf-8')).hexdigest()

    def analyze_duplication_patterns(self, task_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """重複パターン分析"""

        analysis = {
            "total_tasks": len(task_list),
            "duplication_patterns": {},
            "common_targets": {},
            "error_type_distribution": {},
            "recommendations": []
        }

        # タスクタイプ別の分析
        type_groups = {}
        for task in task_list:
            task_type = task.get("type", "unknown")
            if task_type not in type_groups:
                type_groups[task_type] = []
            type_groups[task_type].append(task)

        for task_type, tasks in type_groups.items():
            if len(tasks) > 1:
                analysis["duplication_patterns"][task_type] = {
                    "count": len(tasks),
                    "potential_duplicates": self._find_potential_duplicates_in_group(tasks)
                }

        # 共通対象ファイルの分析
        file_frequency = {}
        for task in task_list:
            for file_path in task.get("target_files", []):
                file_frequency[file_path] = file_frequency.get(file_path, 0) + 1

        analysis["common_targets"] = {
            file_path: count for file_path, count in file_frequency.items() if count > 1
        }

        # エラータイプ分布
        error_types = {}
        for task in task_list:
            error_type = task.get("requirements", {}).get("error_type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

        analysis["error_type_distribution"] = error_types

        # 推奨事項
        if analysis["common_targets"]:
            analysis["recommendations"].append("共通ファイルを対象とするタスクの統合を検討")

        if len(analysis["duplication_patterns"]) > 0:
            analysis["recommendations"].append("同一タイプのタスクの重複確認と統合")

        return analysis

    def _find_potential_duplicates_in_group(self, tasks: List[Dict[str, Any]]) -> int:
        """グループ内の潜在的重複数を推定"""

        potential_duplicates = 0

        for i in range(len(tasks)):
            for j in range(i+1, len(tasks)):
                # 簡易的な重複判定
                targets_a = set(tasks[i].get("target_files", []))
                targets_b = set(tasks[j].get("target_files", []))

                overlap = len(targets_a & targets_b)
                if overlap > 0:
                    potential_duplicates += 1

        return potential_duplicates

    def save_deduplication_report(self, report: DeduplicationReport,
                                output_path: str = "tmp/task_deduplication_report.json") -> str:
        """重複排除レポート保存"""

        # 出力ディレクトリ作成
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # レポートデータ構築
        report_data = {
            "deduplication_timestamp": datetime.datetime.now().isoformat(),
            "summary": {
                "original_task_count": report.original_task_count,
                "duplicate_groups_found": report.duplicate_groups_found,
                "tasks_removed": report.tasks_removed,
                "tasks_merged": report.tasks_merged,
                "estimated_time_saved": report.estimated_time_saved,
                "estimated_token_saved": report.estimated_token_saved,
                "action_summary": report.action_summary
            },
            "duplicate_groups": []
        }

        # 重複グループの詳細
        for group in report.duplication_groups:
            group_data = {
                "group_id": group.group_id,
                "duplication_level": group.duplication_level.value,
                "similarity_score": group.similarity_score,
                "task_count": len(group.tasks),
                "task_ids": [task.get("task_id") for task in group.tasks],
                "merge_strategy": group.merge_strategy.value,
                "recommended_action": group.recommended_action,
                "merged_task_id": group.merged_task.get("task_id") if group.merged_task else None,
                "savings_estimate": group.savings_estimate
            }
            report_data["duplicate_groups"].append(group_data)

        # JSON保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"📊 重複排除レポート保存完了: {output_path}")
        return output_path


def main():
    """テスト実行"""

    print("🧪 TaskDeduplicator テスト実行")

    deduplicator = TaskDeduplicator()

    # テストタスクデータ（重複を含む）
    test_tasks = [
        {
            "task_id": "task_001",
            "type": "file_code_modification",
            "target_files": ["file_a.py"],
            "requirements": {"error_type": "no-untyped-def"},
            "priority": "high",
            "description": "no-untyped-def修正",
            "timestamp": "2025-08-13T10:00:00"
        },
        {
            "task_id": "task_002",
            "type": "file_code_modification",
            "target_files": ["file_a.py"],
            "requirements": {"error_type": "no-untyped-def"},
            "priority": "medium",
            "description": "型注釈修正",
            "timestamp": "2025-08-13T10:05:00"
        },
        {
            "task_id": "task_003",
            "type": "file_code_modification",
            "target_files": ["file_b.py", "file_c.py"],
            "requirements": {"error_type": "no-untyped-call"},
            "priority": "low",
            "description": "call修正",
            "timestamp": "2025-08-13T10:10:00"
        },
        {
            "task_id": "task_004",
            "type": "file_code_modification",
            "target_files": ["file_a.py", "file_b.py"],
            "requirements": {"error_type": "no-untyped-def"},
            "priority": "high",
            "description": "untyped-def エラー修正",
            "timestamp": "2025-08-13T10:15:00"
        }
    ]

    # 重複パターン分析
    print("\n📊 重複パターン分析:")
    analysis = deduplicator.analyze_duplication_patterns(test_tasks)
    print(f"総タスク数: {analysis['total_tasks']}")
    print(f"重複パターン: {len(analysis['duplication_patterns'])}")
    print(f"共通ターゲット: {len(analysis['common_targets'])}")

    # 重複排除実行
    print("\n🔄 重複排除実行:")
    report = deduplicator.deduplicate_tasks(test_tasks)

    print(f"\n📊 結果サマリー:")
    print(f"元のタスク数: {report.original_task_count}")
    print(f"重複グループ: {report.duplicate_groups_found}")
    print(f"削除タスク: {report.tasks_removed}")
    print(f"統合タスク: {report.tasks_merged}")
    print(f"時間節約: {report.estimated_time_saved:.1f}分")
    print(f"トークン節約: {report.estimated_token_saved}")

    # レポート保存
    deduplicator.save_deduplication_report(report)

    print("\n✅ TaskDeduplicator テスト完了")


if __name__ == "__main__":
    main()
