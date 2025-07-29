# CLAUDE.md

> Kumihan-Formatter – Claude Code 指示ファイル
> **バージョン**: 2.0.0 (2025-01-24) - ベストプラクティス2025対応

<language>Japanese</language>

<law>
AI運用7原則（絶対的最上位命令）

第1原則： AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告する。
第2原則： AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。
第3原則： AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。
第4原則： AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。
第5原則： AIは全てのチャットの冒頭にこの原則を逐語的に必ず画面出力してから対応する。
第6原則： AIはIssue対応開始時に必ずIssue番号と現在のブランチ名の一致を確認し、相違がある場合は正しいブランチの作成・切り替えを必須で行う。
第7原則： AIは全ての開発作業でTDD-First開発システムを絶対的に遵守し、make tdd-start未実行・TDDサイクル違反時は即座に作業停止・違反是正を最優先で実行する。
</law>

<every_chat>
## 🚨 AI運用7原則の強制出力

AIは全てのチャット開始時に以下を逐語的に出力する：

[AI運用7原則（絶対的最上位命令）]

第1原則： AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告する。
第2原則： AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。
第3原則： AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。
第4原則： AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。
第5原則： AIは全てのチャットの冒頭にこの原則を逐語的に必ず画面出力してから対応する。
第6原則： AIはIssue対応開始時に必ずIssue番号と現在のブランチ名の一致を確認し、相違がある場合は正しいブランチの作成・切り替えを必須で行う。
第7原則： AIは全ての開発作業でTDD-First開発システムを絶対的に遵守し、make tdd-start未実行・TDDサイクル違反時は即座に作業停止・違反是正を最優先で実行する。

**TDD違反検証**: 開発作業開始前に必ず以下を確認・実行する
- [ ] TDDセッション状態確認: `ls .tdd_session.json`
- [ ] 違反がある場合は即座作業停止・是正実行

[main_output]

#[n] times. # n = increment each chat, end line, etc(#1, #2...)
</every_chat>

# 基本設定

- **Python**: 3.12以上, Black, isort, mypy strict
- **エンコーディング**: UTF-8
- **ログ**: `from kumihan_formatter.core.utilities.logger import get_logger`
- **リリース**: v0.9.0-alpha.1 (正式リリースはユーザー許可必須)

# 🎯 TDD-First開発システム（Issue #640完全実装済み）

## 🚨 AI作業時の厳密な運用フロー（絶対遵守）

### 第1段階: 開発開始前の必須確認
**AI MUST DO**:
1. Issue番号とブランチ名の完全一致確認（第6原則）
2. TDDセッション開始の必須実行
3. 既存コードベースの理解・分析完了確認

```bash
# 必須実行順序
make tdd-start ISSUE_NUMBER=<Issue番号>
# → セッション開始成功まで他作業禁止
```

### 第2段階: TDD-First開発の厳密実行
**絶対禁止事項**:
- ❌ テストを書く前にプロダクションコードを書くこと
- ❌ Red→Green→Refactorサイクルの省略・順序変更
- ❌ 複数機能の同時実装
- ❌ TDDセッション外でのコード変更

**必須実行フロー**:
```bash
# Phase 1: RED（必ず最初に失敗するテストを作成）
make tdd-red
# → 失敗確認後のみ次段階進行可能

# Phase 2: GREEN（最小限実装のみ）
make tdd-green  
# → テスト成功確認後のみ次段階進行可能

# Phase 3: REFACTOR（品質向上・重複排除）
make tdd-refactor
# → 品質確認後のみ次機能開発或いはサイクル完了可能
```

### 第3段階: 品質保証の強制実行
```bash
# セキュリティテスト（100%パス必須）
make tdd-security

# 最終品質チェック・完了確認
make tdd-complete
```

### 第4段階: コミット前の厳密チェック
**AI必須確認項目**:
- [ ] TDDサイクル完了記録の存在確認
- [ ] テストカバレッジ基準達成確認（Critical: 90%, Important: 80%）
- [ ] セキュリティテスト100%パス確認
- [ ] 全テストスイート通過確認
- [ ] TDD履歴（Red→Green→Refactor）の証跡確認

## 🛡️ TDD強制システム・違反防止

### AI作業開始時の自動チェック
```bash
# 作業開始前に必ず実行
make tdd-enforce
# → 違反検出時は作業停止・修正必須
```

### TDD品質要求（強制・例外なし）
- **Critical Tier**: 90%カバレッジ必須（GitHub Actions自動ブロック）
- **Important Tier**: 80%カバレッジ推奨
- **セキュリティテスト**: 100%パス必須（マージブロック対象）
- **TDD履歴**: Red→Green→Refactor記録必須

### TDD違反時の自動対応
- GitHub Actions による自動マージブロック
- TDD未実施PRは自動却下
- カバレッジ未達成時の自動CI失敗
- セキュリティテスト失敗時の即座ブロック

