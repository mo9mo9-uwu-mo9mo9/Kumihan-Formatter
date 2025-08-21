#!/usr/bin/env python3
"""
Kumihan記法 大規模サンプルファイル生成スクリプト
約10,000行のパフォーマンステスト用サンプルファイルを生成
"""

import os
import random
from pathlib import Path

# Kumihan記法の全キーワード（α-dev 対応）
KEYWORDS = [
    "太字",
    "イタリック",
    "下線",
    "取り消し線",
    "コード",
    "引用",
    "枠線",
    "ハイライト",
    "見出し1",
    "見出し2",
    "見出し3",
    "見出し4",
    "見出し5",
    "折りたたみ",
    "ネタバレ",
    "中央寄せ",
    "注意",
    "情報",
    "コードブロック",
]

# 色名（英単語30種）
COLOR_NAMES = [
    "red",
    "blue",
    "green",
    "yellow",
    "orange",
    "purple",
    "pink",
    "brown",
    "black",
    "white",
    "gray",
    "cyan",
    "magenta",
    "lime",
    "navy",
    "olive",
    "maroon",
    "teal",
    "silver",
    "gold",
    "indigo",
    "violet",
    "coral",
    "salmon",
    "khaki",
    "crimson",
    "azure",
    "beige",
    "turquoise",
    "lavender",
]

# 16進数カラーコード例
HEX_COLORS = [
    "#ff0000",
    "#00ff00",
    "#0000ff",
    "#ffff00",
    "#ff00ff",
    "#00ffff",
    "#ffa500",
    "#800080",
    "#ffc0cb",
    "#a52a2a",
    "#808080",
    "#000080",
    "#008000",
    "#800000",
    "#008080",
    "#ffd700",
    "#4b0082",
    "#ee82ee",
    "#ff7f50",
    "#fa8072",
    "#f0e68c",
    "#dc143c",
    "#f0ffff",
    "#f5f5dc",
    "#40e0d0",
    "#e6e6fa",
    "#ffe4e1",
    "#dda0dd",
    "#98fb98",
    "#f0f8ff",
]

# マーカー（半角・全角）
MARKERS = ["#", "＃"]

# サンプルコンテンツテンプレート
SAMPLE_TEXTS = {
    "technical": [
        "APIエンドポイントの設計において、RESTfulな設計原則を遵守することが重要です。",
        "データベースのインデックス戦略は、クエリパフォーマンスに直接影響します。",
        "マイクロサービスアーキテクチャでは、サービス間通信の最適化が鍵となります。",
        "クラウドネイティブな開発では、コンテナオーケストレーションの理解が必須です。",
        "機械学習モデルのデプロイには、継続的インテグレーションが不可欠です。",
    ],
    "trpg": [
        "古代遺跡の奥深くで、冒険者たちは光る宝石を発見した。",
        "ドラゴンの咆哮が響き渡り、パーティーは戦闘態勢に入る。",
        "謎めいた魔法使いが現れ、重要な情報を提供する。",
        "トラップが作動し、ダンジェンの構造が変化した。",
        "最終ボスとの決戦が迫り、運命の時が訪れる。",
    ],
    "documentation": [
        "このマニュアルでは、基本的な操作方法について説明します。",
        "システム要件を満たしていることを事前に確認してください。",
        "設定ファイルの編集には管理者権限が必要です。",
        "トラブルシューティングガイドを参照して問題を解決してください。",
        "定期的なバックアップの実行を強く推奨します。",
    ],
    "general": [
        "今日は良い天気ですね。散歩に出かけたくなります。",
        "新しい技術を学ぶことは、常に刺激的な体験です。",
        "チームワークの重要性は、どんなプロジェクトでも変わりません。",
        "創造性と論理性のバランスが、良いソリューションを生み出します。",
        "継続的な改善こそが、成功への鍵だと考えています。",
    ],
}


def get_random_color():
    """ランダムな色（英単語または16進数）を取得"""
    if random.choice([True, False]):
        return random.choice(COLOR_NAMES)
    else:
        return random.choice(HEX_COLORS)


