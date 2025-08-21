"""
統合ログシステム ダッシュボード設定管理
===================================

環境設定・データベース・セキュリティ・API設定を統合管理
"""

import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DatabaseConfig:
    """データベース設定"""

    url: str = "sqlite:///workflow_logs.db"
    echo: bool = False
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30


@dataclass
class SecurityConfig:
    """セキュリティ設定"""

    secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    api_key_length: int = 32
    rate_limit_per_minute: int = 100
    cors_origins: List[str] = None

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000", "http://localhost:8501"]


@dataclass
class DashboardConfig:
    """ダッシュボード設定"""

    title: str = "Kumihan Workflow Dashboard"
    theme: str = "light"
    auto_refresh_seconds: int = 30
    max_log_entries: int = 1000
    chart_colors: List[str] = None
    enable_realtime: bool = True

    def __post_init__(self):
        if self.chart_colors is None:
            self.chart_colors = [
                "#1f77b4",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
                "#8c564b",
                "#e377c2",
                "#7f7f7f",
            ]


@dataclass
class APIConfig:
    """API設定"""

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 1
    log_level: str = "info"
    enable_docs: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"


@dataclass
class NotificationConfig:
    """通知設定"""

    enable_slack: bool = False
    slack_webhook_url: Optional[str] = None
    enable_email: bool = False
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    notification_recipients: List[str] = None

    def __post_init__(self):
        if self.notification_recipients is None:
            self.notification_recipients = []


