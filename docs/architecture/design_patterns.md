# Kumihan-Formatter 設計パターン

## 概要

Kumihan-Formatterは、エンタープライズレベルの拡張性・保守性・セキュリティを実現するため、包括的な設計パターンを採用しています。本ドキュメントでは、プロジェクトで実装されている主要な設計パターンとその実装例、適用理由について詳細に説明します。

## コア設計パターン

### Factory Pattern - 統一ファクトリーシステム

#### 実装場所
- `kumihan_formatter/core/patterns/factories.py`
- `kumihan_formatter/core/ast_nodes/factories.py`

#### 概要
複数のパーサーやレンダラーの生成を統一インターフェースで管理し、依存関係注入(DI)と組み合わせて柔軟なオブジェクト生成を実現しています。

#### 実装例
```python
from kumihan_formatter.core.patterns.factories import get_service_factory, create_parser

# 統一ファクトリー経由でのパーサー生成
parser = create_parser("keyword", config=my_config)

# 複合パーサーの動的生成
composite_parser = factory.create_composite_parser(
    ["keyword", "block", "list"]
)
```

#### 適用メリット
- **拡張性**: 新しいパーサー/レンダラー種別の追加が容易
- **保守性**: オブジェクト生成ロジックの一元化
- **テスタビリティ**: モックオブジェクトの注入が簡単

#### アーキテクチャ図
```
ServiceFactory
├── ParserFactory
│   ├── KeywordParser
│   ├── BlockParser
│   └── ListParser
└── RendererFactory
    ├── HtmlRenderer
    └── MarkdownRenderer
```

### Strategy Pattern - 処理戦略の動的切り替え

#### 実装場所
- `kumihan_formatter/core/patterns/strategy.py`
- `kumihan_formatter/core/config/optimization/`

#### 概要
パース処理やレンダリング処理の戦略を実行時に選択・切り替えできる柔軟なシステムを提供しています。

#### 実装例
```python
from kumihan_formatter.core.patterns.strategy import StrategyManager

# 戦略管理システム
strategy_manager = StrategyManager()

# コンテンツに最適なパーシング戦略を自動選択
best_strategy = strategy_manager.select_parsing_strategy(content)
result = best_strategy.parse(content, context)

# 出力フォーマットに応じたレンダリング戦略選択
renderer = strategy_manager.select_rendering_strategy("html")
output = renderer.render(parsed_data, context)
```

#### 戦略種別
- **パーシング戦略**: Kumihan記法、Markdown、プレーンテキスト
- **レンダリング戦略**: HTML、Markdown、JSON出力
- **最適化戦略**: 性能重視、メモリ効率重視、品質重視

#### 適用メリット
- **アルゴリズム切り替え**: 実行時の動的戦略選択
- **性能最適化**: コンテンツ特性に応じた最適戦略
- **プラグイン対応**: サードパーティ戦略の容易な追加

### Observer Pattern - イベント駆動アーキテクチャ

#### 実装場所
- `kumihan_formatter/core/patterns/observer.py`
- `kumihan_formatter/core/patterns/event_bus.py`

#### 概要
処理進行状況のモニタリング、エラー通知、プラグインシステムなどを疎結合で実現するイベントバスシステムです。

#### 実装例
```python
from kumihan_formatter.core.patterns.observer import EventBus, Event, EventType

# イベントバス初期化
event_bus = EventBus()

# オブザーバー登録
event_bus.subscribe(EventType.PARSING_STARTED, progress_monitor)
event_bus.subscribe(EventType.PARSING_ERROR, error_handler)

# イベント発行
event = Event(
    event_type=EventType.PARSING_COMPLETED,
    source="keyword_parser",
    data={"duration": 0.15, "tokens": 1500}
)
event_bus.publish(event)
```

#### イベント種別
- **パース系**: 開始、完了、エラー
- **レンダリング系**: 開始、完了、エラー
- **検証系**: 検証失敗、警告
- **プラグイン系**: ロード、アンロード

#### 適用メリット
- **疎結合**: コンポーネント間の依存関係最小化
- **拡張性**: 新しいオブザーバーの容易な追加
- **モニタリング**: 処理状況の包括的監視

