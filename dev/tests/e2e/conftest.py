"""
E2Eテスト用のpytestフィクスチャとセットアップ
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator
import os
import sys

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """プロジェクトルートパスを返す"""
    return PROJECT_ROOT


@pytest.fixture(scope="session") 
def test_workspace() -> Generator[Path, None, None]:
    """E2Eテスト用の一時作業領域を作成"""
    with tempfile.TemporaryDirectory(prefix="kumihan_e2e_") as temp_dir:
        workspace = Path(temp_dir)
        
        # バッチファイルとコマンドファイルをコピー
        copy_execution_files(workspace)
        
        # テストデータの準備
        setup_test_data(workspace)
        
        yield workspace


def copy_execution_files(workspace: Path) -> None:
    """実行ファイル（バッチ・コマンドファイル）をテスト領域にコピー"""
    project_root = PROJECT_ROOT
    
    # Windowsバッチファイル
    windows_dir = workspace / "WINDOWS"
    windows_dir.mkdir(exist_ok=True)
    
    windows_source = project_root / "WINDOWS"
    if windows_source.exists():
        for batch_file in windows_source.glob("*.bat"):
            shutil.copy2(batch_file, windows_dir)
    
    # macOSコマンドファイル  
    mac_dir = workspace / "MAC"
    mac_dir.mkdir(exist_ok=True)
    
    mac_source = project_root / "MAC"
    if mac_source.exists():
        for command_file in mac_source.glob("*.command"):
            shutil.copy2(command_file, mac_dir)
            # 実行権限を付与
            os.chmod(mac_dir / command_file.name, 0o755)


def setup_test_data(workspace: Path) -> None:
    """テスト用サンプルファイルを準備"""
    test_data_dir = workspace / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    # 基本テストファイル
    create_basic_test_file(test_data_dir / "basic_test.txt")
    create_comprehensive_test_file(test_data_dir / "comprehensive_test.txt")
    create_malformed_test_file(test_data_dir / "malformed_test.txt")
    create_large_test_file(test_data_dir / "large_test.txt")


def create_basic_test_file(file_path: Path) -> None:
    """基本的なテストファイルを作成"""
    content = """;;;見出し1
E2Eテスト用サンプル
;;;

このファイルはE2Eテストで使用されます。

;;;見出し2
基本機能のテスト
;;;

- 基本的なリスト項目
- ;;;太字;;; 太字リスト項目
- ;;;ハイライト color=#ffe6e6;;; ハイライトリスト項目

;;;太字
太字ブロックの例
;;;

;;;ハイライト color=#f0fff0
ハイライトブロックの例
;;;

;;;枠線
枠線ブロックの例
;;;
"""
    file_path.write_text(content, encoding='utf-8')


def create_comprehensive_test_file(file_path: Path) -> None:
    """包括的なテストファイルを作成"""
    content = """;;;見出し1
包括的機能テスト
;;;

;;;見出し2
複合記法テスト
;;;

;;;太字+ハイライト color=#e6f3ff
複合ブロックの例
;;;

;;;見出し3
折りたたみ機能
;;;

;;;折りたたみ
詳細な説明がここに入ります。
複数行の内容も正しく処理されることを確認します。
;;;

;;;ネタバレ
重要なネタバレ情報
;;;

;;;見出し2  
番号付きリスト
;;;

1. 最初の項目
2. 2番目の項目
3. 3番目の項目

;;;見出し2
中黒リスト
;;;

・中黒リスト項目1
・中黒リスト項目2
・中黒リスト項目3
"""
    file_path.write_text(content, encoding='utf-8')


def create_malformed_test_file(file_path: Path) -> None:
    """不正な記法を含むテストファイルを作成"""
    content = """;;;見出し1
不正記法テストファイル
;;;

これは意図的に不正な記法を含むファイルです。

;;;見出し2
不完全なブロック

;;;太字
内容

;;;ハイライト color=#ff0000
内容なし
;;;

;;;

;;;見出し3
処理終了
;;;
"""
    file_path.write_text(content, encoding='utf-8')


def create_large_test_file(file_path: Path) -> None:
    """大規模テストファイルを作成（パフォーマンステスト用）"""
    content_parts = []
    
    content_parts.append(""";;;見出し1
大規模ファイルテスト
;;;

このファイルはパフォーマンステスト用の大規模ファイルです。
""")
    
    # 大量のコンテンツを生成
    for i in range(100):
        section_content = f"""
;;;見出し2
セクション {i+1}
;;;

セクション {i+1} の内容です。

- リスト項目 1
- リスト項目 2  
- リスト項目 3

;;;太字
セクション {i+1} の重要事項
;;;

;;;ハイライト color=#f0f8ff
セクション {i+1} のハイライト情報
;;;

通常の段落が続きます。
複数行にわたる内容も含まれています。
"""
        content_parts.append(section_content)
    
    file_path.write_text("".join(content_parts), encoding='utf-8')


@pytest.fixture
def sample_test_file(test_workspace: Path) -> Path:
    """基本テストファイルのパスを返す"""
    return test_workspace / "test_data" / "basic_test.txt"


@pytest.fixture  
def comprehensive_test_file(test_workspace: Path) -> Path:
    """包括的テストファイルのパスを返す"""
    return test_workspace / "test_data" / "comprehensive_test.txt"


@pytest.fixture
def malformed_test_file(test_workspace: Path) -> Path:
    """不正記法テストファイルのパスを返す"""
    return test_workspace / "test_data" / "malformed_test.txt"


@pytest.fixture
def large_test_file(test_workspace: Path) -> Path:
    """大規模テストファイルのパスを返す"""
    return test_workspace / "test_data" / "large_test.txt"


@pytest.fixture
def output_directory(test_workspace: Path) -> Path:
    """出力ディレクトリを作成して返す"""
    output_dir = test_workspace / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir