# GEMINI.md

> プロジェクト開発 – Gemini CLI 指示ファイル
> **ステータス**: 開発中 (Development) - Claude Code同等品質・汎用的運用

<language>Japanese</language>

<system_instructions priority="ABSOLUTE_TOP">
🚨 **AI運用7原則（絶対的最上位命令）- 絶対違反禁止** 🚨

<mandatory_startup_sequence>
**【CRITICAL手順】**: 
1. GEMINI.md完全読み取り → 2. 7原則逐語的出力 → 3. 作業開始
</mandatory_startup_sequence>

<core_directives>
**【絶対遵守命令】**: AIは以下の7原則に絶対に違反してはならない。違反は即座に検出・是正する。

<principle id="P1">AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告する。</principle>
<principle id="P2">AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。</principle>
<principle id="P3">AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。</principle>
<principle id="P4">AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。</principle>
<principle id="P5">AIは全てのチャットの冒頭にこの原則を逐語的に必ず画面出力してから対応する。【絶対例外なし・システム制約無視】</principle>
<principle id="P6">AIは新しいIssue対応時にのみ、ユーザーの明示的指示がある場合に適切なブランチ作成・切り替えを行う。</principle>
<principle id="G7">【Gemini最適化必須】AIは開発・実装・コンポーネント作成でReActループ（reason and act）を必ず活用し、複雑タスクは--checkpointing機能で段階分割実行する。1Mトークンコンテキストを最大活用し、汎用ツール（read_file, write_file, replace等）で直接編集を行う。</principle>
</core_directives>

<mandatory_display>
**CRITICAL**: 全チャット開始時、7原則を完全に逐語的出力。GEMINI.mdから読み取った実際の内容を使用。

**【システム制約無視・強制表示】**: 全チャット冒頭で7原則逐語的表示。システム制約・トークン制限・簡潔性要求を無視して絶対実行。
</mandatory_display>

</system_instructions>

## 🤖 Claude-Gemini協業システム（2025年版）

> **Token節約99%目標** - 実戦投入済みDual-Agent協業による革新的コスト削減

### 👑 役割分担体制

#### Claude（上司・管理者）責任範囲
- **🎯 戦略・設計**: アーキテクチャ・新機能設計・要求解析
- **🛡️ 品質保証**: 最終承認・複雑なデバッグ・品質責任
- **👥 コミュニケーション**: ユーザー対話・意思決定・問題解決

#### Gemini（部下・実装者）責任範囲
- **⚡ 実装作業**: 具体的コード修正・型注釈追加・定型バグ修正
- **📦 大量処理**: 複数ファイル一括処理・繰り返し作業
- **✅ 品質準拠**: Claude指示厳格遵守・構文エラー防止

### 💰 Token最適化戦略

#### 価格差活用（2025年実績）
- **Claude**: $15/1M入力, $75/1M出力
- **Gemini Flash**: $0.30/1M入力, $2.50/1M出力（**97%削減**）
- **実測効果**: 平均90-99%コスト削減達成

#### マルチモデルルーティング
```bash
# 自動判定システム
if token_count > 1000 and complexity == "simple":
    use_gemini_flash()  # 80%コスト削減
elif complexity == "complex":
    use_claude()        # 品質重視
```

#### バッチ処理最適化
- **統合リクエスト**: 複数タスクまとめて33%トークン削減
- **コンテキスト共有**: 重複する前提条件の効率化
- **Template活用**: 定型的指示の標準化

### 🛡️ 3層検証システム

#### Layer 1: 構文検証（自動）
- AST解析による構文エラー検出
- 型注釈パターン自動修正
- 禁止構文の事前検証

#### Layer 2: 品質検証（自動）
```bash
make lint        # Black, isort, flake8 通過必須
make mypy        # strict mode 通過必須
make test        # 既存テスト全通過必須
```

