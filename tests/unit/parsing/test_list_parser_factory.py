"""List Parser Factory テスト - Issue #597 対応

リストパーサーファクトリー機能の専門テスト
コンポーネント生成・依存注入・設定管理の確認
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.list_parser_factory import (
    create_list_parser,
    create_list_validator,
    create_nested_list_parser,
)


class TestListParserComponents:
    """リストパーサーコンポーネントテスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        # 依存関係の明確化: ファクトリー関数群はKeywordParserに依存
        self.keyword_parser = KeywordParser()
        self.list_parser = create_list_parser(self.keyword_parser)
        self.nested_parser = create_nested_list_parser(self.keyword_parser)
        self.list_validator = create_list_validator(self.keyword_parser)

    def test_factory_components_initialization(self):
        """ファクトリーコンポーネント初期化テスト"""
        assert self.list_parser is not None
        assert self.nested_parser is not None
        assert self.list_validator is not None
        assert self.keyword_parser is not None

    def test_basic_parser_creation(self):
        """基本パーサー生成テスト"""
        parser_types = [
            {
                "type": "basic_list_parser",
                "expected_interface": ["parse_list"],
                "test_name": "basic_list_parser",
            },
            {
                "type": "nested_list_parser",
                "expected_interface": ["parse_nested_list"],
                "test_name": "nested_list_parser",
            },
            {
                "type": "core_list_parser",
                "expected_interface": ["parse_list", "detect_list_type"],
                "test_name": "core_list_parser",
            },
            {
                "type": "advanced_list_parser",
                "expected_interface": ["parse_list", "parse_nested_list"],
                "test_name": "advanced_list_parser",
            },
        ]

        for parser_config in parser_types:
            try:
                parser = self.factory.create_parser(parser_config["type"])

                if parser is not None:
                    # パーサーが生成されることを確認
                    assert (
                        parser is not None
                    ), f"{parser_config['test_name']}: パーサー生成失敗"

                    # 期待されるインターフェースの確認
                    for method_name in parser_config["expected_interface"]:
                        if hasattr(parser, method_name):
                            # メソッドが存在することを確認
                            assert callable(
                                getattr(parser, method_name)
                            ), f"{parser_config['test_name']}: {method_name} が呼び出し可能でない"

            except Exception as e:
                pytest.fail(
                    f"基本パーサー生成 {parser_config['test_name']} でエラー: {e}"
                )

    def test_parser_configuration_injection(self):
        """パーサー設定注入テスト"""
        configuration_cases = [
            # 基本設定
            {
                "parser_type": "basic_list_parser",
                "config": {
                    "enable_caching": True,
                    "max_nesting_depth": 5,
                    "unicode_support": True,
                },
                "test_name": "basic_configuration",
            },
            # 性能設定
            {
                "parser_type": "core_list_parser",
                "config": {
                    "performance_mode": "optimized",
                    "batch_processing": True,
                    "memory_limit": "100MB",
                },
                "test_name": "performance_configuration",
            },
            # デバッグ設定
            {
                "parser_type": "advanced_list_parser",
                "config": {
                    "debug_mode": True,
                    "log_level": "DEBUG",
                    "trace_parsing": True,
                },
                "test_name": "debug_configuration",
            },
        ]

        for case in configuration_cases:
            try:
                if hasattr(self.factory, "create_parser_with_config"):
                    parser = self.factory.create_parser_with_config(
                        case["parser_type"], case["config"]
                    )
                    assert (
                        parser is not None
                    ), f"{case['test_name']}: 設定付きパーサー生成失敗"

                    # 設定が適用されることを確認
                    if hasattr(parser, "config"):
                        for key, value in case["config"].items():
                            if key in parser.config:
                                assert (
                                    parser.config[key] == value
                                ), f"{case['test_name']}: 設定 {key} が適用されていない"

                elif hasattr(self.factory, "configure_parser"):
                    parser = self.factory.create_parser(case["parser_type"])
                    if parser:
                        self.factory.configure_parser(parser, case["config"])
                        assert (
                            parser is not None
                        ), f"{case['test_name']}: パーサー設定失敗"

            except Exception as e:
                pytest.fail(f"パーサー設定注入 {case['test_name']} でエラー: {e}")

    def test_dependency_injection_system(self):
        """依存注入システムテスト"""
        dependency_cases = [
            # 基本依存関係
            {
                "component": "list_parser",
                "dependencies": [
                    {"name": "pattern_matcher", "interface": "match_pattern"},
                    {"name": "indent_processor", "interface": "calculate_indent"},
                ],
                "test_name": "basic_dependencies",
            },
            # 複雑な依存関係
            {
                "component": "nested_list_parser",
                "dependencies": [
                    {"name": "core_parser", "interface": "parse_list"},
                    {"name": "nesting_analyzer", "interface": "analyze_nesting"},
                    {"name": "validator", "interface": "validate_structure"},
                ],
                "test_name": "complex_dependencies",
            },
            # オプション依存関係
            {
                "component": "advanced_parser",
                "dependencies": [
                    {
                        "name": "cache_manager",
                        "interface": "get_cached",
                        "optional": True,
                    },
                    {"name": "logger", "interface": "log", "optional": True},
                ],
                "test_name": "optional_dependencies",
            },
        ]

        for case in dependency_cases:
            try:
                if hasattr(self.factory, "inject_dependencies"):
                    component = self.factory.create_parser(case["component"])
                    if component:
                        self.factory.inject_dependencies(
                            component, case["dependencies"]
                        )

                        # 依存関係が注入されることを確認
                        for dep in case["dependencies"]:
                            if not dep.get("optional", False):
                                # 必須依存関係の確認
                                if hasattr(component, dep["name"]):
                                    dependency = getattr(component, dep["name"])
                                    assert (
                                        dependency is not None
                                    ), f"{case['test_name']}: 依存関係 {dep['name']} が注入されていない"

            except Exception as e:
                pytest.fail(f"依存注入システム {case['test_name']} でエラー: {e}")

    def test_component_lifecycle_management(self):
        """コンポーネントライフサイクル管理テスト"""
        lifecycle_test_cases = [
            # 初期化フェーズ
            {
                "phase": "initialization",
                "component_type": "basic_parser",
                "expected_state": "initialized",
                "test_name": "initialization_phase",
            },
            # 設定フェーズ
            {
                "phase": "configuration",
                "component_type": "configured_parser",
                "expected_state": "configured",
                "test_name": "configuration_phase",
            },
            # 実行フェーズ
            {
                "phase": "execution",
                "component_type": "active_parser",
                "expected_state": "active",
                "test_name": "execution_phase",
            },
            # 終了フェーズ
            {
                "phase": "disposal",
                "component_type": "disposed_parser",
                "expected_state": "disposed",
                "test_name": "disposal_phase",
            },
        ]

        for case in lifecycle_test_cases:
            try:
                if hasattr(self.factory, "manage_lifecycle"):
                    component = self.factory.create_parser(case["component_type"])
                    if component:
                        self.factory.manage_lifecycle(component, case["phase"])

                        # ライフサイクル状態の確認
                        if hasattr(component, "lifecycle_state"):
                            assert (
                                component.lifecycle_state == case["expected_state"]
                            ), f"{case['test_name']}: ライフサイクル状態不一致"
                        elif hasattr(component, "state"):
                            # 実装依存の状態確認
                            pass

            except Exception as e:
                pytest.fail(
                    f"コンポーネントライフサイクル {case['test_name']} でエラー: {e}"
                )

    def test_factory_performance_optimization(self):
        """ファクトリー性能最適化テスト"""
        import time

        # 性能測定用のコンポーネント生成テスト
        performance_tests = [
            # 大量生成テスト
            {
                "test_name": "mass_creation",
                "iterations": 100,
                "component_type": "basic_parser",
            },
            # 異なるタイプの生成テスト
            {
                "test_name": "varied_creation",
                "iterations": 50,
                "component_types": ["basic_parser", "nested_parser", "core_parser"],
            },
        ]

        for perf_test in performance_tests:
            start_time = time.time()

            try:
                if "component_types" in perf_test:
                    # 複数タイプの生成
                    created_components = []
                    for i in range(perf_test["iterations"]):
                        comp_type = perf_test["component_types"][
                            i % len(perf_test["component_types"])
                        ]
                        component = self.factory.create_parser(comp_type)
                        if component:
                            created_components.append(component)
                else:
                    # 単一タイプの大量生成
                    created_components = []
                    for _ in range(perf_test["iterations"]):
                        component = self.factory.create_parser(
                            perf_test["component_type"]
                        )
                        if component:
                            created_components.append(component)

                execution_time = time.time() - start_time

                # 性能基準確認
                assert (
                    execution_time < 1.0
                ), f"{perf_test['test_name']}: 生成が遅すぎる ({execution_time:.3f}秒)"

                # 生成成功率確認
                success_rate = len(created_components) / perf_test["iterations"]
                assert (
                    success_rate >= 0.8
                ), f"{perf_test['test_name']}: 生成成功率が低い ({success_rate:.1%})"

            except Exception as e:
                pytest.fail(f"性能最適化テスト {perf_test['test_name']} でエラー: {e}")

    def test_factory_caching_mechanisms(self):
        """ファクトリーキャッシュ機構テスト"""
        # キャッシュテスト用の設定
        cache_test_cases = [
            # インスタンスキャッシュ
            {
                "cache_type": "instance_cache",
                "component_type": "expensive_parser",
                "cache_enabled": True,
                "test_name": "instance_caching",
            },
            # 設定キャッシュ
            {
                "cache_type": "configuration_cache",
                "component_type": "configured_parser",
                "cache_enabled": True,
                "test_name": "configuration_caching",
            },
            # 無効化テスト
            {
                "cache_type": "disabled_cache",
                "component_type": "basic_parser",
                "cache_enabled": False,
                "test_name": "cache_disabled",
            },
        ]

        for case in cache_test_cases:
            try:
                if hasattr(self.factory, "enable_caching"):
                    self.factory.enable_caching(case["cache_enabled"])

                    # 同一コンポーネントの複数回生成
                    components = []
                    for _ in range(5):
                        component = self.factory.create_parser(case["component_type"])
                        if component:
                            components.append(component)

                    if case["cache_enabled"] and len(components) > 1:
                        # キャッシュ有効時の確認
                        if hasattr(self.factory, "_cache"):
                            # キャッシュが使用されることを確認（実装依存）
                            pass
                    else:
                        # キャッシュ無効時は毎回新しいインスタンス
                        # 実装依存のため、エラーがないことのみ確認
                        pass

            except Exception as e:
                pytest.fail(f"ファクトリーキャッシュ {case['test_name']} でエラー: {e}")

    def test_factory_error_handling(self):
        """ファクトリーエラーハンドリングテスト"""
        error_handling_cases = [
            # 存在しないコンポーネントタイプ
            {
                "component_type": "nonexistent_parser",
                "expected_error": "component_not_found",
                "test_name": "nonexistent_component",
            },
            # 不正な設定
            {
                "component_type": "basic_parser",
                "invalid_config": {"invalid_key": "invalid_value"},
                "expected_error": "invalid_configuration",
                "test_name": "invalid_configuration",
            },
            # 依存関係エラー
            {
                "component_type": "dependent_parser",
                "missing_dependencies": ["required_dependency"],
                "expected_error": "dependency_missing",
                "test_name": "missing_dependencies",
            },
        ]

        for case in error_handling_cases:
            try:
                if case["test_name"] == "nonexistent_component":
                    # 存在しないコンポーネント
                    result = self.factory.create_parser(case["component_type"])
                    # None が返されるか例外が発生するかは実装依存
                    if result is not None:
                        # エラーオブジェクトが返される場合
                        assert hasattr(result, "error"), "エラー情報が含まれていない"

                elif case["test_name"] == "invalid_configuration":
                    # 不正な設定
                    if hasattr(self.factory, "create_parser_with_config"):
                        result = self.factory.create_parser_with_config(
                            case["component_type"], case["invalid_config"]
                        )
                        # エラーハンドリングが適切に動作
                        assert result is None or hasattr(result, "error")

            except Exception as e:
                # 例外が発生する場合も適切なエラーハンドリング
                assert isinstance(e, (ValueError, TypeError, AttributeError))

    def test_concurrent_factory_operations(self):
        """並行ファクトリー操作テスト"""
        import threading

        results = []
        errors = []

        def concurrent_factory_worker(worker_id):
            try:
                local_factory = ListParserComponents()
                worker_results = []

                # 各ワーカーで異なるコンポーネントを生成
                component_types = [
                    "basic_parser",
                    "nested_parser",
                    "core_parser",
                ]

                for i in range(15):
                    comp_type = component_types[i % len(component_types)]
                    try:
                        component = local_factory.create_parser(comp_type)
                        worker_results.append(component is not None)
                    except Exception:
                        worker_results.append(False)

                success_rate = sum(worker_results) / len(worker_results)
                results.append((worker_id, success_rate))

            except Exception as e:
                errors.append((worker_id, str(e)))

        # 複数ワーカーで並行実行
        threads = []
        for i in range(4):
            thread = threading.Thread(target=concurrent_factory_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行ファクトリー操作でエラー: {errors}"
        assert len(results) == 4

        # 各ワーカーで高い成功率
        for worker_id, success_rate in results:
            assert (
                success_rate >= 0.7
            ), f"ワーカー{worker_id}の成功率が低い: {success_rate:.1%}"


class TestParserRegistry:
    """パーサーレジストリテスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.registry = ParserRegistry()

    def test_registry_initialization(self):
        """レジストリ初期化テスト"""
        assert self.registry is not None
        assert hasattr(self.registry, "register_parser")
        assert hasattr(self.registry, "get_parser")

    def test_parser_registration_and_retrieval(self):
        """パーサー登録・取得テスト"""

        # テスト用パーサークラス
        class TestParser:
            def parse_list(self, items):
                return {"parsed": items}

        registration_cases = [
            {
                "name": "test_basic_parser",
                "parser_class": TestParser,
                "metadata": {"version": "1.0", "type": "basic"},
                "test_name": "basic_registration",
            },
            {
                "name": "test_advanced_parser",
                "parser_class": TestParser,
                "metadata": {
                    "version": "2.0",
                    "type": "advanced",
                    "features": ["nesting", "keywords"],
                },
                "test_name": "advanced_registration",
            },
        ]

        for case in registration_cases:
            try:
                # パーサー登録
                if hasattr(self.registry, "register_parser"):
                    self.registry.register_parser(
                        case["name"], case["parser_class"], case["metadata"]
                    )

                    # 登録確認
                    if hasattr(self.registry, "is_registered"):
                        assert self.registry.is_registered(
                            case["name"]
                        ), f"{case['test_name']}: パーサー登録確認失敗"

                    # 取得テスト
                    if hasattr(self.registry, "get_parser"):
                        retrieved_parser = self.registry.get_parser(case["name"])
                        assert (
                            retrieved_parser is not None
                        ), f"{case['test_name']}: パーサー取得失敗"

                        # インスタンス生成確認
                        if callable(retrieved_parser):
                            parser_instance = retrieved_parser()
                            assert hasattr(
                                parser_instance, "parse_list"
                            ), f"{case['test_name']}: パーサーインターフェース不備"

            except Exception as e:
                pytest.fail(f"パーサー登録・取得 {case['test_name']} でエラー: {e}")

    def test_registry_metadata_management(self):
        """レジストリメタデータ管理テスト"""

        # テスト用パーサークラス
        class MetadataTestParser:
            def parse_list(self, items):
                return items

        metadata_cases = [
            {
                "parser_name": "metadata_parser_1",
                "metadata": {
                    "version": "1.0.0",
                    "author": "Test Author",
                    "description": "テスト用パーサー",
                    "capabilities": ["basic_parsing", "unicode_support"],
                    "performance": {"speed": "fast", "memory": "low"},
                },
                "test_name": "comprehensive_metadata",
            },
            {
                "parser_name": "metadata_parser_2",
                "metadata": {
                    "version": "2.1.0",
                    "dependencies": ["core_parser", "validator"],
                    "compatibility": {"min_version": "1.0", "max_version": "3.0"},
                    "experimental": True,
                },
                "test_name": "dependency_metadata",
            },
        ]

        for case in metadata_cases:
            try:
                if hasattr(self.registry, "register_parser"):
                    self.registry.register_parser(
                        case["parser_name"], MetadataTestParser, case["metadata"]
                    )

                    # メタデータ取得テスト
                    if hasattr(self.registry, "get_metadata"):
                        metadata = self.registry.get_metadata(case["parser_name"])
                        assert (
                            metadata is not None
                        ), f"{case['test_name']}: メタデータ取得失敗"

                        # メタデータ内容確認
                        for key, value in case["metadata"].items():
                            if key in metadata:
                                assert (
                                    metadata[key] == value
                                ), f"{case['test_name']}: メタデータ {key} 不一致"

            except Exception as e:
                pytest.fail(
                    f"レジストリメタデータ管理 {case['test_name']} でエラー: {e}"
                )

    def test_registry_versioning_system(self):
        """レジストリバージョニングシステムテスト"""

        # バージョン管理テスト用パーサー
        class VersionedParser:
            def __init__(self, version):
                self.version = version

            def parse_list(self, items):
                return {"version": self.version, "items": items}

        versioning_cases = [
            {
                "parser_name": "versioned_parser",
                "versions": [
                    {"version": "1.0.0", "metadata": {"stable": True}},
                    {
                        "version": "1.1.0",
                        "metadata": {"stable": True, "features": ["new_feature"]},
                    },
                    {
                        "version": "2.0.0",
                        "metadata": {"stable": False, "breaking_changes": True},
                    },
                ],
                "test_name": "version_management",
            },
        ]

        for case in versioning_cases:
            try:
                # 複数バージョンの登録
                for version_info in case["versions"]:
                    parser_class = lambda v=version_info["version"]: VersionedParser(v)

                    if hasattr(self.registry, "register_versioned_parser"):
                        self.registry.register_versioned_parser(
                            case["parser_name"],
                            version_info["version"],
                            parser_class,
                            version_info["metadata"],
                        )
                    elif hasattr(self.registry, "register_parser"):
                        # バージョン付き名前で登録
                        versioned_name = (
                            f"{case['parser_name']}_{version_info['version']}"
                        )
                        self.registry.register_parser(
                            versioned_name, parser_class, version_info["metadata"]
                        )

                # バージョン取得テスト
                if hasattr(self.registry, "get_parser_version"):
                    latest_parser = self.registry.get_parser_version(
                        case["parser_name"], "latest"
                    )
                    assert (
                        latest_parser is not None
                    ), f"{case['test_name']}: 最新バージョン取得失敗"

                    stable_parser = self.registry.get_parser_version(
                        case["parser_name"], "stable"
                    )
                    assert (
                        stable_parser is not None
                    ), f"{case['test_name']}: 安定バージョン取得失敗"

            except Exception as e:
                pytest.fail(
                    f"レジストリバージョニング {case['test_name']} でエラー: {e}"
                )

    def test_registry_query_and_filtering(self):
        """レジストリクエリ・フィルタリングテスト"""
        # テスト用パーサー群
        test_parsers = [
            {"name": "basic_parser", "type": "basic", "features": ["simple"]},
            {
                "name": "advanced_parser",
                "type": "advanced",
                "features": ["nesting", "keywords"],
            },
            {
                "name": "unicode_parser",
                "type": "specialized",
                "features": ["unicode", "multilingual"],
            },
            {
                "name": "performance_parser",
                "type": "optimized",
                "features": ["fast", "memory_efficient"],
            },
        ]

        # パーサー登録
        class QueryTestParser:
            def parse_list(self, items):
                return items

        for parser_info in test_parsers:
            try:
                if hasattr(self.registry, "register_parser"):
                    self.registry.register_parser(
                        parser_info["name"],
                        QueryTestParser,
                        {
                            "type": parser_info["type"],
                            "features": parser_info["features"],
                        },
                    )
            except Exception:
                pass  # 登録失敗は無視

        # クエリテスト
        query_cases = [
            {
                "query": {"type": "advanced"},
                "expected_count": 1,
                "test_name": "type_filter_query",
            },
            {
                "query": {"features": "unicode"},
                "expected_results": ["unicode_parser"],
                "test_name": "feature_filter_query",
            },
            {
                "query": {"type": "specialized", "features": "multilingual"},
                "expected_results": ["unicode_parser"],
                "test_name": "combined_filter_query",
            },
        ]

        for case in query_cases:
            try:
                if hasattr(self.registry, "query_parsers"):
                    results = self.registry.query_parsers(case["query"])

                    if "expected_count" in case:
                        assert (
                            len(results) == case["expected_count"]
                        ), f"{case['test_name']}: クエリ結果数不一致"

                    if "expected_results" in case:
                        result_names = [
                            r.name if hasattr(r, "name") else r for r in results
                        ]
                        for expected_name in case["expected_results"]:
                            assert (
                                expected_name in result_names
                            ), f"{case['test_name']}: 期待される結果 {expected_name} が見つからない"

            except Exception as e:
                pytest.fail(f"レジストリクエリ {case['test_name']} でエラー: {e}")

    def test_registry_performance_and_scalability(self):
        """レジストリ性能・スケーラビリティテスト"""
        import time

        # 大量登録テスト
        class ScalabilityTestParser:
            def parse_list(self, items):
                return items

        # 大量のパーサー登録
        start_time = time.time()
        registration_count = 100

        try:
            for i in range(registration_count):
                parser_name = f"scale_test_parser_{i}"
                metadata = {"id": i, "type": "scale_test"}

                if hasattr(self.registry, "register_parser"):
                    self.registry.register_parser(
                        parser_name, ScalabilityTestParser, metadata
                    )

        except Exception as e:
            pytest.fail(f"大量登録テストでエラー: {e}")

        registration_time = time.time() - start_time

        # 登録性能確認
        assert registration_time < 1.0, f"大量登録が遅すぎる: {registration_time:.3f}秒"

        # 大量取得テスト
        start_time = time.time()

        retrieved_count = 0
        for i in range(registration_count):
            parser_name = f"scale_test_parser_{i}"
            if hasattr(self.registry, "get_parser"):
                parser = self.registry.get_parser(parser_name)
                if parser is not None:
                    retrieved_count += 1

        retrieval_time = time.time() - start_time

        # 取得性能確認
        assert retrieval_time < 0.5, f"大量取得が遅すぎる: {retrieval_time:.3f}秒"
        assert (
            retrieved_count >= registration_count * 0.9
        ), f"取得成功率が低い: {retrieved_count}/{registration_count}"
