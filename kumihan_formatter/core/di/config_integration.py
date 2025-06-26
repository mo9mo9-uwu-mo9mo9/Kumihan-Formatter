"""DIコンテナの設定統合機能"""

import json
import yaml
from typing import Dict, Any, Type, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field

from .container import DIContainer
from .interfaces import ServiceLifetime
from .exceptions import ServiceRegistrationError


@dataclass
class ServiceConfiguration:
    """サービス設定"""
    type_name: str
    implementation_name: Optional[str] = None
    lifetime: str = "transient"
    parameters: Dict[str, Any] = field(default_factory=dict)
    factory_method: Optional[str] = None
    enabled: bool = True
    environment: Optional[str] = None  # dev, test, prod


@dataclass
class DIConfiguration:
    """DI設定"""
    services: List[ServiceConfiguration] = field(default_factory=list)
    auto_discovery: bool = True
    discovery_packages: List[str] = field(default_factory=list)
    enable_hot_reload: bool = False
    hot_reload_interval: float = 5.0


class ConfigurationLoader:
    """設定ローダー"""
    
    def __init__(self):
        self._type_registry: Dict[str, Type] = {}
        
    def register_type(self, name: str, type_class: Type) -> None:
        """型を登録"""
        self._type_registry[name] = type_class
    
    def load_from_file(self, config_path: Path) -> DIConfiguration:
        """ファイルから設定を読み込み"""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() == '.json':
                data = json.load(f)
            elif config_path.suffix.lower() in ['.yml', '.yaml']:
                data = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported configuration format: {config_path.suffix}")
        
        return self._parse_configuration(data)
    
    def load_from_dict(self, config_data: Dict[str, Any]) -> DIConfiguration:
        """辞書から設定を読み込み"""
        return self._parse_configuration(config_data)
    
    def _parse_configuration(self, data: Dict[str, Any]) -> DIConfiguration:
        """設定データをパース"""
        config = DIConfiguration()
        
        # サービス設定
        if 'services' in data:
            for service_data in data['services']:
                service_config = ServiceConfiguration(**service_data)
                config.services.append(service_config)
        
        # その他の設定
        if 'auto_discovery' in data:
            config.auto_discovery = data['auto_discovery']
        
        if 'discovery_packages' in data:
            config.discovery_packages = data['discovery_packages']
        
        if 'enable_hot_reload' in data:
            config.enable_hot_reload = data['enable_hot_reload']
        
        if 'hot_reload_interval' in data:
            config.hot_reload_interval = data['hot_reload_interval']
        
        return config


