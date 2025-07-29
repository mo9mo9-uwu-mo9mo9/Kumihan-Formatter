# Changelog

All notable changes to Kumihan-Formatter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-06-23

### Added
- **上書き確認機能**: サンプル実行時に既存ファイルの上書き確認を追加
- **想定エラー表示**: サンプルファイルのエラーを「想定されたエラー」として明示
- **目次機能**: `;;;目次;;;`マーカーで自動目次生成
- **ソーストグル機能**: 記法と結果を切り替え表示（`--with-source-toggle`オプション）
- **Windows/macOS対応**: 両OS用のバッチファイル/コマンドファイル
- **サンプルファイル**: 基本・高度・ショーケースの3種類

### Changed
- サンプル生成時の自動ブラウザ起動を削除
- showcase.htmlのテンプレートをデフォルトに変更（トグルボタン削除）

### Fixed
- Windows/macOSバッチファイルの動作同期

### Technical
- Python 3.9+ 対応
- Click CLI フレームワーク使用
- Jinja2 テンプレートエンジン
- Rich ライブラリでコンソール表示強化
- pytest によるテスト自動化

## [0.0.1] - 2025-01-21

### Added
- 初回リリース
- 基本的なテキスト→HTML変換機能
- 主要記法サポート（見出し、太字、枠線、リスト）
- macOS/Windows対応の実行スクリプト

---

**Versioning Strategy:**
- **Major (X.0.0)**: 破壊的変更、アーキテクチャ変更
- **Minor (0.X.0)**: 新機能追加、機能拡張
- **Patch (0.0.X)**: バグ修正、小さな改善

**Links:**
- [Repository](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter)
- [Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)
- [Documentation](docs/)