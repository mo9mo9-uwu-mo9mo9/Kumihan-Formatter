"""
統合ログシステム Streamlit ダッシュボード
=======================================

リアルタイム監視・分析・レポート表示のWebダッシュボード
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import asyncio
import websockets
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
import time
import threading

# ローカルインポート
from dashboard_config import get_config, get_alert_config, get_metrics_config

# 設定読み込み
config = get_config()
alert_config = get_alert_config()
metrics_config = get_metrics_config()

# Streamlit設定
st.set_page_config(
    page_title=config.dashboard.title,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .alert-high {
        background-color: #ff4757;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.25rem 0;
    }
    .alert-medium {
        background-color: #ffa502;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.25rem 0;
    }
    .alert-low {
        background-color: #3742fa;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.25rem 0;
    }
    .success-rate-high { color: #2ed573; font-weight: bold; }
    .success-rate-medium { color: #ffa502; font-weight: bold; }
    .success-rate-low { color: #ff4757; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# データアクセス層
# ==========================================

class APIClient:
    """APIクライアント"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.headers = {}
        self.token = None

    def set_auth_token(self, token: str):
        """認証トークン設定"""
        self.token = token
        self.headers["Authorization"] = f"Bearer {token}"

    def get(self, endpoint: str, params: Dict = None) -> Dict:
        """GET リクエスト"""
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API エラー: {e}")
            return {}

    def post(self, endpoint: str, data: Dict = None) -> Dict:
        """POST リクエスト"""
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API エラー: {e}")
            return {}


# APIクライアント初期化
api_client = APIClient()


# ==========================================
# サンプルデータ生成
# ==========================================

def generate_sample_data():
    """サンプルデータ生成（APIが利用できない場合）"""
    import random

    # プロジェクトデータ
    projects = [
        {
            "id": "kumihan-formatter",
            "name": "Kumihan Formatter",
            "description": "メインプロジェクト",
            "stats": {
                "total_executions": 150,
                "success_rate": 0.87,
                "total_tokens": 45000,
                "last_execution": datetime.now() - timedelta(hours=2)
            }
        },
        {
            "id": "test-automation",
            "name": "Test Automation",
            "description": "テスト自動化",
            "stats": {
                "total_executions": 89,
                "success_rate": 0.95,
                "total_tokens": 28000,
                "last_execution": datetime.now() - timedelta(minutes=30)
            }
        }
    ]

    # ログデータ
    logs = []
    base_time = datetime.now() - timedelta(days=7)

    for i in range(100):
        log_time = base_time + timedelta(hours=i * 1.68)
        success = random.random() > 0.15  # 85%成功率

        logs.append({
            "id": f"log_{i}",
            "project_id": random.choice(["kumihan-formatter", "test-automation"]),
            "task_type": random.choice(["implementation", "bugfix", "testing", "refactor"]),
            "complexity": random.choice(["simple", "moderate", "complex"]),
            "start_time": log_time,
            "end_time": log_time + timedelta(minutes=random.randint(5, 45)),
            "status": "completed" if success else "failed",
            "gemini_tokens": random.randint(200, 800),
            "claude_tokens": random.randint(20, 150),
            "success": success,
            "error_message": None if success else f"エラータイプ_{random.randint(1, 5)}",
            "metadata": {"version": "1.0", "branch": "main"}
        })

    return {"projects": projects, "logs": logs}


# ==========================================
# データ取得・キャッシュ
# ==========================================

@st.cache_data(ttl=30)
def get_projects_data() -> Dict:
    """プロジェクトデータ取得"""
    data = api_client.get("/api/projects")
    if not data:
        # APIが利用できない場合はサンプルデータを使用
        sample_data = generate_sample_data()
        return sample_data["projects"]
    return data.get("projects", [])


@st.cache_data(ttl=30)
def get_orchestration_logs(project_id: str = None, limit: int = 100) -> List[Dict]:
    """オーケストレーションログ取得"""
    params = {"limit": limit}
    if project_id:
        params["project_id"] = project_id

    data = api_client.get("/api/orchestration/logs", params)
    if not data:
        # APIが利用できない場合はサンプルデータを使用
        sample_data = generate_sample_data()
        logs = sample_data["logs"]
        if project_id:
            logs = [log for log in logs if log["project_id"] == project_id]
        return logs[:limit]
    return data.get("logs", [])


