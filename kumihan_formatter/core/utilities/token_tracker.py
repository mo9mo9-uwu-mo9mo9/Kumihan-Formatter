"""
Token使用量追跡システム
Claude単体でのToken使用量を追跡

シンプル実装・オーバーエンジニアリングなし
"""

import json
import logging
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)


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
) -> None:
    """Task使用量をログ記録

    Args:
        task_name: タスク名
        prompt_text: プロンプトテキスト
        response_text: レスポンステキスト
    """
    actual_prompt_tokens = estimate_tokens(prompt_text)
    actual_response_tokens = estimate_tokens(response_text)
    actual_total = actual_prompt_tokens + actual_response_tokens

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "task_name": task_name,
        "actual_prompt_tokens": actual_prompt_tokens,
        "actual_response_tokens": actual_response_tokens,
        "actual_total": actual_total,
    }

    # tmp/token_usage.jsonl に追記
    log_file = Path("tmp/token_usage.jsonl")
    log_file.parent.mkdir(exist_ok=True)

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        logger.info(
            f"Token使用量記録: {task_name} - "
            f"プロンプト:{actual_prompt_tokens}, レスポンス:{actual_response_tokens}, "
            f"合計:{actual_total}"
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
        "| 作業名 | プロンプト | レスポンス | 合計 |",
        "|--------|-----------|-----------|------|",
    ]

    total_tokens = 0
    total_tasks = 0

    for entry in data:
        task_name = entry["task_name"]
        prompt_tokens = entry["actual_prompt_tokens"]
        response_tokens = entry["actual_response_tokens"]
        total = entry["actual_total"]

        report_lines.append(
            f"| {task_name} | {prompt_tokens:,} | " f"{response_tokens:,} | {total:,} |"
        )

        total_tokens += total
        total_tasks += 1

    # サマリー計算
    avg_tokens_per_task = total_tokens / total_tasks if total_tasks > 0 else 0

    report_lines.extend(
        [
            "",
            "## サマリー",
            f"- 総作業数: {total_tasks}",
            f"- 使用総Token: {total_tokens:,}",
            f"- 平均Token/作業: {avg_tokens_per_task:.1f}",
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
