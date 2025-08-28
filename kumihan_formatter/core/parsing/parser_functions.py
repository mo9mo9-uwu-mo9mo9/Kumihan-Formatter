"""Parser Functions - パーサー関数専用モジュール

parser.py分割により抽出 (Phase3最適化)
グローバルパーサー関数群
"""

from typing import List, Optional, Dict, Any

from ..ast_nodes import Node, error_node
import logging
from .parser_core import Parser


def parse(
    content: str, config: Optional[Dict[str, Any]] = None, use_parallel: bool = True
) -> List[Node]:
    """テキストを解析してASTノードのリストを返すメイン関数

    Args:
        content: 解析するテキストコンテンツ
        config: パーサー設定（オプション）
        use_parallel: 並列処理を使用するかどうか

    Returns:
        ASTノードのリスト
    """
    if not content:
        return []

    logger = logging.getLogger(__name__)

    try:
        # パーサーを作成して実行
        parser = Parser(config)
        result = parser.parse(content, use_parallel=use_parallel)

        # エラーがある場合はログに記録
        if parser.get_errors():
            logger.warning(
                f"解析中に{len(parser.get_errors())}件のエラーが発生しました"
            )
            for error in parser.get_errors()[:5]:  # 最初の5件のみログ
                logger.warning(f"  - {error}")

        # Gracefulエラーの報告
        if parser.has_graceful_errors():
            graceful_summary = parser.get_graceful_error_summary()
            logger.info(f"Gracefulエラー: {graceful_summary['count']}件")

        return result

    except Exception as e:
        logger.error(f"パーサー実行エラー: {e}")
        return [error_node(f"パーサー実行エラー: {str(e)}")]


def parse_with_error_config(
    content: str, error_config: Optional[Dict[str, Any]] = None
) -> tuple[List[Node], Dict[str, Any]]:
    """エラー設定付きでテキストを解析

    Args:
        content: 解析するテキストコンテンツ
        error_config: エラー処理設定

    Returns:
        (ASTノードのリスト, エラー統計情報)のタプル
    """
    if not content:
        return [], {"error_count": 0, "graceful_error_count": 0}

    logger = logging.getLogger(__name__)

    # デフォルトエラー設定
    default_error_config = {
        "enable_graceful_errors": True,
        "enable_correction_suggestions": True,
        "max_errors_per_line": 3,
        "stop_on_critical_error": False,
    }

    # 設定をマージ
    effective_config = {**default_error_config, **(error_config or {})}

    try:
        # エラー設定をパーサー設定に統合
        parser_config = {"error_handling": effective_config}

        parser = Parser(parser_config)
        result = parser.parse(content)

        # エラー統計を構築
        error_stats = {
            "error_count": len(parser.get_errors()),
            "graceful_error_count": len(parser.get_graceful_errors()),
            "total_lines": len(content.splitlines()),
            "performance_stats": parser.get_performance_statistics(),
            "graceful_error_summary": parser.get_graceful_error_summary(),
        }

        # 詳細エラー情報
        if effective_config.get("include_error_details", False):
            error_stats["errors"] = parser.get_errors()
            error_stats["graceful_errors"] = parser.get_graceful_errors()

        logger.info(
            f"エラー設定付き解析完了: "
            f"通常エラー{error_stats['error_count']}件, "
            f"Gracefulエラー{error_stats['graceful_error_count']}件"
        )

        return result, error_stats

    except Exception as e:
        logger.error(f"エラー設定付き解析エラー: {e}")
        error_stats = {
            "error_count": 1,
            "graceful_error_count": 0,
            "critical_error": str(e),
        }
        return [error_node(f"エラー設定付き解析エラー: {str(e)}")], error_stats


