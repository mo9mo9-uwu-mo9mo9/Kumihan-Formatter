from typing import Dict, Optional

"""HTML Color Processing - 色処理専用モジュール

HTMLFormatter分割により抽出 (Phase3最適化)
色関連の処理をすべて統合
"""


class HTMLColorProcessor:
    """HTML色処理専用クラス"""

    def __init__(self) -> None:
        self.supported_color_formats = ["hex", "rgb", "rgba", "hsl", "named"]

    def process_color_attribute(
        self, color_value: str, attribute_name: str = "color"
    ) -> str:
        """色属性を処理してCSSスタイルを生成"""
        if not color_value or not color_value.strip():
            return ""

        color_value = color_value.strip()

        # Hex color (#RGB or #RRGGBB)
        if color_value.startswith("#"):
            normalized_color = self._normalize_hex_color(color_value)
            if normalized_color:
                return f"{attribute_name}: {normalized_color};"

        # RGB/RGBA color
        elif color_value.startswith(("rgb(", "rgba(")):
            normalized_color = self._normalize_rgb_color(color_value)
            if normalized_color:
                return f"{attribute_name}: {normalized_color};"

        # Named color
        else:
            named_colors = self._get_named_colors()
            if color_value.lower() in named_colors:
                return f"{attribute_name}: {color_value.lower()};"

        return ""

    def _normalize_hex_color(self, hex_color: str) -> Optional[str]:
        """16進数カラーコードを正規化"""
        if not hex_color.startswith("#"):
            return None

        hex_part = hex_color[1:]

        # 3桁の場合は6桁に展開
        if len(hex_part) == 3:
            hex_part = "".join(c * 2 for c in hex_part)

        # 6桁の16進数かチェック
        if len(hex_part) == 6 and all(c in "0123456789ABCDEFabcdef" for c in hex_part):
            return f"#{hex_part.lower()}"

        return None

    def _normalize_rgb_color(self, rgb_color: str) -> Optional[str]:
        """RGB/RGBAカラーを正規化"""
        import re

        # rgb(r, g, b) または rgba(r, g, b, a) の形式をチェック
        rgb_pattern = (
            r"^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)$"
        )
        match = re.match(rgb_pattern, rgb_color.replace(" ", ""))

        if match:
            r, g, b, a = match.groups()
            r, g, b = int(r), int(g), int(b)

            # RGB値の範囲チェック
            if all(0 <= val <= 255 for val in [r, g, b]):
                if a is not None:
                    a_val = float(a)
                    if 0 <= a_val <= 1:
                        return f"rgba({r}, {g}, {b}, {a_val})"
                else:
                    return f"rgb({r}, {g}, {b})"

        return None

    def _get_named_colors(self) -> Dict[str, str]:
        """サポートされている名前付きカラーを取得"""
        return {
            "black": "#000000",
            "white": "#ffffff",
            "red": "#ff0000",
            "green": "#008000",
            "blue": "#0000ff",
            "yellow": "#ffff00",
            "cyan": "#00ffff",
            "magenta": "#ff00ff",
            "orange": "#ffa500",
            "purple": "#800080",
            "pink": "#ffc0cb",
            "brown": "#a52a2a",
            "gray": "#808080",
            "grey": "#808080",
            "darkred": "#8b0000",
            "darkgreen": "#006400",
            "darkblue": "#00008b",
            "lightblue": "#add8e6",
            "lightgreen": "#90ee90",
            "lightgray": "#d3d3d3",
            "lightgrey": "#d3d3d3",
        }