def generate_inline_notation(keyword, content, use_color=False):
    """α-dev: インライン記法は廃止 - ブロック記法に統一"""
    # α-devではインライン記法は廃止、ブロック記法のみ使用
    return generate_block_notation(keyword, content, use_color)


def generate_block_notation(keyword, content, use_color=False):
    """ブロック記法を生成"""
    marker = random.choice(MARKERS)

    if use_color and keyword == "ハイライト":
        color = get_random_color()
        return f"{marker}{keyword} color={color}{marker}\n{content}\n{marker}{marker}"
    else:
        return f"{marker}{keyword}{marker}\n{content}\n{marker}{marker}"


def generate_complex_notation():
    """複雑な組み合わせ記法を生成"""
    base_keywords = random.sample(
        KEYWORDS[:8], random.randint(2, 3)
    )  # 装飾系キーワードから2-3個選択
    combined = "+".join(base_keywords)
    marker = random.choice(MARKERS)
    content = random.choice(SAMPLE_TEXTS["general"])

    # 色属性を追加する場合
    if "ハイライト" in base_keywords and random.choice([True, False]):
        color = get_random_color()
        return f"{marker}{combined} color={color}{marker} {content}"
    else:
        return f"{marker}{combined}{marker} {content}"


def generate_table_of_contents():
    """目次セクションを生成"""
    sections = []
    sections.append("# 目次")
    sections.append("")

    for i in range(1, random.randint(8, 15)):
        level = random.randint(1, 3)
        title = f"第{i}章 " + random.choice(
            [
                "システム概要",
                "基本操作",
                "応用機能",
                "トラブルシューティング",
                "設定方法",
                "API リファレンス",
                "パフォーマンス最適化",
                "セキュリティ",
            ]
        )
        marker = random.choice(MARKERS)
        sections.append(f"{marker}見出し{level}{marker} {title}")

        # サブセクション
        for j in range(1, random.randint(3, 6)):
            sub_title = random.choice(
                ["概要", "詳細", "例", "注意事項", "設定", "使用方法"]
            )
            sections.append(f"  {i}.{j} {sub_title}")

    sections.append("")
    return "\n".join(sections)


def generate_trpg_scenario():
    """TRPGシナリオセクションを生成"""
    sections = []
    marker1 = random.choice(MARKERS)
    marker2 = random.choice(MARKERS)

    sections.append(f"{marker1}見出し1+枠線{marker1} TRPGシナリオ: 失われた遺跡の謎")
    sections.append("")

    # シナリオ概要
    sections.append(
        f"{marker2}見出し2+ハイライト color={get_random_color()}{marker2} シナリオ概要"
    )
    sections.append(f"{marker2}枠線{marker2}")
    sections.append("古代文明の遺跡で発見された謎の石版。")
    sections.append("それは世界の運命を左右する秘密を秘めていた。")
    sections.append(f"{marker2}{marker2}")
    sections.append("")

    # キャラクター情報
    sections.append(f"{marker1}見出し2{marker1} 登場キャラクター")
    for i, char in enumerate(
        ["エリア（魔法使い）", "ガレス（戦士）", "リン（盗賊）"], 1
    ):
        sections.append(f"{marker2}見出し3+太字{marker2} {char}")
        sections.append(f"- {marker2}太字{marker2} HP: {random.randint(80, 120)}")
        sections.append(
            f"- {marker2}イタリック{marker2} 特技: {random.choice(['魔法詠唱', '剣術', '隠密'])}"
        )
        sections.append(
            f"- {marker2}ハイライト color={get_random_color()}{marker2} 装備: {random.choice(['魔法の杖', '銀の剣', '影の短剣'])}"
        )
        sections.append("")

    # イベント
    sections.append(f"{marker1}見出し2+枠線{marker1} 主要イベント")
    for i in range(1, 6):
        event_title = random.choice(
            ["遺跡の入口", "謎解きの間", "モンスター遭遇", "宝物庫", "最終決戦"]
        )
        sections.append(f"{marker2}見出し3{marker2} イベント{i}: {event_title}")
        sections.append(random.choice(SAMPLE_TEXTS["trpg"]))

        # ランダムで特殊効果を追加
        if random.choice([True, False]):
            sections.append(
                f"{marker2}注意+ハイライト color=#ffe6e6{marker2} 判定が必要です！"
            )
        sections.append("")

    return "\n".join(sections)


