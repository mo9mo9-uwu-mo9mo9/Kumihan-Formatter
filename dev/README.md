# 開発者向け情報

このディレクトリには、Kumihan-Formatterの開発に必要なファイルが含まれています。

## ディレクトリ構成

```
dev/
├── tests/          # 自動テストコード
├── tools/          # 開発支援ツール
├── test_data/      # テスト用データファイル
└── README.md       # 本ファイル
```

## 開発環境セットアップ

```bash
# 1. 仮想環境の作成
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 開発用依存関係のインストール
pip install -e ".[dev]"
```

## テスト実行

```bash
# すべてのテストを実行
pytest

# 特定のテストファイルを実行
pytest dev/tests/test_parser.py

# カバレッジレポート付きで実行
pytest --cov=kumihan_formatter
```

## 開発ツール

### generate_test_file.py
テスト用の入力ファイルを生成します。

```bash
python dev/tools/generate_test_file.py
```

### generate_showcase.py
機能ショーケース用のサンプルファイルを生成します。

```bash
python dev/tools/generate_showcase.py
```

### cleanup.py
開発中に生成された一時ファイルやテスト出力を削除します。

```bash
# 削除対象を確認（実際には削除しない）
python dev/tools/cleanup.py --dry-run

# 実際に削除
python dev/tools/cleanup.py --no-dry-run
```

## コーディング規約

- **スタイルガイド**: PEP 8に準拠
- **型ヒント**: Python 3.9以降の型アノテーションを使用
- **ドキュメント**: すべての公開関数・クラスにdocstringを記述
- **テスト**: 新機能には必ず対応するテストを追加

## テスト作成ガイド

1. テストファイルは `dev/tests/test_機能名.py` の形式で作成
2. テストクラスは `Test機能名` の形式で命名
3. テストメソッドは `test_説明的な名前` の形式で命名
4. 境界値、エラーケース、正常系を網羅

例：
```python
# dev/tests/test_new_feature.py
import pytest
from kumihan_formatter.new_feature import process

class TestNewFeature:
    def test_正常系(self):
        result = process("input")
        assert result == "expected"
    
    def test_エラーケース(self):
        with pytest.raises(ValueError):
            process(None)
```

## コミット規約

Conventional Commitsに従ってください：

- `feat:` 新機能
- `fix:` バグ修正
- `docs:` ドキュメントのみの変更
- `test:` テストの追加・修正
- `refactor:` リファクタリング
- `chore:` ビルドプロセスやツールの変更

例：
```
feat: 画像埋め込み機能を追加
fix: 複合キーワードのパース処理を修正
docs: 開発者向けREADMEを追加
```

## トラブルシューティング

### テストが失敗する場合
1. 依存関係が最新か確認: `pip install -e ".[dev]"`
2. Pythonバージョンを確認: 3.9以降が必要
3. テストデータが正しい場所にあるか確認

### import エラーが発生する場合
1. 仮想環境が有効か確認
2. プロジェクトルートからコマンドを実行しているか確認
3. `pip install -e .` でパッケージがインストールされているか確認