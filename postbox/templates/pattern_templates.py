#!/usr/bin/env python3
"""
Pattern Templates for Gemini Capability Enhancement
Factory/Strategy/Observer/Pluginパターンの具体的実装テンプレート・カスタマイゼーション機構
"""

import json
import re
import os
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import ast
import textwrap

class PatternType(Enum):
    """パターンタイプ"""
    FACTORY = "factory"
    ABSTRACT_FACTORY = "abstract_factory"
    STRATEGY = "strategy"
    OBSERVER = "observer"
    PLUGIN = "plugin"
    DECORATOR = "decorator"
    ADAPTER = "adapter"
    COMMAND = "command"
    BUILDER = "builder"
    SINGLETON = "singleton"

class TemplateComplexity(Enum):
    """テンプレート複雑度"""
    BASIC = "basic"           # 基本実装
    INTERMEDIATE = "intermediate"  # 中級実装  
    ADVANCED = "advanced"     # 高度実装
    PRODUCTION = "production" # 本格運用

@dataclass
class PatternTemplate:
    """パターンテンプレート"""
    pattern_type: PatternType
    name: str
    description: str
    complexity: TemplateComplexity
    base_template: str
    customization_points: List[str]
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    usage_examples: List[str] = field(default_factory=list)
    test_template: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CustomizationConfig:
    """カスタマイゼーション設定"""
    class_names: Dict[str, str] = field(default_factory=dict)
    method_names: Dict[str, str] = field(default_factory=dict)
    interface_names: Dict[str, str] = field(default_factory=dict)
    type_parameters: Dict[str, str] = field(default_factory=dict)
    custom_imports: List[str] = field(default_factory=list)
    custom_decorators: List[str] = field(default_factory=list)
    docstring_style: str = "google"  # google, numpy, sphinx
    add_type_comments: bool = True
    add_logging: bool = False
    add_validation: bool = False

