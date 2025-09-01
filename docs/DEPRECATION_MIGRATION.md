# Deprecation Migration Guide

> 最終更新: 2025-09-01

本ガイドは、段階的廃止ポリシー（Phase 1→2→3）に伴う移行手順の要点をまとめたものです。

## 対象と代替

- core/parsing/markdown_parser.MarkdownParser → parsers/unified_markdown_parser.UnifiedMarkdownParser
- core/parsing/legacy_parser（互換API） → kumihan_formatter.parser（統合ファサード）または unified_api.KumihanFormatter
- parsers/specialized_parser の互換関数（parse_marker / parse_new_format / parse_ruby_format） → SpecializedParser クラスの各メソッド
- parsers/トップレベル再エクスポート → 各モジュールからの直接 import（Phase 2）
- commands/トップレベル再エクスポート → 各モジュールからの直接 import（Phase 2）
- unified_api.DummyParser / DummyRenderer → KumihanFormatterの `parse_text` / `convert_text`

## フェーズと期日

- Phase 1（〜2025-09-15）: 実行時 DeprecationWarning、ドキュメント整備、移行案内
- Phase 2（〜2025-10-15）: 互換エイリアスの非公開化・トップレベル再エクスポート停止
- Phase 3（〜2025-11-30）: レガシーAPIの削除

## 代表的な移行コード例

```python
# 旧: DummyParserでの解析
# from kumihan_formatter.unified_api import DummyParser
# nodes = DummyParser().parse(text)

# 新: KumihanFormatterでの解析
from kumihan_formatter.unified_api import KumihanFormatter
nodes = KumihanFormatter().parse_text(text)
```

```python
# 旧: トップレベル再エクスポートからのimport
# from kumihan_formatter.parsers import UnifiedListParser

# 新: モジュールを直接import
from kumihan_formatter.parsers.unified_list_parser import UnifiedListParser
```

```python
# 旧: specialized_parser の互換関数
# from kumihan_formatter.parsers.specialized_parser import parse_marker
# node = parse_marker(content)

# 新: クラスAPI
from kumihan_formatter.parsers.specialized_parser import SpecializedParser
node = SpecializedParser().parse_marker_content(content)
```

## 変更履歴（抜粋）

- Phase 1: DummyParser/DummyRenderer に DeprecationWarning を追加（#1314）
- Phase 2: parsers/commands のトップレベル再エクスポートを停止（#1303）
- Phase 3: markdown_parser / legacy_parser の削除、specialized_parser 互換関数の撤去（#1304/#1305/#1306）

---

ご不明点は Issues にてお知らせください。

