@echo off
setlocal EnableDelayedExpansion

REM ============================================
REM Kumihan-Formatter テスト用記法網羅ファイル生成
REM ダブルクリック実行用 Windows バッチファイル
REM ============================================

echo.
echo ==========================================
echo  Kumihan-Formatter テスト用記法網羅ファイル生成
echo ==========================================
echo.

REM 現在のディレクトリを保存
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 出力先をdev/test-output内に設定
set TIMESTAMP=%date:~0,4%-%date:~5,2%-%date:~8,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%
set TIMESTAMP=!TIMESTAMP: =0!
set OUTPUT_DIR=%SCRIPT_DIR%test-output\!TIMESTAMP!
set TEST_FILE=test_patterns.txt

echo 出力先: %OUTPUT_DIR%
echo テストファイル名: %TEST_FILE%
echo.

REM 出力ディレクトリを作成
if not exist "%OUTPUT_DIR%" (
    mkdir "%OUTPUT_DIR%"
    echo 出力ディレクトリを作成しました: %OUTPUT_DIR%
)

REM Python環境の検出
set PYTHON_CMD=
set VENV_PATH=

REM 1. 仮想環境の確認（.venv）
if exist "..\\.venv\\Scripts\\python.exe" (
    set PYTHON_CMD=..\\.venv\\Scripts\\python.exe
    set VENV_PATH=..\\.venv\\Scripts\\activate.bat
    echo [✓] 仮想環境を検出: .venv
) else if exist "..\\venv\\Scripts\\python.exe" (
    set PYTHON_CMD=..\\venv\\Scripts\\python.exe
    set VENV_PATH=..\\venv\\Scripts\\activate.bat
    echo [✓] 仮想環境を検出: venv
)

REM 2. システムPythonの確認（仮想環境が見つからない場合）
if "!PYTHON_CMD!"=="" (
    REM Pythonの存在確認
    python --version >nul 2>&1
    if !errorlevel! equ 0 (
        REM Pythonバージョンチェック（Python 3.9以上）
        for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
        REM バージョン番号を取得（例: 3.13.0 → 3.13）
        for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
            set MAJOR=%%a
            set MINOR=%%b
        )
        REM バージョン比較（3.9以上）
        if !MAJOR! gtr 3 (
            set PYTHON_CMD=python
            echo [✓] システムPythonを使用 (バージョン: !PYTHON_VERSION! ^>= 3.9)
        ) else if !MAJOR! equ 3 (
            if !MINOR! geq 9 (
                set PYTHON_CMD=python
                echo [✓] システムPythonを使用 (バージョン: !PYTHON_VERSION! ^>= 3.9)
            ) else (
                echo [✗] エラー: Python 3.9以上が必要です (現在: !PYTHON_VERSION!)
                echo.
                echo Python 3.9以上をインストールするか、
                echo 仮想環境（.venv または venv）を作成してください。
                echo.
                pause
                exit /b 1
            )
        ) else (
            echo [✗] エラー: Python 3.9以上が必要です (現在: !PYTHON_VERSION!)
            echo.
            echo Python 3.9以上をインストールしてください。
            echo.
            pause
            exit /b 1
        )
    ) else (
        echo [✗] エラー: Pythonが見つかりません
        echo.
        echo Python 3.9以上をインストールするか、
        echo 仮想環境（.venv または venv）を作成してください。
        echo.
        pause
        exit /b 1
    )
)

