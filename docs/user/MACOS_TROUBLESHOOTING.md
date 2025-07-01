# macOS トラブルシューティング

> Kumihan Formatter macOS 版でよくある問題と解決方法

## 起動・実行に関する問題

### 1. アプリケーションが起動しない

#### 症状
- ダブルクリックしても何も起こらない
- 起動後すぐにクラッシュする

#### 原因と対処法

**ケース A: セキュリティ制限**
```bash
# 隔離属性の確認
xattr "/Applications/Kumihan Formatter.app"

# 隔離属性の削除（注意: セキュリティリスクを理解の上実行）
sudo xattr -rd com.apple.quarantine "/Applications/Kumihan Formatter.app"
```

**ケース B: 破損したアプリケーション**
```bash
# 署名の確認
codesign --verify --verbose "/Applications/Kumihan Formatter.app"

# システムポリシーの確認
spctl --assess --verbose "/Applications/Kumihan Formatter.app"
```

**ケース C: 権限の問題**
```bash
# 実行権限の確認
ls -la "/Applications/Kumihan Formatter.app/Contents/MacOS/"

# 実行権限の付与
chmod +x "/Applications/Kumihan Formatter.app/Contents/MacOS/Kumihan Formatter"
```

### 2. 「開発元が未確認」エラー

#### 症状
```
"Kumihan Formatter" は、開発元が未確認のため開けません。
```

#### 対処法

**方法 1: 右クリックから開く**
1. アプリケーションを右クリック
2. 「開く」を選択
3. 警告ダイアログで「開く」をクリック

**方法 2: システム設定から許可**
1. システム設定 → プライバシーとセキュリティ
2. 「セキュリティ」セクションで「このまま開く」をクリック

**方法 3: ターミナルから実行**
```bash
# 直接実行
open "/Applications/Kumihan Formatter.app"

# または
"/Applications/Kumihan Formatter.app/Contents/MacOS/Kumihan Formatter"
```

### 3. ファイルアクセス権限エラー

#### 症状
- ファイル選択ダイアログが表示されない
- 「アクセス権限がありません」エラー

#### 対処法

**プライバシー設定の確認**
1. システム設定 → プライバシーとセキュリティ
2. 「ファイルとフォルダ」を選択
3. Kumihan Formatter にチェックを入れる

**フルディスクアクセス権限の付与**
1. システム設定 → プライバシーとセキュリティ
2. 「フルディスクアクセス」を選択
3. 「+」ボタンで Kumihan Formatter を追加

## 変換処理に関する問題

### 1. 変換が失敗する

#### 症状
- エラーメッセージが表示される
- 出力ファイルが生成されない

#### よくある原因と対処法

**文字エンコーディングの問題**
```bash
# ファイルのエンコーディング確認
file -I your_file.txt

# UTF-8 への変換
iconv -f SHIFT_JIS -t UTF-8 input.txt > output.txt
```

**ファイルパスの問題**
- 日本語や特殊文字を含むパス名は避ける
- スペースを含むパス名は「"」で囲む
- 長すぎるパス名（255文字超）は短縮する

**権限の問題**
```bash
# ファイル権限の確認
ls -la input.txt

# 読み取り権限の付与
chmod +r input.txt

# 出力ディレクトリの書き込み権限確認
ls -la output_directory/
```

### 2. 処理が非常に遅い

#### 症状
- 小さなファイルでも変換に時間がかかる
- 進捗バーが進まない

#### 対処法

**メモリ使用量の確認**
```bash
# プロセス監視
top -pid $(pgrep "Kumihan Formatter")

# メモリ使用量確認
ps -o pid,ppid,pcpu,pmem,comm -p $(pgrep "Kumihan Formatter")
```

**ディスク容量の確認**
```bash
# 使用可能容量の確認
df -h

# 一時ファイルの削除
sudo rm -rf /tmp/KumihanFormatter*
```

## システム環境による問題

### 1. macOS バージョン互換性

#### 対応バージョン
- **サポート**: macOS 10.13 (High Sierra) 以降
- **推奨**: macOS 11.0 (Big Sur) 以降

