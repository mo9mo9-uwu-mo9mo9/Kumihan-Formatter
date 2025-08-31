"""Types Module - 型定義

Issue #1217対応: ディレクトリ構造最適化による型定義系統合モジュール
Issue #1259対応: chunk_types.pyをdocument_types.pyに統合
"""

# 型定義関連クラス・関数の公開
from .document_types import DocumentType, ChunkInfo
from .toc_types import TOCEntry

__all__ = [
    # 文書型定義
    "DocumentType",
    # 目次型定義
    "TOCEntry",
    # チャンク型定義（document_types.pyに統合済み）
    "ChunkInfo",
]
