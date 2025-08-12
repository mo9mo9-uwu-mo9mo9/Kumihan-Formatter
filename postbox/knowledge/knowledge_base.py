#!/usr/bin/env python3
"""
Knowledge Base for Gemini Capability Enhancement
設計パターンテンプレート集・Kumihan-Formatter固有コンテキスト知識システム
"""

import json
import os
import yaml
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime

class KnowledgeCategory(Enum):
    """知識カテゴリ"""
    DESIGN_PATTERNS = "design_patterns"           # 設計パターン
    PROJECT_SPECIFIC = "project_specific"        # プロジェクト固有
    IMPLEMENTATION_GUIDES = "implementation_guides"  # 実装ガイド
    ERROR_SOLUTIONS = "error_solutions"          # エラー解決策  
    QUALITY_STANDARDS = "quality_standards"      # 品質基準
    BEST_PRACTICES = "best_practices"           # ベストプラクティス
    CODE_TEMPLATES = "code_templates"           # コードテンプレート
    ARCHITECTURE_PATTERNS = "architecture_patterns"  # アーキテクチャパターン

class KnowledgeType(Enum):
    """知識タイプ"""
    TEMPLATE = "template"                        # テンプレート
    GUIDE = "guide"                             # ガイド
    REFERENCE = "reference"                     # リファレンス
    EXAMPLE = "example"                         # 例
    RULE = "rule"                               # ルール
    PATTERN = "pattern"                         # パターン
    CHECKLIST = "checklist"                     # チェックリスト

@dataclass
class KnowledgeEntry:
    """知識エントリ"""
    entry_id: str
    title: str
    category: KnowledgeCategory
    knowledge_type: KnowledgeType
    content: Dict[str, Any]
    description: str
    tags: List[str]
    difficulty_level: str  # basic, intermediate, advanced
    usage_frequency: int = 0
    created_at: str = ""
    updated_at: str = ""
    version: str = "1.0"
    prerequisites: List[str] = field(default_factory=list)
    related_entries: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class KumihanFormatterContext:
    """Kumihan-Formatter固有コンテキスト"""
    
    def __init__(self):
        self.project_info = {
            "name": "Kumihan-Formatter",
            "description": "Kumihan独自ブロック記法のフォーマッター",
            "language": "Python 3.12+",
            "framework": "CLI-based",
            "notation": "Kumihan Block Notation",
            "encoding": "UTF-8",
            "main_components": [
                "core/block_parser.py",
                "core/rendering/",  
                "cli.py",
                "commands/",
                "config/"
            ]
        }
        
        self.notation_rules = {
            "block_notation": "# 装飾名 #内容##",
            "supported_decorations": [
                "太字", "イタリック", "見出し", "リスト", "目次", "リンク"
            ],
            "structure_elements": [
                "見出し構造", "リスト構造", "目次構造", "リンク構造"
            ]
        }
        
        self.architecture_patterns = {
            "parser_architecture": {
                "pattern": "Pipeline Pattern",
                "components": ["Lexer", "Parser", "AST Builder", "Renderer"],
                "flow": "Input -> Tokenize -> Parse -> Build AST -> Render -> Output"
            },
            "cli_architecture": {
                "pattern": "Command Pattern",
                "components": ["CLI Parser", "Command Classes", "Handlers"],
                "flow": "CLI Input -> Command Selection -> Handler Execution"
            },
            "config_architecture": {
                "pattern": "Configuration Pattern",
                "components": ["Config Loader", "Validator", "Manager"],
                "flow": "Config File -> Load -> Validate -> Apply"
            }
        }
        
        self.quality_standards = {
            "code_quality": {
                "mypy_strict": True,
                "black_formatting": True,
                "isort_imports": True,
                "docstring_required": True,
                "type_annotations_required": True,
                "test_coverage_min": 80
            },
            "file_organization": {
                "temp_files_location": "tmp/",
                "module_structure": "core/ -> components -> utilities",
                "test_structure": "tests/ -> mirror src structure",
                "config_location": "config/"
            },
            "naming_conventions": {
                "classes": "PascalCase",
                "functions": "snake_case",
                "variables": "snake_case",
                "constants": "UPPER_SNAKE_CASE",
                "private": "_prefix"
            }
        }
        
        self.common_patterns = {
            "parser_patterns": [
                "Visitor Pattern for AST traversal",
                "Builder Pattern for complex objects",
                "Strategy Pattern for different renderers"
            ],
            "error_handling": [
                "Custom exception classes",
                "Detailed error messages",
                "Recovery strategies"
            ],
            "logging": [
                "Structured logging with logger module",
                "Different log levels",
                "Context information inclusion"
            ]
        }

class DesignPatternLibrary:
    """設計パターンライブラリ"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, Dict[str, Any]]:
        """設計パターンの初期化"""
        
        return {
            "factory": {
                "name": "Factory Pattern",
                "intent": "オブジェクト作成のインターフェースを提供",
                "applicability": [
                    "オブジェクト作成の詳細を隠蔽したい場合",
                    "作成するオブジェクトのタイプを実行時に決定したい場合",
                    "オブジェクトの作成プロセスが複雑な場合"
                ],
                "structure": {
                    "creator": "抽象的な作成者クラス",
                    "concrete_creator": "具体的な作成者クラス",
                    "product": "作成される製品の抽象クラス",
                    "concrete_product": "具体的な製品クラス"
                },
                "template": """
from abc import ABC, abstractmethod
from typing import Any

class Product(ABC):
    \"\"\"製品の抽象クラス\"\"\"
    
    @abstractmethod
    def operation(self) -> str:
        pass

