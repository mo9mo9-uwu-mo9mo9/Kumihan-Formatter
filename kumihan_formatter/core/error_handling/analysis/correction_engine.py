"""
修正提案エンジン
Issue #700対応 - 高度なエラー表示機能

具体的な修正提案を自動生成するエンジン
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List

from ...common.error_base import GracefulSyntaxError
from ...utilities.logger import get_logger


@dataclass
class CorrectionRule:
    """修正ルール定義"""

    pattern: str  # エラーパターン（正規表現）
    suggestions: List[str]  # 修正提案リスト
    priority: int = 1  # 優先度（高いほど優先）
    error_type: str = ""  # エラー種別


class CorrectionEngine:
    """
    修正提案自動生成エンジン

    機能:
    - エラーパターンの分析
    - 具体的な修正提案の生成
    - コンテキストに基づく提案の調整
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.correction_rules: List[CorrectionRule] = []
        self._initialize_rules()

    def _initialize_rules(self) -> None:
        """修正ルールを初期化"""
        # 基本的なマーカー修正ルール
        self.correction_rules.extend(
            [
                CorrectionRule(
                    pattern=r"incomplete.*marker",
                    suggestions=[
                        "マーカーを完全な形式「# キーワード #」に修正してください",
                        "終了マーカー「#」が不足している可能性があります",
                        "半角・全角文字の混在を確認してください",
                    ],
                    priority=3,
                    error_type="incomplete_marker",
                ),
                CorrectionRule(
                    pattern=r"marker.*mismatch",
                    suggestions=[
                        "開始マーカーと終了マーカーの種類を統一してください",
                        "「##」で正しく終了させてください",
                        "ネストされたマーカーの順序を確認してください",
                    ],
                    priority=3,
                    error_type="marker_mismatch",
                ),
                CorrectionRule(
                    pattern=r"invalid.*syntax",
                    suggestions=[
                        "記法の構文を確認してください",
                        "半角スペースと全角スペースの使い分けを確認してください",
                        "特殊文字のエスケープが必要な場合があります",
                    ],
                    priority=2,
                    error_type="invalid_syntax",
                ),
                CorrectionRule(
                    pattern=r"missing.*element",
                    suggestions=[
                        "必要な要素が不足しています",
                        "記法の完全な形式を確認してください",
                        "前後のコンテキストとの整合性を確認してください",
                    ],
                    priority=2,
                    error_type="missing_element",
                ),
                CorrectionRule(
                    pattern=r"color.*invalid",
                    suggestions=[
                        "カラーコードは「#」で始まる16進数形式で入力してください",
                        "有効な色名（red, blue, green等）を使用してください",
                        "カラー属性の構文「color=#ff0000」を確認してください",
                    ],
                    priority=2,
                    error_type="invalid_color",
                ),
            ]
        )

        self.logger.info(f"Initialized {len(self.correction_rules)} correction rules")

    def generate_suggestions(self, error: GracefulSyntaxError) -> List[str]:
        """エラーに対する修正提案を生成"""
        suggestions: List[str] = []

        # ルールベースの提案生成
        rule_suggestions = self._apply_correction_rules(error)
        suggestions.extend(rule_suggestions)

        # コンテキストベースの提案生成
        context_suggestions = self._generate_context_suggestions(error)
        suggestions.extend(context_suggestions)

        # 重複を除去し、優先度でソート
        unique_suggestions = list(dict.fromkeys(suggestions))  # 順序を保持して重複除去

        self.logger.debug(
            f"Generated {len(unique_suggestions)} suggestions for error: {error.error_type}"
        )

        return unique_suggestions[:5]  # 最大5つの提案

    def _apply_correction_rules(self, error: GracefulSyntaxError) -> List[str]:
        """ルールベースの修正提案を適用"""
        suggestions: List[str] = []
        message_lower = error.message.lower()

        for rule in sorted(
            self.correction_rules, key=lambda r: r.priority, reverse=True
        ):
            if re.search(rule.pattern, message_lower):
                suggestions.extend(rule.suggestions)
                error.error_pattern = rule.error_type  # エラーパターンを設定
                break  # 最初にマッチしたルールのみ適用

        return suggestions

    def _generate_context_suggestions(self, error: GracefulSyntaxError) -> List[str]:
        """コンテキストに基づく修正提案を生成"""
        suggestions: List[str] = []

        if not error.context:
            return suggestions

        context = error.context

        # ブロック記法の不完全パターンを検出
        if context.startswith("#") and not context.endswith("#"):
            # 開始マーカーはあるが終了マーカーがない場合
            if " " in context:
                keyword = context[1:].strip()
                suggestions.append(
                    f"「{context}」を「# {keyword} #」に修正してください"
                )
            else:
                suggestions.append(f"「{context}」の後に「 #」を追加してください")

        # 半角・全角混在の検出
        if self._has_mixed_width_chars(context):
            suggestions.append("半角文字と全角文字の混在を統一してください")

        # よくある間違いパターン
        common_mistakes = self._detect_common_mistakes(context)
        suggestions.extend(common_mistakes)

        return suggestions

    def _has_mixed_width_chars(self, text: str) -> bool:
        """半角・全角文字の混在を検出"""
        has_halfwidth = any(ord(char) < 256 for char in text if char != " ")
        has_fullwidth = any(ord(char) >= 256 for char in text)
        return has_halfwidth and has_fullwidth

    def _detect_common_mistakes(self, context: str) -> List[str]:
        """よくある間違いパターンを検出"""
        suggestions: List[str] = []

        # 全角スペースの使用
        if "\u3000" in context:  # 全角スペース
            suggestions.append("全角スペースを半角スペースに変更してください")

        # マーカーの不統一
        if "#" in context and "＃" in context:  # 半角＃と全角＃の混在
            suggestions.append("マーカーは半角「#」で統一してください")

        # 終了マーカーの間違い
        if context.endswith("###") or context.endswith("####"):
            suggestions.append("終了マーカーは「##」を使用してください")

        return suggestions

    def enhance_error_with_suggestions(
        self, error: GracefulSyntaxError
    ) -> GracefulSyntaxError:
        """エラーに修正提案を追加して拡張"""
        suggestions = self.generate_suggestions(error)

        # 修正提案を設定
        error.correction_suggestions = suggestions

        # エラーパターンを分類
        error.classify_error_pattern()

        # ハイライト範囲を推定（基本的な実装）
        self._estimate_highlight_range(error)

        return error

    def _estimate_highlight_range(self, error: GracefulSyntaxError) -> None:
        """エラーのハイライト範囲を推定"""
        if not error.context:
            return

        context = error.context

        # マーカー関連エラーの場合
        if error.error_pattern in ["incomplete_marker", "marker_mismatch"]:
            # '#' 文字の位置を特定
            start = context.find("#")
            if start >= 0:
                # マーカー部分全体をハイライト
                end = len(context.rstrip())
                error.set_highlight_range(start, end)

        # カラー関連エラーの場合
        elif error.error_pattern == "invalid_color":
            # color= パターンを検索
            color_match = re.search(r"color\s*=\s*[^\s]+", context)
            if color_match:
                error.set_highlight_range(color_match.start(), color_match.end())

        # デフォルト: 全体をハイライト
        else:
            error.set_highlight_range(0, len(context.strip()))

    def get_error_statistics(self, errors: List[GracefulSyntaxError]) -> Dict[str, Any]:
        """エラー統計情報を取得"""
        if not errors:
            return {"total": 0, "patterns": {}, "severity_breakdown": {}}

        # エラーパターンの統計
        pattern_counts: dict[str, int] = {}
        severity_counts = {"error": 0, "warning": 0, "info": 0}

        for error in errors:
            # パターン統計
            pattern = error.error_pattern or "unknown"
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

            # 重要度統計
            severity = getattr(error, "severity", "error")
            if severity in severity_counts:
                severity_counts[severity] += 1

        return {
            "total": len(errors),
            "patterns": pattern_counts,
            "severity_breakdown": severity_counts,
            "avg_suggestions_per_error": (
                sum(
                    (
                        len(error.correction_suggestions)
                        if error.correction_suggestions
                        else 0
                    )
                    for error in errors
                )
                / len(errors)
                if errors
                else 0
            ),
        }