class PatternTemplateEngine:
    """パターンテンプレートエンジン"""
    
    def __init__(self):
        self.templates: Dict[str, PatternTemplate] = {}
        self._initialize_builtin_templates()
        
        # カスタマイゼーションルール
        self.naming_conventions = {
            "class": "PascalCase",
            "method": "snake_case", 
            "variable": "snake_case",
            "constant": "UPPER_SNAKE_CASE",
            "interface": "I{PascalCase}"
        }
        
        print("🏗️ PatternTemplateEngine 初期化完了")
        print(f"📐 利用可能パターン: {len(self.templates)}種類")
    
    def generate_pattern(self, pattern_type: PatternType, 
                        config: CustomizationConfig,
                        context: Optional[Dict[str, Any]] = None) -> str:
        """
        パターン実装の生成
        
        Args:
            pattern_type: パターンタイプ
            config: カスタマイゼーション設定
            context: 追加コンテキスト
            
        Returns:
            生成されたコード
        """
        
        template_key = pattern_type.value
        if template_key not in self.templates:
            raise ValueError(f"Unsupported pattern type: {pattern_type}")
        
        template = self.templates[template_key]
        
        print(f"🎨 パターン生成開始: {pattern_type.value}")
        
        # テンプレート変数の準備
        template_vars = self._prepare_template_variables(template, config, context or {})
        
        # テンプレートの展開
        generated_code = self._expand_template(template.base_template, template_vars)
        
        # ポストプロセッシング
        generated_code = self._post_process_code(generated_code, config)
        
        print(f"✅ パターン生成完了: {len(generated_code)}文字")
        return generated_code
    
    def generate_test_code(self, pattern_type: PatternType,
                          config: CustomizationConfig,
                          context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        テストコードの生成
        
        Args:
            pattern_type: パターンタイプ
            config: カスタマイゼーション設定
            context: 追加コンテキスト
            
        Returns:
            生成されたテストコード
        """
        
        template_key = pattern_type.value
        if template_key not in self.templates:
            return None
        
        template = self.templates[template_key]
        if not template.test_template:
            return None
        
        print(f"🧪 テストコード生成: {pattern_type.value}")
        
        # テンプレート変数の準備
        template_vars = self._prepare_template_variables(template, config, context or {})
        
        # テストテンプレートの展開
        test_code = self._expand_template(template.test_template, template_vars)
        
        # ポストプロセッシング
        test_code = self._post_process_code(test_code, config)
        
        return test_code
    
    def get_pattern_info(self, pattern_type: PatternType) -> Optional[Dict[str, Any]]:
        """パターン情報の取得"""
        
        template_key = pattern_type.value
        if template_key not in self.templates:
            return None
        
        template = self.templates[template_key]
        
        return {
            "name": template.name,
            "description": template.description,
            "complexity": template.complexity.value,
            "customization_points": template.customization_points,
            "parameters": template.parameters,
            "dependencies": template.dependencies,
            "usage_examples": template.usage_examples
        }
    
    def list_available_patterns(self) -> List[Dict[str, str]]:
        """利用可能パターン一覧"""
        
        patterns = []
        for pattern_type, template in self.templates.items():
            patterns.append({
                "type": pattern_type,
                "name": template.name,
                "description": template.description,
                "complexity": template.complexity.value
            })
        
        return patterns
    
    def customize_pattern(self, pattern_type: PatternType,
                         customizations: Dict[str, Any]) -> CustomizationConfig:
        """パターンのカスタマイゼーション設定生成"""
        
        config = CustomizationConfig()
        
        # 基本的なカスタマイゼーション適用
        if "class_names" in customizations:
            config.class_names.update(customizations["class_names"])
        
        if "method_names" in customizations:
            config.method_names.update(customizations["method_names"])
        
        if "interface_names" in customizations:
            config.interface_names.update(customizations["interface_names"])
        
        if "imports" in customizations:
            config.custom_imports.extend(customizations["imports"])
        
        # パターン固有のカスタマイゼーション
        if pattern_type == PatternType.FACTORY:
            self._customize_factory_pattern(config, customizations)
        elif pattern_type == PatternType.STRATEGY:
            self._customize_strategy_pattern(config, customizations)
        elif pattern_type == PatternType.OBSERVER:
            self._customize_observer_pattern(config, customizations)
        elif pattern_type == PatternType.PLUGIN:
            self._customize_plugin_pattern(config, customizations)
        
        return config
    
    def _initialize_builtin_templates(self) -> None:
        """組み込みテンプレートの初期化"""
        
        # Factory Pattern
        self._add_factory_pattern()
        
        # Strategy Pattern
        self._add_strategy_pattern()
        
        # Observer Pattern  
        self._add_observer_pattern()
        
        # Plugin Pattern
        self._add_plugin_pattern()
        
        # Builder Pattern
        self._add_builder_pattern()
        
        # Decorator Pattern
        self._add_decorator_pattern()
    
    def _add_factory_pattern(self) -> None:
        """Factory Pattern テンプレート追加"""
        
        base_template = '''
"""
{description}
Factory Pattern Implementation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
{custom_imports}

class {product_interface}(ABC):
    """製品インターフェース"""
    
    @abstractmethod
    def {operation_method}(self) -> str:
        """製品の操作"""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """製品情報の取得"""
        pass

class {concrete_product_a}({product_interface}):
    """具体製品A"""
    
    def __init__(self, name: str = "ProductA") -> None:
        self.name = name
    
    def {operation_method}(self) -> str:
        return f"Operation from {self.name}"
    
    def get_info(self) -> Dict[str, Any]:
        return {{
            "name": self.name,
            "type": "{concrete_product_a}",
            "version": "1.0"
        }}

class {concrete_product_b}({product_interface}):
    """具体製品B"""
    
    def __init__(self, name: str = "ProductB") -> None:
        self.name = name
    
    def {operation_method}(self) -> str:
        return f"Operation from {self.name}"
    
    def get_info(self) -> Dict[str, Any]:
        return {{
            "name": self.name,
            "type": "{concrete_product_b}",
            "version": "1.0"
        }}

class {creator_interface}(ABC):
    """作成者インターフェース"""
    
    @abstractmethod
    def {factory_method}(self, product_type: str, **kwargs: Any) -> {product_interface}:
        """ファクトリメソッド"""
        pass
    
    def {business_logic}(self, product_type: str) -> str:
        """ビジネスロジック"""
        product = self.{factory_method}(product_type)
        return f"Creator: {product.{operation_method}()}"

class {concrete_creator}({creator_interface}):
    """具体的な作成者"""
    
    def __init__(self) -> None:
        self._product_registry: Dict[str, Type[{product_interface}]] = {{
            "A": {concrete_product_a},
            "B": {concrete_product_b}
        }}
    
    def {factory_method}(self, product_type: str, **kwargs: Any) -> {product_interface}:
        """製品の作成"""
        if product_type not in self._product_registry:
            raise ValueError(f"Unknown product type: {product_type}")
        
        product_class = self._product_registry[product_type]
        return product_class(**kwargs)
    
    def register_product(self, product_type: str, product_class: Type[{product_interface}]) -> None:
        """新しい製品タイプの登録"""
        self._product_registry[product_type] = product_class
    
    def list_available_products(self) -> List[str]:
        """利用可能な製品タイプの一覧"""
        return list(self._product_registry.keys())

# 使用例
def create_factory_example() -> None:
    """ファクトリーパターンの使用例"""
    creator = {concrete_creator}()
    
    # 製品Aの作成
    product_a = creator.{factory_method}("A", name="Custom Product A")
    print(product_a.{operation_method}())
    print(product_a.get_info())
    
    # 製品Bの作成
    product_b = creator.{factory_method}("B", name="Custom Product B")
    print(product_b.{operation_method}())
    print(product_b.get_info())
    
    # ビジネスロジックの実行
    result = creator.{business_logic}("A")
    print(result)

if __name__ == "__main__":
    create_factory_example()
'''
        
        test_template = '''
"""
{description} - Test Cases
"""

import unittest
from unittest.mock import Mock, patch
from {module_name} import {product_interface}, {concrete_product_a}, {concrete_product_b}, {concrete_creator}

class Test{concrete_creator}(unittest.TestCase):
    """ファクトリテストケース"""
    
    def setUp(self) -> None:
        self.creator = {concrete_creator}()
    
    def test_create_product_a(self) -> None:
        """製品A作成テスト"""
        product = self.creator.{factory_method}("A")
        self.assertIsInstance(product, {concrete_product_a})
        self.assertEqual(product.{operation_method}(), "Operation from ProductA")
    
    def test_create_product_b(self) -> None:
        """製品B作成テスト"""
        product = self.creator.{factory_method}("B")
        self.assertIsInstance(product, {concrete_product_b})
        self.assertEqual(product.{operation_method}(), "Operation from ProductB")
    
    def test_invalid_product_type(self) -> None:
        """無効な製品タイプテスト"""
        with self.assertRaises(ValueError):
            self.creator.{factory_method}("INVALID")
    
    def test_register_new_product(self) -> None:
        """新製品登録テスト"""
        class MockProduct({product_interface}):
            def {operation_method}(self) -> str:
                return "Mock operation"
            
            def get_info(self) -> Dict[str, Any]:
                return {{"name": "Mock", "type": "MockProduct"}}
        
        self.creator.register_product("MOCK", MockProduct)
        product = self.creator.{factory_method}("MOCK")
        self.assertIsInstance(product, MockProduct)

if __name__ == "__main__":
    unittest.main()
'''
        
        template = PatternTemplate(
            pattern_type=PatternType.FACTORY,
            name="Factory Pattern",
            description="オブジェクト作成のインターフェースを提供するパターン",
            complexity=TemplateComplexity.INTERMEDIATE,
            base_template=base_template,
            customization_points=[
                "product_interface", "concrete_product_a", "concrete_product_b",
                "creator_interface", "concrete_creator", "factory_method",
                "operation_method", "business_logic"
            ],
            parameters={
                "product_interface": "Product",
                "concrete_product_a": "ConcreteProductA", 
                "concrete_product_b": "ConcreteProductB",
                "creator_interface": "Creator",
                "concrete_creator": "ConcreteCreator",
                "factory_method": "create_product",
                "operation_method": "execute",
                "business_logic": "do_something"
            },
            dependencies=["abc", "typing"],
            test_template=test_template,
            usage_examples=[
                "creator = ConcreteCreator()",
                "product = creator.create_product('A')",
                "result = product.execute()"
            ]
        )
        
        self.templates["factory"] = template
    
    def _add_strategy_pattern(self) -> None:
        """Strategy Pattern テンプレート追加"""
        
        base_template = '''
"""
{description}
Strategy Pattern Implementation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
{custom_imports}

class {strategy_interface}(ABC):
    """戦略インターフェース"""
    
    @abstractmethod
    def {execute_method}(self, data: Any) -> Any:
        """戦略の実行"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """戦略名の取得"""
        pass

class {concrete_strategy_a}({strategy_interface}):
    """具体的戦略A"""
    
    def {execute_method}(self, data: List[int]) -> List[int]:
        """昇順ソート戦略"""
        return sorted(data)
    
    def get_name(self) -> str:
        return "Ascending Sort Strategy"

class {concrete_strategy_b}({strategy_interface}):
    """具体的戦略B"""
    
    def {execute_method}(self, data: List[int]) -> List[int]:
        """降順ソート戦略"""
        return sorted(data, reverse=True)
    
    def get_name(self) -> str:
        return "Descending Sort Strategy"

class {context_class}:
    """戦略コンテキスト"""
    
    def __init__(self, strategy: Optional[{strategy_interface}] = None) -> None:
        self._strategy = strategy
        self._strategy_registry: Dict[str, Type[{strategy_interface}]] = {{
            "asc": {concrete_strategy_a},
            "desc": {concrete_strategy_b}
        }}
    
    @property
    def strategy(self) -> Optional[{strategy_interface}]:
        return self._strategy
    
    @strategy.setter
    def strategy(self, strategy: {strategy_interface}) -> None:
        self._strategy = strategy
    
    def set_strategy_by_name(self, strategy_name: str) -> None:
        """名前による戦略設定"""
        if strategy_name not in self._strategy_registry:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        strategy_class = self._strategy_registry[strategy_name]
        self._strategy = strategy_class()
    
    def register_strategy(self, name: str, strategy_class: Type[{strategy_interface}]) -> None:
        """新しい戦略の登録"""
        self._strategy_registry[name] = strategy_class
    
    def {context_method}(self, data: Any) -> Any:
        """コンテキストインターフェース"""
        if not self._strategy:
            raise ValueError("No strategy set")
        
        return self._strategy.{execute_method}(data)
    
    def get_available_strategies(self) -> List[str]:
        """利用可能な戦略の一覧"""
        return list(self._strategy_registry.keys())
    
    def get_current_strategy_name(self) -> Optional[str]:
        """現在の戦略名"""
        if not self._strategy:
            return None
        return self._strategy.get_name()

# 使用例
def strategy_example() -> None:
    """戦略パターンの使用例"""
    data = [64, 34, 25, 12, 22, 11, 90]
    
    # 昇順ソート戦略
    context = {context_class}()
    context.set_strategy_by_name("asc")
    result1 = context.{context_method}(data.copy())
    print(f"昇順: {result1}")
    
    # 降順ソート戦略
    context.set_strategy_by_name("desc")
    result2 = context.{context_method}(data.copy())
    print(f"降順: {result2}")
    
    # 利用可能戦略の表示
    strategies = context.get_available_strategies()
    print(f"利用可能戦略: {strategies}")

if __name__ == "__main__":
    strategy_example()
'''
        
        test_template = '''
"""
{description} - Test Cases
"""

import unittest
from {module_name} import {strategy_interface}, {concrete_strategy_a}, {concrete_strategy_b}, {context_class}

class Test{context_class}(unittest.TestCase):
    """戦略パターンテストケース"""
    
    def setUp(self) -> None:
        self.context = {context_class}()
        self.test_data = [3, 1, 4, 1, 5, 9, 2, 6]
    
    def test_ascending_strategy(self) -> None:
        """昇順戦略テスト"""
        self.context.set_strategy_by_name("asc")
        result = self.context.{context_method}(self.test_data.copy())
        self.assertEqual(result, [1, 1, 2, 3, 4, 5, 6, 9])
    
    def test_descending_strategy(self) -> None:
        """降順戦略テスト"""
        self.context.set_strategy_by_name("desc")
        result = self.context.{context_method}(self.test_data.copy())
        self.assertEqual(result, [9, 6, 5, 4, 3, 2, 1, 1])
    
    def test_no_strategy_error(self) -> None:
        """戦略未設定エラーテスト"""
        with self.assertRaises(ValueError):
            self.context.{context_method}(self.test_data)
    
    def test_invalid_strategy_name(self) -> None:
        """無効戦略名テスト"""
        with self.assertRaises(ValueError):
            self.context.set_strategy_by_name("invalid")

if __name__ == "__main__":
    unittest.main()
'''
        
        template = PatternTemplate(
            pattern_type=PatternType.STRATEGY,
            name="Strategy Pattern",
            description="アルゴリズムファミリーを定義し実行時選択可能にするパターン",
            complexity=TemplateComplexity.INTERMEDIATE,
            base_template=base_template,
            customization_points=[
                "strategy_interface", "concrete_strategy_a", "concrete_strategy_b",
                "context_class", "execute_method", "context_method"
            ],
            parameters={
                "strategy_interface": "Strategy",
                "concrete_strategy_a": "ConcreteStrategyA",
                "concrete_strategy_b": "ConcreteStrategyB",
                "context_class": "Context",
                "execute_method": "execute",
                "context_method": "do_algorithm"
            },
            dependencies=["abc", "typing"],
            test_template=test_template
        )
        
        self.templates["strategy"] = template
    
    def _add_observer_pattern(self) -> None:
        """Observer Pattern テンプレート追加"""
        
        base_template = '''
"""
{description}
Observer Pattern Implementation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set
from weakref import WeakSet
{custom_imports}

class {observer_interface}(ABC):
    """観察者インターフェース"""
    
    @abstractmethod
    def {update_method}(self, subject: '{subject_interface}', event_data: Any = None) -> None:
        """更新通知"""
        pass
    
    @abstractmethod
    def get_observer_id(self) -> str:
        """観察者ID取得"""
        pass

class {subject_interface}(ABC):
    """被観察者インターフェース"""
    
    def __init__(self) -> None:
        self._observers: Set[{observer_interface}] = WeakSet()
    
    def {attach_method}(self, observer: {observer_interface}) -> None:
        """観察者の登録"""
        self._observers.add(observer)
    
    def {detach_method}(self, observer: {observer_interface}) -> None:
        """観察者の登録解除"""
        self._observers.discard(observer)
    
    def {notify_method}(self, event_data: Any = None) -> None:
        """観察者への通知"""
        for observer in self._observers.copy():
            try:
                observer.{update_method}(self, event_data)
            except Exception as e:
                print(f"Observer notification failed: {e}")
    
    def get_observer_count(self) -> int:
        """観察者数の取得"""
        return len(self._observers)

class {concrete_subject}({subject_interface}):
    """具体的被観察者"""
    
    def __init__(self, initial_state: Any = None) -> None:
        super().__init__()
        self._state = initial_state
        self._change_history: List[Dict[str, Any]] = []
    
    @property
    def state(self) -> Any:
        return self._state
    
    @state.setter
    def state(self, new_state: Any) -> None:
        old_state = self._state
        self._state = new_state
        
        # 変更履歴記録
        change_record = {{
            "timestamp": str(datetime.now()),
            "old_state": old_state,
            "new_state": new_state
        }}
        self._change_history.append(change_record)
        
        # 観察者に通知
        self.{notify_method}(change_record)
    
    def get_change_history(self) -> List[Dict[str, Any]]:
        """変更履歴の取得"""
        return self._change_history.copy()

class {concrete_observer_a}({observer_interface}):
    """具体的観察者A"""
    
    def __init__(self, observer_id: str) -> None:
        self.observer_id = observer_id
        self.received_updates: List[Dict[str, Any]] = []
    
    def {update_method}(self, subject: {subject_interface}, event_data: Any = None) -> None:
        update_record = {{
            "observer_id": self.observer_id,
            "subject_type": type(subject).__name__,
            "event_data": event_data,
            "timestamp": str(datetime.now())
        }}
        self.received_updates.append(update_record)
        print(f"Observer {self.observer_id}: Received update from {type(subject).__name__}")
    
    def get_observer_id(self) -> str:
        return self.observer_id
    
    def get_update_history(self) -> List[Dict[str, Any]]:
        """更新履歴の取得"""
        return self.received_updates.copy()

class {concrete_observer_b}({observer_interface}):
    """具体的観察者B"""
    
    def __init__(self, observer_id: str, filter_condition: Optional[callable] = None) -> None:
        self.observer_id = observer_id
        self.filter_condition = filter_condition
        self.update_count = 0
    
    def {update_method}(self, subject: {subject_interface}, event_data: Any = None) -> None:
        # フィルター条件チェック
        if self.filter_condition and not self.filter_condition(event_data):
            return
        
        self.update_count += 1
        print(f"Observer {self.observer_id}: Update #{self.update_count}")
        
        if hasattr(subject, 'state'):
            print(f"  New state: {subject.state}")
    
    def get_observer_id(self) -> str:
        return self.observer_id

# 使用例
def observer_example() -> None:
    """観察者パターンの使用例"""
    from datetime import datetime
    
    # 被観察者の作成
    subject = {concrete_subject}("initial_state")
    
    # 観察者の作成
    observer1 = {concrete_observer_a}("logger")
    observer2 = {concrete_observer_b}("monitor")
    observer3 = {concrete_observer_b}("filtered", lambda data: data.get("new_state") != "ignore")
    
    # 観察者を登録
    subject.{attach_method}(observer1)
    subject.{attach_method}(observer2)
    subject.{attach_method}(observer3)
    
    print(f"Observer count: {subject.get_observer_count()}")
    
    # 状態変更（通知が発生）
    subject.state = "state_1"
    subject.state = "state_2"
    subject.state = "ignore"  # observer3 はフィルターで除外
    
    # 履歴表示
    print("\\nChange history:")
    for change in subject.get_change_history():
        print(f"  {change}")

if __name__ == "__main__":
    observer_example()
'''
        
        template = PatternTemplate(
            pattern_type=PatternType.OBSERVER,
            name="Observer Pattern",
            description="オブジェクト間の一対多の依存関係を定義するパターン",
            complexity=TemplateComplexity.INTERMEDIATE,
            base_template=base_template,
            customization_points=[
                "observer_interface", "subject_interface", "concrete_subject",
                "concrete_observer_a", "concrete_observer_b", "update_method",
                "attach_method", "detach_method", "notify_method"
            ],
            parameters={
                "observer_interface": "Observer",
                "subject_interface": "Subject",
                "concrete_subject": "ConcreteSubject",
                "concrete_observer_a": "ConcreteObserverA",
                "concrete_observer_b": "ConcreteObserverB", 
                "update_method": "update",
                "attach_method": "attach",
                "detach_method": "detach",
                "notify_method": "notify"
            },
            dependencies=["abc", "typing", "weakref", "datetime"]
        )
        
        self.templates["observer"] = template
    
    def _add_plugin_pattern(self) -> None:
        """Plugin Pattern テンプレート追加"""
        
        base_template = '''
"""
{description}
Plugin Pattern Implementation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Set
import importlib
import inspect
from pathlib import Path
{custom_imports}

class {plugin_interface}(ABC):
    """プラグインインターフェース"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """プラグイン名"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """プラグインバージョン"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """プラグイン説明"""
        pass
    
    @abstractmethod
    def {initialize_method}(self, config: Dict[str, Any]) -> None:
        """プラグインの初期化"""
        pass
    
    @abstractmethod
    def {execute_method}(self, data: Any, **kwargs: Any) -> Any:
        """プラグインの実行"""
        pass
    
    @abstractmethod
    def {cleanup_method}(self) -> None:
        """プラグインの終了処理"""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """プラグインメタデータ"""
        return {{
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "class": self.__class__.__name__
        }}

class {plugin_manager}:
    """プラグインマネージャー"""
    
    def __init__(self) -> None:
        self._plugins: Dict[str, {plugin_interface}] = {{}}
        self._plugin_configs: Dict[str, Dict[str, Any]] = {{}}
        self._execution_order: List[str] = []
    
    def {register_method}(self, plugin: {plugin_interface}, 
                         config: Optional[Dict[str, Any]] = None) -> None:
        """プラグインの登録"""
        plugin_name = plugin.name
        
        if plugin_name in self._plugins:
            raise ValueError(f"Plugin '{plugin_name}' is already registered")
        
        try:
            plugin.{initialize_method}(config or {{}})
            self._plugins[plugin_name] = plugin
            self._plugin_configs[plugin_name] = config or {{}}
            self._execution_order.append(plugin_name)
            
            print(f"Plugin '{plugin_name}' registered successfully")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize plugin '{plugin_name}': {e}")
    
    def {unregister_method}(self, plugin_name: str) -> None:
        """プラグインの登録解除"""
        if plugin_name not in self._plugins:
            raise ValueError(f"Plugin '{plugin_name}' is not registered")
        
        try:
            plugin = self._plugins[plugin_name]
            plugin.{cleanup_method}()
            
            del self._plugins[plugin_name]
            del self._plugin_configs[plugin_name]
            self._execution_order.remove(plugin_name)
            
            print(f"Plugin '{plugin_name}' unregistered successfully")
            
        except Exception as e:
            print(f"Warning: Error during plugin cleanup: {e}")
    
    def {execute_plugin_method}(self, plugin_name: str, data: Any, **kwargs: Any) -> Any:
        """特定プラグインの実行"""
        if plugin_name not in self._plugins:
            raise ValueError(f"Plugin '{plugin_name}' is not registered")
        
        plugin = self._plugins[plugin_name]
        
        try:
            return plugin.{execute_method}(data, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Plugin '{plugin_name}' execution failed: {e}")
    
    def {execute_all_method}(self, data: Any, **kwargs: Any) -> Dict[str, Any]:
        """全プラグインの実行"""
        results = {{}}
        
        for plugin_name in self._execution_order:
            try:
                result = self.{execute_plugin_method}(plugin_name, data, **kwargs)
                results[plugin_name] = {{
                    "status": "success",
                    "result": result
                }}
            except Exception as e:
                results[plugin_name] = {{
                    "status": "error",
                    "error": str(e)
                }}
        
        return results
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """プラグイン情報の取得"""
        if plugin_name not in self._plugins:
            return None
        
        plugin = self._plugins[plugin_name]
        info = plugin.get_metadata()
        info["config"] = self._plugin_configs[plugin_name]
        
        return info
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """登録済みプラグイン一覧"""
        return [
            self.get_plugin_info(plugin_name)
            for plugin_name in self._execution_order
        ]
    
    def set_execution_order(self, order: List[str]) -> None:
        """実行順序の設定"""
        # 全プラグインが存在することを確認
        for plugin_name in order:
            if plugin_name not in self._plugins:
                raise ValueError(f"Plugin '{plugin_name}' is not registered")
        
        # 全登録済みプラグインが含まれることを確認
        if set(order) != set(self._execution_order):
            raise ValueError("All registered plugins must be included in the order")
        
        self._execution_order = order
    
    def load_plugins_from_directory(self, plugin_dir: str) -> None:
        """ディレクトリからプラグインを読み込み"""
        plugin_path = Path(plugin_dir)
        
        if not plugin_path.exists():
            raise FileNotFoundError(f"Plugin directory not found: {plugin_dir}")
        
        for py_file in plugin_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            try:
                # モジュール名を作成
                module_name = f"{plugin_path.name}.{py_file.stem}"
                
                # モジュールをインポート
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # プラグインクラスを検索
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, {plugin_interface}) and 
                        obj is not {plugin_interface}):
                        
                        # プラグインインスタンスを作成・登録
                        plugin_instance = obj()
                        self.{register_method}(plugin_instance)
                        
            except Exception as e:
                print(f"Failed to load plugin from {py_file}: {e}")

# 具体的なプラグイン実装例
class {example_plugin}({plugin_interface}):
    """テキスト処理プラグインの例"""
    
    @property
    def name(self) -> str:
        return "text_processor"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "テキスト処理を行うサンプルプラグイン"
    
    def {initialize_method}(self, config: Dict[str, Any]) -> None:
        self.transform_type = config.get("transform", "upper")
        self.prefix = config.get("prefix", "")
        print(f"TextProcessor initialized with transform: {self.transform_type}")
    
    def {execute_method}(self, data: Any, **kwargs: Any) -> Any:
        if not isinstance(data, str):
            raise TypeError("TextProcessor requires string input")
        
        result = data
        
        if self.transform_type == "upper":
            result = result.upper()
        elif self.transform_type == "lower":
            result = result.lower()
        elif self.transform_type == "title":
            result = result.title()
        
        if self.prefix:
            result = self.prefix + result
        
        return result
    
    def {cleanup_method}(self) -> None:
        print("TextProcessor cleanup completed")

# 使用例
def plugin_example() -> None:
    """プラグインパターンの使用例"""
    # プラグインマネージャーの作成
    manager = {plugin_manager}()
    
    # プラグインの登録
    text_plugin = {example_plugin}()
    manager.{register_method}(text_plugin, {{"transform": "upper", "prefix": ">>> "}})
    
    # プラグインの実行
    result = manager.{execute_plugin_method}("text_processor", "hello world")
    print(f"Plugin result: {result}")
    
    # 全プラグインの実行
    results = manager.{execute_all_method}("test data")
    print(f"All plugins results: {results}")
    
    # プラグイン情報の表示
    plugin_info = manager.get_plugin_info("text_processor")
    print(f"Plugin info: {plugin_info}")
    
    # プラグインの登録解除
    manager.{unregister_method}("text_processor")

if __name__ == "__main__":
    plugin_example()
'''
        
        template = PatternTemplate(
            pattern_type=PatternType.PLUGIN,
            name="Plugin Pattern",
            description="実行時に機能を動的に追加・削除可能にするパターン",
            complexity=TemplateComplexity.ADVANCED,
            base_template=base_template,
            customization_points=[
                "plugin_interface", "plugin_manager", "example_plugin",
                "initialize_method", "execute_method", "cleanup_method",
                "register_method", "unregister_method", "execute_plugin_method",
                "execute_all_method"
            ],
            parameters={
                "plugin_interface": "Plugin",
                "plugin_manager": "PluginManager",
                "example_plugin": "TextProcessorPlugin",
                "initialize_method": "initialize",
                "execute_method": "execute",
                "cleanup_method": "cleanup",
                "register_method": "register_plugin",
                "unregister_method": "unregister_plugin",
                "execute_plugin_method": "execute_plugin",
                "execute_all_method": "execute_all_plugins"
            },
            dependencies=["abc", "typing", "importlib", "inspect", "pathlib"]
        )
        
        self.templates["plugin"] = template
    
    def _add_builder_pattern(self) -> None:
        """Builder Pattern テンプレート追加"""
        
        base_template = '''
"""
{description}
Builder Pattern Implementation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
{custom_imports}

class {product_class}:
    """構築される製品"""
    
    def __init__(self) -> None:
        self.parts: Dict[str, Any] = {{}}
        self._is_built = False
    
    def add_part(self, name: str, value: Any) -> None:
        """パーツの追加"""
        if self._is_built:
            raise RuntimeError("Cannot modify built product")
        self.parts[name] = value
    
    def mark_as_built(self) -> None:
        """構築完了マーク"""
        self._is_built = True
    
    def get_info(self) -> Dict[str, Any]:
        """製品情報の取得"""
        return {{
            "parts": self.parts.copy(),
            "is_built": self._is_built,
            "part_count": len(self.parts)
        }}
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.parts})"

