#!/usr/bin/env python3
"""
TDD System Base - Code Duplication Fix
TDDシステム共通基盤クラス

目的: コード重複解消と統一インターフェース提供
- 共通設定管理
- 統一ログ出力
- セキュアなサブプロセス実行
- リソース管理統合
- エラーハンドリング標準化
"""

import json
import os
import signal
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from contextlib import contextmanager

from kumihan_formatter.core.utilities.logger import get_logger
from scripts.secure_subprocess import secure_run, SecurityError, SubprocessResult
from scripts.resource_manager import memory_manager, memory_tracking
from scripts.performance_optimizer import get_performance_optimizer, cached

logger = get_logger(__name__)

@dataclass
class TDDSystemConfig:
    """TDDシステム共通設定"""
    project_root: Path
    log_level: str = "INFO"
    enable_performance_optimization: bool = True
    enable_memory_monitoring: bool = True
    enable_security_checks: bool = True
    max_concurrent_operations: int = 10
    default_timeout: int = 60
    cache_enabled: bool = True
    
    # 品質基準
    coverage_thresholds: Dict[str, float] = None
    complexity_limits: Dict[str, float] = None
    
    def __post_init__(self):
        if self.coverage_thresholds is None:
            self.coverage_thresholds = {
                "critical": 95.0,
                "important": 85.0,
                "supportive": 70.0,
                "special": 50.0
            }
        
        if self.complexity_limits is None:
            self.complexity_limits = {
                "critical": 10.0,
                "important": 15.0,
                "supportive": 20.0,
                "special": 25.0
            }

class TDDSystemError(Exception):
    """TDDシステム基底例外"""
    pass

class TDDOperationError(TDDSystemError):
    """TDD操作エラー"""
    pass

class TDDValidationError(TDDSystemError):
    """TDD検証エラー"""
    pass

