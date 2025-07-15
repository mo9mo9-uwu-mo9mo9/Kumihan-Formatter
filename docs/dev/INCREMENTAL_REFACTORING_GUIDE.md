# 漸進的リファクタリングガイド

> **目的**: 大規模リファクタリングを回避し、継続的な品質改善を実現する
> **対象**: Issue #476のような技術的負債蓄積の予防策
> **更新**: 2025-01-15

## 📋 概要

このガイドは、Kumihan-Formatterにおける**漸進的リファクタリング**の実践方法を定義します。
大規模な技術的負債の蓄積を防ぎ、コードベースの健全性を維持することを目指します。

## 🎯 基本原則

### 1. Boy Scout Rule（ボーイスカウトルール）
> "キャンプ場は来た時よりも美しく去る"

```python
# ❌ 悪い例：コードを触ったが改善しない
def process_file(file_path):
    # 既存の長い関数に機能追加のみ
    ...  # 200行の既存コード
    new_feature_code()  # 新機能を追加するだけ

# ✅ 良い例：触ったコードは改善する
def process_file(file_path):
    # 機能追加と同時に既存コードも改善
    file_data = _load_file(file_path)  # 抽出
    processed_data = _process_data(file_data)  # 抽出
    new_feature_result = _apply_new_feature(processed_data)  # 新機能
    return _save_result(new_feature_result)  # 抽出

def _load_file(file_path):
    """ファイル読み込み処理を分離"""
    # 既存コードから抽出

def _process_data(data):
    """データ処理を分離"""
    # 既存コードから抽出
```

### 2. 2つのハット原則
機能追加とリファクタリングを同時に行わない：

```bash
# ✅ 正しいアプローチ
git commit -m "refactor: extract file loading logic"
git commit -m "feat: add new processing feature"

# ❌ 間違ったアプローチ
git commit -m "feat: add feature and refactor everything"
```

### 3. 安全第一の原則
- リファクタリング前後でテスト結果が変わらない
- 小さな変更を積み重ねる
- 一度に変更するファイル数を制限

## 🔧 実践手法

### レベル1: 日常的改善（毎日）

#### 命名改善
```python
# Before
def proc(d):
    return d * 2

# After
def double_value(data: float) -> float:
    return data * 2
```

#### コメント改善
```python
# Before
# TODO: fix this later
def complex_function():
    pass

# After
def complex_function():
    """Calculate conversion rate based on input metrics

    Args:
        metrics: Input performance metrics

    Returns:
        Conversion rate as percentage

    TODO: Add caching for expensive calculations (Issue #123)
    """
    pass
```

#### 小さな関数抽出
```python
# Before: 長い関数
def validate_input(data):
    # 30行の検証ロジック

# After: 機能分割
def validate_input(data):
    _validate_format(data)
    _validate_business_rules(data)
    _validate_constraints(data)
```

### レベル2: 週次改善（毎週）

#### クラス責任分離
```python
# Before: 神クラス
class FileProcessor:
    def read_file(self): pass
    def validate_data(self): pass
    def transform_data(self): pass
    def save_file(self): pass
    def send_email(self): pass  # 責任外

# After: 責任分離
class FileReader:
    def read_file(self): pass

class DataValidator:
    def validate_data(self): pass

class DataTransformer:
    def transform_data(self): pass

class FileWriter:
    def save_file(self): pass

class NotificationService:  # 別責任
    def send_email(self): pass
```

#### ファイル分割
```python
# Before: 1つの大きなファイル
# utils.py (500行)

# After: 機能別分割
# utils/
#   ├── file_utils.py      (100行)
#   ├── string_utils.py    (80行)
#   ├── validation_utils.py (90行)
#   └── __init__.py        (re-export)
```

### レベル3: 月次改善（毎月）

#### アーキテクチャ改善
```python
# Before: 循環依存
# module_a.py
from .module_b import ClassB

# module_b.py
from .module_a import ClassA

# After: 依存関係整理
# interfaces.py
class IProcessor(Protocol):
    def process(self) -> Any: ...

# module_a.py
from .interfaces import IProcessor

# module_b.py
from .interfaces import IProcessor
```

## 📊 メトリクス監視

### 自動監視項目
```bash
# コミット時自動チェック（pre-commit hook）
scripts/check_file_size.py --max-lines=300
scripts/architecture_check.py

# 手動実行（必要時のみ）
radon cc kumihan_formatter/ --min=B
radon mi kumihan_formatter/ --min=B
```

### 改善トリガー
| メトリクス | 閾値 | アクション |
|------------|------|------------|
| ファイル行数 | >300行 | 即座に分割検討 |
| 関数行数 | >20行 | 分割検討 |
| クラス行数 | >100行 | 責任分離検討 |
| 複雑度 | >10 | 条件分岐の簡素化 |
| インポート数 | >20個 | モジュール依存見直し |

