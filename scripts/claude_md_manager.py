#!/usr/bin/env python3
"""
CLAUDE.md Management System - Phase 2 & 3 Implementation
Issue #686 対応: 構造化管理・自動最適化・持続可能運用
"""

import os
import re
import sys
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class CLAUDEmdMetrics:
    """CLAUDE.md メトリクス"""

    timestamp: str
    lines: int
    bytes: int
    sections: int
    deep_nesting: int
    duplicates: int
    long_sections: int
    outdated_markers: int


@dataclass
class StructureIssue:
    """構造問題"""

    type: str
    severity: str  # 'critical', 'warning', 'info'
    line: Optional[int]
    description: str
    suggestion: Optional[str] = None


class CLAUDEmdManager:
    """CLAUDE.md管理システム"""

    def __init__(self, claude_md_path: str = "CLAUDE.md"):
        self.claude_md_path = claude_md_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """設定読み込み"""
        default_config = {
            "limits": {
                # 段階制限システム（緩和版）
                "warning": {"lines": 250, "bytes": 12288},  # 12KB
                "caution": {"lines": 300, "bytes": 15360},  # 15KB
                "critical": {"lines": 400, "bytes": 20480},  # 20KB
                # 旧制限（参考値・推奨）
                "recommended_lines": 150,
                "recommended_bytes": 8192,  # 8KB
                "max_section_lines": 20,
                "max_nesting_depth": 3,
            },
            "structure": {
                "required_sections": [
                    "AI運用7原則",
                    "基本設定",
                    "必須ルール",
                    "記法仕様",
                ],
                "outdated_markers": ["TODO", "FIXME", "v1.", "alpha-", "beta-"],
            },
            "optimization": {
                "enabled": True,
                "auto_fix": False,
                "backup_before_fix": True,
            },
        }

        config_path = Path(".claude_md_config.yaml")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    def analyze(self) -> Tuple[CLAUDEmdMetrics, List[StructureIssue]]:
        """Phase 2: 構造化分析"""
        if not os.path.exists(self.claude_md_path):
            raise FileNotFoundError(f"{self.claude_md_path} not found")

        with open(self.claude_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()
        metrics = CLAUDEmdMetrics(
            timestamp=datetime.now().isoformat(),
            lines=len(lines),
            bytes=len(content.encode("utf-8")),
            sections=content.count("#"),
            deep_nesting=content.count("####"),
            duplicates=0,
            long_sections=0,
            outdated_markers=0,
        )

        issues = []

        # 必須セクション確認
        for section in self.config["structure"]["required_sections"]:
            if section not in content:
                issues.append(
                    StructureIssue(
                        type="missing_section",
                        severity="critical",
                        line=None,
                        description=f"必須セクション不在: {section}",
                        suggestion=f"セクション '{section}' を追加してください",
                    )
                )

        # 重複コンテンツ検出
        seen_lines = {}
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith("#"):
                if line in seen_lines:
                    metrics.duplicates += 1
                    issues.append(
                        StructureIssue(
                            type="duplicate_content",
                            severity="warning",
                            line=i + 1,
                            description=f"重複コンテンツ: {line[:50]}...",
                            suggestion="重複する内容を統合または削除",
                        )
                    )
                else:
                    seen_lines[line] = i + 1

        # セクション長分析
        sections = re.split(r"^(#+\s.*)", content, flags=re.MULTILINE)
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                title = sections[i].strip()
                body = sections[i + 1]
                section_lines = len(body.splitlines())

                if section_lines > self.config["limits"]["max_section_lines"]:
                    metrics.long_sections += 1
                    issues.append(
                        StructureIssue(
                            type="long_section",
                            severity="warning",
                            line=None,
                            description=f"長大セクション ({section_lines}行): {title[:30]}...",
                            suggestion=f"セクションを{self.config['limits']['max_section_lines']}行以内に分割",
                        )
                    )

        # 古いマーカー検出
        for marker in self.config["structure"]["outdated_markers"]:
            if marker in content:
                metrics.outdated_markers += 1
                issues.append(
                    StructureIssue(
                        type="outdated_marker",
                        severity="info",
                        line=None,
                        description=f"古いマーカー検出: {marker}",
                        suggestion="古い情報を更新または削除",
                    )
                )

        return metrics, issues

    def optimize(self, auto_fix: bool = False) -> List[str]:
        """Phase 2: 自動最適化提案・実行（段階制限対応）"""
        metrics, issues = self.analyze()
        suggestions = []

        # 重複統合提案
        if metrics.duplicates > 0:
            suggestions.append(f"🔄 {metrics.duplicates}個の重複コンテンツ統合を推奨")

        # セクション分割提案
        if metrics.long_sections > 0:
            suggestions.append(
                f"✂️  {metrics.long_sections}個の長大セクション分割を推奨"
            )

        # 古い情報更新提案
        if metrics.outdated_markers > 0:
            suggestions.append(
                f"🕐 {metrics.outdated_markers}個の古いマーカー更新を推奨"
            )

        # 段階制限チェック
        limits = self.config["limits"]

        # クリティカル制限
        if metrics.lines > limits["critical"]["lines"]:
            suggestions.append(
                f"🚨 行数クリティカル制限超過 ({metrics.lines}/{limits['critical']['lines']}) - 即座に内容削減が必要"
            )
        elif metrics.bytes > limits["critical"]["bytes"]:
            suggestions.append(
                f"🚨 サイズクリティカル制限超過 ({metrics.bytes}B/{limits['critical']['bytes']}B) - 即座に圧縮が必要"
            )

        # 注意制限
        elif metrics.lines > limits["caution"]["lines"]:
            suggestions.append(
                f"⚠️ 行数注意制限超過 ({metrics.lines}/{limits['caution']['lines']}) - 内容削減を検討"
            )
        elif metrics.bytes > limits["caution"]["bytes"]:
            suggestions.append(
                f"⚠️ サイズ注意制限超過 ({metrics.bytes}B/{limits['caution']['bytes']}B) - 圧縮を検討"
            )

        # 警告制限
        elif metrics.lines > limits["warning"]["lines"]:
            suggestions.append(
                f"💡 行数警告制限超過 ({metrics.lines}/{limits['warning']['lines']}) - 見直しを推奨"
            )
        elif metrics.bytes > limits["warning"]["bytes"]:
            suggestions.append(
                f"💡 サイズ警告制限超過 ({metrics.bytes}B/{limits['warning']['bytes']}B) - 最適化を推奨"
            )

        # 推奨制限（情報提供）
        elif metrics.lines > limits["recommended_lines"]:
            suggestions.append(
                f"📝 推奨行数超過 ({metrics.lines}/{limits['recommended_lines']}) - 品質維持のため短縮を検討"
            )
        elif metrics.bytes > limits["recommended_bytes"]:
            suggestions.append(
                f"📦 推奨サイズ超過 ({metrics.bytes}B/{limits['recommended_bytes']}B) - より簡潔な記述を検討"
            )

        # 自動修正実行
        if auto_fix and self.config["optimization"]["auto_fix"]:
            if self.config["optimization"]["backup_before_fix"]:
                self._backup_file()
            suggestions.extend(self._auto_fix_issues(issues))

        return suggestions

    def _backup_file(self):
        """バックアップ作成"""
        backup_path = (
            f"{self.claude_md_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        import shutil

        shutil.copy2(self.claude_md_path, backup_path)
        print(f"📋 バックアップ作成: {backup_path}")

    def _auto_fix_issues(self, issues: List[StructureIssue]) -> List[str]:
        """自動修正実行"""
        fixes = []

        with open(self.claude_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 簡単な修正のみ実装（安全性重視）
        original_content = content

        # 末尾空白削除
        content = re.sub(r" +$", "", content, flags=re.MULTILINE)
        if content != original_content:
            fixes.append("🧹 末尾空白を自動削除")

        # 空行正規化
        content = re.sub(r"\n{3,}", "\n\n", content)
        if content != original_content:
            fixes.append("📏 空行を正規化")

        if fixes:
            with open(self.claude_md_path, "w", encoding="utf-8") as f:
                f.write(content)

        return fixes

    def generate_dashboard(self) -> Dict:
        """Phase 3: 監視ダッシュボード生成"""
        metrics, issues = self.analyze()

        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "status": self._get_overall_status(metrics, issues),
            "metrics": asdict(metrics),
            "issues": {
                "critical": len([i for i in issues if i.severity == "critical"]),
                "warning": len([i for i in issues if i.severity == "warning"]),
                "info": len([i for i in issues if i.severity == "info"]),
            },
            "trends": self._get_size_trends(),
            "recommendations": self.optimize(),
        }

        return dashboard

    def _get_overall_status(
        self, metrics: CLAUDEmdMetrics, issues: List[StructureIssue]
    ) -> str:
        """総合ステータス判定（段階制限システム対応）"""
        limits = self.config["limits"]

        # クリティカル問題チェック
        critical_issues = [i for i in issues if i.severity == "critical"]
        if critical_issues:
            return "🚨 CRITICAL"

        # クリティカル制限チェック
        if (
            metrics.lines > limits["critical"]["lines"]
            or metrics.bytes > limits["critical"]["bytes"]
        ):
            return "🚨 CRITICAL"

        # 注意制限チェック
        if (
            metrics.lines > limits["caution"]["lines"]
            or metrics.bytes > limits["caution"]["bytes"]
        ):
            return "⚠️ CAUTION"

        # 警告制限チェック
        if (
            metrics.lines > limits["warning"]["lines"]
            or metrics.bytes > limits["warning"]["bytes"]
        ):
            return "⚠️ WARNING"

        # 警告問題チェック
        warning_issues = [i for i in issues if i.severity == "warning"]
        if warning_issues:
            return "⚠️ WARNING"

        # 推奨制限チェック（情報レベル）
        if (
            metrics.lines > limits["recommended_lines"]
            or metrics.bytes > limits["recommended_bytes"]
        ):
            return "💡 INFO"

        return "✅ GOOD"

    def _get_size_trends(self) -> List[Dict]:
        """サイズ推移取得"""
        # 実装簡略化: 単純な履歴管理
        history_file = Path(".claude_md_history.json")
        if not history_file.exists():
            return []

        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)[-10:]  # 最新10件
        except:
            return []

    def save_metrics(self, metrics: CLAUDEmdMetrics):
        """メトリクス履歴保存"""
        history_file = Path(".claude_md_history.json")
        history = []

        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except:
                history = []

        history.append(asdict(metrics))

        # 最新100件のみ保持
        if len(history) > 100:
            history = history[-100:]

        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)