class TDDSystemBase(ABC):
    """TDDシステム共通基盤クラス"""
    
    def __init__(self, config: TDDSystemConfig):
        self.config = config
        self.project_root = config.project_root
        self.logger = get_logger(self.__class__.__name__)
        
        # システム状態
        self.initialized = False
        self.running = False
        self._shutdown_callbacks = []
        self._cleanup_resources = set()
        
        # スレッド安全性
        self._lock = threading.RLock()
        self._operation_semaphore = threading.Semaphore(config.max_concurrent_operations)
        
        # システム統合
        self._setup_integrations()
        
        # シグナルハンドラー設定
        self._setup_signal_handlers()
    
    def _setup_integrations(self):
        """システム統合設定"""
        # パフォーマンス最適化
        if self.config.enable_performance_optimization:
            from scripts.performance_optimizer import init_performance_optimizer
            self.performance_optimizer = init_performance_optimizer(self.project_root)
        else:
            self.performance_optimizer = None
        
        # メモリ監視
        if self.config.enable_memory_monitoring:
            memory_manager.register_cleanup_callback(
                self.__class__.__name__, self._memory_cleanup_callback
            )
    
    def _setup_signal_handlers(self):
        """シグナルハンドラー設定"""
        def signal_handler(signum, frame):
            self.logger.info(f"シグナル {signum} 受信。安全にシャットダウン中...")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    @abstractmethod
    def initialize(self) -> bool:
        """システム初期化（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def execute_main_operation(self) -> Any:
        """メイン操作実行（サブクラスで実装）"""
        pass
    
    def run(self) -> Any:
        """システム実行"""
        try:
            # 初期化
            if not self.initialize():
                raise TDDSystemError("システム初期化に失敗しました")
            
            self.initialized = True
            self.running = True
            
            self.logger.info(f"🚀 {self.__class__.__name__} 開始")
            
            # メイン操作実行
            with self._operation_context():
                result = self.execute_main_operation()
            
            self.logger.info(f"✅ {self.__class__.__name__} 完了")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ {self.__class__.__name__} 実行エラー: {e}")
            raise TDDOperationError(f"システム実行失敗: {e}") from e
        
        finally:
            self.shutdown()
    
    @contextmanager
    def _operation_context(self):
        """操作コンテキスト"""
        with self._operation_semaphore:
            operation_id = f"{self.__class__.__name__}_{int(time.time())}"
            
            # リソース追跡開始
            if self.config.enable_memory_monitoring:
                with memory_tracking(operation_id, self):
                    yield
            else:
                yield
    
    def safe_subprocess_run(self, 
                           command: Union[str, List[str]], 
                           timeout: Optional[int] = None,
                           **kwargs) -> SubprocessResult:
        """安全なサブプロセス実行"""
        if not self.config.enable_security_checks:
            # セキュリティチェック無効時は通常のsubprocess使用
            import subprocess
            result = subprocess.run(command, capture_output=True, text=True, **kwargs)
            return SubprocessResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=0,
                command=command if isinstance(command, list) else [command],
                success=result.returncode == 0,
                timeout=False
            )
        
        # セキュアなサブプロセス実行
        return secure_run(
            command, 
            timeout=timeout or self.config.default_timeout,
            cwd=self.project_root,
            **kwargs
        )
    
    @cached(ttl_seconds=300)  # 5分キャッシュ
    def get_project_info(self) -> Dict[str, Any]:
        """プロジェクト情報取得（キャッシュ付き）"""
        try:
            info = {
                "project_root": str(self.project_root),
                "git_branch": self._get_git_branch(),
                "git_commit": self._get_git_commit(),
                "python_version": self._get_python_version(),
                "timestamp": datetime.now().isoformat()
            }
            
            # pyproject.toml情報
            pyproject_file = self.project_root / "pyproject.toml"
            if pyproject_file.exists():
                info["has_pyproject"] = True
                # プロジェクト名やバージョン情報を読み取り可能
            
            return info
            
        except Exception as e:
            self.logger.warning(f"プロジェクト情報取得エラー: {e}")
            return {"error": str(e)}
    
    def _get_git_branch(self) -> str:
        """現在のGitブランチ取得"""
        try:
            result = self.safe_subprocess_run(["git", "branch", "--show-current"])
            return result.stdout.strip() if result.success else "unknown"
        except:
            return "unknown"
    
    def _get_git_commit(self) -> str:
        """現在のGitコミットハッシュ取得"""
        try:
            result = self.safe_subprocess_run(["git", "rev-parse", "HEAD"])
            return result.stdout.strip()[:8] if result.success else "unknown"
        except:
            return "unknown"
    
    def _get_python_version(self) -> str:
        """Pythonバージョン取得"""
        try:
            result = self.safe_subprocess_run(["python3", "--version"])
            return result.stdout.strip() if result.success else "unknown"
        except:
            return "unknown"
    
    def validate_preconditions(self) -> List[str]:
        """事前条件検証"""
        issues = []
        
        # プロジェクトルート存在確認
        if not self.project_root.exists():
            issues.append(f"プロジェクトルートが存在しません: {self.project_root}")
        
        # Git リポジトリ確認
        git_dir = self.project_root / ".git"
        if not git_dir.exists():
            issues.append("Gitリポジトリではありません")
        
        # Python実行可能確認
        try:
            result = self.safe_subprocess_run(["python3", "--version"], timeout=5)
            if not result.success:
                issues.append("Python3が実行できません")
        except:
            issues.append("Python3コマンドが見つかりません")
        
        # 必要なディレクトリ作成
        required_dirs = [
            self.project_root / ".tdd_logs",
            self.project_root / ".quality_data",
            self.project_root / "scripts"
        ]
        
        for dir_path in required_dirs:
            try:
                dir_path.mkdir(exist_ok=True)
            except Exception as e:
                issues.append(f"ディレクトリ作成失敗 {dir_path}: {e}")
        
        return issues
    
    def register_shutdown_callback(self, callback: Callable):
        """シャットダウンコールバック登録"""
        self._shutdown_callbacks.append(callback)
    
    def register_cleanup_resource(self, resource: Any):
        """クリーンアップリソース登録"""
        self._cleanup_resources.add(resource)
    
    def _memory_cleanup_callback(self):
        """メモリクリーンアップコールバック"""
        self.logger.info(f"🧹 {self.__class__.__name__} メモリクリーンアップ実行")
        
        # サブクラス固有のクリーンアップ
        try:
            self.cleanup_resources()
        except Exception as e:
            self.logger.error(f"リソースクリーンアップエラー: {e}")
    
    def cleanup_resources(self):
        """リソースクリーンアップ（サブクラスでオーバーライド可能）"""
        # 登録されたリソースのクリーンアップ
        for resource in self._cleanup_resources.copy():
            try:
                if hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, 'shutdown'):
                    resource.shutdown()
                elif hasattr(resource, 'cleanup'):
                    resource.cleanup()
                
                self._cleanup_resources.discard(resource)
            except Exception as e:
                self.logger.debug(f"リソースクリーンアップエラー: {e}")
    
    def shutdown(self):
        """システムシャットダウン"""
        if not self.running:
            return
            
        self.logger.info(f"🛑 {self.__class__.__name__} シャットダウン開始")
        self.running = False
        
        # シャットダウンコールバック実行
        for callback in self._shutdown_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"シャットダウンコールバックエラー: {e}")
        
        # リソースクリーンアップ
        self.cleanup_resources()
        
        # パフォーマンス最適化システム終了
        if self.performance_optimizer:
            self.performance_optimizer.shutdown()
        
        self.logger.info(f"👋 {self.__class__.__name__} シャットダウン完了")
    
    def get_status(self) -> Dict[str, Any]:
        """システム状況取得"""
        return {
            "class_name": self.__class__.__name__,
            "initialized": self.initialized,
            "running": self.running,
            "project_root": str(self.project_root),
            "config": asdict(self.config),
            "cleanup_resources_count": len(self._cleanup_resources),
            "shutdown_callbacks_count": len(self._shutdown_callbacks),
            "timestamp": datetime.now().isoformat()
        }
    
    def __enter__(self):
        """コンテキストマネージャー入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー出口"""
        self.shutdown()

class TDDSystemRegistry:
    """TDDシステムレジストリ"""
    
    _systems = {}
    _lock = threading.RLock()
    
    @classmethod
    def register_system(cls, name: str, system: TDDSystemBase):
        """システム登録"""
        with cls._lock:
            cls._systems[name] = system
            logger.debug(f"TDDシステム登録: {name}")
    
    @classmethod
    def get_system(cls, name: str) -> Optional[TDDSystemBase]:
        """システム取得"""
        with cls._lock:
            return cls._systems.get(name)
    
    @classmethod
    def shutdown_all(cls):
        """全システムシャットダウン"""
        with cls._lock:
            logger.info("🛑 全TDDシステムシャットダウン開始")
            
            for name, system in cls._systems.items():
                try:
                    system.shutdown()
                    logger.info(f"✅ {name} シャットダウン完了")
                except Exception as e:
                    logger.error(f"❌ {name} シャットダウンエラー: {e}")
            
            cls._systems.clear()
            logger.info("👋 全TDDシステムシャットダウン完了")
    
    @classmethod
    def get_systems_status(cls) -> Dict[str, Dict]:
        """全システム状況取得"""
        with cls._lock:
            return {name: system.get_status() for name, system in cls._systems.items()}

# 便利関数
def create_tdd_config(project_root: Path, **kwargs) -> TDDSystemConfig:
    """TDD設定作成便利関数"""
    return TDDSystemConfig(project_root=project_root, **kwargs)

def with_tdd_system(system_class: type, config: TDDSystemConfig):
    """TDDシステム利用デコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with system_class(config) as system:
                return func(system, *args, **kwargs)
        return wrapper
    return decorator

