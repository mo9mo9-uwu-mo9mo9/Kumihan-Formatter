"""
CSS関連のユーティリティ機能
Phase 2のCSS依存問題対応
"""

import os
from pathlib import Path
from typing import Optional


def get_default_css_path() -> Path:
    """デフォルトCSSファイルのパスを取得
    
    Returns:
        Path: デフォルトCSSファイルのパス
    """
    # kumihan_formatterパッケージのルートディレクトリを取得
    current_dir = Path(__file__).parent.parent.parent
    css_path = current_dir / "assets" / "default-styles.css"
    return css_path


def load_default_css() -> str:
    """デフォルトCSSの内容を読み込み
    
    Returns:
        str: CSSの内容
        
    Raises:
        FileNotFoundError: CSSファイルが見つからない場合
    """
    css_path = get_default_css_path()
    
    if not css_path.exists():
        raise FileNotFoundError(f"デフォルトCSSファイルが見つかりません: {css_path}")
    
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"CSSファイルの読み込みに失敗しました: {e}")


def get_css_requirements() -> dict[str, list[str]]:
    """各キーワードのCSS要件を取得
    
    Returns:
        dict: キーワード名をキー、必要なCSSクラス一覧を値とする辞書
    """
    return {
        "注意": ["alert", "warning"],
        "情報": ["alert", "info"],
        # 他のキーワードはstyle属性またはCSSなしで動作
        "中央寄せ": [],  # style属性で対応
        "取り消し線": [],  # ブラウザ標準で対応
        "コード": [],  # 基本スタイルは任意
        "引用": [],  # 基本スタイルは任意
        "コードブロック": [],  # 基本スタイルは任意
    }


def validate_css_availability(css_content: str) -> dict[str, bool]:
    """CSSの利用可能性を検証
    
    Args:
        css_content: 検証するCSS内容
        
    Returns:
        dict: キーワード名をキー、CSS利用可能性を値とする辞書
    """
    requirements = get_css_requirements()
    availability = {}
    
    for keyword, required_classes in requirements.items():
        if not required_classes:
            # CSS不要なキーワードは常に利用可能
            availability[keyword] = True
        else:
            # 必要なクラスがすべて含まれているかチェック
            all_classes_available = all(
                f".{cls}" in css_content or f".{cls} " in css_content 
                for cls in required_classes
            )
            availability[keyword] = all_classes_available
    
    return availability


def generate_css_documentation() -> str:
    """CSS要件のドキュメントを生成
    
    Returns:
        str: CSS要件説明のMarkdown文書
    """
    requirements = get_css_requirements()
    
    doc = """# Phase 2キーワードのCSS要件

## 概要
Phase 2で追加されたキーワードの一部は、適切な表示のためにCSSスタイルが必要です。

## キーワード別CSS要件

### CSS必須キーワード

"""
    
    css_required = {k: v for k, v in requirements.items() if v}
    css_optional = {k: v for k, v in requirements.items() if not v}
    
    for keyword, classes in css_required.items():
        doc += f"#### `{keyword}`キーワード\n"
        doc += f"- 必要なCSSクラス: `{', '.join(classes)}`\n"
        doc += f"- 使用例: `<div class=\"{' '.join(classes)}\">内容</div>`\n\n"
    
    doc += """### CSS任意キーワード

以下のキーワードはCSSなしでも動作しますが、スタイルを適用することで見た目を改善できます。

"""
    
    for keyword in css_optional.keys():
        doc += f"- `{keyword}`\n"
    
    doc += """
## デフォルトCSSの使用

Kumihan-Formatterは基本的なスタイルを提供しています：

```python
from kumihan_formatter.core.utilities.css_utils import load_default_css

# デフォルトCSSを取得
default_css = load_default_css()
```

## カスタムCSS

デフォルトスタイルをカスタマイズしたい場合は、同じクラス名を使用して独自のCSSを作成してください。

"""
    
    return doc


def is_css_dependent_keyword(keyword: str) -> bool:
    """キーワードがCSS依存かどうかを判定
    
    Args:
        keyword: 判定するキーワード名
        
    Returns:
        bool: CSS依存の場合True
    """
    requirements = get_css_requirements()
    return bool(requirements.get(keyword, []))


def get_missing_css_classes(keyword: str, css_content: str) -> list[str]:
    """指定キーワードで不足しているCSSクラスを取得
    
    Args:
        keyword: チェックするキーワード名
        css_content: 検証するCSS内容
        
    Returns:
        list: 不足しているCSSクラス名のリスト
    """
    requirements = get_css_requirements()
    required_classes = requirements.get(keyword, [])
    
    missing_classes = []
    for cls in required_classes:
        if f".{cls}" not in css_content and f".{cls} " not in css_content:
            missing_classes.append(cls)
    
    return missing_classes