"""Benchmark Scenario Data Generators

ベンチマークシナリオのテストデータ生成機能
"""

import random
import string
from pathlib import Path
from typing import Any, Dict, List, Optional


class ScenarioDataGenerators:
    """Scenario data generation utilities"""

    @staticmethod
    def generate_file_content(size: int = 1000, **kwargs: Any) -> str:
        """ファイル内容を生成

        Args:
            size: 行数
            **kwargs: 追加パラメータ

        Returns:
            生成されたファイル内容
        """
        lines = []
        for i in range(size):
            # 様々な長さの行を生成
            line_length = random.randint(10, 100)
            line = "".join(
                random.choices(
                    string.ascii_letters + string.digits + " ", k=line_length
                )
            )
            lines.append(f"Line {i + 1}: {line}")
        return "\n".join(lines)

    @staticmethod
    def generate_markup_content(
        size: int = 1000, markup_density: float = 0.3, **kwargs: Any
    ) -> str:
        """マークアップ内容を生成

        Args:
            size: 行数
            markup_density: マークアップ記法の密度（0.0-1.0）
            **kwargs: 追加パラメータ

        Returns:
            生成されたマークアップ内容
        """
        markup_patterns = [
            ";;;bold;;; {text} ;;;",
            ";;;italic;;; {text} ;;;",
            ";;;underline;;; {text} ;;;",
            ";;;color:red;;; {text} ;;;",
            "|||{text}《{reading}》",
            "(({text}))",
        ]

        lines = []
        for i in range(size):
            # 基本テキスト生成
            base_text = "".join(
                random.choices(
                    string.ascii_letters + string.digits + " ", k=random.randint(20, 80)
                )
            )

            # マークアップ記法を追加
            if random.random() < markup_density:
                pattern = random.choice(markup_patterns)
                if "|||" in pattern:  # ルビ記法
                    word = random.choice(base_text.split())
                    reading = "".join(
                        random.choices(string.ascii_lowercase, k=random.randint(3, 8))
                    )
                    markup_text = pattern.format(text=word, reading=reading)
                else:
                    word = random.choice(base_text.split())
                    markup_text = pattern.format(text=word)
                base_text = base_text.replace(word, markup_text, 1)

            lines.append(f"Line {i + 1}: {base_text}")
        return "\n".join(lines)

    @staticmethod
    def generate_memory_test_data(size_mb: int = 10, **kwargs: Any) -> bytes:
        """メモリテスト用データを生成

        Args:
            size_mb: データサイズ（MB）
            **kwargs: 追加パラメータ

        Returns:
            生成されたバイナリデータ
        """
        size_bytes = size_mb * 1024 * 1024
        return bytes(random.getrandbits(8) for _ in range(size_bytes))

    @staticmethod
    def generate_nested_structure(
        depth: int = 5, breadth: int = 3, **kwargs: Any
    ) -> Dict[str, Any]:
        """ネストした構造体を生成

        Args:
            depth: ネストの深さ
            breadth: 各レベルの幅
            **kwargs: 追加パラメータ

        Returns:
            生成されたネスト構造
        """

        def _generate_level(current_depth: int) -> Dict[str, Any]:
            if current_depth <= 0:
                return {f"value_{i}": random.randint(1, 1000) for i in range(breadth)}

            result: Dict[str, Any] = {}
            for i in range(breadth):
                key = f"level_{current_depth}_item_{i}"
                if random.random() < 0.7:  # 70% chance of nesting
                    result[key] = _generate_level(current_depth - 1)
                else:
                    result[key] = f"leaf_value_{random.randint(1, 1000)}"
            return result

        return _generate_level(depth)

    @staticmethod
    def generate_cache_test_keys(count: int = 1000, **kwargs: Any) -> List[str]:
        """キャッシュテスト用キーを生成

        Args:
            count: キー数
            **kwargs: 追加パラメータ

        Returns:
            生成されたキーのリスト
        """
        keys = []
        for i in range(count):
            # 様々なパターンのキーを生成
            if i % 3 == 0:
                # ファイルパス風
                key = f"file_{i // 10}/{random.choice(['doc', 'img', 'data'])}_{i}.txt"
            elif i % 3 == 1:
                # ID風
                key = f"id_{i:06d}_{random.choice(['user', 'product', 'order'])}"
            else:
                # ランダム文字列
                key = "".join(
                    random.choices(
                        string.ascii_letters + string.digits, k=random.randint(8, 16)
                    )
                )
            keys.append(key)
        return keys

    @staticmethod
    def generate_test_files(
        count: int = 10, base_dir: Optional[Path] = None, **kwargs: Any
    ) -> List[Path]:
        """テスト用ファイルを生成

        Args:
            count: ファイル数
            base_dir: ベースディレクトリ
            **kwargs: 追加パラメータ

        Returns:
            生成されたファイルパスのリスト
        """
        if base_dir is None:
            base_dir = Path("/tmp/benchmark_test_files")

        base_dir.mkdir(parents=True, exist_ok=True)
        generated_files = []

        for i in range(count):
            filename = f"test_file_{i:03d}.txt"
            filepath = base_dir / filename

            # ファイル内容を生成
            content = ScenarioDataGenerators.generate_file_content(
                size=random.randint(100, 1000)
            )

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            generated_files.append(filepath)

        return generated_files
