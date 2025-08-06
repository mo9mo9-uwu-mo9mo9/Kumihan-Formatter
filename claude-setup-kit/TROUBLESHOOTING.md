# 🔍 Serena最適化設定 トラブルシューティングガイド

> Issue #803/#804 Serena最適化設定継承システムの問題解決完全ガイド  
> 66.8%削減効果が得られない場合の詳細な診断・修復手順

## 🚨 緊急対応: 最適化効果が全く得られない場合

### 即座実行チェックリスト

1. **Serena設定確認**
```bash
# 設定ファイル存在確認
ls -la .serena/project.yml

# Phase B.2設定確認
grep -A5 "phase_b2_settings:" .serena/project.yml | grep "enabled: true"

# 現在のmax_answer_chars設定値確認
grep -A20 "default_settings:" .serena/project.yml | grep "default:"
```

2. **MCP接続確認**
```bash
# Claude Code MCP接続状況
claude mcp list

# Serena接続テスト
claude mcp test serena

# MCP設定ファイル確認
cat .mcp.json | jq '.mcpServers.serena'
```

3. **緊急修復実行**
```bash
# 自動診断・修復
./scripts/setup-serena-optimization.sh \
  --project-name "$(basename $(pwd))" \
  --project-path "." \
  --optimization-level "phase_b2"

# 効果確認
./scripts/verify-optimization.sh --sample-size 10
```

## 📊 問題別診断・解決ガイド

### 1. トークン削減効果不足（66.8%未達成）

#### 🔍 診断手順

```bash
# 現在の削減率確認
./scripts/verify-optimization.sh --report-only --output-format json | jq '.optimization_metrics.token_efficiency.reduction_rate_percentage'

# 設定値詳細確認
cat .serena/project.yml | grep -A30 "default_settings:"

# 期待値との比較
echo "ベースライン: 200000, 目標: 80000 (66.8%削減)"
echo "現在設定: $(grep 'default:' .serena/project.yml | awk '{print $2}' | head -1)"
```

#### 🛠️ 解決策

**Case 1: 設定値が大きすぎる（>100000）**
```bash
# 即座修正
sed -i 's/default: [0-9]*/default: 80000/' .serena/project.yml

# 確認
grep "default:" .serena/project.yml
```

**Case 2: Phase B.2設定が無効**
```bash
# Phase B.2有効化確認
if ! grep -A5 "phase_b2_settings:" .serena/project.yml | grep -q "enabled: true"; then
    echo "Phase B.2設定が無効です - 修復中..."
    
    # バックアップ作成
    cp .serena/project.yml .serena/project.yml.backup-$(date +%Y%m%d-%H%M%S)
    
    # 自動修復
    ./scripts/setup-serena-optimization.sh \
        --project-name "$(basename $(pwd))" \
        --project-path "." \
        --optimization-level "phase_b2"
fi
```

**Case 3: 動的設定調整が働かない**
```bash
# 適応設定診断
if ! grep -A10 "adaptive_settings:" .serena/project.yml | grep -q "enabled: true"; then
    echo "動的設定調整が無効 - 有効化中..."
    sed -i '/adaptive_settings:/,/enabled:/ s/enabled: false/enabled: true/' .serena/project.yml
fi

# 監視ウィンドウ設定確認
grep -A15 "adaptive_settings:" .serena/project.yml | grep "monitoring_window_size"
```

### 2. Serena接続問題

#### 🔍 診断手順

```bash
# MCP サーバーリスト確認
claude mcp list 2>&1 | grep -i serena

# Serenaパス確認
cat .mcp.json | jq -r '.mcpServers.serena.args[2]'

# Serena実行確認
if [ -d "$HOME/GitHub/serena" ]; then
    cd "$HOME/GitHub/serena" && uv run serena-mcp-server --help
fi
```

#### 🛠️ 解決策

**Case 1: Serenaがインストールされていない**
```bash
# 自動インストール実行
./scripts/install-serena-local.sh \
    --install-path "$HOME/GitHub/serena" \
    --optimization-ready

# MCP設定更新
./scripts/setup-serena-optimization.sh \
    --project-name "$(basename $(pwd))" \
    --project-path "." \
    --serena-path "$HOME/GitHub/serena"
```

**Case 2: Serenaパスが間違っている**
```bash
# 正しいパス検出
SERENA_PATHS=(
    "$HOME/GitHub/serena"
    "/opt/serena"
    "$HOME/.local/share/serena"
    "./serena"
)

for path in "${SERENA_PATHS[@]}"; do
    if [ -d "$path" ] && [ -f "$path/pyproject.toml" ]; then
        echo "Serena発見: $path"
        
        # MCP設定更新
        sed -i "s|\"--directory\",.*,|\"--directory\", \"$path\",|" .mcp.json
        break
    fi
done
```

