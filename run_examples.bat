@echo off
setlocal enabledelayedexpansion
rem Windows character encoding safe version
rem This script works with both UTF-8 and Shift-JIS environments

rem Try to set UTF-8 encoding, but don't fail if it doesn't work
chcp 65001 > nul 2>&1

title Kumihan-Formatter - サンプル一括実行スクリプト

echo.
echo ==========================================
echo  Kumihan-Formatter - サンプル一括実行
echo ==========================================
echo すべてのサンプルファイルをHTMLに変換
echo 出力先: examples/output/
echo ==========================================
echo.

rem Check if setup has been completed
if not exist ".venv\Scripts\activate.bat" (
    echo [警告] セットアップがまだ完了していません！
    echo.
    echo 最初にセットアップを実行してください：
    echo   1. ダブルクリック: setup.bat
    echo   2. セットアップが完了するまで待機
    echo   3. その後このスクリプトを再実行
    echo.
    echo ヘルプについては: LAUNCH_GUIDE.md を参照
    echo.
    pause
    exit /b 1
)
echo [OK] セットアップを検出、続行します...

rem Check Python version
echo [デバッグ] Python インストールを確認中...
python --version > nul 2>&1
if errorlevel 1 (
    echo [エラー] Python が見つかりません
    echo.
    echo Python 3.9 以上をインストールしてください：
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [OK] Python が見つかりました: !PYTHON_VERSION!
)

rem Check virtual environment
echo [デバッグ] 仮想環境を確認中...
if exist ".venv\Scripts\activate.bat" (
    echo [デバッグ] 仮想環境を発見、アクティベート中...
    call .venv\Scripts\activate.bat
    if errorlevel 1 (
        echo [エラー] 仮想環境のアクティベートに失敗
        echo.
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
    echo [OK] 仮想環境をアクティベートしました
) else (
    echo [警告] 仮想環境が見つかりません
    echo 最初に kumihan_convert.bat を実行してセットアップを完了してください
    echo.
    pause
    exit /b 1
)

rem Check dependencies
echo [デバッグ] 依存関係を確認中...
%PYTHON_CMD% -c "import click, jinja2, rich" 2>nul
if errorlevel 1 (
    echo [エラー] 必要なライブラリが不足しています
    echo 最初に kumihan_convert.bat を実行してセットアップを完了してください
    echo.
    pause
    exit /b 1
)

echo [OK] 環境確認完了
echo.

rem Prepare output directory
echo [デバッグ] 出力ディレクトリを準備中...
set "OUTPUT_BASE=examples\output"
if not exist "%OUTPUT_BASE%" mkdir "%OUTPUT_BASE%"
echo [OK] 出力ディレクトリの準備完了: %OUTPUT_BASE%

echo [デバッグ] サンプル変換を開始...
echo.

rem Sample 1: basic
echo [1/3] 基本サンプル (sample.txt)
set "OUTPUT_DIR=%OUTPUT_BASE%\basic"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

set PYTHONIOENCODING=utf-8
%PYTHON_CMD% -m kumihan_formatter "examples\input\sample.txt" -o "%OUTPUT_DIR%" --no-preview
if errorlevel 1 (
    echo エラー: 基本サンプルの変換に失敗
    goto error_end
) else (
    echo OK: 基本サンプル完了 -> %OUTPUT_DIR%
)
echo.

rem Sample 2: advanced
echo [2/3] 高度なサンプル (comprehensive-sample.txt)
set "OUTPUT_DIR=%OUTPUT_BASE%\advanced"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

set PYTHONIOENCODING=utf-8
%PYTHON_CMD% -m kumihan_formatter "examples\input\comprehensive-sample.txt" -o "%OUTPUT_DIR%" --no-preview
if errorlevel 1 (
    echo エラー: 高度なサンプルの変換に失敗
    goto error_end
) else (
    echo OK: 高度なサンプル完了 -> %OUTPUT_DIR%
)
echo.

rem Sample 3: showcase
echo [3/3] 機能ショーケース (--generate-sample)
set "OUTPUT_DIR=%OUTPUT_BASE%\showcase"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

set PYTHONIOENCODING=utf-8
%PYTHON_CMD% -m kumihan_formatter --generate-sample -o "%OUTPUT_DIR%" --no-preview
if errorlevel 1 (
    echo エラー: ショーケースサンプルの変換に失敗
    goto error_end
) else (
    echo OK: ショーケースサンプル完了 -> %OUTPUT_DIR%
)
echo.

echo ==========================================
echo すべてのサンプル変換が完了しました！
echo ==========================================
echo.
echo 生成されたファイル:
echo   examples\output\basic\        - 基本的な記法のサンプル
echo   examples\output\advanced\     - 高度な記法のサンプル
echo   examples\output\showcase\     - 機能ショーケース
echo.
echo HTMLファイルをブラウザで確認してください
echo.
echo 出力フォルダを開きますか？ [Y/N]
set /p choice="> "
if /i "%choice%"=="y" (
    explorer "%OUTPUT_BASE%"
)

echo.
echo 何かキーを押して終了してください...
pause > nul
exit /b 0

:error_end
echo.
echo トラブルシューティング:
echo   1. 最初に kumihan_convert.bat を実行してセットアップを完了
echo   2. エラーメッセージを確認して問題を修正
echo   3. ヘルプについては FIRST_RUN.md を参照
echo.
pause
exit /b 1