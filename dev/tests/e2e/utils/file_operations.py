"""
ファイル操作関連のユーティリティ関数
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
import stat


def create_test_files_with_permissions(base_dir: Path) -> Dict[str, Path]:
    """様々な権限設定のテストファイルを作成"""
    test_files = {}
    
    # 通常のファイル
    normal_file = base_dir / "normal_test.txt"
    normal_file.write_text("通常のテストファイル", encoding='utf-8')
    test_files['normal'] = normal_file
    
    # 読み取り専用ファイル
    readonly_file = base_dir / "readonly_test.txt"
    readonly_file.write_text("読み取り専用テストファイル", encoding='utf-8')
    readonly_file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)  # 読み取り専用
    test_files['readonly'] = readonly_file
    
    # 空のファイル
    empty_file = base_dir / "empty_test.txt"
    empty_file.touch()
    test_files['empty'] = empty_file
    
    # 非常に長いファイル名
    long_name = "very_long_filename_" + "x" * 100 + ".txt"
    long_name_file = base_dir / long_name
    long_name_file.write_text("長いファイル名のテスト", encoding='utf-8')
    test_files['long_name'] = long_name_file
    
    # 特殊文字を含むファイル名
    special_char_file = base_dir / "特殊文字_test_123.txt"
    special_char_file.write_text("特殊文字ファイル名のテスト", encoding='utf-8')
    test_files['special_chars'] = special_char_file
    
    return test_files


def create_invalid_files(base_dir: Path) -> Dict[str, Path]:
    """無効なファイルを作成"""
    invalid_files = {}
    
    # バイナリファイル（.txt拡張子だが実際はバイナリ）
    binary_file = base_dir / "fake_text.txt"
    binary_file.write_bytes(b'\x00\x01\x02\x03\xFF\xFE\xFD')
    invalid_files['binary'] = binary_file
    
    # 不正なエンコーディング
    encoding_file = base_dir / "invalid_encoding.txt"
    with open(encoding_file, 'wb') as f:
        # UTF-8として無効なバイト列
        f.write(b'\xFF\xFE\x00\x00invalid\x80\x81\x82')
    invalid_files['invalid_encoding'] = encoding_file
    
    # 非常に大きなファイル（メモリテスト用）
    large_file = base_dir / "large_test.txt"
    create_large_file(large_file, size_mb=1)  # 1MBのファイル
    invalid_files['large'] = large_file
    
    return invalid_files


def create_large_file(file_path: Path, size_mb: int) -> None:
    """指定サイズの大きなファイルを作成"""
    content_block = "このブロックは繰り返されます。" * 100 + "\n"
    block_size = len(content_block.encode('utf-8'))
    
    target_bytes = size_mb * 1024 * 1024
    blocks_needed = target_bytes // block_size
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(";;;見出し1\n大規模ファイルテスト\n;;;\n\n")
        
        for i in range(blocks_needed):
            f.write(f"セクション {i+1}\n")
            f.write(content_block)
            
            # 定期的にKumihan記法を挿入
            if i % 50 == 0:
                f.write(f";;;見出し2\nセクション {i+1} 見出し\n;;;\n")
                f.write(f";;;太字\n重要な情報 {i+1}\n;;;\n")


def create_directory_structure_test(base_dir: Path) -> Dict[str, Path]:
    """複雑なディレクトリ構造でのテスト用ファイルを作成"""
    structure = {}
    
    # 深いネストのディレクトリ
    deep_dir = base_dir / "level1" / "level2" / "level3" / "level4"
    deep_dir.mkdir(parents=True, exist_ok=True)
    deep_file = deep_dir / "deep_test.txt"
    deep_file.write_text("深いディレクトリのテスト", encoding='utf-8')
    structure['deep'] = deep_file
    
    # スペースを含むディレクトリ名
    space_dir = base_dir / "directory with spaces"
    space_dir.mkdir(exist_ok=True)
    space_file = space_dir / "file in space dir.txt"
    space_file.write_text("スペース含むディレクトリのテスト", encoding='utf-8')
    structure['space_dir'] = space_file
    
    # 日本語ディレクトリ名
    japanese_dir = base_dir / "日本語ディレクトリ"
    japanese_dir.mkdir(exist_ok=True)
    japanese_file = japanese_dir / "日本語ファイル.txt"
    japanese_file.write_text("日本語ディレクトリ・ファイル名のテスト", encoding='utf-8')
    structure['japanese'] = japanese_file
    
    return structure


def cleanup_output_directory(output_dir: Path) -> None:
    """出力ディレクトリをクリーンアップ"""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def backup_and_restore_files(files: List[Path]):
    """ファイルのバックアップと復元を行うコンテキストマネージャー"""
    class BackupManager:
        def __init__(self, file_list):
            self.files = file_list
            self.backups = {}
        
        def __enter__(self):
            # バックアップを作成
            for file_path in self.files:
                if file_path.exists():
                    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                    shutil.copy2(file_path, backup_path)
                    self.backups[file_path] = backup_path
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            # バックアップから復元
            for original_path, backup_path in self.backups.items():
                if backup_path.exists():
                    shutil.copy2(backup_path, original_path)
                    backup_path.unlink()
    
    return BackupManager(files)


def check_file_locks(file_path: Path) -> Dict[str, bool]:
    """ファイルロック状況をチェック"""
    results = {}
    
    try:
        # 読み取り可能かチェック
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1)
        results['readable'] = True
    except Exception:
        results['readable'] = False
    
    try:
        # 書き込み可能かチェック
        with open(file_path, 'a', encoding='utf-8') as f:
            pass
        results['writable'] = True
    except Exception:
        results['writable'] = False
    
    return results


def simulate_disk_space_issue(target_dir: Path, reserve_mb: int = 10):
    """ディスク容量不足をシミュレート（テスト用の大きなファイルを作成）"""
    class DiskSpaceManager:
        def __init__(self, directory, reserve_size):
            self.directory = directory
            self.reserve_size = reserve_size
            self.dummy_file = directory / "disk_space_filler.tmp"
        
        def __enter__(self):
            # ダミーファイルでディスク容量を消費
            try:
                shutil.disk_usage(self.directory)
                # 実際の実装では、利用可能容量を計算して大きなファイルを作成
                # ここでは簡略化してスキップ
                pass
            except Exception:
                pass
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            # ダミーファイルを削除
            if self.dummy_file.exists():
                self.dummy_file.unlink()
    
    return DiskSpaceManager(target_dir, reserve_mb)


def get_file_info(file_path: Path) -> Dict[str, any]:
    """ファイルの詳細情報を取得"""
    if not file_path.exists():
        return {'error': 'File does not exist'}
    
    stat_info = file_path.stat()
    
    return {
        'size_bytes': stat_info.st_size,
        'size_kb': round(stat_info.st_size / 1024, 2),
        'size_mb': round(stat_info.st_size / (1024 * 1024), 2),
        'modified_time': stat_info.st_mtime,
        'permissions': oct(stat_info.st_mode)[-3:],
        'is_readable': os.access(file_path, os.R_OK),
        'is_writable': os.access(file_path, os.W_OK),
        'is_executable': os.access(file_path, os.X_OK),
    }