REM 仮想環境の自動作成・アクティベート
set VENV_CREATED=0
if not "!VENV_PATH!"=="" (
    echo [→] 仮想環境をアクティベート中...
    call "!VENV_PATH!"
    if !errorlevel! neq 0 (
        echo [✗] エラー: 仮想環境のアクティベートに失敗
        pause
        exit /b 1
    )
) else if "!PYTHON_CMD!"=="python" (
    REM 仮想環境が見つからない場合は自動作成
    echo [→] 仮想環境が見つかりません。自動で作成します...
    echo [→] 初回セットアップを実行しています...
    echo.
    
    REM 仮想環境を作成
    echo [→] 仮想環境を作成中...
    python -m venv ..\.venv
    if !errorlevel! equ 0 (
        echo [✓] 仮想環境を作成しました
        set PYTHON_CMD=..\\.venv\\Scripts\\python.exe
        set VENV_PATH=..\\.venv\\Scripts\\activate.bat
        set VENV_CREATED=1
        
        REM 仮想環境をアクティベート
        echo [→] 仮想環境をアクティベート中...
        call "!VENV_PATH!"
        if !errorlevel! neq 0 (
            echo [✗] エラー: 仮想環境のアクティベートに失敗
            pause
            exit /b 1
        )
    ) else (
        echo [✗] エラー: 仮想環境の作成に失敗しました
        pause
        exit /b 1
    )
)

REM パッケージの存在確認と自動インストール
REM 仮想環境を新規作成した場合は必ずインストールを実行
if !VENV_CREATED! equ 1 (
    echo [→] 新規仮想環境にKumihan-Formatterをインストール中...
    echo [→] パッケージと依存関係をインストール中... (しばらくお待ちください)
    echo.
    
    !PYTHON_CMD! -m pip install -e "..[dev]" --quiet
    if !errorlevel! equ 0 (
        echo [✓] Kumihan-Formatterのインストールが完了しました
    ) else (
        echo [✗] エラー: Kumihan-Formatterのインストールに失敗しました
        echo.
        echo 手動で以下のコマンドを実行してください:
        echo   ..\\.venv\\Scripts\\activate.bat
        echo   pip install -e "..[dev]"
        echo.
        pause
        exit /b 1
    )
) else (
    REM 既存の仮想環境の場合はパッケージの存在を確認
    echo [→] Kumihan-Formatterパッケージを確認中...
    !PYTHON_CMD! -c "import kumihan_formatter" >nul 2>&1
    if !errorlevel! neq 0 (
        echo [→] Kumihan-Formatterが見つかりません。自動でインストールします...
        echo [→] パッケージをインストール中... (しばらくお待ちください)
        echo.
        
        !PYTHON_CMD! -m pip install -e "..[dev]" --quiet
        if !errorlevel! equ 0 (
            echo [✓] Kumihan-Formatterのインストールが完了しました
        ) else (
            echo [✗] エラー: Kumihan-Formatterのインストールに失敗しました
            echo.
            echo 手動で以下のコマンドを実行してください:
            echo   ..\\.venv\\Scripts\\activate.bat
            echo   pip install -e "..[dev]"
            echo.
            pause
            exit /b 1
        )
    ) else (
        echo [✓] Kumihan-Formatterパッケージが利用可能です
    )
)

echo.

REM テスト用記法網羅ファイルの生成
echo [→] テスト用記法網羅ファイルを生成中...
echo.

!PYTHON_CMD! -m kumihan_formatter --generate-test --test-output "%OUTPUT_DIR%\%TEST_FILE%" --pattern-count 150 --double-click-mode -o "%OUTPUT_DIR%"

if !errorlevel! neq 0 (
    echo.
    echo [✗] エラー: テストファイルの生成に失敗しました
    pause
    exit /b 1
)

echo.
echo ==========================================
echo  生成完了！
echo ==========================================
echo.
echo [✓] テストファイルが生成されました:
echo     %OUTPUT_DIR%\%TEST_FILE%
echo.
echo [✓] HTMLファイルも生成されました:
echo     %OUTPUT_DIR%\%TEST_FILE:~0,-4%.html
echo.

REM 出力フォルダを開く
echo [→] 出力フォルダを開いています...
explorer "%OUTPUT_DIR%"

echo.
echo 生成されたファイルを確認してください。
echo HTMLファイルをブラウザで開くと、変換結果を確認できます。
echo.

pause