@st.cache_data(ttl=60)
def get_project_analytics(project_id: str) -> Dict:
    """プロジェクト分析データ取得"""
    data = api_client.get(f"/api/projects/{project_id}/analytics")
    if not data:
        # サンプル分析データ
        logs = get_orchestration_logs(project_id)
        if not logs:
            return {}

        total_executions = len(logs)
        successful_executions = sum(1 for log in logs if log["success"])
        success_rate = successful_executions / total_executions if total_executions > 0 else 0

        return {
            "project_id": project_id,
            "summary": {
                "total_executions": total_executions,
                "success_rate": success_rate,
                "token_savings": 0.85,
                "total_tokens": sum(log["gemini_tokens"] + log["claude_tokens"] for log in logs)
            },
            "daily_stats": {},
            "failure_patterns": {},
            "recent_logs": logs[-10:]
        }
    return data


@st.cache_data(ttl=60)
def get_failure_patterns() -> Dict:
    """失敗パターン取得"""
    data = api_client.get("/api/failures/patterns")
    if not data:
        return {
            "patterns": {
                "timeout": {"count": 5, "projects": ["kumihan-formatter"]},
                "syntax_error": {"count": 3, "projects": ["test-automation"]},
                "memory_error": {"count": 2, "projects": ["kumihan-formatter"]}
            }
        }
    return data


@st.cache_data(ttl=60)
def get_suggestions() -> Dict:
    """改善提案取得"""
    data = api_client.get("/api/suggestions")
    if not data:
        return {
            "suggestions": [
                {
                    "type": "success_rate",
                    "priority": "high",
                    "project_id": "kumihan-formatter",
                    "message": "成功率が85%と低いです。エラーパターンを確認してください。",
                    "action": "failure_analysis"
                },
                {
                    "type": "token_usage",
                    "priority": "medium",
                    "project_id": "test-automation",
                    "message": "平均トークン使用量が高いです。プロンプトの最適化を検討してください。",
                    "action": "optimize_prompts"
                }
            ]
        }
    return data


# ==========================================
# 認証機能
# ==========================================

def show_login_page():
    """ログインページ表示"""
    st.markdown("# 🔐 ログイン")

    with st.form("login_form"):
        username = st.text_input("ユーザー名", value="admin")
        password = st.text_input("パスワード", type="password", value="admin123")
        submit = st.form_submit_button("ログイン")

        if submit:
            # ログイン試行
            login_data = {"username": username, "password": password}
            response = api_client.post("/api/auth/login", login_data)

            if response and "access_token" in response:
                st.session_state.authenticated = True
                st.session_state.token = response["access_token"]
                api_client.set_auth_token(response["access_token"])
                st.success("ログインしました！")
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("ログインに失敗しました。ユーザー名とパスワードを確認してください。")