#### 古いバージョンでの問題
```bash
# システムバージョンの確認
sw_vers

# 互換性の問題がある場合の対処
# → macOS のアップデート、または旧バージョンのアプリを使用
```

### 2. アーキテクチャの問題

#### Apple Silicon (M1/M2/M3) での動作

**現在のアーキテクチャ確認**
```bash
uname -m
# arm64: Apple Silicon
# x86_64: Intel Mac
```

**Rosetta 2 の確認（Intel版の場合）**
```bash
# Rosetta 2 のインストール状況確認
/usr/bin/pgrep -q oahd && echo "Rosetta 2 is running" || echo "Rosetta 2 is not installed"

# Rosetta 2 のインストール
sudo softwareupdate --install-rosetta
```

## ログとデバッグ

### 1. アプリケーションログの確認

**ログファイルの場所**
```bash
# アプリケーションログ
~/Library/Logs/KumihanFormatter/

# クラッシュレポート
~/Library/Logs/DiagnosticReports/Kumihan\ Formatter*
```

**ログの確認方法**
```bash
# 最新のログを表示
tail -f ~/Library/Logs/KumihanFormatter/app.log

# エラーレベルのログのみ表示
grep -i error ~/Library/Logs/KumihanFormatter/app.log
```

### 2. システムログの確認

**Console.app を使用**
1. アプリケーション → ユーティリティ → Console
2. 左サイドバーで「システムレポート」を選択
3. 検索欄で「Kumihan Formatter」を検索

**ターミナルから確認**
```bash
# 最近1時間のログ
log show --predicate 'process == "Kumihan Formatter"' --last 1h

# エラーレベルのみ
log show --predicate 'process == "Kumihan Formatter" AND messageType >= 16' --last 1h
```

### 3. デバッグモードでの実行

**ターミナルから詳細ログ付きで実行**
```bash
# 環境変数を設定してデバッグモード実行
export DEBUG=1
"/Applications/Kumihan Formatter.app/Contents/MacOS/Kumihan Formatter"
```

## ネットワーク関連の問題

### 1. テンプレートダウンロードの失敗

#### 症状
- オンラインテンプレートが取得できない
- 「ネットワークエラー」メッセージ

#### 対処法

**ネットワーク接続の確認**
```bash
# インターネット接続確認
ping -c 3 github.com

# DNS 解決確認
nslookup github.com
```

**ファイアウォール設定**
1. システム設定 → ネットワーク → ファイアウォール
2. Kumihan Formatter の通信を許可

## 高度なトラブルシューティング

### 1. 完全なリセット

**アプリケーションの完全削除と再インストール**
```bash
# アプリケーションの削除
sudo rm -rf "/Applications/Kumihan Formatter.app"

# 設定ファイルの削除
rm -rf ~/Library/Preferences/com.kumihan.formatter.plist
rm -rf ~/Library/Application\ Support/KumihanFormatter/
rm -rf ~/Library/Caches/KumihanFormatter/
rm -rf ~/Library/Logs/KumihanFormatter/

# Spotlight インデックスの更新
sudo mdutil -i on /
```

### 2. 診断情報の収集

**システム情報の収集**
```bash
# システムレポートの生成
system_profiler SPSoftwareDataType SPHardwareDataType > system_info.txt

# プロセス情報
ps aux | grep -i kumihan > process_info.txt

# ネットワーク情報
ifconfig > network_info.txt
```

## サポートへの問い合わせ

### 必要な情報

問題報告時は以下の情報を含めてください：

1. **システム情報**
   ```bash
   sw_vers
   uname -m
   ```

2. **アプリケーションバージョン**
   - アプリケーション → Kumihan Formatter について

3. **エラーメッセージ**
   - 完全なエラーテキスト
   - スクリーンショット

4. **再現手順**
   - 問題が発生する具体的な操作

5. **ログファイル**
   - `~/Library/Logs/KumihanFormatter/app.log`

### 問い合わせ先

- **GitHub Issues**: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues
- **ラベル**: `macOS`, `bug`, `support`
