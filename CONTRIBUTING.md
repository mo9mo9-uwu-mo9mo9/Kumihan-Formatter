# 開発ガイド

> **Kumihan-Formatter の開発・コントリビューション指針**

---

## 🧩 アーキテクチャ概要

```text
┌─ kumihan_formatter/            # Python パッケージルート
│  ├─ cli.py          ← Click CLIエントリポイント
│  ├─ parser.py       ← テキスト → AST (段落・ブロック・キーワード付きリスト)
│  ├─ renderer.py     ← AST → HTML (Jinja2 テンプレート)
│  ├─ config.py       ← YAML/JSON設定ファイル管理
│  ├─ templates/      ← base.html.j2
│  └─ utils/
│      └─ __init__.py
├─ dev/                # 開発者向けファイル
│  ├─ tests/          # テストファイル群
│  │  ├─ test_parser.py
│  │  ├─ test_renderer.py
│  │  ├─ test_config.py
│  │  └─ test_cli.py
│  └─ tools/
│      └─ generate_test_file.py
└─ examples/
    ├─ sample.txt
    ├─ comprehensive-sample.txt
    └─ config-sample.yaml
```

**設計原則:**
* **単一責任:** parser は純粋に構文解析、renderer は純粋に変換を担当
* **プラガブル:** マーカーや CSS は YAML で増減可能
* **ステートレス:** 大部分を純粋関数で構成しテスト容易性を向上

---

## ⚙️ 開発環境セットアップ

### 初期化コマンド

```bash
# 1) リポジトリを取得
$ git clone https://github.com/USERNAME/kumihan-formatter.git
$ cd kumihan-formatter

# 2) 仮想環境（Python ≥ 3.9）を作成しインストール
$ python -m venv .venv && source .venv/bin/activate
$ pip install -e .[dev]        # dev extras = pytest, flake8, rich

# 3) テスト実行
$ pytest -q
```

### ローカル実行例

```bash
$ python -m kumihan_formatter.cli \
    examples/sample.txt \
    -o dist/
```

**主なフラグ:**

| フラグ | 説明 |
|------|-------------|
| `-o, --output DIR` | 出力フォルダ (default: ./dist) |
| `--no-preview` | HTML 生成後にブラウザを開かない |
| `--config FILE` | YAML/JSON 設定ファイルを指定 |

---

## 🛠️ テスト戦略

* **ユニット**: パーサ & レンダラの境界ケース（マーカー入れ子、不正構文）
* **ゴールデン**: sample.txt → expected.html のスナップショット比較
* **パフォーマンス**: 10 k 文字 ≤ 1 秒（pytest-benchmark）

### CI スモークテスト

```bash
pytest && \
python -m kumihan_formatter.cli examples/sample.txt -o /tmp/out
```

---

## 📃 非機能要件

| 分類 | 要件 |
|----------|-------------|
| **性能** | 10 k 文字 → HTML ≤ 1 秒 |
| **信頼性** | エラー位置を HTML 内で可視化 |
| **移植性** | Python 標準 + `rich`, `jinja2`, `click` のみ |
| **セキュリティ** | 完全オフライン。上書き防止チェック有 |
| **i18n** | UI・メッセージともに日本語のみ |

---

## 🏷️ GitHub Issue ラベリングルール

シンプルで使いやすいラベル体系を採用しています。

### 基本ラベル（6種類のみ）

| ラベル | 用途 | 使用場面 |
|-------|------|---------|
| `緊急` | システム停止・重大バグ | 変換できない、データ破損 |
| `通常` | 一般的な改善・バグ | 通常の機能改善・軽微なバグ |
| `バグ` | 動作不具合 | 何かが正常に動作しない |
| `機能改善` | 新機能・改善 | 既存機能の改善・新機能リクエスト |
| `ドキュメント` | 文書関連 | ドキュメントの改善・追加 |
| `質問` | 情報確認 | 詳細情報が必要・質問 |

### ラベル付与ルール
1. **優先度**: `緊急` または `通常` のいずれかを必ず付与
2. **種類**: `バグ`、`機能改善`、`ドキュメント`、`質問` から選択
3. **シンプル重視**: 複雑なラベル組み合わせは避ける

---

## 🔄 開発ワークフロー

1. **応答は必ず日本語を使用すること**
2. **コード追加前** に必ず *開発ブランチ* (`feature/XXX`) を切る
3. 機能コードと **対応するテストコード** を *セットで追加* する
4. **コミット後** に *プルリクエスト* を作成し、レビュー後 **main ブランチにマージ** する
5. **マージ後**、関連 **Issue を更新・整理** する
6. マージが完了したら **不要ブランチを削除** する
7. 1から6までの作業完了後、作業に関連するIssueがあれば更新する

---

## 🤝 コントリビューション

* **コードスタイル**: black + isort + flake8
* **コミット規約**: Conventional Commits (`feat:`, `fix:` など)

### 📝 Kumihan記法ルール

サンプルファイルや文書作成時は以下のKumihan記法ルールに従ってください：

#### ✅ 推奨Kumihan記法
- **見出し**: `;;;見出し1\n内容\n;;;` 形式を使用
- **複合マーカー**: `;;;太字+ハイライト color=#ff0000;;;` の順序を守る
- **色指定**: [STYLE_GUIDE.md](STYLE_GUIDE.md) の推奨カラーパレット使用
- **構造化**: 論理的な見出し階層と適切なリスト使用

#### ❌ 禁止記法
- **Markdown記法**: `# 見出し`、`**太字**` 等は使用禁止（Kumihan記法を使用）
- **不完全なブロック**: 閉じマーカー `;;;` の忘れは禁止
- **目次マーカー**: `;;;目次;;;` の手動使用は禁止（自動生成）
- **color属性の誤順序**: `;;;ハイライト color=#xxx+太字;;;` は禁止

### 🔍 Kumihan記法検証の実行

プルリクエスト前に必ずKumihan記法検証を実行してください：

```bash
# 新規作成・変更したテキストファイルの検証
python dev/tools/syntax_validator.py examples/*.txt

# テストスイートの実行
python -m pytest dev/tests/test_syntax_validation.py -v

# CI/CDでの自動チェック
# GitHub Actionsにより、PRマージ時に自動実行されます
```

### 📚 Kumihan記法ガイドライン参照
- [SPEC.md](SPEC.md) - 完全なKumihan記法仕様
- [STYLE_GUIDE.md](STYLE_GUIDE.md) - Kumihan記法スタイルガイド
- [examples/](examples/) - 実践的なサンプル集

---

## 🔮 拡張フック（今後検討）

* テーマ / フォント / レイアウト切替（JSON スキーマ）
* 画像埋め込み (`:::画像 path=... alt=...`)
* PDF 出力（`weasyprint`）
* カスタムブロック用プラグインインタフェース