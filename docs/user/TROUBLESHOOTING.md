# トラブルシューティング

このガイドでは、Windows・macOS共通の問題と解決方法を説明します。

## 🖥️ Windows環境の問題

### 文字化け問題
**症状**: batファイル実行時に日本語が文字化けする

**解決方法**:
1. **推奨**: `WINDOWS/`フォルダ内のスクリプト使用
2. コマンドプロンプトで `chcp 65001` 実行
3. PowerShell使用（UTF-8対応が良好）

### Windows バージョン別対応
- **Windows 10 Build 1903以降**: UTF-8サポート改善済み
- **古いWindows**: PowerShell使用を推奨

## 🍎 macOS環境の問題

### 権限エラー
**症状**: `.command`ファイルが実行できない

**解決方法**:
```bash
chmod +x MAC/*.command
```

### ターミナル設定
**症状**: 日本語が正しく表示されない

**解決方法**:
```bash
export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8
```

## 🔧 共通の問題

### Python関連エラー
**症状**: `Python not found`

**解決方法**:
1. Python 3.9以上をインストール: https://www.python.org/downloads/
2. **Windows**: インストール時に「Add Python to PATH」をチェック
3. **macOS**: Homebrewでのインストールも可能

### 仮想環境関連エラー
**症状**: `Virtual environment not found`

**解決方法**:
1. **Windows**: `WINDOWS/初回セットアップ.bat` を実行
2. **macOS**: `MAC/初回セットアップ.command` を実行
3. 自動セットアップを完了させる

### 権限関連エラー
**症状**: `Access denied` / `Permission denied`

**解決方法**:
- **Windows**: コマンドプロンプトを管理者として実行
- **macOS**: `sudo` またはファイル権限を確認

### ファイル変換エラー
**症状**: 変換が失敗する

**解決方法**:
1. ファイル名に特殊文字が含まれていないか確認
2. `.txt`ファイルのエンコーディングをUTF-8で保存
3. ファイルが他のプログラムで開かれていないか確認

## 🆘 完全リセット手順

問題が解決しない場合の完全クリーンインストール：

1. `.venv` フォルダを削除
2. 初回セットアップを再実行:
   - **Windows**: `WINDOWS/初回セットアップ.bat`
   - **macOS**: `MAC/初回セットアップ.command`

## 📞 サポート

問題が続く場合は、以下の情報とともに[GitHub Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)で報告してください：

- OSとバージョン（Windows 10、macOS Ventura など）
- Python バージョン
- エラーメッセージの完全なコピー
- 使用したスクリプトファイル名