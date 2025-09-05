# クラス依存関係マップ（最小雛形）

レイヤ構造と主な依存方向を示す。詳細は順次追加。

## レイヤ
- core/api: `FormatterAPI`, `FormatterCore`, `ManagerCoordinator`, `FormatterConfig`
- managers: `CoreManager`, `ProcessingManager`, `PluginManager`
- core/rendering: `HTMLFormatterCore` ほか
- core/parsing: `MainParser`, `CoreParser`, `SpecializedParser`
- core/utilities: 各種ユーティリティ

## 依存原則
- 上位→下位の一方向。下位から上位は参照しない。
- API 層はエントリーポイントのみ公開。

## データフロー（概要）
`FormatterAPI` → `FormatterCore` → `ManagerCoordinator` → `CoreManager` → (parsing/rendering)

