"""
CSSユーティリティ機能
CSSProcessor分割版 - CSS最適化・検証・レスポンシブ機能
"""

import logging
import re
from typing import Any, Dict, List, Union, Optional


class CSSUtilities:
    """CSS ユーティリティクラス"""

    def __init__(self) -> None:
        """CSS ユーティリティ初期化"""
        self.logger = logging.getLogger(__name__)

    def minify_css(self, css: str) -> str:
        """CSS最小化"""
        # コメント除去
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)

        # 改行・余分な空白除去
        css = re.sub(r"\s+", " ", css)
        css = re.sub(r";\s*}", "}", css)
        css = re.sub(r"{\s+", "{", css)
        css = re.sub(r"}\s+", "}", css)
        css = re.sub(r":\s+", ":", css)
        css = re.sub(r";\s+", ";", css)

        return css.strip()

    def validate_css(self, css: str) -> List[str]:
        """CSS検証（基本）"""
        errors = []

        # 基本的な構文チェック
        brace_count = css.count("{") - css.count("}")
        if brace_count != 0:
            errors.append(f"ブレースの数が一致しません（差分: {brace_count}）")

        # 不正な文字チェック
        if re.search(r'[<>"]', css):
            errors.append("CSS内に不正な文字が含まれています")

        return errors

    def generate_responsive_styles(self) -> str:
        """レスポンシブスタイル生成"""
        return """
/* Responsive Styles */
@media (max-width: 768px) {
    body {
        font-size: 16px;
        line-height: 1.6;
        padding: 1em;
    }
    
    .content-heading.level-1 {
        font-size: 1.8em;
    }
    
    .content-heading.level-2 {
        font-size: 1.5em;
    }
    
    .table-of-contents {
        padding: 1em;
        margin: 1em 0;
    }
    
    .content-list {
        padding-left: 1.5em;
    }
}

@media (max-width: 480px) {
    .content-heading.level-1 {
        font-size: 1.6em;
    }
    
    .content-heading.level-2 {
        font-size: 1.3em;
    }
    
    .inline-code {
        word-break: break-all;
    }
}
"""

    def process_custom_styles(self, custom_css: Union[str, Dict[str, Any]]) -> str:
        """カスタムスタイル処理"""
        if isinstance(custom_css, str):
            return custom_css

        if isinstance(custom_css, dict):
            css_rules = []
            for selector, properties in custom_css.items():
                if isinstance(properties, dict):
                    props = "; ".join([f"{k}: {v}" for k, v in properties.items()])
                    css_rules.append(f"{selector} {{ {props}; }}")
                else:
                    css_rules.append(f"{selector} {{ {properties}; }}")

            return "\n".join(css_rules)

        # この行は到達しないがtype checkerのために残す
        # return ""

    def apply_css_classes(
        self, element_type: str, additional_classes: Optional[List[str]] = None
    ) -> str:
        """CSS クラス適用"""
        base_classes = self._get_base_classes(element_type)

        if additional_classes:
            base_classes.extend(additional_classes)

        return " ".join(base_classes)

    def get_inline_styles(
        self, element_type: str, custom_props: Optional[Dict[str, str]] = None
    ) -> str:
        """インライン スタイル取得"""
        base_styles = self._get_base_styles(element_type)

        if custom_props:
            base_styles.update(custom_props)

        if not base_styles:
            return ""

        style_props = [f"{k}: {v}" for k, v in base_styles.items()]
        return "; ".join(style_props)

    def _get_base_classes(self, element_type: str) -> List[str]:
        """基本CSSクラス取得"""
        class_map = {
            "paragraph": ["content-paragraph", "text-block"],
            "heading": ["content-heading", "section-title"],
            "list": ["content-list", "structured-list"],
            "strong": ["text-bold", "emphasis-strong"],
            "em": ["text-italic", "emphasis-em"],
            "code": ["inline-code", "syntax-highlight"],
            "section": ["content-section", "document-part"],
            "article": ["content-article", "main-content"],
            "aside": ["content-aside", "supplementary"],
            "toc": ["table-of-contents", "navigation-toc"],
            "footnotes": ["footnote-section", "reference-notes"],
            "error": ["error-display", "validation-error"],
            "responsive": ["responsive-content", "mobile-friendly"],
            "accessibility": ["screen-reader", "high-contrast"],
        }

        return class_map.get(element_type, [])

    def _get_base_styles(self, element_type: str) -> Dict[str, str]:
        """基本インラインスタイル取得"""
        style_map = {
            "paragraph": {"margin": "1em 0", "line-height": "1.6"},
            "heading": {"margin-top": "1.5em", "font-weight": "bold"},
            "code": {"font-family": "monospace", "padding": "0.2em 0.4em"},
            "error": {
                "color": "#c53030",
                "background-color": "#fed7d7",
                "padding": "0.5em",
            },
        }

        return style_map.get(element_type, {})

    def get_css_classes_reference(self) -> Dict[str, List[str]]:
        """CSSクラス参照一覧取得"""
        return {
            # 基本要素
            "paragraph": ["content-paragraph", "text-block"],
            "heading": ["content-heading", "section-title"],
            "list": ["content-list", "structured-list"],
            # 強調要素
            "strong": ["text-bold", "emphasis-strong"],
            "em": ["text-italic", "emphasis-em"],
            "code": ["inline-code", "syntax-highlight"],
            # 構造要素
            "section": ["content-section", "document-part"],
            "article": ["content-article", "main-content"],
            "aside": ["content-aside", "supplementary"],
            # 特殊要素
            "toc": ["table-of-contents", "navigation-toc"],
            "footnotes": ["footnote-section", "reference-notes"],
            "error": ["error-display", "validation-error"],
            # レスポンシブクラス
            "responsive": ["responsive-content", "mobile-friendly"],
            "accessibility": ["screen-reader", "high-contrast"],
        }
