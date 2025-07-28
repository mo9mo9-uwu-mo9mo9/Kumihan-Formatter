#!/usr/bin/env python3
"""
TDD Specification Generator - Issue #640 Phase 2
TDD仕様テンプレート生成システム

目的: Issue内容からTDDテスト仕様の自動生成
- Issue分析・テスト項目抽出
- Given-When-Thenテンプレート生成
- ファイル構造自動作成
"""

import json
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

@dataclass
class TestSpecification:
    """テスト仕様"""
    test_name: str
    description: str
    given: List[str]
    when: List[str]
    then: List[str]
    test_category: str  # "unit", "integration", "e2e"
    priority: str       # "high", "medium", "low"
    complexity: str     # "simple", "medium", "complex"

@dataclass
class SpecificationSet:
    """仕様セット"""
    issue_number: str
    issue_title: str
    module_name: str
    class_name: str
    test_file_path: Path
    implementation_file_path: Path
    specifications: List[TestSpecification]
    setup_requirements: List[str]
    dependencies: List[str]

class TDDSpecGenerator:
    """TDD仕様生成クラス"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.session_file = project_root / ".tdd_session.json"
        self.templates_dir = project_root / "scripts" / "tdd_templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        # テンプレートパターン定義
        self.test_patterns = {
            "parser": {
                "category": "unit",
                "base_class": "TestCase",
                "common_given": ["有効な入力テキスト", "パーサーインスタンス"],
                "common_when": ["テキストを解析する"],
                "common_then": ["適切なASTノードが生成される", "エラーが発生しない"]
            },
            "renderer": {
                "category": "unit", 
                "base_class": "TestCase",
                "common_given": ["有効なASTノード", "レンダラーインスタンス"],
                "common_when": ["ノードをレンダリングする"],
                "common_then": ["期待されるHTML出力が生成される", "フォーマットが正しい"]
            },
            "validator": {
                "category": "unit",
                "base_class": "TestCase", 
                "common_given": ["検証対象データ", "バリデーターインスタンス"],
                "common_when": ["データを検証する"],
                "common_then": ["検証結果が正しい", "適切なエラーメッセージが表示される"]
            },
            "command": {
                "category": "integration",
                "base_class": "TestCase",
                "common_given": ["コマンドライン引数", "テスト用ファイル"],
                "common_when": ["コマンドを実行する"],
                "common_then": ["期待される出力が生成される", "正しい終了コードが返される"]
            }
        }
    
    def generate_specifications(self) -> SpecificationSet:
        """仕様生成メイン処理"""
        logger.info("📋 TDD仕様テンプレート生成開始...")
        
        # 現在のTDDセッション取得
        session = self._load_current_session()
        if not session:
            logger.error("アクティブなTDDセッションがありません")
            return None
        
        # Issue情報分析
        issue_analysis = self._analyze_issue(session)
        
        # モジュール・クラス名決定
        naming_info = self._determine_naming(issue_analysis)
        
        # テスト仕様生成
        specifications = self._generate_test_specifications(issue_analysis, naming_info)
        
        # ファイルパス決定
        file_paths = self._determine_file_paths(naming_info)
        
        # 仕様セット作成
        spec_set = SpecificationSet(
            issue_number=session["issue_number"],
            issue_title=session["issue_title"],
            module_name=naming_info["module_name"],
            class_name=naming_info["class_name"],
            test_file_path=file_paths["test_file"],
            implementation_file_path=file_paths["implementation_file"],
            specifications=specifications,
            setup_requirements=self._determine_setup_requirements(issue_analysis),
            dependencies=self._determine_dependencies(issue_analysis)
        )
        
        # テンプレートファイル生成
        self._generate_template_files(spec_set)
        
        logger.info(f"✅ TDD仕様テンプレート生成完了: {len(specifications)}個のテスト仕様")
        return spec_set
    
    def _load_current_session(self) -> Optional[Dict]:
        """現在のセッション読み込み"""
        if not self.session_file.exists():
            return None
            
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"セッション読み込み失敗: {e}")
            return None
    
    def _analyze_issue(self, session: Dict) -> Dict:
        """Issue分析"""
        title = session["issue_title"]
        description = session["issue_description"]
        
        # キーワード抽出
        keywords = self._extract_keywords(title + " " + description)
        
        # 機能分類
        feature_type = self._classify_feature_type(keywords, title)
        
        # 複雑度推定
        complexity = self._estimate_complexity(description, keywords)
        
        # テスト項目抽出
        test_scenarios = self._extract_test_scenarios(description)
        
        return {
            "title": title,
            "description": description,
            "keywords": keywords,
            "feature_type": feature_type,
            "complexity": complexity,
            "test_scenarios": test_scenarios,
            "acceptance_criteria": self._extract_acceptance_criteria(description)
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """キーワード抽出"""
        # 技術用語パターン
        tech_patterns = [
            r'パーサー?', r'parser', r'レンダラー?', r'renderer',
            r'バリデーター?', r'validator', r'コマンド', r'command',
            r'GUI', r'UI', r'API', r'HTML', r'CSS', r'JSON',
            r'テスト', r'test', r'キャッシュ', r'cache',
            r'エラー', r'error', r'例外', r'exception'
        ]
        
        keywords = []
        text_lower = text.lower()
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text_lower)
            keywords.extend(matches)
        
        # 動詞パターン
        action_patterns = [
            r'追加', r'add', r'修正', r'fix', r'改善', r'improve',
            r'実装', r'implement', r'削除', r'remove', r'更新', r'update'
        ]
        
        for pattern in action_patterns:
            if re.search(pattern, text_lower):
                keywords.append(pattern)
        
        return list(set(keywords))
    
    def _classify_feature_type(self, keywords: List[str], title: str) -> str:
        """機能分類"""
        title_lower = title.lower()
        
        if any(k in keywords for k in ['parser', 'パーサー']):
            return "parser"
        elif any(k in keywords for k in ['renderer', 'レンダラー']):
            return "renderer"
        elif any(k in keywords for k in ['validator', 'バリデーター']):
            return "validator"
        elif any(k in keywords for k in ['command', 'コマンド']):
            return "command"
        elif any(k in keywords for k in ['gui', 'ui']):
            return "gui"
        elif any(k in keywords for k in ['cache', 'キャッシュ']):
            return "cache"
        else:
            return "utility"
    
    def _estimate_complexity(self, description: str, keywords: List[str]) -> str:
        """複雑度推定"""
        complexity_indicators = {
            "simple": ["単純", "simple", "基本", "basic"],
            "medium": ["拡張", "extend", "改善", "improve"],
            "complex": ["完全", "complete", "根本", "fundamental", "再構築", "rebuild"]
        }
        
        description_lower = description.lower()
        
        for complexity, indicators in complexity_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                return complexity
        
        # デフォルトは文章長で判定
        if len(description) > 500:
            return "complex"
        elif len(description) > 200:
            return "medium"
        else:
            return "simple"
    
    def _extract_test_scenarios(self, description: str) -> List[str]:
        """テストシナリオ抽出"""
        scenarios = []
        
        # 箇条書きパターン抽出
        bullet_patterns = [
            r'^\s*[-\*\+]\s+(.+)$',
            r'^\s*\d+\.\s+(.+)$',
            r'^\s*\d+\)\s+(.+)$'
        ]
        
        lines = description.split('\n')
        for line in lines:
            for pattern in bullet_patterns:
                match = re.match(pattern, line)
                if match:
                    scenario = match.group(1).strip()
                    if len(scenario) > 10:  # 意味のある長さのもののみ
                        scenarios.append(scenario)
        
        # パターンベースシナリオ生成
        if not scenarios:
            scenarios = [
                "正常なケースで期待される動作を確認する",
                "異常なケースでエラーが適切に処理される",
                "境界値での動作を確認する"
            ]
        
        return scenarios
    
    def _extract_acceptance_criteria(self, description: str) -> List[str]:
        """受け入れ条件抽出"""
        criteria = []
        
        # 受け入れ条件のセクション検索
        ac_section_patterns = [
            r'受け入れ条件[：:]\s*(.+?)(?=\n\n|\n#|\Z)',
            r'Acceptance Criteria[：:]\s*(.+?)(?=\n\n|\n#|\Z)',
            r'条件[：:]\s*(.+?)(?=\n\n|\n#|\Z)'
        ]
        
        for pattern in ac_section_patterns:
            match = re.search(pattern, description, re.DOTALL | re.IGNORECASE)
            if match:
                section_text = match.group(1)
                # 各行を条件として追加
                for line in section_text.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        criteria.append(line)
                break
        
        return criteria
    
    def _determine_naming(self, analysis: Dict) -> Dict:
        """命名決定"""
        feature_type = analysis["feature_type"]
        title = analysis["title"]
        
        # モジュール名生成
        title_words = re.findall(r'\w+', title.lower())
        meaningful_words = [w for w in title_words if len(w) > 2 and w not in ['the', 'and', 'for', 'with']]
        
        if meaningful_words:
            module_name = "_".join(meaningful_words[:3])
        else:
            module_name = f"{feature_type}_module"
        
        # クラス名生成
        class_words = [w.capitalize() for w in meaningful_words[:2]]
        if class_words:
            if feature_type == "parser":
                class_name = "".join(class_words) + "Parser"
            elif feature_type == "renderer":
                class_name = "".join(class_words) + "Renderer"
            elif feature_type == "validator":
                class_name = "".join(class_words) + "Validator"
            elif feature_type == "command":
                class_name = "".join(class_words) + "Command"
            else:
                class_name = "".join(class_words) + "Handler"
        else:
            class_name = f"{feature_type.capitalize()}Handler"
        
        return {
            "module_name": module_name,
            "class_name": class_name,
            "feature_type": feature_type
        }
    
    def _generate_test_specifications(self, analysis: Dict, naming: Dict) -> List[TestSpecification]:
        """テスト仕様生成"""
        specifications = []
        feature_type = naming["feature_type"]
        
        # パターンベーステンプレート取得
        pattern = self.test_patterns.get(feature_type, self.test_patterns["parser"])
        
        # 基本仕様生成
        for i, scenario in enumerate(analysis["test_scenarios"], 1):
            spec = TestSpecification(
                test_name=f"test_{naming['module_name']}_scenario_{i}",
                description=scenario,
                given=pattern["common_given"].copy(),
                when=pattern["common_when"].copy(),
                then=pattern["common_then"].copy(),
                test_category=pattern["category"],
                priority="high" if i <= 2 else "medium",
                complexity=analysis["complexity"]
            )
            
            # シナリオ固有の調整
            spec.when.append(f"{scenario}を実行する")
            spec.then.append("期待される結果が得られる")
            
            specifications.append(spec)
        
        # エラーケース仕様追加
        error_spec = TestSpecification(
            test_name=f"test_{naming['module_name']}_error_handling",
            description="エラーケースの適切な処理",
            given=["無効な入力データ", f"{naming['class_name']}インスタンス"],
            when=["無効なデータで処理を実行する"],
            then=["適切な例外が発生する", "エラーメッセージが表示される"],
            test_category=pattern["category"],
            priority="high",
            complexity="simple"
        )
        specifications.append(error_spec)
        
        # 境界値テスト仕様追加
        boundary_spec = TestSpecification(
            test_name=f"test_{naming['module_name']}_boundary_values",
            description="境界値での動作確認",
            given=["境界値データ", f"{naming['class_name']}インスタンス"],
            when=["境界値で処理を実行する"],
            then=["境界値が正しく処理される", "エラーが発生しない"],
            test_category=pattern["category"],
            priority="medium",
            complexity="medium"
        )
        specifications.append(boundary_spec)
        
        return specifications
    
    def _determine_file_paths(self, naming: Dict) -> Dict:
        """ファイルパス決定"""
        module_name = naming["module_name"]
        feature_type = naming["feature_type"]
        
        # 実装ファイルパス
        if feature_type in ["parser", "renderer"]:
            impl_dir = self.project_root / "kumihan_formatter" / "core" / f"{feature_type}s"
        elif feature_type == "command":
            impl_dir = self.project_root / "kumihan_formatter" / "commands"
        else:
            impl_dir = self.project_root / "kumihan_formatter" / "core" / "utilities"
        
        impl_file = impl_dir / f"{module_name}.py"
        
        # テストファイルパス
        test_dir = self.project_root / "tests" / "unit"
        if feature_type in ["parser", "renderer"]:
            test_dir = test_dir / f"{feature_type}s"
        
        test_file = test_dir / f"test_{module_name}.py"
        
        return {
            "implementation_file": impl_file,
            "test_file": test_file
        }
    
    def _determine_setup_requirements(self, analysis: Dict) -> List[str]:
        """セットアップ要件決定"""
        requirements = ["pytest", "unittest.mock"]
        
        if "gui" in analysis["keywords"]:
            requirements.append("pytest-qt")
        
        if "database" in analysis["keywords"]:
            requirements.append("pytest-database")
        
        if analysis["complexity"] == "complex":
            requirements.extend(["pytest-cov", "pytest-benchmark"])
        
        return requirements
    
    def _determine_dependencies(self, analysis: Dict) -> List[str]:
        """依存関係決定"""
        dependencies = []
        
        if "parser" in analysis["feature_type"]:
            dependencies.append("kumihan_formatter.core.ast_nodes")
        
        if "renderer" in analysis["feature_type"]:
            dependencies.append("kumihan_formatter.core.rendering")
        
        if "command" in analysis["feature_type"]:
            dependencies.append("kumihan_formatter.core.file_operations")
        
        return dependencies
    
    def _generate_template_files(self, spec_set: SpecificationSet):
        """テンプレートファイル生成"""
        # テストファイル生成
        self._generate_test_file(spec_set)
        
        # 実装ファイルスケルトン生成
        self._generate_implementation_skeleton(spec_set)
        
        # README生成
        self._generate_tdd_readme(spec_set)
    
    def _generate_test_file(self, spec_set: SpecificationSet):
        """テストファイル生成"""
        test_content = f'''#!/usr/bin/env python3
"""
Test for {spec_set.class_name} - Issue #{spec_set.issue_number}
Generated by TDD Spec Generator

