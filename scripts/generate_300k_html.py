#!/usr/bin/env python3
"""
300K行ファイルのHTML出力生成
実際の300K行ファイルを処理してHTMLファイルを生成
"""

import sys
import time
import psutil
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_300k_html():
    """300K行ファイルのHTML生成"""

    print("🚀 300K行ファイルHTML生成開始")
    print("=" * 60)

    # 300K行ファイル
    file_path = project_root / "samples" / "ultra_large" / "41_ultra_large_300k.txt"
    output_path = project_root / "300k_output.html"

    if not file_path.exists():
        print(f"❌ ファイルが存在しません: {file_path}")
        return False

    # ファイル情報
    file_size_mb = file_path.stat().st_size / 1024 / 1024
    with open(file_path, "rb") as f:
        line_count = sum(1 for _ in f)

    print(f"📄 ファイル情報:")
    print(f"  ファイル: {file_path.name}")
    print(f"  サイズ: {file_size_mb:.1f} MB")
    print(f"  行数: {line_count:,} 行")

    # メモリ監視開始
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024

    print(f"\n⚡ 最適化パーサーで処理開始...")
    print(f"初期メモリ: {initial_memory:.1f} MB")

    try:
        from kumihan_formatter.parser import Parser
        from kumihan_formatter.core.rendering.main_renderer import HTMLRenderer
        from kumihan_formatter.core.template_manager import TemplateManager

        start_time = time.time()

        # ファイル読み込み
        print("📖 ファイル読み込み中...")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        read_time = time.time() - start_time
        current_memory = process.memory_info().rss / 1024 / 1024
        print(f"  読み込み完了: {read_time:.1f}秒")
        print(f"  メモリ使用量: {current_memory:.1f} MB")

        # パーサー初期化
        print("🔧 パーサー初期化中...")
        parser = Parser()

        # 最適化解析実行
        print("⚡ 最適化解析実行中...")
        parse_start = time.time()

        nodes = parser.parse_optimized(content)

        parse_time = time.time() - parse_start
        current_memory = process.memory_info().rss / 1024 / 1024
        print(f"  解析完了: {parse_time:.1f}秒")
        print(f"  生成ノード数: {len(nodes):,}")
        print(f"  メモリ使用量: {current_memory:.1f} MB")

        # HTML生成
        print("🎨 HTMLレンダリング開始...")
        render_start = time.time()

        # ノードをHTMLレンダリング
        renderer = HTMLRenderer()
        body_content = renderer.render_nodes_optimized(nodes)

        # テンプレートマネージャーで完全なHTMLドキュメント生成
        template_manager = TemplateManager()
        html_content = template_manager.render_template(
            "base.html.j2",
            {
                "title": "300K行ファイル出力",
                "body_content": body_content,
                "has_toc": False,
                "css_vars": {},
                "metadata": {
                    "source_file": file_path.name,
                    "generation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
        )

        render_time = time.time() - render_start
        final_memory = process.memory_info().rss / 1024 / 1024
        total_time = time.time() - start_time

        print(f"  レンダリング完了: {render_time:.1f}秒")
        print(f"  最終メモリ: {final_memory:.1f} MB")

        # HTML保存
        print("💾 HTMLファイル保存中...")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        output_size_mb = output_path.stat().st_size / 1024 / 1024

        print(f"\n🎉 300K行ファイルHTML生成成功！")
        print("=" * 60)
        print(f"📊 処理結果:")
        print(f"  総処理時間: {total_time:.1f}秒 ({total_time/60:.1f}分)")
        print(f"  解析時間: {parse_time:.1f}秒")
        print(f"  レンダリング時間: {render_time:.1f}秒")
        print(f"  生成ノード数: {len(nodes):,}")
        print(f"  エラー数: {len(parser.get_errors())}")
        print(f"  出力ファイル: {output_path}")
        print(f"  出力サイズ: {output_size_mb:.1f} MB")
        print(f"  最終メモリ: {final_memory:.1f} MB")
        print(f"  処理速度: {line_count / parse_time:.0f} 行/秒")

        return True

    except Exception as e:
        print(f"❌ 処理エラー: {str(e)}")
        return False


def main():
    """メイン実行"""

    success = generate_300k_html()

    print(f"\n🏁 300K行ファイルHTML生成完了")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
