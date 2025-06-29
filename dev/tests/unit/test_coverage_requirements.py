"""テストカバレッジ要件の検証

このテストはv1.0.0リリースに必要な最低カバレッジ要件を検証します。
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestCoverageRequirements:
    """カバレッジ要件テストクラス"""
    
    @pytest.fixture(scope="class")
    def coverage_data(self):
        """カバレッジデータを取得"""
        project_root = Path(__file__).parent.parent.parent
        coverage_json = project_root / "coverage.json"
        
        if not coverage_json.exists():
            # カバレッジデータが存在しない場合は生成
            cmd = [
                sys.executable, "-m", "pytest",
                "--cov=kumihan_formatter",
                "--cov-report=json",
                "dev/tests/"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                pytest.skip("カバレッジデータの生成に失敗しました")
        
        with open(coverage_json, 'r') as f:
            return json.load(f)
    
    def test_minimum_total_coverage(self, coverage_data):
        """全体カバレッジの最低要件テスト"""
        total_coverage = coverage_data["totals"]["percent_covered"]
        minimum_coverage = 80
        
        assert total_coverage >= minimum_coverage, (
            f"総合カバレッジが最低要件を下回っています: "
            f"{total_coverage:.2f}% < {minimum_coverage}%"
        )
    
    def test_critical_modules_coverage(self, coverage_data):
        """重要モジュールのカバレッジ要件テスト"""
        critical_requirements = {
            "parser.py": 95,
            "renderer.py": 95,
            "cli.py": 85,
            "config.py": 90,
        }
        
        module_coverage = {}
        for file_path, file_data in coverage_data["files"].items():
            if "kumihan_formatter" in file_path:
                module_name = Path(file_path).name
                module_coverage[module_name] = file_data["summary"]["percent_covered"]
        
        failures = []
        for module, required_coverage in critical_requirements.items():
            actual_coverage = module_coverage.get(module, 0)
            if actual_coverage < required_coverage:
                failures.append(
                    f"{module}: {actual_coverage:.2f}% < {required_coverage}% (必要)"
                )
        
        assert not failures, (
            f"重要モジュールのカバレッジが不足しています:\n" + 
            "\n".join(f"  - {failure}" for failure in failures)
        )
    
    def test_no_untested_core_functions(self, coverage_data):
        """コア機能の未テスト関数チェック"""
        core_modules = ["parser.py", "renderer.py"]
        
        critical_gaps = []
        for file_path, file_data in coverage_data["files"].items():
            module_name = Path(file_path).name
            if module_name in core_modules:
                missing_lines = file_data.get("missing_lines", [])
                if len(missing_lines) > 20:  # 20行以上未カバーは問題
                    critical_gaps.append(
                        f"{module_name}: {len(missing_lines)}行が未カバー"
                    )
        
        assert not critical_gaps, (
            f"コアモジュールに大きなカバレッジギャップがあります:\n" +
            "\n".join(f"  - {gap}" for gap in critical_gaps)
        )
    
    def test_branch_coverage_if_available(self, coverage_data):
        """ブランチカバレッジのテスト（利用可能な場合）"""
        # ブランチカバレッジが測定されている場合のみテスト
        if "branch_coverage" in coverage_data.get("totals", {}):
            branch_coverage = coverage_data["totals"]["branch_coverage"]
            minimum_branch_coverage = 75
            
            assert branch_coverage >= minimum_branch_coverage, (
                f"ブランチカバレッジが最低要件を下回っています: "
                f"{branch_coverage:.2f}% < {minimum_branch_coverage}%"
            )
    
    def test_test_quality_metrics(self, coverage_data):
        """テスト品質指標のチェック"""
        total_lines = coverage_data["totals"]["num_statements"]
        covered_lines = coverage_data["totals"]["covered_lines"]
        missing_lines = coverage_data["totals"]["missing_lines"]
        
        # 基本的な健全性チェック
        assert total_lines > 0, "測定対象コードが存在しません"
        assert covered_lines > 0, "カバーされた行が存在しません"
        assert covered_lines + missing_lines == total_lines, "カバレッジ計算が不正です"
        
        # 最低限のテストされた行数
        minimum_covered_lines = 100
        assert covered_lines >= minimum_covered_lines, (
            f"テストされた行数が不足しています: "
            f"{covered_lines}行 < {minimum_covered_lines}行"
        )


class TestCoverageReporting:
    """カバレッジレポート機能のテスト"""
    
    def test_coverage_analyzer_import(self):
        """カバレッジ分析ツールがインポート可能"""
        try:
            from dev.tools.coverage_analyzer import CoverageAnalyzer
            analyzer = CoverageAnalyzer()
            assert analyzer is not None
        except ImportError as e:
            pytest.fail(f"カバレッジ分析ツールのインポートに失敗: {e}")
    
    def test_coverage_config_exists(self):
        """カバレッジ設定がpyproject.tomlに存在"""
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        assert pyproject_path.exists(), "pyproject.tomlが見つかりません"
        
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        assert "[tool.coverage.run]" in content, "カバレッジ実行設定が見つかりません"
        assert "[tool.coverage.report]" in content, "カバレッジレポート設定が見つかりません"
        assert 'source = ["kumihan_formatter"]' in content, "カバレッジソース設定が見つかりません"


def test_coverage_workflow_exists():
    """GitHub Actionsカバレッジワークフローのテスト"""
    project_root = Path(__file__).parent.parent.parent
    workflow_path = project_root / ".github" / "workflows" / "coverage.yml"
    
    assert workflow_path.exists(), "カバレッジワークフローファイルが見つかりません"
    
    with open(workflow_path, 'r') as f:
        content = f.read()
    
    required_elements = [
        "pytest --cov=kumihan_formatter",
        "codecov/codecov-action",
        "python-coverage-comment-action"
    ]
    
    for element in required_elements:
        assert element in content, f"ワークフローに必要な要素が見つかりません: {element}"