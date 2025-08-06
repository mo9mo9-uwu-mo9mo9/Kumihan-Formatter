# Kumihan-Formatter プロジェクト概要

## プロジェクトの目的
- CoC6th同人シナリオなどのテキストファイルをワンコマンドで美しいHTMLに変換する日本語ツール
- プロ品質の出力、直感的な改行処理、A4印刷対応
- GUI版とCLI版を提供

## 基本情報
- **バージョン**: 0.9.0-alpha.8 (開発中)
- **Python要求**: 3.12以上
- **プラットフォーム**: Windows・macOS対応
- **ライセンス**: Proprietary

## 主要な特徴
- 直感的な改行処理（改行したらそのまま改行される）
- プロ品質の出力（美しい組版、A4印刷対応）
- クロスプラットフォーム対応
- GUI版とCLI版の両方を提供

## 技術スタック
- **言語**: Python 3.12+
- **主要依存関係**: Click, Jinja2, Rich, Watchdog, PyYAML, Pydantic
- **開発ツール**: Black, isort, flake8, mypy, beautifulsoup4

## メインエントリーポイント
- **GUI**: `python -m kumihan_formatter.gui_launcher`
- **CLI**: `kumihan convert input.txt` または `python -m kumihan_formatter convert input.txt`