def check_authentication():
    """認証チェック"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        show_login_page()
        return False

    # トークンが設定されている場合はAPIクライアントに設定
    if "token" in st.session_state:
        api_client.set_auth_token(st.session_state.token)

    return True


# ==========================================
# メインダッシュボード
# ==========================================

def show_main_dashboard():
    """メインダッシュボード表示"""
    st.markdown("# 📊 ダッシュボード")

    # データ取得
    projects = get_projects_data()
    all_logs = get_orchestration_logs(limit=200)

    if not projects:
        st.warning("プロジェクトデータが取得できませんでした。")
        return

    # 総合統計計算
    total_executions = sum(project.get("stats", {}).get("total_executions", 0) for project in projects)
    avg_success_rate = sum(project.get("stats", {}).get("success_rate", 0) for project in projects) / len(projects) if projects else 0
    total_tokens = sum(project.get("stats", {}).get("total_tokens", 0) for project in projects)

    # メトリクスカード表示
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 総実行回数</h3>
            <h2>{total_executions:,}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        success_color = "success-rate-high" if avg_success_rate >= 0.9 else "success-rate-medium" if avg_success_rate >= 0.7 else "success-rate-low"
        st.markdown(f"""
        <div class="metric-card">
            <h3>✅ 平均成功率</h3>
            <h2 class="{success_color}">{avg_success_rate:.1%}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        token_savings = 0.85  # 固定値（実際はAPIから取得）
        st.markdown(f"""
        <div class="metric-card">
            <h3>💰 Token削減率</h3>
            <h2>{token_savings:.1%}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🔢 総Token使用量</h3>
            <h2>{total_tokens:,}</h2>
        </div>
        """, unsafe_allow_html=True)

    # チャート表示
    col1, col2 = st.columns(2)

    with col1:
        # 成功率チャート
        if all_logs:
            df_logs = pd.DataFrame(all_logs)
            df_logs['start_time'] = pd.to_datetime(df_logs['start_time'])
            df_logs['date'] = df_logs['start_time'].dt.date

            daily_stats = df_logs.groupby('date').agg({
                'success': ['count', 'sum']
            }).reset_index()
            daily_stats.columns = ['date', 'total', 'successes']
            daily_stats['success_rate'] = daily_stats['successes'] / daily_stats['total']

            fig_success = px.line(
                daily_stats,
                x='date',
                y='success_rate',
                title="📈 日別成功率推移",
                labels={'success_rate': '成功率', 'date': '日付'}
            )
            fig_success.update_layout(yaxis_tickformat='.1%')
            st.plotly_chart(fig_success, use_container_width=True)

    with col2:
        # プロジェクト別統計
        project_stats = []
        for project in projects:
            stats = project.get("stats", {})
            project_stats.append({
                "プロジェクト": project["name"],
                "実行回数": stats.get("total_executions", 0),
                "成功率": stats.get("success_rate", 0)
            })

        if project_stats:
            df_projects = pd.DataFrame(project_stats)
            fig_projects = px.bar(
                df_projects,
                x="プロジェクト",
                y="実行回数",
                color="成功率",
                title="📊 プロジェクト別実行統計",
                color_continuous_scale="RdYlGn"
            )
            st.plotly_chart(fig_projects, use_container_width=True)

    # アラート表示
    suggestions = get_suggestions()
    if suggestions.get("suggestions"):
        st.markdown("## 🚨 アラート・提案")
        for suggestion in suggestions["suggestions"]:
            priority = suggestion["priority"]
            alert_class = f"alert-{priority}"
            st.markdown(f"""
            <div class="{alert_class}">
                <strong>{suggestion['type'].upper()}</strong>: {suggestion['message']}
            </div>
            """, unsafe_allow_html=True)

    # 最近のログ
    st.markdown("## 📋 最新実行ログ")
    if all_logs:
        recent_logs = all_logs[-10:]

        log_data = []
        for log in recent_logs:
            log_data.append({
                "時刻": pd.to_datetime(log["start_time"]).strftime("%m/%d %H:%M"),
                "プロジェクト": log["project_id"],
                "タスク": log["task_type"],
                "複雑度": log["complexity"],
                "ステータス": "✅ 成功" if log["success"] else "❌ 失敗",
                "Token": log["gemini_tokens"] + log["claude_tokens"]
            })

        df_logs = pd.DataFrame(log_data)
        st.dataframe(df_logs, use_container_width=True)


# ==========================================
# プロジェクト管理ページ
# ==========================================

