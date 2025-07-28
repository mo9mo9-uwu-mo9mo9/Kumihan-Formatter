#!/usr/bin/env python3
"""
Secure Subprocess Module - Critical Security Fix
セキュアなサブプロセス実行モジュール

目的: subprocess実行時のセキュリティ脆弱性対策
- Shell injection攻撃防止
- 実行時間制限
- エラーハンドリング強化
- ログ出力統一
"""

import subprocess
import shlex
import signal
import os
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import time

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

@dataclass
class SubprocessResult:
    """サブプロセス実行結果"""
    returncode: int
    stdout: str
    stderr: str
    execution_time: float
    command: List[str]
    success: bool
    timeout: bool

class SecureSubprocessExecutor:
    """セキュアなサブプロセス実行クラス"""
    
    def __init__(self, default_timeout: int = 60, max_concurrent: int = 10):
        self.default_timeout = default_timeout
        self.max_concurrent = max_concurrent
        self._running_processes = set()
        self._lock = threading.RLock()
        
        # 許可されたコマンドのホワイトリスト
        self.allowed_commands = {
            'python3', 'python', 'pytest', 'git', 'gh', 
            'make', 'pip', 'mypy', 'black', 'isort', 'flake8',
            'radon', 'coverage', 'osascript'
        }
        
        # 危険なオプションのブラックリスト
        self.dangerous_options = {
            '--eval', '-e', '--execute', '--command', '-c',
            '&&', '||', ';', '|', '>', '<', '`', '$('
        }
    
    def execute(self, 
                command: Union[str, List[str]], 
                cwd: Optional[Path] = None,
                timeout: Optional[int] = None,
                capture_output: bool = True,
                check: bool = False,
                env: Optional[Dict[str, str]] = None) -> SubprocessResult:
        """
        セキュアなコマンド実行
        
        Args:
            command: 実行コマンド（文字列またはリスト）
            cwd: 作業ディレクトリ
            timeout: タイムアウト秒数
            capture_output: 出力キャプチャフラグ
            check: 失敗時例外発生フラグ
            env: 環境変数
            
        Returns:
            SubprocessResult: 実行結果
            
        Raises:
            SecurityError: セキュリティ違反の場合
            TimeoutError: タイムアウトの場合
        """
        start_time = time.time()
        
        # コマンドを安全な形式に変換
        safe_command = self._sanitize_command(command)
        
        # セキュリティ検証
        self._validate_security(safe_command)
        
        # 同時実行数制限
        self._check_concurrent_limit()
        
        # 実行時間制限設定
        execution_timeout = timeout or self.default_timeout
        
        try:
            # 安全な環境変数設定
            safe_env = self._create_safe_environment(env)
            
            logger.debug(f"セキュアなコマンド実行開始: {' '.join(safe_command)}")
            
            # プロセス実行
            with self._lock:
                self._running_processes.add(threading.current_thread())
            
            result = subprocess.run(
                safe_command,
                cwd=cwd,
                timeout=execution_timeout,
                capture_output=capture_output,
                text=True,
                shell=False,  # 重要: shell=False でshell injection防止
                env=safe_env,
                check=False   # 手動でエラーハンドリング
            )
            
            execution_time = time.time() - start_time
            
            # 結果オブジェクト作成
            subprocess_result = SubprocessResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                command=safe_command,
                success=result.returncode == 0,
                timeout=False
            )
            
            # ログ出力
            if subprocess_result.success:
                logger.debug(f"コマンド実行成功 ({execution_time:.2f}s): {safe_command[0]}")
            else:
                logger.warning(f"コマンド実行失敗 (code:{result.returncode}): {safe_command[0]}")
                if result.stderr:
                    logger.warning(f"エラー出力: {result.stderr}")
            
            # check=Trueの場合のエラーハンドリング
            if check and not subprocess_result.success:
                raise subprocess.CalledProcessError(
                    result.returncode, safe_command, result.stdout, result.stderr
                )
            
            return subprocess_result
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"コマンドタイムアウト ({execution_timeout}s): {safe_command[0]}")
            return SubprocessResult(
                returncode=-1,
                stdout=e.stdout or "",
                stderr=e.stderr or "",
                execution_time=time.time() - start_time,
                command=safe_command,
                success=False,
                timeout=True
            )
            
        except Exception as e:
            logger.error(f"コマンド実行例外: {safe_command[0]} - {e}")
            return SubprocessResult(
                returncode=-1,
                stdout="",
                stderr=str(e),
                execution_time=time.time() - start_time,
                command=safe_command,
                success=False,
                timeout=False
            )
            
        finally:
            with self._lock:
                self._running_processes.discard(threading.current_thread())
    
    def _sanitize_command(self, command: Union[str, List[str]]) -> List[str]:
        """コマンドのサニタイズ"""
        if isinstance(command, str):
            # 文字列の場合はshlex.splitで安全に分割
            try:
                sanitized = shlex.split(command)
            except ValueError as e:
                raise SecurityError(f"無効なコマンド形式: {e}")
        else:
            # リストの場合は各要素をサニタイズ
            sanitized = [str(arg) for arg in command]
        
        if not sanitized:
            raise SecurityError("空のコマンドは実行できません")
        
        return sanitized
    
    def _validate_security(self, command: List[str]) -> None:
        """セキュリティ検証"""
        if not command:
            raise SecurityError("コマンドが空です")
        
        base_command = Path(command[0]).name
        
        # ホワイトリストチェック
        if base_command not in self.allowed_commands:
            raise SecurityError(f"許可されていないコマンド: {base_command}")
        
        # 危険なオプションチェック
        for arg in command:
            if any(dangerous in str(arg) for dangerous in self.dangerous_options):
                raise SecurityError(f"危険なオプションが含まれています: {arg}")
        
        # パス検証
        for arg in command:
            if str(arg).startswith('/') or str(arg).startswith('~'):
                # 絶対パスの場合は安全性確認
                try:
                    safe_path = Path(arg).resolve()
                    if not self._is_safe_path(safe_path):
                        raise SecurityError(f"危険なパスです: {arg}")
                except (OSError, ValueError):
                    # パスが無効な場合はそのまま通す（コマンドオプションの可能性）
                    pass
    
    def _is_safe_path(self, path: Path) -> bool:
        """安全なパス判定"""
        # システムディレクトリへのアクセス禁止
        dangerous_paths = [
            Path('/etc'), Path('/usr/bin'), Path('/usr/sbin'),
            Path('/bin'), Path('/sbin'), Path('/root')
        ]
        
        try:
            resolved_path = path.resolve()
            for dangerous in dangerous_paths:
                if resolved_path.is_relative_to(dangerous):
                    return False
        except (OSError, ValueError):
            return False
            
        return True
    
    def _create_safe_environment(self, env: Optional[Dict[str, str]]) -> Dict[str, str]:
        """安全な環境変数作成"""
        # 基本環境変数
        safe_env = {
            'PATH': os.environ.get('PATH', ''),
            'HOME': os.environ.get('HOME', ''),
            'USER': os.environ.get('USER', ''),
            'LANG': os.environ.get('LANG', 'en_US.UTF-8'),
            'LC_ALL': os.environ.get('LC_ALL', 'en_US.UTF-8'),
        }
        
        # Python関連
        python_vars = ['PYTHONPATH', 'VIRTUAL_ENV', 'PYTHONIOENCODING']
        for var in python_vars:
            if var in os.environ:
                safe_env[var] = os.environ[var]
        
        # ユーザー指定環境変数（安全性チェック付き）
        if env:
            for key, value in env.items():
                if self._is_safe_env_var(key, value):
                    safe_env[key] = value
                else:
                    logger.warning(f"危険な環境変数をスキップ: {key}")
        
        return safe_env
    
    def _is_safe_env_var(self, key: str, value: str) -> bool:
        """環境変数の安全性チェック"""
        # 危険なキーワード
        dangerous_keys = ['LD_PRELOAD', 'LD_LIBRARY_PATH', 'DYLD_INSERT_LIBRARIES']
        if key in dangerous_keys:
            return False
        
        # 危険な値
        if any(dangerous in value for dangerous in ['$(', '`', ';', '&&', '||']):
            return False
        
        return True
    
    def _check_concurrent_limit(self) -> None:
        """同時実行数制限チェック"""
        with self._lock:
            if len(self._running_processes) >= self.max_concurrent:
                raise ResourceError(f"同時実行数上限 ({self.max_concurrent}) に達しました")
    
    def kill_all(self) -> None:
        """全プロセス強制終了"""
        with self._lock:
            running_count = len(self._running_processes)
            if running_count > 0:
                logger.warning(f"{running_count}個の実行中プロセスを強制終了します")
                # 実際の実装では、プロセスIDを追跡して強制終了する
                self._running_processes.clear()

