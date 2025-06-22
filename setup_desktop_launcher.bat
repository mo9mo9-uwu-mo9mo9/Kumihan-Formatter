@echo off
chcp 65001 > nul
title Kumihan-Formatter - デスクトップセットアップ

echo.
echo ============================================
echo  Kumihan-Formatter プロジェクト内セットアップ
echo ============================================
echo.

rem 現在のディレクトリを取得
set CURRENT_DIR=%~dp0
set CURRENT_DIR=%CURRENT_DIR:~0,-1%

echo 📁 現在のディレクトリ: %CURRENT_DIR%
echo.

rem バッチファイルの存在確認
if not exist "%CURRENT_DIR%\kumihan_convert.bat" (
    echo ❌ エラー: kumihan_convert.bat が見つかりません
    echo   このセットアップスクリプトをKumihan-Formatterフォルダ内で実行してください
    echo.
    pause
    exit /b 1
)

echo 🔧 プロジェクト内にショートカットを作成しています...

rem VBScriptでショートカットを作成
echo Set WshShell = WScript.CreateObject("WScript.Shell") > temp_shortcut.vbs
echo Set Shortcut = WshShell.CreateShortcut("%CURRENT_DIR%\Kumihan-Formatter.lnk") >> temp_shortcut.vbs
echo Shortcut.TargetPath = "%CURRENT_DIR%\kumihan_convert.bat" >> temp_shortcut.vbs
echo Shortcut.WorkingDirectory = "%CURRENT_DIR%" >> temp_shortcut.vbs
echo Shortcut.Description = "Kumihan-Formatter - CoC6thシナリオ組版ツール" >> temp_shortcut.vbs
echo Shortcut.IconLocation = "shell32.dll,21" >> temp_shortcut.vbs
echo Shortcut.Save >> temp_shortcut.vbs

cscript //nologo temp_shortcut.vbs
del temp_shortcut.vbs

if exist "%CURRENT_DIR%\Kumihan-Formatter.lnk" (
    echo ✅ ショートカットを作成しました！
    echo 📍 場所: %CURRENT_DIR%\Kumihan-Formatter.lnk
    echo.
    echo 🎉 セットアップ完了！
    echo.
    echo 📝 使い方:
    echo   1. プロジェクト内の「Kumihan-Formatter」をダブルクリック
    echo   2. .txtファイルをドラッグ&ドロップするか、パスを入力
    echo   3. 自動的にHTMLに変換されます
    echo.
    echo 💡 ヒント:
    echo   - .txtファイルを直接ショートカットにドラッグ&ドロップも可能です
    echo   - プロジェクト内実行のため「dist」フォルダに保存されます
) else (
    echo ❌ ショートカットの作成に失敗しました
    echo   手動でプロジェクト内にショートカットを作成してください
)

echo.
echo 何かキーを押して終了してください...
pause > nul