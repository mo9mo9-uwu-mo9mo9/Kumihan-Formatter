# Claude Code リファレンス

> Kumihan-Formatter をClaude Codeで効率的に扱うためのリファレンス

## 📋 ファイル構造（Claude Code最適化済み）

```
Kumihan-Formatter/
├── README.md                    # プロジェクト概要
├── CLAUDE.md                    # Claude Code指示ファイル（最重要）
├── CONTRIBUTING.md              # 開発プロセス
├── CHANGELOG.md                 # 変更履歴
├── Makefile                     # 開発コマンド
└── docs/                        # ドキュメント集
    ├── REFERENCE.md             # 本ファイル（Claude Code用）
    ├── ARCHITECTURE.md          # システム全体仕様
    ├── DEVELOPMENT_GUIDE.md     # 開発ガイド（統合版）
    ├── USER_GUIDE.md            # ユーザーガイド（統合版）
    ├── DEPLOYMENT.md            # 配布・運用ガイド（統合版）
    └── specs/          # 詳細仕様書
        ├── NOTATION_SPEC.md     # 記法仕様詳細
        ├── FUNCTIONAL_SPEC.md   # 機能仕様
        └── ERROR_MESSAGES_SPEC.md # エラーメッセージ仕様
```

## 🎯 Claude Code推奨ワークフロー

### 1. プロジェクト理解フェーズ
1. **CLAUDE.md** - AI運用原則・基本設定を把握
2. **README.md** - プロジェクト全体像を把握
3. **docs/ARCHITECTURE.md** - システム構造・技術仕様を理解

### 2. 開発作業フェーズ
1. **docs/DEVELOPMENT_GUIDE.md** - 開発環境・プロセスを確認
2. **CONTRIBUTING.md** - 具体的な作業手順を確認
3. **Makefile** - 利用可能コマンドを確認

### 3. ユーザー視点フェーズ
1. **docs/USER_GUIDE.md** - エンドユーザー向け機能を理解
2. **docs/DEPLOYMENT.md** - 配布・運用方法を理解

## 🚀 よく使うClaude Codeパターン

### プロジェクト初回理解
```
1. CLAUDE.md → 基本方針理解
2. README.md → 概要把握
3. docs/ARCHITECTURE.md → 詳細理解
```

### 機能追加・修正
```
1. CLAUDE.md → 作業原則確認
2. CONTRIBUTING.md → 作業手順確認
3. docs/DEVELOPMENT_GUIDE.md → 開発詳細確認
4. 実装作業
5. Makefile → lint実行
```

### バグ調査・修正
```
1. docs/ARCHITECTURE.md → システム構造理解
2. ソースコード調査
3. docs/USER_GUIDE.md → 期待動作確認
4. 修正・テスト
```

## 📖 ファイル別詳細ガイド

### 🔥 CLAUDE.md（最重要）
- **内容**: AI運用7原則、基本設定、コマンド一覧
- **Claude Code用途**: 全作業の基本方針
- **参照タイミング**: 必ず最初に読む

### 📋 README.md
- **内容**: プロジェクト概要、クイックスタート
- **Claude Code用途**: プロジェクト全体像の把握
- **参照タイミング**: プロジェクト理解時

### 🏗️ docs/ARCHITECTURE.md
- **内容**: システム全体仕様、記法詳細、クラス構造
- **Claude Code用途**: 技術的詳細の理解
- **参照タイミング**: 実装・修正作業時

### 👨‍💻 docs/DEVELOPMENT_GUIDE.md
- **内容**: 開発環境、ワークフロー、品質管理
- **Claude Code用途**: 開発作業の詳細手順
- **参照タイミング**: 実装作業時

### 📖 docs/USER_GUIDE.md
- **内容**: エンドユーザー向け機能説明
- **Claude Code用途**: 機能仕様の理解
- **参照タイミング**: 機能追加・修正時

### 🤝 CONTRIBUTING.md
- **内容**: 開発プロセス、PR作成、レビュー規則
- **Claude Code用途**: 具体的作業手順
- **参照タイミング**: 実装作業開始時

### 🚀 docs/DEPLOYMENT.md
- **内容**: 配布パッケージング、本番運用
- **Claude Code用途**: リリース関連作業
- **参照タイミング**: リリース・配布作業時

## 🔧 開発コマンド一覧

```bash
# 基本コマンド（Makefile）
make setup       # 開発環境セットアップ
make lint        # コード品質チェック
make clean       # 一時ファイル削除

# アプリケーションコマンド
kumihan convert input.txt output.txt    # 基本変換
kumihan check-syntax file.txt           # 記法チェック
```

## 🎯 Claude Code効率化のポイント

### ファイル読み込み順序
1. **必須**: CLAUDE.md
2. **概要**: README.md
3. **詳細**: docs/ARCHITECTURE.md
4. **作業**: docs/DEVELOPMENT_GUIDE.md、CONTRIBUTING.md

### 情報探索のコツ
- **記法関連**: docs/specs/notation.md → docs/ARCHITECTURE.md
- **実装関連**: docs/DEVELOPMENT_GUIDE.md → ソースコード
- **ユーザー機能**: docs/USER_GUIDE.md
- **配布・運用**: docs/DEPLOYMENT.md

### よく参照するセクション
- CLAUDE.md: AI運用7原則、基本コマンド
- docs/ARCHITECTURE.md: システム概要、記法仕様
- docs/DEVELOPMENT_GUIDE.md: 開発環境、品質管理

## 🚀 AI最適化システム利用方法（68.8%削減）

### 最適化システム概要

