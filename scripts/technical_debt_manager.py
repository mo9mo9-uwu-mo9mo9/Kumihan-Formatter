#!/usr/bin/env python3
"""
Kumihan-Formatter Technical Debt Management System
Issue #1240: Development Process Normalization

技術的負債の自動検出・分類・追跡・報告を行うシステム
"""

import os
import sys
import json
import yaml
import subprocess
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# プロジェクトルートの取得
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from kumihan_formatter.core.utilities.logger import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)


class DebtSeverity(Enum):
    """技術的負債の重要度レベル"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DebtType(Enum):
    """技術的負債のタイプ"""

    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    PERFORMANCE = "performance"


@dataclass
class TechnicalDebt:
    """技術的負債項目"""

    id: str
    title: str
    description: str
    severity: DebtSeverity
    debt_type: DebtType
    file_path: str
    line_number: Optional[int]
    detected_date: datetime.datetime
    estimated_effort_hours: float
    auto_detected: bool = False
    resolution_status: str = "open"


class TechnicalDebtManager:
    """技術的負債管理システム"""

    def __init__(self, config_path: Optional[str] = None):
        """初期化"""
        self.config_path = (
            config_path or PROJECT_ROOT / ".github" / "quality" / "technical_debt.yml"
        )
        self.config = self._load_config()
        self.debt_db_path = PROJECT_ROOT / "tmp" / "technical_debt.json"
        self.debt_db_path.parent.mkdir(exist_ok=True)
        self.debts: List[TechnicalDebt] = self._load_existing_debts()

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルの読み込み"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー: {e}")
            return {}

    def _load_existing_debts(self) -> List[TechnicalDebt]:
        """既存の技術的負債データの読み込み"""
        if not self.debt_db_path.exists():
            return []

        try:
            with open(self.debt_db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                debts = []
                for item in data:
                    debt = TechnicalDebt(
                        id=item["id"],
                        title=item["title"],
                        description=item["description"],
                        severity=DebtSeverity(item["severity"]),
                        debt_type=DebtType(item["debt_type"]),
                        file_path=item["file_path"],
                        line_number=item.get("line_number"),
                        detected_date=datetime.datetime.fromisoformat(
                            item["detected_date"]
                        ),
                        estimated_effort_hours=item["estimated_effort_hours"],
                        auto_detected=item.get("auto_detected", False),
                        resolution_status=item.get("resolution_status", "open"),
                    )
                    debts.append(debt)
                return debts
        except Exception as e:
            logger.error(f"技術的負債データ読み込みエラー: {e}")
            return []

    def _save_debts(self):
        """技術的負債データの保存"""
        try:
            data = []
            for debt in self.debts:
                data.append(
                    {
                        "id": debt.id,
                        "title": debt.title,
                        "description": debt.description,
                        "severity": debt.severity.value,
                        "debt_type": debt.debt_type.value,
                        "file_path": debt.file_path,
                        "line_number": debt.line_number,
                        "detected_date": debt.detected_date.isoformat(),
                        "estimated_effort_hours": debt.estimated_effort_hours,
                        "auto_detected": debt.auto_detected,
                        "resolution_status": debt.resolution_status,
                    }
                )

            with open(self.debt_db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"技術的負債データを保存しました: {len(data)}件")
        except Exception as e:
            logger.error(f"技術的負債データ保存エラー: {e}")

    def detect_code_quality_debt(self) -> List[TechnicalDebt]:
        """コード品質に関する技術的負債の検出"""
        debts = []

        try:
            # mypy実行
            mypy_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "mypy",
                    str(PROJECT_ROOT / "kumihan_formatter"),
                    "--ignore-missing-imports",
                ],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            mypy_errors = mypy_result.stdout.count("error:")
            if mypy_errors > self.config.get("tracking", {}).get("detection", {}).get(
                "static_analysis", {}
            ).get("tools", [{}])[0].get("threshold", 150):
                debt = TechnicalDebt(
                    id=f"mypy_errors_{datetime.datetime.now().strftime('%Y%m%d')}",
                    title=f"mypy型エラー過多 ({mypy_errors}個)",
                    description=f"mypyで{mypy_errors}個の型エラーが検出されました。目標値を超過しています。",
                    severity=DebtSeverity.HIGH,
                    debt_type=DebtType.CODE_QUALITY,
                    file_path="kumihan_formatter/",
                    line_number=None,
                    detected_date=datetime.datetime.now(),
                    estimated_effort_hours=mypy_errors * 0.5,  # 1エラー30分見積もり
                    auto_detected=True,
                )
                debts.append(debt)

            # 巨大ファイル検出
            for py_file in (PROJECT_ROOT / "kumihan_formatter").rglob("*.py"):
                lines = len(py_file.read_text(encoding="utf-8").splitlines())
                if lines > 500:  # 500行以上の大きなファイル
                    debt = TechnicalDebt(
                        id=f"large_file_{py_file.stem}_{datetime.datetime.now().strftime('%Y%m%d')}",
                        title=f"巨大ファイル: {py_file.name} ({lines}行)",
                        description=f"{py_file}が{lines}行になっており、保守が困難です。分割を検討してください。",
                        severity=(
                            DebtSeverity.HIGH if lines > 1000 else DebtSeverity.MEDIUM
                        ),
                        debt_type=DebtType.CODE_QUALITY,
                        file_path=str(py_file.relative_to(PROJECT_ROOT)),
                        line_number=None,
                        detected_date=datetime.datetime.now(),
                        estimated_effort_hours=max(
                            2, lines / 200
                        ),  # 200行で1時間見積もり
                        auto_detected=True,
                    )
                    debts.append(debt)

        except Exception as e:
            logger.error(f"コード品質負債検出エラー: {e}")

        return debts

    def detect_testing_debt(self) -> List[TechnicalDebt]:
        """テスト関連の技術的負債検出"""
        debts = []

        try:
            # テストカバレッジ確認
            coverage_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--cov=kumihan_formatter",
                    "--cov-report=term-missing",
                    "--quiet",
                ],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            # カバレッジパーセンテージを抽出（簡単な実装）
            coverage_line = [
                line for line in coverage_result.stdout.split("\n") if "TOTAL" in line
            ]
            if coverage_line:
                try:
                    coverage_percent = int(coverage_line[0].split()[-1].rstrip("%"))
                    if coverage_percent < 60:  # 60%未満の場合
                        debt = TechnicalDebt(
                            id=f"low_coverage_{datetime.datetime.now().strftime('%Y%m%d')}",
                            title=f"低テストカバレッジ ({coverage_percent}%)",
                            description=f"テストカバレッジが{coverage_percent}%と低く、品質リスクがあります。",
                            severity=(
                                DebtSeverity.CRITICAL
                                if coverage_percent < 30
                                else DebtSeverity.HIGH
                            ),
                            debt_type=DebtType.TESTING,
                            file_path="tests/",
                            line_number=None,
                            detected_date=datetime.datetime.now(),
                            estimated_effort_hours=(80 - coverage_percent)
                            * 0.5,  # 1%向上に30分
                            auto_detected=True,
                        )
                        debts.append(debt)
                except (ValueError, IndexError):
                    pass

        except Exception as e:
            logger.error(f"テスト負債検出エラー: {e}")

        return debts

    def detect_documentation_debt(self) -> List[TechnicalDebt]:
        """ドキュメント関連の技術的負債検出"""
        debts = []

        try:
            # docstring不足の検出
            missing_docstrings = 0
            for py_file in (PROJECT_ROOT / "kumihan_formatter").rglob("*.py"):
                content = py_file.read_text(encoding="utf-8")
                # 簡単な関数・クラス定義とdocstringの確認
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.strip().startswith(
                        ("def ", "class ")
                    ) and not line.strip().startswith("def _"):
                        # 次の行がdocstringかチェック
                        next_lines = lines[i + 1 : i + 3]
                        has_docstring = any(
                            '"""' in line or "'''" in line for line in next_lines
                        )
                        if not has_docstring:
                            missing_docstrings += 1

            if missing_docstrings > 20:  # 20以上の関数/クラスでdocstring不足
                debt = TechnicalDebt(
                    id=f"missing_docstrings_{datetime.datetime.now().strftime('%Y%m%d')}",
                    title=f"docstring不足 ({missing_docstrings}個)",
                    description=f"{missing_docstrings}個の関数・クラスでdocstringが不足しています。",
                    severity=DebtSeverity.MEDIUM,
                    debt_type=DebtType.DOCUMENTATION,
                    file_path="kumihan_formatter/",
                    line_number=None,
                    detected_date=datetime.datetime.now(),
                    estimated_effort_hours=missing_docstrings * 0.25,  # 1個15分
                    auto_detected=True,
                )
                debts.append(debt)

        except Exception as e:
            logger.error(f"ドキュメント負債検出エラー: {e}")

        return debts

    def run_full_detection(self) -> List[TechnicalDebt]:
        """全技術的負債検出の実行"""
        logger.info("技術的負債検出を開始します...")

        all_debts = []
        all_debts.extend(self.detect_code_quality_debt())
        all_debts.extend(self.detect_testing_debt())
        all_debts.extend(self.detect_documentation_debt())

        # 既存の負債と重複チェック・更新
        existing_ids = {debt.id for debt in self.debts}
        new_debts = [debt for debt in all_debts if debt.id not in existing_ids]

        self.debts.extend(new_debts)
        self._save_debts()

        logger.info(
            f"技術的負債検出完了: 新規{len(new_debts)}件, 総計{len(self.debts)}件"
        )
        return new_debts

    def generate_weekly_report(self) -> str:
        """週次レポートの生成"""
        report_date = datetime.datetime.now().strftime("%Y-%m-%d")

        # 重要度別集計
        severity_counts = {}
        for severity in DebtSeverity:
            severity_counts[severity.value] = len(
                [
                    d
                    for d in self.debts
                    if d.severity == severity and d.resolution_status == "open"
                ]
            )

        # タイプ別集計
        type_counts = {}
        for debt_type in DebtType:
            type_counts[debt_type.value] = len(
                [
                    d
                    for d in self.debts
                    if d.debt_type == debt_type and d.resolution_status == "open"
                ]
            )

        # 古い負債の特定
        week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        old_debts = [
            d
            for d in self.debts
            if d.detected_date < week_ago and d.resolution_status == "open"
        ]

        report = f"""# 技術的負債 週次レポート
生成日時: {report_date}

## 📊 現在の技術的負債状況

### 重要度別
- 🔴 Critical: {severity_counts['critical']}件
- 🟡 High: {severity_counts['high']}件
- 🟢 Medium: {severity_counts['medium']}件
- ⚪ Low: {severity_counts['low']}件

**合計: {sum(severity_counts.values())}件**

### タイプ別
- コード品質: {type_counts['code_quality']}件
- アーキテクチャ: {type_counts['architecture']}件
- ドキュメント: {type_counts['documentation']}件
- テスト: {type_counts['testing']}件
- パフォーマンス: {type_counts['performance']}件

## ⚠️ 対応が必要な項目

### 1週間以上未解決の負債
"""

        if old_debts:
            for debt in sorted(
                old_debts[:10], key=lambda x: x.detected_date
            ):  # 古い順に最大10件
                days_old = (datetime.datetime.now() - debt.detected_date).days
                report += f"\n- **{debt.title}** ({debt.severity.value})\n"
                report += f"  - ファイル: {debt.file_path}\n"
                report += f"  - 検出日: {debt.detected_date.strftime('%Y-%m-%d')} ({days_old}日前)\n"
                report += f"  - 見積工数: {debt.estimated_effort_hours:.1f}時間\n"
        else:
            report += "\n✅ 1週間以上未解決の負債はありません。"

        report += f"""

## 📈 推奨アクション

### 今週の目標
- Critical負債: {severity_counts['critical']}件 → 0件 (100%解決)
- High負債: {severity_counts['high']}件 → {int(severity_counts['high'] * 0.2)}件 (80%解決)
- Medium負債: {severity_counts['medium']}件 → {int(severity_counts['medium'] * 0.5)}件 (50%解決)

### 優先対応項目
1. Critical負債の即座解決
2. High負債の計画的解決
3. 古い負債の優先処理

---
*Generated by Technical Debt Manager - Issue #1240*
"""

        # レポートをファイルに保存
        report_path = PROJECT_ROOT / "tmp" / f"technical_debt_report_{report_date}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"週次レポートを生成しました: {report_path}")
        return report

    def get_debt_summary(self) -> Dict[str, Any]:
        """技術的負債サマリーの取得"""
        open_debts = [d for d in self.debts if d.resolution_status == "open"]

        return {
            "total_open_debts": len(open_debts),
            "critical_count": len(
                [d for d in open_debts if d.severity == DebtSeverity.CRITICAL]
            ),
            "high_count": len(
                [d for d in open_debts if d.severity == DebtSeverity.HIGH]
            ),
            "medium_count": len(
                [d for d in open_debts if d.severity == DebtSeverity.MEDIUM]
            ),
            "low_count": len([d for d in open_debts if d.severity == DebtSeverity.LOW]),
            "estimated_total_hours": sum(d.estimated_effort_hours for d in open_debts),
            "oldest_debt_days": max(
                [(datetime.datetime.now() - d.detected_date).days for d in open_debts]
                + [0]
            ),
        }


def main():
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("Usage: python technical_debt_manager.py [detect|report|summary]")
        return

    command = sys.argv[1]
    manager = TechnicalDebtManager()

    if command == "detect":
        new_debts = manager.run_full_detection()
        print(f"✅ 技術的負債検出完了: {len(new_debts)}件の新規負債を検出")

    elif command == "report":
        report = manager.generate_weekly_report()
        print("✅ 週次レポートを生成しました")
        print(report)

    elif command == "summary":
        summary = manager.get_debt_summary()
        print("📊 技術的負債サマリー:")
        print(f"  - 総未解決負債: {summary['total_open_debts']}件")
        print(f"  - Critical: {summary['critical_count']}件")
        print(f"  - High: {summary['high_count']}件")
        print(f"  - Medium: {summary['medium_count']}件")
        print(f"  - Low: {summary['low_count']}件")
        print(f"  - 見積総工数: {summary['estimated_total_hours']:.1f}時間")
        print(f"  - 最古負債: {summary['oldest_debt_days']}日前")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
