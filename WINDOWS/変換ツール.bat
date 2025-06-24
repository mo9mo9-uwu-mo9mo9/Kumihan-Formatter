@echo off
setlocal enabledelayedexpansion
rem Try to set UTF-8 code page, but don't fail if it doesn't work
chcp 65001 > nul 2>&1
if errorlevel 1 (
    rem Fallback: Try to set UTF-8 via environment
    set PYTHONIOENCODING=utf-8
)
title Kumihan-Formatter - CoC6th Text to HTML Converter

echo.
echo ==========================================
echo  Kumihan-Formatter - Text to HTML Converter
echo ==========================================
echo Convert .txt files to beautiful HTML
echo Usage: Drag and drop .txt file to this window
echo First run will auto-setup environment
echo ==========================================
echo.

rem Check if setup has been completed
if not exist "../.venv\Scripts\activate.bat" (
    echo [WARNING] Setup not completed yet!
    echo.
    echo Please run the setup first:
    echo   1. Double-click: 初回セットアップ.bat
    echo   2. Wait for setup to complete
    echo   3. Then run this script again
    echo.
    echo For help, see: ../docs/user/LAUNCH_GUIDE.md
    echo.
    pause
    exit /b 1
)
echo [OK] Setup detected, proceeding...

rem Pythonのパスとバージョンを確認
python --version > nul 2>&1
if errorlevel 1 (
    echo [エラー] エラー: Python が見つかりません
    echo.
    echo Python 3.9 以上をインストールしてください：
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
) else (
    rem Pythonバージョンチェック（Python 3.9以上）
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    rem バージョン番号を取得（例: 3.13.0 → 3.13）
    for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
        set MAJOR=%%a
        set MINOR=%%b
    )
    rem バージョン比較（3.9以上）
    if !MAJOR! lss 3 (
        echo [エラー] エラー: Python 3.9以上が必要です (現在: !PYTHON_VERSION!)
        echo.
        echo Python 3.9以上をインストールしてください：
        echo https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    ) else if !MAJOR! equ 3 (
        if !MINOR! lss 9 (
            echo [エラー] エラー: Python 3.9以上が必要です (現在: !PYTHON_VERSION!)
            echo.
            echo Python 3.9以上をインストールしてください：
            echo https://www.python.org/downloads/
            echo.
            pause
            exit /b 1
        )
    )
    echo [完了] Python バージョン確認: !PYTHON_VERSION! (>= 3.9)
)

rem 仮想環境の確認とアクティベート
set VENV_CREATED=0
if exist "../.venv\Scripts\activate.bat" (
    echo [設定] 仮想環境をアクティベート中...
    call ..\.venv\Scripts\activate.bat
    set PYTHON_CMD=python
) else (
    echo [警告]  仮想環境が見つかりません。自動で作成します...
    echo [構築]  初回セットアップを実行しています...
    echo.
    
    rem 仮想環境を作成
    echo [パッケージ] 仮想環境を作成中...
    python -m venv ../.venv
    if !errorlevel! equ 0 (
        echo [完了] 仮想環境を作成しました
        set VENV_CREATED=1
    ) else (
        echo [エラー] エラー: 仮想環境の作成に失敗しました
        echo.
        pause
        exit /b 1
    )
    
    rem 仮想環境をアクティベート
    echo [設定] 仮想環境をアクティベート中...
    call ..\.venv\Scripts\activate.bat
    set PYTHON_CMD=python
)

rem Pythonのバージョンを表示
echo [Python] Python バージョン:
%PYTHON_CMD% --version

rem 依存関係の確認と自動インストール
rem 仮想環境を新規作成した場合は必ずインストールを実行
if !VENV_CREATED! equ 1 (
    echo [ドキュメント] 新規仮想環境に依存関係をインストール中...
    echo [インストール] パッケージをインストール中... (しばらくお待ちください)
    echo.
    
    %PYTHON_CMD% -m pip install -e "../[dev]" --quiet
    if !errorlevel! equ 0 (
        echo [完了] 依存関係のインストールが完了しました
    ) else (
        echo [エラー] エラー: 依存関係のインストールに失敗しました
        echo.
        echo 手動で以下のコマンドを実行してください：
        echo     ..\.venv\Scripts\activate.bat
        echo     pip install -e "../[dev]"
        echo.
        pause
        exit /b 1
    )
) else (
    rem 既存の仮想環境の場合は依存関係を確認
    echo [検証] 依存関係を確認中...
    %PYTHON_CMD% -c "import click, jinja2, rich" 2>nul
    if errorlevel 1 (
        echo [ドキュメント] 必要なライブラリが不足しています。自動でインストールします...
        echo [インストール] パッケージをインストール中... (しばらくお待ちください)
        echo.
        
        %PYTHON_CMD% -m pip install -e "../[dev]" --quiet
        if !errorlevel! equ 0 (
            echo [完了] 依存関係のインストールが完了しました
        ) else (
            echo [エラー] エラー: 依存関係のインストールに失敗しました
            echo.
            echo 手動で以下のコマンドを実行してください：
            echo     ..\.venv\Scripts\activate.bat
            echo     pip install -e "../[dev]"
            echo.
            pause
            exit /b 1
        )
    ) else (
        echo [完了] 依存関係の確認完了
    )
)

