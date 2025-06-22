#!/bin/bash

# ============================================
# Kumihan-Formatter テスト用記法網羅ファイル生成
# ダブルクリック実行用 macOS コマンドファイル
# ============================================

echo ""
echo "=========================================="
echo " Kumihan-Formatter テスト用記法網羅ファイル生成"
echo "=========================================="
echo ""

# スクリプトのディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 出力先をdev/test-output内に設定
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
OUTPUT_DIR="$SCRIPT_DIR/test-output/$TIMESTAMP"
TEST_FILE="test_patterns.txt"

echo "出力先: $OUTPUT_DIR"
echo "テストファイル名: $TEST_FILE"
echo ""

# 出力ディレクトリを作成
if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
    echo "出力ディレクトリを作成しました: $OUTPUT_DIR"
fi

# Python環境の検出
PYTHON_CMD=""
VENV_PATH=""

# 1. 仮想環境の確認（.venv）
if [ -f "../.venv/bin/python" ]; then
    PYTHON_CMD="../.venv/bin/python"
    VENV_PATH="../.venv/bin/activate"
    echo "[✓] 仮想環境を検出: .venv"
elif [ -f "../venv/bin/python" ]; then
    PYTHON_CMD="../venv/bin/python"
    VENV_PATH="../venv/bin/activate"
    echo "[✓] 仮想環境を検出: venv"
fi

# 2. システムPythonの確認（仮想環境が見つからない場合）
if [ -z "$PYTHON_CMD" ]; then
    if command -v python3 &> /dev/null; then
        # Python3のバージョン確認（修正版）
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        REQUIRED_VERSION="3.9"
        
        # バージョン比較（sort -Vを使用）
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            PYTHON_CMD="python3"
            echo "[✓] システムPython3を使用 (バージョン: $PYTHON_VERSION >= $REQUIRED_VERSION)"
        else
            echo "[✗] エラー: Python $REQUIRED_VERSION以上が必要です (現在: $PYTHON_VERSION)"
            echo ""
            echo "Python $REQUIRED_VERSION以上をインストールするか、"
            echo "仮想環境（.venv または venv）を作成してください。"
            echo ""
            read -p "何かキーを押してください..."
            exit 1
        fi
    elif command -v python &> /dev/null; then
        # Pythonのバージョン確認（修正版）
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        REQUIRED_VERSION="3.9"
        
        # バージョン比較（sort -Vを使用）
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            PYTHON_CMD="python"
            echo "[✓] システムPythonを使用 (バージョン: $PYTHON_VERSION >= $REQUIRED_VERSION)"
        else
            echo "[✗] エラー: Python $REQUIRED_VERSION以上が必要です (現在: $PYTHON_VERSION)"
            echo ""
            echo "Python $REQUIRED_VERSION以上をインストールしてください。"
            echo ""
            read -p "何かキーを押してください..."
            exit 1
        fi
    else
        echo "[✗] エラー: Pythonが見つかりません"
        echo ""
        echo "Python 3.9以上をインストールするか、"
        echo "仮想環境（.venv または venv）を作成してください。"
        echo ""
        read -p "何かキーを押してください..."
        exit 1
    fi
fi

# 仮想環境の自動作成・アクティベート
VENV_CREATED=0
if [ -n "$VENV_PATH" ]; then
    echo "[→] 仮想環境をアクティベート中..."
    source "$VENV_PATH"
    if [ $? -ne 0 ]; then
        echo "[✗] エラー: 仮想環境のアクティベートに失敗"
        read -p "何かキーを押してください..."
        exit 1
    fi
