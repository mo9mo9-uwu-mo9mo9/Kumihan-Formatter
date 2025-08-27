"""
監査ログシステム - 基本型・データクラス定義

監査イベント種別、操作結果、監査レコードデータクラス群
audit_logger.pyから分離（Issue: 巨大ファイル分割 - 945行→200行程度）
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional


class EventType:
    """監査イベント種別定数"""

    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    DATA_ACCESS = "DATA_ACCESS"
    SYSTEM_CHANGE = "SYSTEM_CHANGE"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    COMPLIANCE_EVENT = "COMPLIANCE_EVENT"
    USER_ACTION = "USER_ACTION"
    API_CALL = "API_CALL"
    FILE_ACCESS = "FILE_ACCESS"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"


class ActionResult:
    """操作結果定数"""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ERROR = "ERROR"
    DENIED = "DENIED"
    TIMEOUT = "TIMEOUT"


@dataclass
class AuditRecord:
    """監査レコードのデータクラス

    セキュリティイベント、アクセス、システム変更等の監査情報を構造化
    """

    event_id: str
    timestamp: datetime
    sequence_number: int
    event_type: str
    user_id: Optional[str]
    source_ip: Optional[str]
    user_agent: Optional[str]
    resource: Optional[str]
    action: str
    result: str
    details: Dict[str, Any]
    hash_value: str
    previous_hash: str

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        # datetimeをISO形式に変換
        data["timestamp"] = self.timestamp.isoformat()
        return data

    def to_json(self) -> str:
        """JSON形式に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"))


__all__ = ["EventType", "ActionResult", "AuditRecord"]