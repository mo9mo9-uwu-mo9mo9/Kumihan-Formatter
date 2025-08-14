#!/usr/bin/env python3
"""
Pattern Implementation Engine - 設計パターン自動実装エンジン
Issue #870: 複雑タスクパターン拡張

デザインパターンの自動検出・実装・適用システム
SOLID原則準拠の高品質コード生成
"""

import ast
import os
import re
import sys
from typing import Dict, List, Any, Set, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import textwrap
import inspect

# ロガー統合
try:
    from kumihan_formatter.core.utilities.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class DesignPattern(Enum):
    """設計パターン種別"""
    FACTORY = "factory"
    ABSTRACT_FACTORY = "abstract_factory"
    BUILDER = "builder"
    PROTOTYPE = "prototype"
    SINGLETON = "singleton"
    ADAPTER = "adapter"
    BRIDGE = "bridge"
    COMPOSITE = "composite"
    DECORATOR = "decorator"
    FACADE = "facade"
    FLYWEIGHT = "flyweight"
    PROXY = "proxy"
    CHAIN_OF_RESPONSIBILITY = "chain_of_responsibility"
    COMMAND = "command"
    INTERPRETER = "interpreter"
    ITERATOR = "iterator"
    MEDIATOR = "mediator"
    MEMENTO = "memento"
    OBSERVER = "observer"
    STATE = "state"
    STRATEGY = "strategy"
    TEMPLATE_METHOD = "template_method"
    VISITOR = "visitor"


class PatternCategory(Enum):
    """パターンカテゴリ"""
    CREATIONAL = "creational"  # 生成パターン
    STRUCTURAL = "structural"  # 構造パターン
    BEHAVIORAL = "behavioral"  # 振る舞いパターン


@dataclass
class PatternRequirement:
    """パターン実装要件"""
    pattern: DesignPattern
    category: PatternCategory
    target_classes: List[str]
    interfaces: List[str]
    methods: List[str]
    properties: List[str]
    solid_principles: List[str]  # 適用するSOLID原則
    complexity_level: int
    estimated_effort: int  # 実装工数（時間）


@dataclass
class PatternImplementation:
    """パターン実装結果"""
    pattern: DesignPattern
    generated_code: str
    file_path: str
    imports: List[str]
    classes: List[str]
    methods: List[str]
    test_code: str
    documentation: str
    solid_compliance: Dict[str, bool]  # SOLID原則準拠状況
    quality_score: float


@dataclass
class RefactoringOpportunity:
    """リファクタリング機会"""
    file_path: str
    line_number: int
    current_pattern: str
    suggested_pattern: DesignPattern
    reason: str
    complexity_reduction: int
    maintainability_gain: float


class PatternTemplate(ABC):
    """パターンテンプレート基底クラス"""

    @abstractmethod
    def generate_code(self, requirements: PatternRequirement) -> str:
        """コード生成"""
        pass

    @abstractmethod
    def generate_tests(self, requirements: PatternRequirement) -> str:
        """テストコード生成"""
        pass

    @abstractmethod
    def get_imports(self) -> List[str]:
        """必要なインポート取得"""
        pass


class FactoryPatternTemplate(PatternTemplate):
    """Factoryパターンテンプレート"""

    def generate_code(self, requirements: PatternRequirement) -> str:
        """Factoryパターンコード生成"""

        template = textwrap.dedent('''
        from abc import ABC, abstractmethod
        from typing import Dict, Any, Type

        class {product_interface}(ABC):
            """製品インターフェース - Interface Segregation Principle準拠"""

            @abstractmethod
            def operation(self) -> str:
                """製品固有の操作"""
                pass

        {concrete_products}

        class {factory_name}:
            """Factory - Open/Closed Principle準拠"""

            _products: Dict[str, Type[{product_interface}]] = {{}}

            @classmethod
            def register_product(cls, name: str, product_class: Type[{product_interface}]) -> None:
                """製品登録 - Dependency Inversion Principle準拠"""
                cls._products[name] = product_class

            @classmethod
            def create_product(cls, product_type: str, **kwargs: Any) -> {product_interface}:
                """製品生成 - Single Responsibility Principle準拠"""
                if product_type not in cls._products:
                    raise ValueError(f"Unknown product type: {{product_type}}")

                product_class = cls._products[product_type]
                return product_class(**kwargs)

            @classmethod
            def get_available_products(cls) -> List[str]:
                """利用可能製品一覧取得"""
                return list(cls._products.keys())

        # 自動登録システム
        def auto_register_products():
            """製品の自動登録 - Liskov Substitution Principle準拠"""
            import inspect
            current_module = sys.modules[__name__]

            for name, obj in inspect.getmembers(current_module):
                if (inspect.isclass(obj) and
                    issubclass(obj, {product_interface}) and
                    obj != {product_interface}):
                    product_name = obj.__name__.replace('Concrete', '').lower()
                    {factory_name}.register_product(product_name, obj)

        # モジュール読み込み時に自動登録実行
        auto_register_products()
        ''').strip()

        # 具象製品クラス生成
        concrete_products = []
        for class_name in requirements.target_classes:
            if class_name != requirements.target_classes[0]:  # インターフェースを除く
                concrete_product = textwrap.dedent(f'''
                class {class_name}({requirements.target_classes[0]}):
                    """具象製品: {class_name}"""

                    def __init__(self, **kwargs: Any):
                        self.config = kwargs

                    def operation(self) -> str:
                        return f"{class_name} operation with {{self.config}}"
                ''').strip()
                concrete_products.append(concrete_product)

        return template.format(
            product_interface=requirements.target_classes[0],
            factory_name=f"{requirements.target_classes[0]}Factory",
            concrete_products='\n\n'.join(concrete_products)
        )

    def generate_tests(self, requirements: PatternRequirement) -> str:
        """Factoryパターンテスト生成"""

        template = textwrap.dedent('''
        import pytest
        from unittest.mock import Mock, patch

        class Test{factory_name}:
            """Factory Pattern Tests - 品質保証"""

            def test_product_creation(self):
                """製品生成テスト"""
                # Given: 有効な製品タイプ
                product_type = "{first_product}"

                # When: 製品を生成
                product = {factory_name}.create_product(product_type)

                # Then: 正しい型のインスタンスが生成される
                assert isinstance(product, {product_interface})
                assert product.operation() is not None

            def test_invalid_product_type(self):
                """無効な製品タイプのエラーハンドリング"""
                # Given: 無効な製品タイプ
                invalid_type = "nonexistent"

                # When & Then: ValueError が発生
                with pytest.raises(ValueError, match="Unknown product type"):
                    {factory_name}.create_product(invalid_type)

            def test_product_registration(self):
                """動的製品登録テスト"""
                # Given: 新しい製品クラス
                class TestProduct({product_interface}):
                    def operation(self) -> str:
                        return "test operation"

                # When: 製品を登録
                {factory_name}.register_product("test", TestProduct)

                # Then: 製品が生成可能
                product = {factory_name}.create_product("test")
                assert isinstance(product, TestProduct)

            def test_available_products_list(self):
                """利用可能製品一覧テスト"""
                # When: 利用可能製品を取得
                products = {factory_name}.get_available_products()

                # Then: リストが返される
                assert isinstance(products, list)
                assert len(products) > 0

            def test_product_with_configuration(self):
                """設定付き製品生成テスト"""
                # Given: 設定パラメータ
                config = {{"param1": "value1", "param2": "value2"}}

                # When: 設定付きで製品生成
                product = {factory_name}.create_product("{first_product}", **config)

                # Then: 設定が適用される
                assert hasattr(product, 'config')
                assert product.config == config
        ''').strip()

        first_product = requirements.target_classes[1] if len(requirements.target_classes) > 1 else "concrete"

        return template.format(
            factory_name=f"{requirements.target_classes[0]}Factory",
            product_interface=requirements.target_classes[0],
            first_product=first_product.replace('Concrete', '').lower()
        )

    def get_imports(self) -> List[str]:
        """必要なインポート"""
        return [
            "from abc import ABC, abstractmethod",
            "from typing import Dict, Any, Type, List",
            "import sys"
        ]