def generate_code_documentation():
    """コードドキュメントセクションを生成"""
    sections = []
    marker = random.choice(MARKERS)

    sections.append(f"{marker}見出し1+枠線{marker} API ドキュメント")
    sections.append("")

    # API概要
    sections.append(f"{marker}見出し2{marker} 概要")
    sections.append(random.choice(SAMPLE_TEXTS["technical"]))
    sections.append("")

    # エンドポイント
    sections.append(f"{marker}見出し2{marker} エンドポイント")
    for endpoint in ["/api/users", "/api/posts", "/api/comments"]:
        sections.append(f"{marker}見出し3+コード{marker} {endpoint}")
        sections.append(f"{marker}コードブロック{marker}")
        sections.append("GET /api/users")
        sections.append("POST /api/users")
        sections.append("PUT /api/users/{id}")
        sections.append("DELETE /api/users/{id}")
        sections.append(f"{marker}{marker}")
        sections.append("")

        # パラメータ説明
        sections.append(f"{marker}見出し4{marker} パラメータ")
        sections.append(f"- {marker}太字{marker} id: ユーザーID")
        sections.append(f"- {marker}イタリック{marker} name: ユーザー名")
        sections.append(f"- {marker}下線{marker} email: メールアドレス")
        sections.append("")

        # レスポンス例
        sections.append(
            f"{marker}見出し4+ハイライト color={get_random_color()}{marker} レスポンス例"
        )
        sections.append(f"{marker}コードブロック{marker}")
        sections.append("{")
        sections.append('  "id": 1,')
        sections.append('  "name": "John Doe",')
        sections.append('  "email": "john@example.com"')
        sections.append("}")
        sections.append(f"{marker}{marker}")
        sections.append("")

    return "\n".join(sections)


def generate_mixed_content_section():
    """混在コンテンツセクションを生成"""
    sections = []
    marker = random.choice(MARKERS)

    sections.append(
        f"{marker}見出し2+枠線+ハイライト color={get_random_color()}{marker} 混在記法の例"
    )
    sections.append("")

    # 各種記法を混在させる
    for _ in range(random.randint(10, 20)):
        content_type = random.choice(list(SAMPLE_TEXTS.keys()))
        content = random.choice(SAMPLE_TEXTS[content_type])

        # ランダムで記法を選択
        if random.choice([True, False]):
            # インライン記法
            keyword = random.choice(KEYWORDS)
            use_color = keyword == "ハイライト" and random.choice([True, False])
            sections.append(generate_inline_notation(keyword, content, use_color))
        else:
            # ブロック記法
            keyword = random.choice(KEYWORDS)
            use_color = keyword == "ハイライト" and random.choice([True, False])
            sections.append(generate_block_notation(keyword, content, use_color))

        sections.append("")

        # たまに複雑な記法を挿入
        if random.random() < 0.3:
            sections.append(generate_complex_notation())
            sections.append("")

    return "\n".join(sections)


def generate_performance_test_patterns():
    """パフォーマンステスト特化パターンを生成"""
    sections = []
    marker = random.choice(MARKERS)

    sections.append(
        f"{marker}見出し1+太字+ハイライト color=#f0f8ff{marker} パフォーマンステストパターン"
    )
    sections.append("")

    # 大量の短い記法
    sections.append(f"{marker}見出し2{marker} 短縮記法パターン")
    for i in range(50):
        keyword = random.choice(KEYWORDS[:8])  # 装飾系のみ
        short_content = f"テスト{i+1}"
        marker_type = random.choice(MARKERS)
        sections.append(f"{marker_type}{keyword}{marker_type} {short_content}")
    sections.append("")

    # ネストパターン
    sections.append(f"{marker}見出し2{marker} ネストパターン")
    for i in range(20):
        outer_keyword = random.choice(KEYWORDS[6:8])  # 枠線、ハイライト
        inner_keyword = random.choice(KEYWORDS[:5])  # 装飾系
        content = f"ネストテスト{i+1}: " + random.choice(SAMPLE_TEXTS["general"])

        sections.append(f"{marker}{outer_keyword}{marker}")
        sections.append(f"{marker}{inner_keyword}{marker} {content}")
        sections.append(f"{marker}{marker}")
        sections.append("")

    # 色パターンの網羅
    sections.append(f"{marker}見出し2{marker} 色パターン網羅")
    for color in COLOR_NAMES[:15]:  # 半分の色名
        content = f"色テスト: {color}"
        sections.append(f"{marker}ハイライト color={color}{marker} {content}")

    for color in HEX_COLORS[:15]:  # 半分の16進数色
        content = f"色テスト: {color}"
        sections.append(f"{marker}ハイライト color={color}{marker} {content}")

    sections.append("")
    return "\n".join(sections)


