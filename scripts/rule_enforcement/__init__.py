#!/usr/bin/env python3
"""
規則遵守原則絶対遵守システム - 統合パッケージ
Claude's行動制御・ツール検証・自動是正システム（統合インポート）

Created: 2025-08-04
Updated: 2025-08-16 (Issue #898対応: rule_enforcement_system.py 分割・リファクタリング)
Purpose: CLAUDE.md 規則遵守原則の技術的強制実装（統合パッケージ）
Status: Production Ready

このパッケージは1417行のrule_enforcement_system.pyを以下に分割：
- core_enforcement.py: 規則遵守エンフォースメント本体（基本クラス・コア制御）
- behavioral_control.py: 行動制御・心理的条件付けシステム
- integrated_system.py: 統合管理・レポート生成システム
- __init__.py: 統合インポート（後方互換性維持）
"""

# === コア機能インポート ===
from .core_enforcement import (
    # データクラスとEnum
    ViolationLevel,
    ToolCategory,
    ViolationEvent,
    ToolUsageStats,
    # メインシステム
    RuleEnforcementSystem
)

# === 行動制御機能インポート ===
from .behavioral_control import (
    # 行動制御システム
    BehavioralControlLayer,
    RuntimeBehaviorModifier
)

# === 統合システム機能インポート ===
from .integrated_system import (
    # 統合システム
    IntegratedBehavioralControlSystem,
    BehavioralControlReportGenerator,
    # メイン実行関数
    main
)

# === 後方互換性のため全シンボルをエクスポート ===
__all__ = [
    # データクラス・Enum
    'ViolationLevel',
    'ToolCategory',
    'ViolationEvent',
    'ToolUsageStats',

    # コアシステム
    'RuleEnforcementSystem',

    # 監視・制御システム
    'BehavioralControlLayer',
    'RuntimeBehaviorModifier',
    'IntegratedBehavioralControlSystem',
    'BehavioralControlReportGenerator',

    # ユーティリティ
    'logger',
    'main'
]

# === パッケージ情報 ===
__version__ = "2.0.0"
__author__ = "Claude Code - Kumihan-Formatter"
__description__ = "規則遵守原則絶対遵守システム - 統合行動制御・監視・エンフォースメントパッケージ"

# === 統合システム初期化ヘルパー ===
def create_integrated_system(config_path: str = ".claude-behavioral-control.json") -> IntegratedBehavioralControlSystem:
    """統合行動制御システム作成ヘルパー

    Args:
        config_path: 設定ファイルパス

    Returns:
        IntegratedBehavioralControlSystem: 統合システムインスタンス
    """
    return IntegratedBehavioralControlSystem(config_path)

def create_rule_enforcement_system(config_path: str = ".claude-system-override.yml") -> RuleEnforcementSystem:
    """規則遵守エンフォースメントシステム作成ヘルパー

    Args:
        config_path: 設定ファイルパス

    Returns:
        RuleEnforcementSystem: エンフォースメントシステムインスタンス
    """
    return RuleEnforcementSystem(config_path)

def create_report_generator(integrated_system: IntegratedBehavioralControlSystem) -> BehavioralControlReportGenerator:
    """レポート生成システム作成ヘルパー

    Args:
        integrated_system: 統合システムインスタンス

    Returns:
        BehavioralControlReportGenerator: レポート生成システムインスタンス
    """
    return BehavioralControlReportGenerator(integrated_system)

# === システム情報表示 ===
def show_system_info():
    """システム情報表示"""
    print("=" * 60)
    print("🧠 規則遵守原則絶対遵守システム - 統合パッケージ")
    print("=" * 60)
    print(f"📦 パッケージ版本: {__version__}")
    print(f"📝 説明: {__description__}")
    print(f"👨‍💻 開発者: {__author__}")
    print("")
    print("📁 分割構成:")
    print("  ├── core_enforcement.py  - 規則遵守エンフォースメント本体")
    print("  ├── behavioral_control.py - 行動制御・心理的条件付けシステム")
    print("  ├── integrated_system.py  - 統合管理・レポート生成システム")
    print("  └── __init__.py           - 統合インポート")
    print("")
    print("🎯 使用例:")
    print("  from rule_enforcement import create_integrated_system")
    print("  system = create_integrated_system()")
    print("  result = system.process_comprehensive_conditioning('tool_name')")
    print("=" * 60)

# === パッケージ初期化時の情報表示 ===
if __name__ == "__main__":
    show_system_info()
    # メインデモ実行
    main()
