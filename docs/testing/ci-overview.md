# CI/CDパイプライン概要

Kumihan-FormatterのCI/CD構成と各ワークフローの役割について説明します。

## ワークフロー構成

### 🔧 **コアテスト**（必須）

#### `test.yml` - メインテストスイート
- **目的**: コード品質と動作保証
- **実行環境**: Ubuntu、Windows、macOS（Python 3.12）
- **テスト内容**:
  - 全152個のテストケース
  - mypy strict modeチェック
  - pre-commitフック（black, isort, flake8）
- **判定**: このテストが通過しないとマージ不可

### 🤖 **自動化**

#### `auto-merge.yml` - 自動マージ機能
- **目的**: コアテストが成功した場合の自動マージ
- **条件**: `test.yml`が全て成功
- **動作**: PR419で正常動作確認済み

### 🚀 **配布パッケージ関連**（実験的・Issue #391対応）

#### `build-macos-app.yml` - macOSアプリビルド
- **目的**: PyInstallerでmacOSアプリ(.app)作成
- **機能**:
  - 配布ZIP生成
  - 自動コミット
  - アーティファクト保存（30日間）
- **実行条件**:
  - `experimental/macos-app-packaging`ブランチ
  - `feature/issue391-cross-platform-packaging`ブランチ
- **現状**: 実装途中のため失敗中

#### `build-test-packages.yml` - パッケージビルドテスト
- **目的**: PR時のパッケージング関連ファイル変更検証
- **テスト対象**:
  - Windows `.exe`ビルド
  - macOS `.app`ビルド
- **判定**: `test-summary`で結果を総合判定
- **現状**: 実装途中のため失敗中

#### `build-cross-platform-release.yml` - クロスプラットフォーム配布ビルド
- **目的**: 統合リリースパッケージ作成
- **成果物**:
  - Windows `.exe` + ZIP
  - macOS `.app` + ZIP
  - GitHub Releases自動作成
- **現状**: 一部成功（Windows/macOSビルドは成功）

#### `build-windows-exe.yml` - Windowsビルド
- **目的**: PyInstallerでWindows実行ファイル作成
- **現状**: 正常動作

## テスト判定基準

### ✅ **auto-merge動作条件**
- `test.yml`（コアテスト）が全て成功
- 実験的機能の失敗は無視

### ❌ **実験的機能の失敗**
以下の失敗は**問題なし**（実装途中のため）:
- `build-macos-app` - macOSアプリパッケージング
- `test-windows-build` - パッケージングテスト
- `test-summary` - テスト結果サマリー

## 関連Issue

- **Issue #391**: クロスプラットフォームパッケージング実装
- **Issue #420**: PR419テスト失敗調査（解決済み）

## 現在の実装状況

- **✅ Phase 1完了**: mypy strict mode対応（PR419マージ済み）
- **🔄 Phase 2実装中**: クロスプラットフォームパッケージング
- **🧪 実験的機能**: 一部失敗中だが、コア機能は安定