### Command Pattern - CLIコマンドシステム

#### 実装場所
- `kumihan_formatter/core/patterns/command.py`
- `kumihan_formatter/commands/`

#### 概要
CLI操作をコマンドオブジェクトとして抽象化し、実行、取り消し、キューイングを統一的に処理します。

#### 実装例
```python
from kumihan_formatter.core.patterns.command import CommandProcessor, ParseCommand

# コマンド作成
parse_cmd = ParseCommand(
    input_file="document.kumihan",
    output_file="output.html",
    config=config
)

# コマンド実行
processor = CommandProcessor()
result = processor.execute(parse_cmd)

# バッチ処理
processor.execute_batch([parse_cmd1, parse_cmd2, render_cmd])
```

#### コマンド種別
- **ParseCommand**: ファイル解析処理
- **RenderCommand**: レンダリング処理
- **ValidateCommand**: 構文検証
- **OptimizeCommand**: 最適化処理

#### 適用メリット
- **undo/redo**: 操作の取り消し・やり直し
- **バッチ処理**: 複数操作の一括実行
- **ログ記録**: 実行履歴の自動記録

### Builder Pattern - 設定オブジェクトの段階的構築

#### 実装場所
- `kumihan_formatter/core/ast_nodes/node_builder.py`
- `kumihan_formatter/core/config/`

#### 概要
複雑な設定オブジェクトやAST構造を段階的に構築するためのビルダーパターンを実装しています。

#### 実装例
```python
from kumihan_formatter.core.config.config_manager import ConfigBuilder

# 設定の段階的構築
config = (ConfigBuilder()
    .set_parsing_mode("strict")
    .enable_security_features()
    .set_cache_strategy("adaptive")
    .add_custom_validator(my_validator)
    .build())
```

## アーキテクチャパターン

### Layered Architecture - 階層アーキテクチャ

#### 構造概要
```
┌─────────────────────────────┐
│         CLI Layer           │  # コマンドライン インターフェース
├─────────────────────────────┤
│       Service Layer         │  # ビジネスロジック
├─────────────────────────────┤
│       Core Layer            │  # パース・レンダリング処理
├─────────────────────────────┤
│     Infrastructure Layer    │  # ファイルI/O、ログ、設定
└─────────────────────────────┘
```

#### 層別責務
- **CLI Layer**: ユーザーインターフェース、コマンド解析
- **Service Layer**: ワークフロー制御、ビジネスルール
- **Core Layer**: Kumihan記法処理、AST操作
- **Infrastructure Layer**: 外部リソース、横断的関心事

### Plugin Architecture - プラグインアーキテクチャ

#### 実装場所
- `kumihan_formatter/core/plugins/plugin_manager.py`
- プラグインインターフェース定義

#### 概要
コア機能を拡張するためのプラグインシステムを提供し、サードパーティ開発者による機能追加を支援します。

#### プラグイン種別
- **パーサープラグイン**: 新しい記法の追加
- **レンダラープラグイン**: 新しい出力形式
- **バリデータープラグイン**: カスタム検証ルール
- **最適化プラグイン**: 性能向上施策

### Microkernel Architecture - マイクロカーネルアーキテクチャ

#### 設計思想
最小限のコア機能（マイクロカーネル）を中心に、機能拡張をプラグインとして実装する柔軟なアーキテクチャです。

#### コア機能
- **基本パーサー**: Kumihan記法の基本解析
- **基本レンダラー**: HTML出力
- **設定管理**: 基本設定の読み込み・管理
- **プラグインローダー**: プラグインの動的ロード

## セキュリティ設計パターン

### Input Validation Pattern - 多層入力検証

#### 実装場所
- `kumihan_formatter/core/security/input_validation.py`
- `kumihan_formatter/core/security/input_validator.py`

#### 概要
複数層での入力検証により、セキュリティ脅威を段階的に除去するパターンです。

#### 検証レイヤー
```python
# Layer 1: 構文レベル検証
syntax_validator = SyntaxValidator()
syntax_result = syntax_validator.validate(input_text)

# Layer 2: セマンティック検証
semantic_validator = SemanticValidator()
semantic_result = semantic_validator.validate(parsed_ast)

# Layer 3: セキュリティ検証
security_validator = SecurityValidator()
security_result = security_validator.validate(content, context)
```

