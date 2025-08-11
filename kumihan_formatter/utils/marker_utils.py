"""マーカーキーワードのパース処理に関する共通ユーティリティ"""

import re
from typing import Any, Dict, List


def parse_marker_keywords(marker_line: str) -> tuple[list[str], dict[str, str]]:
    """
    マーカー行からキーワードと属性を抽出する共通関数（新記法対応）

    Args:
        marker_line: #で囲まれたマーカー行（例: "# 見出し1+太字 color=#ff0000 #"）

    Returns:
        tuple: (キーワードリスト, 属性辞書)
    """
    # # または ＃を除去してキーワード部分を取得
    keyword_part = marker_line.strip()

    # 新記法パターンマッチング
    pattern = r"^[#＃]\s*(.+?)\s*[#＃]"
    match = re.match(pattern, keyword_part)

    if match:
        keyword_part = match.group(1).strip()
    else:
        # パターンに一致しない場合はそのまま処理
        keyword_part = keyword_part.strip()

    # 属性の抽出（例: color=#ff0000）
    attributes: Dict[str, Any] = {}

    # color属性の検出と分離
    color_match = re.search(r"\s+color=([#\w]+)", keyword_part)
    if color_match:
        attributes["color"] = color_match.group(1)
        keyword_part = re.sub(r"\s+color=[#\w]+", "", keyword_part)

    # alt属性の検出と分離（画像用）- alt属性は削除されました（Phase 1）
    # alt_match = re.search(r"\s+alt=([^;]+)", keyword_part)
    # if alt_match:
    #     attributes["alt"] = alt_match.group(1).strip()
    #     keyword_part = re.sub(r"\s+alt=[^;]+", "", keyword_part)

    # キーワードの分割（+または＋で区切る）
    if "+" in keyword_part or "＋" in keyword_part:
        # 複合キーワード
        keywords: List[str] = []
        parts = re.split(r"[+＋]", keyword_part)
        for part in parts:
            part = part.strip()
            if part:
                keywords.append(part)
    else:
        # 単一キーワード
        keywords = [keyword_part.strip()] if keyword_part.strip() else []

    return keywords, attributes


def normalize_keywords(keywords: list[str]) -> list[str]:
    """
    キーワードの正規化（表記揺れの統一）

    Args:
        keywords: 正規化前のキーワードリスト

    Returns:
        正規化後のキーワードリスト
    """
    normalized = []

    # キーワードの正規化マッピング
    normalization_map = {
        # 見出しレベルの正規化
        "見出し": "見出し1",
        "h1": "見出し1",
        "h2": "見出し2",
        "h3": "見出し3",
        "h4": "見出し4",
        "h5": "見出し5",
        # スタイルの正規化
        "ボールド": "太字",
        "bold": "太字",
        "strong": "太字",
        "italic": "イタリック",
        "em": "イタリック",
        # レイアウトの正規化
        "ボックス": "枠線",
        "box": "枠線",
        "highlight": "ハイライト",
        # 画像の正規化
        "img": "画像",
        "image": "画像",
    }

    for keyword in keywords:
        # 正規化マッピングを適用
        normalized_keyword = normalization_map.get(keyword, keyword)

        # 重複を排除
        if normalized_keyword not in normalized:
            normalized.append(normalized_keyword)

    return normalized


def validate_keyword_combinations(keywords: list[str]) -> tuple[bool, list[str]]:
    """
    キーワードの組み合わせの妥当性をチェック

    Args:
        keywords: 検証するキーワードリスト

    Returns:
        tuple: (有効かどうか, エラーメッセージリスト)
    """
    errors: List[str] = []

    # 定義されたキーワードセット
    valid_keywords = {
        "見出し1",
        "見出し2",
        "見出し3",
        "見出し4",
        "見出し5",
        "太字",
        "イタリック",
        "枠線",
        "ハイライト",
        "画像",
    }

    # 未知のキーワードをチェック
    unknown_keywords = [kw for kw in keywords if kw not in valid_keywords]
    if unknown_keywords:
        errors.append(f"未知のキーワード: {', '.join(unknown_keywords)}")

    # 重複する見出しレベルをチェック
    heading_keywords = [kw for kw in keywords if kw.startswith("見出し")]
    if len(heading_keywords) > 1:
        errors.append(f"複数の見出しレベル指定: {', '.join(heading_keywords)}")

    return len(errors) == 0, errors


def get_keyword_suggestions(invalid_keyword: str) -> list[str]:
    """
    無効なキーワードに対する修正候補を提案

    Args:
        invalid_keyword: 無効なキーワード

    Returns:
        修正候補のリスト
    """
    # 全有効キーワード
    valid_keywords = [
        "見出し1",
        "見出し2",
        "見出し3",
        "見出し4",
        "見出し5",
        "太字",
        "イタリック",
        "枠線",
        "ハイライト",
        "画像",
    ]

    suggestions = []
    invalid_lower = invalid_keyword.lower()

    # 部分一致による候補検出
    for valid_keyword in valid_keywords:
        valid_lower = valid_keyword.lower()

        # 前方一致
        if valid_lower.startswith(invalid_lower[:3]) and len(invalid_lower) >= 2:
            suggestions.append(valid_keyword)
        # 含有チェック
        elif invalid_lower in valid_lower or valid_lower in invalid_lower:
            suggestions.append(valid_keyword)

    # レーベンシュタイン距離による類似度チェック（簡易版）
    def simple_similarity(s1: str, s2: str) -> float:
        """簡易類似度計算"""
        if not s1 or not s2:
            return 0.0
        # 簡易的な類似度計算（共通文字数 / 最大長）
        common_chars = sum(1 for c in s1 if c in s2)
        return common_chars / max(len(s1), len(s2))

    # 類似度による追加候補検出
    for valid_keyword in valid_keywords:
        if valid_keyword not in suggestions:
            similarity = simple_similarity(invalid_lower, valid_keyword.lower())
            if similarity > 0.3:  # 30%以上の類似度
                suggestions.append(valid_keyword)

    return suggestions[:3]  # 最大3つまで
