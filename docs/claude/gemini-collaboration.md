# 🤖 Claude ↔ Gemini 協業システム

> **Token節約システム** - 60-70%コスト削減を実現するDual-Agent Workflow

## 🎯 システム概要

Claude Code ↔ Gemini 2.5 Flashの協業により、大幅なToken削減と効率的なコード修正を実現。

### 💰 コスト効率
- **Claude**: $15/1M入力, $75/1M出力
- **Gemini**: $0.30/1M入力, $2.50/1M出力 (95%削減)
- **平均効果**: 60-70%コスト削減

## ⚙️ 基本使用方法

### 🚀 クイックスタート

```bash
# 自動判断でGemini使用
make gemini-mypy TARGET_FILES="file1.py,file2.py"

# 手動実行
python3 postbox/workflow/dual_agent_coordinator.py \
    --files kumihan_formatter/core/parser.py \
    --error-type no-untyped-def
```

### 🎛️ 高度な制御

```python
# 自動化レベル設定
coordinator.set_automation_config({
    "automation_level": "SEMI_AUTO",        # FULL_AUTO, APPROVAL_REQUIRED, MANUAL_ONLY
    "token_threshold": 1000,                # Gemini判定閾値
    "cost_limit": 0.01,                     # 1タスク最大コスト
    "quality_gate": "pre_commit",           # 品質基準
    "flash_optimization": {
        "micro_task_division": True,        # 関数レベル分割
        "context_limit": 2000,              # トークン制限
        "min_benefit_score": 0.7,           # 最小効果スコア
        "complexity_threshold": "moderate"  # 複雑度閾値
    }
})
```

### 🔍 監視・品質管理

**自動品質チェック:**
- mypy strict mode適合性
- pre-commit hooks通過
- テスト全件通過
- セキュリティスキャン

**進捗監視:**
```bash
# 実行統計表示
python3 postbox/workflow/dual_agent_coordinator.py --stats

# コスト追跡
cat postbox/monitoring/cost_tracking.json

# 品質レポート
make gemini-report
```

## 🎯 統合品質管理システム

**Claude ↔ Gemini協業での統一品質保証:**

```bash
# 包括的品質チェック (7項目評価)
make gemini-quality-check

# 品質ゲートチェック (段階別基準)
make gemini-quality-gate GATE_TYPE=pre_commit   # 0.8以上
make gemini-quality-gate GATE_TYPE=pre_push     # 0.85以上
make gemini-quality-gate GATE_TYPE=production   # 0.9以上

# 品質統合ワークフロー (事前→修正→事後チェック)
make gemini-integrated-workflow

# 詳細品質レポート生成
make gemini-quality-report FORMAT=html    # HTML形式
make gemini-quality-report FORMAT=json    # JSON形式

# リアルタイム品質監視
make gemini-quality-monitor
```

**品質基準統一:**
- **総合スコア**: 0.7以上（最低基準）
- **型チェック**: 0.8以上（mypy strict必須）
- **セキュリティ**: 0.9以上（脆弱性ゼロ目標）
- **エラー数制限**: 10件以下
- **フォーマット**: Black完全準拠

**自動アラート:**
- 品質スコア急低下検出
- エラー数閾値超過通知
- 連続的品質劣化警告
- セキュリティリスク即時通知

## 🔧 技術的詳細

### システム構成
```
postbox/
├── core/workflow_decision_engine.py    # 自動判断エンジン
├── workflow/dual_agent_coordinator.py  # 協業コーディネーター
├── quality/quality_manager.py         # 統合品質管理
└── monitoring/quality_monitor.py      # リアルタイム監視
```

### Flash 2.5最適化
- **micro-task分割**: 関数レベルでの細分化
- **コンテキスト制限**: 2,000トークン以内
- **段階的実行**: 1関数ずつの確実処理
- **テンプレート**: エラー種別対応の具体的指示

### 判定アルゴリズム
1. **複雑度分析**: ファイルサイズ・エラー数・構造複雑性
2. **コスト計算**: 推定Token数×料金体系
3. **効果予測**: 過去実績から成功率算出
4. **閾値判定**: 設定基準による自動選択

### 品質保証
- **事前チェック**: 修正前の品質ベースライン測定
- **修正実行**: Gemini最適化によるエラー修正
- **事後検証**: Claude による修正内容レビュー
- **統合評価**: 品質改善度の定量評価

---

*🤖 Token節約システム - Claude ↔ Gemini Dual-Agent Workflow*