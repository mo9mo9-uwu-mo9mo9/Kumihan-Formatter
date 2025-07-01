# Kumihan記法 実装指針

> **開発者向けの実装ガイドラインと技術的詳細**

---

## 🔄 動作フロー

### パース処理
1. **行単位解析**: テキストを行ごとに解析
2. **ブロック検出**: `;;;` マーカーでブロック開始・終了を検出
3. **キーワード解析**: マーカー内のキーワードと属性を分離
4. **リスト処理**: `- ` および `1. ` でリスト項目を検出
5. **目次マーカー**: `;;;目次;;;` を検出（手動記述は警告）

### レンダリング処理
1. **AST構築**: パース結果からASTを構築
2. **見出し収集**: 目次生成用に見出しを収集
3. **HTML変換**: ASTを順次HTMLに変換
4. **目次生成**: 見出しリストから目次HTMLを生成
5. **テンプレート適用**: Jinja2テンプレートで最終HTML生成

---

## 🏗️ ネスト処理

### ネスト順序（renderer.py内の実装）
1. `div`系（枠線、ハイライト）
2. `見出し`系（見出し1-5）  
3. `strong`（太字）
4. `em`（イタリック）

### 複合キーワード処理
- 複合キーワードは `+` または `＋` で分割
- 各キーワードを個別に標準キーワードとして解釈
- タグのネスト順は `nesting_order` で決定

---

## 🎯 実装指針

### コアルール
- 複合キーワードは `+` または `＋` で分割し、一つずつ標準キーワードとして解釈
- 変換時に **タグのネスト順** を renderer.py 内の `nesting_order` で決定
- 目次マーカーは手動使用禁止、見出しの存在から自動生成

### パフォーマンス考慮事項
- 大きなファイルでは行単位での逐次処理
- メモリ効率のため、不要な中間データの削除
- 正規表現の最適化による高速化

### エラーハンドリング
- 記法エラーは警告として表示、処理継続
- 致命的エラーのみプログラム停止
- ユーザーフレンドリーなエラーメッセージ

---

## 🔧 開発者向けツール

### デバッグ機能
```bash
# デバッグモードでの実行
python -m kumihan_formatter --debug input.txt

# AST表示
python -m kumihan_formatter --show-ast input.txt

# パース結果の詳細表示
python -m kumihan_formatter --verbose input.txt
```

### テスト実行
```bash
# 単体テスト
python -m pytest tests/test_parser.py -v

# 結合テスト
python -m pytest tests/test_integration.py -v

# カバレッジ付きテスト
python -m pytest --cov=kumihan_formatter tests/
```

---

## 📚 アーキテクチャ

### モジュール構成
- `parser.py`: Kumihan記法の解析
- `renderer.py`: HTML生成とネスト処理
- `template_manager.py`: Jinja2テンプレート管理
- `syntax_validator.py`: 記法検証ツール

### 拡張ポイント
- 新しいキーワードの追加: `KEYWORD_MAP` に登録
- カスタムレンダラー: `BaseRenderer` を継承
- 独自テンプレート: `templates/` ディレクトリに配置

---

**関連ドキュメント:**
- コア仕様: [SPEC_CORE.md](SPEC_CORE.md)
- 構文詳細: [SPEC_SYNTAX.md](SPEC_SYNTAX.md)
- リファレンス: [SPEC_REFERENCE.md](SPEC_REFERENCE.md)