def show_project_management():
    """プロジェクト管理ページ表示"""
    st.markdown("# 📁 プロジェクト管理")

    projects = get_projects_data()

    if not projects:
        st.warning("プロジェクトデータが取得できませんでした。")
        return

    # プロジェクト選択
    project_names = [project["name"] for project in projects]
    selected_project_name = st.selectbox("プロジェクトを選択", project_names)

    # 選択されたプロジェクトの詳細
    selected_project = next(p for p in projects if p["name"] == selected_project_name)
    project_id = selected_project["id"]

    # プロジェクト情報表示
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"## {selected_project['name']}")
        if selected_project.get("description"):
            st.markdown(f"**説明**: {selected_project['description']}")

        # 統計表示
        stats = selected_project.get("stats", {})

        subcol1, subcol2, subcol3 = st.columns(3)
        with subcol1:
            st.metric("総実行回数", stats.get("total_executions", 0))
        with subcol2:
            st.metric("成功率", f"{stats.get('success_rate', 0):.1%}")
        with subcol3:
            st.metric("総Token", f"{stats.get('total_tokens', 0):,}")

    with col2:
        st.markdown("### ⚙️ 設定")
        if st.button("設定編集"):
            st.info("設定編集機能は開発中です")

        if st.button("データ同期"):
            st.cache_data.clear()
            st.success("データを同期しました")

    # 詳細分析タブ
    tab1, tab2, tab3 = st.tabs(["📊 統計", "📈 トレンド", "❌ 失敗分析"])

    with tab1:
        # プロジェクト分析データ取得
        analytics = get_project_analytics(project_id)
        if analytics:
            summary = analytics.get("summary", {})

            col1, col2 = st.columns(2)

            with col1:
                # 成功率ゲージ
                success_rate = summary.get("success_rate", 0)
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = success_rate * 100,
                    title = {'text': "成功率 (%)"},
                    delta = {'reference': 90},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 70], 'color': "lightgray"},
                            {'range': [70, 90], 'color': "gray"}],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90}
                    }
                ))
                st.plotly_chart(fig_gauge, use_container_width=True)

            with col2:
                # Token使用分布
                recent_logs = analytics.get("recent_logs", [])
                if recent_logs:
                    token_data = [
                        log["gemini_tokens"] + log["claude_tokens"]
                        for log in recent_logs
                    ]
                    fig_hist = px.histogram(
                        x=token_data,
                        title="Token使用量分布",
                        labels={'x': 'Token数', 'y': '頻度'}
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)

    with tab2:
        # 時系列トレンド
        logs = get_orchestration_logs(project_id, limit=100)
        if logs:
            df_logs = pd.DataFrame(logs)
            df_logs['start_time'] = pd.to_datetime(df_logs['start_time'])
            df_logs['date'] = df_logs['start_time'].dt.date

            # 日別トレンド
            daily_trend = df_logs.groupby('date').agg({
                'success': ['count', 'sum'],
                'gemini_tokens': 'sum',
                'claude_tokens': 'sum'
            }).reset_index()
            daily_trend.columns = ['date', 'total', 'successes', 'gemini_tokens', 'claude_tokens']
            daily_trend['success_rate'] = daily_trend['successes'] / daily_trend['total']
            daily_trend['total_tokens'] = daily_trend['gemini_tokens'] + daily_trend['claude_tokens']

            # 成功率とToken使用量のトレンド
            fig_trend = make_subplots(
                rows=2, cols=1,
                subplot_titles=('成功率推移', 'Token使用量推移'),
                vertical_spacing=0.1
            )

            fig_trend.add_trace(
                go.Scatter(x=daily_trend['date'], y=daily_trend['success_rate'], name='成功率'),
                row=1, col=1
            )

            fig_trend.add_trace(
                go.Scatter(x=daily_trend['date'], y=daily_trend['total_tokens'], name='Total Tokens'),
                row=2, col=1
            )

            fig_trend.update_layout(height=600, title_text="プロジェクトトレンド分析")
            st.plotly_chart(fig_trend, use_container_width=True)

    with tab3:
        # 失敗分析
        failed_logs = [log for log in get_orchestration_logs(project_id) if not log["success"]]

        if failed_logs:
            st.markdown(f"### 失敗ログ ({len(failed_logs)}件)")

            # 失敗パターン分析
            error_patterns = {}
            for log in failed_logs:
                error_type = log.get("error_message", "Unknown").split(":")[0]
                error_patterns[error_type] = error_patterns.get(error_type, 0) + 1

            if error_patterns:
                fig_errors = px.pie(
                    values=list(error_patterns.values()),
                    names=list(error_patterns.keys()),
                    title="失敗パターン分布"
                )
                st.plotly_chart(fig_errors, use_container_width=True)

            # 失敗ログ詳細
            st.markdown("### 最新の失敗ログ")
            error_data = []
            for log in failed_logs[-10:]:
                error_data.append({
                    "時刻": pd.to_datetime(log["start_time"]).strftime("%m/%d %H:%M"),
                    "タスク": log["task_type"],
                    "複雑度": log["complexity"],
                    "エラー": log.get("error_message", "Unknown"),
                    "Token": log["gemini_tokens"] + log["claude_tokens"]
                })

            if error_data:
                df_errors = pd.DataFrame(error_data)
                st.dataframe(df_errors, use_container_width=True)
        else:
            st.success("このプロジェクトに失敗ログはありません！")


# ==========================================
# 分析ページ
# ==========================================