class {builder_interface}(ABC):
    """ビルダーインターフェース"""
    
    def __init__(self) -> None:
        self.reset()
    
    @abstractmethod
    def reset(self) -> None:
        """リセット"""
        pass
    
    @abstractmethod
    def {build_part_a_method}(self, value: Any) -> '{builder_interface}':
        """パーツAの構築"""
        pass
    
    @abstractmethod
    def {build_part_b_method}(self, value: Any) -> '{builder_interface}':
        """パーツBの構築"""
        pass
    
    @abstractmethod
    def {get_result_method}(self) -> {product_class}:
        """結果の取得"""
        pass

class {concrete_builder}({builder_interface}):
    """具体的ビルダー"""
    
    def reset(self) -> None:
        self._product = {product_class}()
    
    def {build_part_a_method}(self, value: Any) -> '{concrete_builder}':
        self._product.add_part("part_a", value)
        return self
    
    def {build_part_b_method}(self, value: Any) -> '{concrete_builder}':
        self._product.add_part("part_b", value)
        return self
    
    def {get_result_method}(self) -> {product_class}:
        result = self._product
        result.mark_as_built()
        self.reset()  # 新しい製品用にリセット
        return result

class {director_class}:
    """ディレクター"""
    
    def __init__(self, builder: {builder_interface}) -> None:
        self._builder = builder
    
    @property
    def builder(self) -> {builder_interface}:
        return self._builder
    
    @builder.setter
    def builder(self, builder: {builder_interface}) -> None:
        self._builder = builder
    
    def {construct_minimal_method}(self) -> None:
        """最小構成の構築"""
        self._builder.{build_part_a_method}("minimal_a")
    
    def {construct_full_method}(self) -> None:
        """完全構成の構築"""
        (self._builder
         .{build_part_a_method}("full_a")
         .{build_part_b_method}("full_b"))