class ContainerConfigurator:
    """コンテナ設定器"""
    
    def __init__(self, container: DIContainer):
        self.container = container
        self.loader = ConfigurationLoader()
        self._registered_types: Dict[str, Type] = {}
    
    def register_types(self, types: Dict[str, Type]) -> None:
        """型マッピングを登録"""
        self._registered_types.update(types)
        for name, type_class in types.items():
            self.loader.register_type(name, type_class)
    
    def configure_from_file(
        self, 
        config_path: Path,
        environment: Optional[str] = None
    ) -> None:
        """ファイルから設定を適用"""
        config = self.loader.load_from_file(config_path)
        self.apply_configuration(config, environment)
    
    def configure_from_dict(
        self, 
        config_data: Dict[str, Any],
        environment: Optional[str] = None
    ) -> None:
        """辞書から設定を適用"""
        config = self.loader.load_from_dict(config_data)
        self.apply_configuration(config, environment)
    
    def apply_configuration(
        self, 
        config: DIConfiguration,
        environment: Optional[str] = None
    ) -> None:
        """設定をコンテナに適用"""
        
        # 環境固有のサービスをフィルター
        filtered_services = self._filter_services_by_environment(
            config.services, 
            environment
        )
        
        # サービスを登録
        for service_config in filtered_services:
            if service_config.enabled:
                self._register_service(service_config)
        
        # 自動発見
        if config.auto_discovery:
            self._perform_auto_discovery(config.discovery_packages)
    
    def _filter_services_by_environment(
        self, 
        services: List[ServiceConfiguration],
        environment: Optional[str]
    ) -> List[ServiceConfiguration]:
        """環境に基づいてサービスをフィルター"""
        if environment is None:
            return [s for s in services if s.environment is None]
        
        return [
            s for s in services 
            if s.environment is None or s.environment == environment
        ]
    
    def _register_service(self, config: ServiceConfiguration) -> None:
        """サービスを登録"""
        try:
            # 型を解決
            service_type = self._resolve_type(config.type_name)
            implementation_type = None
            
            if config.implementation_name:
                implementation_type = self._resolve_type(config.implementation_name)
            
            # ライフタイムを解決
            lifetime = self._resolve_lifetime(config.lifetime)
            
            # ファクトリーメソッドがある場合
            factory = None
            if config.factory_method:
                factory = self._create_factory(config.factory_method, config.parameters)
            
            # 登録
            if lifetime == ServiceLifetime.SINGLETON:
                self.container.register_singleton(
                    service_type, 
                    implementation_type, 
                    factory
                )
            elif lifetime == ServiceLifetime.SCOPED:
                self.container.register_scoped(
                    service_type, 
                    implementation_type, 
                    factory
                )
            else:
                self.container.register_transient(
                    service_type, 
                    implementation_type, 
                    factory
                )
                
        except Exception as e:
            raise ServiceRegistrationError(
                service_type if 'service_type' in locals() else type(None),
                f"Failed to register service from configuration: {e}"
            )
    
    def _resolve_type(self, type_name: str) -> Type:
        """型名から型を解決"""
        if type_name in self._registered_types:
            return self._registered_types[type_name]
        
        # 動的インポートを試行
        try:
            parts = type_name.split('.')
            module_name = '.'.join(parts[:-1])
            class_name = parts[-1]
            
            import importlib
            module = importlib.import_module(module_name)
            return getattr(module, class_name)
            
        except Exception:
            raise ValueError(f"Cannot resolve type: {type_name}")
    
    def _resolve_lifetime(self, lifetime_str: str) -> ServiceLifetime:
        """ライフタイム文字列を解決"""
        lifetime_map = {
            'singleton': ServiceLifetime.SINGLETON,
            'scoped': ServiceLifetime.SCOPED,
            'transient': ServiceLifetime.TRANSIENT
        }
        
        if lifetime_str.lower() not in lifetime_map:
            raise ValueError(f"Unknown lifetime: {lifetime_str}")
        
        return lifetime_map[lifetime_str.lower()]
    
    def _create_factory(
        self, 
        factory_method: str, 
        parameters: Dict[str, Any]
    ) -> callable:
        """ファクトリーメソッドを作成"""
        def factory(provider):
            # ファクトリーメソッドを動的に呼び出し
            parts = factory_method.split('.')
            module_name = '.'.join(parts[:-1])
            method_name = parts[-1]
            
            import importlib
            module = importlib.import_module(module_name)
            method = getattr(module, method_name)
            
            # パラメータを注入
            return method(provider, **parameters)
        
        return factory
    
    def _perform_auto_discovery(self, packages: List[str]) -> None:
        """自動発見を実行"""
        import importlib
        import pkgutil
        
        for package_name in packages:
            try:
                package = importlib.import_module(package_name)
                
                # パッケージ内のモジュールを探索
                for _, module_name, _ in pkgutil.iter_modules(
                    package.__path__, 
                    package_name + '.'
                ):
                    try:
                        module = importlib.import_module(module_name)
                        self._discover_services_in_module(module)
                    except Exception:
                        continue  # モジュール読み込みエラーは無視
                        
            except ImportError:
                continue  # パッケージが見つからない場合は無視
    
    def _discover_services_in_module(self, module) -> None:
        """モジュール内のサービスを発見"""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # @serviceデコレータが付いているクラスを探す
            if (hasattr(attr, '__class__') and 
                hasattr(attr, '_auto_register') and
                attr._auto_register):
                
                # 既に登録済みかチェック
                service_type = getattr(attr, '_service_type', attr)
                if not self.container.has_service(service_type):
                    
                    lifetime = getattr(attr, '_service_lifetime', ServiceLifetime.TRANSIENT)
                    
                    # 登録
                    if lifetime == ServiceLifetime.SINGLETON:
                        self.container.register_singleton(service_type, attr)
                    elif lifetime == ServiceLifetime.SCOPED:
                        self.container.register_scoped(service_type, attr)
                    else:
                        self.container.register_transient(service_type, attr)