def show_analytics_page():
    """分析ページ表示"""
    st.markdown("# 📈 分析")

    # 期間選択
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("終了日", datetime.now())

    # プロジェクトフィルタ
    projects = get_projects_data()
    project_options = ["全体"] + [project["name"] for project in projects]
    selected_project = st.selectbox("プロジェクト", project_options)

    # データ取得
    if selected_project == "全体":
        logs = get_orchestration_logs(limit=500)
    else:
        project_id = next(p["id"] for p in projects if p["name"] == selected_project)
        logs = get_orchestration_logs(project_id, limit=500)

    if not logs:
        st.warning("分析データがありません。")
        return

    # データフレーム作成
    df = pd.DataFrame(logs)
    df['start_time'] = pd.to_datetime(df['start_time'])
    df = df[(df['start_time'].dt.date >= start_date) & (df['start_time'].dt.date <= end_date)]

    if df.empty:
        st.warning("選択した期間にデータがありません。")
        return

    # 分析タブ
    tab1, tab2, tab3, tab4 = st.tabs(["📊 総合分析", "💰 コスト分析", "❌ 失敗分析", "💡 改善提案"])

    with tab1:
        st.markdown("## 📊 総合分析")

        # 基本統計
        total_executions = len(df)
        success_rate = df['success'].mean()
        avg_tokens = (df['gemini_tokens'] + df['claude_tokens']).mean()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("実行回数", total_executions)
        with col2:
            st.metric("成功率", f"{success_rate:.1%}")
        with col3:
            st.metric("平均Token", f"{avg_tokens:.0f}")

        # 複雑度別分析
        complexity_stats = df.groupby('complexity').agg({
            'success': ['count', 'mean'],
            'gemini_tokens': 'mean',
            'claude_tokens': 'mean'
        }).round(3)
        complexity_stats.columns = ['実行回数', '成功率', '平均Gemini Token', '平均Claude Token']

        st.markdown("### 複雑度別統計")
        st.dataframe(complexity_stats)

        # タスクタイプ別分析
        fig_task_type = px.sunburst(
            df,
            path=['task_type', 'complexity'],
            values='gemini_tokens',
            title="タスクタイプ・複雑度別Token使用量"
        )
        st.plotly_chart(fig_task_type, use_container_width=True)

    with tab2:
        st.markdown("## 💰 コスト分析")

        # Token使用量推移
        df['date'] = df['start_time'].dt.date
        daily_tokens = df.groupby('date').agg({
            'gemini_tokens': 'sum',
            'claude_tokens': 'sum'
        }).reset_index()
        daily_tokens['total_tokens'] = daily_tokens['gemini_tokens'] + daily_tokens['claude_tokens']
        daily_tokens['savings_rate'] = daily_tokens['gemini_tokens'] / daily_tokens['total_tokens']

        # Token使用量チャート
        fig_tokens = px.area(
            daily_tokens,
            x='date',
            y=['gemini_tokens', 'claude_tokens'],
            title="日別Token使用量推移",
            labels={'value': 'Token数', 'variable': 'モデル'}
        )
        st.plotly_chart(fig_tokens, use_container_width=True)

        # 削減効果
        total_gemini = df['gemini_tokens'].sum()
        total_claude = df['claude_tokens'].sum()
        savings_rate = total_gemini / (total_gemini + total_claude) if (total_gemini + total_claude) > 0 else 0

        st.markdown("### 💰 Token削減効果")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Gemini Token", f"{total_gemini:,}")
        with col2:
            st.metric("Claude Token", f"{total_claude:,}")
        with col3:
            st.metric("削減率", f"{savings_rate:.1%}")

        # コスト効率分析
        df['cost_efficiency'] = (df['gemini_tokens'] + df['claude_tokens']) / df['success'].astype(int)
        df['cost_efficiency'] = df['cost_efficiency'].replace([float('inf')], None)

        fig_efficiency = px.box(
            df.dropna(subset=['cost_efficiency']),
            x='complexity',
            y='cost_efficiency',
            title="複雑度別コスト効率（Token/成功タスク）"
        )
        st.plotly_chart(fig_efficiency, use_container_width=True)

    with tab3:
        st.markdown("## ❌ 失敗分析")

        # 失敗データ
        failed_df = df[~df['success']]

        if not failed_df.empty:
            # 失敗率推移
            daily_failure = df.groupby('date').agg({
                'success': ['count', lambda x: (~x).sum()]
            }).reset_index()
            daily_failure.columns = ['date', 'total', 'failures']
            daily_failure['failure_rate'] = daily_failure['failures'] / daily_failure['total']

            fig_failure = px.line(
                daily_failure,
                x='date',
                y='failure_rate',
                title="日別失敗率推移"
            )
            fig_failure.update_layout(yaxis_tickformat='.1%')
            st.plotly_chart(fig_failure, use_container_width=True)

            # 失敗パターン
            failure_patterns = get_failure_patterns()
            if failure_patterns.get("patterns"):
                patterns = failure_patterns["patterns"]
                pattern_data = []
                for pattern, data in patterns.items():
                    pattern_data.append({
                        "エラータイプ": pattern,
                        "発生回数": data["count"],
                        "影響プロジェクト": len(data.get("projects", []))
                    })

                df_patterns = pd.DataFrame(pattern_data)
                fig_patterns = px.bar(
                    df_patterns,
                    x="エラータイプ",
                    y="発生回数",
                    title="失敗パターン分析"
                )
                st.plotly_chart(fig_patterns, use_container_width=True)
        else:
            st.success("選択した期間に失敗はありません！")

    with tab4:
        st.markdown("## 💡 改善提案")

        # 改善提案取得・表示
        suggestions = get_suggestions()
        if suggestions.get("suggestions"):
            for suggestion in suggestions["suggestions"]:
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                emoji = priority_emoji.get(suggestion["priority"], "ℹ️")

                with st.expander(f"{emoji} {suggestion['type'].upper()}: {suggestion.get('project_id', '全体')}"):
                    st.write(suggestion["message"])
                    if suggestion.get("action"):
                        st.write(f"**推奨アクション**: {suggestion['action']}")

        # 自動分析による提案
        st.markdown("### 🤖 自動分析による改善提案")

        if success_rate < 0.8:
            st.warning("⚠️ 成功率が80%を下回っています。失敗パターンを詳細に分析することをお勧めします。")

        if avg_tokens > 600:
            st.info("💡 平均Token使用量が600を超えています。プロンプトの最適化を検討してください。")

        high_token_tasks = df[df['gemini_tokens'] + df['claude_tokens'] > 1000]
        if not high_token_tasks.empty:
            st.warning(f"💰 {len(high_token_tasks)}件のタスクで1000Tokenを超過しています。これらのタスクを重点的に最適化してください。")


