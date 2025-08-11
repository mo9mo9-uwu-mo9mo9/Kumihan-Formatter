# Enhanced ccusage Integration

Claude Code usage tracking with Japanese timezone support and prediction features for Claude max 100USD plan.

## Features

### 1. 日本時間での制限リセット時期表示
- Claude APIの5時間ローリング制限の次回リセット時刻をJSTで表示
- 5時間境界 (0:00, 5:00, 10:00, 15:00, 20:00) に基づく正確な計算

### 2. 使用量から上限到達時期の予測
- 現在の日割り使用料から月額予測を算出
- 100USD上限到達までの残り日数を予測表示
- 高精度な浮動小数点演算 (awk) または整数演算 (fallback) 対応

### 3. 統合されたステータス表示
- 現在の月額使用料と使用率を一目で確認
- コンパクト版はプロンプト統合に最適

## Usage

### コマンド

```bash
# 詳細ステータス表示
ccusage-status

# コンパクト表示（プロンプト用）
ccusage-info

# 直接実行
~/GitHub/Kumihan-Formatter/scripts/ccusage_enhanced.sh enhanced
~/GitHub/Kumihan-Formatter/scripts/ccusage_enhanced.sh compact
```

### プロンプト統合 (Optional)

```bash
# 右プロンプトに使用状況を常時表示
RPROMPT='$(ccusage_compact)'
```

## Output Examples

### Enhanced View
```
=== Claude Code Enhanced Usage Status ===
今月の使用料: $1053.58 / $100
使用率: 1053.6%
次回5時間制限リセット: 2025-08-11 00:00 JST
予測月額: $3266.16 | 上限到達予測: 1日後
制限: Max 5x プラン (月額$100)
5時間制限: ~225メッセージまたは50-200 Claude Codeプロンプト
```

### Compact View
```
💰$1053.58(1054%) 🕒00:00
```

## API Limits Reference

### Claude Max 5x Plan ($100/month)
- **5時間制限**: 約225メッセージまたは50-200 Claude Codeプロンプト
- **リセット**: 5時間ローリング制限 (初回プロンプトから5時間後)
- **月額制限**: $100 (超過時は追加API料金)

### 週次制限 (2025年8月28日から)
- **Sonnet 4**: 週140-280時間
- **Opus 4**: 週15-35時間
- **リセット**: 毎週7日間隔

## Configuration

### Script Location
```
~/GitHub/Kumihan-Formatter/scripts/ccusage_enhanced.sh
```

### Dependencies
- `ccusage` command (Node.js package)
- `jq` for JSON parsing
- `awk` for precise calculations (optional, fallback available)

### Environment Variables
```bash
MAX_MONTHLY_USD=100  # Max plan monthly limit
```

## Integration

The script is automatically sourced in `.zshrc` and provides:

1. **ccusage_enhanced()** - Detailed status function
2. **ccusage_compact()** - Compact display function  
3. **Aliases** - Easy-to-remember command names
4. **Optional RPROMPT** - Continuous monitoring capability

## Troubleshooting

### Common Issues

1. **ccusage command not found**
   ```bash
   npm install -g ccusage
   ```

2. **jq command not found**
   ```bash
   brew install jq
   ```

3. **No usage data**
   - Ensure ccusage has API access to Claude Code usage data
   - Check that current month data exists in ccusage output

### macOS Compatibility

All date calculations are macOS-compatible using BSD date command format.

---

*✨ Generated for Kumihan-Formatter Claude Code integration*