elif [ -z "$PYTHON_CMD" ] || [ "$PYTHON_CMD" = "python3" ] || [ "$PYTHON_CMD" = "python" ]; then
    # 仮想環境が見つからない場合は自動作成
    echo "[→] 仮想環境が見つかりません。自動で作成します..."
    echo "[→] 初回セットアップを実行しています..."
    
    # 仮想環境を作成
    echo "[→] 仮想環境を作成中..."
    if python3 -m venv ../.venv; then
        echo "[✓] 仮想環境を作成しました"
        PYTHON_CMD="../.venv/bin/python"
        VENV_PATH="../.venv/bin/activate"
        VENV_CREATED=1
        
        # 仮想環境をアクティベート
        echo "[→] 仮想環境をアクティベート中..."
        source "$VENV_PATH"
        if [ $? -ne 0 ]; then
            echo "[✗] エラー: 仮想環境のアクティベートに失敗"
            read -p "何かキーを押してください..."
            exit 1
        fi
    else
        echo "[✗] エラー: 仮想環境の作成に失敗しました"
        read -p "何かキーを押してください..."
        exit 1
    fi
fi

# パッケージの存在確認と自動インストール
# 仮想環境を新規作成した場合は必ずインストールを実行
if [ $VENV_CREATED -eq 1 ]; then
    echo "[→] 新規仮想環境にKumihan-Formatterをインストール中..."
    echo "[→] パッケージと依存関係をインストール中... (しばらくお待ちください)"
    
    if $PYTHON_CMD -m pip install -e "../[dev]" --quiet; then
        echo "[✓] Kumihan-Formatterのインストールが完了しました"
    else
        echo "[✗] エラー: Kumihan-Formatterのインストールに失敗しました"
        echo ""
        echo "手動で以下のコマンドを実行してください:"
        echo "  source ../.venv/bin/activate"
        echo "  pip install -e ../[dev]"
        echo ""
        read -p "何かキーを押してください..."
        exit 1
    fi
else
    # 既存の仮想環境の場合はパッケージの存在を確認
    echo "[→] Kumihan-Formatterパッケージを確認中..."
    $PYTHON_CMD -c "import kumihan_formatter" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "[→] Kumihan-Formatterが見つかりません。自動でインストールします..."
        echo "[→] パッケージをインストール中... (しばらくお待ちください)"
        
        if $PYTHON_CMD -m pip install -e "../[dev]" --quiet; then
            echo "[✓] Kumihan-Formatterのインストールが完了しました"
        else
            echo "[✗] エラー: Kumihan-Formatterのインストールに失敗しました"
            echo ""
            echo "手動で以下のコマンドを実行してください:"
            echo "  source ../.venv/bin/activate"
            echo "  pip install -e ../[dev]"
            echo ""
            read -p "何かキーを押してください..."
            exit 1
        fi
    else
        echo "[✓] Kumihan-Formatterパッケージが利用可能です"
    fi
fi

echo ""

# テスト用記法網羅ファイルの生成
echo "[→] テスト用記法網羅ファイルを生成中..."
echo ""

$PYTHON_CMD -m kumihan_formatter --generate-test --test-output "$OUTPUT_DIR/$TEST_FILE" --pattern-count 150 --double-click-mode -o "$OUTPUT_DIR"

if [ $? -ne 0 ]; then
    echo ""
    echo "[✗] エラー: テストファイルの生成に失敗しました"
    read -p "何かキーを押してください..."
    exit 1
fi

echo ""
echo "=========================================="
echo " 生成完了！"
echo "=========================================="
echo ""
echo "[✓] テストファイルが生成されました:"
echo "     $OUTPUT_DIR/$TEST_FILE"
echo ""
echo "[✓] HTMLファイルも生成されました:"
echo "     $OUTPUT_DIR/${TEST_FILE%.*}.html"
echo ""

# 出力フォルダを開く
echo "[→] 出力フォルダを開いています..."
open "$OUTPUT_DIR"

# 成功通知（macOS通知センター）
if command -v osascript &> /dev/null; then
    osascript -e "display notification \"テスト用記法網羅ファイルの生成が完了しました\" with title \"Kumihan-Formatter\" sound name \"Glass\""
fi

echo ""
echo "生成されたファイルを確認してください。"
echo "HTMLファイルをブラウザで開くと、変換結果を確認できます。"
echo ""

read -p "何かキーを押してください..."