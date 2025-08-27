# Legacy wrapper - Phase3 Integration (Issue #1168 Parser Responsibility Separation)
# 9個のキーワードパーサーがCoreKeywordParserに統合完了
from ..core.parsing.integrated.core_keyword_parser import CoreKeywordParser

# 後方互換性維持
KeywordParser = CoreKeywordParser
UnifiedKeywordParser = CoreKeywordParser
