"""
監査ログシステム - ハッシュチェーン実装

監査ログの改ざん防止のためのハッシュチェーン管理
audit_logger.pyから分離（Issue: 巨大ファイル分割 - 945行→200行程度）
"""

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .audit_types import AuditRecord


class HashChain:
    """ハッシュチェーン管理クラス

    監査ログの改ざん防止のため、各レコードが前のレコードのハッシュを含むチェーン構造を構築
    """

    def __init__(self, initial_hash: str = "genesis"):
        self.current_hash: str = initial_hash
        self.sequence_counter: int = 0
        self._lock = threading.Lock()

    def calculate_hash(self, record: AuditRecord, previous_hash: str) -> str:
        """レコードのSHA-256ハッシュを計算

        Args:
            record: ハッシュ計算対象の監査レコード
            previous_hash: 前のレコードのハッシュ値

        Returns:
            計算されたSHA-256ハッシュ文字列
        """
        # ソルト追加で辞書攻撃・レインボーテーブル攻撃を防止
        salt = "kumihan_audit_salt_2025"

        # ハッシュ対象データ作成（順序を保証するためsort_keys=True）
        hash_data = {
            "event_id": record.event_id,
            "timestamp": record.timestamp.isoformat(),
            "sequence_number": record.sequence_number,
            "event_type": record.event_type,
            "user_id": record.user_id,
            "action": record.action,
            "result": record.result,
            "details": json.dumps(record.details, sort_keys=True),
            "previous_hash": previous_hash,
            "salt": salt,
        }

        # JSON文字列化して正規化
        hash_string = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))

        # SHA-256計算
        return hashlib.sha256(hash_string.encode("utf-8")).hexdigest()

    def add_record(self, record: AuditRecord) -> str:
        """レコードをチェーンに追加し、ハッシュを更新

        Args:
            record: 追加する監査レコード

        Returns:
            計算された新しいハッシュ値
        """
        with self._lock:
            # シーケンス番号を設定
            self.sequence_counter += 1
            record.sequence_number = self.sequence_counter

            # 前のハッシュを設定
            record.previous_hash = self.current_hash

            # ハッシュを計算
            new_hash = self.calculate_hash(record, self.current_hash)
            record.hash_value = new_hash

            # 現在のハッシュを更新
            self.current_hash = new_hash

            return new_hash

    def verify_chain(self, records: List[AuditRecord]) -> bool:
        """ハッシュチェーンの整合性を検証

        Args:
            records: 検証対象の監査レコードリスト

        Returns:
            チェーンが有効な場合True
        """
        if not records:
            return True

        # シーケンス順にソート
        sorted_records = sorted(records, key=lambda r: r.sequence_number)

        # 最初のレコードの前のハッシュをgenesisとして開始
        previous_hash = "genesis"

        for record in sorted_records:
            # 期待されるハッシュを計算
            expected_hash = self.calculate_hash(record, previous_hash)

            # 記録されたハッシュと比較
            if record.hash_value != expected_hash:
                return False

            # 前のハッシュが正しく設定されているか確認
            if record.previous_hash != previous_hash:
                return False

            previous_hash = record.hash_value

        return True

    def save_state(self, file_path: Path) -> None:
        """現在の状態をファイルに保存"""
        with self._lock:
            state_data = {
                "current_hash": self.current_hash,
                "sequence_number": self.sequence_counter,
                "last_update": datetime.now(timezone.utc).isoformat(),
                "total_records": self.sequence_counter,
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)

    def load_state(self, file_path: Path) -> None:
        """ファイルから状態を読み込み"""
        if not file_path.exists():
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                state_data = json.load(f)

            with self._lock:
                self.current_hash = state_data.get("current_hash", "genesis")
                self.sequence_counter = state_data.get("sequence_number", 0)
        except (json.JSONDecodeError, OSError):
            # 状態ファイルが破損している場合はgenesisからやり直し
            pass


__all__ = ["HashChain"]