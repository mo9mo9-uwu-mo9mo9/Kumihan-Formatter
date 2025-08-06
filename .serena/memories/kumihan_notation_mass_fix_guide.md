# Kumihan記法 大規模エラー修正ガイド

> Issue #726 (2025-08-02) での516-2595エラー完全解決経験をベースとした実践的修正手順

## 🎯 修正戦略の基本原則

### 段階的エラー減少アプローチ
- **一度に全修正を狙わない** - 段階的に確実にエラーを減らす
- **修正結果を即座に検証** - `python3 -m kumihan_formatter check-syntax` で効果確認
- **安全な巻き戻し確保** - `git checkout HEAD -- ファイル名` でいつでも復旧可能

### 実績パターン (Issue #726)
```
12_heavy_decoration_7k.txt: 2595 → 516 → 83 → 30 → 0 (100%解決)
11_complex_nested_5k.txt:    2241 → 1225 → 219 → 0 (100%解決)
```

## 🔧 修正スクリプトテンプレート

### 基本構造
```python
#!/usr/bin/env python3
"""
{対象ファイル}用の修正スクリプト - {具体的な修正内容}
"""
import re
import sys
from pathlib import Path

def fix_patterns(content: str) -> str:
    """修正パターンの実装"""
    
    # 全角マーカーを半角に統一（必須前処理）
    content = content.replace('＃', '#')
    
    # パターン1: 具体的修正ロジック
    content = re.sub(r'パターン正規表現', r'置換後', content)
    
    return content

def main():
    """メイン処理 - 複数ファイル対応"""
    files = [
        "samples/performance/ファイル1.txt",
        "samples/practical/ファイル2.txt"
    ]
    
    for file_path_str in files:
        file_path = Path(file_path_str)
        
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
            
        print(f"Processing: {file_path}")
        
        # 安全な読み書き処理
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            continue
        
        fixed_content = fix_patterns(original_content)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"✅ Fixed: {file_path}")
        except Exception as e:
            print(f"Error writing file: {e}")
            continue

if __name__ == "__main__":
    main()
```

## 📋 実証済み修正パターン集

### 1. 16進数カラーコード問題
```python
# パターン: プライマリカラーは#4169e1、 → プライマリカラーは色コード4169e1、
content = re.sub(r'([ぁ-ん]|[ァ-ヴ]|[一-龯]|[a-zA-Z0-9])#([0-9a-fA-F]{6})([、。を])', r'\1色コード\2\3', content)
content = re.sub(r'は\s*#([0-9a-fA-F]{6})', r'は色コード\1', content)
content = re.sub(r'(?<!\w)#([0-9a-fA-F]{6})(?!\w)', r'色コード\1', content)
```

### 2. 不正##マーカー除去
```python
# パターン: データベース##。 → データベース。
content = re.sub(r'([ぁ-ん]|[ァ-ヴ]|[一-龯]|[a-zA-Z0-9])\s*##\s*([。、！？])', r'\1\2', content)
content = re.sub(r'データベース\s*##\s*。', 'データベース。', content)
```

### 3. 未完了マーカー → ブロック記法変換
```python
# パターン: イタリック # 85% → イタリック #\n85%\n##
content = re.sub(
    r'^(\s*)([^#\n]+)\s*#\s*(\d+%)$',
    r'\1\2 #\n\1\3\n\1##',
    content,
    flags=re.MULTILINE
)
```

### 4. color属性付き修正
```python
# パターン: color=色コード008000 # 下線装飾 → ブロック化
content = re.sub(
    r'(color=色コード[0-9a-fA-F]{6})\s*#\s*([^#\n]+)',
    r'\1 #\n\2\n##',
    content
)
```

### 5. 装飾例文パターン
```python
# パターン: ##色コード000080色を使用した装飾の例として、 → 色コード000080色を使用した装飾の例として、
content = re.sub(
    r'##色コード([0-9a-fA-F]{6})色を使用した([^#\n]+)',
    r'色コード\1色を使用した\2',
    content
)
```

## 📊 効率的検証フロー

### 修正前エラー数確認
```bash
python3 -m kumihan_formatter check-syntax ファイル名.txt
```

### 修正実行
```bash
python3 fix_スクリプト名.py
```

### 修正後結果確認
```bash
python3 -m kumihan_formatter check-syntax ファイル名.txt
```

### 問題発生時の巻き戻し
```bash
git checkout HEAD -- ファイル名.txt
```

## 🎯 TodoWrite活用パターン

```python
# 修正作業の進捗管理
todos = [
    {"content": "エラーパターン分析", "status": "in_progress", "priority": "high", "id": "analyze"},
    {"content": "16進数カラーコード修正", "status": "pending", "priority": "high", "id": "fix_colors"},
    {"content": "不正##マーカー修正", "status": "pending", "priority": "high", "id": "fix_markers"},
    {"content": "最終ゼロエラー確認", "status": "pending", "priority": "high", "id": "final_check"}
]
```

## 🚨 注意事項・失敗回避

### 避けるべき修正パターン
- **過度に汎用的な正規表現** - 予期しない置換が発生
- **一度の大量修正** - エラー発生時の原因特定困難
- **バックアップなし修正** - Git管理下で作業必須

### 成功要因
- **具体的パターンの段階的修正** - 1つずつ確実に
- **即座の結果検証** - 修正効果の定量的確認
- **安全な巻き戻し機能** - git checkout活用

## 📈 効果測定

### Issue #726実績
- **総エラー数**: 4836個 → 0個 (100%解決)
- **作業時間**: 複数セッション
- **修正スクリプト数**: 7個
- **成功要因**: 段階的アプローチ + パターン分析

---
*✨ 2025-08-02 Issue #726完全解決経験より抽出 - 大規模記法修正の実践的ガイド*