class ObserverPatternTemplate(PatternTemplate):
    """Observerパターンテンプレート"""

    def generate_code(self, requirements: PatternRequirement) -> str:
        """Observerパターンコード生成"""

        template = textwrap.dedent('''
        from abc import ABC, abstractmethod
        from typing import List, Any, Optional
        import weakref

        class Observer(ABC):
            """Observer Interface - Interface Segregation Principle準拠"""

            @abstractmethod
            def update(self, subject: 'Subject', event_data: Any = None) -> None:
                """状態変更通知の受信"""
                pass

        class Subject(ABC):
            """Subject Interface - Single Responsibility Principle準拠"""

            def __init__(self):
                self._observers: List[Observer] = []
                self._state: Any = None

            def attach(self, observer: Observer) -> None:
                """Observer登録 - Open/Closed Principle準拠"""
                if observer not in self._observers:
                    self._observers.append(observer)

            def detach(self, observer: Observer) -> None:
                """Observer解除"""
                if observer in self._observers:
                    self._observers.remove(observer)

            def notify(self, event_data: Any = None) -> None:
                """全Observerへの通知 - Dependency Inversion Principle準拠"""
                for observer in self._observers[:]:  # コピーして安全な反復
                    try:
                        observer.update(self, event_data)
                    except Exception as e:
                        # Observer個別エラーでシステム全体を停止させない
                        self._handle_observer_error(observer, e)

            def _handle_observer_error(self, observer: Observer, error: Exception) -> None:
                """Observer エラーハンドリング"""
                print(f"Observer {{observer}} でエラー発生: {{error}}")
                # エラーのあるObserverを自動除去（オプション）
                # self.detach(observer)

            @property
            def state(self) -> Any:
                """状態取得"""
                return self._state

            @state.setter
            def state(self, value: Any) -> None:
                """状態設定と通知"""
                if self._state != value:
                    old_state = self._state
                    self._state = value
                    self.notify({{'old_state': old_state, 'new_state': value}})

        {concrete_subject}

        {concrete_observers}

        class ObserverManager:
            """Observer管理クラス - 高度な機能提供"""

            def __init__(self):
                self._subject_observers: Dict[Subject, List[Observer]] = {{}}
                self._observer_subscriptions: Dict[Observer, List[Subject]] = {{}}

            def subscribe(self, observer: Observer, subject: Subject) -> None:
                """購読設定"""
                subject.attach(observer)

                if subject not in self._subject_observers:
                    self._subject_observers[subject] = []
                self._subject_observers[subject].append(observer)

                if observer not in self._observer_subscriptions:
                    self._observer_subscriptions[observer] = []
                self._observer_subscriptions[observer].append(subject)

            def unsubscribe(self, observer: Observer, subject: Subject) -> None:
                """購読解除"""
                subject.detach(observer)

                if subject in self._subject_observers:
                    self._subject_observers[subject].remove(observer)

                if observer in self._observer_subscriptions:
                    self._observer_subscriptions[observer].remove(subject)

            def unsubscribe_all(self, observer: Observer) -> None:
                """Observer の全購読解除"""
                if observer in self._observer_subscriptions:
                    for subject in self._observer_subscriptions[observer][:]:
                        self.unsubscribe(observer, subject)

            def get_observer_count(self, subject: Subject) -> int:
                """Subject のObserver数取得"""
                return len(self._subject_observers.get(subject, []))
        ''').strip()

        # 具象Subjectクラス生成
        concrete_subject = textwrap.dedent(f'''
        class {requirements.target_classes[0]}(Subject):
            """具象Subject - Liskov Substitution Principle準拠"""

            def __init__(self, name: str = "DefaultSubject"):
                super().__init__()
                self.name = name
                self._data: Dict[str, Any] = {{}}

            def set_data(self, key: str, value: Any) -> None:
                """データ設定と通知"""
                old_value = self._data.get(key)
                self._data[key] = value

                if old_value != value:
                    self.notify({{
                        'action': 'data_changed',
                        'key': key,
                        'old_value': old_value,
                        'new_value': value
                    }})

            def get_data(self, key: str) -> Any:
                """データ取得"""
                return self._data.get(key)

            def remove_data(self, key: str) -> None:
                """データ削除と通知"""
                if key in self._data:
                    old_value = self._data.pop(key)
                    self.notify({{
                        'action': 'data_removed',
                        'key': key,
                        'old_value': old_value
                    }})
        ''').strip()

        # 具象Observerクラス生成
        concrete_observers = []
        observer_classes = requirements.target_classes[1:] if len(requirements.target_classes) > 1 else ["LoggingObserver", "NotificationObserver"]

        for observer_class in observer_classes:
            concrete_observer = textwrap.dedent(f'''
            class {observer_class}(Observer):
                """具象Observer: {observer_class}"""

                def __init__(self, name: str = "{observer_class}"):
                    self.name = name
                    self.received_updates: List[Dict[str, Any]] = []

                def update(self, subject: Subject, event_data: Any = None) -> None:
                    """更新通知の処理"""
                    update_info = {{
                        'timestamp': __import__('time').time(),
                        'subject': subject.__class__.__name__,
                        'subject_name': getattr(subject, 'name', 'Unknown'),
                        'event_data': event_data,
                        'observer': self.name
                    }}

                    self.received_updates.append(update_info)
                    self._process_update(update_info)

                def _process_update(self, update_info: Dict[str, Any]) -> None:
                    """更新処理の具体実装"""
                    print(f"[{{self.name}}] Update received: {{update_info['event_data']}}")

                def get_update_history(self) -> List[Dict[str, Any]]:
                    """更新履歴取得"""
                    return self.received_updates[:]

                def clear_history(self) -> None:
                    """履歴クリア"""
                    self.received_updates.clear()
            ''').strip()
            concrete_observers.append(concrete_observer)

        return template.format(
            concrete_subject=concrete_subject,
            concrete_observers='\n\n'.join(concrete_observers)
        )

    def generate_tests(self, requirements: PatternRequirement) -> str:
        """Observerパターンテスト生成"""

        template = textwrap.dedent('''
        import pytest
        from unittest.mock import Mock, patch
        import time

        class TestObserverPattern:
            """Observer Pattern Tests - 総合品質保証"""

            def setup_method(self):
                """テストセットアップ"""
                self.subject = {subject_class}("TestSubject")
                self.observer1 = {observer_class}("Observer1")
                self.observer2 = {observer_class}("Observer2")

            def test_observer_attachment(self):
                """Observer登録テスト"""
                # When: Observer を登録
                self.subject.attach(self.observer1)
                self.subject.attach(self.observer2)

                # Then: Observer が登録される
                assert len(self.subject._observers) == 2
                assert self.observer1 in self.subject._observers
                assert self.observer2 in self.subject._observers

            def test_observer_detachment(self):
                """Observer解除テスト"""
                # Given: Observer が登録済み
                self.subject.attach(self.observer1)
                self.subject.attach(self.observer2)

                # When: Observer を解除
                self.subject.detach(self.observer1)

                # Then: 指定したObserver のみ解除される
                assert len(self.subject._observers) == 1
                assert self.observer1 not in self.subject._observers
                assert self.observer2 in self.subject._observers

            def test_notification_delivery(self):
                """通知配信テスト"""
                # Given: Observer が登録済み
                self.subject.attach(self.observer1)
                self.subject.attach(self.observer2)

                # When: 状態変更
                test_data = {{"key": "value", "timestamp": time.time()}}
                self.subject.notify(test_data)

                # Then: 全Observer に通知が届く
                assert len(self.observer1.received_updates) == 1
                assert len(self.observer2.received_updates) == 1
                assert self.observer1.received_updates[0]['event_data'] == test_data
                assert self.observer2.received_updates[0]['event_data'] == test_data

            def test_state_change_notification(self):
                """状態変更自動通知テスト"""
                # Given: Observer が登録済み
                self.subject.attach(self.observer1)

                # When: 状態を変更
                new_state = "new_state_value"
                self.subject.state = new_state

                # Then: 自動通知が発生
                assert len(self.observer1.received_updates) == 1
                event_data = self.observer1.received_updates[0]['event_data']
                assert event_data['new_state'] == new_state

            def test_data_operations(self):
                """データ操作通知テスト"""
                # Given: Observer が登録済み
                self.subject.attach(self.observer1)

                # When: データ設定・削除
                self.subject.set_data("key1", "value1")
                self.subject.set_data("key2", "value2")
                self.subject.remove_data("key1")

                # Then: 各操作で通知が発生
                assert len(self.observer1.received_updates) == 3

                # データ設定通知確認
                set_event1 = self.observer1.received_updates[0]['event_data']
                assert set_event1['action'] == 'data_changed'
                assert set_event1['key'] == 'key1'
                assert set_event1['new_value'] == 'value1'

                # データ削除通知確認
                remove_event = self.observer1.received_updates[2]['event_data']
                assert remove_event['action'] == 'data_removed'
                assert remove_event['key'] == 'key1'

            def test_observer_error_handling(self):
                """Observer エラーハンドリングテスト"""
                # Given: エラーを発生させるObserver
                error_observer = Mock()
                error_observer.update.side_effect = Exception("Observer Error")

                self.subject.attach(self.observer1)
                self.subject.attach(error_observer)

                # When: 通知実行（エラーObserver含む）
                self.subject.notify("test_data")

                # Then: エラーがあっても他Observer は正常動作
                assert len(self.observer1.received_updates) == 1
                assert error_observer.update.called

            def test_observer_manager(self):
                """ObserverManager テスト"""
                # Given: ObserverManager
                manager = ObserverManager()

                # When: 購読設定
                manager.subscribe(self.observer1, self.subject)
                manager.subscribe(self.observer2, self.subject)

                # Then: Observer数確認
                assert manager.get_observer_count(self.subject) == 2

                # When: 通知発生
                self.subject.notify("manager_test")

                # Then: 管理されたObserver に通知が届く
                assert len(self.observer1.received_updates) == 1
                assert len(self.observer2.received_updates) == 1

            def test_observer_unsubscribe_all(self):
                """Observer 全購読解除テスト"""
                # Given: 複数Subject に購読したObserver
                subject2 = {subject_class}("TestSubject2")
                manager = ObserverManager()

                manager.subscribe(self.observer1, self.subject)
                manager.subscribe(self.observer1, subject2)

                # When: 全購読解除
                manager.unsubscribe_all(self.observer1)

                # Then: すべてのSubject から解除される
                assert manager.get_observer_count(self.subject) == 0
                assert manager.get_observer_count(subject2) == 0
        ''').strip()

        return template.format(
            subject_class=requirements.target_classes[0],
            observer_class=requirements.target_classes[1] if len(requirements.target_classes) > 1 else "LoggingObserver"
        )

    def get_imports(self) -> List[str]:
        """必要なインポート"""
        return [
            "from abc import ABC, abstractmethod",
            "from typing import List, Any, Optional, Dict",
            "import weakref",
            "import time"
        ]