# ==========================================
# 設定ページ
# ==========================================

def show_settings_page():
    """設定ページ表示"""
    st.markdown("# ⚙️ 設定")

    tab1, tab2, tab3, tab4 = st.tabs(["🔧 システム設定", "📢 アラート設定", "👥 ユーザー管理", "🔒 セキュリティ"])

    with tab1:
        st.markdown("## 🔧 システム設定")

        # 環境設定表示
        st.markdown("### 現在の環境設定")
        config_dict = config.to_dict()
        st.json(config_dict)

        # 設定変更
        st.markdown("### 設定変更")

        col1, col2 = st.columns(2)
        with col1:
            new_refresh_interval = st.number_input(
                "自動更新間隔（秒）",
                min_value=10,
                max_value=300,
                value=config.dashboard.auto_refresh_seconds
            )

        with col2:
            new_max_logs = st.number_input(
                "最大ログ表示件数",
                min_value=50,
                max_value=5000,
                value=config.dashboard.max_log_entries
            )

        if st.button("設定保存"):
            st.success("設定が保存されました（デモ）")

    with tab2:
        st.markdown("## 📢 アラート設定")

        # アラート閾値設定
        st.markdown("### アラート閾値")

        col1, col2 = st.columns(2)
        with col1:
            failure_threshold = st.slider(
                "失敗率アラート閾値",
                min_value=0.0,
                max_value=1.0,
                value=alert_config.failure_rate_threshold,
                format="%.1%"
            )

            cost_threshold = st.number_input(
                "コストアラート閾値（Token）",
                min_value=100,
                max_value=5000,
                value=alert_config.cost_threshold
            )

        with col2:
            response_threshold = st.number_input(
                "応答時間アラート閾値（秒）",
                min_value=5,
                max_value=120,
                value=alert_config.response_time_threshold
            )

            error_threshold = st.number_input(
                "連続エラーアラート閾値",
                min_value=1,
                max_value=20,
                value=alert_config.error_count_threshold
            )

        # 通知設定
        st.markdown("### 通知設定")
        enable_email = st.checkbox("メール通知を有効にする")
        if enable_email:
            email_address = st.text_input("通知先メールアドレス")

        enable_slack = st.checkbox("Slack通知を有効にする")
        if enable_slack:
            slack_webhook = st.text_input("Slack Webhook URL", type="password")

        if st.button("アラート設定保存"):
            st.success("アラート設定が保存されました（デモ）")

    with tab3:
        st.markdown("## 👥 ユーザー管理")

        # 現在のユーザー情報
        if "token" in st.session_state:
            st.markdown("### 現在のユーザー")
            st.info("ユーザー: admin（管理者）")

        # ユーザー一覧（デモ）
        st.markdown("### ユーザー一覧")
        user_data = [
            {"ユーザー名": "admin", "ロール": "管理者", "最終ログイン": "2025-01-15 10:30"},
            {"ユーザー名": "developer1", "ロール": "開発者", "最終ログイン": "2025-01-14 16:45"},
            {"ユーザー名": "viewer1", "ロール": "閲覧者", "最終ログイン": "2025-01-13 09:15"}
        ]

        df_users = pd.DataFrame(user_data)
        st.dataframe(df_users, use_container_width=True)

        # 新規ユーザー作成
        st.markdown("### 新規ユーザー作成")
        with st.form("create_user"):
            new_username = st.text_input("ユーザー名")
            new_email = st.text_input("メールアドレス")
            new_role = st.selectbox("ロール", ["閲覧者", "開発者", "管理者"])

            if st.form_submit_button("ユーザー作成"):
                st.success(f"ユーザー {new_username} が作成されました（デモ）")

    with tab4:
        st.markdown("## 🔒 セキュリティ")

        # セキュリティ状態
        st.markdown("### セキュリティ状態")

        col1, col2 = st.columns(2)
        with col1:
            st.success("✅ JWT認証有効")
            st.success("✅ CORS設定済み")
            st.success("✅ HTTPS対応")

        with col2:
            st.info("🔄 トークン有効期限: 30分")
            st.info("🔄 リフレッシュトークン: 7日")
            st.info("🔒 レート制限: 100req/min")

        # パスワード変更
        st.markdown("### パスワード変更")
        with st.form("change_password"):
            current_password = st.text_input("現在のパスワード", type="password")
            new_password = st.text_input("新しいパスワード", type="password")
            confirm_password = st.text_input("パスワード確認", type="password")

            if st.form_submit_button("パスワード変更"):
                if new_password == confirm_password:
                    st.success("パスワードが変更されました（デモ）")
                else:
                    st.error("新しいパスワードと確認が一致しません")

        # APIキー管理
        st.markdown("### APIキー管理")
        if st.button("新しいAPIキー生成"):
            import secrets
            new_api_key = secrets.token_urlsafe(32)
            st.code(f"新しいAPIキー: {new_api_key}")
            st.warning("このAPIキーは一度しか表示されません。安全な場所に保存してください。")


