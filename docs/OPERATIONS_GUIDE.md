# Kumihan-Formatter 運用ガイド

> Phase 3-3 完成版運用ガイド
> Issue #598対応 - プロジェクト完成

## 概要

Kumihan-Formatterの本番運用における
インストール・設定・監視・メンテナンス手順を説明します。

## システム要件

- Python 3.12以上
- メモリ: 最小512MB、推奨2GB以上
- ストレージ: 100MB以上の空き容量
- OS: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)

## インストール手順

### 1. 基本インストール
```bash
pip install kumihan-formatter
```

### 2. 開発者インストール
```bash
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter
pip install -e .
```

## 基本使用方法

### コマンドライン
```bash
# 基本変換
kumihan convert input.txt output.txt

# バッチ処理
kumihan batch --input-dir ./docs --output-dir ./formatted
```

### Python API
```python
from kumihan_formatter import KumihanFormatter

formatter = KumihanFormatter()
result = formatter.format_text(input_text)
```

## 設定管理

### 設定ファイル
- メイン設定: `~/.kumihan/config.yaml`
- ログ設定: `~/.kumihan/logging.yaml`
- キャッシュ設定: `~/.kumihan/cache.yaml`

### 推奨設定
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

## パフォーマンス監視

### 品質監視
```bash
# 品質ダッシュボード
python scripts/quality_monitoring_system.py

# 統合テスト
python scripts/phase_3_3_integration_tests.py
```

### メトリクス収集
- テストカバレッジ: 80%以上維持
- 品質ゲート通過率: 98%以上
- パフォーマンス: 1秒以内での処理
- メモリ使用量: 100MB以下

## トラブルシューティング

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

## メンテナンス

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

## セキュリティ

### セキュリティ設定
- 入力ファイルの検証を有効化
- 信頼できないファイルの処理制限
- ログ出力の機密情報マスク

### 更新管理
```bash
# セキュリティ更新確認
pip list --outdated
```

## 支援・サポート

### コミュニティ
- GitHub Issues: バグ報告・機能要求
- Discussions: 使用方法・質問
- Wiki: 詳細ドキュメント

### 開発者向け
- 開発環境構築: `docs/dev/SETUP.md`
- コントリビューション: `CONTRIBUTING.md`
- API リファレンス: `docs/api/`

---

**Phase 3-3 完成記念** 🎉

生成日時: 2025-07-27 17:09:51
最終最適化完了: Issue #598対応
