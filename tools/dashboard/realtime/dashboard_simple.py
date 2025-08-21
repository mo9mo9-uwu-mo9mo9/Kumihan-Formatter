import logging
import time

import pandas as pd
import streamlit as st
from analytics_engine import AnalyticsEngine
from data_generator import DataGenerator

logger = logging.getLogger(__name__)


def main():
    """
    Streamlitダッシュボードのメイン関数（plotlyなし版）。
    """
    logging.basicConfig(level=logging.INFO)

    st.title("🚀 リアルタイム分析ダッシュボード")
    st.markdown("*Gemini実装による複雑システムデモ*")

    # データ生成器の初期化
    num_series = st.sidebar.slider("系列数", min_value=1, max_value=5, value=3)
    data_points = st.sidebar.slider(
        "初期データポイント数", min_value=50, max_value=200, value=100
    )
    update_interval = st.sidebar.slider(
        "更新間隔 (秒)", min_value=1, max_value=5, value=2
    )

    data_generator = DataGenerator(num_series=num_series, data_points=data_points)
    analytics_engine = AnalyticsEngine()

    # チャートの種類を選択
    chart_type = st.sidebar.selectbox(
        "チャートの種類", ["線グラフ", "エリアチャート", "棒グラフ"]
    )

    # データフィルタリング
    data = data_generator.get_data()
    filter_column = st.sidebar.selectbox("フィルタリング対象の系列", data.columns)
    filter_threshold = st.sidebar.slider(
        "フィルタリング閾値", min_value=-5.0, max_value=5.0, value=0.0, step=0.1
    )

    # リアルタイム更新のためのプレースホルダー
    placeholder = st.empty()
    stats_placeholder = st.empty()

    # 実行制御
    col1, col2 = st.columns(2)
    with col1:
        run_dashboard = st.button("🎯 ダッシュボード実行", type="primary")
    with col2:
        stop_dashboard = st.button("⏹️ 停止")

    if run_dashboard and not stop_dashboard:
        iteration = 0
        max_iterations = 10  # デモ用に制限

        progress_bar = st.progress(0)

        while iteration < max_iterations:
            try:
                # データの更新
                data_generator.update_data(new_points=5)
                data = data_generator.get_data()

                # データフィルタリング
                filtered_data = data[data[filter_column] > filter_threshold]

                # 統計量の計算
                statistics = analytics_engine.calculate_statistics(filtered_data)

                # トレンドの計算
                trends = analytics_engine.calculate_trends(filtered_data)

                with placeholder.container():
                    st.subheader(
                        f"📊 データ可視化 (更新: {iteration + 1}/{max_iterations})"
                    )

                    # チャート表示
                    if chart_type == "線グラフ":
                        st.line_chart(filtered_data)
                    elif chart_type == "エリアチャート":
                        st.area_chart(filtered_data)
                    elif chart_type == "棒グラフ":
                        st.bar_chart(filtered_data.tail(20))

                    # データサマリー表示
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📏 データポイント", len(filtered_data))
                    with col2:
                        st.metric("📈 系列数", len(filtered_data.columns))
                    with col3:
                        st.metric(
                            "🎯 フィルタ適用", f"{filter_column} > {filter_threshold}"
                        )

                with stats_placeholder.container():
                    st.subheader("📈 統計分析結果")

                    # 統計情報表示
                    stats_col1, stats_col2 = st.columns(2)

                    with stats_col1:
                        st.markdown("**📊 基本統計量**")
                        for column, stats in statistics.items():
                            st.markdown(f"**{column}**")
                            st.markdown(f"- 平均: {stats['mean']:.3f}")
                            st.markdown(f"- 標準偏差: {stats['std']:.3f}")
                            st.markdown("---")

                    with stats_col2:
                        st.markdown("**📈 トレンド分析**")
                        for column, trend in trends.items():
                            direction = (
                                "📈 上昇"
                                if trend > 0
                                else "📉 下降" if trend < 0 else "➡️ 横ばい"
                            )
                            st.markdown(f"**{column}**: {direction} ({trend:.3f})")

                        st.markdown("---")
                        st.markdown("**🔄 リアルタイム更新中...**")

                # 進行状況更新
                progress_bar.progress((iteration + 1) / max_iterations)

                iteration += 1

                # リアルタイム更新間隔
                time.sleep(update_interval)

            except Exception as e:
                st.error(f"❌ エラーが発生しました: {e}")
                logger.error(f"ダッシュボード実行エラー: {e}")
                break

        st.success("✅ ダッシュボードデモ完了！")
        st.balloons()


if __name__ == "__main__":
    main()