def main():
    """CLI エントリーポイント"""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="CLAUDE.md Management System")
    parser.add_argument(
        "command", choices=["check", "analyze", "optimize", "dashboard"]
    )
    parser.add_argument("--auto-fix", action="store_true", help="自動修正実行")
    parser.add_argument("--output", help="出力ファイル")
    parser.add_argument(
        "--claude-md", default="CLAUDE.md", help="CLAUDE.mdファイルパス"
    )

    args = parser.parse_args()

    manager = CLAUDEmdManager(args.claude_md)

    try:
        if args.command == "check":
            metrics, issues = manager.analyze()

            print(f"📊 CLAUDE.md Statistics:")
            print(f"   Lines: {metrics.lines}")
            print(f"   Bytes: {metrics.bytes} ({metrics.bytes/1024:.1f}KB)")
            print(f"   Sections: {metrics.sections}")
            print(f"   Deep nesting: {metrics.deep_nesting}")

            if issues:
                print(f"\n🔍 Issues Found ({len(issues)}):")
                for issue in issues:
                    severity_icon = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}
                    print(f"   {severity_icon[issue.severity]} {issue.description}")

            manager.save_metrics(metrics)

            # 終了コード判定
            critical = [i for i in issues if i.severity == "critical"]
            sys.exit(1 if critical else 0)

        elif args.command == "analyze":
            metrics, issues = manager.analyze()
            result = {"metrics": asdict(metrics), "issues": [asdict(i) for i in issues]}

            if args.output:
                # tmp/配下にファイル出力
                tmp_dir = Path("tmp")
                tmp_dir.mkdir(exist_ok=True)
                output_path = tmp_dir / Path(args.output).name

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"📄 分析結果を {output_path} に保存しました")
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "optimize":
            suggestions = manager.optimize(auto_fix=args.auto_fix)

            print("💡 最適化提案:")
            for suggestion in suggestions:
                print(f"   - {suggestion}")

            if args.output:
                # tmp/配下にファイル出力
                tmp_dir = Path("tmp")
                tmp_dir.mkdir(exist_ok=True)
                output_path = tmp_dir / Path(args.output).name

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {"suggestions": suggestions}, f, indent=2, ensure_ascii=False
                    )
                print(f"📄 最適化結果を {output_path} に保存しました")

        elif args.command == "dashboard":
            dashboard_data = manager.generate_dashboard()

            print("📊 ダッシュボード生成完了:")
            print(f"   Status: {dashboard_data['status']}")
            print(
                f"   Issues: Critical={dashboard_data['issues']['critical']}, "
                f"Warning={dashboard_data['issues']['warning']}, "
                f"Info={dashboard_data['issues']['info']}"
            )

            if args.output:
                # tmp/配下にファイル出力
                tmp_dir = Path("tmp")
                tmp_dir.mkdir(exist_ok=True)
                output_path = tmp_dir / Path(args.output).name

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
                print(f"📄 ダッシュボードデータを {output_path} に保存しました")

    except FileNotFoundError:
        print(f"❌ {args.claude_md} が見つかりません", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        import traceback

        print(f"❌ エラーが発生しました: {e}", file=sys.stderr)
        print("詳細:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