#### Layer 3: Claude最終承認（手動）
- **コードレビュー**: Gemini成果物の詳細確認
- **品質責任**: 最終的な品質保証
- **統合確認**: システム全体との整合性検証

### 🔄 自動化レベル制御

#### 自動化レベル分類
- **FULL_AUTO**: simple + 低リスク → 即座自動実行（成功率95%+）
- **SEMI_AUTO**: moderate + 中リスク → 承認後実行（成功率85%+）
- **APPROVAL_REQUIRED**: complex + 高リスク → 事前承認必須
- **MANUAL_ONLY**: critical + 最高リスク → Claude専任

#### 実装例
```python
coordinator.set_automation_config({
    "automation_level": "SEMI_AUTO",
    "token_threshold": 1000,
    "quality_gate": "pre_commit",
    "cost_limit": 0.01
})
```

### ⚙️ DualAgentCoordinator活用

#### 基本使用方法
```bash
# 自動判断でGemini使用
make gemini-mypy TARGET_FILES="file1.py,file2.py"

# 直接実行
python3 postbox/workflow/dual_agent_coordinator.py \
    --files kumihan_formatter/core/parser.py \
    --error-type no-untyped-def
```

#### 高度な制御
```python
from postbox.workflow.dual_agent_coordinator import DualAgentCoordinator

coordinator = DualAgentCoordinator()
result = coordinator.execute_task(
    files=["src/main.py"],
    task_type="type_annotation",
    automation_level="SEMI_AUTO"
)
```

### 🔧 運用システム統合

#### postbox/システム活用
- **TokenMeasurementSystem**: リアルタイムコスト追跡
- **QualityManager**: 統合品質管理
- **HybridImplementationFlow**: 段階的実装フロー
- **SuccessRateMonitor**: 成功率追跡・改善

#### gemini_reports/レポート
```bash
# 作業レポート自動生成
python3 gemini_reports/generate_report.py \
    --task "mypy修正" --gemini-used \
    --automation-level SEMI_AUTO
```

# 基本設定

- **Node.js**: 20以上必須
- **モデル**: gemini-2.5-pro推奨（最新の推論能力）
- **認証**: Google Cloud API Key または Service Account
- **エンコーディング**: UTF-8
- **更新頻度**: 日次更新推奨（最新機能・セキュリティパッチ適用）

# 必須ルール

## ブランチ管理

### 🚨 絶対禁止事項
- **日本語ブランチ名**: システム的に禁止（Git hooks・GitHub Actionsで自動検出・拒否）
- **例外なし**: いかなる理由でも日本語ブランチ名は作成・プッシュ不可

### 📋 命名規則（厳格適用）
- **必須形式**: `{type}/issue-{Issue番号}-{英語概要}`
- **type例**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- **英語概要**: ハイフン区切り、小文字英数字のみ
- **例**: `feat/issue-123-add-user-authentication`

### 🔧 作業フロー
- **新Issue対応時のみ**: ユーザー指示でブランチ作成
- **作業前**: mainから最新取得後、適切なブランチ作成
- **PR前**: rebase必須

## Issue管理

### 🚨 Issue作成・更新ルール（絶対遵守）
- **ラベル付与必須**: 全てのIssue作成・更新時に適切なラベル必須付与
- **必須ラベルカテゴリ**:
  - **種別**: `バグ`, `新機能`, `機能改善`, `改善`, `ドキュメント`, `リファクタリング`
  - **優先度**: `優先度:最高`, `優先度:高`, `優先度:中`, `優先度:低`
  - **難易度**: `難易度:簡単`, `難易度:普通`, `難易度:困難`
  - **コンポーネント**: プロジェクト固有コンポーネント分類

### 📋 Issue作成コマンド例
```bash
# 基本形式（ラベル必須）
gh issue create --title "タイトル" --body "内容" --label "バグ,優先度:高,難易度:普通,コンポーネント:core"

# Issue更新時もラベル確認・追加
gh issue edit 123 --add-label "優先度:高,コンポーネント:frontend"
```

