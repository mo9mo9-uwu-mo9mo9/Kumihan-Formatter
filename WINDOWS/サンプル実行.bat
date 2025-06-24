@echo off
setlocal enabledelayedexpansion
rem Windows character encoding safe version
rem This script works with both UTF-8 and Shift-JIS environments

rem Try to set UTF-8 encoding, but don't fail if it doesn't work
chcp 65001 > nul 2>&1

title Kumihan-Formatter - サンプル実行スクリプト

rem カラー出力の有効化（Windows 10以降）
for /f "tokens=3" %%a in ('ver ^| findstr /R "[0-9]"') do set WINVER=%%a
for /f "delims=. tokens=1" %%a in ("%WINVER%") do set MAJOR=%%a
if %MAJOR% geq 10 (
    rem Windows 10以降はANSIカラーコードをサポート
    set "RED=[91m"
    set "GREEN=[92m"
    set "YELLOW=[93m"
    set "BLUE=[94m"
    set "CYAN=[96m"
    set "NC=[0m"
) else (
    rem Windows 10未満はカラーなし
    set "RED="
    set "GREEN="
    set "YELLOW="
    set "BLUE="
    set "CYAN="
    set "NC="
)

echo.
echo ==========================================
echo  Kumihan-Formatter - サンプル一括実行
echo ==========================================
echo 全サンプルファイルをHTMLに変換します
echo 出力先: ../dist/samples/
echo ==========================================
echo.

rem Check if setup has been completed
if not exist "../.venv\Scripts\activate.bat" (
    echo %YELLOW%[警告] セットアップが完了していません！%NC%
    echo.
    echo 先にセットアップを実行してください：
    echo   1. ダブルクリック: 初回セットアップ.bat
    echo   2. セットアップの完了を待つ
    echo   3. その後、このスクリプトを再実行
    echo.
    echo ヘルプ: ../docs/user/LAUNCH_GUIDE.md を参照
    echo.
    echo 何かキーを押して終了してください...
    pause > nul
    exit /b 1
)
echo %GREEN%[完了] セットアップ検出、続行します...%NC%

rem Pythonのバージョン確認
echo %BLUE%[確認] Python環境を確認中...%NC%
python --version > nul 2>&1
if errorlevel 1 (
    echo %RED%[エラー] Python 3 が見つかりません%NC%
    echo.
    echo Python 3.9 以上をインストールしてください：
    echo https://www.python.org/downloads/
    echo.
    echo 何かキーを押して終了してください...
    pause > nul
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %GREEN%[完了] Python検出: !PYTHON_VERSION!%NC%
)

rem 仮想環境の確認
echo %BLUE%[設定] 仮想環境を確認中...%NC%
if exist "../.venv\Scripts\activate.bat" (
    echo %BLUE%[設定] 仮想環境をアクティベート中...%NC%
    call ..\.venv\Scripts\activate.bat
    if errorlevel 1 (
        echo %RED%[エラー] 仮想環境のアクティベートに失敗%NC%
        echo.
        echo 何かキーを押して終了してください...
        pause > nul
        exit /b 1
    )
    set PYTHON_CMD=python
    echo %GREEN%[完了] 仮想環境をアクティベート%NC%
) else (
    echo %RED%[警告] 仮想環境が見つかりません%NC%
    echo %YELLOW%[ヒント] 変換ツール.bat を先に実行してセットアップを完了してください%NC%
    echo.
    echo 何かキーを押して終了してください...
    pause > nul
    exit /b 1
)

rem 依存関係の確認
echo %BLUE%[検証] 依存関係を確認中...%NC%
%PYTHON_CMD% -c "import click, jinja2, rich" 2>nul
if errorlevel 1 (
    echo %RED%[エラー] 必要なライブラリが不足しています%NC%
    echo %YELLOW%[ヒント] 変換ツール.bat を先に実行してセットアップを完了してください%NC%
    echo.
    echo 何かキーを押して終了してください...
    pause > nul
    exit /b 1
)

echo %GREEN%[完了] 環境確認完了%NC%
echo.

rem 出力ディレクトリの準備
set "OUTPUT_BASE=..\dist\samples"

rem Check if output directory exists and is not empty
if exist "%OUTPUT_BASE%" (
    dir /b "%OUTPUT_BASE%" | findstr . > nul
    if not errorlevel 1 (
        echo %YELLOW%[警告] 出力ディレクトリ内にファイルが存在します%NC%
        echo %YELLOW%   以下のファイルが上書きされます:%NC%
        echo.
        for /f "delims=" %%i in ('dir /b "%OUTPUT_BASE%"') do (
            echo %YELLOW%     - %%i%NC%
        )
        echo.
        echo %CYAN%続行しますか？ [Y/n]: %NC%
        set /p confirm=""
        if /i not "!confirm!"=="y" if not "!confirm!"=="" (
            echo %YELLOW%処理を中止しました%NC%
            echo.
            echo 何かキーを押して終了してください...
            pause > nul
            exit /b 0
        )
    )
)

if not exist "%OUTPUT_BASE%" mkdir "%OUTPUT_BASE%"