# 使用例
class ExampleTDDSystem(TDDSystemBase):
    """使用例: カスタムTDDシステム"""
    
    def initialize(self) -> bool:
        """初期化"""
        self.logger.info("ExampleTDDSystem 初期化中...")
        
        # 事前条件検証
        issues = self.validate_preconditions()
        if issues:
            for issue in issues:
                self.logger.error(f"事前条件エラー: {issue}")
            return False
        
        return True
    
    def execute_main_operation(self) -> str:
        """メイン操作"""
        self.logger.info("ExampleTDDSystem メイン操作実行中...")
        
        # プロジェクト情報取得
        project_info = self.get_project_info()
        self.logger.info(f"プロジェクト情報: {project_info}")
        
        # 安全なコマンド実行例
        result = self.safe_subprocess_run(["python3", "--version"])
        self.logger.info(f"Python バージョン: {result.stdout.strip()}")
        
        return "操作完了"

def test_tdd_system_base():
    """TDD基盤システムテスト"""
    logger.info("🧪 TDD基盤システムテスト開始")
    
    project_root = Path(__file__).parent.parent
    config = create_tdd_config(project_root)
    
    # システム作成・実行
    system = ExampleTDDSystem(config)
    result = system.run()
    
    logger.info(f"テスト結果: {result}")
    logger.info("🎯 TDD基盤システムテスト完了")

if __name__ == "__main__":
    test_tdd_system_base()