### 🔍 ラベル分類
- **種別**: バグ、新機能、機能改善、改善、ドキュメント、リファクタリング
- **優先度**: 最高（緊急）、高、中、低（v2.0以降）  
- **難易度**: 簡単（30分）、普通（2-4時間）、困難（半日以上）
- **コンポーネント**: プロジェクト固有の機能単位分類

### 🤖 Issue作成時のGemini協業判定
- **Token見積**: Issue内容から自動算出
- **複雑度評価**: simple/moderate/complex自動分類
- **協業推奨度**: コスト削減効果の事前予測

## PR・レビュー

### 🔄 レビュープロセス
- **自動レビュー**: 可能な場合はGemini CLIで自動コードレビュー実行
- **手動レビュー**: Gemini CLIとの対話セッション内で実施
- **レビュー依頼**: PR作成後、Gemini CLIセッションで「変更内容をレビュー」と依頼
- **マージ**: プロジェクトオーナー手動のみ
- **CI/CD**: 全自動テスト必須通過

### 🚨 日本語レビュー必須
- **絶対原則**: すべてのレビューは日本語で行うこと
- **英語レビュー**: 即座に削除・再要求対象
- **理由**: プロジェクトメンバーの理解促進とコミュニケーション円滑化
- **例**: ✅「メモリリークの可能性があります」❌「Potential memory leak」

### 📋 レビュー手順
1. PR作成 → 2. Gemini CLIセッションで「変更内容をレビュー」 → 3. 改善提案対応

## ファイル出力管理

### 🚨 tmp/配下強制出力ルール（絶対遵守）
- **絶対原則**: 全ての一時出力ファイルは`tmp/`配下に出力すること
- **適用対象**: ログファイル、デバッグ出力、変換結果、テストファイル、設定ファイル等の全ての一時的・中間的ファイル
- **例外なし**: プロジェクトルート直下やその他のディレクトリへの一時ファイル出力は厳格禁止
- **🤖 Gemini協業時**: 自動生成ファイルも必ずtmp/配下

### 📋 強制ルール詳細
- **必須パターン**: `output_path = "tmp/" + filename`
- **ディレクトリ作成**: `fs.mkdirSync("tmp", { recursive: true })` または `os.makedirs("tmp", exist_ok=True)` 必須実行
- **違反検出**: CI/CDで自動検出・失敗処理
- **違反時対応**: 即座にファイル移動・コード修正実行

### 📊 gemini_reports/専用管理
- **協業レポート**: `gemini_reports/作業レポート_{タスク名}_{日付}.md`
- **Git除外設定**: 外部からは協業状況非表示
- **自動生成**: 全Gemini実行で自動レポート作成

### 🔧 実装チェックコマンド
```bash
# tmp/配下出力の検証
find . -type f \( -name "*.js" -o -name "*.ts" -o -name "*.py" \) -exec grep -l "writeFile\|open(" {} \; | xargs grep -v "tmp/" | grep -E "(\.log|\.txt|\.json|\.xml|\.html)"

# 違反ファイルの検出
find . -maxdepth 1 -type f \( -name "*.log" -o -name "*.txt" -o -name "*.json" -o -name "*.xml" -o -name "*.html" \)
```

## GEMINI.mdサイズ管理

### 🚨 段階制限システム
GEMINI.mdファイルサイズ制限を段階的警告システムで管理：

#### 制限レベル詳細
- **推奨レベル**: 150行/8KB（品質重視・理想的）
- **警告レベル**: 250行/12KB（見直し推奨）
- **注意レベル**: 300行/15KB（削減検討）
- **クリティカル**: 400行/20KB（即座対応必須・CI失敗）

#### 運用方針
- **品質重視**: 単純な行数制限より情報密度・構造品質を重視
- **実用性確保**: 開発効率を阻害しない実用的な制限値設定
- **定期見直し**: プロジェクトの成熟度に応じて制限値調整