class ConcreteProductA(Product):
    \"\"\"具体的な製品A\"\"\"
    
    def operation(self) -> str:
        return "Result of ConcreteProductA"

class ConcreteProductB(Product):
    \"\"\"具体的な製品B\"\"\"
    
    def operation(self) -> str:
        return "Result of ConcreteProductB"

class Creator(ABC):
    \"\"\"作成者の抽象クラス\"\"\"
    
    @abstractmethod
    def factory_method(self) -> Product:
        pass
    
    def some_operation(self) -> str:
        product = self.factory_method()
        return f"Creator: {product.operation()}"

class ConcreteCreatorA(Creator):
    \"\"\"具体的な作成者A\"\"\"
    
    def factory_method(self) -> Product:
        return ConcreteProductA()

class ConcreteCreatorB(Creator):
    \"\"\"具体的な作成者B\"\"\"
    
    def factory_method(self) -> Product:
        return ConcreteProductB()
""",
                "usage_example": """
# 使用例
creator_a = ConcreteCreatorA()
result_a = creator_a.some_operation()

creator_b = ConcreteCreatorB()
result_b = creator_b.some_operation()
""",
                "benefits": [
                    "オブジェクト作成のカプセル化",
                    "コードの柔軟性向上",
                    "単一責任原則の遵守"
                ],
                "drawbacks": [
                    "クラス数の増加",
                    "複雑性の増加"
                ]
            },
            
            "strategy": {
                "name": "Strategy Pattern",
                "intent": "アルゴリズムファミリーを定義し、実行時に選択可能にする",
                "applicability": [
                    "同じ問題に対して複数のアルゴリズムが存在する場合",
                    "実行時にアルゴリズムを選択したい場合",
                    "条件分岐を戦略クラスで置き換えたい場合"
                ],
                "structure": {
                    "strategy": "戦略の抽象インターフェース",
                    "concrete_strategy": "具体的な戦略実装",
                    "context": "戦略を使用するコンテキスト"
                },
                "template": """
from abc import ABC, abstractmethod
from typing import Any, List

class Strategy(ABC):
    \"\"\"戦略の抽象インターフェース\"\"\"
    
    @abstractmethod
    def algorithm_interface(self, data: Any) -> Any:
        pass

class ConcreteStrategyA(Strategy):
    \"\"\"具体的な戦略A\"\"\"
    
    def algorithm_interface(self, data: List[int]) -> List[int]:
        return sorted(data)

class ConcreteStrategyB(Strategy):
    \"\"\"具体的な戦略B\"\"\"
    
    def algorithm_interface(self, data: List[int]) -> List[int]:
        return sorted(data, reverse=True)

class Context:
    \"\"\"戦略を使用するコンテキスト\"\"\"
    
    def __init__(self, strategy: Strategy) -> None:
        self._strategy = strategy
    
    @property
    def strategy(self) -> Strategy:
        return self._strategy
    
    @strategy.setter
    def strategy(self, strategy: Strategy) -> None:
        self._strategy = strategy
    
    def context_interface(self, data: Any) -> Any:
        return self._strategy.algorithm_interface(data)
""",
                "usage_example": """
# 使用例
data = [1, 5, 3, 9, 2]

context = Context(ConcreteStrategyA())
result1 = context.context_interface(data)  # 昇順ソート

context.strategy = ConcreteStrategyB()
result2 = context.context_interface(data)  # 降順ソート
""",
                "benefits": [
                    "アルゴリズムの交換可能性",
                    "オープン・クローズド原則の遵守",
                    "実行時の柔軟性"
                ],
                "drawbacks": [
                    "クラス数の増加",
                    "クライアントの複雑化"
                ]
            },
            
            "observer": {
                "name": "Observer Pattern",
                "intent": "オブジェクト間の一対多の依存関係を定義",
                "applicability": [
                    "オブジェクトの状態変更を他のオブジェクトに通知したい場合",
                    "疎結合なシステムを構築したい場合",
                    "イベント駆動アーキテクチャを実装したい場合"
                ],
                "structure": {
                    "subject": "観察対象の抽象インターフェース",
                    "concrete_subject": "具体的な観察対象",
                    "observer": "観察者の抽象インターフェース",
                    "concrete_observer": "具体的な観察者"
                },
                "template": """
from abc import ABC, abstractmethod
from typing import List, Any

class Observer(ABC):
    \"\"\"観察者の抽象インターフェース\"\"\"
    
    @abstractmethod
    def update(self, subject: 'Subject') -> None:
        pass

class Subject(ABC):
    \"\"\"観察対象の抽象インターフェース\"\"\"
    
    @abstractmethod
    def attach(self, observer: Observer) -> None:
        pass
    
    @abstractmethod
    def detach(self, observer: Observer) -> None:
        pass
    
    @abstractmethod
    def notify(self) -> None:
        pass

class ConcreteSubject(Subject):
    \"\"\"具体的な観察対象\"\"\"
    
    _state: int = None
    _observers: List[Observer] = []
    
    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)
    
    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)
    
    def notify(self) -> None:
        for observer in self._observers:
            observer.update(self)
    
    @property
    def state(self) -> int:
        return self._state
    
    @state.setter
    def state(self, state: int) -> None:
        self._state = state
        self.notify()

class ConcreteObserverA(Observer):
    \"\"\"具体的な観察者A\"\"\"
    
    def update(self, subject: Subject) -> None:
        if isinstance(subject, ConcreteSubject) and subject.state < 3:
            print("ConcreteObserverA: Reacted to the event")

class ConcreteObserverB(Observer):
    \"\"\"具体的な観察者B\"\"\"
    
    def update(self, subject: Subject) -> None:
        if isinstance(subject, ConcreteSubject) and subject.state >= 2:
            print("ConcreteObserverB: Reacted to the event")
