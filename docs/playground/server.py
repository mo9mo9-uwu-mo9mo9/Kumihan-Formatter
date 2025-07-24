#!/usr/bin/env python3
"""
Kumihan Formatter コードプレイグラウンド用Webサーバー
Issue #580 - ドキュメント改善 Phase 2

リアルタイムプレビュー機能とDX指標収集を提供
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# FastAPIとUvicorn
try:
    import uvicorn
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
except ImportError:
    print("FastAPI dependencies not found. Installing...")
    os.system("pip install fastapi uvicorn jinja2")
    import uvicorn
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates

# プロジェクトルートの追加
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from kumihan_formatter import parser, renderer
from kumihan_formatter.core.utilities.logger import get_logger

# ロガー設定
logger = get_logger(__name__)

# FastAPIアプリ初期化
app = FastAPI(
    title="Kumihan Formatter Playground",
    description="リアルタイムプレビュー機能付きKumihan記法プレイグラウンド",
    version="1.0.0",
)

# 静的ファイルとテンプレート設定
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"

# ディレクトリが存在しない場合は作成
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# DX指標データ収集用
dx_metrics = {"sessions": [], "conversions": [], "errors": [], "performance": []}


@app.get("/", response_class=HTMLResponse)
async def playground_home(request: Request):
    """プレイグラウンドのメインページ"""
    return templates.TemplateResponse(
        "playground.html", {"request": request, "title": "Kumihan Formatter Playground"}
    )


@app.post("/api/convert")
async def convert_kumihan(request: Request):
    """Kumihan記法をHTMLに変換"""
    try:
        data = await request.json()
        kumihan_text = data.get("text", "")

        if not kumihan_text.strip():
            return {"html": "", "success": True}

        # タイムスタンプ記録（パフォーマンス測定）
        start_time = time.time()

        # Kumihan記法をHTMLに変換
        parsed_content = parser.parse(kumihan_text)
        html_output = renderer.render(parsed_content)

        end_time = time.time()
        processing_time = end_time - start_time

        # DX指標記録
        dx_metrics["performance"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
                "input_length": len(kumihan_text),
                "output_length": len(html_output),
            }
        )

        logger.info(f"Conversion completed in {processing_time:.3f}s")

        return {
            "html": html_output,
            "success": True,
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")

        # エラー記録
        dx_metrics["errors"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "input": kumihan_text[:100] if "kumihan_text" in locals() else "",
            }
        )

        return {
            "html": f"<div class='error'>変換エラー: {str(e)}</div>",
            "success": False,
            "error": str(e),
        }


@app.post("/api/metrics/session")
async def record_session_start(request: Request):
    """セッション開始を記録"""
    try:
        data = await request.json()
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "user_agent": request.headers.get("user-agent", ""),
            "referrer": request.headers.get("referer", ""),
            "session_id": data.get("session_id", ""),
        }

        dx_metrics["sessions"].append(session_data)
        logger.info(f"Session started: {session_data['session_id']}")

        return {"success": True}

    except Exception as e:
        logger.error(f"Session recording error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.get("/api/metrics/summary")
async def get_metrics_summary():
    """DX指標サマリーを取得"""
    try:
        total_sessions = len(dx_metrics["sessions"])
        total_conversions = len(dx_metrics["performance"])
        total_errors = len(dx_metrics["errors"])

        avg_processing_time = 0
        if dx_metrics["performance"]:
            avg_processing_time = sum(
                p["processing_time"] for p in dx_metrics["performance"]
            ) / len(dx_metrics["performance"])

        return {
            "total_sessions": total_sessions,
            "total_conversions": total_conversions,
            "total_errors": total_errors,
            "avg_processing_time": avg_processing_time,
            "error_rate": (total_errors / max(total_conversions, 1)) * 100,
        }

    except Exception as e:
        logger.error(f"Metrics summary error: {str(e)}")
        return {"error": str(e)}


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    logger.info("Starting Kumihan Formatter Playground server...")
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True, log_level="info")