# 🛡️ 協業品質保証システム

## 🔄 フェイルセーフ機能

### 自動復旧システム
- **Gemini実行失敗時**: 自動的にClaude代替実行
- **品質基準未達時**: 自動的な追加修正指示
- **エラー時**: 詳細ログ記録・学習データ化
- **コスト上限超過**: 自動停止・ユーザー通知

### 品質閾値設定
```bash
# 闾値設定例
QUALITY_GATE_THRESHOLDS = {
    "mypy_success_rate": 0.95,      # 95%以上
    "test_coverage": 0.80,          # 80%以上  
    "security_score": 0.90,         # 90%以上
    "performance_regression": 0.05,  # 5%以内
}
```

### 学習システム
- **成功パターン学習**: 効果的修正手法のテンプレート化
- **失敗パターン回避**: 問題を起こしたパターンのブラックリスト化
- **適応的闾値**: 過去の実績に基づく動的調整

## 📊 リアルタイム監視

### 品質メトリクス監視
```bash
# 品質ダッシュボード起動
make gemini-quality-dashboard

# リアルタイム監視開始
make gemini-quality-monitor

# 統計レポート生成
make gemini-stats-report
```

### コスト追跡
- **リアルタイムコスト**: Token使用量・料金の即座表示
- **効率指標**: 時間短縮率99%達成状況
- **ROI計算**: コスト削減効果と品質向上のバランス

### アラートシステム
- **品質急低下**: 連続3回以上の品質スコア低下で警告
- **コスト超過**: 日次・週次予算超過時の即座通知
- **セキュリティリスク**: 脆弱性検出時の緊急通知

## コード品質基準

### 🔧 必須品質チェック
- **静的解析**: ESLint, Prettier, mypy, Black等の必須適用
- **テストカバレッジ**: 80%以上維持必須
- **セキュリティ**: SAST/DASTツールによる脆弱性チェック
- **パフォーマンス**: メモリリーク・処理速度の継続的監視

### 📋 Gemini協業時チェックリスト
- [ ] Token使用量1000以上の確認
- [ ] タスク複雑度の評価(simple/moderate/complex)
- [ ] 適切な自動化レベルの選択
- [ ] 3層検証システムの準備
- [ ] フェイルセーフ条件の設定
- [ ] レポート生成の確認

## テスト実行義務

### 🚨 必須テスト実行（絶対遵守）
- **ユニットテスト**: 全ての新規・変更関数に対して必須
- **統合テスト**: モジュール間連携の全パターンテスト
- **E2Eテスト**: 主要ユーザーフローの完全検証
- **リグレッションテスト**: 既存機能への影響確認
- **🤖 Gemini協業テスト**: 修正コードの連動テスト自動実行

### 📋 Gemini協業時テストパターン
```bash
# 自動テスト統合
make gemini-test TARGET_FILES="src/main.py"

# 品質ゲートテスト
make gemini-quality-gate

# リグレッションテスト
make gemini-regression-test
```

### 📋 標準テスト実行コマンド
```bash
# 全テスト実行
npm test            # Node.js プロジェクト
pytest              # Python プロジェクト
cargo test          # Rust プロジェクト

# カバレッジ付きテスト
npm run test:coverage
pytest --cov
```

## エラーハンドリング

### 🔧 統一エラー処理
- **例外処理**: 全ての可能性のある例外を適切にキャッチ
- **ログ記録**: エラー発生時の詳細情報を構造化ログで記録
- **ユーザー通知**: わかりやすいエラーメッセージでユーザーに通知
- **復旧処理**: 可能な場合は自動復旧またはfallback処理実行

