"""型安全な設定モデル

pydantic BaseModelを使用した設定管理
Issue #370対応 - 型安全性強化
"""

from pydantic import BaseModel, Field


class FormatterConfig(BaseModel):
    """Kumihan-Formatter設定モデル

    型安全な設定管理のためのpydantic BaseModel
    """

    # 基本設定
    input_encoding: str = Field(default="utf-8", description="入力ファイルの文字エンコーディング")
    output_encoding: str = Field(default="utf-8", description="出力ファイルの文字エンコーディング")

    # テンプレート設定
    template_dir: str | None = Field(default=None, description="テンプレートディレクトリのパス")
    template_name: str | None = Field(default=None, description="使用するテンプレート名")

    # 変換設定
    strict_mode: bool = Field(default=False, description="厳密モードで実行")
    include_source: bool = Field(default=False, description="ソース表示機能を含める")
    syntax_check: bool = Field(default=True, description="構文チェックを実行")

    # 出力設定
    no_preview: bool = Field(default=False, description="プレビューをスキップ")
    watch_mode: bool = Field(default=False, description="ファイル変更監視モード")

    # CSS設定
    css_variables: dict[str, str] = Field(
        default_factory=lambda: {
            "max_width": "800px",
            "background_color": "#f9f9f9",
            "container_background": "white",
            "text_color": "#333",
            "line_height": "1.8",
            "font_family": (
                "Hiragino Kaku Gothic ProN, Hiragino Sans, " "Yu Gothic, Meiryo, sans-serif"
            ),
        },
        description="CSS変数の辞書",
    )

    class Config:
        """pydantic設定"""

        extra = "forbid"  # 未定義フィールドを禁止
        validate_assignment = True  # 代入時の検証を有効化
        str_strip_whitespace = True  # 文字列の前後空白を自動削除


class SimpleFormatterConfig(BaseModel):
    """簡素化された設定モデル

    初心者向けの簡素化された設定
    """

    # 基本設定のみ
    template_name: str = Field(default="default", description="テンプレート名")
    include_source: bool = Field(default=False, description="ソース表示機能")

    # 固定CSS設定
    css_variables: dict[str, str] = Field(
        default_factory=lambda: {
            "max_width": "800px",
            "background_color": "#f9f9f9",
            "container_background": "white",
            "text_color": "#333",
            "line_height": "1.8",
            "font_family": (
                "Hiragino Kaku Gothic ProN, Hiragino Sans, " "Yu Gothic, Meiryo, sans-serif"
            ),
        },
        description="CSS変数の辞書",
    )

    class Config:
        """pydantic設定"""

        extra = "forbid"
        validate_assignment = True
        str_strip_whitespace = True

    def get_theme_name(self) -> str:
        """テーマ名を取得"""
        return "デフォルト"