{spec_set.issue_title}
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
from pathlib import Path
import tempfile
import json

# プロジェクト固有インポート
{chr(10).join(f"# from {dep}" for dep in spec_set.dependencies)}

class Test{spec_set.class_name}(unittest.TestCase):
    """
    {spec_set.class_name}のテストクラス
    
    TDD仕様に基づく包括的テストスイート
    Issue #{spec_set.issue_number}: {spec_set.issue_title}
    """
    
    def setUp(self):
        """テスト前準備"""
        # TODO: {spec_set.class_name}インスタンス生成
        # self.{spec_set.module_name} = {spec_set.class_name}()
        
        # テスト用データ準備
        self.test_data = {{
            "valid_input": "テスト用の有効な入力",
            "invalid_input": "",
            "boundary_input": "境界値テスト用データ"
        }}
        
        # モックオブジェクト準備
        self.mock_logger = Mock()
    
    def tearDown(self):
        """テスト後クリーンアップ"""
        # 一時ファイル削除など必要に応じて実装
        pass

'''

        # 各仕様のテストメソッド生成
        for spec in spec_set.specifications:
            test_content += self._generate_test_method(spec)
        
        test_content += '''

if __name__ == "__main__":
    unittest.main()
'''
        
        # ディレクトリ作成
        spec_set.test_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ファイル書き込み
        with open(spec_set.test_file_path, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        logger.info(f"📝 テストファイル生成: {spec_set.test_file_path}")
    
    def _generate_test_method(self, spec: TestSpecification) -> str:
        """テストメソッド生成"""
        method_content = f'''
    def {spec.test_name}(self):
        """
        {spec.description}
        
        Category: {spec.test_category}
        Priority: {spec.priority}
        Complexity: {spec.complexity}
        """
        # Given: {", ".join(spec.given)}
        # TODO: テスト前提条件の設定
        
        # When: {", ".join(spec.when)}
        # TODO: テスト対象の実行
        
        # Then: {", ".join(spec.then)}
        # TODO: 結果の検証
        
        # 実装例:
        # result = self.{spec.test_name.replace("test_", "")}
        # self.assertIsNotNone(result)
        # self.assertEqual(expected_value, result)
        
        self.fail("TODO: テスト実装が必要です - TDD Red Phase")