#### 検証項目
- **構文検証**: Kumihan記法の構文正当性
- **サイズ制限**: ファイルサイズ、ネスト深度制限
- **コンテンツ検証**: XSS、インジェクション攻撃パターン
- **リソース制限**: メモリ使用量、処理時間制限

#### 実装例
```python
from kumihan_formatter.core.security.input_validation import SecureInputValidator

# セキュア入力検証
validator = SecureInputValidator(
    max_file_size_mb=10,
    max_nesting_depth=20,
    enable_xss_protection=True,
    enable_injection_protection=True
)

# 包括的検証実行
validation_result = validator.validate_comprehensive(
    input_content=user_input,
    content_type="kumihan",
    security_context=context
)

if not validation_result.is_valid:
    raise SecurityError(validation_result.error_message)
```

### Sanitization Pattern - データサニタイゼーション

#### 実装場所
- `kumihan_formatter/core/security/sanitizer.py`

#### 概要
外部入力データを安全な形式に変換し、潜在的な脅威を無害化するパターンです。

#### サニタイゼーション段階
```python
# 段階1: 基本サニタイゼーション
sanitized_content = basic_sanitizer.sanitize(raw_input)

# 段階2: フォーマット特有サニタイゼーション
format_sanitized = format_sanitizer.sanitize(sanitized_content, "html")

# 段階3: コンテキスト依存サニタイゼーション
final_content = context_sanitizer.sanitize(
    format_sanitized, 
    context={"output_format": "html", "trusted_source": False}
)
```

### Secure Error Handling Pattern - セキュアエラーハンドリング

#### 実装場所
- `kumihan_formatter/core/security/secure_error_handling.py`

#### 概要
セキュリティに配慮したエラーハンドリングにより、機密情報の漏洩を防止します。

#### 実装例
```python
from kumihan_formatter.core.security.secure_error_handling import SecureErrorHandler

# セキュアエラーハンドラー設定
error_handler = SecureErrorHandler(
    debug_mode=False,  # 本番環境では詳細情報を隠蔽
    sanitize_stack_traces=True,
    log_security_events=True
)

try:
    process_user_input(user_data)
except Exception as e:
    # セキュアなエラー応答生成
    secure_response = error_handler.handle_error_safely(
        error=e,
        request_context=request_info,
        user_role="anonymous"
    )
    return secure_response
```

### Audit Log Pattern - 監査ログ

#### 実装場所
- `kumihan_formatter/core/security/secure_logging.py`
- `kumihan_formatter/core/logging/audit_logger.py`

#### 概要
セキュリティ関連イベントの包括的ログ記録により、インシデント調査と予防を支援します。

#### ログ記録項目
- **認証・認可イベント**: アクセス試行、権限変更
- **データアクセス**: ファイル読み込み、設定変更
- **エラーイベント**: 異常入力、処理失敗
- **システムイベント**: 起動・終了、プラグインロード

## パフォーマンス設計パターン

### Caching Pattern - 多層キャッシュシステム

#### 実装場所
- `kumihan_formatter/core/optimization/performance/cache_manager.py`

#### 概要
複数のキャッシュ戦略を組み合わせた高度なキャッシュシステムにより、処理性能を大幅に向上させます。

#### キャッシュ戦略
```python
from kumihan_formatter.core.optimization.performance.cache_manager import (
    HighPerformanceCacheManager,
    LRUStrategy,
    AdaptiveStrategy
)

# アダプティブキャッシュ戦略
adaptive_cache = HighPerformanceCacheManager(
    strategy=AdaptiveStrategy(max_entries=5000),
    max_memory_mb=100,
    enable_persistence=True
)

# キャッシュ統合利用
cached_result = adaptive_cache.get_with_factory(
    key=cache_key,
    value_factory=lambda: expensive_parse_operation(content),
    ttl_seconds=3600
)
```

#### キャッシュレベル
- **L1キャッシュ**: インメモリ、LRU戦略
- **L2キャッシュ**: ディスク永続化、LFU戦略  
- **L3キャッシュ**: 分散キャッシュ（将来拡張）

