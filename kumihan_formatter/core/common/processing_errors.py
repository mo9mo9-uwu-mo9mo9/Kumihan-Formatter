"""
共通処理エラークラス定義

複数のモジュールで重複していたエラークラスを統合
Issue #1259: ファイル数削減・構造最適化対応
"""


class ParallelProcessingError(Exception):
    """並列処理固有のエラー

    並列処理実行中に発生するエラーを表現する例外クラス。
    プロセス間通信、リソース競合、タイムアウト等の問題を示す。

    Examples:
        >>> raise ParallelProcessingError("プロセス間でのデータ競合が発生")
    """

    pass


class ChunkProcessingError(Exception):
    """チャンク処理でのエラー

    テキストをチャンク単位で処理する際に発生するエラー。
    チャンク分割失敗、処理中断、結果統合失敗等を示す。

    Examples:
        >>> raise ChunkProcessingError("チャンクサイズが制限を超過")
    """

    pass


class MemoryMonitoringError(Exception):
    """メモリ監視でのエラー

    メモリ使用量監視システムで発生するエラー。
    メモリ制限超過、監視システム障害、リソース不足等を示す。

    Examples:
        >>> raise MemoryMonitoringError("メモリ使用量が制限値250MBを超過")
    """

    pass


# パーサー系エラー
class SpecializedParsingError(Exception):
    """特殊化パーサー固有のエラー"""
    pass


class MarkerValidationError(Exception):
    """マーカー検証エラー"""
    pass


class FormatProcessingError(Exception):
    """フォーマット処理エラー"""
    pass


class ParserUtilsError(Exception):
    """パーサーユーティリティ固有のエラー"""
    pass


class KeywordValidationError(Exception):
    """キーワード検証エラー"""
    pass


class ExtractionError(Exception):
    """抽出処理エラー"""
    pass


__all__ = [
    "ParallelProcessingError",
    "ChunkProcessingError",
    "MemoryMonitoringError",
    "SpecializedParsingError",
    "MarkerValidationError",
    "FormatProcessingError",
    "ParserUtilsError",
    "KeywordValidationError",
    "ExtractionError",
]
