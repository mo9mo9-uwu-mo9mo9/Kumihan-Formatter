@echo off
setlocal enabledelayedexpansion
rem Kumihan-Formatter - One-time Setup Script
rem This script automatically sets up everything needed to use Kumihan-Formatter

rem Try to set UTF-8 encoding, but don't fail if it doesn't work
chcp 65001 > nul 2>&1

title Kumihan-Formatter - 初回セットアップ

echo.
echo ==========================================
echo  Kumihan-Formatter - 初回セットアップ
echo ==========================================
echo 必要な環境を自動でセットアップします
echo すぐにKumihan-Formatterを使用できるようになります
echo ==========================================
echo.

rem Check Python version
echo [1/4] Python インストールを確認中...
python --version > nul 2>&1
if errorlevel 1 (
    echo [エラー] Python が見つかりません
    echo.
    echo Python 3.9 以上をインストールしてください：
    echo https://www.python.org/downloads/
    echo.
    echo Python インストール後、再度このセットアップを実行してください。
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [OK] Python が見つかりました: !PYTHON_VERSION!
)

rem Create virtual environment
echo [2/4] 仮想環境を作成中...
if exist ".venv" (
    echo [OK] 仮想環境は既に存在します
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo [エラー] 仮想環境の作成に失敗しました
        echo.
        pause
        exit /b 1
    ) else (
        echo [OK] 仮想環境を作成しました
    )
)

rem Activate virtual environment
echo [3/4] 仮想環境をアクティベート中...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [エラー] 仮想環境のアクティベートに失敗しました
    echo.
    pause
    exit /b 1
) else (
    echo [OK] 仮想環境をアクティベートしました
)

rem Install dependencies
echo [4/4] 依存関係をインストール中...
echo しばらくお待ちください...
python -m pip install -e ".[dev]" --quiet
if errorlevel 1 (
    echo [エラー] 依存関係のインストールに失敗しました
    echo.
    echo インターネット接続を確認して、再度お試しください。
    echo.
    pause
    exit /b 1
) else (
    echo [OK] 依存関係のインストールが完了しました
)

echo.
echo ==========================================
echo  セットアップ完了！
echo ==========================================
echo.
echo これでKumihan-Formatterを使用できます：
echo.
echo 基本的な変換の場合：
echo   - ダブルクリック: kumihan_convert.bat
echo   - .txtファイルをドラッグ&ドロップで変換
echo.
echo サンプルを試す場合：
echo   - ダブルクリック: run_examples.bat
echo   - examples/output/ でサンプル結果を確認
echo.
echo アップデートの場合：
echo   - GitHub releases から最新版をダウンロード
echo   - または: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter
echo.
echo ヘルプの場合：
echo   - 参照: LAUNCH_GUIDE.md
echo   - 参照: FIRST_RUN.md
echo.
echo 何かキーを押して終了してください...
pause > nul