@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM Windows用 Kumihan記法構文チェッカー
REM ダブルクリックで実行可能

echo.
echo ==========================================
echo  Kumihan-Formatter - Syntax Checker
echo ==========================================
echo Kumihan記法の構文をチェックします
echo ドラッグ&ドロップでファイルを指定できます
echo ==========================================
echo.

REM スクリプトのディレクトリに移動
cd /d "%~dp0"

REM Python環境の確認
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [エラー] Python が見つかりません
    echo.
    echo Python 3.9 以上をインストールしてください：
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM 仮想環境の確認
if not exist "..\\.venv" (
    echo [警告] 仮想環境が見つかりません
    echo [ヒント] 変換ツール.bat を先に実行してセットアップを完了してください
    echo.
    pause
    exit /b 1
)

echo [設定] 仮想環境をアクティベート中...
call "..\\.venv\\Scripts\\activate.bat"

REM 依存関係の確認
python -c "import click, jinja2, rich" 2>nul
if %errorlevel% neq 0 (
    echo [エラー] 必要なライブラリが不足しています
    echo [ヒント] 変換ツール.bat を先に実行してセットアップを完了してください
    echo.
    pause
    exit /b 1
)

echo [完了] 環境確認完了
echo.

REM 引数の処理
if "%~1"=="" (
    REM ファイル指定なし - 対話モード
    call :interactive_mode
) else (
    REM ファイル指定あり - 直接チェック
    call :check_files %*
)

echo.
echo 何かキーを押して終了してください...
pause > nul
exit /b 0

:interactive_mode
echo [対話モード] ファイルまたはフォルダを指定してください
echo.
echo 使用方法:
echo   1. ファイルパス入力: 例) example.txt
echo   2. フォルダパス入力: 例) examples
echo   3. ワイルドカード: 例) *.txt
echo   4. 空白で区切って複数指定可能
echo.
set /p "INPUT=チェックするファイル/フォルダ: "

if "!INPUT!"=="" (
    echo [情報] ファイルが指定されませんでした
    goto :eof
)

REM 再帰検索の確認
set /p "RECURSIVE=フォルダを再帰的に検索しますか？ [Y/n]: "
if /i "!RECURSIVE!"=="n" (
    set RECURSIVE_FLAG=
) else (
    set RECURSIVE_FLAG=-r
)

REM 修正提案の確認
set /p "SUGGESTIONS=修正提案を表示しますか？ [Y/n]: "
if /i "!SUGGESTIONS!"=="n" (
    set SUGGESTIONS_FLAG=--no-suggestions
) else (
    set SUGGESTIONS_FLAG=
)

echo.
echo [実行] 構文チェックを開始します...
python -m kumihan_formatter check-syntax !INPUT! !RECURSIVE_FLAG! !SUGGESTIONS_FLAG!
goto :eof

:check_files
echo [実行] 指定されたファイルをチェックします...
echo ファイル: %*
echo.

REM ドラッグ&ドロップされたファイルの処理
set "FILES="
:loop
if "%~1"=="" goto :execute_check
set "FILES=!FILES! "%~1""
shift
goto :loop

:execute_check
python -m kumihan_formatter check-syntax !FILES! -r
goto :eof