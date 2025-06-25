#!/usr/bin/env python3
"""
配布物内容の検証ツール

配布パッケージに必要なファイルが含まれ、不要なファイルが除外されていることを検証する。
"""

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Set, Tuple

# 配布物に必要なファイル・ディレクトリ
REQUIRED_FILES = {
    # 基本実行ファイル
    "WINDOWS/初回セットアップ.bat",
    "WINDOWS/変換ツール.bat", 
    "WINDOWS/サンプル実行.bat",
    "MAC/初回セットアップ.command",
    "MAC/変換ツール.command",
    "MAC/サンプル実行.command",
    
    # Pythonパッケージ
    "kumihan_formatter/__init__.py",
    "kumihan_formatter/cli.py",
    "kumihan_formatter/parser.py", 
    "kumihan_formatter/renderer.py",
    "kumihan_formatter/config.py",
    
    # 基本ドキュメント
    "README.html",
    "SPEC.html",
    "LICENSE",
    "index.html",
    
    # サンプルファイル
    "examples/01-quickstart.txt",
    "examples/02-basic.txt",
    "examples/index.html",
}

REQUIRED_DIRECTORIES = {
    "WINDOWS",
    "MAC", 
    "kumihan_formatter",
    "examples",
    "docs",
}

# 配布物に含まれてはいけないファイル・パターン
FORBIDDEN_PATTERNS = {
    # 開発ファイル
    "dev/",
    ".venv/",
    "__pycache__/",
    ".git/",
    ".github/", 
    ".pytest_cache/",
    
    # 設定ファイル
    ".distignore",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "pyproject.toml",
    ".gitignore",
    
    # 開発用ドキュメント
    "docs/analysis/",
    "docs/dev/",
    "docs/generated/",
    
    # 一時・ログファイル
    "*.log",
    "*.tmp",
    "*.pyc",
    "*_preview/",
}

# ユーザー使用パターン別の最小必要ファイル
USER_SCENARIOS = {
    "初心者": {
        "description": "バッチファイルから初回利用する一般ユーザー",
        "required_files": {
            "WINDOWS/初回セットアップ.bat",
            "WINDOWS/変換ツール.bat",
            "kumihan_formatter/",
            "examples/01-quickstart.txt",
            "README.html",
        }
    },
    "macOS_ユーザー": {
        "description": "macOSでcommandファイルから利用するユーザー", 
        "required_files": {
            "MAC/初回セットアップ.command",
            "MAC/変換ツール.command",
            "kumihan_formatter/",
            "examples/01-quickstart.txt",
            "README.html",
        }
    },
    "学習者": {
        "description": "Kumihan記法を学習したいユーザー",
        "required_files": {
            "SPEC.html",
            "examples/",
            "docs/QUICKSTART.html",
            "docs/SYNTAX_REFERENCE.html",
        }
    }
}


def extract_and_analyze_zip(zip_path: Path) -> Tuple[Set[str], Dict]:
    """
    ZIPファイルを展開して内容を分析
    
    Returns:
        Tuple[Set[str], Dict]: (ファイルパスのセット, 分析結果)
    """
    analysis = {
        "total_files": 0,
        "total_size": 0,
        "file_types": {},
        "directory_structure": {},
    }
    
    file_paths = set()
    
    # ZIPファイルサイズチェック
    zip_size = zip_path.stat().st_size
    if zip_size > 100 * 1024 * 1024:  # 100MB
        print("⚠️  大容量ファイルのため処理に時間がかかる可能性があります")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            for file_info in zipf.filelist:
                if not file_info.is_dir():
                    file_paths.add(file_info.filename)
                    analysis["total_files"] += 1
                    analysis["total_size"] += file_info.file_size
                    
                    # ファイル拡張子の集計
                    ext = Path(file_info.filename).suffix.lower()
                    if ext:
                        analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1
                    else:
                        analysis["file_types"]["(no extension)"] = analysis["file_types"].get("(no extension)", 0) + 1
    except zipfile.BadZipFile:
        raise ValueError(f"不正なZIPファイルです: {zip_path}")
    except PermissionError:
        raise ValueError(f"ZIPファイルへのアクセス権限がありません: {zip_path}")
    
    return file_paths, analysis


