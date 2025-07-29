#!/usr/bin/env python3
"""
TDD Session Manager - Issue #640 Phase 2
TDDセッション管理システム

目的: Issue番号からTDDセッションの自動開始・管理
- Issue情報自動取得
- TDDセッション状態管理
- 進捗追跡・レポート生成
"""

import json
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TDDPhase(Enum):
    """TDDフェーズ定義"""

    NOT_STARTED = "not_started"
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"
    COMPLETED = "completed"


@dataclass
class TDDSession:
    """TDDセッション情報"""

    issue_number: str
    issue_title: str
    issue_description: str
    branch_name: str
    start_time: datetime
    current_phase: TDDPhase
    cycles_completed: int
    test_files: List[str]
    implementation_files: List[str]
    phase_history: List[Dict]
    quality_metrics: Dict
    session_id: str


@dataclass
class TDDCycle:
    """TDD個別サイクル情報"""

    cycle_number: int
    red_phase_completed: bool
    green_phase_completed: bool
    refactor_phase_completed: bool
    test_coverage_before: float
    test_coverage_after: float
    complexity_before: float
    complexity_after: float
    start_time: datetime
    end_time: Optional[datetime]


class TDDSessionManager:
    """TDDセッション管理クラス"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.session_file = project_root / ".tdd_session.json"
        self.log_dir = project_root / ".tdd_logs"
        self.log_dir.mkdir(exist_ok=True)

    def start_session(self, issue_number: str) -> TDDSession:
        """TDDセッション開始"""
        logger.info(f"🎯 TDDセッション開始: Issue #{issue_number}")

        # 既存セッションチェック
        if self.session_file.exists():
            existing_session = self.load_session()
            if existing_session:
                logger.warning(
                    f"既存セッションが存在します: Issue #{existing_session.issue_number}"
                )
                # 非対話環境での自動処理
                import sys
                if not sys.stdin.isatty():
                    logger.info("非対話環境: 既存セッションをアーカイブして新セッション開始")
                    self._archive_session(existing_session)
                else:
                    response = input(
                        "既存セッションを終了して新しいセッションを開始しますか? (y/N): "
                    )
                    if response.lower() != "y":
                        logger.info("セッション開始をキャンセルしました")
                        return existing_session
                    else:
                        self._archive_session(existing_session)

        # Issue情報取得
        issue_info = self._fetch_issue_info(issue_number)

        # ブランチ確認・作成
        branch_name = self._ensure_correct_branch(issue_number, issue_info["title"])

        # TDDセッション作成
        session = TDDSession(
            issue_number=issue_number,
            issue_title=issue_info["title"],
            issue_description=issue_info["description"],
            branch_name=branch_name,
            start_time=datetime.now(),
            current_phase=TDDPhase.NOT_STARTED,
            cycles_completed=0,
            test_files=[],
            implementation_files=[],
            phase_history=[],
            quality_metrics={},
            session_id=f"tdd-{issue_number}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        )

        # セッション保存
        self.save_session(session)

        # 初期レポート生成
        self._generate_session_report(session)

        logger.info(f"✅ TDDセッション開始完了: {session.session_id}")
        return session

    def _fetch_issue_info(self, issue_number: str) -> Dict:
        """GitHub Issue情報取得"""
        try:
            # GitHub CLI使用してIssue情報取得
            cmd = [
                "gh",
                "issue",
                "view",
                issue_number,
                "--json",
                "title,body,labels,assignees",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            issue_data = json.loads(result.stdout)

            return {
                "title": issue_data.get("title", f"Issue #{issue_number}"),
                "description": issue_data.get("body", ""),
                "labels": [label["name"] for label in issue_data.get("labels", [])],
                "assignees": [
                    assignee["login"] for assignee in issue_data.get("assignees", [])
                ],
            }

        except subprocess.CalledProcessError as e:
            logger.warning(f"GitHub Issue情報取得失敗: {e}")
            return {
                "title": f"Issue #{issue_number}",
                "description": "Issue情報を自動取得できませんでした。",
                "labels": [],
                "assignees": [],
            }
        except json.JSONDecodeError as e:
            logger.error(f"Issue情報パース失敗: {e}")
            return {
                "title": f"Issue #{issue_number}",
                "description": "",
                "labels": [],
                "assignees": [],
            }

    def _ensure_correct_branch(self, issue_number: str, issue_title: str) -> str:
        """正しいブランチの確認・作成"""
        # 現在のブランチ確認
        result = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, text=True
        )
        current_branch = result.stdout.strip()

        # 期待するブランチ名生成
        safe_title = "".join(
            c for c in issue_title.lower() if c.isalnum() or c in "-_"
        )[:50]
        expected_branch = f"feat/issue-{issue_number}-{safe_title}"

        if current_branch == expected_branch:
            logger.info(f"✅ 正しいブランチにいます: {current_branch}")
            return current_branch

        # ブランチ切り替え・作成
        logger.info(f"🔄 ブランチ切り替え: {current_branch} → {expected_branch}")

        # mainブランチから最新取得
        subprocess.run(["git", "checkout", "main"], check=True)
        subprocess.run(["git", "pull", "origin", "main"], check=True)

        # 新ブランチ作成・切り替え
        try:
            subprocess.run(["git", "checkout", "-b", expected_branch], check=True)
            logger.info(f"✅ 新ブランチ作成完了: {expected_branch}")
        except subprocess.CalledProcessError:
            # ブランチが既に存在する場合は切り替え
            subprocess.run(["git", "checkout", expected_branch], check=True)
            logger.info(f"✅ 既存ブランチに切り替え: {expected_branch}")

        return expected_branch

    def load_session(self) -> Optional[TDDSession]:
        """TDDセッション読み込み"""
        if not self.session_file.exists():
            logger.debug(f"TDDセッションファイルが存在しません: {self.session_file}")
            return None

        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            logger.debug(f"TDDセッションデータ読み込み: {len(data)} fields")

            # 必須フィールドの検証
            required_fields = {"issue_number", "start_time", "current_phase"}
            missing_fields = required_fields - data.keys()
            if missing_fields:
                logger.error(f"必須フィールドが不足: {missing_fields}")
                self._backup_corrupted_session(data)
                return None

            # datetime文字列をdatetimeオブジェクトに変換
            try:
                data["start_time"] = datetime.fromisoformat(data["start_time"])
            except (ValueError, TypeError) as e:
                logger.error(f"start_time形式エラー: {data.get('start_time')} - {e}")
                self._backup_corrupted_session(data)
                return None
                
            # TDDPhase enum変換
            try:
                data["current_phase"] = TDDPhase(data["current_phase"])
            except (ValueError, TypeError) as e:
                logger.error(f"current_phase形式エラー: {data.get('current_phase')} - {e}")
                self._backup_corrupted_session(data)
                return None
            
            # 不要なフィールドを除外（後方互換性のため）
            session_fields = {
                "issue_number", "issue_title", "issue_description", "branch_name",
                "start_time", "current_phase", "cycles_completed", "test_files",
                "implementation_files", "phase_history", "quality_metrics", "session_id"
            }
            filtered_data = {k: v for k, v in data.items() if k in session_fields}
            
            # デフォルト値設定
            defaults = {
                "issue_title": f"Issue #{filtered_data.get('issue_number', 'Unknown')}",
                "issue_description": "",
                "branch_name": f"feat/issue-{filtered_data.get('issue_number', 'unknown')}",
                "cycles_completed": 0,
                "test_files": [],
                "implementation_files": [],
                "phase_history": [],
                "quality_metrics": {},
                "session_id": f"tdd-{filtered_data.get('issue_number', 'unknown')}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            }
            
            for key, default_value in defaults.items():
                if key not in filtered_data:
                    filtered_data[key] = default_value
                    logger.debug(f"デフォルト値設定: {key} = {default_value}")

            session = TDDSession(**filtered_data)
            logger.info(f"✅ TDDセッション読み込み成功: {session.issue_number}")
            return session

        except json.JSONDecodeError as e:
            logger.error(f"JSONパースエラー: {e}")
            self._backup_corrupted_session(f"Invalid JSON: {e}")
            return None
        except FileNotFoundError as e:
            logger.error(f"セッションファイル読み込みエラー: {e}")
            return None
        except TypeError as e:
            logger.error(f"TDDSessionオブジェクト作成エラー: {e}")
            self._backup_corrupted_session(data if 'data' in locals() else {})
            return None
        except Exception as e:
            logger.error(f"予期しないセッション読み込みエラー: {type(e).__name__}: {e}")
            import traceback
            logger.debug(f"スタックトレース: {traceback.format_exc()}")
            self._backup_corrupted_session(data if 'data' in locals() else {})
            return None

    def _backup_corrupted_session(self, corrupted_data):
        """破損したセッションデータをバックアップ"""
        try:
            backup_file = self.session_file.with_suffix('.json.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                if isinstance(corrupted_data, dict):
                    json.dump(corrupted_data, f, indent=2, ensure_ascii=False, default=str)
                else:
                    f.write(str(corrupted_data))
            logger.info(f"🗃️  破損セッションをバックアップ: {backup_file}")
        except Exception as e:
            logger.warning(f"バックアップ作成失敗: {e}")

    def save_session(self, session: TDDSession):
        """TDDセッション保存"""
        try:
            # セッションデータの検証
            if not session.issue_number:
                raise ValueError("issue_numberが設定されていません")
            if not session.start_time:
                raise ValueError("start_timeが設定されていません")
            
            data = asdict(session)
            
            # datetimeオブジェクトを文字列に変換
            try:
                data["start_time"] = session.start_time.isoformat()
            except AttributeError as e:
                logger.error(f"start_time変換エラー: {session.start_time} - {e}")
                raise ValueError(f"無効なstart_time: {session.start_time}")
                
            # enum値を文字列に変換
            try:
                data["current_phase"] = session.current_phase.value
            except AttributeError as e:
                logger.error(f"current_phase変換エラー: {session.current_phase} - {e}")
                raise ValueError(f"無効なcurrent_phase: {session.current_phase}")

            # 一時ファイルに書き込み後、原子的に置換
            temp_file = self.session_file.with_suffix('.json.tmp')
            try:
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # 原子的置換
                temp_file.replace(self.session_file)
                logger.info(f"✅ TDDセッション保存完了: {session.session_id}")
                
            except Exception as e:
                # 一時ファイルの削除
                if temp_file.exists():
                    temp_file.unlink()
                raise e

        except (ValueError, TypeError) as e:
            logger.error(f"セッションデータ検証エラー: {e}")
            raise e
        except OSError as e:
            logger.error(f"ファイル保存エラー: {e}")
            raise e
        except Exception as e:
            logger.error(f"予期しないセッション保存エラー: {type(e).__name__}: {e}")
            import traceback
            logger.debug(f"スタックトレース: {traceback.format_exc()}")
            raise e

    def get_session_status(self) -> Dict:
        """セッション状況取得"""
        session = self.load_session()

        if not session:
            return {"active": False, "message": "アクティブなTDDセッションがありません"}

        # 現在の品質メトリクス取得
        current_metrics = self._get_current_quality_metrics()

        # 進捗計算
        duration = datetime.now() - session.start_time

        status = {
            "active": True,
            "session_id": session.session_id,
            "issue_number": session.issue_number,
            "issue_title": session.issue_title,
            "branch_name": session.branch_name,
            "current_phase": session.current_phase.value,
            "cycles_completed": session.cycles_completed,
            "duration_hours": duration.total_seconds() / 3600,
            "test_files_count": len(session.test_files),
            "implementation_files_count": len(session.implementation_files),
            "current_metrics": current_metrics,
            "phase_history": session.phase_history[-5:],  # 最新5件
        }

        return status

    def _get_current_quality_metrics(self) -> Dict:
        """現在の品質メトリクス取得"""
        try:
            # カバレッジ取得
            coverage_cmd = [
                sys.executable,
                "-m",
                "pytest",
                "--cov=kumihan_formatter",
                "--cov-report=json:temp_coverage.json",
                "--collect-only",
                "-q",
            ]
            subprocess.run(coverage_cmd, capture_output=True, cwd=self.project_root)

            coverage_file = self.project_root / "temp_coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                    coverage_percentage = coverage_data["totals"]["percent_covered"]
                coverage_file.unlink()  # 一時ファイル削除
            else:
                coverage_percentage = 0.0

            # テスト数取得
            test_cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
            result = subprocess.run(
                test_cmd, capture_output=True, text=True, cwd=self.project_root
            )

            test_count = 0
            for line in result.stdout.split("\n"):
                if " tests collected" in line:
                    test_count = int(line.split()[0])
                    break

            return {
                "coverage_percentage": coverage_percentage,
                "test_count": test_count,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.warning(f"品質メトリクス取得失敗: {e}")
            return {
                "coverage_percentage": 0.0,
                "test_count": 0,
                "timestamp": datetime.now().isoformat(),
            }

    def _generate_session_report(self, session: TDDSession):
        """セッションレポート生成"""
        # ログディレクトリが存在することを確保
        self.log_dir.mkdir(exist_ok=True)
        
        report_path = self.log_dir / f"{session.session_id}_report.md"

        report_content = f"""# TDDセッションレポート