""",
                "usage_example": """
# 使用例
subject = ConcreteSubject()

observer_a = ConcreteObserverA()
observer_b = ConcreteObserverB()

subject.attach(observer_a)
subject.attach(observer_b)

subject.state = 1  # observer_a が反応
subject.state = 3  # observer_b が反応
""",
                "benefits": [
                    "疎結合の実現",
                    "動的な関係性の管理",
                    "オープン・クローズド原則の遵守"
                ],
                "drawbacks": [
                    "メモリリークの可能性",
                    "通知順序の不確定性"
                ]
            },
            
            "plugin": {
                "name": "Plugin Pattern",
                "intent": "実行時に機能を動的に追加・削除可能にする",
                "applicability": [
                    "機能の動的な追加・削除が必要な場合",
                    "モジュール化されたアーキテクチャを構築したい場合",
                    "サードパーティ拡張をサポートしたい場合"
                ],
                "structure": {
                    "plugin_interface": "プラグインの抽象インターフェース",
                    "concrete_plugin": "具体的なプラグイン実装",
                    "plugin_manager": "プラグイン管理クラス",
                    "application": "プラグインを使用するアプリケーション"
                },
                "template": """
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import importlib
import os

class Plugin(ABC):
    \"\"\"プラグインの抽象インターフェース\"\"\"
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        pass
    
    @abstractmethod
    def execute(self, data: Any) -> Any:
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        pass

class PluginManager:
    \"\"\"プラグイン管理クラス\"\"\"
    
    def __init__(self) -> None:
        self._plugins: Dict[str, Plugin] = {}
    
    def register_plugin(self, plugin: Plugin) -> None:
        \"\"\"プラグインの登録\"\"\"
        plugin.initialize()
        self._plugins[plugin.name] = plugin
    
    def unregister_plugin(self, plugin_name: str) -> None:
        \"\"\"プラグインの登録解除\"\"\"
        if plugin_name in self._plugins:
            self._plugins[plugin_name].cleanup()
            del self._plugins[plugin_name]
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        \"\"\"プラグインの取得\"\"\"
        return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        \"\"\"登録済みプラグインの一覧\"\"\"
        return list(self._plugins.keys())
    
    def execute_plugin(self, plugin_name: str, data: Any) -> Any:
        \"\"\"プラグインの実行\"\"\"
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.execute(data)
        return None

# 具体的なプラグイン例
class TextProcessorPlugin(Plugin):
    \"\"\"テキスト処理プラグイン\"\"\"
    
    @property
    def name(self) -> str:
        return "text_processor"
    
    @property  
    def version(self) -> str:
        return "1.0.0"
    
    def initialize(self) -> None:
        print(f"{self.name} plugin initialized")
    
    def execute(self, data: str) -> str:
        return data.upper()
    
    def cleanup(self) -> None:
        print(f"{self.name} plugin cleanup")
""",
                "usage_example": """
# 使用例
manager = PluginManager()

# プラグイン登録
text_plugin = TextProcessorPlugin()
manager.register_plugin(text_plugin)

# プラグイン実行
result = manager.execute_plugin("text_processor", "hello world")
print(result)  # "HELLO WORLD"

# プラグイン一覧
plugins = manager.list_plugins()
print(plugins)  # ["text_processor"]
""",
                "benefits": [
                    "拡張性の向上",
                    "モジュール性の実現",
                    "実行時の機能変更"
                ],
                "drawbacks": [
                    "複雑性の増加",
                    "セキュリティリスク",
                    "依存関係管理の複雑化"
                ]
            }
        }

class ImplementationGuideLibrary:
    """実装ガイドライブラリ"""
    
    def __init__(self):
        self.guides = self._initialize_guides()
    
    def _initialize_guides(self) -> Dict[str, Dict[str, Any]]:
        """実装ガイドの初期化"""
        
        return {
            "new_class_implementation": {
                "title": "新規クラス実装ガイド",
                "description": "新しいクラスを実装する際の段階的ガイド",
                "steps": [
                    {
                        "step": 1,
                        "title": "要件分析",
                        "description": "クラスの責任と役割を明確にする",
                        "checklist": [
                            "クラスの主要な責任は何か？",
                            "他のクラスとの関係は？",
                            "インターフェースは必要か？",
                            "継承関係は適切か？"
                        ]
                    },
                    {
                        "step": 2,
                        "title": "設計決定",
                        "description": "適切な設計パターンと構造を選択",
                        "checklist": [
                            "適用可能な設計パターンはあるか？",
                            "属性とメソッドの可視性は適切か？",
                            "依存関係の注入方法は？",
                            "エラーハンドリング戦略は？"
                        ]
                    },
                    {
                        "step": 3,
                        "title": "基本構造実装",
                        "description": "クラスの基本構造を実装",
                        "template": """
from typing import Any, Optional
from abc import ABC, abstractmethod

class NewClass:
    \"\"\"
    新規クラスの説明
    
    Attributes:
        attribute1: 属性1の説明
        attribute2: 属性2の説明
    \"\"\"
    
    def __init__(self, param1: Any, param2: Optional[Any] = None) -> None:
        \"\"\"
        コンストラクタ
        
        Args:
            param1: パラメータ1の説明
            param2: パラメータ2の説明
        \"\"\"
        self.attribute1 = param1
        self.attribute2 = param2
    
    def method1(self, param: Any) -> Any:
        \"\"\"
        メソッド1の説明
        
        Args:
            param: パラメータの説明
            
        Returns:
            戻り値の説明
            
        Raises:
            Exception: エラーの説明
        \"\"\"
        pass
    
    def __str__(self) -> str:
        \"\"\"文字列表現\"\"\"
        return f"NewClass({self.attribute1}, {self.attribute2})"
    
    def __repr__(self) -> str:
        \"\"\"デバッグ用文字列表現\"\"\"
        return f"NewClass(attribute1={self.attribute1!r}, attribute2={self.attribute2!r})"