def check_required_files(file_paths: Set[str]) -> Tuple[List[str], List[str]]:
    """
    必要ファイルの存在チェック
    
    Returns:
        Tuple[List[str], List[str]]: (存在するファイル, 不足ファイル)
    """
    found = []
    missing = []
    
    for required_file in REQUIRED_FILES:
        # 完全一致を試す
        if required_file in file_paths:
            found.append(required_file)
            continue
        
        # パターンマッチングを試す（日本語ファイル名対応）
        file_found = False
        if required_file.endswith('.command') and 'MAC/' in required_file:
            # MACディレクトリの.commandファイルは文字化けの可能性があるので、
            # パターンマッチングで確認
            command_files = [fp for fp in file_paths if fp.startswith('MAC/') and fp.endswith('.command')]
            expected_name = required_file.split('/')[-1]
            
            if '初回セットアップ' in expected_name and any('初回' in cf or len(cf.split('/')[-1]) > 20 for cf in command_files):
                found.append(required_file)
                file_found = True
            elif '変換ツール' in expected_name and any('変換' in cf or '変' in cf for cf in command_files):
                found.append(required_file)
                file_found = True
            elif 'サンプル実行' in expected_name and any('サンプル' in cf or 'サ' in cf for cf in command_files):
                found.append(required_file)
                file_found = True
        
        if not file_found:
            missing.append(required_file)
    
    return found, missing


def check_required_directories(file_paths: Set[str]) -> Tuple[List[str], List[str]]:
    """
    必要ディレクトリの存在チェック
    
    Returns:
        Tuple[List[str], List[str]]: (存在するディレクトリ, 不足ディレクトリ)
    """
    found_dirs = set()
    for file_path in file_paths:
        path_parts = Path(file_path).parts
        if path_parts:
            found_dirs.add(path_parts[0])
    
    found = []
    missing = []
    
    for required_dir in REQUIRED_DIRECTORIES:
        if required_dir in found_dirs:
            found.append(required_dir)
        else:
            missing.append(required_dir)
    
    return found, missing


def check_forbidden_files(file_paths: Set[str]) -> List[str]:
    """
    禁止ファイルの存在チェック
    
    Returns:
        List[str]: 含まれるべきでないファイルのリスト
    """
    forbidden = []
    
    for file_path in file_paths:
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.endswith('/'):
                # ディレクトリパターン
                if file_path.startswith(pattern):
                    forbidden.append(file_path)
                    break
            elif '*' in pattern:
                # ワイルドカードパターン
                import fnmatch
                if fnmatch.fnmatch(file_path, pattern):
                    forbidden.append(file_path)
                    break
            else:
                # 完全一致
                if pattern in file_path:
                    forbidden.append(file_path)
                    break
    
    return forbidden


def check_user_scenarios(file_paths: Set[str]) -> Dict:
    """
    ユーザーシナリオ別の必要ファイルチェック
    
    Returns:
        Dict: シナリオ別の検証結果
    """
    results = {}
    
    for scenario_name, scenario in USER_SCENARIOS.items():
        missing = []
        for required in scenario["required_files"]:
            # ディレクトリの場合は配下にファイルがあるかチェック
            if required.endswith('/'):
                has_files = any(fp.startswith(required) for fp in file_paths)
                if not has_files:
                    missing.append(required)
            else:
                if required not in file_paths:
                    missing.append(required)
        
        results[scenario_name] = {
            "description": scenario["description"],
            "missing_files": missing,
            "usable": len(missing) == 0
        }
    
    return results


