"""Plugin system for Kumihan-Formatter

This package provides a flexible plugin architecture that allows
users to extend functionality without modifying core code.
"""

from .plugin_manager import PluginManager
from .plugin_interface import (
    KumihanPlugin,
    ParserPlugin,
    RendererPlugin,
    ValidatorPlugin,
    ProcessorPlugin
)
from .plugin_registry import PluginRegistry
from .plugin_loader import PluginLoader

__all__ = [
    'PluginManager',
    'KumihanPlugin',
    'ParserPlugin',
    'RendererPlugin', 
    'ValidatorPlugin',
    'ProcessorPlugin',
    'PluginRegistry',
    'PluginLoader'
]