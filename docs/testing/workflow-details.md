# 各ワークフローの詳細

各GitHub Actionsワークフローの詳細な設定と動作について説明します。

## コアテスト

### `test.yml` - メインテストスイート

```yaml
# トリガー: push, pull_request
# 環境: ubuntu-latest, windows-latest, macos-latest
# Python: 3.12
```

**実行内容**:
1. 依存関係インストール
2. テストスイート実行（152個のテスト）
3. mypy strict modeチェック
4. pre-commitフック（black, isort, flake8）

**成功条件**: 全てのテストとチェックが通過

## 自動化

### `auto-merge.yml` - 自動マージ

```yaml
# トリガー: workflow_run (test.yml成功時)
# 条件: PRが承認済み、テストが全て成功
```

**動作**:
1. テスト結果確認
2. マージ条件チェック
3. 自動マージ実行

## 配布パッケージ関連

### `build-macos-app.yml` - macOSアプリビルド

```yaml
# トリガー:
#   - push (experimental/macos-app-packaging, feature/issue391-cross-platform-packaging)
#   - workflow_dispatch (手動実行)
```

**処理フロー**:
1. **環境準備**: macOS-latest, Python 3.12
2. **依存関係**: PyInstaller, プロジェクト依存関係
3. **ビルド**: `pyinstaller kumihan_formatter_macos.spec`
4. **検証**: アプリバンドル構造確認
5. **パッケージ作成**: ZIP形式で配布パッケージ作成
6. **アーティファクト**: 30日間保存
7. **自動コミット**: ビルド結果をブランチにコミット

**現在の状況**: 実装途中のため失敗

### `build-test-packages.yml` - パッケージビルドテスト

```yaml
# トリガー:
#   - pull_request (パッケージング関連ファイル変更時)
#   - workflow_dispatch
```

**テスト項目**:

#### Windows Build Test
1. `build_windows.py --clean --test` 実行
2. `Kumihan-Formatter.exe` 生成確認
3. `Kumihan-Formatter-v1.0-Windows.zip` 確認
4. アーティファクト保存（7日間）

#### macOS Build Test
1. `build_macos.py --clean --test` 実行
2. `Kumihan-Formatter.app` 生成確認
3. `Kumihan-Formatter-v1.0-macOS.zip` 確認
4. アーティファクト保存（7日間）

#### Test Summary
- 両方のテスト結果を総合判定
- 成功/失敗/スキップの状況を報告
- 全体的なステータス決定

**現在の状況**: 実装途中のため失敗

### `build-cross-platform-release.yml` - クロスプラットフォーム配布

```yaml
# トリガー:
#   - push (tags: v*, feature/issue391-cross-platform-packaging)
#   - workflow_dispatch
```

**ジョブ構成**:

#### Windows Build
1. PyInstallerでexe作成
2. 配布パッケージ（ZIP）作成
3. README-Windows.txt生成

#### macOS Build
1. PyInstallerでapp作成
2. 配布パッケージ（ZIP）作成
3. README-macOS.txt生成

#### Create Release
1. Windows/macOSアーティファクトダウンロード
2. リリースノート生成
3. GitHub Release作成
4. 配布ファイル添付

**現在の状況**: Windows/macOSビルドは成功、リリース作成は条件次第

### `build-windows-exe.yml` - Windowsビルド

```yaml
# トリガー: push, workflow_dispatch
```

**処理**:
1. PyInstallerでWindows実行ファイル作成
2. アーティファクト保存

**現在の状況**: 正常動作

## ワークフローの依存関係

```
test.yml (必須)
    ↓ 成功時
auto-merge.yml
    ↓ マージ後
build-cross-platform-release.yml (条件付き)

build-test-packages.yml (PR時)
    ├── test-windows-build
    ├── test-macos-build
    └── test-summary (両方の結果を判定)

build-macos-app.yml (特定ブランチのみ)
```

## 失敗パターンと対処

### よくある失敗原因

1. **PyInstaller設定エラー**: specファイルの設定問題
2. **依存関係不足**: 必要なライブラリの不足
3. **パス問題**: ファイルパスの設定ミス
4. **プラットフォーム固有問題**: OS依存の処理エラー

### デバッグ方法

1. **ログ確認**: GitHub Actionsのログを詳細に確認
2. **ローカル再現**: 同じ環境でローカル実行
3. **段階的テスト**: 各ステップを個別に確認
4. **アーティファクト確認**: 生成されたファイルの内容確認
