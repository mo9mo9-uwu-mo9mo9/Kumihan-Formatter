# Issue #1173対応: block_parser.py責任分離（650行→3ファイル）
from .parser import UnifiedBlockParser, BlockParser
from .handlers import BlockHandler
from .utils import BlockPatterns

# Legacy imports for backward compatibility
from .block_parser import UnifiedBlockParser as LegacyUnifiedBlockParser
from .block_handlers import (
    KumihanBlockHandler,
    TextBlockHandler,
    ImageBlockHandler,
    SpecialBlockHandler,
    MarkerBlockHandler,
    ContentBlockHandler,
    ListBlockHandler,
    BlockValidatorCollection,
    BlockHandlerCollection,
)
from .block_utils import (
    setup_block_patterns,
    BlockExtractor,
    BlockTypeDetector,
    BlockProcessor,
    BlockCache,
    BlockLineProcessor,
)

__all__ = [
    # New separated structure (Issue #1173)
    "UnifiedBlockParser",
    "BlockParser",
    "BlockHandler",
    "BlockPatterns",
    # Legacy compatibility
    "LegacyUnifiedBlockParser",
    "KumihanBlockHandler",
    "TextBlockHandler",
    "ImageBlockHandler",
    "SpecialBlockHandler",
    "MarkerBlockHandler",
    "ContentBlockHandler",
    "ListBlockHandler",
    "BlockValidatorCollection",
    "BlockHandlerCollection",
    "setup_block_patterns",
    "BlockExtractor",
    "BlockTypeDetector",
    "BlockProcessor",
    "BlockCache",
    "BlockLineProcessor",
]
