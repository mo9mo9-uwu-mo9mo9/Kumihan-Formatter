"""GUI Theme Configuration

モダンなUIテーマ設定（2025年基準）
"""

import customtkinter as ctk


class KumihanTheme:
    """Kumihan-Formatter用モダンテーマ設定"""

    # カラーパレット（モダンで上品）
    PRIMARY_COLOR = "#2563EB"  # ブルー（メイン）
    SECONDARY_COLOR = "#7C3AED"  # パープル（アクセント）
    SUCCESS_COLOR = "#10B981"  # グリーン（成功）
    WARNING_COLOR = "#F59E0B"  # アンバー（警告）
    ERROR_COLOR = "#EF4444"  # レッド（エラー）

    # 背景・テキスト
    BG_PRIMARY = "#FFFFFF"  # メイン背景
    BG_SECONDARY = "#F8FAFC"  # セカンダリ背景
    BG_HOVER = "#E2E8F0"  # ホバー時
    TEXT_PRIMARY = "#1E293B"  # メインテキスト
    TEXT_SECONDARY = "#64748B"  # セカンダリテキスト

    # ボーダー・その他
    BORDER_COLOR = "#CBD5E1"
    SHADOW_COLOR = "#0F172A20"

    @classmethod
    def apply_modern_theme(cls) -> None:
        """モダンテーマを適用"""
        ctk.set_appearance_mode("light")  # ライトモード固定
        ctk.set_default_color_theme("blue")  # デフォルトはブルー

        # カスタムカラー設定
        ctk.set_widget_scaling(1.0)  # デフォルトスケール
        ctk.set_window_scaling(1.0)  # ウィンドウスケール

    @classmethod
    def get_button_style(cls, button_type: str = "primary") -> dict:
        """ボタンスタイル設定を取得"""
        styles = {
            "primary": {
                "fg_color": cls.PRIMARY_COLOR,
                "hover_color": "#1D4ED8",
                "text_color": "#FFFFFF",
                "corner_radius": 8,
                "height": 40,
                "font": ("Helvetica", 14, "bold"),
            },
            "secondary": {
                "fg_color": cls.BG_SECONDARY,
                "hover_color": cls.BG_HOVER,
                "text_color": cls.TEXT_PRIMARY,
                "border_width": 1,
                "border_color": cls.BORDER_COLOR,
                "corner_radius": 8,
                "height": 40,
                "font": ("Helvetica", 14),
            },
            "success": {
                "fg_color": cls.SUCCESS_COLOR,
                "hover_color": "#059669",
                "text_color": "#FFFFFF",
                "corner_radius": 8,
                "height": 40,
                "font": ("Helvetica", 14, "bold"),
            },
        }
        return styles.get(button_type, styles["primary"])

    @classmethod
    def get_frame_style(cls) -> dict:
        """フレームスタイル設定を取得"""
        return {
            "fg_color": cls.BG_PRIMARY,
            "corner_radius": 12,
            "border_width": 1,
            "border_color": cls.BORDER_COLOR,
        }

    @classmethod
    def get_label_style(cls, label_type: str = "primary") -> dict:
        """ラベルスタイル設定を取得"""
        styles = {
            "primary": {"text_color": cls.TEXT_PRIMARY, "font": ("Helvetica", 14)},
            "secondary": {"text_color": cls.TEXT_SECONDARY, "font": ("Helvetica", 12)},
            "title": {
                "text_color": cls.TEXT_PRIMARY,
                "font": ("Helvetica", 18, "bold"),
            },
        }
        return styles.get(label_type, styles["primary"])
