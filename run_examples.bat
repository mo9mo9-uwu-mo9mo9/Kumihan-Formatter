@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
title Kumihan-Formatter - サンプル実行スクリプト

echo.
echo ==========================================
echo  Kumihan-Formatter - サンプル一括実行
echo ==========================================
echo 📝 全サンプルファイルを一括変換します
echo 🎯 出力先: examples/output/
echo ==========================================
echo.

rem Pythonのバージョン確認
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ エラー: Python が見つかりません
    echo.
    echo Python 3.9 以上をインストールしてください：
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

rem 仮想環境の確認
if exist ".venv\Scripts\activate.bat" (
    echo 🔧 仮想環境をアクティベート中...
    call .venv\Scripts\activate.bat
    set PYTHON_CMD=python
) else (
    echo ⚠️  仮想環境が見つかりません
    echo 💡 kumihan_convert.bat を先に実行してセットアップを完了してください
    echo.
    pause
    exit /b 1
)

rem 依存関係の確認
echo 🔍 依存関係を確認中...
%PYTHON_CMD% -c "import click, jinja2, rich" 2>nul
if errorlevel 1 (
    echo ❌ エラー: 必要なライブラリが不足しています
    echo 💡 kumihan_convert.bat を先に実行してセットアップを完了してください
    echo.
    pause
    exit /b 1
)

echo ✅ 環境確認完了
echo.

rem 出力ディレクトリの準備
set "OUTPUT_BASE=examples\output"
if not exist "%OUTPUT_BASE%" mkdir "%OUTPUT_BASE%"

echo 🚀 サンプル変換を開始します...
echo.

rem サンプル1: basic
echo 📝 [1/3] 基本サンプル (sample.txt)
set "OUTPUT_DIR=%OUTPUT_BASE%\basic"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

%PYTHON_CMD% -m kumihan_formatter "examples\input\sample.txt" -o "%OUTPUT_DIR%" --no-preview
if errorlevel 1 (
    echo ❌ エラー: basic サンプルの変換に失敗
    goto error_end
) else (
    echo ✅ basic サンプル完了 → %OUTPUT_DIR%
)
echo.

rem サンプル2: advanced
echo 📝 [2/3] 高度なサンプル (comprehensive-sample.txt)
set "OUTPUT_DIR=%OUTPUT_BASE%\advanced"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

%PYTHON_CMD% -m kumihan_formatter "examples\input\comprehensive-sample.txt" -o "%OUTPUT_DIR%" --no-preview
if errorlevel 1 (
    echo ❌ エラー: advanced サンプルの変換に失敗
    goto error_end
) else (
    echo ✅ advanced サンプル完了 → %OUTPUT_DIR%
)
echo.

rem サンプル3: showcase
echo 📝 [3/3] 機能ショーケース (--generate-sample)
set "OUTPUT_DIR=%OUTPUT_BASE%\showcase"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

%PYTHON_CMD% -m kumihan_formatter --generate-sample -o "%OUTPUT_DIR%" --no-preview
if errorlevel 1 (
    echo ❌ エラー: showcase サンプルの変換に失敗
    goto error_end
) else (
    echo ✅ showcase サンプル完了 → %OUTPUT_DIR%
)
echo.

echo ==========================================
echo ✅ 全サンプルの変換が完了しました！
echo ==========================================
echo.
echo 📁 生成されたファイル:
echo   examples\output\basic\        - 基本的な記法のサンプル
echo   examples\output\advanced\     - 高度な記法のサンプル
echo   examples\output\showcase\     - 全機能のショーケース
echo.
echo 🌐 HTMLファイルをブラウザで確認してください
echo.
echo 📁 出力フォルダを開きますか？ [Y/N]
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
echo 💡 トラブルシューティング:
echo   1. kumihan_convert.bat を先に実行してセットアップ
echo   2. エラーメッセージを確認して対処
echo   3. FIRST_RUN.md を参照してヘルプを確認
echo.
pause
exit /b 1