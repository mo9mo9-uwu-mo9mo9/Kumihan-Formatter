# Postbox: Claude ↔ Gemini Dual-Agent Workflow

## 🎯 概要

Claude Code と Gemini CLI 間のタスク受け渡し・協業システム

## 📁 ディレクトリ構造

```
postbox/
├── todo/           # Claude → Gemini タスク指示
├── completed/      # Gemini → Claude 結果報告
├── planning/       # 共同計画書・戦略文書
└── monitoring/     # 進捗・コスト・品質監視
```

## 🔄 ワークフロー

### Pattern 1: Dual-Agent Workflow

```
Claude Code (分析・計画・レビュー)
    ↓ タスク作成
postbox/todo/task_YYYYMMDD_HHMMSS.json
    ↓ 取得・実行
Gemini CLI (実装・テスト・修正)
    ↓ 結果報告
postbox/completed/result_YYYYMMDD_HHMMSS.json
    ↓ レビュー・検証
Claude Code (品質確認・次タスク)
```

## 📋 ファイル形式

### タスクファイル (todo/)
```json
{
  "task_id": "task_20250812_143000",
  "type": "code_modification",
  "priority": "high",
  "description": "no-untyped-def エラー修正",
  "target_files": ["path/to/file.py"],
  "requirements": {
    "error_count": 10,
    "error_type": "no-untyped-def",
    "fix_pattern": "add_return_type_annotations"
  },
  "claude_analysis": "分析結果・修正方針",
  "expected_outcome": "期待される結果",
  "timestamp": "2025-08-12T14:30:00Z"
}
```

### 結果ファイル (completed/)
```json
{
  "task_id": "task_20250812_143000",
  "result_id": "result_20250812_144500",
  "status": "completed",
  "execution_time": "15m",
  "modifications": {
    "files_modified": ["path/to/file.py"],
    "errors_fixed": 10,
    "tests_passed": true,
    "quality_checks": "passed"
  },
  "gemini_report": "実行詳細・課題・提案",
  "next_recommendations": "次のステップ提案",
  "timestamp": "2025-08-12T14:45:00Z"
}
```

## 💰 コスト最適化戦略

### Gemini 2.5 Flash主力 (90%)
- **実装作業**: コード生成・修正・テスト
- **反復作業**: 大量エラー修正・リファクタリング
- **検証作業**: 品質チェック・動作確認

### Claude温存 (10%)
- **アーキテクチャ設計**: 重要な設計判断
- **複雑分析**: 複雑なバグ・依存関係分析  
- **最終レビュー**: 品質保証・戦略的判断

## 🔧 利用方法

### Claude側
```bash
# タスク作成
echo '{"task_id": "task_20250812_143000", ...}' > postbox/todo/task_20250812_143000.json

# 結果確認
cat postbox/completed/result_20250812_144500.json
```

### Gemini側
```bash
# タスク取得・実行
gemini -p "postbox/todo/task_20250812_143000.json のタスクを実行してください"

# 結果レポート作成
# → postbox/completed/result_20250812_144500.json に自動出力
```

## 📊 監視・品質管理

### monitoring/ ファイル
- `cost_tracking.json`: Token・API使用量追跡
- `quality_metrics.json`: 品質指標・エラー削減状況
- `workflow_performance.json`: ワークフロー効率・実行時間

---

*🤖 Generated for Claude Code × Gemini CLI Collaboration System*