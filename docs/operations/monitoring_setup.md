# Kumihan-Formatter 監視システム設定ガイド

> **Version**: 2025年版 Phase 4統合対応  
> **対象**: エンタープライズレベル包括的監視システム  
> **更新日**: 2025-08-19

---

## 概要

Kumihan-Formatterのエンタープライズレベル監視システムの構築・運用ガイドです。Phase 4で実装されたセキュリティ監視、構造化ログ、監査機能と統合した包括的な監視体制を構築します。

### 監視目標
- **可用性**: 99.9%以上のサービス稼働率
- **パフォーマンス**: 処理時間・スループット最適化追跡
- **セキュリティ**: 脅威検知・インシデント対応
- **ビジネス**: 利用状況・品質指標追跡
- **運用効率**: 自動化・早期検知・迅速対応

---

## 監視アーキテクチャ

### 全体構成
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   Monitoring    │───▶│   Dashboard     │
│   Kumihan       │    │   Collection    │    │   & Alerting    │
│   Formatter     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Logs & Traces │    │   Metrics Store │    │   Alert Manager │
│   ELK Stack     │    │   Prometheus    │    │   Notification  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### コンポーネント構成

#### データ収集層
- **Prometheus**: システム・アプリケーションメトリクス収集
- **Filebeat**: ログファイル収集・転送
- **APM Agent**: アプリケーション性能監視
- **Node Exporter**: システムリソース監視

#### データ保存層
- **Prometheus TSDB**: 時系列メトリクス保存
- **Elasticsearch**: ログデータ保存・検索
- **InfluxDB**: 高頻度メトリクス保存（オプション）

#### 可視化・分析層
- **Grafana**: ダッシュボード・可視化
- **Kibana**: ログ分析・検索
- **AlertManager**: アラート管理・通知

---

## 基本監視設定

### 1. Prometheusセットアップ

#### prometheus.yml
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'kumihan-formatter'
    environment: 'production'

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Kumihan-Formatter Application
  - job_name: 'kumihan-formatter'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s

  # System Monitoring
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  # Process Monitoring
  - job_name: 'process-exporter'
    static_configs:
      - targets: ['localhost:9256']

  # Docker Monitoring
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['localhost:8080']
```

#### アプリケーションメトリクス設定
```python
# kumihan_formatter/core/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from functools import wraps

