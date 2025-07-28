#!/usr/bin/env python3
"""
Security Test Utilities - Issue #640 Phase 3
セキュリティテスト共通ユーティリティ

目的: セキュリティテストで使用する共通機能
- 統計的信頼度計算
- リスク評価
- 共通パターン処理
"""

import math
import statistics
import fcntl
import time
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import json

def load_security_config() -> Dict[str, Any]:
    """セキュリティ設定を読み込み（排他制御付き）"""
    config_file = Path(__file__).parent / "security_config.json"
    if config_file.exists():
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    # Unix系でのファイルロック
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                        config_data = json.load(f)
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                        return config_data
                    except (OSError, BlockingIOError):
                        # Windows対応またはロック失敗時は短時間待機後リトライ
                        if attempt < max_retries - 1:
                            time.sleep(0.1 * (attempt + 1))
                            continue
                        else:
                            # ロックなしで読み込み
                            f.seek(0)
                            return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, PermissionError):
                if attempt < max_retries - 1:
                    time.sleep(0.05)
                    continue
                break
    return {}

def calculate_statistical_confidence(
    sample_size: int,
    positive_samples: int,
    population_size: Optional[int] = None,
    confidence_level: float = 0.95
) -> float:
    """
    統計的信頼度を計算
    
    Args:
        sample_size: サンプルサイズ
        positive_samples: 陽性サンプル数
        population_size: 母集団サイズ（Noneの場合は無限母集団）
        confidence_level: 信頼水準（デフォルト95%）
    
    Returns:
        信頼度（0.0-1.0）
    """
    if sample_size == 0:
        return 0.0
    
    # 標本比率
    p = positive_samples / sample_size
    
    # 標準誤差計算
    if p == 0 or p == 1:
        # 極端な値の場合は補正
        se = 0.5 / math.sqrt(sample_size)
    else:
        se = math.sqrt(p * (1 - p) / sample_size)
    
    # 有限母集団修正
    if population_size and population_size > sample_size:
        fpc = math.sqrt((population_size - sample_size) / (population_size - 1))
        se *= fpc
    
    # Z値（95%信頼区間の場合は1.96）
    z_scores = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576
    }
    z = z_scores.get(confidence_level, 1.96)
    
    # 信頼区間幅
    margin = z * se
    
    # 信頼度計算（理論的根拠に基づく）
    # 最大理論マージンは比率が0.5の時に最大となる: z * sqrt(0.25/n)
    max_theoretical_margin = z * math.sqrt(0.25 / sample_size)
    
    # 相対的信頼度（実際のマージンと理論的最大マージンの比較）
    if max_theoretical_margin > 0:
        relative_precision = max(0.0, 1.0 - (margin / max_theoretical_margin))
    else:
        relative_precision = 1.0
    
    # サンプルサイズによる信頼度調整（より段階的）
    if sample_size >= 100:
        size_factor = 1.0
    elif sample_size >= 30:
        size_factor = 0.7 + 0.3 * (sample_size - 30) / 70
    elif sample_size >= 10:
        size_factor = 0.4 + 0.3 * (sample_size - 10) / 20
    else:
        size_factor = 0.1 + 0.3 * sample_size / 10
    
    confidence = relative_precision * size_factor
    
    return round(confidence, 3)

def calculate_regression_confidence(
    measurements: List[float],
    baseline: float,
    threshold: float
) -> float:
    """
    パフォーマンス回帰の信頼度を計算
    
    Args:
        measurements: 測定値のリスト
        baseline: ベースライン値
        threshold: 閾値
    
    Returns:
        信頼度（0.0-1.0）
    """
    if not measurements:
        return 0.0
    
    # 基本統計量
    mean = statistics.mean(measurements)
    
    if len(measurements) < 2:
        # サンプルが少ない場合は低信頼度
        return 0.3
    
    stdev = statistics.stdev(measurements)
    
    # 変動係数（CV）
    cv = stdev / mean if mean != 0 else 1.0
    
    # 回帰の程度
    regression = abs(mean - baseline) / baseline if baseline != 0 else 0
    
    # t統計量（簡易版）
    se = stdev / math.sqrt(len(measurements))
    t_stat = abs(mean - baseline) / se if se > 0 else 0
    
    # 信頼度計算
    # 1. 変動が小さいほど高信頼度
    stability_score = max(0, 1 - cv)
    
    # 2. 回帰が閾値を超えているほど高信頼度
    regression_score = min(1.0, regression / threshold) if threshold > 0 else 0
    
    # 3. t統計量が大きいほど高信頼度
    t_score = min(1.0, t_stat / 2.0)  # t > 2 で高信頼度
    
    # 4. サンプルサイズ
    size_score = min(1.0, len(measurements) / 10.0)
    
    # 総合信頼度
    confidence = (stability_score * 0.3 + 
                 regression_score * 0.3 + 
                 t_score * 0.3 + 
                 size_score * 0.1)
    
    return round(confidence, 3)