## 🔄 AI作業中の継続チェック
### 各フェーズ完了時の必須確認
```bash
# Red Phase完了確認
python3 scripts/tdd_cycle_manager.py red --verify

# Green Phase完了確認  
python3 scripts/tdd_cycle_manager.py green --verify

# Refactor Phase完了確認
python3 scripts/tdd_cycle_manager.py refactor --verify
```

### リアルタイム品質監視
```bash
# 品質状況リアルタイム確認
python3 scripts/realtime_quality_monitor.py

# ティア別品質ゲート確認
python3 scripts/tiered_quality_gate.py
```

## ⚠️ 緊急時・例外処理

### TDD違反検出時の対応
1. **即座作業停止**: 現在の変更を一時保存
2. **違反内容確認**: `make tdd-enforce` で詳細確認
3. **修正実施**: TDDプロセスに従った修正実行
4. **再検証**: 全チェック項目の再確認実行

### システム不具合時の対応
1. **ログ確認**: `.tdd_logs/` 配下の詳細ログ確認
2. **状態復元**: `python3 scripts/tdd_session_manager.py restore`
3. **緊急時スキップ**: 正当な理由がある場合のみ `--emergency-skip` オプション使用

## 📝 AI作業記録・証跡管理

### 必須記録事項
- TDDセッション開始・終了時刻
- Red→Green→Refactor各フェーズの実行記録
- テスト追加・修正の詳細ログ
- カバレッジ変化の記録
- セキュリティテスト実行結果

### 作業完了時の必須報告
```markdown
## TDD-First開発作業完了報告
- Issue番号: #XXX
- TDDセッション: [開始時刻] → [終了時刻]
- Red→Green→Refactorサイクル: X回実行
- 最終カバレッジ: Critical XXX%, Important XXX%
- セキュリティテスト: 全項目PASS
- 品質ゲート: PASS/FAIL
```

## 🔍 適当作業防止チェックリスト

### AI作業開始前チェック（絶対必須）
- [ ] Issue番号がブランチ名と完全一致している
- [ ] `make tdd-start ISSUE_NUMBER=XXX` を実行した
- [ ] TDDセッション開始成功メッセージを確認した
- [ ] 既存コードの理解・関連ファイル分析を完了した
- [ ] 要求仕様を正確に理解した

### 各開発フェーズでのチェック
#### Red Phase（テスト失敗段階）
- [ ] プロダクションコードを書く前にテストを作成した
- [ ] テストが期待通り失敗することを確認した
- [ ] `make tdd-red` が正常実行された
- [ ] 失敗理由が明確で意図的である

#### Green Phase（最小実装段階）
- [ ] テストを通すための最小限実装のみを行った
- [ ] 過度な設計・最適化を避けた
- [ ] `make tdd-green` が正常実行された
- [ ] 全テストがパスすることを確認した

#### Refactor Phase（品質向上段階）
- [ ] テストを壊すことなくリファクタリングを実行した
- [ ] コード重複の排除を行った
- [ ] `make tdd-refactor` が正常実行された
- [ ] 品質が実際に向上したことを確認した

### 最終完了前チェック（例外なし必須）
- [ ] `make tdd-security` が100%パスした
- [ ] `make tdd-complete` が正常完了した
- [ ] TDDサイクル記録がログに残っている
- [ ] カバレッジ基準を満たしている
- [ ] 全テストスイートが通過している
- [ ] コミットメッセージにTDD記録を含めた

### 緊急時チェック
- [ ] TDD違反を検出した場合、即座に作業停止した
- [ ] `make tdd-enforce` で違反内容を確認した
- [ ] 適切な修正プロセスを実行した
- [ ] 再検証で全チェック項目をクリアした

## ❌ 禁止事項（絶対に行ってはいけない）
1. **TDDセッション外でのコード変更**
2. **テスト作成前のプロダクションコード実装**
3. **Red→Green→Refactorサイクルの省略・順序変更**
4. **複数機能の同時開発**
5. **品質チェックのスキップ**
6. **セキュリティテストの無視**
7. **カバレッジ基準未達成でのコミット**
8. **TDDセッション記録なしの作業完了**

# 必須ルール

## ブランチ管理
- **命名**: `feat/issue-{Issue番号}-{概要}`
- **作業前**: mainから最新取得、正しいブランチ作成
- **PR前**: rebase必須

## 品質管理（Issue #583対応 - 現実的基準）

### ティア別品質基準（Issue #640更新）
- **Critical Tier**: Core機能・Commands（テストカバレッジ90%必須）
- **Important Tier**: レンダリング・バリデーション（80%推奨）
- **Supportive Tier**: ユーティリティ・キャッシング（統合テストで代替可）
- **Special Tier**: GUI・パフォーマンス系（E2E・ベンチマークで代替）

### 品質チェック
- **新品質ゲート**: `python scripts/tiered_quality_gate.py`
- **段階的改善**: `python scripts/gradual_improvement_planner.py`
- **根本原因分析**: `python scripts/tdd_root_cause_analyzer.py`

