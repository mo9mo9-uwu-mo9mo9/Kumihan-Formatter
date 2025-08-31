"""parsers パッケージ（Phase 2: 公開API最小化）

本パッケージのトップレベル再エクスポートは段階的に廃止しました。
以降は必要なクラス/関数を各モジュールから直接 import してください。

例:
    from kumihan_formatter.parsers.unified_list_parser import UnifiedListParser
    from kumihan_formatter.parsers.main_parser import MainParser

注記:
- 互換目的のトップレベル名（Unified* / CoreParser 等）の公開は停止しました。
- 公開APIは AGENTS.md の「公開API（現時点）」に準拠し、parsers 配下は内部扱いです。
"""

from __future__ import annotations

import warnings

__all__: list[str] = []

# パッケージレベルの import による利用を抑止するため、読み込み時に一度だけ警告します。
warnings.warn(
    "kumihan_formatter.parsers のトップレベル再エクスポートは廃止されました。"
    "必要なシンボルは各モジュールから直接 import してください (Phase 2).",
    DeprecationWarning,
    stacklevel=2,
)
