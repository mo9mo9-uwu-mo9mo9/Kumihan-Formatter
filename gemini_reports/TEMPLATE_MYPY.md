# Gemini協業指示書 - MyPy修正テンプレート

## 作業概要
- **作業種別**: MyPy Strict Mode エラー修正
- **対象**: `kumihan_formatter/` パッケージ全体
- **自動化レベル**: SEMI_AUTO
- **推定Token削減**: 85-90%

## 🎯 修正対象エラーパターン

### 1. no-any-return エラー
```python
# ❌ 修正前
def validator_function(cls, v: Any, info: Any) -> None:
    return v

# ✅ 修正後  
def validator_function(cls, v: Any, info: Any) -> Any:
    return v
```

### 2. untyped-def エラー
```python
# ❌ 修正前
def function(param):
    return param

# ✅ 修正後
def function(param: Any) -> Any:
    return param
```

### 3. attr-defined エラー
```python
# ❌ 修正前
if hasattr(obj, 'method'):
    return obj.method()

# ✅ 修正後
if hasattr(obj, 'method'):
    result = obj.method()
    return result if isinstance(result, dict) else {}
```

## 📋 実行手順

### Step 1: 現状確認
```bash
cd /path/to/Kumihan-Formatter
python3 -m mypy kumihan_formatter --strict
```

### Step 2: エラー解析・修正計画
- エラー数・種別を確認
- 修正対象ファイルをリストアップ
- 修正パターンを決定

### Step 3: ファイル別修正実行
- **config_models.py**: Pydantic validator return型修正
- **config_manager.py**: hasattr型安全性向上
- **その他**: 検出されたファイルを順次修正

### Step 4: 修正後検証
```bash
# 構文チェック（Layer 1）
python3 -c "import ast; [ast.parse(open(f).read()) for f in ['修正ファイル1', '修正ファイル2']]"

# 品質チェック（Layer 2）  
python3 -m mypy kumihan_formatter --strict
python3 -m flake8 kumihan_formatter
```

## 🛡️ 品質保証チェックリスト

### 必須確認項目
- [ ] 全MyPyエラー解消（0 errors）
- [ ] 既存テストの通過確認
- [ ] 構文エラーの発生確認
- [ ] インポート・依存関係の正常性
- [ ] 型注釈の一貫性

### リスク回避
- [ ] 元ファイルのバックアップ作成
- [ ] 段階的修正（1ファイルずつ検証）
- [ ] 修正影響範囲の最小化
- [ ] エラー発生時の即座停止・報告

## 📊 報告書フォーマット

### 修正完了報告
```markdown
## MyPy Strict Mode 修正完了報告

### 修正結果
- **修正前エラー数**: X件
- **修正後エラー数**: 0件  
- **修正ファイル数**: Y件
- **所要時間**: Z分

### 修正内容詳細
1. config_models.py: validator return型 None→Any (3箇所)
2. config_manager.py: hasattr型ガード追加 (2箇所)

### 品質検証結果
✅ python3 -m mypy kumihan_formatter --strict
   Success: no issues found in 241 source files

### Claude確認依頼項目
- [ ] 修正内容の妥当性レビュー
- [ ] 型安全性向上の確認
- [ ] 他システムへの影響評価
```

## ⚠️ 緊急時対応

### エラー発生時
1. **即座作業停止**
2. **エラー詳細ログ取得**
3. **Claude報告・支援要請**
4. **必要に応じてロールバック**

### フェイルセーフ基準
- 構文エラー発生 → 即座停止
- テスト失敗 → 修正内容見直し
- 予期しない副作用 → Claude引き継ぎ

---
*テンプレート生成日: 2025-08-14*  
*Issue #876反省改善 - 定型作業効率化*