"""Design Patterns Implementation

アーキテクチャパターンによる拡張性・保守性向上
"""

from .command import (
    Command,
    CommandProcessor,
    CommandQueue,
    CommandStatus,
    ParseCommand,
    RenderCommand,
)
from .decorator import (
    CachingParserDecorator,
    DecoratorChain,
    LoggingDecorator,
    ParserDecorator,
    RendererDecorator,
)
from .integration import ArchitectureManager
from .observer import Event, EventBus, EventType, Observer
from .strategy import (
    ParsingStrategy,
    RenderingStrategy,
    StrategyManager,
    StrategyPriority,
)

__all__ = [
    "EventBus",
    "Observer",
    "Event",
    "EventType",
    "ParsingStrategy",
    "RenderingStrategy",
    "StrategyManager",
    "StrategyPriority",
    "ParserDecorator",
    "RendererDecorator",
    "DecoratorChain",
    "CachingParserDecorator",
    "LoggingDecorator",
    "Command",
    "CommandProcessor",
    "CommandQueue",
    "CommandStatus",
    "ParseCommand",
    "RenderCommand",
    "ArchitectureManager",
]
