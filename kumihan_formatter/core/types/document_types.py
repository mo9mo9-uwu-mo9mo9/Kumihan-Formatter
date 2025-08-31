"""Document Types Definition
文書タイプの定義 - Issue #118対応
"""

from enum import Enum


class DocumentType(Enum):
    """文書タイプの分類"""

    USER_ESSENTIAL = "user_essential"  # 最重要ユーザー文書（.txt化）
    USER_GUIDE = "user_guide"  # ユーザーガイド（HTML化）
    DEVELOPER = "developer"  # 開発者向け文書（Markdownのまま）
    TECHNICAL = "technical"  # 技術文書（開発者ディレクトリ）
    EXCLUDE = "exclude"  # 配布から除外
    EXAMPLE = "example"  # サンプルファイル
    GENERAL = "general"  # 一般文書（デフォルト）


def get_type_display_names() -> dict[DocumentType, str]:
    """文書タイプの表示名を取得"""
    return {
        DocumentType.USER_ESSENTIAL: "🎯 重要文書（.txt変換）",
        DocumentType.USER_GUIDE: "📖 ユーザーガイド（HTML変換）",
        DocumentType.DEVELOPER: "🔧 開発者文書",
        DocumentType.TECHNICAL: "⚙️ 技術文書",
        DocumentType.EXAMPLE: "📝 サンプル・例",
        DocumentType.EXCLUDE: "🚫 除外対象",
        DocumentType.GENERAL: "📄 一般文書",
    }


# チャンク関連型定義（chunk_types.pyから統合）
from dataclasses import dataclass
from typing import List


@dataclass
class ChunkInfo:
    """チャンク情報"""

    chunk_id: int
    start_line: int
    end_line: int
    lines: List[str]
    file_position: int