""",
                        "checklist": [
                            "型注釈が全てのメソッドに追加されているか？",
                            "docstringが適切に記述されているか？",
                            "__init__メソッドは適切に実装されているか？",
                            "__str__と__repr__メソッドが実装されているか？"
                        ]
                    },
                    {
                        "step": 4,
                        "title": "メソッド実装",
                        "description": "各メソッドの具体的な実装",
                        "checklist": [
                            "各メソッドの責任は単一か？",
                            "エラーハンドリングは適切か？",
                            "戻り値の型は正しいか？",
                            "副作用は最小限か？"
                        ]
                    },
                    {
                        "step": 5,
                        "title": "テスト実装",
                        "description": "ユニットテストの実装",
                        "template": """
import unittest
from unittest.mock import Mock, patch
from your_module import NewClass

class TestNewClass(unittest.TestCase):
    \"\"\"NewClassのテストケース\"\"\"
    
    def setUp(self) -> None:
        \"\"\"テストセットアップ\"\"\"
        self.instance = NewClass("test_param1", "test_param2")
    
    def test_init(self) -> None:
        \"\"\"初期化のテスト\"\"\"
        self.assertEqual(self.instance.attribute1, "test_param1")
        self.assertEqual(self.instance.attribute2, "test_param2")
    
    def test_method1(self) -> None:
        \"\"\"method1のテスト\"\"\"
        # テスト実装
        pass
    
    def test_str_representation(self) -> None:
        \"\"\"文字列表現のテスト\"\"\"
        result = str(self.instance)
        self.assertIn("NewClass", result)
    
    def test_repr_representation(self) -> None:
        \"\"\"repr表現のテスト\"\"\"
        result = repr(self.instance)
        self.assertIn("NewClass", result)
        self.assertIn("attribute1", result)

if __name__ == "__main__":
    unittest.main()
""",
                        "checklist": [
                            "正常ケースのテストは網羅されているか？",
                            "エラーケースのテストは実装されているか？",
                            "境界値のテストは含まれているか？",
                            "カバレッジは適切か？"
                        ]
                    },
                    {
                        "step": 6,
                        "title": "品質チェック",
                        "description": "コード品質の確認",
                        "checklist": [
                            "mypy --strict でエラーが出ないか？",
                            "black でフォーマットされているか？",
                            "isort でインポートが整理されているか？",
                            "flake8 でリントエラーがないか？",
                            "pytest でテストが全て通るか？"
                        ]
                    }
                ]
            },
            
            "error_handling_implementation": {
                "title": "エラーハンドリング実装ガイド",
                "description": "適切なエラーハンドリングの実装方法",
                "steps": [
                    {
                        "step": 1,
                        "title": "エラー分類",
                        "description": "エラーを適切に分類する",
                        "categories": [
                            "ユーザー入力エラー",
                            "システムエラー",
                            "プログラミングエラー",
                            "外部リソースエラー"
                        ]
                    },
                    {
                        "step": 2,
                        "title": "カスタム例外の設計",
                        "template": """
class KumihanFormatterError(Exception):
    \"\"\"Kumihan-Formatter基底例外\"\"\"
    
    def __init__(self, message: str, error_code: Optional[str] = None) -> None:
        super().__init__(message)
        self.error_code = error_code

class ParseError(KumihanFormatterError):
    \"\"\"パース処理エラー\"\"\"
    pass

class ValidationError(KumihanFormatterError):
    \"\"\"バリデーションエラー\"\"\"
    pass

class ConfigurationError(KumihanFormatterError):
    \"\"\"設定エラー\"\"\"
    pass
""",
                        "checklist": [
                            "基底例外クラスが定義されているか？",
                            "エラーコードシステムがあるか？",
                            "エラーメッセージは分かりやすいか？"
                        ]
                    }
                ]
            },
            
            "testing_implementation": {
                "title": "テスト実装ガイド",
                "description": "効果的なテストの実装方法",
                "testing_pyramid": {
                    "unit_tests": {
                        "percentage": 70,
                        "description": "個別のクラス・関数のテスト",
                        "tools": ["unittest", "pytest", "mock"]
                    },
                    "integration_tests": {
                        "percentage": 20,
                        "description": "モジュール間連携のテスト", 
                        "tools": ["pytest", "docker", "testcontainers"]
                    },
                    "e2e_tests": {
                        "percentage": 10,
                        "description": "エンドツーエンドのテスト",
                        "tools": ["pytest", "subprocess", "tempfile"]
                    }
                }
            }
        }

class ErrorSolutionLibrary:
    """エラー解決策ライブラリ"""
    
    def __init__(self):
        self.solutions = self._initialize_solutions()
    
    def _initialize_solutions(self) -> Dict[str, Dict[str, Any]]:
        """エラー解決策の初期化"""
        
        return {
            "no-untyped-def": {
                "error_type": "no-untyped-def",
                "description": "関数に型注釈が不足している",
                "common_causes": [
                    "関数の引数に型注釈がない",
                    "関数の戻り値に型注釈がない",
                    "typing モジュールがインポートされていない"
                ],
                "solutions": [
                    {
                        "method": "引数型注釈追加",
                        "example": """
# 修正前
def process_data(data, options):
    return processed_result

