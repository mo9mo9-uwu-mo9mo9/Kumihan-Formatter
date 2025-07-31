#!/usr/bin/env python3
"""
Serena MCP Server最適化スクリプト
Issue #687対応 - プロセス管理・キャッシュ最適化・メモリ管理効率化
"""

import os
import sys
import subprocess
import shutil
import json
import psutil
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta
import argparse


class SerenaOptimizer:
    """Serena MCP Server最適化クラス"""
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.serena_dir = self.project_path / ".serena"
        self.cache_dir = self.serena_dir / "cache"
        self.memory_dir = self.serena_dir / "memories"
        
    def find_serena_processes(self) -> List[Dict[str, Any]]:
        """Serena MCPサーバープロセスを検出"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any('serena-mcp-server' in arg for arg in cmdline):
                    processes.append({
                        'pid': proc.info['pid'],
                        'cmdline': ' '.join(cmdline),
                        'create_time': datetime.fromtimestamp(proc.info['create_time']),
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
    
    def kill_duplicate_processes(self, keep_newest: bool = True) -> List[int]:
        """重複プロセスを終了（デフォルトで最新プロセスを保持）"""
        processes = self.find_serena_processes()
        if len(processes) <= 1:
            return []
        
        processes.sort(key=lambda x: x['create_time'], reverse=keep_newest)
        killed_pids = []
        
        for proc in processes[1:]:  # 最初の1つを除いて終了
            try:
                psutil.Process(proc['pid']).terminate()
                killed_pids.append(proc['pid'])
                print(f"プロセス終了: PID {proc['pid']} (メモリ: {proc['memory_mb']:.1f}MB)")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"プロセス終了失敗 PID {proc['pid']}: {e}")
        
        return killed_pids
    
    def analyze_cache_usage(self) -> Dict[str, Any]:
        """キャッシュディレクトリの使用状況分析"""
        if not self.cache_dir.exists():
            return {"status": "no_cache_dir"}
        
        total_size = 0
        file_count = 0
        old_files = []
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for file_path in self.cache_dir.rglob('*'):
            if file_path.is_file():
                stat = file_path.stat()
                size = stat.st_size
                total_size += size
                file_count += 1
                
                modified_time = datetime.fromtimestamp(stat.st_mtime)
                if modified_time < cutoff_date:
                    old_files.append({
                        'path': str(file_path.relative_to(self.cache_dir)),
                        'size': size,
                        'modified': modified_time
                    })
        
        return {
            'total_size_mb': total_size / 1024 / 1024,
            'file_count': file_count,
            'old_files': old_files,
            'old_files_size_mb': sum(f['size'] for f in old_files) / 1024 / 1024
        }
    
    def cleanup_cache(self, days_old: int = 7) -> int:
        """古いキャッシュファイルをクリーンアップ"""
        if not self.cache_dir.exists():
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0
        
        for file_path in self.cache_dir.rglob('*'):
            if file_path.is_file():
                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if modified_time < cutoff_date:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                    except OSError as e:
                        print(f"ファイル削除失敗 {file_path}: {e}")
        
        return cleaned_count
    
    def analyze_memory_files(self) -> Dict[str, Any]:
        """メモリファイルの分析"""
        if not self.memory_dir.exists():
            return {"status": "no_memory_dir"}
        
        memory_files = []
        total_size = 0
        
        for memory_file in self.memory_dir.glob('*.md'):
            stat = memory_file.stat()
            size = stat.st_size
            total_size += size
            
            # ファイル内容の重複チェック用にハッシュ取得
            try:
                content = memory_file.read_text(encoding='utf-8')
                content_hash = hash(content)
                word_count = len(content.split())
            except Exception:
                content_hash = None
                word_count = 0
            
            memory_files.append({
                'name': memory_file.stem,
                'path': str(memory_file),
                'size': size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'content_hash': content_hash,
                'word_count': word_count
            })
        
        # 重複検出
        hash_groups = {}
        for f in memory_files:
            if f['content_hash']:
                if f['content_hash'] not in hash_groups:
                    hash_groups[f['content_hash']] = []
                hash_groups[f['content_hash']].append(f)
        
        duplicates = [group for group in hash_groups.values() if len(group) > 1]
        
        return {
            'total_files': len(memory_files),
            'total_size_mb': total_size / 1024 / 1024,
            'files': memory_files,
            'duplicates': duplicates
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """最適化レポート生成"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'project_path': str(self.project_path),
            'processes': self.find_serena_processes(),
            'cache_analysis': self.analyze_cache_usage(),
            'memory_analysis': self.analyze_memory_files()
        }
        return report
    
    def optimize(self, kill_duplicates: bool = True, cleanup_cache: bool = True, 
                cache_days: int = 7) -> Dict[str, Any]:
        """総合最適化実行"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'killed_processes': [],
            'cleaned_cache_files': 0,
            'before': {},
            'after': {}
        }
        
        # 最適化前の状態
        results['before'] = self.generate_report()
        
        # 重複プロセス終了
        if kill_duplicates:
            results['killed_processes'] = self.kill_duplicate_processes()
        
        # キャッシュクリーンアップ
        if cleanup_cache:
            results['cleaned_cache_files'] = self.cleanup_cache(cache_days)
        
        # 最適化後の状態
        results['after'] = self.generate_report()
        
        return results


def main():
    parser = argparse.ArgumentParser(description='Serena MCP Server最適化ツール')
    parser.add_argument('--project', '-p', default=None, 
                       help='プロジェクトパス（デフォルト: カレントディレクトリ）')
    parser.add_argument('--report-only', '-r', action='store_true',
                       help='レポート生成のみ（最適化は実行しない）')
    parser.add_argument('--no-kill', action='store_true',
                       help='重複プロセス終了をスキップ')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='キャッシュクリーンアップをスキップ')
    parser.add_argument('--cache-days', type=int, default=7,
                       help='キャッシュファイル保持日数（デフォルト: 7日）')
    parser.add_argument('--output', '-o', 
                       help='結果出力ファイル（JSON形式）')
    
    args = parser.parse_args()
    
    optimizer = SerenaOptimizer(args.project)
    
    if args.report_only:
        result = optimizer.generate_report()
        print("=== Serena MCP Server状況レポート ===")
        print(f"プロジェクト: {result['project_path']}")
        print(f"実行中プロセス数: {len(result['processes'])}")
        
        for i, proc in enumerate(result['processes']):
            print(f"  プロセス{i+1}: PID {proc['pid']}, メモリ {proc['memory_mb']:.1f}MB")
        
        cache = result['cache_analysis']
        if cache.get('status') != 'no_cache_dir':
            print(f"キャッシュサイズ: {cache['total_size_mb']:.1f}MB ({cache['file_count']}ファイル)")
            print(f"古いファイル: {len(cache['old_files'])}個 ({cache['old_files_size_mb']:.1f}MB)")
        
        memory = result['memory_analysis']
        if memory.get('status') != 'no_memory_dir':
            print(f"メモリファイル: {memory['total_files']}個 ({memory['total_size_mb']:.1f}MB)")
            if memory['duplicates']:
                print(f"重複ファイル群: {len(memory['duplicates'])}群")
    else:
        result = optimizer.optimize(
            kill_duplicates=not args.no_kill,
            cleanup_cache=not args.no_cleanup,
            cache_days=args.cache_days
        )
        
        print("=== Serena MCP Server最適化結果 ===")
        print(f"終了プロセス数: {len(result['killed_processes'])}")
        print(f"クリーンアップファイル数: {result['cleaned_cache_files']}")
        
        before_processes = len(result['before']['processes'])
        after_processes = len(result['after']['processes'])
        print(f"プロセス数: {before_processes} → {after_processes}")
        
        before_cache = result['before']['cache_analysis']
        after_cache = result['after']['cache_analysis']
        if before_cache.get('status') != 'no_cache_dir':
            before_size = before_cache['total_size_mb']
            after_size = after_cache['total_size_mb']
            print(f"キャッシュサイズ: {before_size:.1f}MB → {after_size:.1f}MB "
                  f"({before_size - after_size:.1f}MB削減)")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        print(f"結果をファイルに出力: {args.output}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())