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
import time
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import json

# 統一排他制御マネージャーを使用
try:
    from kumihan_formatter.core.utilities.config_lock_manager import safe_read_config, LockMode
    USE_UNIFIED_LOCKING = True
except ImportError:
    USE_UNIFIED_LOCKING = False

def load_security_config() -> Dict[str, Any]:
    """セキュリティ設定を読み込み（統一排他制御付き）"""
    config_file = Path(__file__).parent / "security_config.json"
    
    if USE_UNIFIED_LOCKING:
        # 統一ロック機構を使用
        return safe_read_config(config_file, default={}, timeout=5.0)
    else:
        # フォールバック：従来のロック機構
        return _load_security_config_fallback(config_file)

def _load_security_config_fallback(config_file: Path) -> Dict[str, Any]:
    """フォールバック用の設定読み込み"""
    if not config_file.exists():
        return {}
        
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                # プラットフォーム非依存のシンプルな実装
                try:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                    config_data = json.load(f)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    return config_data
                except (ImportError, OSError, BlockingIOError):
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

def _load_statistical_parameters() -> Dict[str, Any]:
    """統計計算パラメータを外部設定から読み込み"""
    config_file = Path(__file__).parent.parent / "config" / "statistical_parameters.json"
    
    if USE_UNIFIED_LOCKING:
        return safe_read_config(config_file, default={}, timeout=2.0)
    else:
        return _load_security_config_fallback(config_file)