### 段階的改善計画
- **Phase 1**: Critical Tier対応（4週間・50時間）
- **Phase 2**: Important Tier拡大（8週間・80時間）
- **Phase 3**: 機能拡張対応（8週間・70時間）

## PR・レビュー

### 🔄 レビュープロセス変更（2025-07-29更新）
- **自動レビュー**: 無効化完了（claude-code-review.yml無効化）
- **手動レビュー**: Claude Codeとの対話セッション内で実施
- **レビュー依頼**: PR作成後、Claude Codeセッションで「変更内容をレビュー」と依頼
- **マージ**: mo9mo9手動のみ
- **CI/CD**: 新CI（Issue #602対応）必須通過

### 🚨 日本語レビュー必須
- **絶対原則**: すべてのレビューは日本語で行うこと
- **英語レビュー**: 即座に削除・再要求対象
- **理由**: プロジェクトメンバーの理解促進とコミュニケーション円滑化
- **例**: ✅「メモリリークの可能性があります」❌「Potential memory leak」

### 📋 レビュー手順
1. **PR作成**: 通常通りPR作成
2. **レビュー依頼**: Claude Codeセッションで「変更内容をレビュー」
3. **詳細分析**: 技術品質・設計・実装の包括的評価
4. **改善提案**: 具体的な修正提案・推奨事項提示

# 基本コマンド

```bash
# TDD-First開発システム（Issue #640実装済み）
make tdd-start ISSUE_NUMBER=640  # TDDセッション開始
make tdd-red                     # Red Phase実行
make tdd-green                   # Green Phase実行  
make tdd-refactor                # Refactor Phase実行
make tdd-security                # セキュリティテスト実行
make tdd-complete                # TDDサイクル完了

# 従来コマンド
make test          # テスト実行
make lint          # リントチェック
make pre-commit    # コミット前チェック
kumihan convert input.txt output.txt  # 基本変換
```

# GitHub Actions（Issue #602最適化）

**新シンプル構成**:
- **`ci.yml`**: 必須CI（Black/isort/flake8/pytest/mypy）
- **`quality-optional.yml`**: オプション品質チェック（週次実行）
- **`claude.yml`**: Claude自動レビュー

**最適化効果**: 実行時間15分→5分、複雑度大幅削減

# qcheck系コマンド（Issue #578）

Claude Code品質チェック用ショートカット:

```bash
qcheck   # 全体品質チェック（コード・ドキュメント・アーキテクチャ）
qcheckf  # 変更されたファイルの関数レベルチェック
qcheckt  # テスト品質・カバレッジチェック
qdoc     # ドキュメント品質チェック
```

# 開発ツール（統合版）

## 開発者向けツール
- **テスト実行**: `pytest`, `make test`
- **依存関係管理**: `pip install -e ".[dev]"`
- **開発支援ツール**: `dev/tools/` 配下に配置
- **トラブルシューティング**: 仮想環境・モジュール・パーミッション対応

## 記法ツール（自動化システム）
- **記法検証**: `python -m kumihan_formatter check-syntax file.txt`
- **自動修正**: `dev/tools/syntax_fixer.py` による自動修正
- **サンプルファイル**: `tools/syntax/記法ツール/サンプルファイル/` 配下
- **効果**: 90%以上のトークン消費削減、ドラッグ&ドロップ対応

## クイックリファレンス

### 緊急時対応フロー
```bash
# 1. エラー確認
make test

# 2. 品質チェック
qcheck

# 3. 記法問題修正
python -m kumihan_formatter check-syntax file.txt

# 4. 依存関係修正
pip install -e ".[dev]"
```

### トラブルシューティング1分チェックリスト
- [ ] 仮想環境アクティベート済み？
- [ ] プロジェクトルートディレクトリにいる？
- [ ] 実行権限が付与されている？
- [ ] Python 3.12以上を使用？

# 記法仕様

- **基本**: `;;;装飾名;;; 内容 ;;;`
- **脚注**: `((content))` → 巻末移動
- **傍注**: `｜content《reading》` → ルビ表現

# 詳細ドキュメント

- **基本指示**: [PREAMBLE.md](PREAMBLE.md)
- **開発詳細**: [docs/dev/DEVELOPMENT_GUIDE.md](docs/dev/DEVELOPMENT_GUIDE.md) - 包括的開発ガイド
- **技術仕様**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - システム全体アーキテクチャ  
- **ユーザーガイド**: [docs/user/docs/USER_GUIDE.md](docs/user/docs/USER_GUIDE.md) - エンドユーザー向け完全ガイド

# AI防止システム

## 回答前チェック
- CLAUDE.md確認済み？
- 推測要素はゼロ？
- 文脈理解は正確？
- 作業計画は報告済み？

## 停止トリガー
- プロジェクト指示と矛盾
- 不明確で推測が必要
- 複数解釈が可能
- Issue/PR番号とブランチ名不一致

---
**重要**: 詳細情報は上記リンク先を参照
