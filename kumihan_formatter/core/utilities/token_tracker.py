"""
Token使用量追跡システム
Claude単体 vs Claude+Gemini協業のToken節約効果を自動追跡

シンプル実装・オーバーエンジニアリングなし
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logger import get_logger

logger = get_logger(__name__)


def estimate_tokens(text: str) -> int:
    """Token推定（文字数ベース）

    Args:
        text: 推定対象テキスト

    Returns:
        推定Token数
    """
    if not text:
        return 0
    # 保守的推定：文字数÷2.5
    return max(1, len(text) // 2)


def log_task_usage(
    task_name: str,
    prompt_text: str,
    response_text: str,
    execution_method: str = "claude_solo",  # "gemini_collaboration" | "claude_solo"
    claude_solo_estimate: Optional[int] = None,
) -> None:
    """Task使用量をログ記録

    Args:
        task_name: タスク名
        prompt_text: プロンプトテキスト
        response_text: レスポンステキスト
        execution_method: 実行方式
        claude_solo_estimate: Claude単体での推定Token数
    """
    actual_prompt_tokens = estimate_tokens(prompt_text)
    actual_response_tokens = estimate_tokens(response_text)
    actual_total = actual_prompt_tokens + actual_response_tokens

    # Claude単体推定（指定されていない場合は実際の1.5-2倍と仮定）
    if claude_solo_estimate is None:
        if execution_method == "gemini_collaboration":
            claude_solo_estimate = int(actual_total * 2.0)  # 2倍と仮定
        else:
            claude_solo_estimate = actual_total

    savings = claude_solo_estimate - actual_total
    savings_pct = (
        (savings / claude_solo_estimate * 100) if claude_solo_estimate > 0 else 0
    )

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "task_name": task_name,
        "execution_method": execution_method,
        "actual_prompt_tokens": actual_prompt_tokens,
        "actual_response_tokens": actual_response_tokens,
        "actual_total": actual_total,
        "claude_solo_estimate": claude_solo_estimate,
        "savings": savings,
        "savings_pct": round(savings_pct, 1),
    }

    # tmp/token_usage.jsonl に追記
    log_file = Path("tmp/token_usage.jsonl")
    log_file.parent.mkdir(exist_ok=True)

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        logger.info(
            f"Token使用量記録: {task_name} ({execution_method}) - "
            f"実際:{actual_total}, 推定:{claude_solo_estimate}, "
            f"節約:{savings} ({savings_pct:.1f}%)"
        )

    except Exception as e:
        logger.error(f"Token使用量記録エラー: {e}")


def load_usage_data() -> List[Dict[str, Any]]:
    """使用量データ読み込み

    Returns:
        使用量データリスト
    """
    log_file = Path("tmp/token_usage.jsonl")
    if not log_file.exists():
        return []

    data = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    except Exception as e:
        logger.error(f"使用量データ読み込みエラー: {e}")

    return data


def generate_report() -> str:
    """Token使用量レポート生成

    Returns:
        生成されたレポートファイルパス
    """
    data = load_usage_data()
    if not data:
        logger.warning("Token使用量データがありません")
        return ""

    # レポート生成
    report_lines = [
        "# Token使用量レポート",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 作業別Token使用量",
        "| 作業名 | 実行方式 | Claude単体推定 | 実際使用 | 節約量 | 節約率 |",
        "|--------|----------|----------------|----------|--------|--------|",
    ]

    total_claude_estimate = 0
    total_actual = 0
    gemini_tasks = 0
    claude_tasks = 0

    for entry in data:
        task_name = entry["task_name"]
        method = entry["execution_method"]
        claude_est = entry["claude_solo_estimate"]
        actual = entry["actual_total"]
        savings = entry["savings"]
        savings_pct = entry["savings_pct"]

        method_display = (
            "Gemini協業" if method == "gemini_collaboration" else "Claude単体"
        )

        report_lines.append(
            f"| {task_name} | {method_display} | {claude_est:,} | "
            f"{actual:,} | {savings:,} | {savings_pct}% |"
        )

        total_claude_estimate += claude_est
        total_actual += actual

        if method == "gemini_collaboration":
            gemini_tasks += 1
        else:
            claude_tasks += 1

    # サマリー計算
    total_savings = total_claude_estimate - total_actual
    avg_savings_pct = (
        (total_savings / total_claude_estimate * 100)
        if total_claude_estimate > 0
        else 0
    )

    report_lines.extend(
        [
            "",
            "## サマリー",
            f"- 総作業数: {len(data)} (Gemini協業: {gemini_tasks}, Claude単体: {claude_tasks})",
            f"- Claude単体推定総Token: {total_claude_estimate:,}",
            f"- 実際使用総Token: {total_actual:,}",
            f"- 総節約Token: {total_savings:,}",
            f"- 平均節約率: {avg_savings_pct:.1f}%",
        ]
    )

    # ファイル出力
    report_file = Path("tmp/token_report.md")
    report_file.parent.mkdir(exist_ok=True)

    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        logger.info(f"Token使用量レポート生成完了: {report_file}")
        return str(report_file)

    except Exception as e:
        logger.error(f"レポート生成エラー: {e}")
        return ""


def get_latest_savings() -> Optional[Dict[str, Any]]:
    """最新のToken節約効果取得

    Returns:
        最新の節約効果サマリー
    """
    data = load_usage_data()
    if not data:
        return None

    # Gemini協業のみの集計
    gemini_data = [
        entry for entry in data if entry["execution_method"] == "gemini_collaboration"
    ]
    if not gemini_data:
        return None

    total_actual = sum(entry["actual_total"] for entry in gemini_data)
    total_estimate = sum(entry["claude_solo_estimate"] for entry in gemini_data)
    total_savings = total_estimate - total_actual

    avg_savings_pct = (
        (total_savings / total_estimate * 100) if total_estimate > 0 else 0
    )

    return {
        "gemini_tasks": len(gemini_data),
        "total_actual_tokens": total_actual,
        "total_claude_estimate": total_estimate,
        "total_savings": total_savings,
        "avg_savings_pct": round(avg_savings_pct, 1),
    }
