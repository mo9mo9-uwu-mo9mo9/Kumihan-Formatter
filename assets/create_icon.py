#!/usr/bin/env python3
"""
macOS用アイコン（.icns）生成スクリプト
基本的なアイコンを生成し、後で高品質なアイコンに置き換え可能
"""
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def create_base_icon(size=1024):
    """基本的なアイコンイメージを作成"""
    # 新しい画像を作成（背景は白）
    img = Image.new("RGBA", (size, size), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # 背景の角丸四角形
    margin = size // 10
    radius = size // 8

    # 角丸四角形の描画（グラデーション風）
    for i in range(radius):
        alpha = int(255 * (1 - i / radius))
        color = (52, 152, 219, alpha)  # 青色ベース
        x0, y0 = margin + i, margin + i
        x1, y1 = size - margin - i, size - margin - i
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius - i, fill=color)

    # メインの角丸四角形
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=(52, 152, 219, 255),
    )

    # テキストを追加
    text = "KF"
    font_size = size // 3

    # システムフォントを使用（フォントが見つからない場合はデフォルト）
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        font = ImageFont.load_default()

    # テキストのバウンディングボックスを取得
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # テキストを中央に配置
    x = (size - text_width) // 2
    y = (size - text_height) // 2

    # 影を追加
    shadow_offset = size // 50
    draw.text(
        (x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 128)
    )

    # メインテキスト
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    return img


def create_icns(output_path):
    """macOS用の.icnsファイルを作成"""
    # 一時ディレクトリの作成
    temp_dir = Path("temp_icon")
    temp_dir.mkdir(exist_ok=True)

    # 必要なサイズのアイコンを生成
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    base_icon = create_base_icon(1024)

    iconset_dir = temp_dir / "KumihanFormatter.iconset"
    iconset_dir.mkdir(exist_ok=True)

    for size in sizes:
        # 通常解像度
        icon = base_icon.resize((size, size), Image.Resampling.LANCZOS)
        icon.save(iconset_dir / f"icon_{size}x{size}.png")

        # Retina解像度（@2x）
        if size <= 512:
            icon_2x = base_icon.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
            icon_2x.save(iconset_dir / f"icon_{size}x{size}@2x.png")

    # iconutilを使用して.icnsファイルを作成
    try:
        subprocess.run(
            ["iconutil", "-c", "icns", "-o", output_path, str(iconset_dir)], check=True
        )
        print(f"アイコンファイルを作成しました: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"エラー: iconutilの実行に失敗しました: {e}")
        return False
    except FileNotFoundError:
        print("エラー: iconutilが見つかりません。macOSで実行してください。")
        return False
    finally:
        # クリーンアップ
        import shutil

        shutil.rmtree(temp_dir)

    return True


def main():
    """メイン処理"""
    # スクリプトのディレクトリを取得
    script_dir = Path(__file__).parent
    output_path = script_dir / "icon.icns"

    # Pillowのインストール確認
    try:
        import PIL
    except ImportError:
        print("Pillowがインストールされていません。")
        print("実行: pip install Pillow")
        return

    # アイコンの作成
    if create_icns(output_path):
        print("アイコンの作成が完了しました。")
        print("より高品質なアイコンが必要な場合は、デザインツールで作成してください。")
    else:
        print("アイコンの作成に失敗しました。")


if __name__ == "__main__":
    main()
