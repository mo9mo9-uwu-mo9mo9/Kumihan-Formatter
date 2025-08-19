# Kumihan-Formatter デプロイメントガイド

> **企業運用レベル対応** - 2025年版エンタープライズデプロイメント

---

## 📋 概要

Kumihan-FormatterをPython 3.12+環境で本番運用するための包括的なデプロイメントガイドです。開発環境から本番環境まで、段階的で安全なデプロイメント戦略を提供します。

### 対応環境
- **開発環境**: ローカル開発・テスト
- **ステージング環境**: 本番類似環境での検証
- **本番環境**: エンタープライズ運用環境

---

## 🔧 前提条件

### システム要件
- **Python**: 3.12以降（必須）
- **OS**: Linux (Ubuntu 20.04+/RHEL 8+), macOS 13+, Windows 10+
- **RAM**: 最小4GB、推奨8GB以上
- **Storage**: 最小10GB、推奨20GB以上
- **Network**: インターネット接続（依存関係インストール）

### 必要なシステムパッケージ
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev git build-essential

# RHEL/CentOS
sudo dnf install -y python3.12 python3.12-devel git gcc make

# macOS (Homebrew)
brew install python@3.12 git
```

---

## 🏗️ 環境構成

### 1. 開発環境セットアップ

```bash
# 1. プロジェクトクローン
git clone https://github.com/your-org/Kumihan-Formatter.git
cd Kumihan-Formatter

# 2. Python仮想環境作成
python3.12 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 開発依存関係インストール
pip install --upgrade pip setuptools wheel
pip install -e ".[dev,performance,ai_optimization]"

# 4. 開発環境検証
make setup
make lint
make test
```

### 2. ステージング環境構築

```bash
# 1. 本番類似環境準備
python3.12 -m venv staging-env
source staging-env/bin/activate

# 2. 本番レベル依存関係インストール
pip install --no-dev .
pip install gunicorn supervisor  # Webサーバー用

# 3. 設定ファイル準備
cp config/staging.yaml.example config/staging.yaml
# staging.yaml を環境に応じて編集

# 4. ステージング検証
make test-integration
make quality-gate-run PHASE=staging
```

### 3. 本番環境構築

```bash
# 1. 本番環境用仮想環境
python3.12 -m venv production-env
source production-env/bin/activate

# 2. 本番依存関係インストール（最小構成）
pip install --no-dev --no-cache-dir .

# 3. 本番設定適用
cp config/production.yaml.template config/production.yaml
# セキュリティ設定、ログ設定等を調整

# 4. 本番前検証
make gemini-validation-full
make quality-comprehensive
```

---

## 🚀 基本デプロイメント

### 標準デプロイメント手順

```bash
# 1. 品質保証チェック
make gemini-quality-check
make test-coverage

# 2. ビルド準備
make clean
python3.12 -m build

# 3. 依存関係チェック
pip check
pip list --outdated

# 4. デプロイメント実行
# 方法1: pipでインストール
pip install dist/kumihan_formatter-*.whl

# 方法2: 直接実行（開発用）
python3.12 -m kumihan_formatter --help

# 5. 動作確認
kumihan --version
kumihan sample --output tmp/deployment_test.html
```

### Makefileベース品質管理統合

```bash
# デプロイ前必須チェック
make pre-commit              # Git hookレベル検証
make gemini-post-review      # 総合レビュー
make quality-full-check      # 全品質システム実行

# 継続的品質監視
make quality-realtime-start  # リアルタイム監視開始
make tech-debt-check         # 技術的負債監視

# 自動修正・最適化
make quality-auto-correct    # 自動修正エンジン
make gemini-mypy            # 型アノテーション自動修正
```

---

## 🏢 エンタープライズデプロイメント

### Docker化デプロイメント

#### Dockerfile
```dockerfile
FROM python:3.12-slim

# システム依存関係
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# Python依存関係
COPY pyproject.toml ./
COPY requirements.txt ./
RUN pip install --no-cache-dir -e .

# アプリケーションコピー
COPY kumihan_formatter/ ./kumihan_formatter/
COPY config/ ./config/

# 非rootユーザー作成
RUN useradd -m -u 1000 kumihan && \
    chown -R kumihan:kumihan /app
USER kumihan

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD kumihan --version || exit 1

# 実行
EXPOSE 8000
CMD ["kumihan", "serve"]
```

#### Docker Compose
```yaml
version: '3.8'
services:
  kumihan-formatter:
    build: .
    ports:
      - "8000:8000"
    environment:
      - KUMIHAN_ENV=production
      - KUMIHAN_LOG_LEVEL=INFO
    volumes:
      - ./tmp:/app/tmp
      - ./logs:/app/logs
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - kumihan-formatter
    restart: unless-stopped