def generate_large_sample_file():
    """大規模サンプルファイルを生成"""
    content_sections = []

    # ファイルヘッダー
    content_sections.append("# Kumihan記法 大規模パフォーマンステストファイル")
    content_sections.append("# 生成日: 自動生成")
    content_sections.append("# 用途: パフォーマンステスト・負荷テスト")
    content_sections.append("")

    # 目次
    content_sections.append(generate_table_of_contents())

    # メインコンテンツセクション
    sections_to_generate = [
        ("TRPGシナリオ", generate_trpg_scenario),
        ("技術ドキュメント", generate_code_documentation),
        ("混在コンテンツ", generate_mixed_content_section),
        ("パフォーマンステストパターン", generate_performance_test_patterns),
    ]

    # 各セクションを複数回生成して行数を稼ぐ
    target_lines = 10000
    current_lines = 0

    while current_lines < target_lines:
        for section_name, generator_func in sections_to_generate:
            if current_lines >= target_lines:
                break

            # セクション生成
            section_content = generator_func()
            content_sections.append(section_content)
            content_sections.append("")  # セクション間の空行

            # 行数をカウント
            current_lines += section_content.count("\n") + 2

            # プログレス表示用のコメント
            if current_lines % 1000 < 100:
                marker = random.choice(MARKERS)
                content_sections.append(
                    f"{marker}情報{marker} 進行状況: 約{current_lines}行生成済み"
                )
                content_sections.append("")

    # 最終的な統計情報
    final_content = "\n".join(content_sections)
    actual_lines = final_content.count("\n") + 1

    # 統計情報を追加
    stats_section = f"""
＃見出し1+枠線＃ 生成統計
＃情報+ハイライト color=#e6f3ff＃
- 総行数: {actual_lines}行
- 使用キーワード: {len(KEYWORDS)}種類
- 色パターン: {len(COLOR_NAMES + HEX_COLORS)}種類
- マーカー: 半角(#) + 全角(＃)
- 記法パターン: インライン + ブロック + 複合
＃＃

＃注意＃ このファイルはパフォーマンステスト用です。実際の文書作成には適していません。
"""

    return final_content + stats_section


def main():
    """メイン実行関数"""
    print("🚀 Kumihan記法 大規模サンプルファイル生成を開始...")

    # 出力ディレクトリを確保
    output_dir = Path(
        "/Users/m2_macbookair_3911/GitHub/Kumihan-Formatter/samples/performance"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    # ファイル生成
    print("📝 サンプルコンテンツ生成中...")
    sample_content = generate_large_sample_file()

    # ファイル保存
    output_file = output_dir / "10_large_document_10k.txt"
    print(f"💾 ファイル保存中: {output_file}")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(sample_content)

    # 結果報告
    actual_lines = sample_content.count("\n") + 1
    file_size = len(sample_content.encode("utf-8"))

    print(f"✅ 生成完了!")
    print(f"📊 統計情報:")
    print(f"   - ファイル: {output_file}")
    print(f"   - 行数: {actual_lines:,}行")
    print(f"   - ファイルサイズ: {file_size:,}バイト ({file_size/1024:.1f}KB)")
    print(f"   - 使用キーワード: {len(KEYWORDS)}種類")
    print(f"   - 色パターン: {len(COLOR_NAMES + HEX_COLORS)}種類")
    print("🎯 パフォーマンステスト準備完了!")


if __name__ == "__main__":
    main()
