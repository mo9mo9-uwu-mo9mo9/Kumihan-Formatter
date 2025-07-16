"""
メモリリーク検出器 - 高度なリーク分析

メモリリークの検出と分析を行う専用モジュール
Issue #402対応 - パフォーマンス最適化
"""

import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from .memory_types import MemoryLeak, MemorySnapshot, LEAK_SEVERITY_THRESHOLDS
from ..utilities.logger import get_logger


class MemoryLeakDetector:
    """メモリリーク検出と分析機能
    
    機能:
    - オブジェクトカウント増加の検出
    - リーク深刻度の計算  
    - リークパターンの分析
    - リーク履歴の管理
    """

    def __init__(
        self,
        leak_detection_threshold: int = 10,
        min_data_points: int = 10,
        analysis_window_hours: float = 24.0,
    ):
        """メモリリーク検出器を初期化

        Args:
            leak_detection_threshold: リーク検出の閾値
            min_data_points: 分析に必要な最小データポイント数
            analysis_window_hours: 分析対象の時間窓（時間）
        """
        self.logger = get_logger(__name__)
        self.leak_detection_threshold = leak_detection_threshold
        self.min_data_points = min_data_points
        self.analysis_window_seconds = analysis_window_hours * 3600

        # リーク追跡データ
        self.detected_leaks: Dict[str, MemoryLeak] = {}
        self.object_history: Dict[str, List[Tuple[float, int]]] = defaultdict(list)
        
        self.logger.info(
            f"メモリリーク検出器初期化完了 threshold={leak_detection_threshold}, "
            f"min_data_points={min_data_points}, analysis_window_hours={analysis_window_hours}"
        )

    def analyze_snapshot(self, snapshot: MemorySnapshot) -> None:
        """スナップショットを分析してリークを検出

        Args:
            snapshot: 分析対象のメモリスナップショット
        """
        # GCオブジェクト数の記録
        self._record_object_count("gc_objects", snapshot.timestamp, snapshot.gc_objects)
        
        # カスタムオブジェクトの記録
        for obj_type, count in snapshot.custom_objects.items():
            self._record_object_count(obj_type, snapshot.timestamp, count)
        
        # 古いデータの削除
        self._remove_old_data(snapshot.timestamp)
        
        # リーク検出の実行
        self._detect_memory_leaks()

    def _record_object_count(self, obj_type: str, timestamp: float, count: int) -> None:
        """オブジェクトカウントを記録

        Args:
            obj_type: オブジェクトタイプ
            timestamp: タイムスタンプ
            count: オブジェクト数
        """
        history = self.object_history[obj_type]
        history.append((timestamp, count))
        
        # 効率性のため、履歴の長さを制限
        if len(history) > 1000:
            self.object_history[obj_type] = history[-500:]

    def _remove_old_data(self, current_timestamp: float) -> None:
        """古いデータを削除

        Args:
            current_timestamp: 現在のタイムスタンプ
        """
        cutoff_time = current_timestamp - self.analysis_window_seconds
        
        for obj_type in list(self.object_history.keys()):
            history = self.object_history[obj_type]
            # 古いデータを削除
            valid_data = [(ts, count) for ts, count in history if ts >= cutoff_time]
            
            if valid_data:
                self.object_history[obj_type] = valid_data
            else:
                del self.object_history[obj_type]

    def get_memory_leaks(self, severity_filter: Optional[str] = None) -> List[MemoryLeak]:
        """検出されたメモリリークを取得

        Args:
            severity_filter: 深刻度フィルター (low, medium, high, critical)

        Returns:
            List[MemoryLeak]: 検出されたリークのリスト（深刻度順）
        """
        leaks = list(self.detected_leaks.values())
        
        # 深刻度フィルター
        if severity_filter:
            leaks = [leak for leak in leaks if leak.severity == severity_filter]
        
        # 深刻度順でソート（高い順）
        leaks.sort(key=lambda x: x.severity_score, reverse=True)
        
        return leaks

    def get_critical_leaks(self) -> List[MemoryLeak]:
        """クリティカルなリークのみを取得

        Returns:
            List[MemoryLeak]: クリティカルなリークのリスト
        """
        return [leak for leak in self.detected_leaks.values() if leak.is_critical_leak()]

    def get_leak_summary(self) -> Dict[str, any]:
        """リーク検出の概要を取得

        Returns:
            Dict: リーク検出の概要情報
        """
        all_leaks = list(self.detected_leaks.values())
        
        severity_counts = defaultdict(int)
        for leak in all_leaks:
            severity_counts[leak.severity] += 1
        
        total_objects_leaked = sum(leak.count_increase for leak in all_leaks)
        critical_leaks = self.get_critical_leaks()
        
        return {
            "total_leaks": len(all_leaks),
            "critical_leaks": len(critical_leaks),
            "severity_breakdown": dict(severity_counts),
            "total_objects_leaked": total_objects_leaked,
            "oldest_leak_age": max(
                (leak.age_seconds for leak in all_leaks), default=0.0
            ),
            "tracked_object_types": len(self.object_history),
        }

    def _detect_memory_leaks(self) -> None:
        """メモリリークを検出"""
        current_time = time.time()
        
        for obj_type, history in self.object_history.items():
            if len(history) < self.min_data_points:
                continue
                
            leak_info = self._analyze_object_leak(obj_type, history, current_time)
            if leak_info:
                object_type, count_increase, size_estimate, first_detected = leak_info
                
                if object_type in self.detected_leaks:
                    # 既存のリークを更新
                    existing_leak = self.detected_leaks[object_type]
                    existing_leak.count_increase = count_increase
                    existing_leak.last_detected = current_time
                else:
                    # 新しいリークを作成
                    severity = self._calculate_leak_severity(count_increase, size_estimate)
                    
                    new_leak = MemoryLeak(
                        object_type=object_type,
                        count_increase=count_increase,
                        size_estimate=size_estimate,
                        first_detected=first_detected,
                        last_detected=current_time,
                        severity=severity,
                    )
                    
                    self.detected_leaks[object_type] = new_leak
                    
                    self.logger.warning(
                        f"メモリリーク検出: {object_type} count_increase={count_increase}, "
                        f"severity={severity}, estimated_size_mb={size_estimate / 1024 / 1024:.2f}"
                    )

    def _analyze_object_leak(
        self, obj_type: str, history: List[Tuple[float, int]], current_time: float
    ) -> Optional[Tuple[str, int, int, float]]:
        """オブジェクトタイプのリークを分析

        Args:
            obj_type: オブジェクトタイプ
            history: オブジェカウント履歴 [(timestamp, count), ...]
            current_time: 現在時刻

        Returns:
            Optional[Tuple]: (object_type, count_increase, size_estimate, first_detected)
                           リークが検出されない場合はNone
        """
        if len(history) < 2:
            return None
        
        # 最初と最後の値を比較
        start_timestamp, start_count = history[0]
        end_timestamp, end_count = history[-1]
        
        count_increase = end_count - start_count
        
        # 閾値チェック
        if count_increase < self.leak_detection_threshold:
            return None
        
        # 時間経過の確認（短時間での一時的な増加を除外）
        time_span = end_timestamp - start_timestamp
        if time_span < 60:  # 1分未満は除外
            return None
        
        # サイズ推定（簡易的）
        estimated_size_per_object = 100  # 100バイト/オブジェクトと仮定
        size_estimate = count_increase * estimated_size_per_object
        
        return (obj_type, count_increase, size_estimate, start_timestamp)

    def _calculate_leak_severity(self, count_increase: int, size_estimate: int) -> str:
        """リークの深刻度を計算

        Args:
            count_increase: オブジェクト数の増加
            size_estimate: 推定サイズ（バイト）

        Returns:
            str: 深刻度 (low, medium, high, critical)
        """
        # オブジェクト数ベースの評価
        if count_increase >= LEAK_SEVERITY_THRESHOLDS["critical"]:
            return "critical"
        elif count_increase >= LEAK_SEVERITY_THRESHOLDS["high"]:
            return "high"
        elif count_increase >= LEAK_SEVERITY_THRESHOLDS["medium"]:
            return "medium"
        elif count_increase >= LEAK_SEVERITY_THRESHOLDS["low"]:
            return "low"
        
        # サイズベースの評価（バックアップ）
        size_mb = size_estimate / 1024 / 1024
        if size_mb >= 50:
            return "critical"
        elif size_mb >= 20:
            return "high"
        elif size_mb >= 5:
            return "medium"
        else:
            return "low"

    def clear_leak_data(self) -> None:
        """リーク検出データをクリア"""
        cleared_leaks = len(self.detected_leaks)
        cleared_history = len(self.object_history)
        
        self.detected_leaks.clear()
        self.object_history.clear()
        
        self.logger.info(
            f"リーク検出データをクリア cleared_leaks={cleared_leaks}, "
            f"cleared_history_types={cleared_history}"
        )