```

### Kubernetes デプロイメント

#### deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kumihan-formatter
  labels:
    app: kumihan-formatter
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kumihan-formatter
  template:
    metadata:
      labels:
        app: kumihan-formatter
    spec:
      containers:
      - name: kumihan-formatter
        image: kumihan-formatter:latest
        ports:
        - containerPort: 8000
        env:
        - name: KUMIHAN_ENV
          value: "production"
        - name: KUMIHAN_REDIS_URL
          value: "redis://redis:6379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 高可用性構成

#### ロードバランサー設定
```bash
# HAProxy設定例
frontend kumihan_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/kumihan.pem
    redirect scheme https if !{ ssl_fc }
    default_backend kumihan_backend

backend kumihan_backend
    balance roundrobin
    option httpchk GET /health
    server kumihan1 10.0.1.10:8000 check
    server kumihan2 10.0.1.11:8000 check
    server kumihan3 10.0.1.12:8000 check
```

---

## ⚙️ 設定管理

### 環境変数設定

```bash
# 基本設定
export KUMIHAN_ENV=production
export KUMIHAN_DEBUG=false
export KUMIHAN_LOG_LEVEL=INFO

# データベース設定（必要に応じて）
export KUMIHAN_DB_URL=postgresql://user:pass@localhost/kumihan

# Redis設定（キャッシュ用）
export KUMIHAN_REDIS_URL=redis://localhost:6379/0

# セキュリティ設定
export KUMIHAN_SECRET_KEY=your-secret-key-here
export KUMIHAN_ALLOWED_HOSTS=localhost,yourdomain.com
```

### 設定ファイル（production.yaml）

```yaml
# Kumihan-Formatter 本番設定
app:
  name: "Kumihan-Formatter"
  version: "0.9.0-alpha.8"
  environment: "production"
  debug: false

logging:
  level: "INFO"
  format: "json"
  handlers:
    - type: "file"
      filename: "/app/logs/kumihan.log"
      max_size: "100MB"
      backup_count: 5
    - type: "syslog"
      facility: "local0"
    - type: "structured"
      format: "json"

security:
  secret_key: "${KUMIHAN_SECRET_KEY}"
  allowed_hosts:
    - "localhost"
    - "yourdomain.com"
  csrf_protection: true
  secure_cookies: true
  
performance:
  cache:
    type: "redis"
    url: "${KUMIHAN_REDIS_URL}"
    ttl: 3600
  
  parallel_processing:
    max_workers: 4
    chunk_size: 1000

monitoring:
  metrics:
    enabled: true
    endpoint: "/metrics"
  
  health_check:
    enabled: true
    endpoint: "/health"
    
  alerts:
    email:
      enabled: true
      smtp_host: "smtp.company.com"
      recipients: ["ops@company.com"]
```

### 機密情報管理

```bash
# 環境変数ファイル（.env.production）
KUMIHAN_SECRET_KEY=your-256-bit-secret-key
KUMIHAN_DB_PASSWORD=secure-database-password
KUMIHAN_REDIS_PASSWORD=secure-redis-password

# Docker Secrets使用例
echo "secure-secret-key" | docker secret create kumihan_secret_key -

# Kubernetes Secrets使用例
kubectl create secret generic kumihan-secrets \
  --from-literal=secret-key=your-secret-key \
  --from-literal=db-password=your-db-password
```

---

## 🔒 セキュリティ設定

### SSL/TLS設定

```bash
# Let's Encrypt証明書取得
certbot certonly --webroot -w /var/www/html -d yourdomain.com

# 証明書自動更新
echo "0 0,12 * * * root python -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | sudo tee -a /etc/crontab
```

### ファイアウォール設定

```bash
# UFW設定例
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

### セキュリティヘッダー設定（Nginx）

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # セキュリティヘッダー
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'" always;
    
    # SSL設定
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Phase 4セキュリティ監査対応

```bash
# 構造化ログ設定確認
make gemini-quality-check  # セキュリティチェック含む

# 入力検証システム確認
python3.12 -c "
from kumihan_formatter.core.security.input_validation import InputValidator
validator = InputValidator()
print('✅ 入力検証システム正常')
"

# 監査ログ設定
mkdir -p /var/log/kumihan/audit
chown kumihan:kumihan /var/log/kumihan/audit
chmod 750 /var/log/kumihan/audit
```

