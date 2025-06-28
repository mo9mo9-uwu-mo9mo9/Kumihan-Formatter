#!/usr/bin/env python3
"""
E2Eテスト期待値自動管理ツール

使用方法:
    # 期待値の自動更新（品質ゲート通過時のみ）
    python dev/tools/e2e_expectation_manager.py --update-if-quality-pass
    
    # 強制的な期待値更新
    python dev/tools/e2e_expectation_manager.py --force-update
    
    # 期待値の検証（変更確認）
    python dev/tools/e2e_expectation_manager.py --validate
    
    # バックアップからの復元
    python dev/tools/e2e_expectation_manager.py --restore-backup=2024-01-15
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import difflib
import hashlib

# 品質ゲートチェッカーをインポート
try:
    from quality_gates import QualityGateChecker
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from quality_gates import QualityGateChecker


@dataclass
class ExpectationFile:
    """期待値ファイル情報"""
    path: Path
    content_hash: str
    last_modified: datetime
    size_bytes: int


@dataclass
class ExpectationUpdate:
    """期待値更新情報"""
    file_path: Path
    old_hash: str
    new_hash: str
    changed: bool
    backup_path: Optional[Path] = None


@dataclass
class ExpectationReport:
    """期待値管理レポート"""
    timestamp: str
    operation: str  # 'update', 'validate', 'restore'
    quality_gate_passed: bool
    total_files: int
    updated_files: int
    unchanged_files: int
    backup_created: bool
    updates: List[ExpectationUpdate]
    summary: str


class E2EExpectationManager:
    """E2Eテスト期待値管理クラス"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.expectations_dir = self.project_root / "dev" / "tests" / "e2e_expected"
        self.backup_dir = self.project_root / "dev" / "tests" / "e2e_backups"
        self.temp_dir = self.project_root / "temp" / "e2e_generation"
        
        # ディレクトリ作成
        self.expectations_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.quality_checker = QualityGateChecker()
    
    def update_expectations_if_quality_pass(self) -> ExpectationReport:
        """品質ゲート通過時のみ期待値を更新"""
        print("🔍 品質ゲートチェックを実行中...")
        
        # 品質ゲートチェック
        gate_report = self.quality_checker.check_quality_gates(self.project_root)
        
        if not gate_report.overall_passed:
            print("❌ 品質ゲートが失敗したため、期待値は更新されません")
            return ExpectationReport(
                timestamp=datetime.now().isoformat(),
                operation="update_conditional",
                quality_gate_passed=False,
                total_files=0,
                updated_files=0,
                unchanged_files=0,
                backup_created=False,
                updates=[],
                summary="品質ゲート失敗により期待値更新をスキップしました"
            )
        
        print("✅ 品質ゲートを通過しました。期待値を更新します...")
        return self.force_update_expectations()
    
    def force_update_expectations(self) -> ExpectationReport:
        """強制的に期待値を更新"""
        print("📝 E2Eテスト期待値の強制更新を開始...")
        
        # バックアップ作成
        backup_path = self._create_backup()
        print(f"💾 既存期待値をバックアップしました: {backup_path}")
        
        # 新しい期待値生成
        updates = self._generate_new_expectations()
        
        # レポート生成
        updated_count = sum(1 for update in updates if update.changed)
        
        report = ExpectationReport(
            timestamp=datetime.now().isoformat(),
            operation="force_update",
            quality_gate_passed=True,
            total_files=len(updates),
            updated_files=updated_count,
            unchanged_files=len(updates) - updated_count,
            backup_created=True,
            updates=updates,
            summary=f"{updated_count}/{len(updates)} ファイルの期待値を更新しました"
        )
        
        print(f"✅ 期待値更新完了: {updated_count}/{len(updates)} ファイル更新")
        return report
    
    def validate_expectations(self) -> ExpectationReport:
        """期待値の検証（変更確認）"""
        print("🔍 期待値の検証を開始...")
        
        current_expectations = self._get_current_expectations()
        generated_expectations = self._generate_expectations_for_validation()
        
        updates = []
        for file_path in current_expectations:
            current_hash = current_expectations[file_path].content_hash
            generated_hash = generated_expectations.get(file_path, {}).get('hash', '')
            
            update = ExpectationUpdate(
                file_path=file_path,
                old_hash=current_hash,
                new_hash=generated_hash,
                changed=current_hash != generated_hash
            )
            updates.append(update)
        
        changed_count = sum(1 for update in updates if update.changed)
        
        report = ExpectationReport(
            timestamp=datetime.now().isoformat(),
            operation="validate",
            quality_gate_passed=True,
            total_files=len(updates),
            updated_files=0,
            unchanged_files=len(updates) - changed_count,
            backup_created=False,
            updates=updates,
            summary=f"{changed_count}/{len(updates)} ファイルに変更が検出されました"
        )
        
        if changed_count > 0:
            print(f"⚠️ {changed_count}個のファイルに変更が検出されました")
        else:
            print("✅ 全ての期待値が最新です")
        
        return report
    
    def restore_backup(self, backup_date: str) -> ExpectationReport:
        """バックアップから期待値を復元"""
        backup_path = self.backup_dir / f"expectations_{backup_date}"
        
        if not backup_path.exists():
            raise FileNotFoundError(f"バックアップが見つかりません: {backup_path}")
        
        print(f"🔄 バックアップから復元中: {backup_path}")
        
        # 現在の期待値をバックアップ（復元前）
        restore_backup_path = self._create_backup(suffix="_before_restore")
        
        # バックアップから復元
        if self.expectations_dir.exists():
            shutil.rmtree(self.expectations_dir)
        shutil.copytree(backup_path, self.expectations_dir)
        
        # 復元されたファイル数を計算
        restored_files = list(self.expectations_dir.rglob("*.html"))
        
        report = ExpectationReport(
            timestamp=datetime.now().isoformat(),
            operation="restore",
            quality_gate_passed=True,
            total_files=len(restored_files),
            updated_files=len(restored_files),
            unchanged_files=0,
            backup_created=True,
            updates=[],
            summary=f"バックアップ {backup_date} から {len(restored_files)} ファイルを復元しました"
        )
        
        print(f"✅ 復元完了: {len(restored_files)} ファイル")
        return report
    
    def _create_backup(self, suffix: str = "") -> Path:
        """現在の期待値をバックアップ"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"expectations_{timestamp}{suffix}"
        backup_path = self.backup_dir / backup_name
        
        if self.expectations_dir.exists():
            shutil.copytree(self.expectations_dir, backup_path)
        
        return backup_path
    
    def _generate_new_expectations(self) -> List[ExpectationUpdate]:
        """新しい期待値を生成"""
        updates = []
        
        # サンプルファイルを取得
        sample_files = self._get_sample_files()
        print(f"📁 {len(sample_files)} 個のサンプルファイルを処理...")
        
        for sample_file in sample_files:
            try:
                update = self._process_sample_file(sample_file)
                updates.append(update)
            except Exception as e:
                print(f"⚠️ ファイル処理エラー {sample_file}: {e}")
                # エラーの場合も記録
                updates.append(ExpectationUpdate(
                    file_path=sample_file,
                    old_hash="",
                    new_hash="",
                    changed=False
                ))
        
        return updates
    
    def _process_sample_file(self, sample_file: Path) -> ExpectationUpdate:
        """個別サンプルファイルを処理"""
        print(f"   処理中: {sample_file.name}")
        
        # 既存の期待値ハッシュを取得
        expected_file = self.expectations_dir / f"{sample_file.stem}.html"
        old_hash = ""
        if expected_file.exists():
            with open(expected_file, 'r', encoding='utf-8') as f:
                old_hash = hashlib.md5(f.read().encode()).hexdigest()
        
        # 新しいHTMLを生成
        output_file = self.temp_dir / f"{sample_file.stem}.html"
        self._run_conversion(sample_file, output_file)
        
        # 新しいハッシュを計算
        new_hash = ""
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                new_hash = hashlib.md5(content.encode()).hexdigest()
            
            # 期待値ファイルにコピー
            shutil.copy2(output_file, expected_file)
        
        return ExpectationUpdate(
            file_path=sample_file,
            old_hash=old_hash,
            new_hash=new_hash,
            changed=old_hash != new_hash
        )
    
    def _run_conversion(self, input_file: Path, output_file: Path):
        """変換を実行"""
        cmd = [
            sys.executable,
            '-m', 'kumihan_formatter.cli',
            str(input_file),
            '--no-preview',
            '-o', str(output_file.parent)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise RuntimeError(f"変換失敗: {result.stderr}")
    
    def _get_sample_files(self) -> List[Path]:
        """サンプルファイルのリストを取得"""
        sample_dirs = [
            self.project_root / "examples",
            self.project_root / "examples" / "templates",
            self.project_root / "examples" / "showcase"
        ]
        
        sample_files = []
        for sample_dir in sample_dirs:
            if sample_dir.exists():
                sample_files.extend(sample_dir.glob("*.txt"))
        
        # エラーサンプルファイルは除外
        sample_files = [f for f in sample_files if "エラーサンプル" not in f.name and "error-" not in f.name]
        
        return sorted(sample_files)
    
    def _get_current_expectations(self) -> Dict[Path, ExpectationFile]:
        """現在の期待値ファイル情報を取得"""
        expectations = {}
        
        for html_file in self.expectations_dir.glob("*.html"):
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            expectation = ExpectationFile(
                path=html_file,
                content_hash=hashlib.md5(content.encode()).hexdigest(),
                last_modified=datetime.fromtimestamp(html_file.stat().st_mtime),
                size_bytes=html_file.stat().st_size
            )
            expectations[html_file] = expectation
        
        return expectations
    
    def _generate_expectations_for_validation(self) -> Dict[Path, Dict[str, str]]:
        """検証用の期待値を一時生成"""
        expectations = {}
        sample_files = self._get_sample_files()
        
        for sample_file in sample_files:
            try:
                output_file = self.temp_dir / f"validation_{sample_file.stem}.html"
                self._run_conversion(sample_file, output_file)
                
                if output_file.exists():
                    with open(output_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    expected_path = self.expectations_dir / f"{sample_file.stem}.html"
                    expectations[expected_path] = {
                        'hash': hashlib.md5(content.encode()).hexdigest(),
                        'content': content
                    }
            except Exception:
                pass  # エラーは無視
        
        return expectations
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """利用可能なバックアップのリストを取得"""
        backups = []
        
        for backup_dir in self.backup_dir.glob("expectations_*"):
            if backup_dir.is_dir():
                # ディレクトリ名から日時を抽出
                timestamp_str = backup_dir.name.replace("expectations_", "").split("_")[0]
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d")
                    
                    # ファイル数を計算
                    file_count = len(list(backup_dir.glob("*.html")))
                    
                    backups.append({
                        'name': backup_dir.name,
                        'date': timestamp.strftime("%Y-%m-%d"),
                        'path': backup_dir,
                        'file_count': file_count,
                        'size_mb': sum(f.stat().st_size for f in backup_dir.rglob("*")) / 1024 / 1024
                    })
                except ValueError:
                    pass  # 日時解析失敗は無視
        
        return sorted(backups, key=lambda x: x['date'], reverse=True)


def format_expectation_report(report: ExpectationReport, format_type: str = 'detailed') -> str:
    """期待値管理レポートのフォーマット"""
    if format_type == 'json':
        # dataclassを辞書に変換（PathオブジェクトをstrIngに変換）
        report_dict = {
            'timestamp': report.timestamp,
            'operation': report.operation,
            'quality_gate_passed': report.quality_gate_passed,
            'total_files': report.total_files,
            'updated_files': report.updated_files,
            'unchanged_files': report.unchanged_files,
            'backup_created': report.backup_created,
            'updates': [
                {
                    'file_path': str(update.file_path),
                    'old_hash': update.old_hash,
                    'new_hash': update.new_hash,
                    'changed': update.changed,
                    'backup_path': str(update.backup_path) if update.backup_path else None
                }
                for update in report.updates
            ],
            'summary': report.summary
        }
        return json.dumps(report_dict, indent=2, ensure_ascii=False)
    
    elif format_type == 'summary':
        operation_names = {
            'update_conditional': '条件付き更新',
            'force_update': '強制更新',
            'validate': '検証',
            'restore': '復元'
        }
        
        operation_name = operation_names.get(report.operation, report.operation)
        
        return f"""
