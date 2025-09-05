"""サンプルコンテンツ（外部examples/への移設ラッパー）"""

from __future__ import annotations

from pathlib import Path
import json
import warnings
from typing import Dict, Any


def _project_root() -> Path:
    # package/kumihan_formatter/sample_content.py → repo root
    return Path(__file__).resolve().parents[1].parent


def get_showcase_sample() -> str:
    """examples/sample_content.kumi からサンプルを読み込む。

    なければ短いフォールバックサンプルを返す。
    """
    examples_path = _project_root() / "examples" / "sample_content.kumi"
    try:
        if examples_path.exists():
            return examples_path.read_text(encoding="utf-8")
    except Exception:
        pass
    return "#見出し1#\nKumihan-Formatter サンプル\n##\n\n段落テキスト\n"


def get_sample_images() -> Dict[str, str]:
    """examples/sample_images.json を辞書で返す（Base64）。

    なければ小さなプレースホルダーを返す。
    """
    json_path = _project_root() / "examples" / "sample_images.json"
    try:
        if json_path.exists():
            data: Dict[str, Any] = json.loads(json_path.read_text(encoding="utf-8"))
            # 型の安全化（値は文字列のみを許容）
            return {k: str(v) for k, v in data.items()}
    except Exception:
        pass
    return {
        "placeholder.png": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mNkYPhfAAIMAAUlA0V8vU0iAAAAAElFTkSuQmCC"
    }


# 後方互換: 旧定数名を維持（import利用を壊さない）
warnings.warn(
    "kumihan_formatter.sample_content は examples/ へ移設予定です。"
    "今後は examples データを参照してください。",
    DeprecationWarning,
    stacklevel=2,
)

SHOWCASE_SAMPLE: str = get_showcase_sample()
SAMPLE_IMAGES: Dict[str, str] = get_sample_images()

__all__ = [
    "SHOWCASE_SAMPLE",
    "SAMPLE_IMAGES",
    "get_showcase_sample",
    "get_sample_images",
]
