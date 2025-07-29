# 配布・運用ガイド

> Kumihan-Formatter の配布パッケージング・本番運用の統合ガイド

## 📦 配布パッケージング

### 概要
Kumihan-Formatterは以下のプラットフォームで実行可能形式のファイルとして配布されます：
- **Windows**: `.exe` 形式の実行ファイル
- **macOS**: `.app` 形式のアプリケーションバンドル

### ビルド方法

#### Windows (.exe)
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

#### macOS (.app)
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

### 配布パッケージ構成

#### Windows パッケージ
```
Kumihan-Formatter-v1.0-Windows.zip
├── Kumihan-Formatter.exe     # 実行ファイル
└── README-Windows.txt        # インストール説明書
```

#### macOS パッケージ
```
Kumihan-Formatter-v1.0-macOS.zip
├── Kumihan-Formatter.app/    # アプリケーションバンドル
│   ├── Contents/
│   │   ├── Info.plist
│   │   ├── MacOS/
│   │   └── Resources/
└── README-macOS.txt          # インストール説明書
```

## 🏭 本番運用

### システム要件
- Python 3.12以上
- メモリ: 最小512MB、推奨2GB以上
- ストレージ: 100MB以上の空き容量
- OS: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)

### インストール手順

#### 1. 基本インストール
```bash
pip install kumihan-formatter
```

#### 2. 開発者インストール
```bash
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter
pip install -e .
```

### 基本使用方法

#### コマンドライン
```bash
# 基本変換
kumihan convert input.txt output.txt

# バッチ処理
kumihan batch --input-dir ./docs --output-dir ./formatted
```

#### Python API
```python
from kumihan_formatter import KumihanFormatter

formatter = KumihanFormatter()
result = formatter.format_text(input_text)
```

### 設定管理

#### 設定ファイル
- メイン設定: `~/.kumihan/config.yaml`
- ログ設定: `~/.kumihan/logging.yaml`
- キャッシュ設定: `~/.kumihan/cache.yaml`

#### 推奨設定
```yaml
# config.yaml
performance:
  cache_enabled: true
  max_cache_size: 1000
  concurrent_processing: true

quality:
  strict_validation: true
  encoding_detection: true
```

## 🔧 メンテナンス・トラブルシューティング

### よくある問題

#### エンコーディングエラー
```bash
# UTF-8以外のファイルの場合
kumihan convert --encoding=shift_jis input.txt output.txt
```

#### メモリ不足
```bash
# チャンク処理を有効化
kumihan convert --chunk-size=1000 large_file.txt output.txt
```

### ログ確認
```bash
# ログファイル場所
tail -f ~/.kumihan/logs/kumihan.log
```

### 定期メンテナンス
- 月次: キャッシュクリーンアップ
- 四半期: 依存関係更新
- 年次: 設定見直し

### キャッシュ管理
```bash
# キャッシュクリア
kumihan cache clear

# キャッシュ統計
kumihan cache stats
```

## 🔒 セキュリティ

### セキュリティ設定
- 入力ファイルの検証を有効化
- 信頼できないファイルの処理制限
- ログ出力の機密情報マスク

### 更新管理
```bash
# セキュリティ更新確認
pip list --outdated
```

## 🤝 サポート

### コミュニティ
- GitHub Issues: バグ報告・機能要求
- Discussions: 使用方法・質問
- Wiki: 詳細ドキュメント

### 開発者向け
- 開発環境構築: `docs/DEVELOPMENT_GUIDE.md`
- コントリビューション: `CONTRIBUTING.md`
- API リファレンス: `docs/ARCHITECTURE.md`

---

**統合完了**: 配布・運用ガイドの統合実装完了