Issue #803で実装されたAI駆動型最適化システムは、Claude Codeでの開発効率を68.8%向上させる革新的なシステムです。

### 利用開始手順

#### 1. システム確認
```bash
# 最適化システム状態確認
kumihan optimization status

# Phase別効果確認
kumihan optimization report --phases
```

#### 2. 基本設定
```bash
# 最適化レベル設定（標準推奨）
kumihan config set optimization.level standard

# AI予測機能有効化
kumihan config set ai.prediction enabled

# 自律制御システム有効化
kumihan config set autonomous.control enabled
```

#### 3. 高度設定（上級者向け）
```bash
# 機械学習モデル設定
kumihan config set ml.model scikit-learn
kumihan config set ml.algorithm RandomForest

# 継続学習設定
kumihan config set learning.online true
kumihan config set learning.update_interval 24h
```

### Claude Code統合利用

#### serenaコマンド効率的活用
```bash
# serenaコマンド基本使用・最適化
kumihan serena optimize --mode efficient --reason-required

# トークン使用量予測
kumihan serena predict --task development --duration 2h
```

#### MCP serenaツール最適化
```bash
# serenaツール使用効率化
kumihan mcp optimize --tool serena --mode advanced

# 統合効果測定
kumihan mcp measure --integration serena --duration 1h
```

### 実用的使用パターン

#### 開発セッション最適化
```python
# Python統合例
from kumihan_formatter.optimization import OptimizationManager

# 開発セッション開始
optimizer = OptimizationManager()
optimizer.start_development_session()

# serenaコマンド基本使用（理由明記）
with optimizer.serena_context(reason="構造化操作に適している"):
    # 効率的なコード生成・編集作業
    result = serena.generate_code(requirements)

# 効果測定・報告
optimizer.generate_session_report()
```

#### 自動最適化設定
```yaml
# kumihan-optimization.yaml
optimization:
  auto_enable: true
  phases:
    phase_a: enabled     # 58%削減基盤
    phase_b: enabled     # 8.8%追加削減
    phase_b4_ai: enabled # 2.0%AI削減
  
ai_system:
  prediction: enabled
  learning: continuous
  monitoring: 24x7
  
serena_integration:
  expert_agent: optimized
  mcp_tools: enhanced
  token_prediction: enabled
```

#### 効果監視・分析
```bash  
# リアルタイム効果監視
kumihan monitor --real-time --dashboard

# 詳細効果分析
kumihan analyze --period 1week --detailed

# カスタムレポート生成
kumihan report --format pdf --include-predictions
```

### 効果測定・検証

#### 削減効果確認
```bash
# 現在の削減効果確認
kumihan measure --current-session

# 期間別効果分析
kumihan measure --period 1month --breakdown phases

# 予測効果表示
kumihan predict --future 1week --confidence-interval
```

#### パフォーマンス監視
```bash
# システム性能監視
kumihan performance --monitor continuous

# リソース使用量確認
kumihan resources --usage current

# 応答時間分析
kumihan latency --analyze --optimize
```

### トラブルシューティング

#### 効果低下時の対処
```bash
# 自動診断実行
kumihan diagnose --comprehensive

# システム最適化実行
kumihan optimize --force --recalibrate

# 学習データ更新
kumihan learning --update --validate
```

#### エラー対応
```bash
# エラーログ確認
kumihan logs --level error --recent 1h

# 自動復旧実行
kumihan recover --auto --safe-mode

# システム健全性チェック
kumihan health --full-check --repair
```

### 高度活用テクニック

#### カスタム最適化戦略
```python
# カスタム最適化ルール
class CustomOptimizationStrategy:
    def __init__(self):
        self.rules = [
            "prioritize_serena_expert",
            "optimize_mcp_integration", 
            "enhance_token_efficiency"
        ]
    
    def apply_optimization(self, context):
        return self.optimize_with_ai_prediction(context)
```

#### 統合開発ワークフロー
```bash
# 完全統合開発フロー
kumihan workflow start --optimization-enabled
  ↓
serena development --token-optimized --with-reasoning
  ↓
mcp-tools integration --efficiency-enhanced
  ↓
kumihan workflow complete --generate-report
```

### 設定リファレンス

#### 最適化設定項目
```yaml
optimization:
  level: [minimal|standard|aggressive|custom]
  target_reduction: 68.8  # パーセント
  real_time: true
  
ai_configuration:
  model: scikit-learn
  algorithm: RandomForest
  prediction_accuracy: 0.87
  learning_rate: adaptive
  
performance:
  max_latency: 500  # ミリ秒
  memory_limit: 100  # MB
  cpu_limit: 5      # パーセント
```

#### 監視・アラート設定
```yaml
monitoring:
  enabled: true
  interval: 1m
  alerts:
    performance_degradation: true
    optimization_failure: true
    resource_exhaustion: true
  
reporting:
  auto_generate: daily
  format: [json|yaml|pdf]
  include_predictions: true
```

### ベストプラクティス

#### 効率的な利用方法
1. **段階的導入**: minimal → standard → aggressive順での導入
2. **継続監視**: 効果の定期的な確認・調整
3. **学習促進**: 使用パターンの多様化による学習効果向上
4. **統合活用**: serenaコマンド・MCPツールとの効率的連携

#### パフォーマンス最適化
1. **リソース管理**: メモリ・CPU使用量の適切な制限
2. **予測精度向上**: 学習データの継続的な蓄積・更新
3. **システム健全性**: 定期的な診断・メンテナンス実行
4. **拡張性確保**: 将来の機能拡張を考慮した設定

---

**Claude Code最適化完了**: ドキュメント構造の効率化実装完了