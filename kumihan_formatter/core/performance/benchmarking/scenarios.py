"""ベンチマークシナリオ定義

Single Responsibility Principle適用: ベンチマークシナリオの責任分離
Issue #476 Phase2対応 - パフォーマンスモジュール統合
"""

import random
import string
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ...utilities.logger import get_logger


class BenchmarkScenarios:
    """ベンチマークシナリオ管理クラス

    機能:
    - 標準ベンチマークシナリオの提供
    - テストデータの生成
    - シナリオ別パラメータ管理
    """

    def __init__(self) -> None:
        """ベンチマークシナリオを初期化"""
        self.logger = get_logger(__name__)
        self.scenarios: Dict[str, Dict[str, Any]] = {}
        self._register_default_scenarios()

    def _register_default_scenarios(self) -> None:
        """デフォルトシナリオを登録"""
        # ファイル読み込みシナリオ
        self.register_scenario(
            "file_read_small",
            {
                "description": "Small file reading benchmark",
                "data_generator": self.generate_file_content,
                "data_size": 1000,  # 行数
                "params": {"encoding": "utf-8"},
            },
        )

        self.register_scenario(
            "file_read_medium",
            {
                "description": "Medium file reading benchmark",
                "data_generator": self.generate_file_content,
                "data_size": 10000,
                "params": {"encoding": "utf-8"},
            },
        )

        self.register_scenario(
            "file_read_large",
            {
                "description": "Large file reading benchmark",
                "data_generator": self.generate_file_content,
                "data_size": 100000,
                "params": {"encoding": "utf-8"},
            },
        )

        # パースシナリオ
        self.register_scenario(
            "parse_simple",
            {
                "description": "Simple text parsing benchmark",
                "data_generator": self.generate_parse_content,
                "data_size": 100,
                "params": {"notation_density": 0.1},  # 10%の行に記法
            },
        )

        self.register_scenario(
            "parse_complex",
            {
                "description": "Complex text parsing benchmark",
                "data_generator": self.generate_parse_content,
                "data_size": 1000,
                "params": {"notation_density": 0.5},  # 50%の行に記法
            },
        )

        # レンダリングシナリオ
        self.register_scenario(
            "render_minimal",
            {
                "description": "Minimal HTML rendering benchmark",
                "data_generator": self.generate_render_data,
                "data_size": 50,
                "params": {"template_complexity": "simple"},
            },
        )

        self.register_scenario(
            "render_standard",
            {
                "description": "Standard HTML rendering benchmark",
                "data_generator": self.generate_render_data,
                "data_size": 500,
                "params": {"template_complexity": "standard"},
            },
        )

        self.register_scenario(
            "render_complex",
            {
                "description": "Complex HTML rendering benchmark",
                "data_generator": self.generate_render_data,
                "data_size": 2000,
                "params": {"template_complexity": "complex"},
            },
        )

    def register_scenario(self, name: str, config: Dict[str, Any]) -> None:
        """シナリオを登録

        Args:
            name: シナリオ名
            config: シナリオ設定
        """
        self.scenarios[name] = config
        self.logger.debug(f"Registered scenario: {name}")

    def get_scenario(self, name: str) -> Optional[Dict[str, Any]]:
        """シナリオを取得

        Args:
            name: シナリオ名

        Returns:
            シナリオ設定（見つからない場合はNone）
        """
        return self.scenarios.get(name)

    def list_scenarios(self) -> List[str]:
        """利用可能なシナリオ一覧を取得

        Returns:
            シナリオ名のリスト
        """
        return list(self.scenarios.keys())

    def generate_file_content(self, lines: int = 1000) -> str:
        """ファイル読み込みテスト用コンテンツを生成

        Args:
            lines: 生成する行数

        Returns:
            生成されたコンテンツ
        """
        content_lines = []
        for i in range(lines):
            # ランダムな長さの行を生成
            line_length = random.randint(50, 150)
            line = "".join(
                random.choices(
                    string.ascii_letters + string.digits + " ", k=line_length
                )
            )
            content_lines.append(f"Line {i+1}: {line}")

        return "\n".join(content_lines)

    def generate_parse_content(
        self, lines: int = 100, notation_density: float = 0.3
    ) -> str:
        """パーステスト用コンテンツを生成

        Args:
            lines: 生成する行数
            notation_density: 記法を含む行の割合

        Returns:
            生成されたコンテンツ
        """
        notations = [
            ";;;見出し1;;;",
            ";;;見出し2;;;",
            ";;;太字;;;",
            ";;;斜体;;;",
            ";;;下線;;;",
            ";;;枠線;;;",
            ";;;ハイライト color=#ffe6e6;;;",
            ";;;ネタバレ;;;",
        ]

        content_lines = []
        for i in range(lines):
            if random.random() < notation_density:
                # 記法を含む行
                notation = random.choice(notations)
                if ";;;" in notation:
                    # ブロック記法
                    content_lines.append(notation.replace(";;;", f";;;{i}_"))
                    content_lines.append(f"Content for block {i}")
                    content_lines.append(";;;")
                else:
                    content_lines.append(notation)
            else:
                # 通常のテキスト行
                content_lines.append(
                    f"Normal text line {i}: " + self._generate_lorem_ipsum()
                )

        return "\n".join(content_lines)

    def generate_render_data(
        self, elements: int = 100, template_complexity: str = "standard"
    ) -> Dict[str, Any]:
        """レンダリングテスト用データを生成

        Args:
            elements: 生成する要素数
            template_complexity: テンプレートの複雑さ

        Returns:
            レンダリング用データ
        """
        # ASTノード風のデータ構造を生成
        nodes = []

        for i in range(elements):
            node_type = random.choice(
                ["text", "heading", "paragraph", "list", "blockquote"]
            )

            if node_type == "text":
                nodes.append(
                    {
                        "type": "text",
                        "content": f"Text content {i}: {self._generate_lorem_ipsum()}",
                    }
                )
            elif node_type == "heading":
                nodes.append(
                    {
                        "type": "heading",
                        "level": str(random.randint(1, 6)),
                        "content": f"Heading {i}",
                    }
                )
            elif node_type == "paragraph":
                nodes.append(
                    {
                        "type": "paragraph",
                        "content": self._generate_lorem_ipsum(sentences=3),
                    }
                )
            elif node_type == "list":
                items = [f"Item {j}" for j in range(random.randint(3, 7))]
                nodes.append(
                    {
                        "type": "list",
                        "ordered": str(random.choice([True, False])),
                        "items": ", ".join(items),
                    }
                )
            elif node_type == "blockquote":
                nodes.append(
                    {
                        "type": "blockquote",
                        "content": self._generate_lorem_ipsum(sentences=2),
                    }
                )

        # テンプレート設定
        template_config = {
            "simple": {"css_files": "1", "js_files": "0", "custom_styles": "False"},
            "standard": {"css_files": "2", "js_files": "1", "custom_styles": "True"},
            "complex": {
                "css_files": "3",
                "js_files": "2",
                "custom_styles": "True",
                "plugins": "True",
            },
        }

        return {
            "nodes": nodes,
            "template": template_config.get(
                template_complexity, template_config["standard"]
            ),
            "metadata": {
                "title": f"Benchmark Document ({elements} elements)",
                "author": "Benchmark Generator",
                "date": "2024-01-01",
            },
        }

    def _generate_lorem_ipsum(self, sentences: int = 1) -> str:
        """Lorem Ipsum風のテキストを生成

        Args:
            sentences: 生成する文の数

        Returns:
            生成されたテキスト
        """
        words = [
            "lorem",
            "ipsum",
            "dolor",
            "sit",
            "amet",
            "consectetur",
            "adipiscing",
            "elit",
            "sed",
            "do",
            "eiusmod",
            "tempor",
            "incididunt",
            "ut",
            "labore",
            "et",
            "dolore",
            "magna",
            "aliqua",
        ]

        sentences_list = []
        for _ in range(sentences):
            sentence_length = random.randint(8, 15)
            sentence_words = random.choices(words, k=sentence_length)
            sentence = " ".join(sentence_words).capitalize() + "."
            sentences_list.append(sentence)

        return " ".join(sentences_list)

    def create_benchmark_suite(
        self, scenario_names: Optional[List[str]] = None
    ) -> Dict[str, Tuple[Any, Dict[str, Any]]]:
        """ベンチマークスイートを作成

        Args:
            scenario_names: 使用するシナリオ名のリスト（Noneの場合は全シナリオ）

        Returns:
            シナリオ名とデータ・パラメータのマッピング
        """
        if scenario_names is None:
            scenario_names = list(self.scenarios.keys())

        suite = {}
        for name in scenario_names:
            scenario = self.get_scenario(name)
            if scenario:
                # データ生成
                data_generator = scenario["data_generator"]
                data_size = scenario["data_size"]
                params = scenario.get("params", {})

                if "notation_density" in params:
                    data = data_generator(data_size, params["notation_density"])
                elif "template_complexity" in params:
                    data = data_generator(data_size, params["template_complexity"])
                else:
                    data = data_generator(data_size)

                suite[name] = (data, params)
            else:
                self.logger.warning(f"Scenario '{name}' not found")

        return suite


# グローバルインスタンス
_global_scenarios: Optional[BenchmarkScenarios] = None


def get_benchmark_scenarios() -> BenchmarkScenarios:
    """グローバルなベンチマークシナリオインスタンスを取得

    Returns:
        ベンチマークシナリオインスタンス
    """
    global _global_scenarios
    if _global_scenarios is None:
        _global_scenarios = BenchmarkScenarios()
    return _global_scenarios