**Case 3: Serena権限・依存関係問題**
```bash
# UV バージョン確認・更新
uv --version || curl -LsSf https://astral.sh/uv/install.sh | sh

# Serena依存関係確認・修復
if [ -d "$HOME/GitHub/serena" ]; then
    cd "$HOME/GitHub/serena"
    uv sync
    uv run serena-mcp-server --help
fi
```

### 3. 応答時間・パフォーマンス問題

#### 🔍 診断手順

```bash
# 応答時間測定
./scripts/verify-optimization.sh \
    --sample-size 20 \
    --test-duration 120 \
    --output-format json | jq '.optimization_metrics.response_performance'

# システムリソース確認
python3 -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"

# プロセス確認
ps aux | grep -E "(serena|claude)" | head -10
```

#### 🛠️ 解決策

**Case 1: メモリ使用量過多**
```bash
# メモリ最適化設定適用
cat >> .serena/project.yml << 'EOF'

# メモリ最適化追加設定
memory_optimization:
  enabled: true
  max_cache_size: 50MB
  gc_frequency: high
  buffer_size_limit: 10MB
EOF

# システム再起動推奨
echo "システムリソース解放のため、Claude Code再起動を推奨します"
```

**Case 2: 設定値が過度に厳しい**
```bash
# 設定緩和（段階的）
echo "現在の設定を一時的に緩和..."

# overview設定を5000→8000に調整
sed -i 's/overview: 5000/overview: 8000/' .serena/project.yml

# default設定を80000→100000に調整  
sed -i 's/default: 80000/default: 100000/' .serena/project.yml

# 効果確認
./scripts/verify-optimization.sh --sample-size 5
```

**Case 3: 並列処理・競合問題**
```bash
# 監視間隔調整
if [ -f ".serena/project.yml" ]; then
    # 監視間隔を短縮（負荷軽減）
    sed -i 's/monitoring_interval: [0-9.]*$/monitoring_interval: 5.0/' .serena/project.yml
    
    # 学習処理の軽量化
    sed -i 's/learning_data_threshold: [0-9]*$/learning_data_threshold: 10/' .serena/project.yml
fi
```

### 4. 設定ファイル破損・構文エラー

#### 🔍 診断手順

```bash
# YAML構文チェック
python3 -c "
import yaml
try:
    with open('.serena/project.yml', 'r') as f:
        yaml.safe_load(f)
    print('✅ YAML構文: OK')
except Exception as e:
    print(f'❌ YAML構文エラー: {e}')
"

# JSON構文チェック
if [ -f ".mcp.json" ]; then
    jq empty .mcp.json && echo "✅ JSON構文: OK" || echo "❌ JSON構文エラー"
fi

# ファイルサイズ・権限確認
ls -la .serena/project.yml .mcp.json 2>/dev/null
```

#### 🛠️ 解決策

**Case 1: YAML構文エラー**
```bash
# バックアップ作成（存在する場合）
if [ -f ".serena/project.yml" ]; then
    cp .serena/project.yml .serena/project.yml.broken-$(date +%Y%m%d-%H%M%S)
fi

# 完全再生成
./scripts/setup-serena-optimization.sh \
    --project-name "$(basename $(pwd))" \
    --project-path "." \
    --optimization-level "phase_b2"

echo "✅ 設定ファイル再生成完了"
```

**Case 2: ファイル権限問題**
```bash
# 権限修復
chmod 644 .serena/project.yml .mcp.json 2>/dev/null
chown $(whoami):$(whoami) .serena/project.yml .mcp.json 2>/dev/null

# ディレクトリ権限確認
chmod 755 .serena/ 2>/dev/null
```

**Case 3: ファイル完全破損**
```bash
# 緊急復旧：テンプレートから再生成
if [ -f "claude-setup-kit/templates/serena_project.yml.template" ]; then
    echo "テンプレートから緊急復旧中..."
    
    # テンプレート適用
    cp claude-setup-kit/templates/serena_project.yml.template .serena/project.yml
    
    # プレースホルダー置換
    sed -i "s/{LANGUAGE}/python/g" .serena/project.yml
    sed -i "s/{PROJECT_NAME}/$(basename $(pwd))/g" .serena/project.yml
    sed -i "s/{GENERATION_DATE}/$(date '+%Y-%m-%d %H:%M:%S')/g" .serena/project.yml
    
    echo "✅ 緊急復旧完了"
fi
```

## 🔄 継続監視・メンテナンス問題

