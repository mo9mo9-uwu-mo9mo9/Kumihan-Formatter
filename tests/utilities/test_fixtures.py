"""テストフィクスチャ

共通のテストデータとセットアップを提供する。
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def temp_dir():
    """一時ディレクトリを提供するフィクスチャ"""
    import shutil
    
    temp_path = Path(tempfile.mkdtemp())
    logger.debug(f"一時ディレクトリ作成: {temp_path}")
    
    yield temp_path
    
    # クリーンアップ
    try:
        if temp_path.exists():
            shutil.rmtree(temp_path)
            logger.debug(f"一時ディレクトリ削除: {temp_path}")
    except Exception as e:
        logger.warning(f"一時ディレクトリ削除失敗: {e}")


@pytest.fixture
def sample_kumihan_content():
    """サンプルKumihan記法コンテンツ"""
    return """
# 見出し1 #メインタイトル##
## 見出し2 ##サブタイトル###

# 太字 #重要なテキスト## と # イタリック #強調テキスト## の組み合わせ。

# 枠線 #
枠内のコンテンツ
複数行対応
##

- リストアイテム1
  - ネストアイテム1.1
  - ネストアイテム1.2
- リストアイテム2

1. 番号付きリスト1
2. 番号付きリスト2
   1. ネスト番号2.1
   2. ネスト番号2.2

# ルビ #漢字|かんじ## のテスト
"""


@pytest.fixture
def complex_kumihan_content():
    """複雑なKumihan記法コンテンツ"""
    return """
# 見出し1 #第1章: 導入##
## 見出し2 ##1.1 概要###
### 見出し3 ###1.1.1 背景####

# 太字 ## イタリック ## 下線 #複合装飾テキスト## ## ##

# 折りたたみ #
隠されたコンテンツ
- 項目1
- 項目2
##

```python
def example():
    '''コードブロック内のテキスト'''
    return "# 太字 #これは装飾されない##"
```

# 表 #
| ヘッダー1 | ヘッダー2 | ヘッダー3 |
|---------|---------|---------|
| データ1  | データ2  | データ3  |
| データ4  | データ5  | データ6  |
##

# 注釈 #これは注釈です##

[リンク](https://example.com)と# 太字 #リンク付きテキスト##
"""


@pytest.fixture
def edge_case_content():
    """エッジケースのコンテンツ"""
    return """
# 太字 #開始のみ
終了のみ##
# # 空マーカー ##
###連続ハッシュ###
# 太字 #
改行を
含む
テキスト
##
# 太字 # # イタリック #ネスト## ##
"""


@pytest.fixture
def parser_instance():
    """パーサーインスタンス"""
    from kumihan_formatter.core.parsing.main_parser import MainParser
    return MainParser()


@pytest.fixture
def renderer_instance():
    """レンダラーインスタンス"""
    from kumihan_formatter.renderer import MainRenderer
    return MainRenderer()


@pytest.fixture
def config_manager():
    """設定マネージャーインスタンス"""
    from kumihan_formatter.core.config.config_manager import ConfigManager
    return ConfigManager()


@pytest.fixture
def test_config():
    """テスト用設定"""
    return {
        "markers": {
            "太字": {"tag": "strong"},
            "イタリック": {"tag": "em"},
            "下線": {"tag": "u"},
            "枠線": {"tag": "div", "class": "box"},
        },
        "theme": "test",
        "css": {
            "max_width": "800px",
            "background_color": "#ffffff",
        },
        "performance": {
            "max_recursion_depth": 50,
            "max_nodes": 10000,
        },
        "validation": {
            "strict_mode": False,
            "auto_fix": True,
        },
    }


@pytest.fixture
def mock_logger(monkeypatch):
    """ロガーのモック"""
    class MockLogger:
        def __init__(self):
            self.messages: List[Dict[str, Any]] = []
        
        def debug(self, msg: str, *args, **kwargs):
            self.messages.append({"level": "DEBUG", "msg": msg})
        
        def info(self, msg: str, *args, **kwargs):
            self.messages.append({"level": "INFO", "msg": msg})
        
        def warning(self, msg: str, *args, **kwargs):
            self.messages.append({"level": "WARNING", "msg": msg})
        
        def error(self, msg: str, *args, **kwargs):
            self.messages.append({"level": "ERROR", "msg": msg})
        
        def clear(self):
            self.messages.clear()
        
        def get_messages(self, level: str = None) -> List[str]:
            if level:
                return [m["msg"] for m in self.messages if m["level"] == level]
            return [m["msg"] for m in self.messages]
    
    mock = MockLogger()
    
    # get_loggerをモック化
    def mock_get_logger(name: str):
        return mock
    
    monkeypatch.setattr(
        "kumihan_formatter.core.utilities.logger.get_logger",
        mock_get_logger
    )
    
    return mock


@pytest.fixture
def performance_monitor():
    """パフォーマンス監視用フィクスチャ"""
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.measurements: Dict[str, List[float]] = {}
        
        def start(self, name: str) -> float:
            """計測開始"""
            return time.time()
        
        def end(self, name: str, start_time: float) -> float:
            """計測終了"""
            elapsed = time.time() - start_time
            if name not in self.measurements:
                self.measurements[name] = []
            self.measurements[name].append(elapsed)
            return elapsed
        
        def get_average(self, name: str) -> float:
            """平均時間取得"""
            if name in self.measurements and self.measurements[name]:
                return sum(self.measurements[name]) / len(self.measurements[name])
            return 0.0
        
        def get_stats(self, name: str) -> Dict[str, float]:
            """統計情報取得"""
            if name not in self.measurements or not self.measurements[name]:
                return {"count": 0, "avg": 0, "min": 0, "max": 0}
            
            times = self.measurements[name]
            return {
                "count": len(times),
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
            }
    
    return PerformanceMonitor()


# テストデータ生成ヘルパー
def generate_test_content(lines: int = 100, complexity: str = "simple") -> str:
    """テスト用コンテンツを生成"""
    import random
    
    content = []
    
    if complexity == "simple":
        for i in range(lines):
            content.append(f"Line {i}: This is a simple test line.")
    
    elif complexity == "moderate":
        patterns = [
            "# 太字 #テキスト{}##",
            "## 見出し ##セクション{}###",
            "- リストアイテム{}",
            "通常のテキスト行{}",
        ]
        for i in range(lines):
            pattern = random.choice(patterns)
            content.append(pattern.format(i))
    
    elif complexity == "complex":
        patterns = [
            "# 太字 ## イタリック #複合{}## ##",
            "# ルビ #漢字{}|かんじ##",
            "```\nコード{}\n```",
            "- リスト{}\n  - ネスト{}",
        ]
        for i in range(lines):
            pattern = random.choice(patterns)
            content.append(pattern.format(i, i+1))
    
    return "\n".join(content)