rem 実行コンテキストの検出と出力先の決定
set "SCRIPT_PATH=%~f0"
echo %SCRIPT_PATH% | findstr /i "Desktop" >nul
if %errorlevel%==0 (
    rem デスクトップから実行された場合
    set "OUTPUT_DIR=%USERPROFILE%\Desktop\Kumihan_Output"
    echo [PC] デスクトップ実行を検出しました
    echo [フォルダ] 出力先: !OUTPUT_DIR!
    if not exist "!OUTPUT_DIR!" mkdir "!OUTPUT_DIR!"
) else (
    rem プロジェクト内から実行された場合
    set "OUTPUT_DIR=..\dist"
    echo [設定] プロジェクト内実行を検出しました
    echo [フォルダ] 出力先: !OUTPUT_DIR!
)
echo.

rem 引数がある場合（ドラッグ&ドロップされた場合）
if "%~1"=="" goto interactive_mode

rem ドラッグ&ドロップモード
echo [ファイル] 処理ファイル: %~nx1
echo.

rem ファイル拡張子をチェック
if /i not "%~x1"==".txt" (
    echo [エラー] エラー: .txt ファイルのみ対応しています
    echo   指定されたファイル: %~nx1
    echo.
    pause
    exit /b 1
)

rem ファイルの存在を確認
if not exist "%~1" (
    echo [エラー] エラー: ファイルが見つかりません
    echo   ファイル: %~1
    echo.
    pause
    exit /b 1
)

echo [変換] 変換を開始します...
echo.

rem 変換実行（エンコーディング設定付き）
set PYTHONIOENCODING=utf-8
%PYTHON_CMD% -m kumihan_formatter "%~1" -o "!OUTPUT_DIR!"
if errorlevel 1 (
    echo.
    echo [エラー] 変換中にエラーが発生しました
    echo.
    pause
    exit /b 1
)

echo.
echo [完了] 変換が完了しました！
echo [フォルダ] 出力フォルダを開きますか？ [Y/N]
set /p choice="> "
if /i "%choice%"=="y" (
    explorer "!OUTPUT_DIR!"
)

echo.
echo 何かキーを押して終了してください...
pause > nul
exit /b 0

:interactive_mode
rem 対話モード
echo [ヒント] 使い方:
echo   1. この画面に .txt ファイルをドラッグ&ドロップ
echo   2. または、ファイルパスを直接入力
echo.

set /p input_file="[ファイル] 変換したい .txt ファイルのパス: "

rem 入力チェック
if "%input_file%"=="" (
    echo [エラー] ファイルパスが入力されていません
    echo.
    pause
    exit /b 1
)

rem セキュリティ: 入力パスの検証
:validate_input
rem 危険な文字をチェック（コマンドインジェクション対策）
echo %input_file% | findstr /R "[;&|<>^`$(){}[\]\\!]" >nul
if %errorlevel% equ 0 (
    echo [エラー] セキュリティエラー: ファイルパスに無効な文字が含まれています
    echo   使用できない文字: ; ^& ^| ^< ^> ` $ ^( ^) { } [ ] \ !
    echo.
    pause
    exit /b 1
)

rem パストラバーサル攻撃対策
echo %input_file% | findstr /C:".." >nul
if %errorlevel% equ 0 (
    echo [エラー] セキュリティエラー: 相対パス参照は許可されていません
    echo.
    pause
    exit /b 1
)

rem クォートを安全に除去
set "input_file=%input_file:"=%"

rem ファイルの存在確認
if not exist "%input_file%" (
    echo [エラー] エラー: ファイルが見つかりません
    echo   ファイル: %input_file%
    echo.
    pause
    exit /b 1
)

rem 拡張子チェック
for %%i in ("%input_file%") do set ext=%%~xi
if /i not "%ext%"==".txt" (
    echo [エラー] エラー: .txt ファイルのみ対応しています
    echo   指定されたファイル: %input_file%
    echo.
    pause
    exit /b 1
)

echo.
echo [変換] 変換を開始します...
echo.

rem 変換実行（エンコーディング設定付き）
set PYTHONIOENCODING=utf-8
%PYTHON_CMD% -m kumihan_formatter "%input_file%" -o "!OUTPUT_DIR!"
if errorlevel 1 (
    echo.
    echo [エラー] 変換中にエラーが発生しました
    echo.
    pause
    exit /b 1
)

echo.
echo [完了] 変換が完了しました！
echo [フォルダ] 出力フォルダを開きますか？ [Y/N]
set /p choice="> "
if /i "%choice%"=="y" (
    explorer "!OUTPUT_DIR!"
)

echo.
echo 何かキーを押して終了してください...
pause > nul