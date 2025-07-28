# Kumihan-Formatter 開発ガイド（統合版）

> 包括的な開発・管理指示書 - 27ファイル統合版
> **最終更新**: 2025-01-28

## 📋 目次

- [概要](#概要)
- [開発環境](#開発環境)  
- [Claude Code開発](#claude-code開発)
- [アーキテクチャ](#アーキテクチャ)
- [開発ワークフロー](#開発ワークフロー)
- [品質管理](#品質管理)

## 概要

**Claude Code専用開発プロジェクト** - 人間の可読性は考慮せず、AI効率を最優先

### 基本設定
- **Python**: 3.12以上, Black, isort, mypy strict  
- **エンコーディング**: UTF-8
- **リリース**: v0.9.0-alpha.1

## 開発環境

### 必須コマンド
```bash
make test          # テスト実行
make lint          # リントチェック  
make pre-commit    # コミット前チェック
kumihan convert input.txt output.txt  # 基本変換
```

## Claude Code開発

### ログ機能
```python
from kumihan_formatter.core.utilities.logger import get_logger
logger = get_logger(__name__)
```

### 基本原則
1. **AI完全実行**: 全作業をClaude Codeが実行
2. **人間非関与**: 可読性・規約確認は不要
3. **効率最優先**: Claude参照効率を最大化

## アーキテクチャ

### コア構成
```
kumihan_formatter/
├── core/
│   ├── parser/     # 解析エンジン
│   ├── renderer/   # 出力エンジン  
│   └── utilities/  # 共通機能
├── commands/       # CLI実装
└── templates/      # テンプレート
```

## 開発ワークフロー

### ブランチ戦略
- **命名**: `feat/issue-{Issue番号}-{概要}`
- **作業前**: mainから最新取得、正しいブランチ作成
- **PR前**: rebase必須

### 必須チェック
1. Issue番号とブランチ名の一致確認
2. 実装・テスト
3. PR作成: `@claude PRのレビューをお願いします！`

## 品質管理

### qcheckシステム
```bash
qcheck   # 全体品質チェック
qcheckf  # 関数レベルチェック
qcheckt  # テスト品質チェック  
qdoc     # ドキュメント品質チェック
```

### CI/CD品質ゲート
- **必須**: Black/isort/flake8/pytest/mypy通過
- **実行時間**: 15分→5分に最適化済み

---

*本文書は docs/dev/ の27ファイルを統合したものです*