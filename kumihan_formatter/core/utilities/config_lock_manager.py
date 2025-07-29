#!/usr/bin/env python3
"""
Config Lock Manager - Issue #643 Medium Priority Issue対応
設定ファイルアクセスの統一排他制御システム

目的: 複数のセキュリティシステムが同時にアクセスする設定ファイルの
      排他制御を統一的に管理
"""

import threading
import time
import json
import os
from pathlib import Path
from typing import Dict, Optional, Any, Union, ContextManager
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

class LockMode(Enum):
    """ロックモード"""
    READ = "read"
    WRITE = "write"
    EXCLUSIVE = "exclusive"

@dataclass
class LockInfo:
    """ロック情報"""
    file_path: Path
    mode: LockMode
    owner_thread: str
    acquired_at: datetime
    expires_at: Optional[datetime]
    operation_description: str

class ConfigLockTimeoutError(Exception):
    """設定ファイルロックタイムアウトエラー"""
    pass

class ConfigLockManager:
    """設定ファイルアクセス統一排他制御マネージャー"""
    
    _instance: Optional['ConfigLockManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'ConfigLockManager':
        """シングルトンパターン実装"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初期化（シングルトンのため初回のみ実行）"""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        
        # ファイルレベルのロック管理
        self._file_locks: Dict[str, threading.RLock] = {}
        self._file_locks_lock = threading.Lock()
        
        # アクティブロック情報
        self._active_locks: Dict[str, LockInfo] = {}
        self._active_locks_lock = threading.Lock()
        
        # 読み取り専用ロックのカウンタ（読み書きロック実装用）
        self._read_lock_counts: Dict[str, int] = {}
        
        # デフォルト設定
        self.default_timeout = 10.0  # 10秒
        self.cleanup_interval = 60.0  # 1分間隔でクリーンアップ
        
        # クリーンアップスレッド
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_expired_locks,
            daemon=True,
            name="ConfigLockCleanup"
        )
        self._cleanup_thread.start()
        
        logger.info("設定ファイル統一排他制御マネージャー初期化完了")
    
    def _get_file_lock(self, file_path: Union[str, Path]) -> threading.RLock:
        """ファイル固有のロックを取得"""
        file_key = str(file_path)
        
        with self._file_locks_lock:
            if file_key not in self._file_locks:
                self._file_locks[file_key] = threading.RLock()
            return self._file_locks[file_key]
    
    @contextmanager
    def acquire_config_lock(
        self,
        file_path: Union[str, Path],
        mode: LockMode = LockMode.READ,
        timeout: Optional[float] = None,
        operation_description: str = "Config file access"
    ) -> ContextManager[None]:
        """設定ファイルロック取得（コンテキストマネージャー）"""
        
        file_path = Path(file_path)
        file_key = str(file_path)
        timeout = timeout or self.default_timeout
        thread_id = threading.current_thread().name
        
        logger.debug(f"ロック取得試行: {file_key} ({mode.value}) by {thread_id}")
        
        # ファイル固有ロック取得
        file_lock = self._get_file_lock(file_path)
        
        acquired = False
        start_time = time.time()
        
        try:
            # タイムアウト付きでロック取得
            if not file_lock.acquire(timeout=timeout):
                raise ConfigLockTimeoutError(
                    f"設定ファイルロックタイムアウト: {file_key} "
                    f"({timeout}秒, {mode.value}モード)"
                )
            
            acquired = True
            
            # 読み書きロック制御
            self._handle_read_write_lock(file_key, mode, timeout - (time.time() - start_time))
            
            # アクティブロック情報記録
            expires_at = datetime.now() + timedelta(seconds=timeout)
            lock_info = LockInfo(
                file_path=file_path,
                mode=mode,
                owner_thread=thread_id,
                acquired_at=datetime.now(),
                expires_at=expires_at,
                operation_description=operation_description
            )
            
            with self._active_locks_lock:
                self._active_locks[f"{file_key}_{thread_id}"] = lock_info
            
            logger.debug(f"ロック取得成功: {file_key} ({mode.value}) by {thread_id}")
            
            yield
            
        finally:
            if acquired:
                try:
                    # 読み書きロック解除
                    self._release_read_write_lock(file_key, mode)
                    
                    # アクティブロック情報削除
                    with self._active_locks_lock:
                        self._active_locks.pop(f"{file_key}_{thread_id}", None)
                    
                    # ファイル固有ロック解除
                    file_lock.release()
                    
                    logger.debug(f"ロック解除完了: {file_key} ({mode.value}) by {thread_id}")
                    
                except Exception as e:
                    logger.error(f"ロック解除エラー: {file_key} - {e}")
    
    def _handle_read_write_lock(self, file_key: str, mode: LockMode, remaining_timeout: float):
        """読み書きロック制御"""
        if mode == LockMode.READ:
            # 読み取りロック: 他の読み取りと共存可能
            with self._active_locks_lock:
                self._read_lock_counts[file_key] = self._read_lock_counts.get(file_key, 0) + 1
                
        elif mode in [LockMode.WRITE, LockMode.EXCLUSIVE]:
            # 書き込み/排他ロック: 他のアクセスを待機
            start_wait = time.time()
            
            while True:
                with self._active_locks_lock:
                    # 現在のアクティブロックをチェック
                    active_locks = [
                        lock for lock in self._active_locks.values()
                        if str(lock.file_path) == file_key and 
                           lock.owner_thread != threading.current_thread().name
                    ]
                    
                    if not active_locks and self._read_lock_counts.get(file_key, 0) == 0:
                        break
                
                if time.time() - start_wait > remaining_timeout:
                    raise ConfigLockTimeoutError(
                        f"書き込みロック待機タイムアウト: {file_key}"
                    )
                
                time.sleep(0.01)  # 10ms待機
    
    def _release_read_write_lock(self, file_key: str, mode: LockMode):
        """読み書きロック解除"""
        if mode == LockMode.READ:
            with self._active_locks_lock:
                if file_key in self._read_lock_counts:
                    self._read_lock_counts[file_key] = max(0, self._read_lock_counts[file_key] - 1)
                    if self._read_lock_counts[file_key] == 0:
                        del self._read_lock_counts[file_key]
    
    def read_config_safe(
        self,
        file_path: Union[str, Path],
        timeout: Optional[float] = None,
        default: Any = None
    ) -> Any:
        """安全な設定ファイル読み取り"""
        
        file_path = Path(file_path)
        
        with self.acquire_config_lock(
            file_path,
            LockMode.READ,
            timeout,
            f"読み取り: {file_path.name}"
        ):
            try:
                if not file_path.exists():
                    logger.warning(f"設定ファイルが存在しません: {file_path}")
                    return default
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.suffix.lower() == '.json':
                        return json.load(f)
                    else:
                        return f.read()
                        
            except Exception as e:
                logger.error(f"設定ファイル読み取りエラー: {file_path} - {e}")
                return default
    
    def write_config_safe(
        self,
        file_path: Union[str, Path],
        data: Any,
        timeout: Optional[float] = None,
        backup: bool = True,
        atomic: bool = True
    ) -> bool:
        """安全な設定ファイル書き込み"""
        
        file_path = Path(file_path)
        
        with self.acquire_config_lock(
            file_path,
            LockMode.WRITE,
            timeout,
            f"書き込み: {file_path.name}"
        ):
            try:
                # ディレクトリ作成
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # バックアップ作成
                if backup and file_path.exists():
                    backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                    import shutil
                    shutil.copy2(file_path, backup_path)
                    logger.debug(f"バックアップ作成: {backup_path}")
                
                # アトミック書き込み
                if atomic:
                    temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
                    
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        if isinstance(data, (dict, list)):
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        else:
                            f.write(str(data))
                    
                    # アトミック移動
                    temp_path.replace(file_path)
                else:
                    # 直接書き込み
                    with open(file_path, 'w', encoding='utf-8') as f:
                        if isinstance(data, (dict, list)):
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        else:
                            f.write(str(data))
                
                logger.debug(f"設定ファイル書き込み完了: {file_path}")
                return True
                
            except Exception as e:
                logger.error(f"設定ファイル書き込みエラー: {file_path} - {e}")
                return False
    
    def get_lock_status(self) -> Dict[str, Any]:
        """現在のロック状況取得"""
        with self._active_locks_lock:
            status = {
                "active_locks": len(self._active_locks),
                "read_locks": sum(self._read_lock_counts.values()),
                "lock_details": []
            }
            
            for lock_key, lock_info in self._active_locks.items():
                status["lock_details"].append({
                    "file": str(lock_info.file_path),
                    "mode": lock_info.mode.value,
                    "owner": lock_info.owner_thread,
                    "acquired_at": lock_info.acquired_at.isoformat(),
                    "expires_at": lock_info.expires_at.isoformat() if lock_info.expires_at else None,
                    "operation": lock_info.operation_description
                })
            
            return status
    
    def force_unlock_file(self, file_path: Union[str, Path]) -> int:
        """強制的にファイルのロックを解除"""
        file_key = str(file_path)
        unlocked_count = 0
        
        with self._active_locks_lock:
            # 該当ファイルのアクティブロックを削除
            keys_to_remove = [
                key for key, lock_info in self._active_locks.items()
                if str(lock_info.file_path) == file_key
            ]
            
            for key in keys_to_remove:
                del self._active_locks[key]
                unlocked_count += 1
            
            # 読み取りロックカウンターもリセット
            if file_key in self._read_lock_counts:
                del self._read_lock_counts[file_key]
        
        logger.warning(f"強制ロック解除: {file_path} ({unlocked_count}個のロック)")
        return unlocked_count
    
    def _cleanup_expired_locks(self):
        """期限切れロックのクリーンアップ（バックグラウンドタスク）"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                
                now = datetime.now()
                expired_locks = []
                
                with self._active_locks_lock:
                    for lock_key, lock_info in list(self._active_locks.items()):
                        if (lock_info.expires_at and 
                            now > lock_info.expires_at):
                            expired_locks.append(lock_key)
                    
                    for lock_key in expired_locks:
                        lock_info = self._active_locks.pop(lock_key)
                        file_key = str(lock_info.file_path)
                        
                        # 読み取りロックカウンターも調整
                        if lock_info.mode == LockMode.READ and file_key in self._read_lock_counts:
                            self._read_lock_counts[file_key] = max(0, self._read_lock_counts[file_key] - 1)
                            if self._read_lock_counts[file_key] == 0:
                                del self._read_lock_counts[file_key]
                
                if expired_locks:
                    logger.info(f"期限切れロッククリーンアップ: {len(expired_locks)}個")
                    
            except Exception as e:
                logger.error(f"ロッククリーンアップエラー: {e}")

# グローバルインスタンス
_global_config_lock_manager: Optional[ConfigLockManager] = None

def get_config_lock_manager() -> ConfigLockManager:
    """グローバル設定ロックマネージャー取得"""
    global _global_config_lock_manager
    if _global_config_lock_manager is None:
        _global_config_lock_manager = ConfigLockManager()
    return _global_config_lock_manager

# 便利な関数群
def safe_read_config(file_path: Union[str, Path], default: Any = None, timeout: Optional[float] = None) -> Any:
    """安全な設定ファイル読み取り（関数版）"""
    return get_config_lock_manager().read_config_safe(file_path, timeout, default)

def safe_write_config(
    file_path: Union[str, Path],
    data: Any,
    timeout: Optional[float] = None,
    backup: bool = True,
    atomic: bool = True
) -> bool:
    """安全な設定ファイル書き込み（関数版）"""
    return get_config_lock_manager().write_config_safe(file_path, data, timeout, backup, atomic)

@contextmanager
def config_lock(
    file_path: Union[str, Path],
    mode: LockMode = LockMode.READ,
    timeout: Optional[float] = None,
    operation_description: str = "Config access"
) -> ContextManager[None]:
    """設定ファイルロック（関数版コンテキストマネージャー）"""
    with get_config_lock_manager().acquire_config_lock(file_path, mode, timeout, operation_description):
        yield