# Kumihan-Formatter 開発ガイド

## 開発環境のセットアップ

### 1. リポジトリのクローン
```bash
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter
```

### 2. 仮想環境の作成と有効化
```bash
# 仮想環境の作成
python -m venv .venv

# 有効化 (macOS/Linux)
source .venv/bin/activate

# 有効化 (Windows)
.venv\Scripts\activate
```

### 3. 開発用インストール
```bash
pip install -e ".[dev]"
```

## コーディング規約

### コードスタイル
- Python 3.9以上の機能を使用
- Black + isort + flake8を使用
- 型ヒントを可能な限り使用

### 🚫 絵文字・特殊文字の使用禁止

**重要**: 絵文字・特殊文字の使用は原則禁止です。

- **対象**: CLI出力、シェルスクリプト、テストコード、技術文書
- **理由**: エンコーディング問題、環境依存、保守性の問題
- **代替**: `[タグ]`形式を使用（例: ✅→[完了], ❌→[エラー]）

詳細は [`docs/dev/EMOJI_POLICY.md`](./EMOJI_POLICY.md) を参照してください。

### コミットメッセージ
Conventional Commitsに従います:
- `feat:` 新機能
- `fix:` バグ修正
- `docs:` ドキュメント
- `test:` テスト
- `refactor:` リファクタリング
- `chore:` その他

例: `feat: 画像埋め込み機能の追加`

## 開発フロー

1. **Issueの作成または選択**
   - 新機能や修正内容を明確にする

2. **ブランチの作成**
   ```bash
   git checkout -b feature/機能名
   ```

3. **実装とテスト**
   - 機能コードとテストコードをセットで追加
   - `pytest`でテストを実行

4. **プルリクエスト**
   - mainブランチへのPRを作成
   - CIが通ることを確認

## 新機能の追加方法

### 新しいマーカーの追加
1. `parser.py`の`MARKERS`辞書に追加
2. `test_parser.py`にテストケース追加
3. ドキュメント更新

### 新しいレンダリング処理
1. `renderer.py`の`_render_node()`を拡張
2. 必要に応じてテンプレート更新
3. テストケース追加

## デバッグのヒント

### パーサーのデバッグ
```python
# パース結果を詳細表示
parser = Parser()
nodes = parser.parse(text)
for node in nodes:
    print(f"Type: {node.type}, Content: {node.content}")
```

### レンダラーのデバッグ
```python
# 中間ノードの確認
renderer = Renderer()
renderer.debug = True  # デバッグモード有効化
```

## リリース手順

1. バージョン番号の更新（`pyproject.toml`）
2. CHANGELOGの更新
3. タグの作成とプッシュ
4. GitHub Releaseの作成