## 🛠️ リファクタリングパターン

### パターン1: Extract Method（メソッド抽出）
```python
# Before
def process_order(order):
    # 50行の処理...
    total = 0
    for item in order.items:
        if item.category == 'book':
            total += item.price * 0.9  # 書籍割引
        elif item.category == 'electronics':
            total += item.price * 0.95  # 電子機器割引
        else:
            total += item.price
    # さらに20行の処理...

# After
def process_order(order):
    total = _calculate_total_with_discounts(order.items)
    # 残りの処理...

def _calculate_total_with_discounts(items):
    """割引適用後の総額を計算"""
    total = 0
    for item in items:
        total += _apply_category_discount(item)
    return total

def _apply_category_discount(item):
    """カテゴリ別割引を適用"""
    discounts = {
        'book': 0.9,
        'electronics': 0.95
    }
    return item.price * discounts.get(item.category, 1.0)
```

### パターン2: Extract Class（クラス抽出）
```python
# Before: データクラスに振る舞いが混在
@dataclass
class User:
    name: str
    email: str

    def save_to_database(self):  # データアクセス責任
        pass

    def send_welcome_email(self):  # 通知責任
        pass

    def validate_email(self):  # 検証責任
        pass

# After: 責任分離
@dataclass
class User:
    name: str
    email: str

class UserRepository:
    def save(self, user: User):
        """データベース保存"""
        pass

class UserNotificationService:
    def send_welcome_email(self, user: User):
        """ウェルカムメール送信"""
        pass

class UserValidator:
    def validate_email(self, email: str) -> bool:
        """メールアドレス検証"""
        pass
```

### パターン3: Replace Conditional with Polymorphism
```python
# Before: 条件分岐が多い
class DocumentProcessor:
    def process(self, doc_type: str, content: str):
        if doc_type == 'pdf':
            # PDF処理
            pass
        elif doc_type == 'docx':
            # Word処理
            pass
        elif doc_type == 'txt':
            # テキスト処理
            pass
        else:
            raise ValueError(f"Unsupported type: {doc_type}")

# After: ポリモーフィズム適用
class DocumentProcessor(ABC):
    @abstractmethod
    def process(self, content: str) -> str:
        pass

class PDFProcessor(DocumentProcessor):
    def process(self, content: str) -> str:
        # PDF固有の処理
        pass

class DocxProcessor(DocumentProcessor):
    def process(self, content: str) -> str:
        # Word固有の処理
        pass

class ProcessorFactory:
    _processors = {
        'pdf': PDFProcessor(),
        'docx': DocxProcessor(),
        'txt': TextProcessor()
    }

    @classmethod
    def get_processor(cls, doc_type: str) -> DocumentProcessor:
        processor = cls._processors.get(doc_type)
        if not processor:
            raise ValueError(f"Unsupported type: {doc_type}")
        return processor
```

## 📅 実践アプローチ

### コード触る時（Boy Scout Rule）
- [ ] 修正対象ファイルの命名改善
- [ ] 無用なコメント削除
- [ ] 小さな重複コード排除
- [ ] 20行超過関数の分割検討

### PR作成時
- [ ] pre-commit hookで自動チェック実行
- [ ] ファイルサイズ違反の解消
- [ ] アーキテクチャ違反の確認

### 必要に応じて（問題発見時）
- [ ] 300行超過ファイルの分割
- [ ] 複雑度過多関数の簡素化
- [ ] 循環依存の解消
- [ ] 大きなクラスの責任分離

## 🚨 危険信号

### 即座に対応が必要
- [ ] ファイルが300行を超過
- [ ] 関数が50行を超過
- [ ] クラスが200行を超過
- [ ] 複雑度が15を超過

### 計画的対応が必要
- [ ] 同じパターンのコードが3箇所以上
- [ ] import文が20個を超過
- [ ] TODOコメントが10個を超過
- [ ] テストカバレッジが80%を下回る

## 🎯 成功指標

### 定量指標
- ファイル平均行数: <150行
- 関数平均行数: <10行
- クラス平均行数: <50行
- 複雑度平均: <5
- テストカバレッジ: >90%

### 定性指標
- 新機能開発速度の向上
- バグ発生率の低下
- コードレビュー時間の短縮
- 開発者の満足度向上

## 📚 参考資料

- [Refactoring: Improving the Design of Existing Code](https://martinfowler.com/books/refactoring.html)
- [Clean Code](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350884)
- [Working Effectively with Legacy Code](https://www.amazon.com/Working-Effectively-Legacy-Michael-Feathers/dp/0131177052)

---

**このガイドの効果測定**:
- Issue #476のような大規模リファクタリングの頻度減少
- 技術的負債指標の改善トレンド
- 開発速度の向上