# 修正後
def process_data(data: Any, options: Dict[str, Any]) -> Any:
    return processed_result
""",
                        "note": "具体的な型が不明な場合は Any を使用"
                    },
                    {
                        "method": "戻り値型注釈追加", 
                        "example": """
# 修正前  
def calculate(x, y):
    return x + y

# 修正後
def calculate(x: int, y: int) -> int:
    return x + y
""",
                        "note": "戻り値がない場合は -> None を使用"
                    },
                    {
                        "method": "typing インポート追加",
                        "example": """
# ファイル先頭に追加
from typing import Any, Dict, List, Optional, Union
""",
                        "note": "必要な型のみインポートすることも可能"
                    }
                ],
                "prevention": [
                    "新規関数作成時に必ず型注釈を付ける",
                    "IDE の型チェック機能を有効にする",
                    "pre-commit hook で mypy チェックを実行"
                ],
                "automated_fix_pattern": """
def fix_no_untyped_def(content: str) -> str:
    '''no-untyped-def エラーの自動修正'''
    
    # 1. typing import の確認・追加
    if 'from typing import' not in content:
        content = 'from typing import Any\\n' + content
    
    # 2. 関数定義の型注釈追加
    import re
    
    # 引数の型注釈追加
    pattern = r'def (\w+)\(([^)]*)\):'
    def add_type_annotations(match):
        func_name = match.group(1)
        params = match.group(2)
        
        if not params.strip():
            return f'def {func_name}() -> None:'
        
        # 簡易的な型注釈追加
        typed_params = []
        for param in params.split(','):
            param = param.strip()
            if ':' not in param:
                param += ': Any'
            typed_params.append(param)
        
        return f'def {func_name}({", ".join(typed_params)}) -> Any:'
    
    content = re.sub(pattern, add_type_annotations, content)
    
    return content
"""
            },
            
            "no-untyped-call": {
                "error_type": "no-untyped-call",
                "description": "型注釈のない関数の呼び出し",
                "common_causes": [
                    "外部ライブラリの型情報不足",
                    "動的な関数呼び出し",
                    "型スタブファイルの不足"
                ],
                "solutions": [
                    {
                        "method": "type: ignore コメント追加",
                        "example": """
# 修正前
result = some_untyped_function(arg1, arg2)

# 修正後  
result = some_untyped_function(arg1, arg2)  # type: ignore[no-untyped-call]
""",
                        "note": "一時的な解決策として使用"
                    },
                    {
                        "method": "型スタブファイル作成",
                        "example": """
# external_lib.pyi (型スタブファイル)
def some_untyped_function(arg1: str, arg2: int) -> str: ...
""",
                        "note": "永続的な解決策として推奨"
                    },
                    {
                        "method": "cast() 使用",
                        "example": """
from typing import cast

# 修正前
result = some_untyped_function(arg1, arg2)

# 修正後
result = cast(str, some_untyped_function(arg1, arg2))
""",
                        "note": "戻り値の型が既知の場合に使用"
                    }
                ]
            },
            
            "syntax-error": {
                "error_type": "syntax-error",
                "description": "Python構文エラー",
                "common_causes": [
                    "括弧の不整合",
                    "インデントエラー",
                    "予約語の誤用",
                    "型注釈の構文エラー"
                ],
                "solutions": [
                    {
                        "method": "括弧チェック",
                        "example": """
# よくある間違い
def function(param -> Type):  # ❌ 間違い

