#!/bin/bash

# Discord Webhook通知スクリプト（リッチ版）
# 使用方法: ./discord-notify.sh "メッセージ内容"

# ここにDiscord WebhookのURLを設定してください
WEBHOOK_URL="https://discord.com/api/webhooks/1391279800047501382/qij4BKKapEpXHvGqfCVlxKmGayw35CtXqkxg_q7BWSliaLnDy7Y-3qf89uu3sx_rIsyF"

# あなたのDiscordユーザーID（<@!YOUR_USER_ID>形式でメンションするため）
# ユーザーIDを取得するには: Discordで自分を右クリック→「IDをコピー」
USER_ID="200104211306905601"

# メッセージを引数から取得
MESSAGE="$1"

# メッセージが指定されていない場合のデフォルト
if [ -z "$MESSAGE" ]; then
    MESSAGE="Claude Code: タスクが完了しました"
fi

# 現在時刻を取得
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
CURRENT_DIR=$(basename "$(pwd)")

# Discord embedを構築（メンション付き）
EMBED_JSON=$(cat <<EOF
{
  "content": "<@!${USER_ID}>",
  "embeds": [
    {
      "title": "🤖 Claude Code通知",
      "description": "${MESSAGE}",
      "color": 7506394,
      "fields": [
        {
          "name": "⏰ 時刻",
          "value": "${TIMESTAMP}",
          "inline": true
        },
        {
          "name": "📂 ディレクトリ",
          "value": "\`${CURRENT_DIR}\`",
          "inline": true
        }
      ],
      "footer": {
        "text": "Claude Code"
      },
      "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
    }
  ]
}
EOF
)

# Discordに通知を送信
curl -H "Content-Type: application/json" \
     -X POST \
     -d "$EMBED_JSON" \
     "$WEBHOOK_URL"

echo "Discord通知を送信しました: $MESSAGE"