def wilson_confidence_interval(
    sample_size: int,
    positive_samples: int,
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Wilson信頼区間を計算（理論的根拠に基づく）
    
    Args:
        sample_size: サンプルサイズ
        positive_samples: 陽性サンプル数  
        confidence_level: 信頼水準
        
    Returns:
        (下限, 上限) の信頼区間
    """
    if sample_size == 0:
        return (0.0, 0.0)
    
    # パラメータ設定を読み込み
    params = _load_statistical_parameters()
    stat_params = params.get("statistical_confidence_parameters", {})
    z_scores = stat_params.get("z_scores", {
        "0.90": 1.645, "0.95": 1.96, "0.99": 2.576
    })
    
    # Z値取得
    z = z_scores.get(str(confidence_level), 1.96)
    
    # 標本比率
    p = positive_samples / sample_size
    
    # Wilson信頼区間の計算
    # 理論的根拠: 二項分布の正確な信頼区間
    z_squared = z * z
    denominator = 1 + z_squared / sample_size
    
    # 中央値の調整
    p_adjusted = (p + z_squared / (2 * sample_size)) / denominator
    
    # 信頼区間の幅
    margin = z * math.sqrt(p * (1 - p) / sample_size + z_squared / (4 * sample_size * sample_size)) / denominator
    
    lower = max(0.0, p_adjusted - margin)
    upper = min(1.0, p_adjusted + margin)
    
    return (lower, upper)

def calculate_statistical_confidence(
    sample_size: int,
    positive_samples: int,
    population_size: Optional[int] = None,
    confidence_level: float = 0.95,
    method: str = "wilson_interval"
) -> float:
    """
    統計的信頼度を計算（外部パラメータ化・Wilson信頼区間対応）
    
    Args:
        sample_size: サンプルサイズ
        positive_samples: 陽性サンプル数
        population_size: 母集団サイズ（Noneの場合は無限母集団）
        confidence_level: 信頼水準（デフォルト95%）
        method: 計算手法（wilson_interval, normal_approximation等）
    
    Returns:
        信頼度（0.0-1.0）
    """
    if sample_size == 0:
        return 0.0
    
    # パラメータ設定を読み込み
    params = _load_statistical_parameters()
    stat_params = params.get("statistical_confidence_parameters", {})
    calc_methods = params.get("calculation_methods", {})
    perf_params = params.get("performance_parameters", {})
    
    # 計算手法の決定
    if method == "auto":
        method = calc_methods.get("default_method", "wilson_interval")
    
    # Wilson信頼区間を使用
    if method == "wilson_interval" and stat_params.get("wilson_confidence_interval", {}).get("enabled", True):
        lower, upper = wilson_confidence_interval(sample_size, positive_samples, confidence_level)
        
        # 信頼区間の幅から信頼度を評価
        interval_width = upper - lower
        
        # 理論的最大幅（p=0.5の場合）との比較
        _, max_upper = wilson_confidence_interval(sample_size, sample_size // 2, confidence_level)
        _, max_lower = wilson_confidence_interval(sample_size, sample_size // 2, confidence_level)
        max_width = max_upper - max_lower
        
        if max_width > 0:
            precision = max(0.0, 1.0 - (interval_width / max_width))
        else:
            precision = 1.0
    else:
        # 従来の正規近似手法（フォールバック）
        p = positive_samples / sample_size
        
        # 極端な値の補正（外部パラメータ化）
        extreme_correction = stat_params.get("extreme_value_correction", {})
        if p == 0 or p == 1:
            if extreme_correction.get("use_wilson_interval", True):
                # Wilson区間を使用して補正
                lower, upper = wilson_confidence_interval(sample_size, positive_samples, confidence_level)
                interval_width = upper - lower
                precision = max(0.0, 1.0 - interval_width)
            else:
                # 従来の固定値補正
                correction_factor = extreme_correction.get("fallback_correction_factor", 0.5)
                se = correction_factor / math.sqrt(sample_size)
                z_scores = stat_params.get("z_scores", {"0.95": 1.96})
                z = z_scores.get(str(confidence_level), 1.96)
                margin = z * se
                max_theoretical_margin = z * math.sqrt(0.25 / sample_size)
                precision = max(0.0, 1.0 - (margin / max_theoretical_margin)) if max_theoretical_margin > 0 else 1.0
        else:
            se = math.sqrt(p * (1 - p) / sample_size)
            
            # 有限母集団修正
            if population_size and population_size > sample_size:
                fpc = math.sqrt((population_size - sample_size) / (population_size - 1))
                se *= fpc
            
            z_scores = stat_params.get("z_scores", {"0.95": 1.96})
            z = z_scores.get(str(confidence_level), 1.96)
            margin = z * se
            max_theoretical_margin = z * math.sqrt(0.25 / sample_size)
            precision = max(0.0, 1.0 - (margin / max_theoretical_margin)) if max_theoretical_margin > 0 else 1.0
    
    # サンプルサイズによる信頼度調整（外部パラメータ化）
    thresholds = stat_params.get("sample_size_thresholds", {
        "high_confidence": 100, "medium_confidence": 30, "low_confidence": 10
    })
    factors = stat_params.get("confidence_factors", {})
    
    if sample_size >= thresholds.get("high_confidence", 100):
        size_factor = factors.get("large_sample", 1.0)
    elif sample_size >= thresholds.get("medium_confidence", 30):
        medium_config = factors.get("medium_sample", {"base": 0.7, "increment": 0.3})
        size_factor = medium_config["base"] + medium_config["increment"] * (
            sample_size - thresholds["medium_confidence"]
        ) / (thresholds["high_confidence"] - thresholds["medium_confidence"])
    elif sample_size >= thresholds.get("low_confidence", 10):
        small_config = factors.get("small_sample", {"base": 0.4, "increment": 0.3})
        size_factor = small_config["base"] + small_config["increment"] * (
            sample_size - thresholds["low_confidence"]
        ) / (thresholds["medium_confidence"] - thresholds["low_confidence"])
    else:
        minimal_config = factors.get("minimal_sample", {"base": 0.1, "increment": 0.3})
        size_factor = minimal_config["base"] + minimal_config["increment"] * sample_size / thresholds["low_confidence"]
    
    confidence = precision * size_factor
    
    # 精度調整（外部パラメータ化）
    precision_digits = perf_params.get("precision_digits", 3)
    return round(confidence, precision_digits)

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