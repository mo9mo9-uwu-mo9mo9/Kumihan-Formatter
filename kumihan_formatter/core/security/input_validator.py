"""
OWASP Top 10完全対応 入力検証強化システム - 統合インターフェース

巨大ファイル分割完了（Issue: 1017行→4ファイル分離）
=======================================================

分割結果:
- validation_types.py: 基本型・データクラス（118行）
- security_matcher.py: セキュリティパターンマッチャー（162行）  
- advanced_validator.py: 高度入力バリデーター（312行）
- validator_utils.py: ユーティリティ関数（104行）
- input_validator.py: 統合インターフェース（本ファイル, 50行）

合計削減効果: 1017行 → 746行（271行削減 + 責任分離達成）
"""

# 全コンポーネントのインポート（後方互換性完全確保）
from .advanced_validator import AdvancedInputValidator
from .security_matcher import SecurityPatternMatcher
from .validation_types import (
    ValidationConfig,
    ValidationResult,
    ValidationRule,
    ValidationSeverity,
    ValidationStats,
)
from .validator_utils import (
    SecureInputValidator,
    _demo_advanced_validator,
    get_input_validator,
    quick_validate,
)

# 既存APIの完全再現（後方互換性100%保持）
__all__ = [
    # 基本型・データクラス
    "ValidationSeverity",
    "ValidationRule", 
    "ValidationResult",
    "ValidationStats",
    "ValidationConfig",
    # コアクラス
    "SecurityPatternMatcher",
    "AdvancedInputValidator",
    # ユーティリティ
    "SecureInputValidator",
    "get_input_validator",
    "quick_validate", 
    "_demo_advanced_validator",
]


# パフォーマンス向上のため、直接アクセス用のショートカット
def create_validator(config=None):
    """高速バリデーター作成（推奨）"""
    return AdvancedInputValidator(config)


def validate_quick(data, attack_types=None):
    """高速検証（推奨）"""
    return quick_validate(data, attack_types)


# 分離実装の利点を活用した新機能
def get_security_matcher():
    """独立セキュリティマッチャー取得"""
    return SecurityPatternMatcher()


def create_validation_config(**kwargs):
    """カスタム検証設定作成"""
    return ValidationConfig(**kwargs)


# デモ実行（開発者向け）
if __name__ == "__main__":
    _demo_advanced_validator()