class DecoratorPatternTemplate(PatternTemplate):
    """Decoratorパターンテンプレート"""

    def generate_code(self, requirements: PatternRequirement) -> str:
        """Decoratorパターンコード生成"""

        template = textwrap.dedent('''
        from abc import ABC, abstractmethod
        from typing import Any, List, Dict
        import functools

        class Component(ABC):
            """Component Interface - Interface Segregation Principle準拠"""

            @abstractmethod
            def operation(self) -> str:
                """コンポーネント操作"""
                pass

            def get_description(self) -> str:
                """説明取得"""
                return self.__class__.__name__

        {concrete_component}

        class Decorator(Component):
            """Decorator Base Class - Single Responsibility Principle準拠"""

            def __init__(self, component: Component):
                self._component = component

            def operation(self) -> str:
                """デコレートされた操作"""
                return self._component.operation()

            def get_description(self) -> str:
                """デコレートされた説明"""
                return self._component.get_description()

        {concrete_decorators}

        class DecoratorChain:
            """Decorator Chain Manager - Open/Closed Principle準拠"""

            def __init__(self, base_component: Component):
                self._component = base_component
                self._decorators: List[type] = []

            def add_decorator(self, decorator_class: type, **kwargs: Any) -> 'DecoratorChain':
                """デコレーター追加 - Dependency Inversion Principle準拠"""
                self._component = decorator_class(self._component, **kwargs)
                self._decorators.append(decorator_class)
                return self

            def get_component(self) -> Component:
                """最終コンポーネント取得"""
                return self._component

            def get_chain_info(self) -> Dict[str, Any]:
                """チェーン情報取得"""
                return {{
                    'base_component': self._component.__class__.__name__,
                    'decorators_applied': len(self._decorators),
                    'decorator_chain': [d.__name__ for d in self._decorators],
                    'final_description': self._component.get_description()
                }}

        # 関数デコレーター版（併用提供）
        def performance_decorator(func):
            """性能測定デコレーター"""
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                import time
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                print(f"Function {{func.__name__}} took {{end_time - start_time:.4f}} seconds")
                return result
            return wrapper

        def logging_decorator(prefix: str = "LOG"):
            """ログ出力デコレーター"""
            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    print(f"[{{prefix}}] Calling {{func.__name__}} with args={{args}}, kwargs={{kwargs}}")
                    result = func(*args, **kwargs)
                    print(f"[{{prefix}}] {{func.__name__}} returned: {{result}}")
                    return result
                return wrapper
            return decorator

        def cache_decorator(maxsize: int = 128):
            """キャッシュデコレーター"""
            def decorator(func):
                cache = {{}}

                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    # 簡易キーの生成
                    try:
                        key = str(args) + str(sorted(kwargs.items()))
                        if key in cache:
                            return cache[key]

                        result = func(*args, **kwargs)

                        if len(cache) >= maxsize:
                            # 最古のエントリを削除
                            oldest_key = next(iter(cache))
                            del cache[oldest_key]

                        cache[key] = result
                        return result
                    except (TypeError, ValueError):
                        # unhashableな引数の場合は通常実行
                        return func(*args, **kwargs)

                wrapper.cache_info = lambda: {{'size': len(cache), 'maxsize': maxsize}}
                wrapper.cache_clear = lambda: cache.clear()
                return wrapper
            return decorator
        ''').strip()

        # 具象コンポーネント生成
        component_class = requirements.target_classes[0] if requirements.target_classes else "ConcreteComponent"
        concrete_component = textwrap.dedent(f'''
        class {component_class}(Component):
            """具象コンポーネント - Liskov Substitution Principle準拠"""

            def __init__(self, data: str = "base"):
                self.data = data

            def operation(self) -> str:
                return f"{{self.__class__.__name__}}({{self.data}})"

            def get_description(self) -> str:
                return f"{{self.__class__.__name__}} with data: {{self.data}}"
        ''').strip()

        # 具象デコレーター群生成
        decorator_classes = requirements.target_classes[1:] if len(requirements.target_classes) > 1 else ["BorderDecorator", "ColorDecorator", "SizeDecorator"]
        concrete_decorators = []

        for decorator_class in decorator_classes:
            concrete_decorator = textwrap.dedent(f'''
            class {decorator_class}(Decorator):
                """具象デコレーター: {decorator_class}"""

                def __init__(self, component: Component, style: str = "default"):
                    super().__init__(component)
                    self.style = style

                def operation(self) -> str:
                    base_operation = super().operation()
                    decoration = self._apply_decoration(base_operation)
                    return decoration

                def _apply_decoration(self, base: str) -> str:
                    """装飾の適用"""
                    decorator_name = self.__class__.__name__.replace('Decorator', '').lower()
                    return f"{{decorator_name}}[{{self.style}}]({{base}})"

                def get_description(self) -> str:
                    base_desc = super().get_description()
                    return f"{{base_desc}} + {{self.__class__.__name__}}({{self.style}})"
            ''').strip()
            concrete_decorators.append(concrete_decorator)

        return template.format(
            concrete_component=concrete_component,
            concrete_decorators='\n\n'.join(concrete_decorators)
        )

    def generate_tests(self, requirements: PatternRequirement) -> str:
        """Decoratorパターンテスト生成"""

        template = textwrap.dedent('''
        import pytest
        from unittest.mock import Mock, patch

        class TestDecoratorPattern:
            """Decorator Pattern Tests - 総合品質保証"""

            def setup_method(self):
                """テストセットアップ"""
                self.base_component = {component_class}("test_data")
                self.decorator_class = {first_decorator}

            def test_basic_decoration(self):
                """基本装飾テスト"""
                # When: デコレーターを適用
                decorated = self.decorator_class(self.base_component, "basic_style")

                # Then: 装飾された結果が返される
                result = decorated.operation()
                assert self.base_component.operation() in result
                assert "basic_style" in result
                assert decorated.get_description() != self.base_component.get_description()

            def test_multiple_decorations(self):
                """多重装飾テスト"""
                # Given: 複数のデコレーター
                decorated1 = {first_decorator}(self.base_component, "style1")
                decorated2 = {second_decorator}(decorated1, "style2")

                # When: 操作実行
                result = decorated2.operation()

                # Then: 全装飾が適用される
                assert "style1" in result
                assert "style2" in result
                assert self.base_component.operation() in result

            def test_decorator_chain(self):
                """デコレーターチェーンテスト"""
                # Given: デコレーターチェーン
                chain = DecoratorChain(self.base_component)

                # When: 複数デコレーター追加
                final_component = (chain
                                 .add_decorator({first_decorator}, style="chain1")
                                 .add_decorator({second_decorator}, style="chain2")
                                 .get_component())

                # Then: チェーンが正しく構築される
                result = final_component.operation()
                assert "chain1" in result
                assert "chain2" in result

                # チェーン情報確認
                chain_info = chain.get_chain_info()
                assert chain_info['decorators_applied'] == 2
                assert len(chain_info['decorator_chain']) == 2

            def test_component_interface_preservation(self):
                """インターフェース保持テスト"""
                # Given: 装飾されたコンポーネント
                decorated = self.decorator_class(self.base_component)

                # Then: Componentインターフェースを維持
                assert isinstance(decorated, Component)
                assert hasattr(decorated, 'operation')
                assert hasattr(decorated, 'get_description')
                assert callable(decorated.operation)
                assert callable(decorated.get_description)

            def test_decorator_independence(self):
                """デコレーター独立性テスト"""
                # Given: 同じベースに異なるデコレーター
                decorated1 = {first_decorator}(self.base_component, "independent1")
                decorated2 = {second_decorator}(self.base_component, "independent2")

                # When: それぞれ操作実行
                result1 = decorated1.operation()
                result2 = decorated2.operation()

                # Then: 互いに影響しない
                assert "independent1" in result1
                assert "independent1" not in result2
                assert "independent2" in result2
                assert "independent2" not in result1

            def test_function_decorators(self):
                """関数デコレーターテスト"""
                # Given: テスト関数
                @performance_decorator
                @logging_decorator("TEST")
                @cache_decorator(maxsize=10)
                def test_function(x, y):
                    return x + y

                # When: 関数実行
                result1 = test_function(1, 2)
                result2 = test_function(1, 2)  # キャッシュヒット

                # Then: 正しい結果とデコレーター効果
                assert result1 == 3
                assert result2 == 3

                # キャッシュ情報確認
                cache_info = test_function.cache_info()
                assert cache_info['size'] >= 1
                assert cache_info['maxsize'] == 10

            def test_cache_decorator_functionality(self):
                """キャッシュデコレーター機能テスト"""
                call_count = 0

                @cache_decorator(maxsize=2)
                def expensive_function(n):
                    nonlocal call_count
                    call_count += 1
                    return n * n

                # When: 同じ引数で複数回呼び出し
                result1 = expensive_function(5)
                result2 = expensive_function(5)
                result3 = expensive_function(3)
                result4 = expensive_function(5)  # キャッシュヒット

                # Then: キャッシュが機能
                assert result1 == 25
                assert result2 == 25
                assert result3 == 9
                assert result4 == 25
                assert call_count == 2  # 5と3の2回のみ実行

            def test_decorator_error_handling(self):
                """デコレーターエラーハンドリングテスト"""
                # Given: エラーを発生させるコンポーネント
                error_component = Mock(spec=Component)
                error_component.operation.side_effect = Exception("Component Error")

                decorated = self.decorator_class(error_component)

                # When & Then: エラーが適切に伝播
                with pytest.raises(Exception, match="Component Error"):
                    decorated.operation()
        ''').strip()

        component_class = requirements.target_classes[0] if requirements.target_classes else "ConcreteComponent"
        decorators = requirements.target_classes[1:] if len(requirements.target_classes) > 1 else ["BorderDecorator", "ColorDecorator"]
        first_decorator = decorators[0] if decorators else "BorderDecorator"
        second_decorator = decorators[1] if len(decorators) > 1 else "ColorDecorator"

        return template.format(
            component_class=component_class,
            first_decorator=first_decorator,
            second_decorator=second_decorator
        )

    def get_imports(self) -> List[str]:
        """必要なインポート"""
        return [
            "from abc import ABC, abstractmethod",
            "from typing import Any, List, Dict",
            "import functools",
            "import time"
        ]


