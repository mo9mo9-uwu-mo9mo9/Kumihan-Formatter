# Kumihan-Formatter アーキテクチャ設計原則

> **目的**: 定期的なリファクタリングを不要にする持続可能な設計指針
> **バージョン**: 1.0.0
> **最終更新**: 2025-06-30

## 🎯 基本理念

**「予防的品質管理」** - 問題が発生する前に防ぐ設計

---

## 📐 設計原則

### 1️⃣ **単一責任原則 (Single Responsibility)**

#### **ファイルサイズ制限**
- **Python ファイル**: 最大300行
- **関数/メソッド**: 最大50行
- **クラス**: 最大200行

#### **責任分離の明確化**
```python
# ❌ 悪い例: 複数責任
class ConvertCommand:
    def parse_input(self): ...
    def validate_syntax(self): ...
    def render_html(self): ...
    def handle_errors(self): ...

# ✅ 良い例: 単一責任
class ConvertCommand:
    def __init__(self, parser: Parser, validator: Validator, 
                 renderer: Renderer, error_handler: ErrorHandler):
        ...
    
    def execute(self): ...
```

### 2️⃣ **依存関係の単方向性**

#### **レイヤー構造の厳格化**
```
┌─────────────────────────────────────┐
│  CLI Layer (cli.py, commands/)     │
├─────────────────────────────────────┤
│  Application Layer (parser.py,     │
│                     renderer.py)   │
├─────────────────────────────────────┤
│  Core Layer (core/)                │
├─────────────────────────────────────┤
│  Utilities Layer (utilities/)      │
└─────────────────────────────────────┘
```

#### **依存関係ルール**
- **上位レイヤー** → **下位レイヤー** のみ許可
- **逆方向依存** は Protocol/ABC で抽象化
- **循環依存** は自動検出で禁止

### 3️⃣ **インターフェース駆動設計**

#### **Protocol/ABC の積極活用**
```python
from typing import Protocol
from abc import ABC, abstractmethod

# インターフェース定義
class ErrorHandlerProtocol(Protocol):
    def handle_error(self, error: Exception, context: dict) -> None: ...

class ValidatorProtocol(Protocol):
    def validate(self, data: Any) -> ValidationResult: ...

# 実装クラス
class FileErrorHandler:
    def handle_error(self, error: Exception, context: dict) -> None:
        # ファイルエラー固有の処理
        pass

class SyntaxErrorHandler:
    def handle_error(self, error: Exception, context: dict) -> None:
        # 構文エラー固有の処理
        pass
```

### 4️⃣ **設定管理の一元化**

#### **統一設定システム**
```python
# 現在の問題: 複数の設定クラス
Config, SimpleConfig, EnhancedConfig

# 提案: 単一設定システム
class KumihanConfig:
    """アプリケーション全体の設定を管理"""
    
    @classmethod
    def from_file(cls, path: Path) -> 'KumihanConfig': ...
    
    @classmethod  
    def from_dict(cls, data: dict) -> 'KumihanConfig': ...
    
    @classmethod
    def default(cls) -> 'KumihanConfig': ...
```

---

## 🔧 自動品質管理

### **ファイルサイズ制限の自動チェック**
```bash
# pre-commit で自動実行
python dev/tools/check_file_size.py --max-lines=300
```

### **依存関係検証の自動チェック**
```bash
# CI/CD で自動実行
python dev/tools/dependency_validator.py
```

### **複雑度チェック**
```bash
# McCabe複雑度 10 以下を強制
radon cc --min B kumihan_formatter/
```

---

## 📋 開発フロー

### **新機能追加時のチェックリスト**
- [ ] 単一責任原則に準拠しているか？
- [ ] ファイルサイズ制限内か？
- [ ] 依存関係の方向は正しいか？
- [ ] インターフェースは適切に抽象化されているか？
- [ ] 自動テストは書かれているか？

### **コードレビュー時のチェックポイント**
- [ ] アーキテクチャ原則への準拠
- [ ] 将来の拡張性の考慮
- [ ] 責任分離の適切性
- [ ] エラーハンドリングの一貫性

---

## 🚨 禁止事項

### **絶対に避けるべきパターン**
1. **巨大ファイル**: 300行を超えるPythonファイル
2. **複数責任**: 1つのクラスが複数の責任を持つ
3. **循環依存**: モジュール間の相互依存
4. **重複実装**: 同じ機能の複数実装
5. **ハードコーディング**: 設定値の直接埋め込み

### **レガシーコードの段階的置換**
- 新機能は必ず新原則に準拠
- 既存コードは計画的にリファクタリング
- 互換性を保ちながら段階的移行

---

## 📊 品質メトリクス

### **継続監視指標**
- **ファイルサイズ**: 平均150行以下
- **関数サイズ**: 平均25行以下  
- **McCabe複雑度**: 平均5以下
- **依存関係数**: クラスあたり最大5依存
- **テストカバレッジ**: 80%以上

### **アラートライン**
- ファイルサイズ250行で警告
- 300行で自動拒否
- 複雑度8で警告、10で自動拒否

---

## 🔄 継続的改善

この原則は生きた文書として、プロジェクトの成長とともに更新されます。

**更新頻度**: 四半期ごとの見直し
**更新権限**: アーキテクトレビューによる承認制

---

*このアーキテクチャ原則は、Issue #319 で策定されました。*