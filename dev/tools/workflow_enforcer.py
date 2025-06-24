#!/usr/bin/env python3
"""
ワークフロー強制ツール

Claude Code起動時や作業開始時にGitワークフローの遵守をチェックし、
必要に応じて自動的にブランチ作成を促すツール
"""

import subprocess
import sys
from pathlib import Path
import json
from datetime import datetime

class WorkflowEnforcer:
    """ワークフロー強制クラス"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.warnings = []
        self.errors = []
    
    def get_current_branch(self) -> str:
        """現在のブランチ名を取得"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.project_root,
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"
    
    def get_git_status(self) -> tuple[bool, list]:
        """Gitの作業ディレクトリの状態を取得"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_root,
                capture_output=True, text=True, check=True
            )
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            has_changes = len(lines) > 0
            return has_changes, lines
        except subprocess.CalledProcessError:
            return False, []
    
    def is_main_branch(self, branch_name: str) -> bool:
        """メインブランチかどうかを判定"""
        main_branches = ['main', 'master', 'develop']
        return branch_name in main_branches
    
    def check_workflow_compliance(self) -> dict:
        """ワークフロー遵守状況をチェック"""
        current_branch = self.get_current_branch()
        has_changes, changed_files = self.get_git_status()
        
        status = {
            'current_branch': current_branch,
            'is_main_branch': self.is_main_branch(current_branch),
            'has_uncommitted_changes': has_changes,
            'changed_files': changed_files,
            'compliance_status': 'ok',
            'violations': [],
            'recommendations': []
        }
        
        # メインブランチでの作業チェック
        if status['is_main_branch'] and has_changes:
            status['compliance_status'] = 'violation'
            status['violations'].append({
                'type': 'main_branch_changes',
                'severity': 'high',
                'description': f'{current_branch}ブランチで直接ファイルを変更しています',
                'action_required': True
            })
            status['recommendations'].append({
                'action': 'create_feature_branch',
                'description': '作業用ブランチを作成してください',
                'command': 'git checkout -b feature/作業内容'
            })
        
        # メインブランチにいるが変更がない場合の警告
        elif status['is_main_branch'] and not has_changes:
            status['compliance_status'] = 'warning'
            status['violations'].append({
                'type': 'working_on_main',
                'severity': 'medium',
                'description': f'{current_branch}ブランチで作業を開始しようとしています',
                'action_required': False
            })
            status['recommendations'].append({
                'action': 'create_feature_branch_preemptive',
                'description': '作業前に作業用ブランチを作成することを推奨します',
                'command': 'git checkout -b feature/作業内容'
            })
        
        return status
    
    def suggest_branch_name(self) -> str:
        """作業内容に基づいたブランチ名を提案"""
        timestamp = datetime.now().strftime('%m%d')
        return f'feature/work-{timestamp}'
    
    def create_feature_branch(self, branch_name: str = None) -> bool:
        """作業用ブランチを作成"""
        if not branch_name:
            branch_name = self.suggest_branch_name()
        
        try:
            # 現在の変更をstash
            subprocess.run(['git', 'stash'], cwd=self.project_root, check=False)
            
            # 新しいブランチを作成
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=self.project_root,
                capture_output=True, text=True, check=True
            )
            
            # stashした変更を復元
            subprocess.run(['git', 'stash', 'pop'], cwd=self.project_root, check=False)
            
            print(f"✅ 作業用ブランチ '{branch_name}' を作成しました")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ ブランチ作成に失敗: {e}")
            return False
    
    def display_status_report(self, status: dict) -> None:
        """ワークフロー状況レポートを表示"""
        print("=" * 60)
        print("🔄 Gitワークフロー状況チェック")
        print("=" * 60)
        print(f"現在のブランチ: {status['current_branch']}")
        print(f"未コミット変更: {'あり' if status['has_uncommitted_changes'] else 'なし'}")
        
        if status['changed_files']:
            print("変更ファイル:")
            for file in status['changed_files'][:5]:  # 最初の5ファイルのみ表示
                print(f"  - {file}")
            if len(status['changed_files']) > 5:
                print(f"  ... 他{len(status['changed_files']) - 5}ファイル")
        
        print()
        
        # 違反事項の表示
        if status['violations']:
            for violation in status['violations']:
                severity_icon = "🔴" if violation['severity'] == 'high' else "🟡"
                print(f"{severity_icon} {violation['description']}")
            print()
        
        # 推奨アクションの表示
        if status['recommendations']:
            print("💡 推奨アクション:")
            for rec in status['recommendations']:
                print(f"  - {rec['description']}")
                print(f"    コマンド: {rec['command']}")
            print()
        
        # コンプライアンス状況
        if status['compliance_status'] == 'ok':
            print("✅ ワークフロー: 問題なし")
        elif status['compliance_status'] == 'warning':
            print("🟡 ワークフロー: 注意が必要")
        else:
            print("🔴 ワークフロー: 違反あり - 修正が必要")
    
    def interactive_fix(self, status: dict) -> bool:
        """対話的な修正プロセス"""
        if status['compliance_status'] == 'ok':
            return True
        
        if status['compliance_status'] == 'violation':
            print("\n⚠️  ワークフローに違反しています。修正が必要です。")
            
            # メインブランチでの変更がある場合
            main_violations = [v for v in status['violations'] if v['type'] == 'main_branch_changes']
            if main_violations:
                print("\n🔄 作業用ブランチを作成しますか？")
                response = input("ブランチ名を入力 (Enterでデフォルト): ").strip()
                
                branch_name = response if response else self.suggest_branch_name()
                return self.create_feature_branch(branch_name)
        
        elif status['compliance_status'] == 'warning':
            print("\n💡 事前に作業用ブランチを作成することを推奨します。")
            response = input("作業用ブランチを作成しますか？ (y/n): ").lower().strip()
            
            if response in ['y', 'yes', 'はい']:
                branch_name = input("ブランチ名を入力 (Enterでデフォルト): ").strip()
                branch_name = branch_name if branch_name else self.suggest_branch_name()
                return self.create_feature_branch(branch_name)
        
        return True
    
    def enforce_workflow(self, interactive: bool = True) -> bool:
        """ワークフローを強制チェック・修正"""
        print("🔍 Gitワークフロー状況を確認中...")
        
        status = self.check_workflow_compliance()
        self.display_status_report(status)
        
        if interactive:
            return self.interactive_fix(status)
        else:
            # 非対話モードでは違反があれば失敗
            return status['compliance_status'] != 'violation'

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gitワークフロー強制ツール')
    parser.add_argument('--interactive', action='store_true', default=True,
                       help='対話モードで実行 (default: True)')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false',
                       help='非対話モードで実行')
    parser.add_argument('--project-root', default='.',
                       help='プロジェクトルート (default: .)')
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    enforcer = WorkflowEnforcer(project_root)
    
    success = enforcer.enforce_workflow(interactive=args.interactive)
    
    if not success:
        print("\n❌ ワークフロー違反が修正されませんでした。")
        sys.exit(1)
    else:
        print("\n✅ ワークフロー: 準備完了")
        sys.exit(0)

if __name__ == '__main__':
    main()