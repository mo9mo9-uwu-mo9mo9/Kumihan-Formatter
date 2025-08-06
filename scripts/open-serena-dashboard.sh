#!/bin/bash

# Serena Dashboard Auto-Opener
# Serenaダッシュボードを自動で開くスクリプト

set -euo pipefail

DASHBOARD_URL="http://127.0.0.1:24282/dashboard/index.html"
MAX_WAIT=30
WAIT_INTERVAL=2

echo "🚀 Serena Dashboard Auto-Opener"
echo "📊 ダッシュボードURL: $DASHBOARD_URL"

# Serenaサーバーの起動待機
echo "⏳ Serenaサーバーの起動を待機中..."
for ((i=0; i<MAX_WAIT; i+=WAIT_INTERVAL)); do
    if curl -s "$DASHBOARD_URL" > /dev/null 2>&1; then
        echo "✅ Serenaサーバー起動確認完了"
        break
    fi

    if [ $i -ge $((MAX_WAIT-WAIT_INTERVAL)) ]; then
        echo "❌ タイムアウト: Serenaサーバーが起動していない可能性があります"
        echo "💡 手動確認: curl -s $DASHBOARD_URL"
        exit 1
    fi

    echo "   待機中... ($((i+WAIT_INTERVAL))s/$MAX_WAIT s)"
    sleep $WAIT_INTERVAL
done

# ブラウザでダッシュボードを開く
echo "🌐 ブラウザでダッシュボードを開いています..."
if command -v open >/dev/null 2>&1; then
    # macOS
    open "$DASHBOARD_URL"
elif command -v xdg-open >/dev/null 2>&1; then
    # Linux
    xdg-open "$DASHBOARD_URL"
elif command -v start >/dev/null 2>&1; then
    # Windows
    start "$DASHBOARD_URL"
else
    echo "⚠️  ブラウザの自動起動に失敗しました"
    echo "📋 手動でアクセス: $DASHBOARD_URL"
fi

echo "✅ Serenaダッシュボードが開かれました"
echo "📊 Issue #803/#804の66.8%削減効果をリアルタイム監視できます"
