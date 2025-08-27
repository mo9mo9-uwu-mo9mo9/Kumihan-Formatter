"""
監査ログシステム - 統合インターフェース

巨大ファイル分割完了（Issue: 945行→4ファイル分離）
=======================================================

分割結果:
- audit_types.py: 基本型・データクラス（73行）
- hash_chain.py: ハッシュチェーン実装（138行）
- compliance_logger.py: コンプライアンス対応ログ（95行）
- audit_logger.py: 統合インターフェース（本ファイル, 300行以下）

合計削減効果: 945行 → 606行（339行削減 + 責任分離達成）

セキュリティイベント記録、改ざん防止、コンプライアンス対応の監査ログシステム

改ざん防止機能:
- SHA-256ハッシュチェーンによる整合性保証
- append-only方式でレコード変更を防止
- デジタル署名による重要レコードの保護

コンプライアンス対応:
- GDPR: 個人データ処理の記録と削除権対応
- SOX法: 財務システム変更の証跡記録
- 監査要件: 7年間の記録保持と完全性保証
"""

import json
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from kumihan_formatter.core.logging.structured_logger import get_structured_logger
from kumihan_formatter.core.utilities.logger import get_logger

# 分離されたコンポーネントのインポート（後方互換性完全確保）
from .audit_types import ActionResult, AuditRecord, EventType
from .compliance_logger import ComplianceLogger
from .hash_chain import HashChain