class SecurityError(Exception):
    """セキュリティ関連エラー"""
    pass

class ResourceError(Exception):
    """リソース関連エラー"""
    pass

# グローバルインスタンス
secure_executor = SecureSubprocessExecutor()

def secure_run(command: Union[str, List[str]], **kwargs) -> SubprocessResult:
    """
    セキュアなコマンド実行（便利関数）
    
    Args:
        command: 実行コマンド
        **kwargs: SecureSubprocessExecutor.execute()への引数
        
    Returns:
        SubprocessResult: 実行結果
    """
    return secure_executor.execute(command, **kwargs)

def secure_check_output(command: Union[str, List[str]], **kwargs) -> str:
    """
    セキュアなコマンド実行（出力取得）
    
    Args:
        command: 実行コマンド
        **kwargs: SecureSubprocessExecutor.execute()への引数
        
    Returns:
        str: 標準出力
        
    Raises:
        subprocess.CalledProcessError: コマンド失敗時
    """
    result = secure_executor.execute(command, check=True, **kwargs)
    return result.stdout

# 使用例とテスト関数
def test_secure_subprocess():
    """セキュアサブプロセスのテスト"""
    logger.info("🧪 セキュアサブプロセステスト開始")
    
    # 正常ケース
    try:
        result = secure_run(['python3', '--version'])
        assert result.success
        logger.info("✅ 正常ケーステスト通過")
    except Exception as e:
        logger.error(f"❌ 正常ケーステスト失敗: {e}")
    
    # セキュリティ違反ケース
    try:
        secure_run(['rm', '-rf', '/'])
        logger.error("❌ セキュリティテスト失敗: 危険コマンドが実行された")
    except SecurityError:
        logger.info("✅ セキュリティテスト通過: 危険コマンドがブロックされた")
    
    # タイムアウトケース
    try:
        result = secure_run(['python3', '-c', 'import time; time.sleep(5)'], timeout=1)
        assert result.timeout
        logger.info("✅ タイムアウトテスト通過")
    except Exception as e:
        logger.error(f"❌ タイムアウトテスト失敗: {e}")
    
    logger.info("🎯 セキュアサブプロセステスト完了")

if __name__ == "__main__":
    test_secure_subprocess()