## セッション情報
- **Session ID**: {session.session_id}
- **Issue**: #{session.issue_number} - {session.issue_title}
- **ブランチ**: {session.branch_name}
- **開始時刻**: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **現在フェーズ**: {session.current_phase.value}

## Issue詳細
{session.issue_description}

## 進捗状況
- **完了サイクル数**: {session.cycles_completed}
- **テストファイル数**: {len(session.test_files)}
- **実装ファイル数**: {len(session.implementation_files)}

## 次のアクション
1. `make tdd-spec` でテスト仕様作成
2. `make tdd-red` でRed phaseテスト実装
3. TDDサイクル実行

---
*Generated by TDD Session Manager - Issue #640 Phase 2*
"""

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        logger.info(f"📋 セッションレポート生成: {report_path}")

    def _archive_session(self, session: TDDSession):
        """セッションアーカイブ"""
        archive_path = self.log_dir / f"archived_{session.session_id}.json"

        data = asdict(session)
        data["start_time"] = session.start_time.isoformat()
        data["current_phase"] = session.current_phase.value
        data["archived_at"] = datetime.now().isoformat()

        with open(archive_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # アクティブセッションファイル削除
        if self.session_file.exists():
            self.session_file.unlink()

        logger.info(f"📦 セッションアーカイブ完了: {archive_path}")


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="TDD Session Manager")
    parser.add_argument(
        "command", choices=["start", "status", "debug"], help="実行コマンド"
    )
    parser.add_argument("--issue", type=str, help="Issue番号")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    manager = TDDSessionManager(project_root)

    if args.command == "start":
        if not args.issue:
            logger.error("Issue番号が指定されていません: --issue=<number>")
            sys.exit(1)

        session = manager.start_session(args.issue)
        print(f"✅ TDDセッション開始: {session.session_id}")

    elif args.command == "status":
        status = manager.get_session_status()

        if status["active"]:
            print(f"🎯 アクティブセッション: {status['session_id']}")
            print(f"📋 Issue #{status['issue_number']}: {status['issue_title']}")
            print(f"🌿 ブランチ: {status['branch_name']}")
            print(f"⏱️  経過時間: {status['duration_hours']:.1f}時間")
            print(f"🔄 現在フェーズ: {status['current_phase']}")
            print(f"✅ 完了サイクル: {status['cycles_completed']}")
            print(
                f"📊 カバレッジ: {status['current_metrics']['coverage_percentage']:.1f}%"
            )
        else:
            print(status["message"])

    elif args.command == "debug":
        session = manager.load_session()
        if session:
            print(
                json.dumps(asdict(session), indent=2, default=str, ensure_ascii=False)
            )
        else:
            print("デバッグ情報なし: アクティブセッションがありません")


if __name__ == "__main__":
    main()
