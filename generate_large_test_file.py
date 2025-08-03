#!/usr/bin/env python3
"""
Issue #759対応: 300K行大容量テストファイル生成スクリプト

パフォーマンステスト用の大容量Kumihanファイルを生成
- 300,000行のテストファイル
- 多様なKumihan記法を含む
- リアルな文書構造をシミュレート
"""

import random
from pathlib import Path


def generate_large_kumihan_file(output_path: Path, target_lines: int = 300000):
    """300K行の大容量Kumihanテストファイルを生成"""
    
    print(f"Generating {target_lines:,} line test file: {output_path}")
    
    # Kumihan記法のテンプレート
    templates = [
        # 見出し
        "# 見出し1 #セクション {section}##",
        "# 見出し2 #サブセクション {subsection}##",
        "# 見出し3 #詳細項目 {item}##",
        
        # 段落
        "これは段落テキストです。{content}を説明している内容です。",
        "詳細な説明が続きます。{detail}について詳しく解説します。",
        "重要なポイントは{point}です。注意深く理解してください。",
        
        # 太字・イタリック
        "# 太字 #重要な{keyword}##について説明します。",
        "# イタリック #強調したい{emphasis}##を示しています。",
        
        # リスト
        "- 項目1: {item1}",
        "- 項目2: {item2}",
        "- 項目3: {item3}",
        "  - サブ項目A: {subitem_a}",
        "  - サブ項目B: {subitem_b}",
        
        # 順序リスト
        "1. 手順1: {step1}",
        "2. 手順2: {step2}",
        "3. 手順3: {step3}",
        
        # ハイライト
        "# ハイライト #注意事項: {warning}##",
        "# ハイライト #ヒント: {tip}##",
        
        # コメント行
        "# コメント: {comment}",
        
        # 空行（構造化のため）
        "",
        
        # 複雑な記法組み合わせ
        "# 太字 #重要##かつ# イタリック #強調##された{combined}です。",
        "# ハイライト #警告: # 太字 #{alert}##に注意##してください。",
    ]
    
    # コンテンツ生成用のワード
    keywords = [
        "システム", "アプリケーション", "データベース", "ネットワーク", "セキュリティ",
        "パフォーマンス", "最適化", "設計", "実装", "テスト", "デプロイ", "監視",
        "バックアップ", "復旧", "メンテナンス", "アップデート", "設定", "構成"
    ]
    
    details = [
        "基本的な概念", "詳細な仕様", "実装方法", "ベストプラクティス", "注意点",
        "トラブルシューティング", "パフォーマンス向上", "セキュリティ対策", "運用手順"
    ]
    
    points = [
        "効率性", "安全性", "可用性", "拡張性", "保守性", "互換性", "使いやすさ"
    ]
    
    with open(output_path, 'w', encoding='utf-8') as file:
        section_count = 0
        subsection_count = 0
        item_count = 0
        
        for line_num in range(target_lines):
            # 進捗表示
            if line_num % 10000 == 0:
                print(f"Progress: {line_num:,}/{target_lines:,} lines ({line_num/target_lines*100:.1f}%)")
            
            # 構造化された内容生成
            if line_num % 1000 == 0:
                section_count += 1
                template = templates[0]  # 見出し1
                content = template.format(section=section_count)
                
            elif line_num % 200 == 0:
                subsection_count += 1
                template = templates[1]  # 見出し2
                content = template.format(subsection=subsection_count)
                
            elif line_num % 50 == 0:
                item_count += 1
                template = templates[2]  # 見出し3
                content = template.format(item=item_count)
                
            else:
                # ランダムなテンプレート選択
                template = random.choice(templates)
                
                # テンプレートに応じた内容生成
                content = template.format(
                    content=random.choice(keywords),
                    detail=random.choice(details),
                    point=random.choice(points),
                    keyword=random.choice(keywords),
                    emphasis=random.choice(keywords),
                    item1=random.choice(keywords),
                    item2=random.choice(details),
                    item3=random.choice(points),
                    subitem_a=random.choice(keywords),
                    subitem_b=random.choice(details),
                    step1=random.choice(details),
                    step2=random.choice(keywords),
                    step3=random.choice(points),
                    warning=random.choice(["重要", "注意", "警告", "必須"]),
                    tip=random.choice(["コツ", "ヒント", "アドバイス", "推奨"]),
                    comment=random.choice(["説明", "補足", "参考", "注記"]),
                    combined=random.choice(keywords),
                    alert=random.choice(["エラー", "障害", "問題", "リスク"]),
                    section=section_count,
                    subsection=subsection_count,
                    item=item_count
                )
            
            file.write(content + '\n')
    
    # ファイル情報表示
    file_size = output_path.stat().st_size
    print(f"\nTest file generated successfully!")
    print(f"File: {output_path}")
    print(f"Lines: {target_lines:,}")
    print(f"Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")


def main():
    """メイン実行"""
    output_file = Path("300k_test_file.kumihan")
    
    print("=== Issue #759: Large File Performance Test Generator ===")
    print(f"Target: 300,000 lines")
    print(f"Output: {output_file}")
    print()
    
    # ファイル生成実行
    generate_large_kumihan_file(output_file, 300000)
    
    print(f"\n✅ 300K line test file ready for performance testing!")
    print(f"📁 File location: {output_file.absolute()}")
    
    # 追加の小さいテストファイルも生成
    small_files = [
        (1000, "1k_test_file.kumihan"),
        (10000, "10k_test_file.kumihan"),
        (50000, "50k_test_file.kumihan"),
    ]
    
    for lines, filename in small_files:
        print(f"\nGenerating {lines/1000:.0f}K line file: {filename}")
        generate_large_kumihan_file(Path(filename), lines)
    
    print(f"\n🎯 All test files generated for Issue #759 performance testing!")


if __name__ == "__main__":
    main()