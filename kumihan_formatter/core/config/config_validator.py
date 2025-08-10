"""
設定管理 - 検証機能

設定値検証・スキーマチェックの責任を担当
Issue #319対応 - config_manager.py から分離
"""

from typing import Any, Tuple

from .config_types import ValidationResult


class ConfigValidator:
    """
    設定値検証・スキーマチェック

    設計ドキュメント:
    - 仕様: /SPEC.md#出力形式オプション
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 設定詳細: /docs/configuration.md

    関連クラス:
    - EnhancedConfig: 検証対象の設定管理クラス
    - ValidationResult: 検証結果の格納

    責務:
    - 設定値の型・範囲チェック
    - 必須項目の存在確認
    - キーワード定義の妥当性検証
    """

    # 必須設定スキーマ
    SCHEMA = {
        "markers": {
            "type": dict,
            "required": True,
            "schema": {
                "*": {
                    "type": dict,
                    "required_keys": ["tag"],
                    "optional_keys": ["class", "summary"],
                }
            },
        },
        "theme": {"type": str, "required": False, "default": "default"},
        "font_family": {
            "type": str,
            "required": False,
            "default": "Hiragino Kaku Gothic ProN, Hiragino Sans, Yu Gothic, Meiryo, sans-serif",
        },
        "css": {
            "type": dict,
            "required": False,
            "schema": {
                "max_width": {"type": str},
                "background_color": {"type": str},
                "container_background": {"type": str},
                "text_color": {"type": str},
                "line_height": {"type": str},
            },
        },
        "themes": {
            "type": dict,
            "required": False,
            "schema": {
                "*": {
                    "type": dict,
                    "required_keys": ["name", "css"],
                    "schema": {"name": {"type": str}, "css": {"type": dict}},
                }
            },
        },
    }

    def validate(self, config: dict[str, Any]) -> ValidationResult:
        """設定をスキーマに対して検証"""
        errors: list[str] = []
        warnings: list[str] = []

        # 必須セクションのチェック
        for key, spec in self.SCHEMA.items():
            if spec.get("required", False) and key not in config:
                errors.append(f"Required section '{key}' is missing")
            elif key in config:
                section_errors, section_warnings = self._validate_section(key, config[key], spec)
                errors.extend(section_errors)
                warnings.extend(section_warnings)

        # 未知のトップレベルキーのチェック
        known_keys = set(self.SCHEMA.keys())
        unknown_keys = set(config.keys()) - known_keys
        for key in unknown_keys:
            warnings.append(f"Unknown configuration key: '{key}'")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _validate_section(
        self, section_name: str, section_data: Any, spec: dict[str, Any]
    ) -> Tuple[list[str], list[str]]:
        """設定セクションを検証"""
        errors: list[str] = []
        warnings: list[str] = []

        # 型検証
        expected_type = spec.get("type")
        if expected_type and not isinstance(section_data, expected_type):
            errors.append(f"Section '{section_name}' must be of type {expected_type.__name__}")
            return errors, warnings

        # dict型のスキーマ検証
        if expected_type == dict and "schema" in spec:
            schema = spec["schema"]

            # ワイルドカードスキーマの処理
            if "*" in schema:
                wildcard_spec = schema["*"]
                for key, value in section_data.items():
                    key_errors, key_warnings = self._validate_section(
                        f"{section_name}.{key}", value, wildcard_spec
                    )
                    errors.extend(key_errors)
                    warnings.extend(key_warnings)
            else:
                # 特定キーのスキーマ処理
                for key, sub_spec in schema.items():
                    if key in section_data:
                        key_errors, key_warnings = self._validate_section(
                            f"{section_name}.{key}", section_data[key], sub_spec
                        )
                        errors.extend(key_errors)
                        warnings.extend(key_warnings)

        # 必須キーの検証
        if "required_keys" in spec and isinstance(section_data, dict):
            for required_key in spec["required_keys"]:
                if required_key not in section_data:
                    errors.append(f"Required key '{required_key}' missing in {section_name}")

        return errors, warnings