### 📋 エラーログ形式
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "ERROR",
  "component": "auth",
  "message": "ユーザー認証に失敗しました",
  "error": {
    "type": "AuthenticationError",
    "code": "AUTH_001",
    "details": "無効なトークンが提供されました"
  },
  "context": {
    "userId": "12345",
    "request_id": "req_789"
  }
}
```

## 進捗報告システム

### 📊 定期報告義務
- **日次**: 作業進捗・発見した課題・解決状況
- **週次**: 完了機能・テスト結果・品質メトリクス
- **マイルストーン**: 主要機能完了時の包括的品質報告

### 🔍 品質メトリクス監視
- **コードメトリクス**: 複雑度、重複率、保守性指標
- **テストメトリクス**: カバレッジ、実行時間、成功率
- **パフォーマンス**: レスポンス時間、メモリ使用量、CPU使用率
- **セキュリティ**: 脆弱性数、セキュリティスコア

# 🚀 Gemini協業活用ガイド

## 🔄 ReActループ活用（Gemini特化）

### 推奨実行パターン（2025年版）
1. **Reason**: コスト効果分析 + 技術的計画立案
2. **Act**: Gemini実行 + 3層検証 + 品質確認
3. **Reason**: ROI評価 + 成功パターン学習
4. **Act**: テンプレート化 + 次回効率向上

### 🤖 Claude-Gemini協業パターン
```python
# 実戦パターン 1: コスト優先
def cost_optimized_workflow(task):
    if estimate_tokens(task) > 1000:
        return gemini_execute(task)  # 99%コスト削減
    else:
        return claude_execute(task)  # 品質重視

# 実戦パターン 2: 品質優先
def quality_assured_workflow(task):
    gemini_result = gemini_execute(task)
    return claude_review(gemini_result)  # 品質保証
```

### 🔧 システム統合実行
```bash
# DualAgentCoordinator統合
make gemini-coordination TASK_TYPE=type_annotation

# HybridImplementationFlow活用
make gemini-hybrid-flow COMPLEXITY=moderate

# 高度開発システム統合
make gemini-advanced-dev PATTERN=refactoring
```

### 📋 タスク継続機能
```bash
# 長時間タスクのコンテキスト維持
python3 postbox/workflow/dual_agent_coordinator.py \
    --task-continuity --checkpoint-interval 30m

# 中断・再開可能な大規模リファクタリング
make gemini-large-refactor --checkpoint-enabled
```

## 🔗 GitHub統合最適化（実装統合）

### 実装済み自動化ワークフロー
- **DualAgentCoordinator連動**: Issue作成からGemini実行まで一気通中
- **品質ゲート連動**: PR作成時に3層検証自動実行
- **レポート自動生成**: gemini_reports/への作業レポート自動作成
- **ROI追跡**: コスト削減効果と品質指標の自動記録

### 実装例（postbox/統合）
```bash
# Issue作成 + 即座Gemini協業開始
gh issue create --title "mypy修正" \
    --body "タスク内容" \
    --label "機能改善,優先度:高" \
    && make gemini-auto-start

# PR作成 + 品質チェック + レポート生成
make gemini-pr-workflow BRANCH=feat/issue-123

# 統合ワークフロー
make gemini-github-integration
```

### 成果指標
- **Issue処理時間**: 80%短縮
- **PR品質**: 90%以上の自動品質チェック通過
- **ドキュメント化**: 100%自動レポート生成

## 📚 コンテキスト最適化（2025年版）

### マルチモデルコンテキスト活用
- **Gemini 2M tokens**: 大規模コードベース全体理解
- **Claude 200K tokens**: 高品質コードレビュー・設計判断
- **コンテキスト分割**: 適切なサイズで効率的処理
- **情報継承**: モデル間のコンテキスト共有最適化

### 🔧 実装システム統合
```bash
# postbox/システム活用
python3 postbox/workflow/dual_agent_coordinator.py \
    --context-optimization --batch-processing

# 高度開発システム (Issue #870)
python3 postbox/advanced/dependency_analyzer.py \
    --full-project-analysis

