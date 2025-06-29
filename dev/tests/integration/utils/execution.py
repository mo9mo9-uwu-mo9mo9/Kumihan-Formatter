"""
実行関連のユーティリティ関数
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple, List, Optional
import platform


class ExecutionResult(NamedTuple):
    """実行結果を格納するクラス"""
    returncode: int
    stdout: str
    stderr: str
    execution_time: float
    output_files: List[Path]


class UserActionSimulator:
    """ユーザーアクションをシミュレートするクラス"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.project_root = workspace.parent.parent.parent.parent  # conftest.pyのPROJECT_ROOTと同じ計算
    
    def simulate_cli_conversion(self, input_file: Path, output_dir: Path, 
                                  skip_syntax_check: bool = False) -> ExecutionResult:
        """CLIでの変換をシミュレート"""
        start_time = time.time()
        
        # kumihan_formatterモジュールを直接実行
        cmd = [
            sys.executable, "-m", "kumihan_formatter.cli",
            str(input_file),
            "-o", str(output_dir),
            "--no-preview"  # ブラウザを開かない
        ]
        
        # 記法チェックスキップオプション
        if skip_syntax_check:
            cmd.append("--no-syntax-check")
        
        try:
            # Windowsでのエンコーディング問題を修正
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # デコードエラーを置換文字で対処
                timeout=60  # 1分でタイムアウト
            )
            
            execution_time = time.time() - start_time
            
            # 出力ファイルを検索
            output_files = []
            if output_dir.exists():
                output_files = list(output_dir.glob("*.html"))
            
            return ExecutionResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                output_files=output_files
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return ExecutionResult(
                returncode=-1,
                stdout="",
                stderr="Process timed out",
                execution_time=execution_time,
                output_files=[]
            )
    
    def simulate_batch_file_execution(self, batch_file: Path, input_file: Path) -> ExecutionResult:
        """バッチファイル実行をシミュレート（Windows）"""
        if platform.system() != "Windows":
            # Windows以外では実行をスキップ
            return ExecutionResult(
                returncode=-2,
                stdout="",
                stderr="Batch file execution skipped on non-Windows platform",
                execution_time=0.0,
                output_files=[]
            )
        
        start_time = time.time()
        
        # バッチファイルにファイルパスを引数として渡すことでD&Dをシミュレート
        cmd = [str(batch_file), str(input_file)]
        
        try:
            # Windowsでのエンコーディング問題を修正
            result = subprocess.run(
                cmd,
                cwd=batch_file.parent,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # デコードエラーを置換文字で対処
                timeout=120  # 2分でタイムアウト
            )
            
            execution_time = time.time() - start_time
            
            # 出力ファイルを検索
            output_files = []
            output_dir = input_file.parent / "dist"
            if output_dir.exists():
                output_files = list(output_dir.glob("*.html"))
            
            return ExecutionResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                output_files=output_files
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return ExecutionResult(
                returncode=-1,
                stdout="",
                stderr="Batch file execution timed out",
                execution_time=execution_time,
                output_files=[]
            )
    
    def simulate_command_file_execution(self, command_file: Path, input_file: Path) -> ExecutionResult:
        """コマンドファイル実行をシミュレート（macOS）"""
        if platform.system() != "Darwin":
            # macOS以外では実行をスキップ
            return ExecutionResult(
                returncode=-2,
                stdout="",
                stderr="Command file execution skipped on non-macOS platform",
                execution_time=0.0,
                output_files=[]
            )
        
        start_time = time.time()
        
        # コマンドファイルにファイルパスを引数として渡す
        cmd = [str(command_file), str(input_file)]
        
        try:
            # macOSでのエンコーディング問題を修正
            result = subprocess.run(
                cmd,
                cwd=command_file.parent,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # デコードエラーを置換文字で対処
                timeout=120  # 2分でタイムアウト
            )
            
            execution_time = time.time() - start_time
            
            # 出力ファイルを検索
            output_files = []
            output_dir = input_file.parent / "dist"
            if output_dir.exists():
                output_files = list(output_dir.glob("*.html"))
            
            return ExecutionResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                output_files=output_files
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return ExecutionResult(
                returncode=-1,
                stdout="",
                stderr="Command file execution timed out",
                execution_time=execution_time,
                output_files=[]
            )
    
    def simulate_drag_and_drop(self, input_file: Path, target_executable: Path) -> ExecutionResult:
        """ドラッグ&ドロップをシミュレート"""
        # プラットフォームに応じて適切な実行方法を選択
        if target_executable.suffix == ".bat":
            return self.simulate_batch_file_execution(target_executable, input_file)
        elif target_executable.suffix == ".command":
            return self.simulate_command_file_execution(target_executable, input_file)
        else:
            return ExecutionResult(
                returncode=-3,
                stdout="",
                stderr=f"Unsupported executable type: {target_executable.suffix}",
                execution_time=0.0,
                output_files=[]
            )


def run_multiple_conversions(simulator: UserActionSimulator, input_files: List[Path], output_dir: Path) -> List[ExecutionResult]:
    """複数ファイルの連続変換をテスト"""
    results = []
    
    for input_file in input_files:
        result = simulator.simulate_cli_conversion(input_file, output_dir)
        results.append(result)
        
        # 少し間隔を空ける
        time.sleep(0.1)
    
    return results


def measure_memory_usage(func, *args, **kwargs):
    """メモリ使用量を測定しながら関数を実行"""
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        result = func(*args, **kwargs)
        
        peak_memory = process.memory_info().rss
        memory_diff = peak_memory - initial_memory
        
        return result, memory_diff
        
    except ImportError:
        # psutilが利用できない場合は普通に実行
        return func(*args, **kwargs), 0