class SingletonPatternTemplate(PatternTemplate):
    """Singletonパターンテンプレート"""

    def generate_code(self, requirements: PatternRequirement) -> str:
        """Singletonパターンコード生成"""

        template = textwrap.dedent('''
        import threading
        from typing import Any, Dict, Optional, Type, TypeVar
        import weakref

        T = TypeVar('T', bound='Singleton')

        class SingletonMeta(type):
            """Singleton メタクラス - Thread-Safe実装"""

            _instances: Dict[Type, Any] = {{}}
            _lock = threading.Lock()

            def __call__(cls, *args, **kwargs):
                with cls._lock:
                    if cls not in cls._instances:
                        instance = super().__call__(*args, **kwargs)
                        cls._instances[cls] = instance
                    return cls._instances[cls]

            @classmethod
            def clear_instances(mcs):
                """全インスタンスクリア（テスト用）"""
                with mcs._lock:
                    mcs._instances.clear()

        class Singleton(metaclass=SingletonMeta):
            """Singleton基底クラス - Single Responsibility Principle準拠"""

            def __init__(self):
                if hasattr(self, '_initialized'):
                    return
                self._initialized = True
                self._setup()

            def _setup(self):
                """初期化処理（サブクラスでオーバーライド）"""
                pass

            @classmethod
            def get_instance(cls: Type[T]) -> T:
                """インスタンス取得"""
                return cls()

            @classmethod
            def is_singleton(cls) -> bool:
                """Singletonかどうかの確認"""
                return True

        {concrete_singletons}

        class SingletonRegistry:
            """Singleton レジストリ - Dependency Inversion Principle準拠"""

            _registry: Dict[str, Type[Singleton]] = {{}}
            _lock = threading.Lock()

            @classmethod
            def register(cls, name: str, singleton_class: Type[Singleton]) -> None:
                """Singleton クラス登録"""
                with cls._lock:
                    if not issubclass(singleton_class, Singleton):
                        raise ValueError(f"{{singleton_class}} must inherit from Singleton")
                    cls._registry[name] = singleton_class

            @classmethod
            def get(cls, name: str) -> Optional[Singleton]:
                """登録されたSingleton取得"""
                with cls._lock:
                    singleton_class = cls._registry.get(name)
                    if singleton_class:
                        return singleton_class.get_instance()
                    return None

            @classmethod
            def list_registered(cls) -> List[str]:
                """登録済みSingleton一覧"""
                with cls._lock:
                    return list(cls._registry.keys())

            @classmethod
            def unregister(cls, name: str) -> bool:
                """Singleton登録解除"""
                with cls._lock:
                    if name in cls._registry:
                        del cls._registry[name]
                        return True
                    return False

        class SingletonDecorator:
            """Singleton デコレーター版 - Open/Closed Principle準拠"""

            def __init__(self, cls):
                self._cls = cls
                self._instance = None
                self._lock = threading.Lock()

            def __call__(self, *args, **kwargs):
                if self._instance is None:
                    with self._lock:
                        if self._instance is None:
                            self._instance = self._cls(*args, **kwargs)
                return self._instance

            def __getattr__(self, name):
                return getattr(self._cls, name)

        def singleton_decorator(cls):
            """Singleton デコレーター関数"""
            return SingletonDecorator(cls)

        # 使用例とテンプレート
        class SingletonValidator:
            """Singleton検証ユーティリティ"""

            @staticmethod
            def validate_singleton(cls: Type) -> Dict[str, Any]:
                """Singleton実装の検証"""
                validation_result = {{
                    'is_singleton': False,
                    'thread_safe': False,
                    'properly_implemented': False,
                    'issues': []
                }}

                # メタクラス確認
                if isinstance(cls, SingletonMeta):
                    validation_result['is_singleton'] = True
                    validation_result['thread_safe'] = True
                elif hasattr(cls, '__call__') and isinstance(cls, SingletonDecorator):
                    validation_result['is_singleton'] = True
                    validation_result['thread_safe'] = True
                else:
                    validation_result['issues'].append("Not using SingletonMeta or SingletonDecorator")

                # インスタンス一意性テスト
                try:
                    instance1 = cls()
                    instance2 = cls()
                    if instance1 is instance2:
                        validation_result['properly_implemented'] = True
                    else:
                        validation_result['issues'].append("Multiple instances created")
                except Exception as e:
                    validation_result['issues'].append(f"Instantiation error: {{e}}")

                return validation_result
        ''').strip()

        # 具象Singletonクラス生成
        singleton_classes = requirements.target_classes if requirements.target_classes else ["ConfigManager", "DatabaseConnection", "Logger"]
        concrete_singletons = []

        for singleton_class in singleton_classes:
            concrete_singleton = textwrap.dedent(f'''
            class {singleton_class}(Singleton):
                """具象Singleton: {singleton_class}"""

                def _setup(self):
                    """初期化処理"""
                    self.config = {{}}
                    self.status = "initialized"
                    self.created_at = __import__('time').time()
                    print(f"{{self.__class__.__name__}} Singleton インスタンス作成")

                def get_config(self, key: str, default: Any = None) -> Any:
                    """設定値取得"""
                    return self.config.get(key, default)

                def set_config(self, key: str, value: Any) -> None:
                    """設定値設定"""
                    self.config[key] = value

                def get_status(self) -> str:
                    """ステータス取得"""
                    return self.status

                def reset(self) -> None:
                    """リセット（テスト用）"""
                    self.config.clear()
                    self.status = "reset"

            # レジストリに自動登録
            SingletonRegistry.register("{singleton_class.lower()}", {singleton_class})
            ''').strip()
            concrete_singletons.append(concrete_singleton)

        # デコレーター版の例も追加
        decorator_example = textwrap.dedent('''

        # デコレーター版の使用例
        @singleton_decorator
        class DecoratedSingleton:
            """デコレーター版Singleton例"""

            def __init__(self):
                self.data = "decorated_singleton_data"
                self.calls = 0

            def increment(self) -> int:
                self.calls += 1
                return self.calls
        ''').strip()

        return template.format(
            concrete_singletons='\n\n'.join(concrete_singletons)
        ) + decorator_example

    def generate_tests(self, requirements: PatternRequirement) -> str:
        """Singletonパターンテスト生成"""

        template = textwrap.dedent('''
        import pytest
        import threading
        import time
        from unittest.mock import patch

        class TestSingletonPattern:
            """Singleton Pattern Tests - 総合品質保証"""

            def setup_method(self):
                """テストセットアップ"""
                # インスタンスクリア
                SingletonMeta.clear_instances()
                self.singleton_class = {first_singleton}

            def teardown_method(self):
                """テストクリーンアップ"""
                SingletonMeta.clear_instances()

            def test_singleton_instance_uniqueness(self):
                """Singleton インスタンス一意性テスト"""
                # When: 複数回インスタンス生成
                instance1 = self.singleton_class()
                instance2 = self.singleton_class()
                instance3 = self.singleton_class.get_instance()

                # Then: 全て同一インスタンス
                assert instance1 is instance2
                assert instance2 is instance3
                assert id(instance1) == id(instance2) == id(instance3)

            def test_singleton_thread_safety(self):
                """Singleton スレッドセーフテスト"""
                instances = []

                def create_instance():
                    instance = self.singleton_class()
                    instances.append(instance)

                # When: 複数スレッドで同時生成
                threads = []
                for _ in range(10):
                    thread = threading.Thread(target=create_instance)
                    threads.append(thread)
                    thread.start()

                for thread in threads:
                    thread.join()

                # Then: 全て同一インスタンス
                assert len(instances) == 10
                first_instance = instances[0]
                for instance in instances:
                    assert instance is first_instance

            def test_singleton_initialization_once(self):
                """Singleton 初期化一度のみテスト"""
                # Given: 初期化カウンターをモック
                with patch.object(self.singleton_class, '_setup') as mock_setup:
                    # When: 複数回インスタンス作成
                    instance1 = self.singleton_class()
                    instance2 = self.singleton_class()
                    instance3 = self.singleton_class()

                    # Then: セットアップは一度のみ
                    assert mock_setup.call_count == 1
                    assert instance1 is instance2 is instance3

            def test_singleton_state_persistence(self):
                """Singleton 状態永続性テスト"""
                # Given: 最初のインスタンスで状態設定
                instance1 = self.singleton_class()
                instance1.set_config("test_key", "test_value")

                # When: 新しいインスタンス取得
                instance2 = self.singleton_class()

                # Then: 状態が保持される
                assert instance2.get_config("test_key") == "test_value"
                assert instance1 is instance2

            def test_singleton_registry(self):
                """Singleton レジストリテスト"""
                # When: レジストリから取得
                instance1 = SingletonRegistry.get("{first_singleton_lower}")
                instance2 = SingletonRegistry.get("{first_singleton_lower}")

                # Then: 同一インスタンスが返される
                assert instance1 is not None
                assert instance1 is instance2
                assert isinstance(instance1, {first_singleton})

            def test_singleton_registry_management(self):
                """Singleton レジストリ管理テスト"""
                # Given: カスタムSingleton
                class TestSingleton(Singleton):
                    pass

                # When: 登録・取得・削除
                SingletonRegistry.register("test", TestSingleton)
                registered = SingletonRegistry.list_registered()
                instance = SingletonRegistry.get("test")
                unregistered = SingletonRegistry.unregister("test")

                # Then: 正しく管理される
                assert "test" in registered
                assert isinstance(instance, TestSingleton)
                assert unregistered is True
                assert "test" not in SingletonRegistry.list_registered()

            def test_decorator_singleton(self):
                """デコレーター版Singleton テスト"""
                # When: デコレーター版使用
                instance1 = DecoratedSingleton()
                instance2 = DecoratedSingleton()

                # Then: Singleton動作
                assert instance1 is instance2
                assert instance1.data == "decorated_singleton_data"

                # 状態共有確認
                count1 = instance1.increment()
                count2 = instance2.increment()
                assert count1 == 1
                assert count2 == 2

            def test_singleton_validation(self):
                """Singleton 検証テスト"""
                # When: 検証実行
                validation_result = SingletonValidator.validate_singleton(self.singleton_class)

                # Then: 正しく実装されている
                assert validation_result['is_singleton'] is True
                assert validation_result['thread_safe'] is True
                assert validation_result['properly_implemented'] is True
                assert len(validation_result['issues']) == 0

            def test_singleton_inheritance(self):
                """Singleton 継承テスト"""
                # Given: Singletonを継承したクラス
                class ChildSingleton({first_singleton}):
                    def _setup(self):
                        super()._setup()
                        self.child_data = "child_specific"

                # When: インスタンス生成
                instance1 = ChildSingleton()
                instance2 = ChildSingleton()

                # Then: 子クラスでもSingleton動作
                assert instance1 is instance2
                assert hasattr(instance1, 'child_data')
                assert instance1.child_data == "child_specific"

            def test_singleton_performance(self):
                """Singleton 性能テスト"""
                # When: 大量インスタンス生成
                start_time = time.time()
                instances = [self.singleton_class() for _ in range(1000)]
                end_time = time.time()

                # Then: 高速実行とインスタンス一意性
                execution_time = end_time - start_time
                assert execution_time < 1.0  # 1秒以内

                first_instance = instances[0]
                for instance in instances:
                    assert instance is first_instance
        ''').strip()

        first_singleton = requirements.target_classes[0] if requirements.target_classes else "ConfigManager"
        first_singleton_lower = first_singleton.lower()

        return template.format(
            first_singleton=first_singleton,
            first_singleton_lower=first_singleton_lower
        )

    def get_imports(self) -> List[str]:
        """必要なインポート"""
        return [
            "import threading",
            "from typing import Any, Dict, Optional, Type, TypeVar, List",
            "import weakref",
            "import time"
        ]


class StrategyPatternTemplate(PatternTemplate):
    """Strategyパターンテンプレート"""

    def generate_code(self, requirements: PatternRequirement) -> str:
        """Strategyパターンコード生成"""

        template = textwrap.dedent('''
        from abc import ABC, abstractmethod
        from typing import Any, Dict, Type, Optional

        class Strategy(ABC):
            """Strategy Interface - Interface Segregation Principle準拠"""

            @abstractmethod
            def execute(self, data: Any) -> Any:
                """戦略実行"""
                pass

            def get_name(self) -> str:
                """戦略名取得"""
                return self.__class__.__name__

            def get_description(self) -> str:
                """戦略説明取得"""
                return self.__doc__ or f"{{self.get_name()}} strategy"

        {concrete_strategies}

        class Context:
            """Context - Single Responsibility Principle準拠"""

            def __init__(self, strategy: Optional[Strategy] = None):
                self._strategy = strategy
                self._available_strategies: Dict[str, Type[Strategy]] = {{}}
                self._execution_history: List[Dict[str, Any]] = []

                # 利用可能戦略の自動登録
                self._auto_register_strategies()

            def set_strategy(self, strategy: Strategy) -> None:
                """戦略設定 - Open/Closed Principle準拠"""
                if not isinstance(strategy, Strategy):
                    raise TypeError("Strategy インターフェースを実装した戦略を指定してください")
                self._strategy = strategy

            def execute_strategy(self, data: Any) -> Any:
                """戦略実行 - Dependency Inversion Principle準拠"""
                if self._strategy is None:
                    raise ValueError("戦略が設定されていません")

                # 実行履歴記録
                execution_info = {{
                    'strategy': self._strategy.get_name(),
                    'timestamp': __import__('time').time(),
                    'input_type': type(data).__name__
                }}

                try:
                    result = self._strategy.execute(data)
                    execution_info['status'] = 'success'
                    execution_info['result_type'] = type(result).__name__
                    return result
                except Exception as e:
                    execution_info['status'] = 'error'
                    execution_info['error'] = str(e)
                    raise
                finally:
                    self._execution_history.append(execution_info)

            def get_strategy(self) -> Optional[Strategy]:
                """現在の戦略取得"""
                return self._strategy

            def list_available_strategies(self) -> List[str]:
                """利用可能戦略一覧"""
                return list(self._available_strategies.keys())

            def create_strategy(self, strategy_name: str) -> Strategy:
                """戦略インスタンス生成"""
                if strategy_name not in self._available_strategies:
                    raise ValueError(f"戦略 '{{strategy_name}}' が見つかりません")

                strategy_class = self._available_strategies[strategy_name]
                return strategy_class()

            def switch_to_strategy(self, strategy_name: str, data: Any = None) -> Any:
                """戦略切り替えと実行"""
                strategy = self.create_strategy(strategy_name)
                self.set_strategy(strategy)

                if data is not None:
                    return self.execute_strategy(data)

            def get_execution_history(self) -> List[Dict[str, Any]]:
                """実行履歴取得"""
                return self._execution_history[:]

            def _auto_register_strategies(self) -> None:
                """戦略の自動登録 - Liskov Substitution Principle準拠"""
                import inspect
                current_module = sys.modules[__name__]

                for name, obj in inspect.getmembers(current_module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, Strategy) and
                        obj != Strategy):
                        strategy_name = obj.__name__.replace('Strategy', '').lower()
                        self._available_strategies[strategy_name] = obj

        class StrategyFactory:
            """Strategy Factory - Factory Pattern併用"""

            @staticmethod
            def create_context_with_strategy(strategy_name: str) -> Context:
                """戦略付きContext生成"""
                context = Context()
                strategy = context.create_strategy(strategy_name)
                context.set_strategy(strategy)
                return context

            @staticmethod
            def create_default_context() -> Context:
                """デフォルト戦略付きContext生成"""
                context = Context()
                available = context.list_available_strategies()
                if available:
                    default_strategy = context.create_strategy(available[0])
                    context.set_strategy(default_strategy)
                return context
        ''').strip()

        # 具象戦略クラス生成
        concrete_strategies = []
        strategy_classes = requirements.target_classes if requirements.target_classes else ["SortStrategy", "SearchStrategy", "CompressionStrategy"]

        for strategy_class in strategy_classes:
            concrete_strategy = textwrap.dedent(f'''
            class {strategy_class}(Strategy):
                """具象戦略: {strategy_class}"""

                def execute(self, data: Any) -> Any:
                    """{{strategy_class}} の実行"""
                    # 実際の戦略ロジックをここに実装
                    return self._process_data(data)

                def _process_data(self, data: Any) -> Any:
                    """データ処理の具体実装"""
                    # {strategy_class} 固有の処理
                    processed = f"{{self.get_name()}} processed: {{data}}"
                    return processed

                def get_description(self) -> str:
                    """戦略説明"""
                    return f"{{self.get_name()}} - 高性能な{{self.__class__.__name__[:-8].lower()}}処理"
            ''').strip()
            concrete_strategies.append(concrete_strategy)

        return template.format(
            concrete_strategies='\n\n'.join(concrete_strategies)
        )

    def generate_tests(self, requirements: PatternRequirement) -> str:
        """Strategyパターンテスト生成"""

        template = textwrap.dedent('''
        import pytest
        from unittest.mock import Mock, patch
        import time

        class TestStrategyPattern:
            """Strategy Pattern Tests - 総合品質保証"""

            def setup_method(self):
                """テストセットアップ"""
                self.context = Context()
                self.test_data = "test_input_data"

            def test_strategy_setting(self):
                """戦略設定テスト"""
                # Given: 戦略インスタンス
                strategy = {first_strategy}()

                # When: 戦略設定
                self.context.set_strategy(strategy)

                # Then: 戦略が設定される
                assert self.context.get_strategy() is strategy
                assert self.context.get_strategy().get_name() == "{first_strategy}"

            def test_strategy_execution(self):
                """戦略実行テスト"""
                # Given: 戦略が設定済み
                strategy = {first_strategy}()
                self.context.set_strategy(strategy)

                # When: 戦略実行
                result = self.context.execute_strategy(self.test_data)

                # Then: 正しい結果が返される
                assert result is not None
                assert str(self.test_data) in str(result)

            def test_strategy_switching(self):
                """戦略切り替えテスト"""
                # Given: 初期戦略
                strategy1 = {first_strategy}()
                self.context.set_strategy(strategy1)

                # When: 戦略切り替え
                available = self.context.list_available_strategies()
                if len(available) > 1:
                    result = self.context.switch_to_strategy(available[1], self.test_data)

                    # Then: 戦略が切り替わり実行される
                    assert self.context.get_strategy().get_name() != "{first_strategy}"
                    assert result is not None

            def test_available_strategies_list(self):
                """利用可能戦略一覧テスト"""
                # When: 利用可能戦略取得
                strategies = self.context.list_available_strategies()

                # Then: 戦略リストが返される
                assert isinstance(strategies, list)
                assert len(strategies) > 0
                assert all(isinstance(name, str) for name in strategies)

            def test_strategy_creation(self):
                """戦略生成テスト"""
                # Given: 利用可能戦略名
                available = self.context.list_available_strategies()
                strategy_name = available[0]

                # When: 戦略生成
                strategy = self.context.create_strategy(strategy_name)

                # Then: 正しい戦略インスタンスが生成される
                assert isinstance(strategy, Strategy)
                assert strategy.get_name() is not None

            def test_invalid_strategy_creation(self):
                """無効戦略生成エラーテスト"""
                # Given: 無効な戦略名
                invalid_name = "nonexistent_strategy"

                # When & Then: ValueError が発生
                with pytest.raises(ValueError, match="戦略.*が見つかりません"):
                    self.context.create_strategy(invalid_name)

            def test_execution_without_strategy(self):
                """戦略未設定実行エラーテスト"""
                # Given: 戦略が設定されていないContext
                empty_context = Context()

                # When & Then: ValueError が発生
                with pytest.raises(ValueError, match="戦略が設定されていません"):
                    empty_context.execute_strategy(self.test_data)

            def test_execution_history(self):
                """実行履歴テスト"""
                # Given: 戦略設定
                strategy = {first_strategy}()
                self.context.set_strategy(strategy)

                # When: 複数回実行
                self.context.execute_strategy("data1")
                self.context.execute_strategy("data2")

                # Then: 実行履歴が記録される
                history = self.context.get_execution_history()
                assert len(history) == 2

                for record in history:
                    assert 'strategy' in record
                    assert 'timestamp' in record
                    assert 'input_type' in record
                    assert 'status' in record
                    assert record['status'] == 'success'

            def test_strategy_error_handling(self):
                """戦略エラーハンドリングテスト"""
                # Given: エラーを発生させる戦略
                error_strategy = Mock(spec=Strategy)
                error_strategy.execute.side_effect = Exception("Strategy Error")
                error_strategy.get_name.return_value = "ErrorStrategy"

                self.context.set_strategy(error_strategy)

                # When & Then: 例外が発生し、履歴に記録される
                with pytest.raises(Exception, match="Strategy Error"):
                    self.context.execute_strategy(self.test_data)

                # エラーも履歴に記録される
                history = self.context.get_execution_history()
                assert len(history) == 1
                assert history[0]['status'] == 'error'
                assert 'error' in history[0]

            def test_strategy_factory(self):
                """StrategyFactory テスト"""
                # When: Factory経由でContext生成
                available = Context().list_available_strategies()
                if available:
                    context = StrategyFactory.create_context_with_strategy(available[0])

                    # Then: 戦略付きContextが生成される
                    assert context.get_strategy() is not None

                    # 実行可能確認
                    result = context.execute_strategy(self.test_data)
                    assert result is not None

            def test_default_context_creation(self):
                """デフォルトContext生成テスト"""
                # When: デフォルトContext生成
                context = StrategyFactory.create_default_context()

                # Then: デフォルト戦略が設定される
                if context.list_available_strategies():
                    assert context.get_strategy() is not None

                    # 実行可能確認
                    result = context.execute_strategy(self.test_data)
                    assert result is not None
        ''').strip()

        first_strategy = requirements.target_classes[0] if requirements.target_classes else "SortStrategy"

        return template.format(
            first_strategy=first_strategy
        )

    def get_imports(self) -> List[str]:
        """必要なインポート"""
        return [
            "from abc import ABC, abstractmethod",
            "from typing import Any, Dict, Type, Optional, List",
            "import sys",
            "import time"
        ]


