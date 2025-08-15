import streamlit as st
import pandas as pd
import plotly.express as px
from data_generator import DataGenerator
from analytics_engine import AnalyticsEngine
import time
import logging

logger = logging.getLogger(__name__)

def main():
    """
    Streamlitダッシュボードのメイン関数。
    """
    logging.basicConfig(level=logging.INFO)

    st.title("リアルタイム分析ダッシュボード")

    # データ生成器の初期化
    num_series = st.sidebar.slider("系列数", min_value=1, max_value=5, value=3)
    data_points = st.sidebar.slider("初期データポイント数", min_value=50, max_value=200, value=100)
    update_interval = st.sidebar.slider("更新間隔 (秒)", min_value=1, max_value=5, value=2)

    data_generator = DataGenerator(num_series=num_series, data_points=data_points)
    analytics_engine = AnalyticsEngine()

    # チャートの種類を選択
    chart_type = st.sidebar.selectbox("チャートの種類", ["線グラフ", "棒グラフ", "散布図"])

    # データフィルタリング
    filter_column = st.sidebar.selectbox("フィルタリング対象の系列", data_generator.get_data().columns)
    filter_threshold = st.sidebar.slider("フィルタリング閾値", min_value=-5.0, max_value=5.0, value=0.0, step=0.1)

    placeholder = st.empty()

    while True:
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
                st.header("リアルタイムデータ")

                # チャートの表示
                if chart_type == "線グラフ":
                    fig = px.line(filtered_data, title="時系列データ (線グラフ)")
                elif chart_type == "棒グラフ":
                    fig = px.bar(filtered_data.tail(20), title="時系列データ (棒グラフ)")
                else:  # 散布図
                    if len(filtered_data) > 1:
                        fig = px.scatter(filtered_data.tail(50), x=filtered_data.columns[0], y=filtered_data.columns[1], title="時系列データ (散布図)")
                    else:
                        st.warning("散布図を表示するには、少なくとも2つの系列が必要です。")
                        fig = None

                if fig:
                    st.plotly_chart(fig, use_container_width=True)

                st.subheader("統計量")
                st.write(statistics)

                st.subheader("トレンド")
                st.write(trends)

            time.sleep(update_interval)

        except Exception as e:
            logger.error(f"ダッシュボードの実行中にエラーが発生しました: {e}")
            st.error(f"エラーが発生しました: {e}")
            break

if __name__ == "__main__":
    main()
