# パッケージング・配布ガイド

> Kumihan-Formatter のクロスプラットフォーム配布パッケージング

## 概要

Kumihan-Formatterは以下のプラットフォームで実行可能形式のファイルとして配布されます：

- **Windows**: `.exe` 形式の実行ファイル
- **macOS**: `.app` 形式のアプリケーションバンドル

## 🏗️ ビルド方法

### Windows (.exe)

```bash
# 仮想環境をアクティベート
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate     # Windows

# 依存関係をインストール
pip install pyinstaller

# ビルド実行
python scripts/build/build_windows.py --clean --test
```

**生成ファイル:**
- `dist/Kumihan-Formatter.exe` - 実行ファイル
- `dist/Kumihan-Formatter-v1.0-Windows.zip` - 配布パッケージ

### macOS (.app)

```bash
# 仮想環境をアクティベート
source .venv/bin/activate

# 依存関係をインストール
pip install pyinstaller

# ビルド実行
python scripts/build/build_macos.py --clean --test
```

**生成ファイル:**
- `dist/Kumihan-Formatter.app` - アプリケーションバンドル
- `dist/Kumihan-Formatter-v1.0-macOS.zip` - 配布パッケージ

## 🤖 自動ビルド（CI/CD）

### GitHub Actions ワークフロー

#### 1. テストビルド
- **ファイル**: `.github/workflows/build-test-packages.yml`
- **トリガー**: Pull Request、手動実行
- **目的**: 開発中のパッケージビルドテスト

```bash
# 手動実行
gh workflow run "Test Package Builds"
```

#### 2. リリースビルド
- **ファイル**: `.github/workflows/build-cross-platform-release.yml`
- **トリガー**: タグプッシュ、手動実行
- **目的**: 本番リリース用パッケージ生成

```bash
# 手動実行（バージョン指定）
gh workflow run "Cross-Platform Release Build" -f version=v1.0.0 -f create_release=true
```

#### 3. 個別プラットフォームビルド
- **Windows**: `.github/workflows/build-windows-exe.yml`
- **macOS**: `.github/workflows/build-macos-app.yml`
- **トリガー**: 実験的ブランチでの開発・テスト

## 📦 配布パッケージ構成

### Windows パッケージ
```
Kumihan-Formatter-v1.0-Windows.zip
├── Kumihan-Formatter.exe     # 実行ファイル
└── README-Windows.txt        # インストール説明書
```

### macOS パッケージ
```
Kumihan-Formatter-v1.0-macOS.zip
├── Kumihan-Formatter.app/    # アプリケーションバンドル
│   ├── Contents/
│   │   ├── Info.plist
│   │   ├── MacOS/
│   │   └── Resources/
└── README-macOS.txt          # インストール説明書
```

## ⚙️ 設定ファイル

### PyInstaller 設定

#### Windows用
- **ファイル**: `tools/packaging/kumihan_formatter.spec`
- **出力**: 単一実行ファイル（.exe）
- **特徴**:
  - UPX圧縮有効
  - コンソールウィンドウなし
  - 全依存関係を含む

#### macOS用
- **ファイル**: `tools/packaging/kumihan_formatter_macos.spec`
- **出力**: アプリケーションバンドル（.app）
- **特徴**:
  - ネイティブmacOSアプリ
  - Info.plist設定
  - 文書タイプ関連付け

### ビルドスクリプト

#### Windows
- **ファイル**: `build_windows.py`
- **機能**:
  - 依存関係チェック
  - PyInstaller自動実行
  - テスト機能
  - ZIP配布パッケージ作成

#### macOS
- **ファイル**: `build_macos.py`
- **機能**:
  - 依存関係チェック
  - .appバンドル生成
  - 署名対応（オプション）
  - ZIP配布パッケージ作成

## 🔧 開発者向け情報

### 新しいプラットフォーム対応

1. **PyInstaller設定ファイル作成**
   ```python
   # kumihan_formatter_[platform].spec
   # プラットフォーム固有の設定
   ```

2. **ビルドスクリプト作成**
   ```python
   # build_[platform].py
   # プラットフォーム固有のビルドロジック
   ```

3. **GitHub Actions ワークフロー追加**
   ```yaml
   # .github/workflows/build-[platform].yml
   # CI/CD設定
   ```

### トラブルシューティング

#### 一般的な問題

1. **依存関係エラー**
   ```bash
   # 仮想環境の再作成
   rm -rf .venv
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```

2. **PyInstaller エラー**
   ```bash
   # キャッシュクリア
   pyinstaller --clean --noconfirm [spec_file]
   ```

3. **実行時エラー**
   - ログファイルチェック
   - 依存ファイルの包含確認
   - 権限設定確認

#### プラットフォーム固有の問題

**Windows:**
- UACダイアログ対応
- Windows Defender除外設定
- 必要なDLLの包含

**macOS:**
- 署名・Notarization
- Gatekeeper対応
- 権限要求ダイアログ

## 📋 リリースプロセス

### 1. 準備
- [ ] バージョン番号更新
- [ ] CHANGELOG更新
- [ ] テストビルド実行

### 2. ビルド
- [ ] GitHub Actionsでリリースビルド実行
- [ ] 各プラットフォームでのテスト

### 3. リリース
- [ ] GitHub Releasesで公開
- [ ] ドキュメント更新
- [ ] アナウンス

## 🔗 関連リンク

- [Issue #391](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues/391) - クロスプラットフォーム配布パッケージング統合実装
- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

**Issue #391対応**: クロスプラットフォーム配布パッケージングの統合実装完了