---

## 📊 監視設定

### システム監視

#### Prometheus設定
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'kumihan-formatter'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

#### Grafana ダッシュボード
```json
{
  "dashboard": {
    "title": "Kumihan-Formatter Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(kumihan_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(kumihan_request_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

### アプリケーション監視

```python
# monitoring.py
import logging
from kumihan_formatter.core.utilities.logger import get_logger

# 構造化ログ設定
logger = get_logger(__name__)

def setup_monitoring():
    """監視システム初期化"""
    
    # メトリクス収集
    from prometheus_client import start_http_server, Counter, Histogram
    
    REQUEST_COUNT = Counter('kumihan_requests_total', 'Total requests')
    REQUEST_LATENCY = Histogram('kumihan_request_duration_seconds', 'Request latency')
    
    # メトリクスエンドポイント開始
    start_http_server(8001)
    logger.info("Monitoring server started on port 8001")

def health_check():
    """ヘルスチェック実装"""
    try:
        # 基本機能確認
        from kumihan_formatter.parser import KumihanParser
        parser = KumihanParser()
        
        # レンダラー確認
        from kumihan_formatter.core.rendering.main_renderer import MainRenderer
        renderer = MainRenderer()
        
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
```

### ログ監視

```bash
# ログローテーション設定（logrotate）
cat > /etc/logrotate.d/kumihan << EOF
/app/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 kumihan kumihan
    postrotate
        systemctl reload kumihan-formatter
    endscript
}
EOF
```

---

## 🔄 バックアップ・復旧

### データバックアップ戦略

```bash
#!/bin/bash
# backup.sh - 定期バックアップスクリプト

BACKUP_DIR="/backups/kumihan"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/app"

# バックアップディレクトリ作成
mkdir -p "$BACKUP_DIR"

# アプリケーションファイルバックアップ
echo "🔄 アプリケーションバックアップ開始..."
tar -czf "$BACKUP_DIR/app_$DATE.tar.gz" \
    --exclude="$APP_DIR/tmp/*" \
    --exclude="$APP_DIR/.git" \
    "$APP_DIR"

# 設定ファイルバックアップ
echo "📋 設定ファイルバックアップ..."
cp -r "$APP_DIR/config" "$BACKUP_DIR/config_$DATE"

# データベースバックアップ（必要に応じて）
if [ -n "$KUMIHAN_DB_URL" ]; then
    echo "💾 データベースバックアップ..."
    pg_dump "$KUMIHAN_DB_URL" > "$BACKUP_DIR/db_$DATE.sql"
fi

# 古いバックアップ削除（30日以上）
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "✅ バックアップ完了: $BACKUP_DIR"
```

### 災害復旧計画

```bash
#!/bin/bash
# restore.sh - 緊急復旧スクリプト

BACKUP_DIR="/backups/kumihan"
APP_DIR="/app"
RESTORE_DATE=${1:-$(ls -t "$BACKUP_DIR"/app_*.tar.gz | head -1 | grep -o '[0-9]\{8\}_[0-9]\{6\}')}

echo "🚨 緊急復旧開始: $RESTORE_DATE"

# アプリケーション停止
systemctl stop kumihan-formatter

# 現在の状態バックアップ
mv "$APP_DIR" "$APP_DIR.emergency_backup_$(date +%Y%m%d_%H%M%S)"

# アプリケーション復旧
echo "📁 アプリケーション復旧中..."
mkdir -p "$APP_DIR"
tar -xzf "$BACKUP_DIR/app_$RESTORE_DATE.tar.gz" -C /

