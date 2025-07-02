@echo off
setlocal enabledelayedexpansion
rem Kumihan-Formatter - One-time Setup Script
rem This script automatically sets up everything needed to use Kumihan-Formatter

rem Try to set UTF-8 encoding, but don't fail if it doesn't work
chcp 65001 > nul 2>&1

title Kumihan-Formatter - Initial Setup

echo.
echo ==========================================
echo  Kumihan-Formatter - Initial Setup
echo ==========================================
echo Set up the required environment automatically
echo Kumihan-Formatter will be ready to use soon
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
echo  Setup Complete!
echo ==========================================
echo.
echo [完了] セットアップが完了しました！
echo.
echo 次のステップを選択してください:
echo   Y: 変換ツールを今すぐ起動
echo   N: 後で使用（使用方法を表示）
echo   S: サンプルを確認（出力例を見る）
echo.
set /p choice="[選択] 選択してください [Y/N/S]: "
if /i "%choice%"=="y" (
    echo.
    echo [開始] 変換ツールを起動しています...
    if exist "WINDOWS\変換ツール.bat" (
        call "WINDOWS\変換ツール.bat"
    ) else (
        echo [エラー] 変換ツール.bat が見つかりません
        echo.
        echo 手動で起動してください:
        echo   - ダブルクリック: WINDOWS/変換ツール.bat
        echo.
        pause
    )
) else if /i "%choice%"=="s" (
    echo.
    echo [統計] サンプルを実行しています...
    echo.
    if exist "WINDOWS\サンプル実行.bat" (
        call "WINDOWS\サンプル実行.bat"
        echo.
        echo サンプル確認が完了しました！
        echo.
        set /p convert_choice="[開始] 今度は変換ツールを試しますか？ [Y/N]: "
        if /i "!convert_choice!"=="y" (
            echo.
            echo [開始] 変換ツールを起動しています...
            if exist "WINDOWS\変換ツール.bat" (
                call "WINDOWS\変換ツール.bat"
            ) else (
                echo [エラー] エラー: 変換ツール.bat が見つかりません
                echo 手動で 変換ツール.bat をダブルクリックしてください
            )
        )
    ) else (
        echo [エラー] エラー: サンプル実行.bat が見つかりません
        echo 手動で WINDOWS\サンプル実行.bat をダブルクリックしてください
    )
    echo.
    echo Press any key to exit...
    pause > nul
) else (
    echo.
    echo [ヒント] 後で使用する場合:
    echo    WINDOWS\変換ツール.bat をダブルクリック
    echo.
    echo [統計] サンプルを確認する場合:
    echo    WINDOWS\サンプル実行.bat をダブルクリック
    echo.
    echo Press any key to exit...
    pause > nul
)