📝 E2Eテスト期待値管理結果
========================
操作: {operation_name}
時刻: {report.timestamp}

📊 結果:
- 処理ファイル数: {report.total_files}
- 更新ファイル数: {report.updated_files}
- 未変更ファイル数: {report.unchanged_files}
- バックアップ作成: {'✅ Yes' if report.backup_created else '❌ No'}

💬 サマリー: {report.summary}
"""
    
    else:  # detailed
        operation_names = {
            'update_conditional': '条件付き期待値更新',
            'force_update': '強制期待値更新',
            'validate': '期待値検証',
            'restore': '期待値復元'
        }
        
        operation_name = operation_names.get(report.operation, report.operation)
        
        # 変更されたファイルの詳細
        changed_files = [update for update in report.updates if update.changed]
        unchanged_files = [update for update in report.updates if not update.changed]
        
        change_details = []
        if changed_files:
            change_details.append("🔄 変更されたファイル:")
            for update in changed_files[:10]:  # 最大10件表示
                file_name = update.file_path.name if hasattr(update.file_path, 'name') else str(update.file_path)
                change_details.append(f"   • {file_name}")
            
            if len(changed_files) > 10:
                change_details.append(f"   ... 他 {len(changed_files) - 10} ファイル")
        
        if unchanged_files and report.operation in ['validate', 'update_conditional', 'force_update']:
            change_details.append(f"\n✅ 未変更ファイル: {len(unchanged_files)} 個")
        
        return f"""