'''
        return method_content
    
    def _generate_implementation_skeleton(self, spec_set: SpecificationSet):
        """実装スケルトン生成"""
        impl_content = f'''#!/usr/bin/env python3
"""
{spec_set.class_name} - Issue #{spec_set.issue_number}
Generated by TDD Spec Generator

{spec_set.issue_title}

TODO: このファイルはTDD Green Phaseで実装してください
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

class {spec_set.class_name}:
    """
    {spec_set.issue_title}
    
    Issue #{spec_set.issue_number}の実装
    TDD仕様に基づく実装
    """
    
    def __init__(self):
        """初期化"""
        # TODO: 必要な初期化処理を実装
        pass
    
    # TODO: テスト仕様に基づいてメソッドを実装
    # 各テストケースに対応するメソッドを作成してください
    
    def process(self, input_data: Any) -> Any:
        """
        メイン処理メソッド
        
        Args:
            input_data: 入力データ
            
        Returns:
            処理結果
            
        Raises:
            ValueError: 無効な入力の場合
        """
        # TODO: TDD Green Phaseで最小実装
        raise NotImplementedError("TDD Green Phaseで実装してください")
'''
        
        # ディレクトリ作成
        spec_set.implementation_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 既存ファイルがない場合のみ作成
        if not spec_set.implementation_file_path.exists():
            with open(spec_set.implementation_file_path, "w", encoding="utf-8") as f:
                f.write(impl_content)
            
            logger.info(f"📄 実装スケルトン生成: {spec_set.implementation_file_path}")
        else:
            logger.info(f"⚠️  実装ファイル既存のためスキップ: {spec_set.implementation_file_path}")
    
    def _generate_tdd_readme(self, spec_set: SpecificationSet):
        """TDD README生成"""
        readme_content = f'''# TDD仕様書 - Issue #{spec_set.issue_number}

## 概要
**Issue**: #{spec_set.issue_number} - {spec_set.issue_title}
**モジュール**: {spec_set.module_name}
**クラス**: {spec_set.class_name}

## ファイル構成
- **テスト**: `{spec_set.test_file_path.relative_to(self.project_root)}`
- **実装**: `{spec_set.implementation_file_path.relative_to(self.project_root)}`

## TDD実行手順

### 1. Red Phase
```bash
make tdd-red
```
- テストを実行して失敗を確認
- 全テストが失敗することを確認

### 2. Green Phase  
```bash
make tdd-green
```
- 最小限の実装でテストを通す
- `{spec_set.implementation_file_path.name}`を編集

### 3. Refactor Phase
```bash
make tdd-refactor
```
- コード品質向上
- テストが通ることを確認

## テスト仕様

### テスト一覧
'''

        for i, spec in enumerate(spec_set.specifications, 1):
            readme_content += f'''
#### {i}. {spec.test_name}
- **説明**: {spec.description}
- **カテゴリ**: {spec.test_category}
- **優先度**: {spec.priority}
- **複雑度**: {spec.complexity}

**Given (前提条件)**:
{chr(10).join(f"- {given}" for given in spec.given)}

**When (実行条件)**:
{chr(10).join(f"- {when}" for when in spec.when)}

**Then (期待結果)**:
{chr(10).join(f"- {then}" for then in spec.then)}
'''

        readme_content += f'''

## セットアップ要件
{chr(10).join(f"- {req}" for req in spec_set.setup_requirements)}

## 依存関係
{chr(10).join(f"- {dep}" for dep in spec_set.dependencies)}

## 品質基準
- テストカバレッジ: 95%以上
- 複雑度: 10以下
- 全テストパス

---
*Generated by TDD Spec Generator - Issue #640 Phase 2*
*Generated at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
'''
        
        readme_path = self.templates_dir / f"TDD_SPEC_Issue_{spec_set.issue_number}.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        logger.info(f"📚 TDD仕様書生成: {readme_path}")

def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent
    
    generator = TDDSpecGenerator(project_root)
    
    logger.info("🚀 TDD仕様テンプレート生成開始 - Issue #640 Phase 2")
    
    # 仕様生成
    spec_set = generator.generate_specifications()
    
    if spec_set:
        print(f"✅ TDD仕様テンプレート生成完了")
        print(f"📋 テスト仕様数: {len(spec_set.specifications)}")
        print(f"📝 テストファイル: {spec_set.test_file_path}")
        print(f"📄 実装ファイル: {spec_set.implementation_file_path}")
        print(f"📚 仕様書: scripts/tdd_templates/TDD_SPEC_Issue_{spec_set.issue_number}.md")
        print()
        print("次のステップ:")
        print("1. `make tdd-red` でRed Phaseを開始")
        print("2. テストの失敗を確認")
        print("3. `make tdd-green` で最小実装")
    else:
        logger.error("❌ TDD仕様テンプレート生成失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()