#### 戦略選択
- **LRU**: 一般的なアクセスパターン
- **LFU**: 頻繁アクセスパターン
- **TTL**: 時間依存データ
- **Adaptive**: 動的パターン学習

### Pool Pattern - リソースプール管理

#### 実装場所
- `kumihan_formatter/core/optimization/memory/memory_pool.py`
- `kumihan_formatter/core/optimization/memory/object_recycler.py`

#### 概要
頻繁に作成・破棄されるオブジェクトをプールで管理し、メモリ効率とGC負荷を最適化します。

#### プール種別
```python
# パーサーオブジェクトプール
parser_pool = ParserPool(
    pool_size=20,
    parser_factory=keyword_parser_factory,
    growth_policy="adaptive"
)

# メモリプール
memory_pool = MemoryPool(
    block_size=4096,
    initial_blocks=100,
    max_blocks=1000
)

# プール使用例
with parser_pool.acquire() as parser:
    result = parser.parse(content)
    # パーサーは自動的にプールに返却
```

### Pipeline Pattern - 処理パイプライン

#### 実装場所
- `kumihan_formatter/core/utilities/parallel_processor.py`
- パイプライン処理フレームワーク

#### 概要
複雑な処理を段階的なパイプラインに分割し、並列処理とストリーミング処理を実現します。

#### パイプライン構成
```python
from kumihan_formatter.core.utilities.parallel_processor import ProcessingPipeline

# 処理パイプライン構築
pipeline = (ProcessingPipeline()
    .add_stage("tokenize", tokenizer, parallel=True)
    .add_stage("parse", parser, parallel=True)
    .add_stage("validate", validator, parallel=False)
    .add_stage("optimize", optimizer, parallel=True)
    .add_stage("render", renderer, parallel=False))

# ストリーミング処理実行
for result in pipeline.process_stream(input_documents):
    handle_processed_document(result)
```

### Lazy Loading Pattern - 遅延読み込み最適化

#### 実装場所
- `kumihan_formatter/core/optimization/startup/lazy_loading.py`

#### 概要
必要になるまでリソースの読み込みを遅延させ、起動時間とメモリ使用量を最適化します。

#### 実装例
```python
from kumihan_formatter.core.optimization.startup.lazy_loading import LazyLoader

# 遅延読み込み設定
lazy_config = LazyLoader("config_manager", ConfigManager)
lazy_templates = LazyLoader("templates", TemplateManager)

# 実際の使用時に初期化
config = lazy_config.get()  # この時点でConfigManagerが初期化
templates = lazy_templates.get()  # この時点でTemplateManagerが初期化
```

## エラーハンドリングパターン

### Chain of Responsibility - エラー処理チェーン

#### 実装場所
- エラーハンドラーチェーン実装

#### 概要
異なるレベルのエラーハンドラーをチェーン状に連結し、適切なハンドラーにエラー処理を委譲します。

#### チェーン構成
```python
# エラーハンドラーチェーン構築
error_chain = (ErrorHandlerChain()
    .add_handler(ValidationErrorHandler())
    .add_handler(SecurityErrorHandler()) 
    .add_handler(BusinessLogicErrorHandler())
    .add_handler(SystemErrorHandler())
    .add_fallback(GenericErrorHandler()))

# エラー処理実行
try:
    process_user_request(request)
except Exception as error:
    response = error_chain.handle(error, context)
```

### Circuit Breaker Pattern - サーキットブレーカー

#### 概要
外部サービス呼び出しや重い処理において、連続的な失敗を検知して一時的にサービスを遮断するパターンです。

#### 実装例
```python
from kumihan_formatter.core.patterns.circuit_breaker import CircuitBreaker

# サーキットブレーカー設定
breaker = CircuitBreaker(
    failure_threshold=5,
    timeout_duration=30,
    success_threshold=3
)

@breaker.protected
def expensive_operation(data):
    return process_complex_document(data)

# 保護された実行
try:
    result = expensive_operation(user_data)
except CircuitBreakerOpen:
    return cached_fallback_response()
```

## 拡張性パターン

### Plugin Architecture - プラグインアーキテクチャ

