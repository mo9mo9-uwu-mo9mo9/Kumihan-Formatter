"""チャンク関連型定義 - 循環インポート解決用"""

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