# メトリクス定義
REQUEST_COUNT = Counter(
    'kumihan_formatter_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'kumihan_formatter_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

PROCESSING_TIME = Histogram(
    'kumihan_formatter_processing_duration_seconds',
    'Processing duration',
    ['operation', 'format']
)

ACTIVE_CONNECTIONS = Gauge(
    'kumihan_formatter_active_connections',
    'Active connections'
)

ERROR_RATE = Counter(
    'kumihan_formatter_errors_total',
    'Total errors',
    ['error_type', 'component']
)

def track_metrics(operation_type):
    """メトリクス追跡デコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                REQUEST_COUNT.labels(
                    method='POST',
                    endpoint=f'/{operation_type}',
                    status='200'
                ).inc()
                return result
            except Exception as e:
                ERROR_RATE.labels(
                    error_type=type(e).__name__,
                    component=operation_type
                ).inc()
                REQUEST_COUNT.labels(
                    method='POST',
                    endpoint=f'/{operation_type}',
                    status='500'
                ).inc()
                raise
            finally:
                PROCESSING_TIME.labels(
                    operation=operation_type,
                    format='kumihan'
                ).observe(time.time() - start_time)
        return wrapper
    return decorator
```

### 2. Docker Compose統合
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager:/etc/alertmanager

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro

volumes:
  prometheus_data:
  grafana_data:
```

---

## Phase 4 統合監視

### 1. 構造化ログ監視

#### ELK Stack設定
```yaml
# docker-compose.elk.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    container_name: logstash
    ports:
      - "5044:5044"
    volumes:
      - ./monitoring/logstash/pipeline:/usr/share/logstash/pipeline
      - ./monitoring/logstash/config:/usr/share/logstash/config

  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

volumes:
  elasticsearch_data:
```

#### Logstash設定
```ruby
# monitoring/logstash/pipeline/logstash.conf
input {
  beats {
    port => 5044
  }
  
  # Phase 4 構造化ログ
  file {
    path => "/app/tmp/logs/kumihan_formatter_structured.log"
    start_position => "beginning"
    codec => json
    tags => ["structured", "kumihan-formatter"]
  }
  
  # セキュリティ監査ログ
  file {
    path => "/app/tmp/logs/security_audit.log"
    start_position => "beginning"
    codec => json
    tags => ["security", "audit"]
  }
}

filter {
  if "structured" in [tags] {
    # 構造化ログの解析
    mutate {
      add_field => { "log_type" => "application" }
    }
    
    # パフォーマンスメトリクス抽出
    if [processing_time] {
      mutate {
        convert => { "processing_time" => "float" }
      }
    }
  }
  
  if "security" in [tags] {
    # セキュリティイベント分類
    if [event_type] == "authentication" {
      mutate {
        add_field => { "security_category" => "auth" }
      }
    }
    
    if [event_type] == "input_validation" {
      mutate {
        add_field => { "security_category" => "input" }
      }
    }
  }
  
  # 共通フィールド追加
  mutate {
    add_field => { "[@metadata][index_name]" => "kumihan-formatter-%{+YYYY.MM.dd}" }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[@metadata][index_name]}"
  }
  
  stdout {
    codec => rubydebug
  }
}
```

### 2. セキュリティ監視統合

#### セキュリティメトリクス
```python
# kumihan_formatter/core/monitoring/security_metrics.py
from prometheus_client import Counter, Histogram, Gauge
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

# セキュリティメトリクス
SECURITY_EVENTS = Counter(
    'kumihan_formatter_security_events_total',
    'Total security events',
    ['event_type', 'severity', 'source']
)

AUTH_ATTEMPTS = Counter(
    'kumihan_formatter_auth_attempts_total',
    'Authentication attempts',
    ['result', 'method']
)

INPUT_VALIDATION_FAILURES = Counter(
    'kumihan_formatter_input_validation_failures_total',
    'Input validation failures',
    ['validation_type', 'severity']
)

VULNERABILITY_SCAN_RESULTS = Gauge(
    'kumihan_formatter_vulnerability_count',
    'Vulnerability count',
    ['severity', 'component']
)

class SecurityMetricsCollector:
    """セキュリティメトリクス収集クラス"""
    
    @staticmethod
    def record_security_event(event_type: str, severity: str, source: str):
        """セキュリティイベント記録"""
        SECURITY_EVENTS.labels(
            event_type=event_type,
            severity=severity,
            source=source
        ).inc()
        
        logger.warning(
            "Security event recorded",
            extra={
                "event_type": event_type,
                "severity": severity,
                "source": source,
                "timestamp": time.time()
            }
        )
    
    @staticmethod
    def record_auth_attempt(result: str, method: str):
        """認証試行記録"""
        AUTH_ATTEMPTS.labels(
            result=result,
            method=method
        ).inc()
    
    @staticmethod
    def record_input_validation_failure(validation_type: str, severity: str):
        """入力検証失敗記録"""
        INPUT_VALIDATION_FAILURES.labels(
            validation_type=validation_type,
            severity=severity
        ).inc()
```

---

## メトリクス収集

### 1. システムメトリクス

#### リソース監視
```yaml
# monitoring/prometheus/rules/system_alerts.yml
groups:
  - name: system
    rules:
      # CPU使用率
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% for more than 5 minutes"

      # メモリ使用率
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 85% for more than 5 minutes"

      # ディスク使用率
      - alert: HighDiskUsage
        expr: (1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 > 90
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High disk usage detected"
          description: "Disk usage is above 90%"
```

### 2. アプリケーションメトリクス

#### パフォーマンス監視
```yaml
# monitoring/prometheus/rules/application_alerts.yml
groups:
  - name: application
    rules:
      # 応答時間
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, kumihan_formatter_request_duration_seconds) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is above 2 seconds"

      # エラー率
      - alert: HighErrorRate
        expr: rate(kumihan_formatter_errors_total[5m]) / rate(kumihan_formatter_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for more than 2 minutes"

      # 処理能力
      - alert: LowThroughput
        expr: rate(kumihan_formatter_requests_total[5m]) < 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low throughput detected"
          description: "Request rate is below 10 requests/second for more than 10 minutes"
```

### 3. カスタムメトリクス収集

#### ビジネスメトリクス
```python
# kumihan_formatter/core/monitoring/business_metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time
from typing import Dict, Any

# ビジネスメトリクス
DOCUMENT_PROCESSING = Counter(
    'kumihan_formatter_documents_processed_total',
    'Total documents processed',
    ['format', 'size_category', 'success']
)

FEATURE_USAGE = Counter(
    'kumihan_formatter_feature_usage_total',
    'Feature usage count',
    ['feature', 'user_type']
)

CONVERSION_SUCCESS_RATE = Gauge(
    'kumihan_formatter_conversion_success_rate',
    'Conversion success rate',
    ['format_from', 'format_to']
)

ACTIVE_USERS = Gauge(
    'kumihan_formatter_active_users',
    'Number of active users',
    ['time_window']
)

class BusinessMetricsCollector:
    """ビジネスメトリクス収集クラス"""
    
    def __init__(self):
        self.success_tracking: Dict[str, Dict[str, int]] = {}
    
    def track_document_processing(self, format_type: str, file_size: int, success: bool):
        """ドキュメント処理追跡"""
        size_category = self._categorize_size(file_size)
        
        DOCUMENT_PROCESSING.labels(
            format=format_type,
            size_category=size_category,
            success=str(success)
        ).inc()
    
    def track_feature_usage(self, feature: str, user_type: str = "standard"):
        """機能利用追跡"""
        FEATURE_USAGE.labels(
            feature=feature,
            user_type=user_type
        ).inc()
    
    def update_conversion_rate(self, format_from: str, format_to: str, success: bool):
        """変換成功率更新"""
        key = f"{format_from}_to_{format_to}"
        
        if key not in self.success_tracking:
            self.success_tracking[key] = {"success": 0, "total": 0}
        
        self.success_tracking[key]["total"] += 1
        if success:
            self.success_tracking[key]["success"] += 1
        
        rate = self.success_tracking[key]["success"] / self.success_tracking[key]["total"]
        
        CONVERSION_SUCCESS_RATE.labels(
            format_from=format_from,
            format_to=format_to
        ).set(rate)
    
    @staticmethod
    def _categorize_size(size_bytes: int) -> str:
        """ファイルサイズカテゴリ分類"""
        if size_bytes < 1024:  # 1KB未満
            return "small"
        elif size_bytes < 1024 * 1024:  # 1MB未満
            return "medium"
        elif size_bytes < 10 * 1024 * 1024:  # 10MB未満
            return "large"
        else:
            return "xlarge"
```

---

## ログ監視

### 1. 構造化ログ設定

#### ログ設定統合
```python
# kumihan_formatter/core/logging/monitoring_integration.py
import json
import time
from typing import Dict, Any
from kumihan_formatter.core.utilities.logger import get_logger
from kumihan_formatter.core.monitoring.security_metrics import SecurityMetricsCollector

logger = get_logger(__name__)

class MonitoringLogHandler:
    """監視システム統合ログハンドラー"""
    
    def __init__(self, log_file_path: str = "tmp/logs/monitoring_events.log"):
        self.log_file_path = log_file_path
        self.security_metrics = SecurityMetricsCollector()
    
    def log_monitoring_event(self, event_type: str, data: Dict[str, Any], severity: str = "info"):
        """監視イベントログ出力"""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "severity": severity,
            "data": data,
            "source": "kumihan_formatter"
        }
        
        # 構造化ログ出力
        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        # セキュリティイベントの場合、メトリクス記録
        if event_type.startswith("security_"):
            self.security_metrics.record_security_event(
                event_type=event_type,
                severity=severity,
                source="application"
            )
        
        # 標準ログ出力
        logger.info(f"Monitoring event: {event_type}", extra=event)
    
    def log_performance_event(self, operation: str, duration: float, metadata: Dict[str, Any]):
        """パフォーマンスイベントログ"""
        self.log_monitoring_event(
            event_type="performance",
            data={
                "operation": operation,
                "duration_seconds": duration,
                "metadata": metadata
            },
            severity="info"
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = "warning"):
        """セキュリティイベントログ"""
        self.log_monitoring_event(
            event_type=f"security_{event_type}",
            data=details,
            severity=severity
        )
```

### 2. ログ分析設定

#### Kibana ダッシュボード設定
```json
{
  "version": "8.8.0",
  "objects": [
    {
      "id": "kumihan-formatter-logs",
      "type": "index-pattern",
      "attributes": {
        "title": "kumihan-formatter-*",
        "timeFieldName": "@timestamp"
      }
    },
    {
      "id": "security-events-visualization",
      "type": "visualization",
      "attributes": {
        "title": "Security Events Over Time",
        "visState": {
          "type": "histogram",
          "params": {
            "grid": {"categoryLines": false, "style": {"color": "#eee"}},
            "categoryAxes": [{"id": "CategoryAxis-1", "type": "category", "position": "bottom", "show": true, "style": {}, "scale": {"type": "linear"}, "labels": {"show": true, "truncate": 100}, "title": {}}],
            "valueAxes": [{"id": "ValueAxis-1", "name": "LeftAxis-1", "type": "value", "position": "left", "show": true, "style": {}, "scale": {"type": "linear", "mode": "normal"}, "labels": {"show": true, "rotate": 0, "filter": false, "truncate": 100}, "title": {"text": "Count"}}]
          },
          "aggs": [
            {"id": "1", "enabled": true, "type": "count", "schema": "metric", "params": {}},
            {"id": "2", "enabled": true, "type": "date_histogram", "schema": "segment", "params": {"field": "@timestamp", "interval": "auto", "customInterval": "2h", "min_doc_count": 1, "extended_bounds": {}}}
          ]
        }
      }
    }
  ]
}
```

---

## セキュリティ監視

### 1. 脅威検知システム

#### セキュリティアラート設定
```yaml
# monitoring/prometheus/rules/security_alerts.yml
groups:
  - name: security
    rules:
      # 異常な認証試行
      - alert: SuspiciousAuthenticationActivity
        expr: increase(kumihan_formatter_auth_attempts_total{result="failure"}[5m]) > 10
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Suspicious authentication activity detected"
          description: "More than 10 failed authentication attempts in 5 minutes"

      # 入力検証失敗急増
      - alert: HighInputValidationFailures
        expr: increase(kumihan_formatter_input_validation_failures_total[1m]) > 50
        for: 30s
        labels:
          severity: warning
        annotations:
          summary: "High input validation failures"
          description: "More than 50 input validation failures in 1 minute"

      # セキュリティイベント急増
      - alert: SecurityEventSpike
        expr: increase(kumihan_formatter_security_events_total[5m]) > 20
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Security event spike detected"
          description: "Unusual increase in security events"
```

### 2. 監査ログ分析

#### 監査イベント追跡
```python
# kumihan_formatter/core/monitoring/audit_tracker.py
import json
import time
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

@dataclass
class AuditEvent:
    """監査イベントデータクラス"""
    timestamp: float
    user_id: str
    event_type: str
    resource: str
    action: str
    result: str
    metadata: Dict[str, Any]

class AuditTracker:
    """監査追跡システム"""
    
    def __init__(self, audit_log_path: str = "tmp/logs/audit.log"):
        self.audit_log_path = audit_log_path
        self.events: List[AuditEvent] = []
    
    def log_audit_event(self, user_id: str, event_type: str, resource: str, 
                       action: str, result: str, metadata: Dict[str, Any] = None):
        """監査イベントログ記録"""
        if metadata is None:
            metadata = {}
        
        event = AuditEvent(
            timestamp=time.time(),
            user_id=user_id,
            event_type=event_type,
            resource=resource,
            action=action,
            result=result,
            metadata=metadata
        )
        
        # ログファイル出力
        audit_record = {
            "timestamp": datetime.fromtimestamp(event.timestamp).isoformat(),
            "user_id": event.user_id,
            "event_type": event.event_type,
            "resource": event.resource,
            "action": event.action,
            "result": event.result,
            "metadata": event.metadata
        }
        
        with open(self.audit_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_record, ensure_ascii=False) + "\n")
        
        self.events.append(event)
        
        # 監視システム連携
        logger.info(f"Audit event: {event_type}", extra=audit_record)
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """セキュリティサマリー取得"""
        cutoff_time = time.time() - (hours * 3600)
        recent_events = [e for e in self.events if e.timestamp > cutoff_time]
        
        summary = {
            "total_events": len(recent_events),
            "failed_attempts": len([e for e in recent_events if e.result == "failure"]),
            "event_types": {},
            "user_activity": {}
        }
        
        for event in recent_events:
            # イベントタイプ別集計
            if event.event_type not in summary["event_types"]:
                summary["event_types"][event.event_type] = 0
            summary["event_types"][event.event_type] += 1
            
            # ユーザー別集計
            if event.user_id not in summary["user_activity"]:
                summary["user_activity"][event.user_id] = 0
            summary["user_activity"][event.user_id] += 1
        
        return summary
```

---

## アラート設定

### 1. AlertManager設定

#### alertmanager.yml
```yaml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@kumihan-formatter.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://localhost:5001/webhook'

- name: 'critical-alerts'
  email_configs:
  - to: 'admin@kumihan-formatter.com'
    subject: 'CRITICAL: Kumihan-Formatter Alert'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#alerts-critical'
    title: 'Critical Alert'
    text: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}

- name: 'warning-alerts'
  email_configs:
  - to: 'team@kumihan-formatter.com'
    subject: 'WARNING: Kumihan-Formatter Alert'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
```

### 2. 通知統合設定

#### Slack通知設定
```python
# kumihan_formatter/core/monitoring/notifications.py
import requests
import json
from typing import Dict, Any
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

class NotificationManager:
    """通知管理システム"""
    
    def __init__(self, slack_webhook_url: str = None, email_config: Dict[str, str] = None):
        self.slack_webhook_url = slack_webhook_url
        self.email_config = email_config or {}
    
    def send_slack_alert(self, title: str, message: str, severity: str = "info"):
        """Slackアラート送信"""
        if not self.slack_webhook_url:
            return
        
        color_map = {
            "critical": "danger",
            "warning": "warning",
            "info": "good"
        }
        
        payload = {
            "attachments": [{
                "color": color_map.get(severity, "good"),
                "title": f"Kumihan-Formatter Alert: {title}",
                "text": message,
                "footer": "Kumihan-Formatter Monitoring",
                "ts": int(time.time())
            }]
        }
        
        try:
            response = requests.post(
                self.slack_webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Slack notification sent: {title}")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    def send_email_alert(self, to: str, subject: str, body: str):
        """メールアラート送信"""
        # Email送信実装（SMTPライブラリ使用）
        pass
    
    def send_webhook_alert(self, webhook_url: str, data: Dict[str, Any]):
        """Webhook通知送信"""
        try:
            response = requests.post(
                webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Webhook notification sent to {webhook_url}")
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
```

---

## ダッシュボード構築

### 1. Grafana ダッシュボード設定

#### メインダッシュボード JSON
```json
{
  "dashboard": {
    "id": null,
    "title": "Kumihan-Formatter Monitoring Dashboard",
    "tags": ["kumihan-formatter", "monitoring"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(kumihan_formatter_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {"mode": "thresholds"},
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 10},
                {"color": "green", "value": 50}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Response Time (95th percentile)",
        "type": "stat",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, kumihan_formatter_request_duration_seconds)",
            "legendFormat": "95th percentile"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s",
            "color": {"mode": "thresholds"},
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 1},
                {"color": "red", "value": 2}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(kumihan_formatter_errors_total[5m]) / rate(kumihan_formatter_requests_total[5m])",
            "legendFormat": "Error Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percentunit",
            "color": {"mode": "thresholds"},
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 0.01},
                {"color": "red", "value": 0.05}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
      },
      {
        "id": 4,
        "title": "System Resources",
        "type": "timeseries",
        "targets": [
          {
            "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU Usage %"
          },
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "Memory Usage %"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 5,
        "title": "Security Events",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(kumihan_formatter_security_events_total[5m])",
            "legendFormat": "Security Events/sec"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "30s"
  }
}
```

### 2. カスタムダッシュボード

#### セキュリティダッシュボード
```json
{
  "dashboard": {
    "title": "Security Monitoring Dashboard",
    "panels": [
      {
        "title": "Authentication Attempts",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(kumihan_formatter_auth_attempts_total{result=\"success\"}[5m])",
            "legendFormat": "Successful"
          },
          {
            "expr": "rate(kumihan_formatter_auth_attempts_total{result=\"failure\"}[5m])",
            "legendFormat": "Failed"
          }
        ]
      },
      {
        "title": "Input Validation Failures",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(kumihan_formatter_input_validation_failures_total[5m])",
            "legendFormat": "Validation Failures/sec"
          }
        ]
      },
      {
        "title": "Vulnerability Scan Results",
        "type": "stat",
        "targets": [
          {
            "expr": "kumihan_formatter_vulnerability_count",
            "legendFormat": "{{ severity }} vulnerabilities"
          }
        ]
      }
    ]
  }
}
```

---

## トラブルシューティング

### 1. 一般的な問題と解決方法

#### Prometheus接続問題
```bash
# Prometheusサービス確認
docker ps | grep prometheus
docker logs prometheus

# メトリクスエンドポイント確認
curl http://localhost:9090/-/healthy
curl http://localhost:8000/metrics
```

#### Grafana表示問題
```bash
# Grafanaログ確認
docker logs grafana

# データソース接続確認
curl -X GET http://admin:admin123@localhost:3000/api/datasources

# ダッシュボード確認
curl -X GET http://admin:admin123@localhost:3000/api/dashboards/home
```

#### ELKスタック問題
```bash
# Elasticsearch確認
curl http://localhost:9200/_cluster/health

# Kibanaインデックス確認
curl http://localhost:9200/_cat/indices?v

# Logstash設定確認
docker exec -it logstash /usr/share/logstash/bin/logstash --config.test_and_exit --path.config=/usr/share/logstash/pipeline/
```

### 2. パフォーマンス最適化

#### Prometheus最適化設定
```yaml
# prometheus.yml 最適化設定
global:
  scrape_interval: 30s  # デフォルト15sから変更
  evaluation_interval: 30s
  external_labels:
    cluster: 'kumihan-formatter'

# ストレージ最適化
storage:
  tsdb:
    retention.time: 30d  # 保持期間
    retention.size: 10GB  # 最大サイズ
```

#### Grafana最適化
```ini
# grafana.ini 最適化設定
[database]
max_open_conn = 300
max_idle_conn = 300

[server]
enable_gzip = true

[dashboards]
default_home_dashboard_path = /etc/grafana/provisioning/dashboards/main-dashboard.json
```

### 3. セキュリティ強化

#### 認証・認可設定
```yaml
# docker-compose.yml セキュリティ強化
services:
  grafana:
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_AUTH_ANONYMOUS_ENABLED=false
      - GF_SECURITY_COOKIE_SECURE=true
      - GF_SECURITY_COOKIE_SAMESITE=strict

  prometheus:
    command:
      - '--web.enable-admin-api'
      - '--web.enable-lifecycle'
      - '--web.external-url=https://prometheus.yourdomain.com'
```

---

## 運用手順書

### 1. 日常運用チェックリスト

#### 毎日実施項目
- [ ] システムリソース使用率確認（CPU/メモリ/ディスク）
- [ ] アプリケーションエラー率確認
- [ ] セキュリティイベントレビュー
- [ ] アラート状況確認
- [ ] バックアップ状況確認

#### 週次実施項目
- [ ] パフォーマンストレンド分析
- [ ] ログローテーション状況確認
- [ ] 脆弱性スキャン結果確認
- [ ] 監視システム自体のヘルスチェック
- [ ] ダッシュボード・アラート設定見直し

#### 月次実施項目
- [ ] 監視データ保持期間管理
- [ ] パフォーマンス基準値見直し
- [ ] セキュリティポリシー確認
- [ ] 災害復旧テスト
- [ ] 監視システムアップデート

### 2. インシデント対応手順

#### 重要度レベル定義
- **Critical**: サービス停止・セキュリティ侵害
- **High**: パフォーマンス大幅劣化・機能障害
- **Medium**: 軽微な機能不具合・警告レベル
- **Low**: 情報提供・予防保守

#### 対応フロー
1. **検知・通知受信**
2. **初期調査・影響範囲確認**
3. **エスカレーション判断**
4. **応急対応実施**
5. **根本原因調査**
6. **恒久対策実施**
7. **事後レビュー・改善**

---

## Appendix

### A. 設定ファイルテンプレート

#### 完全なDocker Compose設定
```yaml
# docker-compose.monitoring.yml (完全版)
version: '3.8'

services:
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    restart: unless-stopped

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin123}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_AUTH_ANONYMOUS_ENABLED=false
    restart: unless-stopped

  # AlertManager
  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager:/etc/alertmanager
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    restart: unless-stopped

  # Node Exporter
  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    restart: unless-stopped

  # Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    restart: unless-stopped

  # Logstash
  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    container_name: logstash
    ports:
      - "5044:5044"
      - "9600:9600"
    volumes:
      - ./monitoring/logstash/pipeline:/usr/share/logstash/pipeline
      - ./monitoring/logstash/config:/usr/share/logstash/config
      - ./tmp/logs:/app/logs:ro
    depends_on:
      - elasticsearch
    restart: unless-stopped

  # Kibana
  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:
  elasticsearch_data:

networks:
  default:
    name: monitoring_network
```

### B. 初期セットアップスクリプト

#### setup_monitoring.sh
```bash
#!/bin/bash
# Kumihan-Formatter 監視システム初期セットアップスクリプト

set -e

echo "🚀 Kumihan-Formatter 監視システムセットアップ開始"

# ディレクトリ作成
mkdir -p monitoring/{prometheus,grafana,alertmanager,logstash}/{config,rules,dashboards,pipeline}
mkdir -p tmp/logs

# 設定ファイル配置
echo "📝 設定ファイル配置中..."

# Prometheus設定
cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'kumihan-formatter'
    static_configs:
      - targets: ['host.docker.internal:8000']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
EOF

# AlertManager設定
cat > monitoring/alertmanager/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@kumihan-formatter.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://localhost:5001/webhook'
EOF

# Docker Compose起動
echo "🐳 Docker Compose サービス起動中..."
docker-compose -f docker-compose.monitoring.yml up -d

# 起動確認
echo "⏳ サービス起動確認中..."
sleep 30

# ヘルスチェック
echo "🏥 ヘルスチェック実行中..."
curl -f http://localhost:9090/-/healthy && echo "✅ Prometheus OK"
curl -f http://localhost:3000/api/health && echo "✅ Grafana OK"
curl -f http://localhost:9200/_cluster/health && echo "✅ Elasticsearch OK"

echo "🎉 監視システムセットアップ完了!"
echo "📊 Grafana: http://localhost:3000 (admin/admin123)"
echo "📈 Prometheus: http://localhost:9090"
echo "🔍 Kibana: http://localhost:5601"
```

---

*🎯 Kumihan-Formatter エンタープライズ監視システム設定ガイド - 2025年版*
*📊 Phase 4統合対応・90% Token削減Claude-Gemini協業最適化*