class EnvironmentConfig:
    """環境別設定管理"""

    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.database = self._get_database_config()
        self.security = self._get_security_config()
        self.dashboard = self._get_dashboard_config()
        self.api = self._get_api_config()
        self.notification = self._get_notification_config()

    def _get_database_config(self) -> DatabaseConfig:
        """環境別データベース設定"""
        if self.environment == "production":
            return DatabaseConfig(
                url=os.getenv("DATABASE_URL", "sqlite:///workflow_logs.db"),
                echo=False,
                pool_size=50,
                max_overflow=100,
            )
        elif self.environment == "testing":
            return DatabaseConfig(url="sqlite:///:memory:", echo=True)
        else:  # development
            return DatabaseConfig(url="sqlite:///tmp/workflow_logs_dev.db", echo=True)

    def _get_security_config(self) -> SecurityConfig:
        """環境別セキュリティ設定"""
        config = SecurityConfig()

        if self.environment == "production":
            config.secret_key = os.getenv("SECRET_KEY", config.secret_key)
            config.cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
            config.rate_limit_per_minute = 50
        elif self.environment == "testing":
            config.secret_key = "test-secret-key"
            config.cors_origins = ["*"]

        return config

    def _get_dashboard_config(self) -> DashboardConfig:
        """環境別ダッシュボード設定"""
        config = DashboardConfig()

        if self.environment == "production":
            config.theme = "light"
            config.auto_refresh_seconds = 60
            config.enable_realtime = True
        elif self.environment == "testing":
            config.auto_refresh_seconds = 5
            config.max_log_entries = 100

        return config

    def _get_api_config(self) -> APIConfig:
        """環境別API設定"""
        if self.environment == "production":
            return APIConfig(
                host="0.0.0.0",
                port=int(os.getenv("PORT", "8000")),
                debug=False,
                workers=4,
                log_level="warning",
                enable_docs=False,
            )
        elif self.environment == "testing":
            return APIConfig(host="localhost", port=8001, debug=True, log_level="debug")
        else:  # development
            return APIConfig(host="localhost", port=8000, debug=True, log_level="debug")

    def _get_notification_config(self) -> NotificationConfig:
        """環境別通知設定"""
        config = NotificationConfig()

        if self.environment == "production":
            config.enable_slack = os.getenv("ENABLE_SLACK", "false").lower() == "true"
            config.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
            config.enable_email = os.getenv("ENABLE_EMAIL", "false").lower() == "true"
            config.smtp_server = os.getenv("SMTP_SERVER")
            config.email_username = os.getenv("EMAIL_USERNAME")
            config.email_password = os.getenv("EMAIL_PASSWORD")

        return config

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で取得"""
        return {
            "environment": self.environment,
            "database": self.database.__dict__,
            "security": {
                k: v
                for k, v in self.security.__dict__.items()
                if k not in ["secret_key", "api_key_length"]  # 機密情報は除外
            },
            "dashboard": self.dashboard.__dict__,
            "api": self.api.__dict__,
            "notification": {
                k: v
                for k, v in self.notification.__dict__.items()
                if not k.endswith("password")  # パスワード除外
            },
        }


class AlertConfig:
    """アラート設定"""

    def __init__(self):
        self.failure_rate_threshold = 0.3  # 30%以上の失敗率でアラート
        self.cost_threshold = 1000  # 1000Token以上でアラート
        self.response_time_threshold = 30  # 30秒以上でアラート
        self.error_count_threshold = 5  # 5回連続エラーでアラート

        self.check_intervals = {
            "failure_rate": 300,  # 5分間隔
            "cost": 600,  # 10分間隔
            "response_time": 60,  # 1分間隔
            "error_count": 30,  # 30秒間隔
        }


class MetricsConfig:
    """メトリクス設定"""

    def __init__(self):
        self.retention_days = 90  # データ保持期間
        self.aggregation_intervals = ["1h", "24h", "7d", "30d"]
        self.chart_refresh_seconds = 30

        self.kpi_targets = {
            "success_rate": 0.95,  # 95%成功率目標
            "token_savings": 0.90,  # 90%Token削減目標
            "response_time": 10,  # 10秒以内目標
            "cost_per_task": 100,  # タスク当たり100Token目標
        }


# 環境設定のシングルトンインスタンス
_config_instance: Optional[EnvironmentConfig] = None


def get_config(environment: str = None) -> EnvironmentConfig:
    """設定インスタンスを取得（シングルトン）"""
    global _config_instance

    if _config_instance is None or environment:
        env = environment or os.getenv("ENVIRONMENT", "development")
        _config_instance = EnvironmentConfig(env)

    return _config_instance


def get_alert_config() -> AlertConfig:
    """アラート設定を取得"""
    return AlertConfig()


def get_metrics_config() -> MetricsConfig:
    """メトリクス設定を取得"""
    return MetricsConfig()


# 設定の便利関数
def is_production() -> bool:
    """本番環境かどうか"""
    return get_config().environment == "production"


def is_development() -> bool:
    """開発環境かどうか"""
    return get_config().environment == "development"


def is_testing() -> bool:
    """テスト環境かどうか"""
    return get_config().environment == "testing"


def get_database_url() -> str:
    """データベースURL取得"""
    return get_config().database.url


def get_secret_key() -> str:
    """シークレットキー取得"""
    return get_config().security.secret_key


def get_cors_origins() -> List[str]:
    """CORS許可オリジン取得"""
    return get_config().security.cors_origins


# 設定ファイルの例
def create_sample_env_file():
    """サンプル環境設定ファイルを作成"""
    sample_env = """
# Kumihan Workflow Dashboard 環境設定

# 環境（development/testing/production）
ENVIRONMENT=development

# データベース
DATABASE_URL=sqlite:///workflow_logs.db

# セキュリティ
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:8501

# API
PORT=8000

# 通知
ENABLE_SLACK=false
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
ENABLE_EMAIL=false
SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=your-email@example.com
EMAIL_PASSWORD=your-app-password
"""

    env_file = Path("tmp/.env.sample")
    env_file.parent.mkdir(exist_ok=True)

    with open(env_file, "w", encoding="utf-8") as f:
        f.write(sample_env.strip())

    return env_file


if __name__ == "__main__":
    # 設定テスト
    config = get_config("development")
    print("=== 開発環境設定 ===")
    print(f"データベース: {config.database.url}")
    print(f"API: {config.api.host}:{config.api.port}")
    print(f"デバッグ: {config.api.debug}")

    # サンプル設定ファイル作成
    env_file = create_sample_env_file()
    print(f"\nサンプル設定ファイル作成: {env_file}")
