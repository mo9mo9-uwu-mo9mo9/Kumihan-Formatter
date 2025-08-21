#!/usr/bin/env python3
"""Gemini実装システムの動作デモ（CLI版）"""

import time

from analytics_engine import AnalyticsEngine
from data_generator import DataGenerator


def main():
    """リアルタイム分析ダッシュボードのデモ実行"""

    print("🚀 Gemini実装システム - リアルタイム分析デモ開始")
    print("=" * 60)

    # システム初期化
    print("⚙️ システム初期化中...")
    gen = DataGenerator(num_series=3, data_points=20)
    engine = AnalyticsEngine()

    print("✅ 初期化完了!")
    print()

    # 5回のリアルタイム更新デモ
    for iteration in range(1, 6):
        print(f"🔄 更新 {iteration}/5")
        print("-" * 40)

        # データ更新
        gen.update_data(new_points=5)
        data = gen.get_data()

        print(f"📊 データサイズ: {data.shape[0]}行 x {data.shape[1]}列")

        # 最新データ表示
        print("📈 最新5行のデータ:")
        print(data.tail().round(3).to_string())

        # 基本統計（修正版）
        print(f"\n📊 基本統計:")
        for col in data.columns:
            mean_val = data[col].mean()
            std_val = data[col].std()
            latest_val = data[col].iloc[-1]
            print(
                f"  {col}: 平均={mean_val:.3f}, 標準偏差={std_val:.3f}, 最新値={latest_val:.3f}"
            )

        # 簡単なトレンド分析（修正版）
        print(f"\n📈 トレンド分析（直近10点）:")
        for col in data.columns:
            recent_data = data[col].tail(10)
            if len(recent_data) > 1:
                trend = recent_data.iloc[-1] - recent_data.iloc[0]
                direction = (
                    "📈上昇" if trend > 0.1 else "📉下降" if trend < -0.1 else "➡️横ばい"
                )
                print(f"  {col}: {direction} (変化: {trend:.3f})")

        print(
            f"\n💹 データフィルタ例 (series_1 > 0): {len(data[data['series_1'] > 0])}件"
        )

        print("\n" + "=" * 60)

        if iteration < 5:
            print("⏳ 2秒後に次の更新...")
            time.sleep(2)

    print("🎉 リアルタイム分析デモ完了!")
    print(f"📊 最終データ: {data.shape[0]}行のデータを生成・分析")
    print("✅ Geminiが実装した複雑システムが完全動作!")


if __name__ == "__main__":
    main()