class PatternImplementationEngine:
    """パターン実装エンジン - メインクラス"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.pattern_templates = self._initialize_pattern_templates()
        self.implementation_history: List[PatternImplementation] = []

        logger.info("🎨 Pattern Implementation Engine 初期化完了")
        logger.info(f"📁 プロジェクトルート: {self.project_root}")
        logger.info(f"🔧 利用可能パターン: {len(self.pattern_templates)}種類")

    def _initialize_pattern_templates(self) -> Dict[DesignPattern, PatternTemplate]:
        """パターンテンプレート初期化"""
        return {
            DesignPattern.FACTORY: FactoryPatternTemplate(),
            DesignPattern.OBSERVER: ObserverPatternTemplate(),
            DesignPattern.STRATEGY: StrategyPatternTemplate(),
            DesignPattern.DECORATOR: DecoratorPatternTemplate(),
            DesignPattern.SINGLETON: SingletonPatternTemplate(),
            # 他のパターンは将来追加
        }

    def analyze_code_for_patterns(self, file_path: str) -> List[RefactoringOpportunity]:
        """コード解析によるパターン適用機会検出"""

        logger.info(f"🔍 パターン適用機会解析: {file_path}")

        opportunities = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)

            # 各種パターン適用機会を検出
            opportunities.extend(self._detect_factory_opportunities(tree, file_path))
            opportunities.extend(self._detect_observer_opportunities(tree, file_path))
            opportunities.extend(self._detect_strategy_opportunities(tree, file_path))

            logger.info(f"✅ 解析完了: {len(opportunities)}件の改善機会を検出")

        except Exception as e:
            logger.error(f"コード解析エラー {file_path}: {e}")

        return opportunities

    def implement_pattern(
        self,
        pattern: DesignPattern,
        requirements: PatternRequirement,
        output_path: Optional[str] = None
    ) -> PatternImplementation:
        """設計パターン実装"""

        logger.info(f"🎨 パターン実装開始: {pattern.value}")
        logger.info(f"🎯 対象クラス: {requirements.target_classes}")

        if pattern not in self.pattern_templates:
            raise ValueError(f"サポートされていないパターン: {pattern.value}")

        template = self.pattern_templates[pattern]

        # コード生成
        generated_code = template.generate_code(requirements)
        test_code = template.generate_tests(requirements)
        imports = template.get_imports()

        # ファイルパス決定
        if output_path is None:
            output_path = self._generate_output_path(pattern, requirements)

        # SOLID原則準拠チェック
        solid_compliance = self._check_solid_compliance(generated_code)

        # 品質スコア計算
        quality_score = self._calculate_quality_score(generated_code, solid_compliance)

        # ドキュメント生成
        documentation = self._generate_documentation(pattern, requirements)

        implementation = PatternImplementation(
            pattern=pattern,
            generated_code=generated_code,
            file_path=output_path,
            imports=imports,
            classes=self._extract_class_names(generated_code),
            methods=self._extract_method_names(generated_code),
            test_code=test_code,
            documentation=documentation,
            solid_compliance=solid_compliance,
            quality_score=quality_score
        )

        self.implementation_history.append(implementation)

        logger.info(f"✅ パターン実装完了: {pattern.value}")
        logger.info(f"📄 出力ファイル: {output_path}")
        logger.info(f"⭐ 品質スコア: {quality_score:.2f}")

        return implementation

    def save_implementation(self, implementation: PatternImplementation) -> None:
        """実装コードの保存"""

        logger.info(f"💾 実装保存: {implementation.file_path}")

        # ディレクトリ作成
        os.makedirs(os.path.dirname(implementation.file_path), exist_ok=True)

        # メインコード保存
        with open(implementation.file_path, 'w', encoding='utf-8') as f:
            # インポート
            f.write('\n'.join(implementation.imports))
            f.write('\n\n')

            # 生成コード
            f.write(implementation.generated_code)

        # テストコード保存
        test_path = implementation.file_path.replace('.py', '_test.py')
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(implementation.test_code)

        # ドキュメント保存
        doc_path = implementation.file_path.replace('.py', '_doc.md')
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(implementation.documentation)

        logger.info(f"✅ 保存完了: {implementation.file_path}")
        logger.info(f"🧪 テスト: {test_path}")
        logger.info(f"📖 ドキュメント: {doc_path}")

    def get_available_patterns(self) -> List[DesignPattern]:
        """利用可能パターン一覧"""
        return list(self.pattern_templates.keys())

    def get_implementation_history(self) -> List[PatternImplementation]:
        """実装履歴取得"""
        return self.implementation_history[:]

    def _detect_factory_opportunities(self, tree: ast.AST, file_path: str) -> List[RefactoringOpportunity]:
        """Factory パターン適用機会検出"""
        opportunities = []

        # 大量のif-elif文によるオブジェクト生成を検出
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                elif_count = len(node.orelse)
                if elif_count > 3:  # 3つ以上のelif
                    opportunities.append(RefactoringOpportunity(
                        file_path=file_path,
                        line_number=node.lineno,
                        current_pattern="if-elif chain",
                        suggested_pattern=DesignPattern.FACTORY,
                        reason="大量の条件分岐によるオブジェクト生成パターンを検出",
                        complexity_reduction=elif_count * 2,
                        maintainability_gain=0.7
                    ))

        return opportunities

    def _detect_observer_opportunities(self, tree: ast.AST, file_path: str) -> List[RefactoringOpportunity]:
        """Observer パターン適用機会検出"""
        opportunities = []

        # 多数のメソッド呼び出しによる通知パターンを検出
        method_calls = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                method_calls += 1

        if method_calls > 10:  # 閾値調整可能
            opportunities.append(RefactoringOpportunity(
                file_path=file_path,
                line_number=1,
                current_pattern="direct method calls",
                suggested_pattern=DesignPattern.OBSERVER,
                reason="多数のメソッド呼び出しによる結合度増加を検出",
                complexity_reduction=method_calls // 2,
                maintainability_gain=0.8
            ))

        return opportunities

    def _detect_strategy_opportunities(self, tree: ast.AST, file_path: str) -> List[RefactoringOpportunity]:
        """Strategy パターン適用機会検出"""
        opportunities = []

        # 大きなメソッド内での条件分岐を検出
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if_count = sum(1 for child in ast.walk(node) if isinstance(child, ast.If))
                if if_count > 5:  # 5つ以上のif文
                    opportunities.append(RefactoringOpportunity(
                        file_path=file_path,
                        line_number=node.lineno,
                        current_pattern="complex conditional logic",
                        suggested_pattern=DesignPattern.STRATEGY,
                        reason=f"メソッド '{node.name}' 内の複雑な条件分岐を検出",
                        complexity_reduction=if_count * 3,
                        maintainability_gain=0.6
                    ))

        return opportunities

    def _generate_output_path(self, pattern: DesignPattern, requirements: PatternRequirement) -> str:
        """出力パス生成"""
        pattern_name = pattern.value.replace('_', '')
        class_name = requirements.target_classes[0] if requirements.target_classes else 'default'
        filename = f"{class_name.lower()}_{pattern_name}.py"
        return str(self.project_root / "tmp" / filename)

    def _check_solid_compliance(self, code: str) -> Dict[str, bool]:
        """SOLID原則準拠チェック"""

        # 簡易的なSOLID原則チェック
        compliance = {
            'single_responsibility': True,  # 単一責任原則
            'open_closed': True,           # 開放閉鎖原則
            'liskov_substitution': True,   # リスコフ置換原則
            'interface_segregation': True, # インターフェース分離原則
            'dependency_inversion': True   # 依存関係逆転原則
        }

        # パターン固有のチェックロジックを追加可能

        return compliance

    def _calculate_quality_score(self, code: str, solid_compliance: Dict[str, bool]) -> float:
        """品質スコア計算"""

        base_score = 0.5

        # SOLID原則準拠度
        solid_score = sum(solid_compliance.values()) / len(solid_compliance) * 0.4

        # コード品質指標
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        # ドキュメント率
        doc_lines = [line for line in lines if '"""' in line or "'''" in line]
        doc_score = min(len(doc_lines) / max(len(non_empty_lines), 1), 0.3) * 0.2

        # テスト存在
        test_score = 0.1 if 'test' in code.lower() else 0.0

        # エラーハンドリング
        error_handling_score = 0.1 if 'except' in code or 'raise' in code else 0.0

        total_score = base_score + solid_score + doc_score + test_score + error_handling_score

        return min(total_score, 1.0)

    def _generate_documentation(self, pattern: DesignPattern, requirements: PatternRequirement) -> str:
        """ドキュメント生成"""

        doc_template = textwrap.dedent(f'''
        # {pattern.value.replace('_', ' ').title()} Pattern Implementation

        ## 概要
        {pattern.value} パターンの自動実装コードです。

        ## 対象クラス
        {', '.join(requirements.target_classes)}

        ## SOLID原則準拠
        {', '.join(requirements.solid_principles)}

        ## 使用方法
        ```python
        # インポート
        from {Path(requirements.target_classes[0]).stem} import *

        # 基本使用例
        # TODO: 使用例を追加
        ```

        ## テスト実行
        ```bash
        pytest {requirements.target_classes[0].lower()}_test.py -v
        ```

        ## 実装詳細
        - 複雑度レベル: {requirements.complexity_level}
        - 推定工数: {requirements.estimated_effort}時間
        - インターフェース数: {len(requirements.interfaces)}
        - メソッド数: {len(requirements.methods)}

        ## 設計パターン利点
        - 保守性向上
        - 拡張性確保
        - テスタビリティ改善
        - コード再利用促進
        ''').strip()

        return doc_template

    def _extract_class_names(self, code: str) -> List[str]:
        """クラス名抽出"""
        try:
            tree = ast.parse(code)
            return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        except:
            return []

    def _extract_method_names(self, code: str) -> List[str]:
        """メソッド名抽出"""
        try:
            tree = ast.parse(code)
            return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        except:
            return []


if __name__ == "__main__":
    """簡単なテスト実行"""

    engine = PatternImplementationEngine()

    # Factory パターンテスト
    factory_requirements = PatternRequirement(
        pattern=DesignPattern.FACTORY,
        category=PatternCategory.CREATIONAL,
        target_classes=["Product", "ConcreteProductA", "ConcreteProductB"],
        interfaces=["Product"],
        methods=["operation", "create_product"],
        properties=[],
        solid_principles=["SRP", "OCP", "DIP"],
        complexity_level=3,
        estimated_effort=4
    )

    # パターン実装
    implementation = engine.implement_pattern(DesignPattern.FACTORY, factory_requirements)

    print(f"🎨 パターン実装完了:")
    print(f"  - パターン: {implementation.pattern.value}")
    print(f"  - ファイル: {implementation.file_path}")
    print(f"  - クラス数: {len(implementation.classes)}")
    print(f"  - メソッド数: {len(implementation.methods)}")
    print(f"  - 品質スコア: {implementation.quality_score:.2f}")
    print(f"  - SOLID準拠: {sum(implementation.solid_compliance.values())}/{len(implementation.solid_compliance)}")

    # 実装保存
    engine.save_implementation(implementation)
    print(f"✅ 実装ファイル保存完了")