#### 実装場所
- `kumihan_formatter/core/plugins/plugin_manager.py`

#### 概要
コア機能を変更せずに新機能を追加できるプラグインシステムです。

#### プラグインインターフェース
```python
from abc import ABC, abstractmethod

class ParserPlugin(ABC):
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """対応フォーマット一覧"""
        pass
    
    @abstractmethod
    def parse(self, content: str, context: dict) -> Any:
        """パース処理実装"""
        pass

# カスタムプラグイン実装
class CustomNotationPlugin(ParserPlugin):
    def get_supported_formats(self) -> List[str]:
        return ["custom", "extended"]
    
    def parse(self, content: str, context: dict) -> Any:
        return custom_parse_logic(content)

# プラグイン登録
plugin_manager.register_plugin("custom_parser", CustomNotationPlugin())
```

### Dependency Injection - 依存性注入

#### 実装場所
- `kumihan_formatter/core/patterns/dependency_injection.py`

#### 概要
コンポーネント間の依存関係を外部から注入し、テスタビリティと柔軟性を向上させます。

#### DI設定例
```python
from kumihan_formatter.core.patterns.dependency_injection import DIContainer

# DIコンテナ設定
container = DIContainer()
container.register(ParserInterface, KeywordParser)
container.register(RendererInterface, HtmlRenderer)
container.register(ConfigInterface, EnterpriseConfig)

# 依存関係自動解決
document_processor = container.resolve(DocumentProcessor)
```

## テストパターン

### Test Double Pattern - テスト二重化

#### 概要
テスト対象の外部依存を制御可能なテスト用オブジェクトで置き換えるパターンです。

#### 実装例
```python
# モックパーサー
class MockParser:
    def parse(self, content: str) -> ParseResult:
        return ParseResult(tokens=["mock", "tokens"])

# テスト用DIコンテナ
test_container = DIContainer()
test_container.register(ParserInterface, MockParser)

# テスト実行
def test_document_processing():
    processor = test_container.resolve(DocumentProcessor)
    result = processor.process("test content")
    assert result.is_valid
```

### Builder Pattern for Tests - テスト用ビルダー

#### 概要
複雑なテストデータを段階的に構築するビルダーパターンです。

#### 実装例
```python
class TestDataBuilder:
    def __init__(self):
        self._data = {}
    
    def with_content(self, content: str):
        self._data['content'] = content
        return self
    
    def with_config(self, config: dict):
        self._data['config'] = config
        return self
    
    def build(self) -> TestDocument:
        return TestDocument(**self._data)

# テストデータ構築
test_doc = (TestDataBuilder()
    .with_content("# Test #heading##")
    .with_config({"strict_mode": True})
    .build())
```

## パターン適用の利益

### 開発生産性向上
- **コード再利用**: 共通パターンによる開発効率化
- **保守性**: 構造化されたコードによる保守コスト削減  
- **拡張性**: 新機能追加の容易さ
- **テスタビリティ**: 自動テストの記述しやすさ

### 品質向上
- **可読性**: 一貫したパターンによるコード理解の向上
- **堅牢性**: エラーハンドリングパターンによる安定性
- **セキュリティ**: セキュリティパターンによる脅威対策
- **性能**: パフォーマンスパターンによる最適化

### チーム開発効率
- **学習コスト**: 確立されたパターンによる学習効率化
- **コミュニケーション**: 共通言語としてのパターン
- **レビュー効率**: パターン知識による効率的コードレビュー
- **オンボーディング**: 新メンバーの早期戦力化

### エンタープライズ対応
- **スケーラビリティ**: 大規模システムへの対応
- **運用性**: 監視・ログ・デバッグの容易さ
- **統合性**: 既存システムとの連携
- **標準準拠**: エンタープライズ標準への適合

## まとめ

Kumihan-Formatterは、確立された設計パターンを効果的に組み合わせることで、高品質・高性能・高セキュリティなテキスト処理システムを実現しています。これらのパターンは、プロジェクトの継続的な成長と、エンタープライズ環境での安定運用を支える重要な基盤となっています。

新機能の追加や既存機能の改善においても、これらのパターンを活用することで、品質を維持しながら効率的な開発を継続することができます。