# 使用例
def builder_example() -> None:
    """ビルダーパターンの使用例"""
    # ビルダーとディレクターの作成
    builder = {concrete_builder}()
    director = {director_class}(builder)
    
    # 最小構成の製品作成
    director.{construct_minimal_method}()
    minimal_product = builder.{get_result_method}()
    print(f"Minimal product: {minimal_product}")
    print(f"Info: {minimal_product.get_info()}")
    
    # 完全構成の製品作成
    director.{construct_full_method}()
    full_product = builder.{get_result_method}()
    print(f"Full product: {full_product}")
    print(f"Info: {full_product.get_info()}")
    
    # 手動構築
    manual_product = (builder
                     .{build_part_a_method}("custom_a")
                     .{build_part_b_method}("custom_b")
                     .{get_result_method}())
    print(f"Manual product: {manual_product}")

if __name__ == "__main__":
    builder_example()
'''
        
        template = PatternTemplate(
            pattern_type=PatternType.BUILDER,
            name="Builder Pattern", 
            description="複雑なオブジェクトの段階的構築を可能にするパターン",
            complexity=TemplateComplexity.INTERMEDIATE,
            base_template=base_template,
            customization_points=[
                "product_class", "builder_interface", "concrete_builder", "director_class",
                "build_part_a_method", "build_part_b_method", "get_result_method",
                "construct_minimal_method", "construct_full_method"
            ],
            parameters={
                "product_class": "Product",
                "builder_interface": "Builder",
                "concrete_builder": "ConcreteBuilder",
                "director_class": "Director",
                "build_part_a_method": "build_part_a",
                "build_part_b_method": "build_part_b", 
                "get_result_method": "get_result",
                "construct_minimal_method": "construct_minimal",
                "construct_full_method": "construct_full"
            },
            dependencies=["abc", "typing"]
        )
        
        self.templates["builder"] = template
    
    def _add_decorator_pattern(self) -> None:
        """Decorator Pattern テンプレート追加"""
        
        base_template = '''