def calculate_memory_leak_confidence(
    memory_samples: List[Tuple[int, int]],
    iterations: int
) -> float:
    """
    メモリリークの信頼度を計算
    
    Args:
        memory_samples: (iteration, memory_usage)のタプルリスト
        iterations: 総イテレーション数
    
    Returns:
        信頼度（0.0-1.0）
    """
    if len(memory_samples) < 2:
        return 0.0
    
    # 線形回帰で傾きを計算
    x_values = [sample[0] for sample in memory_samples]
    y_values = [sample[1] for sample in memory_samples]
    
    # 相関係数
    if len(set(x_values)) == 1 or len(set(y_values)) == 1:
        return 0.0
    
    try:
        correlation = statistics.correlation(x_values, y_values)
    except:
        correlation = 0.0
    
    # 決定係数
    r_squared = correlation ** 2
    
    # サンプル密度
    sample_density = len(memory_samples) / iterations if iterations > 0 else 0
    
    # 信頼度計算
    confidence = (r_squared * 0.7 +  # 相関の強さ
                 sample_density * 0.3)  # サンプルの密度
    
    return round(confidence, 3)

def assess_combined_risk(risks: List[Tuple[str, float, float]]) -> Tuple[str, float]:
    """
    複数のリスクを組み合わせて総合リスクを評価
    
    Args:
        risks: [(risk_level, severity_score, confidence)]のリスト
    
    Returns:
        (overall_risk_level, combined_score)
    """
    if not risks:
        return ("safe", 0.0)
    
    config = load_security_config()
    risk_scoring = config.get('risk_scoring', {})
    
    critical_threshold = risk_scoring.get('critical_threshold', 9.0)
    high_threshold = risk_scoring.get('high_threshold', 7.0)
    medium_threshold = risk_scoring.get('medium_threshold', 4.0)
    low_threshold = risk_scoring.get('low_threshold', 2.0)
    
    # 重み付き平均スコア
    total_weight = 0
    weighted_score = 0
    
    for risk_level, severity, confidence in risks:
        weight = confidence
        weighted_score += severity * weight
        total_weight += weight
    
    if total_weight == 0:
        return ("safe", 0.0)
    
    combined_score = weighted_score / total_weight
    
    # リスクレベル判定
    if combined_score >= critical_threshold:
        risk_level = "critical"
    elif combined_score >= high_threshold:
        risk_level = "high"
    elif combined_score >= medium_threshold:
        risk_level = "medium"
    elif combined_score >= low_threshold:
        risk_level = "low"
    else:
        risk_level = "safe"
    
    return (risk_level, round(combined_score, 2))

def get_exclude_patterns() -> List[str]:
    """除外パターンを取得"""
    config = load_security_config()
    return config.get('platform_specific', {}).get('exclude_patterns', [
        "tests/", "venv/", ".venv/", "__pycache__/",
        ".git/", "build/", "dist/", ".tox/", "node_modules/",
        "static/", "assets/"
    ])

def should_scan_file(file_path: Path) -> bool:
    """ファイルをスキャンすべきかチェック"""
    file_str = str(file_path)
    exclude_patterns = get_exclude_patterns()
    
    for pattern in exclude_patterns:
        if pattern in file_str:
            return False
    
    return True

def get_required_validations(validation_type: str) -> List[str]:
    """必須検証項目を取得"""
    config = load_security_config()
    return config.get('platform_specific', {}).get('required_validations', {}).get(validation_type, [])

def get_regression_thresholds() -> Dict[str, float]:
    """回帰検出閾値を取得"""
    config = load_security_config()
    return config.get('regression_thresholds', {
        "execution_time": 0.15,
        "memory_usage": 0.20,
        "cpu_usage": 0.25,
        "throughput": -0.10
    })

def get_alert_thresholds() -> Dict[str, float]:
    """アラート閾値を取得"""
    config = load_security_config()
    return config.get('alert_thresholds', {
        "coverage_drop": 5.0,
        "complexity_increase": 3.0,
        "test_failure": 1,
        "quality_score_drop": 10.0
    })