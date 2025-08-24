"""Strategy Pattern Implementation"""

from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    runtime_checkable,
)

from ..utilities.logger import get_logger

if TYPE_CHECKING:
    from .dependency_injection import DIContainer

logger = get_logger(__name__)


@runtime_checkable
class ParsingStrategy(Protocol):
    """パーシング戦略プロトコル"""

    def parse(self, content: str, context: Dict[str, Any]) -> Any:
        """戦略的パース実行"""
        ...

    def get_strategy_name(self) -> str:
        """戦略名取得"""
        ...

    def supports_content(self, content: str) -> float:
        """コンテンツ対応度（0.0-1.0）"""
        ...


@runtime_checkable
class RenderingStrategy(Protocol):
    """レンダリング戦略プロトコル"""

    def render(self, data: Any, context: Dict[str, Any]) -> str:
        """戦略的レンダリング実行"""
        ...

    def get_strategy_name(self) -> str:
        """戦略名取得"""
        ...

    def supports_format(self, output_format: str) -> bool:
        """フォーマット対応判定"""
        ...


class StrategyPriority(Enum):
    """戦略優先度"""

    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


class StrategyManager:
    """戦略管理システム"""

    def __init__(self, container: Optional["DIContainer"] = None) -> None:
        self._parsing_strategies: Dict[str, ParsingStrategy] = {}
        self._rendering_strategies: Dict[str, RenderingStrategy] = {}
        self._strategy_priorities: Dict[str, int] = {}
        self._default_parsing_strategy: Optional[str] = None
        self._default_rendering_strategy: Optional[str] = None
        self._container = container
        self._strategy_registry: Dict[str, Type[Any]] = {}  # 戦略クラス登録

    def register_parsing_strategy(
        self,
        name: str,
        strategy: ParsingStrategy,
        priority: StrategyPriority = StrategyPriority.NORMAL,
        is_default: bool = False,
    ) -> None:
        """パーシング戦略登録"""
        self._parsing_strategies[name] = strategy
        self._strategy_priorities[name] = priority.value
        if is_default:
            self._default_parsing_strategy = name

    def register_rendering_strategy(
        self,
        name: str,
        strategy: RenderingStrategy,
        priority: StrategyPriority = StrategyPriority.NORMAL,
        is_default: bool = False,
    ) -> None:
        """レンダリング戦略登録"""
        self._rendering_strategies[name] = strategy
        self._strategy_priorities[name] = priority.value
        if is_default:
            self._default_rendering_strategy = name

    def select_parsing_strategy(self, content: str) -> Optional[ParsingStrategy]:
        """最適パーシング戦略選択"""
        best_strategy = None
        best_score = 0.0

        for name, strategy in self._parsing_strategies.items():
            score = strategy.supports_content(content)
            # 優先度を考慮した重み付け
            weighted_score = score * (self._strategy_priorities.get(name, 1) / 10.0)

            if weighted_score > best_score:
                best_score = weighted_score
                best_strategy = strategy

        return best_strategy

    def select_rendering_strategy(
        self, output_format: str
    ) -> Optional[RenderingStrategy]:
        """最適レンダリング戦略選択"""
        for name, strategy in self._rendering_strategies.items():
            if strategy.supports_format(output_format):
                return strategy
        return None

    def get_parsing_strategy(self, name: str) -> Optional[ParsingStrategy]:
        """指定パーシング戦略取得"""
        return self._parsing_strategies.get(name)

    def get_rendering_strategy(self, name: str) -> Optional[RenderingStrategy]:
        """指定レンダリング戦略取得"""
        return self._rendering_strategies.get(name)

    def list_strategies(self) -> Dict[str, List[str]]:
        """登録戦略一覧"""
        return {
            "parsing": list(self._parsing_strategies.keys()),
            "rendering": list(self._rendering_strategies.keys()),
        }

    def register_strategy_class(
        self, name: str, strategy_class: Type[Any], strategy_type: str = "parsing"
    ) -> None:
        """戦略クラスの登録"""
        try:
            self._strategy_registry[f"{strategy_type}:{name}"] = strategy_class

            if self._container:
                # DIコンテナーに登録
                self._container.register(strategy_class, strategy_class)

        except Exception as e:
            logger.error(f"Strategy class registration failed: {name}, error: {e}")

    def create_strategy_instance(
        self, name: str, strategy_type: str = "parsing"
    ) -> Optional[Any]:
        """戦略インスタンス作成"""
        try:
            key = f"{strategy_type}:{name}"
            if key not in self._strategy_registry:
                return None

            strategy_class = self._strategy_registry[key]

            if self._container:
                # DIコンテナー経由で作成
                return self._container.resolve(strategy_class)
            else:
                # 直接作成
                return strategy_class()

        except Exception as e:
            logger.error(f"Strategy instance creation failed: {name}, error: {e}")
            return None

    def validate_strategies(self) -> List[str]:
        """戦略の妥当性検証"""
        issues = []

        try:
            # パーシング戦略の検証
            for name, strategy in self._parsing_strategies.items():
                if not hasattr(strategy, "supports_content"):
                    issues.append(
                        f"Parsing strategy {name} missing supports_content method"
                    )
                if not hasattr(strategy, "parse"):
                    issues.append(f"Parsing strategy {name} missing parse method")

            # レンダリング戦略の検証
            for name, strategy in self._rendering_strategies.items():
                if not hasattr(strategy, "supports_format"):
                    issues.append(
                        f"Rendering strategy {name} missing supports_format method"
                    )
                if not hasattr(strategy, "render"):
                    issues.append(f"Rendering strategy {name} missing render method")

        except Exception as e:
            issues.append(f"Strategy validation error: {e}")

        return issues