def generate_report(zip_path: Path, file_paths: Set[str], analysis: Dict, 
                   required_files: Tuple[List[str], List[str]],
                   required_dirs: Tuple[List[str], List[str]],
                   forbidden: List[str],
                   user_scenarios: Dict,
                   format_type: str = "text") -> str:
    """検証レポートの生成"""
    
    if format_type == "json":
        report_data = {
            "zip_file": str(zip_path),
            "analysis": analysis,
            "required_files": {
                "found": required_files[0],
                "missing": required_files[1]
            },
            "required_directories": {
                "found": required_dirs[0], 
                "missing": required_dirs[1]
            },
            "forbidden_files": forbidden,
            "user_scenarios": user_scenarios,
            "overall_status": "PASS" if not required_files[1] and not required_dirs[1] and not forbidden else "FAIL"
        }
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    # テキスト形式のレポート
    report = []
    report.append(f"📦 配布物検証レポート")
    report.append(f"=" * 50)
    report.append(f"対象: {zip_path.name}")
    report.append(f"ファイル数: {analysis['total_files']}")
    report.append(f"総サイズ: {analysis['total_size']:,} bytes")
    report.append("")
    
    # 必要ファイルチェック
    report.append("✅ 必要ファイルチェック")
    report.append("-" * 30)
    if required_files[1]:  # 不足ファイルがある
        report.append(f"❌ 不足ファイル ({len(required_files[1])}個):")
        for missing in required_files[1]:
            report.append(f"   - {missing}")
    else:
        report.append("✅ 全ての必要ファイルが含まれています")
    report.append("")
    
    # 必要ディレクトリチェック
    report.append("📁 必要ディレクトリチェック")
    report.append("-" * 30)
    if required_dirs[1]:  # 不足ディレクトリがある
        report.append(f"❌ 不足ディレクトリ ({len(required_dirs[1])}個):")
        for missing in required_dirs[1]:
            report.append(f"   - {missing}/")
    else:
        report.append("✅ 全ての必要ディレクトリが含まれています")
    report.append("")
    
    # 禁止ファイルチェック
    report.append("🚫 禁止ファイルチェック")
    report.append("-" * 30)
    if forbidden:
        report.append(f"❌ 含まれるべきでないファイル ({len(forbidden)}個):")
        for fb in forbidden[:10]:  # 最大10個まで表示
            report.append(f"   - {fb}")
        if len(forbidden) > 10:
            report.append(f"   ... 他 {len(forbidden) - 10}個")
    else:
        report.append("✅ 禁止ファイルは含まれていません")
    report.append("")
    
    # ユーザーシナリオチェック
    report.append("👤 ユーザーシナリオチェック")
    report.append("-" * 30)
    for scenario_name, result in user_scenarios.items():
        status = "✅" if result["usable"] else "❌"
        report.append(f"{status} {scenario_name}: {result['description']}")
        if result["missing_files"]:
            for missing in result["missing_files"]:
                report.append(f"     不足: {missing}")
    report.append("")
    
    # ファイル形式統計
    report.append("📊 ファイル形式統計")
    report.append("-" * 30)
    for ext, count in sorted(analysis["file_types"].items(), key=lambda x: x[1], reverse=True):
        report.append(f"   {ext}: {count}個")
    report.append("")
    
    # 総合判定
    overall_pass = not required_files[1] and not required_dirs[1] and not forbidden
    status = "✅ PASS" if overall_pass else "❌ FAIL"
    report.append(f"🎯 総合判定: {status}")
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="配布物内容の検証ツール")
    parser.add_argument("zip_file", help="検証するZIPファイルのパス")
    parser.add_argument("--format", choices=["text", "json"], default="text", 
                       help="出力形式 (default: text)")
    parser.add_argument("--output", "-o", help="出力ファイル (指定しない場合は標準出力)")
    
    args = parser.parse_args()
    
    zip_path = Path(args.zip_file)
    if not zip_path.exists():
        print(f"❌ エラー: ZIPファイルが見つかりません: {zip_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # ZIPファイルを分析
        file_paths, analysis = extract_and_analyze_zip(zip_path)
        
        # 各種チェック実行
        required_files = check_required_files(file_paths)
        required_dirs = check_required_directories(file_paths)
        forbidden = check_forbidden_files(file_paths)
        user_scenarios = check_user_scenarios(file_paths)
        
        # レポート生成
        report = generate_report(
            zip_path, file_paths, analysis,
            required_files, required_dirs, forbidden, user_scenarios,
            args.format
        )
        
        # 出力
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ レポートを出力しました: {args.output}")
        else:
            print(report)
        
        # 検証結果に基づく終了コード
        if required_files[1] or required_dirs[1] or forbidden:
            sys.exit(1)  # 検証失敗
        else:
            sys.exit(0)  # 検証成功
            
    except Exception as e:
        print(f"❌ エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()