echo %CYAN%サンプル変換を開始します...%NC%
echo %CYAN%出力先: ../dist/samples/ (自動作成されます)%NC%
echo.

rem 記法表示機能の選択を事前に確認
echo %CYAN%Kumihan記法をHTML表示に切り替える機能があります%NC%
echo %CYAN%記法学習に便利な機能で、ボタン一つで記法とプレビューが切り替えられます%NC%
set /p choice="この機能を使用しますか？ (Y/n): "
echo.

rem 選択に基づいてフラグを設定
if /i "%choice%"=="y" (
    set "SOURCE_TOGGLE_FLAG=--with-source-toggle"
    echo %GREEN%Kumihan記法切り替え機能を有効にして変換します%NC%
) else if "%choice%"=="" (
    set "SOURCE_TOGGLE_FLAG=--with-source-toggle"
    echo %GREEN%Kumihan記法切り替え機能を有効にして変換します%NC%
) else (
    set "SOURCE_TOGGLE_FLAG="
    echo %YELLOW%通常モードで変換します（記法切り替え機能なし）%NC%
)
echo.


rem サンプル1: quickstart
echo %BLUE%[1/4] クイックスタートサンプル (01-quickstart.txt)%NC%
set "OUTPUT_DIR=%OUTPUT_BASE%\01-quickstart"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

set PYTHONIOENCODING=utf-8
%PYTHON_CMD% -m kumihan_formatter convert "..\examples\01-quickstart.txt" -o "%OUTPUT_DIR%" --no-preview %SOURCE_TOGGLE_FLAG%
if errorlevel 1 (
    echo %RED%エラー: quickstart サンプルの変換に失敗%NC%
    goto error_end
) else (
    echo %GREEN%quickstart サンプル完了 -> %OUTPUT_DIR%%NC%
)
echo.

rem サンプル2: basic
echo %BLUE%[2/4] 基本サンプル (02-basic.txt)%NC%
set "OUTPUT_DIR=%OUTPUT_BASE%\02-basic"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

set PYTHONIOENCODING=utf-8
%PYTHON_CMD% -m kumihan_formatter convert "..\examples\02-basic.txt" -o "%OUTPUT_DIR%" --no-preview %SOURCE_TOGGLE_FLAG%
if errorlevel 1 (
    echo %RED%エラー: basic サンプルの変換に失敗%NC%
    goto error_end
) else (
    echo %GREEN%basic サンプル完了 -> %OUTPUT_DIR%%NC%
)
echo.

rem サンプル3: advanced
echo %BLUE%[3/4] 高度なサンプル (03-comprehensive.txt)%NC%
set "OUTPUT_DIR=%OUTPUT_BASE%\03-advanced"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

set PYTHONIOENCODING=utf-8
%PYTHON_CMD% -m kumihan_formatter convert "..\examples\03-comprehensive.txt" -o "%OUTPUT_DIR%" --no-preview %SOURCE_TOGGLE_FLAG%
if errorlevel 1 (
    echo %RED%エラー: advanced サンプルの変換に失敗%NC%
    goto error_end
) else (
    echo %GREEN%advanced サンプル完了 -> %OUTPUT_DIR%%NC%
)
echo.

rem サンプル4: showcase
echo %BLUE%[4/4] 機能ショーケース (--generate-sample)%NC%
set "OUTPUT_DIR=%OUTPUT_BASE%\04-showcase"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

rem Showcaseサンプルは記法表示機能を使用しない（CLAUDE.md仕様）
set PYTHONIOENCODING=utf-8
rem Showcase: 記法表示機能は使用しない（CLAUDE.md仕様）
%PYTHON_CMD% -m kumihan_formatter convert --generate-sample -o "%OUTPUT_DIR%" --no-preview
if errorlevel 1 (
    echo %RED%エラー: showcase サンプルの変換に失敗%NC%
    goto error_end
) else (
    echo %GREEN%showcase サンプル完了 -> %OUTPUT_DIR%%NC%
)
echo.

echo ==========================================
echo %GREEN%全サンプルの変換が完了しました！%NC%
echo ==========================================
echo.
echo %CYAN%生成されたファイル:%NC%
echo   ../dist/samples/01-quickstart/  - クイックスタートチュートリアル
echo   ../dist/samples/02-basic/       - 基本的な記法のサンプル
echo   ../dist/samples/03-advanced/    - 高度な記法のサンプル
echo   ../dist/samples/04-showcase/    - 全機能のショーケース
echo.
echo %YELLOW%HTMLファイルをブラウザで確認してください%NC%
echo.
echo 出力フォルダを開きますか？ [y/N]
set /p choice=""
if /i "%choice%"=="y" (
    explorer "%OUTPUT_BASE%"
)

echo.
echo 何かキーを押して終了してください...
pause > nul
exit /b 0

:error_end
echo.
echo %CYAN%トラブルシューティング:%NC%
echo   1. 変換ツール.bat を先に実行してセットアップを完了してください
echo   2. エラーメッセージを確認して問題を修正してください
echo   3. ヘルプは ../docs/user/FIRST_RUN.md を参照してください
echo.
echo 何かキーを押して終了してください...
pause > nul
exit /b 1