📝 Kumihan-Formatter E2Eテスト期待値管理詳細レポート
================================================
操作: {operation_name}
実行時刻: {report.timestamp}

🎯 実行結果: {'✅ 成功' if report.quality_gate_passed else '❌ 失敗'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 統計情報:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 総ファイル数: {report.total_files}
• 更新ファイル数: {report.updated_files}
• 未変更ファイル数: {report.unchanged_files}
• バックアップ作成: {'✅ Yes' if report.backup_created else '❌ No'}

{chr(10).join(change_details) if change_details else ''}

💬 サマリー:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{report.summary}

{'🌟 期待値管理が正常に完了しました。' if report.quality_gate_passed else '⚠️ 問題が検出されました。詳細を確認してください。'}
"""


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter E2Eテスト期待値自動管理ツール",
        epilog="例: python dev/tools/e2e_expectation_manager.py --update-if-quality-pass"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--update-if-quality-pass',
        action='store_true',
        help='品質ゲート通過時のみ期待値を更新'
    )
    group.add_argument(
        '--force-update',
        action='store_true',
        help='強制的に期待値を更新'
    )
    group.add_argument(
        '--validate',
        action='store_true',
        help='期待値の検証（変更確認）'
    )
    group.add_argument(
        '--restore-backup',
        type=str,
        help='バックアップから復元（日付指定: YYYY-MM-DD）'
    )
    group.add_argument(
        '--list-backups',
        action='store_true',
        help='利用可能なバックアップをリスト表示'
    )
    
    parser.add_argument(
        '--format',
        choices=['detailed', 'summary', 'json'],
        default='detailed',
        help='レポート形式'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='出力ファイルパス'
    )
    
    args = parser.parse_args()
    
    try:
        manager = E2EExpectationManager()
        
        if args.list_backups:
            backups = manager.list_backups()
            print("📦 利用可能なバックアップ:")
            print("=" * 50)
            for backup in backups:
                print(f"📅 {backup['date']} - {backup['file_count']}ファイル ({backup['size_mb']:.1f}MB)")
                print(f"   📁 {backup['name']}")
            return
        
        # 操作実行
        if args.update_if_quality_pass:
            report = manager.update_expectations_if_quality_pass()
        elif args.force_update:
            report = manager.force_update_expectations()
        elif args.validate:
            report = manager.validate_expectations()
        elif args.restore_backup:
            report = manager.restore_backup(args.restore_backup)
        
        # レポート生成・出力
        formatted_report = format_expectation_report(report, args.format)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(formatted_report)
            print(f"📄 レポートを出力しました: {args.output}")
        else:
            print(formatted_report)
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()