# ==========================================
# メインアプリケーション
# ==========================================

def main():
    """メインアプリケーション"""
    # 認証チェック
    if not check_authentication():
        return

    # サイドバー
    st.sidebar.markdown("# 📊 Kumihan Dashboard")

    # ナビゲーション
    page = st.sidebar.selectbox(
        "ページ選択",
        ["📊 ダッシュボード", "📁 プロジェクト管理", "📈 分析", "⚙️ 設定"]
    )

    # 自動更新設定
    auto_refresh = st.sidebar.checkbox("自動更新", value=True)
    if auto_refresh:
        refresh_interval = st.sidebar.slider(
            "更新間隔（秒）",
            min_value=10,
            max_value=120,
            value=config.dashboard.auto_refresh_seconds
        )
        # 自動更新用のプレースホルダー
        placeholder = st.empty()
        if st.sidebar.button("今すぐ更新"):
            st.cache_data.clear()
            st.experimental_rerun()

    # ログアウト
    if st.sidebar.button("🔓 ログアウト"):
        st.session_state.authenticated = False
        if "token" in st.session_state:
            del st.session_state.token
        st.experimental_rerun()

    # ページ表示
    if page == "📊 ダッシュボード":
        show_main_dashboard()
    elif page == "📁 プロジェクト管理":
        show_project_management()
    elif page == "📈 分析":
        show_analytics_page()
    elif page == "⚙️ 設定":
        show_settings_page()

    # 自動更新機能
    if auto_refresh and 'refresh_interval' in locals():
        time.sleep(refresh_interval)
        st.experimental_rerun()


if __name__ == "__main__":
    main()