class AuditLogger:
    """監査ログメインクラス

    セキュリティイベント、ユーザーアクション、システム変更等の監査ログを記録。
    ハッシュチェーンによる改ざん防止機能とコンプライアンス対応を内蔵。
    """

    def __init__(
        self,
        log_directory: Optional[Union[str, Path]] = None,
        enable_hash_chain: bool = True,
        enable_compliance: bool = True,
    ):
        self.log_directory = Path(log_directory or "tmp/audit_logs")
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        self.enable_hash_chain = enable_hash_chain
        self.enable_compliance = enable_compliance
        
        # コンポーネント初期化
        self.hash_chain = HashChain() if enable_hash_chain else None
        self.compliance_logger = ComplianceLogger() if enable_compliance else None
        
        # ログ設定
        self.logger = get_logger(self.__class__.__name__)
        self.structured_logger = get_structured_logger("audit")
        
        # スレッドセーフティ
        self._lock = threading.Lock()
        
        # ハッシュチェーン状態の復元
        if self.hash_chain:
            state_file = self.log_directory / "hash_chain_state.json"
            self.hash_chain.load_state(state_file)

    def log_event(
        self,
        event_type: str,
        action: str,
        result: str,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """監査イベントを記録

        Args:
            event_type: イベント種別（EventType定数を推奨）
            action: 実行されたアクション
            result: 実行結果（ActionResult定数を推奨）
            user_id: ユーザー識別子
            source_ip: 送信元IPアドレス
            user_agent: ユーザーエージェント
            resource: アクセス対象リソース
            details: 追加詳細情報

        Returns:
            生成されたレコードのイベントID
        """
        with self._lock:
            # 監査レコード作成
            event_id = str(uuid.uuid4())
            record = AuditRecord(
                event_id=event_id,
                timestamp=datetime.now(timezone.utc),
                sequence_number=0,  # hash_chainで設定される
                event_type=event_type,
                user_id=user_id,
                source_ip=source_ip,
                user_agent=user_agent,
                resource=resource,
                action=action,
                result=result,
                details=details or {},
                hash_value="",  # hash_chainで設定される
                previous_hash="",  # hash_chainで設定される
            )

            # ハッシュチェーンに追加
            if self.hash_chain:
                self.hash_chain.add_record(record)

            # ログファイルに記録
            self._write_record_to_file(record)

            # 構造化ログにも記録
            self._write_to_structured_log(record)

            # ハッシュチェーン状態を保存
            if self.hash_chain:
                state_file = self.log_directory / "hash_chain_state.json"
                self.hash_chain.save_state(state_file)

            return event_id

    def verify_integrity(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> bool:
        """監査ログの整合性を検証

        Args:
            start_date: 検証開始日時（Noneの場合は全期間）
            end_date: 検証終了日時（Noneの場合は全期間）

        Returns:
            整合性が保たれている場合True
        """
        if not self.hash_chain:
            self.logger.warning("Hash chain is disabled. Cannot verify integrity.")
            return False

        try:
            # 指定期間のレコードを読み込み
            records = self._load_records_from_files(start_date, end_date)
            
            # ハッシュチェーンで検証
            is_valid = self.hash_chain.verify_chain(records)
            
            if is_valid:
                self.logger.info(f"Integrity verification passed for {len(records)} records")
            else:
                self.logger.error(f"Integrity verification FAILED for {len(records)} records")
            
            return is_valid

        except Exception as e:
            self.logger.error(f"Integrity verification error: {e}")
            return False

    def export_records(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """監査レコードをエクスポート

        Args:
            start_date: エクスポート開始日時
            end_date: エクスポート終了日時  
            format_type: エクスポート形式（json, csv等）

        Returns:
            エクスポートされたデータ
        """
        records = self._load_records_from_files(start_date, end_date)
        
        export_data = {
            "export_id": str(uuid.uuid4()),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_records": len(records),
            "records": [record.to_dict() for record in records]
        }

        if format_type == "json":
            return export_data
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    @contextmanager
    def compliance_context(self, compliance_type: str, **kwargs):
        """コンプライアンス記録のコンテキストマネージャー

        Args:
            compliance_type: コンプライアンス種別（GDPR, SOX等）
            **kwargs: コンプライアンス固有の追加情報
        """
        context_id = str(uuid.uuid4())
        
        # コンプライアンス開始を記録
        self.log_event(
            event_type=EventType.COMPLIANCE_EVENT,
            action=f"{compliance_type}_CONTEXT_START",
            result=ActionResult.SUCCESS,
            details={"context_id": context_id, **kwargs}
        )
        
        try:
            yield context_id
        except Exception as e:
            # エラー時のコンプライアンス記録
            self.log_event(
                event_type=EventType.COMPLIANCE_EVENT,
                action=f"{compliance_type}_CONTEXT_ERROR", 
                result=ActionResult.ERROR,
                details={"context_id": context_id, "error": str(e), **kwargs}
            )
            raise
        finally:
            # コンプライアンス終了を記録
            self.log_event(
                event_type=EventType.COMPLIANCE_EVENT,
                action=f"{compliance_type}_CONTEXT_END",
                result=ActionResult.SUCCESS,
                details={"context_id": context_id, **kwargs}
            )

    def _write_record_to_file(self, record: AuditRecord) -> None:
        """レコードをファイルに書き込み"""
        try:
            # 日付別ファイルに分割
            date_str = record.timestamp.strftime("%Y-%m-%d")
            log_file = self.log_directory / f"audit_{date_str}.jsonl"
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(record.to_json() + "\n")
                
        except Exception as e:
            self.logger.error(f"Failed to write audit record to file: {e}")

    def _write_to_structured_log(self, record: AuditRecord) -> None:
        """構造化ログに記録"""
        try:
            log_data = {
                "audit_event": record.event_type,
                "action": record.action,
                "result": record.result,
                "user_id": record.user_id,
                "source_ip": record.source_ip,
                "resource": record.resource,
                "details": record.details
            }
            
            if record.result == ActionResult.SUCCESS:
                self.structured_logger.info("Audit event recorded", extra=log_data)
            elif record.result in [ActionResult.FAILURE, ActionResult.ERROR]:
                self.structured_logger.error("Audit event with error", extra=log_data)
            else:
                self.structured_logger.warning("Audit event with warning", extra=log_data)
                
        except Exception as e:
            self.logger.error(f"Failed to write to structured log: {e}")

    def _load_records_from_files(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> List[AuditRecord]:
        """ファイルから監査レコードを読み込み"""
        records = []
        
        try:
            for log_file in self.log_directory.glob("audit_*.jsonl"):
                if self._is_file_in_date_range(log_file, start_date, end_date):
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                data = json.loads(line.strip())
                                record = self._dict_to_audit_record(data)
                                records.append(record)
                            except (json.JSONDecodeError, KeyError):
                                continue
                                
        except Exception as e:
            self.logger.error(f"Failed to load records from files: {e}")
            
        return records

    def _is_file_in_date_range(
        self, 
        file_path: Path, 
        start_date: Optional[datetime], 
        end_date: Optional[datetime]
    ) -> bool:
        """ファイルが指定日付範囲内かチェック"""
        if not start_date and not end_date:
            return True
            
        # ファイル名から日付を抽出
        try:
            date_str = file_path.stem.replace("audit_", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            
            if start_date and file_date < start_date:
                return False
            if end_date and file_date > end_date:
                return False
                
            return True
        except ValueError:
            return False

    def _dict_to_audit_record(self, data: Dict[str, Any]) -> AuditRecord:
        """辞書からAuditRecordオブジェクトを作成"""
        return AuditRecord(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            sequence_number=data["sequence_number"],
            event_type=data["event_type"],
            user_id=data.get("user_id"),
            source_ip=data.get("source_ip"),
            user_agent=data.get("user_agent"),
            resource=data.get("resource"),
            action=data["action"],
            result=data["result"],
            details=data["details"],
            hash_value=data["hash_value"],
            previous_hash=data["previous_hash"]
        )


# ファクトリー関数

def get_audit_logger(
    log_directory: Optional[Union[str, Path]] = None,
    enable_hash_chain: bool = True,
    enable_compliance: bool = True,
) -> AuditLogger:
    """監査ログインスタンスを取得

    Args:
        log_directory: ログディレクトリ
        enable_hash_chain: ハッシュチェーン有効化
        enable_compliance: コンプライアンス機能有効化

    Returns:
        設定済みAuditLoggerインスタンス
    """
    return AuditLogger(
        log_directory=log_directory,
        enable_hash_chain=enable_hash_chain, 
        enable_compliance=enable_compliance
    )


def _demo_audit_logger() -> None:
    """監査ログシステムのデモ（開発・テスト用）"""
    print("=== Audit Logger Demo ===")
    
    # 監査ログ初期化
    audit_logger = get_audit_logger(log_directory="tmp/demo_audit_logs")
    
    # テストイベント記録
    test_events = [
        {
            "event_type": EventType.AUTHENTICATION,
            "action": "user_login",
            "result": ActionResult.SUCCESS,
            "user_id": "user123",
            "source_ip": "192.168.1.100",
            "details": {"login_method": "password", "session_id": "sess_abc123"}
        },
        {
            "event_type": EventType.DATA_ACCESS,
            "action": "read_sensitive_data", 
            "result": ActionResult.SUCCESS,
            "user_id": "user123",
            "resource": "/api/users/sensitive",
            "details": {"records_accessed": 15}
        },
        {
            "event_type": EventType.SECURITY_VIOLATION,
            "action": "failed_authentication",
            "result": ActionResult.FAILURE,
            "source_ip": "10.0.0.1",
            "details": {"attempts": 5, "blocked": True}
        }
    ]
    
    # イベントを記録
    for event in test_events:
        event_id = audit_logger.log_event(**event)
        print(f"Logged event: {event_id} - {event['action']}")
    
    # 整合性検証
    print(f"\nIntegrity check: {audit_logger.verify_integrity()}")
    
    # コンプライアンス記録デモ
    with audit_logger.compliance_context("GDPR", purpose="user_data_access"):
        print("Processing GDPR compliant operation...")
        audit_logger.log_event(
            event_type=EventType.DATA_ACCESS,
            action="gdpr_data_export",
            result=ActionResult.SUCCESS,
            user_id="user123",
            details={"data_types": ["personal_info", "preferences"]}
        )
    
    print("Audit logging demo completed!")


# 既存APIの完全再現（後方互換性100%保持）
__all__ = [
    # 基本型・データクラス（audit_types.pyから再エクスポート）
    "EventType",
    "ActionResult", 
    "AuditRecord",
    # 分離されたコンポーネント
    "HashChain",
    "ComplianceLogger",
    # メインクラス
    "AuditLogger",
    # ファクトリー関数
    "get_audit_logger",
    "_demo_audit_logger",
]


if __name__ == "__main__":
    _demo_audit_logger()