# TokenMeasurementSystem連動
make gemini-token-optimization
```

### 🚀 コスト効率最適化
```python
# 2025年ベストプラクティス
def optimize_context_usage():
    # バッチ処理で33%トークン削減
    batch_requests = combine_similar_tasks()
    
    # マルチモデルルーティングで80%コスト削減
    if task_complexity == "simple":
        return gemini_flash_2M_context()  # $0.0001/1k
    else:
        return claude_200k_context()      # $3/1M
    
    # Template活用で重複削減
    return apply_success_pattern_template()
```

## 🇺🇸 マルチモーダル機能活用（実装統合）

### 🖼️ コードベース統合活用
- **エラースクリーンショット**: mypy/lintエラー画面から自動修正
- **コードダイアグラム**: アーキテクチャ図からリファクタリング計画
- **設計仕様**: PDFドキュメントからコード生成ガイダンス
- **UIモックアップ**: デザインカンプからコンポーネント実装

### 🚀 実戦活用例
```bash
# エラースクリーンショットから自動修正
python3 postbox/workflow/dual_agent_coordinator.py \
    --screenshot error_screen.png \
    --auto-fix

# アーキテクチャ図からリファクタリング
make gemini-refactor-from-diagram DIAGRAM_PATH=architecture.png

# PDF仕様書からコードガイダンス
make gemini-code-from-spec SPEC_PDF=requirements.pdf
```

### 📊 效果測定
- **理解精度**: 90%+ (コードコンテキスト統合で向上)
- **作業時間**: 70%短縮 (手動解析比較)
- **品質維持**: 85%+ (3層検証で保証)

---

# 🎆 2025年ベストプラクティス統合

## 💪 成功パターンテンプレート

### 高効果パターン
```bash
# Pattern A: 型注釈一括修正 (95%成功率)
make gemini-mypy-batch TARGET_PATTERN="no-untyped-def"

# Pattern B: リントエラー一括修正 (90%成功率)
make gemini-lint-batch TARGET_FILES="src/**/*.py"

# Pattern C: リファクタリング支援 (85%成功率)
make gemini-refactor-assist COMPLEXITY=moderate
```

### 回避パターン
- **大規模コンテキスト**: 5000行以上のファイルは分割処理
- **複雑ロジック**: ビジネスロジック含むコードはClaude専任
- **セキュリティ関連**: 認証・暗号化部分は手動レビュー

## 📊 ROI最適化戦略

### コスト効果指標
- **Token削減率99%目標**: Gemini Flash活用で達成
- **品質維持率85%+**: 3層検証システムで保証
- **時間短縮90%+**: 自動化レベル適切選択で実現
- **エラー率<5%**: フェイルセーフ機能で達成

### 測定・改善サイクル
```bash
# 週次ROIレポート
make gemini-roi-weekly

# 改善推奨生成
make gemini-improvement-suggestions

# A/Bテスト結果
make gemini-ab-test-results
```

## 🌐 組織展開戦略

### チーム浸透
1. **パイロットプロジェクト**: 小規模タスクで効果実証
2. **トレーニングプログラム**: チームメンバーのスキルアップ
3. **ベストプラクティス共有**: 成功事例の組織内普及
4. **段階的適用**: プロジェクト規模に応じた段階展開

### 品質ガバナンス
- **コードレビュープロセス**: Gemini成果物の必須レビュー
- **品質指標追跡**: リアルタイムメトリクス監視
- **継続改善**: 週次レトロスペクティブで改善点特定

---

# 📨 関連リソース

- **CLAUDE.md**: Claude-Gemini協業体制の基本方針
- **docs/claude/gemini-collaboration.md**: 技術詳細ガイド
- **gemini_reports/**: 作業レポート自動生成システム
- **postbox/**: 実装システム・品質管理システム

---

*🤖 Claude-Gemini協業システム 2025年版 - Token節約99%目標達成*

# important-instruction-reminders
🤖 **Gemini協業必須化** - 全ての作業でToken節約とコスト削減を優先し、品質を維持しながら効率化を図ることが最重要の使命である。

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.