"""
{description}
Decorator Pattern Implementation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
{custom_imports}

class {component_interface}(ABC):
    """コンポーネントインターフェース"""
    
    @abstractmethod
    def {operation_method}(self) -> str:
        """基本操作"""
        pass
    
    @abstractmethod
    def get_cost(self) -> float:
        """コスト取得"""
        pass

class {concrete_component}({component_interface}):
    """具体的コンポーネント"""
    
    def __init__(self, name: str = "Basic Component") -> None:
        self.name = name
    
    def {operation_method}(self) -> str:
        return f"Operation from {self.name}"
    
    def get_cost(self) -> float:
        return 10.0

class {decorator_base}({component_interface}):
    """デコレータ基底クラス"""
    
    def __init__(self, component: {component_interface}) -> None:
        self._component = component
    
    @property
    def component(self) -> {component_interface}:
        return self._component
    
    def {operation_method}(self) -> str:
        return self._component.{operation_method}()
    
    def get_cost(self) -> float:
        return self._component.get_cost()

class {concrete_decorator_a}({decorator_base}):
    """具体的デコレータA"""
    
    def {operation_method}(self) -> str:
        return f"DecoratorA({self._component.{operation_method}()})"
    
    def get_cost(self) -> float:
        return self._component.get_cost() + 5.0

class {concrete_decorator_b}({decorator_base}):
    """具体的デコレータB"""
    
    def {operation_method}(self) -> str:
        return f"DecoratorB({self._component.{operation_method}()})"
    
    def get_cost(self) -> float:
        return self._component.get_cost() + 3.0

# 使用例
def decorator_example() -> None:
    """デコレータパターンの使用例"""
    # 基本コンポーネント
    simple_component = {concrete_component}("Simple")
    print(f"Simple: {simple_component.{operation_method}()}")
    print(f"Cost: {simple_component.get_cost()}")
    
    # デコレータAで装飾
    decorated_a = {concrete_decorator_a}(simple_component)
    print(f"Decorated A: {decorated_a.{operation_method}()}")
    print(f"Cost: {decorated_a.get_cost()}")
    
    # さらにデコレータBで装飾
    decorated_ab = {concrete_decorator_b}(decorated_a)
    print(f"Decorated A+B: {decorated_ab.{operation_method}()}")
    print(f"Cost: {decorated_ab.get_cost()}")

if __name__ == "__main__":
    decorator_example()
'''
        
        template = PatternTemplate(
            pattern_type=PatternType.DECORATOR,
            name="Decorator Pattern",
            description="オブジェクトに動的に機能を追加するパターン",
            complexity=TemplateComplexity.INTERMEDIATE,
            base_template=base_template,
            customization_points=[
                "component_interface", "concrete_component", "decorator_base",
                "concrete_decorator_a", "concrete_decorator_b", "operation_method"
            ],
            parameters={
                "component_interface": "Component",
                "concrete_component": "ConcreteComponent",
                "decorator_base": "Decorator",
                "concrete_decorator_a": "ConcreteDecoratorA",
                "concrete_decorator_b": "ConcreteDecoratorB",
                "operation_method": "operation"
            },
            dependencies=["abc", "typing"]
        )
        
        self.templates["decorator"] = template
    
    def _prepare_template_variables(self, template: PatternTemplate,
                                  config: CustomizationConfig,
                                  context: Dict[str, Any]) -> Dict[str, str]:
        """テンプレート変数の準備"""
        
        variables = template.parameters.copy()
        
        # カスタマイゼーション設定からの更新
        variables.update(config.class_names)
        variables.update(config.method_names)
        variables.update(config.interface_names)
        
        # コンテキスト情報の追加
        variables["description"] = context.get("description", template.description)
        variables["module_name"] = context.get("module_name", "generated_module")
        variables["custom_imports"] = "\n".join(config.custom_imports)
        
        return variables
    
    def _expand_template(self, template: str, variables: Dict[str, str]) -> str:
        """テンプレートの展開"""
        
        expanded = template
        
        # 変数置換
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            expanded = expanded.replace(placeholder, str(value))
        
        return expanded
    
    def _post_process_code(self, code: str, config: CustomizationConfig) -> str:
        """コードのポストプロセッシング"""
        
        # 不要な空行を削除
        lines = code.split('\n')
        processed_lines = []
        
        prev_empty = False
        for line in lines:
            is_empty = line.strip() == ""
            
            # 連続する空行を1つにまとめる
            if is_empty and prev_empty:
                continue
                
            processed_lines.append(line)
            prev_empty = is_empty
        
        code = '\n'.join(processed_lines)
        
        # 先頭・末尾の不要な空行削除
        code = code.strip()
        
        # カスタムデコレータの追加
        if config.custom_decorators:
            # クラス定義の前にデコレータを追加する処理
            # (実装は複雑になるため、ここでは簡易版)
            pass
        
        return code
    
    def _customize_factory_pattern(self, config: CustomizationConfig,
                                 customizations: Dict[str, Any]) -> None:
        """Factory Pattern固有のカスタマイゼーション"""
        
        if "product_types" in customizations:
            product_types = customizations["product_types"]
            if isinstance(product_types, list) and len(product_types) >= 2:
                config.class_names["concrete_product_a"] = product_types[0]
                if len(product_types) > 1:
                    config.class_names["concrete_product_b"] = product_types[1]
    
    def _customize_strategy_pattern(self, config: CustomizationConfig,
                                  customizations: Dict[str, Any]) -> None:
        """Strategy Pattern固有のカスタマイゼーション"""
        
        if "strategies" in customizations:
            strategies = customizations["strategies"]
            if isinstance(strategies, list) and len(strategies) >= 2:
                config.class_names["concrete_strategy_a"] = strategies[0]
                if len(strategies) > 1:
                    config.class_names["concrete_strategy_b"] = strategies[1]
    
    def _customize_observer_pattern(self, config: CustomizationConfig,
                                  customizations: Dict[str, Any]) -> None:
        """Observer Pattern固有のカスタマイゼーション"""
        
        if "event_types" in customizations:
            event_types = customizations["event_types"]
            if isinstance(event_types, list):
                config.metadata["event_types"] = event_types
    
    def _customize_plugin_pattern(self, config: CustomizationConfig,
                                customizations: Dict[str, Any]) -> None:
        """Plugin Pattern固有のカスタマイゼーション"""
        
        if "plugin_directory" in customizations:
            config.metadata["plugin_directory"] = customizations["plugin_directory"]


def main():
    """テスト実行"""
    
    engine = PatternTemplateEngine()
    
    print("🧪 PatternTemplateEngine テスト実行")
    
    # 利用可能パターン一覧
    patterns = engine.list_available_patterns()
    print(f"📐 利用可能パターン: {len(patterns)}種類")
    for pattern in patterns:
        print(f"  - {pattern['name']} ({pattern['complexity']})")
    
    # Factory Pattern 生成テスト
    config = CustomizationConfig()
    config.class_names["concrete_product_a"] = "DatabaseConnection"
    config.class_names["concrete_product_b"] = "FileConnection"
    config.method_names["operation_method"] = "connect"
    config.custom_imports.append("import logging")
    
    context = {
        "description": "Connection Factory Pattern for Kumihan-Formatter",
        "module_name": "connection_factory"
    }
    
    factory_code = engine.generate_pattern(PatternType.FACTORY, config, context)
    print(f"\n🏭 Factory Pattern生成完了: {len(factory_code)}文字")
    
    # テストコード生成
    test_code = engine.generate_test_code(PatternType.FACTORY, config, context)
    if test_code:
        print(f"🧪 テストコード生成完了: {len(test_code)}文字")
    
    # Strategy Pattern カスタマイゼーションテスト
    custom_strategy = engine.customize_pattern(
        PatternType.STRATEGY,
        {
            "class_names": {
                "context_class": "DataProcessor",
                "concrete_strategy_a": "FastProcessor",
                "concrete_strategy_b": "AccurateProcessor"
            },
            "strategies": ["FastProcessor", "AccurateProcessor"]
        }
    )
    
    strategy_code = engine.generate_pattern(PatternType.STRATEGY, custom_strategy)
    print(f"\n🎯 Strategy Pattern生成完了: {len(strategy_code)}文字")
    
    # パターン情報取得テスト
    plugin_info = engine.get_pattern_info(PatternType.PLUGIN)
    if plugin_info:
        print(f"\n🔌 Plugin Pattern情報:")
        print(f"  名前: {plugin_info['name']}")
        print(f"  複雑度: {plugin_info['complexity']}")
        print(f"  カスタマイゼーションポイント: {len(plugin_info['customization_points'])}個")


if __name__ == "__main__":
    main()