# 設定復旧
echo "⚙️ 設定ファイル復旧中..."
cp -r "$BACKUP_DIR/config_$RESTORE_DATE"/* "$APP_DIR/config/"

# データベース復旧（必要に応じて）
if [ -f "$BACKUP_DIR/db_$RESTORE_DATE.sql" ]; then
    echo "💾 データベース復旧中..."
    psql "$KUMIHAN_DB_URL" < "$BACKUP_DIR/db_$RESTORE_DATE.sql"
fi

# サービス再開
echo "🚀 サービス再開中..."
systemctl start kumihan-formatter

# 動作確認
sleep 10
if systemctl is-active --quiet kumihan-formatter; then
    echo "✅ 復旧完了"
    curl -f http://localhost:8000/health
else
    echo "❌ 復旧失敗"
    exit 1
fi
```

---

## 🔍 トラブルシューティング

### 一般的な問題と解決法

#### Python依存関係問題
```bash
# 問題: ModuleNotFoundError
# 解決: 依存関係再インストール
pip install --upgrade --force-reinstall -e .

# 問題: バージョン競合
# 解決: 仮想環境再作成
deactivate
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -e .
```

#### パフォーマンス問題
```bash
# メモリ使用量チェック
python3.12 -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f}MB')
"

# CPU使用率監視
top -p $(pgrep -f kumihan)

# パフォーマンステスト実行
make test-performance
```

#### ログ問題診断
```bash
# エラーログ確認
tail -f /app/logs/kumihan.log | grep ERROR

# 構造化ログ解析
python3.12 -c "
import json
with open('/app/logs/kumihan.log') as f:
    for line in f:
        try:
            log_entry = json.loads(line)
            if log_entry.get('level') == 'ERROR':
                print(f'{log_entry[\"timestamp\"]}: {log_entry[\"message\"]}')
        except:
            continue
"
```

### デプロイメント固有問題

#### Docker関連
```bash
# コンテナログ確認
docker logs kumihan-formatter

# コンテナ内部調査
docker exec -it kumihan-formatter bash

# イメージリビルド
docker build --no-cache -t kumihan-formatter .
```

#### Kubernetes関連
```bash
# Pod状態確認
kubectl get pods -l app=kumihan-formatter

# Pod詳細確認
kubectl describe pod kumihan-formatter-xxx

# ログ確認
kubectl logs kumihan-formatter-xxx -f
```

### 品質保証システム統合トラブルシューティング

```bash
# Gemini協業システム診断
make gemini-status

# 品質チェック失敗時の詳細確認
make gemini-validation-full

# 自動修正システム実行
make quality-auto-correct

# 技術的負債チェック
make tech-debt-check
```

---

## 📚 付録

### デプロイメントチェックリスト

#### 基本チェックリスト
- [ ] Python 3.12+環境確認
- [ ] 依存関係インストール完了
- [ ] 基本テスト実行（`make test`）
- [ ] 品質チェック実行（`make lint`）
- [ ] 設定ファイル準備完了
- [ ] ログディレクトリ作成完了

#### セキュリティチェックリスト
- [ ] SSL/TLS証明書設定完了
- [ ] ファイアウォール設定完了
- [ ] セキュリティヘッダー設定完了
- [ ] 機密情報の環境変数化完了
- [ ] ユーザー権限設定完了
- [ ] 監査ログ設定完了

#### エンタープライズチェックリスト
- [ ] 高可用性構成確認
- [ ] ロードバランサー設定完了
- [ ] 監視システム設定完了
- [ ] バックアップシステム設定完了
- [ ] 災害復旧手順確認済み
- [ ] パフォーマンスチューニング完了

### 有用なコマンド集

```bash
# 即座に使える運用コマンド

# 1. クイックヘルスチェック
curl -f http://localhost:8000/health

# 2. システムメトリクス確認  
curl http://localhost:8001/metrics

# 3. 品質保証統合実行
make quality-full-check

# 4. 緊急時ログ確認
tail -100 /app/logs/kumihan.log | grep -E "(ERROR|CRITICAL)"

# 5. プロセス監視
ps aux | grep kumihan

# 6. ディスク使用量確認
du -sh /app/* | sort -hr

# 7. ネットワーク接続確認
ss -tulpn | grep :8000
```

### 参考リンク

- [Python 3.12公式ドキュメント](https://docs.python.org/3.12/)
- [Docker公式ガイド](https://docs.docker.com/)
- [Kubernetes公式ドキュメント](https://kubernetes.io/docs/)
- [Nginx設定ガイド](https://nginx.org/en/docs/)
- [Prometheus監視設定](https://prometheus.io/docs/)
- [Let's Encrypt証明書](https://letsencrypt.org/docs/)

---

## 🎯 まとめ

このデプロイメントガイドは、Kumihan-Formatterの安全で効率的な本番運用を実現するための包括的な手順書です。

### 重要なポイント
1. **段階的デプロイメント**: 開発→ステージング→本番の順で確実に検証
2. **品質保証統合**: 既存のMakefileコマンドを活用した品質管理
3. **セキュリティファースト**: Phase 4セキュリティ要件に完全対応
4. **運用効率**: 監視・バックアップ・復旧の自動化
5. **エンタープライズ対応**: スケーラビリティと高可用性の確保

### 次のステップ
1. 開発環境での動作確認
2. ステージング環境でのフルテスト
3. 本番環境への段階的ロールアウト
4. 継続的監視・改善サイクルの確立

---

*🚀 Kumihan-Formatter エンタープライズデプロイメント完了 - Production Ready*