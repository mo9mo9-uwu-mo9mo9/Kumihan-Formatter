# コードスタイルと規約

## Python設定
- **Python バージョン**: 3.12以上
- **エンコーディング**: UTF-8
- **ログ取得**: `from kumihan_formatter.core.utilities.logger import get_logger`

## フォーマッティング設定
### Black
- 行長: 88文字
- ターゲット: Python 3.12

### isort
- プロファイル: "black"
- 行長: 88文字

### mypy（厳格設定）
- `strict = true`
- すべての型チェック有効
- 未型定義・any型・不完全定義を禁止

## コード規約
- 厳格な型ヒント必須
- ドキュメント文字列推奨
- エラーハンドリング必須
- ログ出力の適切な使用

## ファイル構造パターン
- `core/` - コアロジック
- `gui_*` - GUI関連
- `commands/` - CLIコマンド実装
- `config/` - 設定管理
- `templates/` - HTMLテンプレート

## import規則
- 標準ライブラリ → サードパーティ → ローカル
- isort で自動整理される

## ログ使用
```python
from kumihan_formatter.core.utilities.logger import get_logger
logger = get_logger(__name__)
```