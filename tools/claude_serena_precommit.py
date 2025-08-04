#!/usr/bin/env python3
"""
Claude Code Serena-Expert Pre-commit Hook
Kumihan-Formatter専用

コミット前にserena-expert使用履歴をチェックし、違反時はコミットを阻止
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class SerenaPrecommitChecker:
    """Serena-Expert使用履歴チェック（Pre-commit）"""
    
    def __init__(self):
        self.project_root = Path(os.getcwd())
        self.usage_log = self.project_root / ".claude-usage.log"
        self.violation_log = self.project_root / ".claude-violations.log"
        
        # 違反パターン定義
        self.forbidden_tools = {
            'Edit', 'MultiEdit', 'Read', 'Write', 'Bash', 'Glob', 'Grep'
        }
        
        self.development_patterns = [
            r'implement|create|build|develop|code|component|function|class|method|api|endpoint|feature',
            r'実装|作成|開発|コンポーネント|機能|クラス|メソッド|API|エンドポイント',
            r'add.*feature|fix.*bug|update.*component|refactor.*code',
            r'追加.*機能|修正.*バグ|更新.*コンポーネント|リファクタ.*コード'
        ]

    def get_recent_commits(self, hours: int = 24) -> List[str]:
        """最近のコミットメッセージを取得"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'log', f'--since={hours} hours ago', '--pretty=format:%s'],
                capture_output=True, text=True, cwd=self.project_root
            )
            return result.stdout.strip().split('\n') if result.stdout else []
        except Exception:
            return []

    def is_development_commit(self, commit_messages: List[str]) -> bool:
        """開発関連コミットかどうかを判定"""
        combined_text = ' '.join(commit_messages).lower()
        
        for pattern in self.development_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return True
        return False

    def check_recent_violations(self, hours: int = 24) -> List[Dict]:
        """最近の違反記録をチェック"""
        violations = []
        
        if not self.violation_log.exists():
            return violations
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with open(self.violation_log, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        violation = json.loads(line.strip())
                        violation_time = datetime.fromisoformat(violation['timestamp'])
                        
                        if violation_time > cutoff_time:
                            violations.append(violation)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        except Exception:
            pass
        
        return violations

    def check_staged_files(self) -> List[str]:
        """ステージされたファイルをチェック"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True, text=True, cwd=self.project_root
            )
            return result.stdout.strip().split('\n') if result.stdout else []
        except Exception:
            return []

    def analyze_file_changes(self, staged_files: List[str]) -> bool:
        """ファイル変更が開発関連かどうかを分析"""
        development_file_patterns = [
            r'\.py$', r'\.js$', r'\.ts$', r'\.jsx$', r'\.tsx$', r'\.java$',
            r'\.cpp$', r'\.c$', r'\.h$', r'\.hpp$', r'\.rs$', r'\.go$',
            r'/src/', r'/lib/', r'/components/', r'/api/', r'/core/',
            r'kumihan_formatter/', r'tests/', r'examples/'
        ]
        
        for file_path in staged_files:
            for pattern in development_file_patterns:
                if re.search(pattern, file_path, re.IGNORECASE):
                    return True
        return False

    def run_precommit_check(self) -> bool:
        """Pre-commitチェック実行"""
        print("🔍 Claude Serena-Expert使用履歴チェック開始...")
        
        # 1. ステージされたファイルチェック
        staged_files = self.check_staged_files()
        if not staged_files or staged_files == ['']:
            print("✅ ステージされたファイルがありません - チェックスキップ")
            return True
        
        print(f"📁 ステージされたファイル数: {len(staged_files)}")
        
        # 2. 開発関連の変更かどうかチェック
        is_dev_change = self.analyze_file_changes(staged_files)
        
        if not is_dev_change:
            print("✅ 非開発ファイルの変更 - serenaチェックスキップ")
            return True
        
        print("🔧 開発関連ファイルの変更を検出")
        
        # 3. 最近のコミットメッセージチェック
        recent_commits = self.get_recent_commits(24)
        is_dev_commit = self.is_development_commit(recent_commits)
        
        # 4. 最近の違反記録チェック
        recent_violations = self.check_recent_violations(24)
        
        # 5. 違反がある場合はコミット阻止
        if recent_violations and is_dev_change:
            self._display_violation_error(recent_violations)
            return False
        
        # 6. 開発作業だがserena使用記録がない場合の警告
        if is_dev_change and not self._has_recent_serena_usage():
            self._display_serena_warning()
            # 警告のみで阻止はしない（ログが存在しない可能性もあるため）
        
        print("✅ Serena-Expert使用履歴チェック完了")
        return True

    def _has_recent_serena_usage(self) -> bool:
        """最近のserena使用記録があるかチェック"""
        if not self.usage_log.exists():
            return False
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        try:
            with open(self.usage_log, 'r', encoding='utf-8') as f:
                for line in reversed(list(f)):
                    if 'serena' in line.lower():
                        # 簡易的なタイムスタンプチェック
                        if any(str(datetime.now().year) in line for line in [line]):
                            return True
        except Exception:
            pass
        
        return False

    def _display_violation_error(self, violations: List[Dict]):
        """違反エラー表示"""
        print("\n" + "="*80)
        print("🚨 CLAUDE.md P7原則違反検出 - コミット阻止 🚨")
        print("="*80)
        print(f"検出された違反数: {len(violations)}")
        
        for i, violation in enumerate(violations[:3], 1):  # 最新3件まで表示
            print(f"\n【違反 {i}】")
            print(f"時刻: {violation.get('timestamp', 'N/A')}")
            print(f"使用ツール: {violation.get('tool_used', 'N/A')}")
            print(f"期待ツール: {violation.get('expected_tool', 'N/A')}")
            print(f"メッセージ: {violation.get('message', 'N/A')}")
        
        print("\n" + "="*80)
        print("【対処方法】")
        print("1. 開発作業では必ずserena-expertツール (mcp__serena__*) を使用")
        print("2. 従来ツール (Edit, Read, Write等) の使用を中止")
        print("3. CLAUDE.md P7原則を再確認")
        print("4. 違反を解決してから再度コミット")
        print("="*80)

    def _display_serena_warning(self):
        """Serena使用推奨警告"""
        print("\n" + "⚠️ "*20)
        print("⚠️  開発作業でのserena-expert使用を推奨")
        print("⚠️  CLAUDE.md P7原則: serena-expert絶対必須")
        print("⚠️ "*20)


def main():
    """メイン実行関数"""
    checker = SerenaPrecommitChecker()
    
    try:
        success = checker.run_precommit_check()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"🚨 Pre-commitチェックエラー: {e}")
        # エラー時はコミットを阻止
        sys.exit(1)


if __name__ == "__main__":
    main()