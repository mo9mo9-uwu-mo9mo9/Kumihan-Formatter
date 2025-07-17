"""
ベンチマーク分析器 - 統合クラス（後方互換性）

ベンチマーク結果の分析とパフォーマンス回帰検出
Issue #492 Phase 5A - 分割により300行制限対応

注意: このクラスは後方互換性のため保持。
新しい実装は分割されたモジュールを使用:
- benchmark_analyzer_core: メイン分析機能
- benchmark_regression_analyzer: 回帰分析
- benchmark_statistics: 統計計算
- benchmark_formatters: フォーマット処理
"""

from typing import Any

from .benchmark_analyzer_core import BenchmarkAnalyzerCore
from .benchmark_types import BenchmarkResult, BenchmarkSummary


class BenchmarkAnalyzer(BenchmarkAnalyzerCore):
    """ベンチマーク結果分析器 - 統合クラス（後方互換性）

    注意: このクラスは既存コードとの互換性のため保持。
    新規開発では分割されたモジュールを直接使用することを推奨。

    機能:
    - 分割されたコンポーネントの統合
    - 既存APIの維持
    - ベンチマーク分析機能の提供
    """

    def __init__(self) -> None:
        """ベンチマーク分析器を初期化（統合版）"""
        # BenchmarkAnalyzerCoreで初期化（分離されたコンポーネントを含む）
        super().__init__()

    # 既存のメソッドは全てBenchmarkAnalyzerCoreから継承
    # 追加の互換性メソッドがあれば以下に定義