def parse_file(
    file_path: str, config: Optional[Dict[str, Any]] = None, encoding: str = "utf-8"
) -> List[Node]:
    """ファイルから読み込んで解析

    Args:
        file_path: ファイルパス
        config: パーサー設定
        encoding: ファイルエンコーディング

    Returns:
        ASTノードのリスト
    """
    import os
    from pathlib import Path

    logger = logging.getLogger(__name__)

    try:
        file_path = Path(file_path)

        # ファイル存在チェック
        if not file_path.exists():
            error_msg = f"ファイルが見つかりません: {file_path}"
            logger.error(error_msg)
            return [error_node(error_msg)]

        # ファイル読み込み
        try:
            content = file_path.read_text(encoding=encoding)
        except UnicodeDecodeError as e:
            error_msg = f"ファイル読み込みエラー (エンコーディング: {encoding}): {e}"
            logger.error(error_msg)
            return [error_node(error_msg)]

        logger.info(f"ファイル解析開始: {file_path} ({len(content)}文字)")

        # 解析実行
        result = parse(content, config)

        logger.info(f"ファイル解析完了: {file_path} ({len(result)}ノード)")
        return result

    except Exception as e:
        error_msg = f"ファイル解析エラー: {e}"
        logger.error(error_msg)
        return [error_node(error_msg)]


def parse_streaming(
    content_iterator, config: Optional[Dict[str, Any]] = None
) -> List[Node]:
    """ストリーミング形式で解析

    Args:
        content_iterator: コンテンツのイテレータ
        config: パーサー設定

    Returns:
        ASTノードのリスト
    """
    logger = logging.getLogger(__name__)

    try:
        # イテレータからコンテンツを収集
        content_chunks = []
        total_size = 0

        for chunk in content_iterator:
            if isinstance(chunk, bytes):
                chunk = chunk.decode("utf-8")

            content_chunks.append(chunk)
            total_size += len(chunk)

            # メモリ制限チェック（100MB）
            if total_size > 100 * 1024 * 1024:
                error_msg = "ストリーミング解析: コンテンツサイズが制限を超えました"
                logger.error(error_msg)
                return [error_node(error_msg)]

        # 全コンテンツを結合
        full_content = "".join(content_chunks)

        logger.info(f"ストリーミング解析: {total_size}文字のコンテンツ")

        # 通常の解析を実行
        return parse(full_content, config)

    except Exception as e:
        error_msg = f"ストリーミング解析エラー: {e}"
        logger.error(error_msg)
        return [error_node(error_msg)]


def validate_parse_config(config: Dict[str, Any]) -> tuple[bool, List[str]]:
    """パーサー設定を検証

    Args:
        config: 検証するパーサー設定

    Returns:
        (有効性, エラーメッセージリスト)のタプル
    """
    errors = []

    # 並列処理設定の検証
    if "parallel_processing" in config:
        parallel_config = config["parallel_processing"]

        if "max_workers" in parallel_config:
            if (
                not isinstance(parallel_config["max_workers"], int)
                or parallel_config["max_workers"] < 1
            ):
                errors.append("max_workers は1以上の整数である必要があります")

        if "chunk_size" in parallel_config:
            if (
                not isinstance(parallel_config["chunk_size"], int)
                or parallel_config["chunk_size"] < 10
            ):
                errors.append("chunk_size は10以上の整数である必要があります")

        if "timeout_seconds" in parallel_config:
            if (
                not isinstance(parallel_config["timeout_seconds"], (int, float))
                or parallel_config["timeout_seconds"] <= 0
            ):
                errors.append("timeout_seconds は正の数である必要があります")

    # エラーハンドリング設定の検証
    if "error_handling" in config:
        error_config = config["error_handling"]

        if "max_errors_per_line" in error_config:
            if (
                not isinstance(error_config["max_errors_per_line"], int)
                or error_config["max_errors_per_line"] < 1
            ):
                errors.append("max_errors_per_line は1以上の整数である必要があります")

    return len(errors) == 0, errors


def create_default_config() -> Dict[str, Any]:
    """デフォルトのパーサー設定を作成

    Returns:
        デフォルトパーサー設定
    """
    return {
        "parallel_processing": {
            "max_workers": None,  # 自動設定
            "chunk_size": 1000,
            "timeout_seconds": 30.0,
            "memory_limit_mb": 512.0,
            "enable_monitoring": True,
        },
        "error_handling": {
            "enable_graceful_errors": True,
            "enable_correction_suggestions": True,
            "max_errors_per_line": 3,
            "stop_on_critical_error": False,
            "include_error_details": False,
        },
        "performance": {
            "enable_optimization": True,
            "cache_parsed_results": False,
            "log_performance": True,
        },
    }