### 監視システムが動作しない

#### 🔍 診断手順

```bash
# 監視プロセス確認
ps aux | grep monitor-serena-efficiency

# 監視ログ確認
ls -la tmp/serena-monitoring/ 2>/dev/null

# Web ダッシュボード確認
curl -s http://localhost:8080 > /dev/null && echo "✅ ダッシュボード応答" || echo "❌ ダッシュボード無応答"
```

#### 🛠️ 解決策

```bash
# 監視システム再起動
pkill -f monitor-serena-efficiency 2>/dev/null

# 清理・再開
rm -rf tmp/serena-monitoring/
./scripts/monitor-serena-efficiency.sh \
    --daemon-mode \
    --maintenance-mode \
    --monitor-interval 300

# Web ダッシュボード再起動
./scripts/monitor-serena-efficiency.sh \
    --web-dashboard \
    --daemon-mode
```

## ⚡ 高速診断スクリプト

### 全体診断（5分で完了）

```bash
#!/bin/bash
# 全体診断スクリプト

echo "🔍 Serena最適化設定診断開始..."

# 1. 基本設定確認
echo "1. 基本設定確認"
ls -la .serena/project.yml .mcp.json 2>/dev/null || echo "❌ 設定ファイル不足"

# 2. Serena接続確認  
echo "2. Serena接続確認"
claude mcp test serena 2>/dev/null && echo "✅ Serena接続OK" || echo "❌ Serena接続失敗"

# 3. 最適化効果確認
echo "3. 最適化効果確認"
current_setting=$(grep 'default:' .serena/project.yml | awk '{print $2}' | head -1 2>/dev/null)
if [ "$current_setting" -le 100000 ] 2>/dev/null; then
    reduction=$(echo "scale=2; ((200000 - $current_setting) * 100) / 200000" | bc -l)
    echo "✅ 削減率: ${reduction}% (設定値: $current_setting)"
else
    echo "❌ 削減効果不十分 (設定値: $current_setting)"
fi

# 4. Phase B.2設定確認
echo "4. Phase B.2設定確認"
if grep -q "phase_b2_settings:" .serena/project.yml && grep -A5 "phase_b2_settings:" .serena/project.yml | grep -q "enabled: true"; then
    echo "✅ Phase B.2有効"
else
    echo "❌ Phase B.2無効"
fi

echo "🔍 診断完了"
```

### 自動修復スクリプト（10分で完了）

```bash
#!/bin/bash
# 自動修復スクリプト

echo "🛠️ Serena最適化設定自動修復開始..."

# バックアップ作成
if [ -f ".serena/project.yml" ]; then
    cp .serena/project.yml .serena/project.yml.backup-$(date +%Y%m%d-%H%M%S)
fi

# 完全再セットアップ
./scripts/setup-serena-optimization.sh \
    --project-name "$(basename $(pwd))" \
    --project-path "." \
    --optimization-level "phase_b2" \
    --with-monitoring

# 効果確認
./scripts/verify-optimization.sh --sample-size 10 --output-format markdown

echo "🛠️ 自動修復完了"
```

## 📞 サポート・エスカレーション

### 解決しない場合の対応

1. **Issue報告**
   - GitHub Issues: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues
   - タイトル: [Setup Kit] Issue #803最適化設定問題
   - 内容: 診断結果・エラーログ・環境情報

2. **ログ収集**
```bash
# 包括ログ収集
mkdir -p debug-info
cp .serena/project.yml debug-info/ 2>/dev/null
cp .mcp.json debug-info/ 2>/dev/null
./scripts/verify-optimization.sh --output-format json > debug-info/verification.json 2>&1
ps aux | grep -E "(serena|claude)" > debug-info/processes.txt
uv --version > debug-info/environment.txt 2>&1
python3 --version >> debug-info/environment.txt 2>&1

echo "デバッグ情報を debug-info/ に収集しました"
```

3. **一時回避策**
```bash
# 基本動作確保（最小限設定）
cat > .serena/project.yml << 'EOF'
language: python
project_name: "Emergency-Setup"
default_settings:
  max_answer_chars:
    default: 100000
EOF

# MCP基本設定
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "serena": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/Users/'$(whoami)'/GitHub/serena", "serena-mcp-server"]
    }
  }
}
EOF

echo "緊急設定適用完了（基本動作確保）"
```

---

**🚀 問題が解決したら効果確認を忘れずに！**

```bash
# 最終確認
./scripts/verify-optimization.sh --benchmark-mode --sample-size 20
```

*Generated by Claude Code Setup Kit v2.0 - Troubleshooting Guide*  
*Issue #803/#804 Serena Optimization Support*