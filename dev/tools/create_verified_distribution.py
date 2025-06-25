#!/usr/bin/env python3
"""
検証付き配布物作成ツール

配布物の作成、検証、品質チェックを一体化して実行する。
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """
    コマンドを実行し、結果を表示
    
    Returns:
        bool: 成功した場合True
    """
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {description} 完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失敗:")
        print(f"   コマンド: {' '.join(cmd)}")
        print(f"   終了コード: {e.returncode}")
        if e.stdout:
            print(f"   標準出力: {e.stdout}")
        if e.stderr:
            print(f"   エラー出力: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="検証付き配布物作成ツール")
    parser.add_argument("--source-dir", default=".", help="ソースディレクトリ (default: .)")
    parser.add_argument("--output-dir", default="verified_distribution", 
                       help="出力ディレクトリ (default: verified_distribution)")
    parser.add_argument("--zip-name", default="kumihan-formatter-distribution",
                       help="ZIPファイル名 (default: kumihan-formatter-distribution)")
    parser.add_argument("--no-validation", action="store_true", 
                       help="検証をスキップ")
    parser.add_argument("--keep-temp", action="store_true",
                       help="一時ファイルを保持（デバッグ用）")
    
    args = parser.parse_args()
    
    source_path = Path(args.source_dir).resolve()
    output_path = Path(args.output_dir).resolve()
    
    print("📦 検証付き配布物作成ツール")
    print("=" * 50)
    print(f"ソース: {source_path}")
    print(f"出力先: {output_path}")
    print("")
    
    # Step 1: 配布物作成
    zip_dist_cmd = [
        sys.executable, "-m", "kumihan_formatter.cli", "zip-dist",
        str(source_path),
        "-o", str(output_path),
        "--zip-name", args.zip_name,
        "--no-preview"
    ]
    
    if not run_command(zip_dist_cmd, "配布物作成"):
        print("❌ 配布物作成に失敗しました")
        sys.exit(1)
    
    # Step 2: ZIPファイルパスの特定
    zip_file = output_path / f"{args.zip_name}.zip"
    if not zip_file.exists():
        print(f"❌ ZIPファイルが見つかりません: {zip_file}")
        sys.exit(1)
    
    print(f"📁 作成されたZIPファイル: {zip_file}")
    zip_size = zip_file.stat().st_size
    print(f"   サイズ: {zip_size:,} bytes ({zip_size / 1024 / 1024:.2f} MB)")
    print("")
    
    # Step 3: 配布物検証
    if not args.no_validation:
        validator_path = Path(__file__).parent / "distribution_validator.py"
        if not validator_path.exists():
            print(f"❌ 検証ツールが見つかりません: {validator_path}")
            sys.exit(1)
        
        validation_cmd = [
            sys.executable, str(validator_path),
            str(zip_file),
            "--format", "text"
        ]
        
        print("🔍 配布物検証中...")
        try:
            result = subprocess.run(validation_cmd, capture_output=True, text=True)
            print(result.stdout)
            
            if result.returncode == 0:
                print("✅ 配布物検証成功")
            else:
                print("❌ 配布物検証失敗")
                if result.stderr:
                    print(f"エラー: {result.stderr}")
                sys.exit(1)
                
        except subprocess.CalledProcessError as e:
            print(f"❌ 検証実行エラー: {e}")
            sys.exit(1)
    else:
        print("⚠️  検証をスキップしました")
    
    print("")
    print("🎉 配布物作成・検証完了")
    print(f"📁 配布物: {zip_file}")
    print(f"📊 サイズ: {zip_size:,} bytes")
    
    # 使用方法のヒント
    print("")
    print("💡 配布物の使用方法:")
    print("   1. ZIPファイルをユーザーに配布")
    print("   2. ユーザーが展開後、WINDOWS/ または MAC/ フォルダのファイルを実行")
    print("   3. 初回セットアップ → 変換ツール の順で使用")


if __name__ == "__main__":
    main()