# 正しい書き方
def function(param: Type) -> ReturnType:  # ✅ 正しい
""",
                        "note": "型注釈の : と -> の使い分けに注意"
                    }
                ]
            }
        }

class KnowledgeBase:
    """
    統合知識ベースシステム
    設計パターン・プロジェクト固有情報・実装ガイド等を統合管理
    """
    
    def __init__(self, knowledge_dir: str = "postbox/knowledge/data"):
        """
        初期化
        
        Args:
            knowledge_dir: 知識データ保存ディレクトリ
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        # 各専門ライブラリの初期化
        self.kumihan_context = KumihanFormatterContext()
        self.design_patterns = DesignPatternLibrary()
        self.implementation_guides = ImplementationGuideLibrary()
        self.error_solutions = ErrorSolutionLibrary()
        
        # 知識エントリストレージ
        self.knowledge_entries: Dict[str, KnowledgeEntry] = {}
        
        # 検索インデックス
        self.tag_index: Dict[str, Set[str]] = {}
        self.content_index: Dict[str, Set[str]] = {}
        
        # 使用統計
        self.usage_stats: Dict[str, int] = {}
        
        # 初期化
        self._initialize_knowledge_base()
        self._load_persistent_data()
        
        print("🧠 KnowledgeBase システム初期化完了")
        print(f"📚 知識エントリ: {len(self.knowledge_entries)}件")
        print(f"📂 データディレクトリ: {self.knowledge_dir}")
    
    def get_design_pattern(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """設計パターンの取得"""
        
        pattern = self.design_patterns.patterns.get(pattern_name)
        if pattern:
            self._update_usage_stats(f"pattern_{pattern_name}")
            return pattern
        return None
    
    def get_implementation_guide(self, guide_name: str) -> Optional[Dict[str, Any]]:
        """実装ガイドの取得"""
        
        guide = self.implementation_guides.guides.get(guide_name)
        if guide:
            self._update_usage_stats(f"guide_{guide_name}")
            return guide
        return None
    
    def get_error_solution(self, error_type: str) -> Optional[Dict[str, Any]]:
        """エラー解決策の取得"""
        
        solution = self.error_solutions.solutions.get(error_type)
        if solution:
            self._update_usage_stats(f"error_{error_type}")
            return solution
        return None
    
    def get_project_context(self) -> Dict[str, Any]:
        """プロジェクト固有コンテキストの取得"""
        
        self._update_usage_stats("project_context")
        return {
            "project_info": self.kumihan_context.project_info,
            "notation_rules": self.kumihan_context.notation_rules,
            "architecture_patterns": self.kumihan_context.architecture_patterns,
            "quality_standards": self.kumihan_context.quality_standards,
            "common_patterns": self.kumihan_context.common_patterns
        }
    
    def search_knowledge(self, query: str, categories: Optional[List[KnowledgeCategory]] = None,
                        knowledge_types: Optional[List[KnowledgeType]] = None,
                        tags: Optional[List[str]] = None,
                        limit: int = 10) -> List[KnowledgeEntry]:
        """知識検索"""
        
        results = []
        query_lower = query.lower()
        
        for entry in self.knowledge_entries.values():
            # カテゴリフィルター
            if categories and entry.category not in categories:
                continue
            
            # タイプフィルター
            if knowledge_types and entry.knowledge_type not in knowledge_types:
                continue
            
            # タグフィルター
            if tags and not any(tag in entry.tags for tag in tags):
                continue
            
            # コンテンツ検索
            searchable_text = (
                entry.title.lower() + " " +
                entry.description.lower() + " " +
                " ".join(entry.tags).lower() + " " +
                json.dumps(entry.content, ensure_ascii=False).lower()
            )
            
            if query_lower in searchable_text:
                results.append(entry)
                self._update_usage_stats(entry.entry_id)
                
                if len(results) >= limit:
                    break
        
        # 使用頻度でソート
        results.sort(key=lambda x: self.usage_stats.get(x.entry_id, 0), reverse=True)
        
        return results
    
    def add_knowledge_entry(self, entry: KnowledgeEntry) -> None:
        """知識エントリの追加"""
        
        entry.created_at = datetime.now().isoformat()
        entry.updated_at = entry.created_at
        
        self.knowledge_entries[entry.entry_id] = entry
        self._update_search_indexes(entry)
        self._save_knowledge_entry(entry)
        
        print(f"📝 知識エントリ追加: {entry.entry_id}")
    
    def update_knowledge_entry(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """知識エントリの更新"""
        
        if entry_id not in self.knowledge_entries:
            return False
        
        entry = self.knowledge_entries[entry_id]
        
        # 更新適用
        for key, value in updates.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        
        entry.updated_at = datetime.now().isoformat()
        
        # インデックス更新
        self._update_search_indexes(entry)
        self._save_knowledge_entry(entry)
        
        print(f"🔄 知識エントリ更新: {entry_id}")
        return True
    
    def remove_knowledge_entry(self, entry_id: str) -> bool:
        """知識エントリの削除"""
        
        if entry_id not in self.knowledge_entries:
            return False
        
        del self.knowledge_entries[entry_id]
        
        # ファイル削除
        file_path = self.knowledge_dir / f"{entry_id}.json"
        if file_path.exists():
            file_path.unlink()
        
        # インデックス更新
        self._rebuild_search_indexes()
        
        print(f"🗑️ 知識エントリ削除: {entry_id}")
        return True
    
    def get_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """コンテキストベース推奨"""
        
        recommendations = []
        
        # タスクタイプベース推奨
        task_type = context.get('type', '')
        
        if 'implementation' in task_type:
            # 設計パターン推奨
            for pattern_name, pattern_data in self.design_patterns.patterns.items():
                score = self._calculate_relevance_score(pattern_data, context)
                if score > 0.5:
                    recommendations.append({
                        "type": "design_pattern",
                        "name": pattern_name,
                        "relevance_score": score,
                        "data": pattern_data
                    })
        
        # エラータイプベース推奨
        error_type = context.get('requirements', {}).get('error_type')
        if error_type:
            solution = self.get_error_solution(error_type)
            if solution:
                recommendations.append({
                    "type": "error_solution",
                    "name": error_type,
                    "relevance_score": 1.0,
                    "data": solution
                })
        
        # 関連実装ガイド推奨
        if task_type == 'new_implementation':
            guide = self.get_implementation_guide('new_class_implementation')
            if guide:
                recommendations.append({
                    "type": "implementation_guide",
                    "name": "new_class_implementation", 
                    "relevance_score": 0.9,
                    "data": guide
                })
        
        # スコア順でソート
        recommendations.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return recommendations[:5]  # 上位5件
    
    def generate_context_aware_template(self, task_data: Dict[str, Any]) -> str:
        """コンテキスト対応テンプレート生成"""
        
        task_type = task_data.get('type', '')
        implementation_spec = task_data.get('requirements', {}).get('implementation_spec', {})
        
        context = f"""
# Kumihan-Formatter 実装コンテキスト

## プロジェクト情報
{json.dumps(self.kumihan_context.project_info, indent=2, ensure_ascii=False)}

## 品質基準
{json.dumps(self.kumihan_context.quality_standards, indent=2, ensure_ascii=False)}

## タスク固有推奨
"""
        
        # 推奨取得
        recommendations = self.get_recommendations(task_data)
        for rec in recommendations:
            context += f"\n### {rec['type']}: {rec['name']} (関連度: {rec['relevance_score']:.2f})\n"
            
            if rec['type'] == 'design_pattern':
                pattern = rec['data']
                context += f"**目的**: {pattern['intent']}\n"
                context += f"**適用場面**: {', '.join(pattern['applicability'])}\n"
                context += f"**テンプレート**:\n```python\n{pattern['template']}\n```\n"
            
            elif rec['type'] == 'error_solution':
                solution = rec['data']
                context += f"**説明**: {solution['description']}\n"
                context += "**解決策**:\n"
                for sol in solution['solutions']:
                    context += f"- {sol['method']}\n"
            
            elif rec['type'] == 'implementation_guide':
                guide = rec['data']
                context += f"**説明**: {guide['description']}\n"
                context += "**手順**:\n"
                for step in guide['steps']:
                    context += f"{step['step']}. {step['title']}\n"
        
        context += """

## Flash 2.5 実行指示
1. 上記コンテキストを参考に実装を進める
2. 品質基準を必ず遵守する
3. 適用可能な設計パターンを考慮する
4. エラーが発生した場合は解決策を参考にする
5. 実装完了後は品質チェックを実行する
"""
        
        return context
    
    def export_knowledge_base(self, export_path: str) -> str:
        """知識ベースのエクスポート"""
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "knowledge_entries": [
                {
                    "entry_id": entry.entry_id,
                    "title": entry.title,
                    "category": entry.category.value,
                    "knowledge_type": entry.knowledge_type.value,
                    "content": entry.content,
                    "description": entry.description,
                    "tags": entry.tags,
                    "difficulty_level": entry.difficulty_level,
                    "usage_frequency": entry.usage_frequency,
                    "created_at": entry.created_at,
                    "updated_at": entry.updated_at,
                    "version": entry.version,
                    "prerequisites": entry.prerequisites,
                    "related_entries": entry.related_entries,
                    "metadata": entry.metadata
                }
                for entry in self.knowledge_entries.values()
            ],
            "design_patterns": self.design_patterns.patterns,
            "implementation_guides": self.implementation_guides.guides,
            "error_solutions": self.error_solutions.solutions,
            "project_context": self.get_project_context(),
            "usage_stats": self.usage_stats
        }
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"📤 知識ベースエクスポート: {export_path}")
        return export_path
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得"""
        
        stats = {
            "total_entries": len(self.knowledge_entries),
            "categories": {},
            "knowledge_types": {},
            "difficulty_levels": {},
            "total_usage": sum(self.usage_stats.values()),
            "most_used": [],
            "storage_size_mb": self._calculate_storage_size()
        }
        
        # カテゴリ別・タイプ別統計
        for entry in self.knowledge_entries.values():
            cat = entry.category.value
            ktype = entry.knowledge_type.value
            diff = entry.difficulty_level
            
            stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
            stats["knowledge_types"][ktype] = stats["knowledge_types"].get(ktype, 0) + 1
            stats["difficulty_levels"][diff] = stats["difficulty_levels"].get(diff, 0) + 1
        
        # 最も使用される知識
        sorted_usage = sorted(self.usage_stats.items(), key=lambda x: x[1], reverse=True)
        stats["most_used"] = sorted_usage[:10]
        
        return stats
    
    def _initialize_knowledge_base(self) -> None:
        """知識ベースの初期化"""
        
        # 設計パターンエントリの作成
        for pattern_name, pattern_data in self.design_patterns.patterns.items():
            entry = KnowledgeEntry(
                entry_id=f"pattern_{pattern_name}",
                title=pattern_data["name"],
                category=KnowledgeCategory.DESIGN_PATTERNS,
                knowledge_type=KnowledgeType.PATTERN,
                content=pattern_data,
                description=pattern_data["intent"],
                tags=["design_pattern", pattern_name] + pattern_data.get("benefits", []),
                difficulty_level="intermediate"
            )
            self.knowledge_entries[entry.entry_id] = entry
        
        # 実装ガイドエントリの作成
        for guide_name, guide_data in self.implementation_guides.guides.items():
            entry = KnowledgeEntry(
                entry_id=f"guide_{guide_name}",
                title=guide_data["title"],
                category=KnowledgeCategory.IMPLEMENTATION_GUIDES,
                knowledge_type=KnowledgeType.GUIDE,
                content=guide_data,
                description=guide_data["description"],
                tags=["implementation", "guide"] + guide_name.split("_"),
                difficulty_level="basic"
            )
            self.knowledge_entries[entry.entry_id] = entry
        
        # エラー解決策エントリの作成
        for error_type, solution_data in self.error_solutions.solutions.items():
            entry = KnowledgeEntry(
                entry_id=f"error_{error_type}",
                title=f"{error_type} 解決策",
                category=KnowledgeCategory.ERROR_SOLUTIONS,
                knowledge_type=KnowledgeType.REFERENCE,
                content=solution_data,
                description=solution_data["description"],
                tags=["error", "solution", error_type],
                difficulty_level="basic"
            )
            self.knowledge_entries[entry.entry_id] = entry
        
        # プロジェクト固有エントリの作成
        project_context = self.get_project_context()
        entry = KnowledgeEntry(
            entry_id="kumihan_project_context",
            title="Kumihan-Formatter プロジェクトコンテキスト",
            category=KnowledgeCategory.PROJECT_SPECIFIC,
            knowledge_type=KnowledgeType.REFERENCE,
            content=project_context,
            description="Kumihan-Formatter プロジェクト固有の情報とルール",
            tags=["project", "kumihan", "context", "rules"],
            difficulty_level="basic"
        )
        self.knowledge_entries[entry.entry_id] = entry
        
        # 検索インデックス構築
        self._rebuild_search_indexes()
    
    def _update_search_indexes(self, entry: KnowledgeEntry) -> None:
        """検索インデックスの更新"""
        
        # タグインデックス
        for tag in entry.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(entry.entry_id)
        
        # コンテンツインデックス（簡易実装）
        content_words = (
            entry.title.lower() + " " +
            entry.description.lower() + " " +
            json.dumps(entry.content, ensure_ascii=False).lower()
        ).split()
        
        for word in content_words:
            if len(word) > 2:  # 2文字以上の単語のみ
                if word not in self.content_index:
                    self.content_index[word] = set()
                self.content_index[word].add(entry.entry_id)
    
    def _rebuild_search_indexes(self) -> None:
        """検索インデックスの再構築"""
        
        self.tag_index.clear()
        self.content_index.clear()
        
        for entry in self.knowledge_entries.values():
            self._update_search_indexes(entry)
    
    def _update_usage_stats(self, entry_id: str) -> None:
        """使用統計の更新"""
        
        self.usage_stats[entry_id] = self.usage_stats.get(entry_id, 0) + 1
        
        # 知識エントリの使用頻度も更新
        if entry_id in self.knowledge_entries:
            self.knowledge_entries[entry_id].usage_frequency += 1
    
    def _calculate_relevance_score(self, item_data: Dict[str, Any], context: Dict[str, Any]) -> float:
        """関連度スコア計算"""
        
        score = 0.0
        
        # キーワードマッチング
        context_text = json.dumps(context, ensure_ascii=False).lower()
        item_text = json.dumps(item_data, ensure_ascii=False).lower()
        
        common_words = set(context_text.split()) & set(item_text.split())
        score += len(common_words) * 0.1
        
        # 特定パターンの関連度
        if 'implementation' in context_text and 'template' in item_text:
            score += 0.3
        
        if 'error' in context_text and 'solution' in item_text:
            score += 0.5
        
        return min(score, 1.0)
    
    def _save_knowledge_entry(self, entry: KnowledgeEntry) -> None:
        """知識エントリのファイル保存"""
        
        file_path = self.knowledge_dir / f"{entry.entry_id}.json"
        
        entry_data = {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "category": entry.category.value,
            "knowledge_type": entry.knowledge_type.value,
            "content": entry.content,
            "description": entry.description,
            "tags": entry.tags,
            "difficulty_level": entry.difficulty_level,
            "usage_frequency": entry.usage_frequency,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
            "version": entry.version,
            "prerequisites": entry.prerequisites,
            "related_entries": entry.related_entries,
            "metadata": entry.metadata
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(entry_data, f, indent=2, ensure_ascii=False)
    
    def _load_persistent_data(self) -> None:
        """永続化データの読み込み"""
        
        if not self.knowledge_dir.exists():
            return
        
        loaded_count = 0
        
        for file_path in self.knowledge_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    entry_data = json.load(f)
                
                # Enumの復元
                entry_data['category'] = KnowledgeCategory(entry_data['category'])
                entry_data['knowledge_type'] = KnowledgeType(entry_data['knowledge_type'])
                
                entry = KnowledgeEntry(**entry_data)
                
                # 既存エントリの更新または新規追加
                if entry.entry_id not in self.knowledge_entries:
                    self.knowledge_entries[entry.entry_id] = entry
                    loaded_count += 1
                
            except Exception as e:
                print(f"⚠️ 知識エントリ読み込みエラー {file_path}: {e}")
                continue
        
        # 使用統計の読み込み
        stats_file = self.knowledge_dir / "usage_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.usage_stats = json.load(f)
            except Exception:
                pass
        
        if loaded_count > 0:
            print(f"📖 永続化知識エントリ読み込み: {loaded_count}件")
    
    def _calculate_storage_size(self) -> float:
        """ストレージサイズ計算（MB）"""
        
        total_size = 0
        
        if self.knowledge_dir.exists():
            for file_path in self.knowledge_dir.rglob("*.json"):
                total_size += file_path.stat().st_size
        
        return total_size / (1024 * 1024)  # MB


def main():
    """テスト実行"""
    
    kb = KnowledgeBase()
    
    print("🧪 KnowledgeBase テスト実行")
    
    # 設計パターン取得テスト
    factory_pattern = kb.get_design_pattern("factory")
    if factory_pattern:
        print(f"🏭 Factory Pattern: {factory_pattern['intent']}")
    
    # エラー解決策取得テスト
    error_solution = kb.get_error_solution("no-untyped-def")
    if error_solution:
        print(f"🛠️ no-untyped-def 解決策: {len(error_solution['solutions'])}種類")
    
    # プロジェクトコンテキスト取得テスト
    project_context = kb.get_project_context()
    print(f"🏗️ プロジェクトコンテキスト: {project_context['project_info']['name']}")
    
    # 知識検索テスト
    search_results = kb.search_knowledge("implementation", limit=3)
    print(f"🔍 実装関連知識: {len(search_results)}件")
    for result in search_results:
        print(f"  - {result.title} ({result.category.value})")
    
    # 推奨テスト
    test_task = {
        'type': 'new_implementation',
        'requirements': {
            'implementation_spec': {
                'template_type': 'class'
            }
        }
    }
    
    recommendations = kb.get_recommendations(test_task)
    print(f"💡 推奨: {len(recommendations)}件")
    for rec in recommendations:
        print(f"  - {rec['name']} (関連度: {rec['relevance_score']:.2f})")
    
    # コンテキスト対応テンプレート生成テスト
    template = kb.generate_context_aware_template(test_task)
    print(f"📄 生成テンプレート: {len(template)}文字")
    
    # 統計表示
    stats = kb.get_statistics()
    print(f"\n📊 統計:")
    print(f"  総知識エントリ: {stats['total_entries']}")
    print(f"  カテゴリ数: {len(stats['categories'])}")
    print(f"  総使用回数: {stats['total_usage']}")
    print(f"  ストレージサイズ: {stats['storage_size_mb']:.2f}MB")


if __name__ == "__main__":
    main()