# 💻 OS固有のトラブルシューティング

> **Windows・macOS特有の問題を解決**

[← トラブルシューティング目次に戻る](TROUBLESHOOTING.md)

---

## 📋 OS固有問題一覧

### 🪟 Windows固有の問題
- [Windows Defender / ウイルス対策ソフトの警告](#-症状-windows-defender--ウイルス対策ソフトの警告)
- [長いパス名 / パスが長すぎるエラー](#-症状-長いパス名--パスが長すぎるエラー)

### 🍎 macOS固有の問題  
- [Gatekeeper / アプリケーションが開けない警告](#-症状-gatekeeper--アプリケーションが開けない警告)
- [SIP（System Integrity Protection）関連エラー](#-症状-sipsystem-integrity-protection関連エラー)

### 📁 共通ファイル・権限問題
- [ファイルが作成されない / 出力フォルダにファイルがない](#-症状-ファイルが作成されない--出力フォルダにファイルがない)

---

## 🪟 Windows固有の問題

### ❌ **症状**: Windows Defender / ウイルス対策ソフトの警告

#### 🔍 **原因**
- `.bat`ファイルや`.exe`ファイルの誤検知
- 一時的なファイル作成の検知
- 未署名実行ファイルの警告

#### ✅ **解決方法**

##### **Step 1: Windows Defenderの除外設定**
1. **Windows設定** → **更新とセキュリティ** → **Windows セキュリティ**
2. **ウイルスと脅威の防止** → **設定の管理**
3. **除外の追加または削除** → **除外を追加**
4. **フォルダ** を選択し、Kumihan-Formatterのフォルダを追加

##### **Step 2: 実行ポリシーの確認・変更**
```powershell
# 現在のポリシー確認
Get-ExecutionPolicy

# 実行ポリシー変更（管理者権限で実行）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

##### **Step 3: 代替実行方法**
```cmd
# 直接Pythonで実行（バッチファイルを使わない）
cd Kumihan-Formatter
python -m kumihan_formatter examples\sample.txt
```

---

### ❌ **症状**: 長いパス名 / パスが長すぎるエラー

#### 🔍 **原因**
- Windowsの標準パス長制限（260文字）
- 深いフォルダ階層でのプロジェクト配置
- 長いファイル名の使用

#### ✅ **解決方法**

##### **Step 1: 長いパス名のサポート有効化**
1. **レジストリエディタ** (`regedit`) を管理者権限で実行
2. `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem`
3. `LongPathsEnabled` を **1** に設定
4. システム再起動

##### **Step 2: 短いパスでの回避**
```cmd
# プロジェクトを短いパスに移動
move "C:\Users\VeryLongUserName\Documents\MyVeryLongProjectFolder\Kumihan-Formatter" "C:\KF"

# 短いパスで実行
cd C:\KF
python -m kumihan_formatter sample.txt
```

##### **Step 3: ネットワークドライブの活用**
```cmd
# 短いドライブレターを割り当て
subst K: "C:\Users\LongPath\Documents\Kumihan-Formatter"

# 短いパスで作業
K:
python -m kumihan_formatter sample.txt
```

---

## 🍎 macOS固有の問題

### ❌ **症状**: Gatekeeper / アプリケーションが開けない警告

#### 🔍 **原因**
- 未署名のスクリプトファイル
- インターネットからダウンロードしたファイルの検疫
- macOSセキュリティ設定による実行制限

#### ✅ **解決方法**

##### **Step 1: 検疫属性の削除**
```bash
# 検疫属性確認
xattr -l setup_mac.command

# 検疫属性削除
xattr -d com.apple.quarantine setup_mac.command
xattr -d com.apple.quarantine *.command
```

##### **Step 2: 実行権限の付与**
```bash
# 実行権限確認
ls -la *.command

# 実行権限付与
chmod +x setup_mac.command
chmod +x *.command
```

##### **Step 3: セキュリティ設定の調整**
1. **システム環境設定** → **セキュリティとプライバシー**
2. **一般** タブ → **ダウンロードしたアプリケーションの実行許可**
3. 「**すべてのアプリケーションを許可**」（一時的に設定）

##### **Step 4: 個別ファイルの許可**
```bash
# 右クリック → 「開く」で個別許可
# または
sudo spctl --master-disable  # 一時的にGatekeeper無効化
# 作業後
sudo spctl --master-enable   # Gatekeeper再有効化
```

---

### ❌ **症状**: SIP（System Integrity Protection）関連エラー

#### 🔍 **原因**
- システム保護ディレクトリでの実行
- システムPythonの使用
- 権限の制限されたディレクトリでの作業

#### ✅ **解決方法**

##### **Step 1: ユーザーディレクトリでの実行**
```bash
# ホームディレクトリに移動
cd ~/
mkdir KumihanProjects
cd KumihanProjects

# プロジェクトをコピー
cp -r /path/to/Kumihan-Formatter ./
```

##### **Step 2: Homebrewでの Python使用**
```bash
# Homebrewインストール（未インストールの場合）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# HombrewのPythonインストール
brew install python

# Homebrewのpipを使用
/opt/homebrew/bin/pip3 install -e .
```

---

## 📁 ファイル・権限関連の問題

### ❌ **症状**: ファイルが作成されない / 出力フォルダにファイルがない

#### 🔍 **原因**
- 出力ディレクトリの書き込み権限なし
- ディスク容量不足
- ウイルス対策ソフトによるブロック
- 出力先の指定間違い

#### ✅ **解決方法**

##### **Step 1: 詳細ログでの実行**
```bash
# デバッグモードで実行
python -m kumihan_formatter sample.txt --verbose

# ログファイル出力
python -m kumihan_formatter sample.txt > conversion.log 2>&1
```

##### **Step 2: ディスク容量の確認**
```bash
# Windows
dir C: 

# macOS
df -h
```

**対処法（容量不足の場合）:**
- 不要ファイルの削除
- 別ドライブへの出力指定

##### **Step 3: 権限確認と修正**
```bash
# Windows（PowerShell）
Get-Acl .\dist\

# macOS
ls -la dist/
chmod 755 dist/
```

##### **Step 4: 一時ディレクトリでのテスト**
```bash
# 一時ディレクトリに出力
python -m kumihan_formatter sample.txt -o /tmp/test_output

# Windowsの場合
python -m kumihan_formatter sample.txt -o %TEMP%\test_output
```

---

## 🛡️ **予防策・ベストプラクティス**

### **Windows**
- **プロジェクト配置**: `C:\Projects\` など短いパス
- **ウイルス対策**: 開発フォルダを除外設定
- **実行ポリシー**: RemoteSignedに設定
- **パス区切り**: バックスラッシュ `\` を使用

### **macOS**
- **プロジェクト配置**: `~/Projects/` などホーム以下
- **権限管理**: `chmod` で適切な権限設定
- **Python環境**: Homebrew版Pythonを推奨
- **パス区切り**: スラッシュ `/` を使用

### **共通**
- **定期バックアップ**: 重要ファイルの複製
- **権限確認**: 書き込み権限のある場所で作業
- **容量監視**: ディスク容量の定期チェック

---

## 🔧 **高度なトラブルシューティング**

### **環境診断スクリプト**

**Windows（PowerShell）:**
```powershell
# 環境情報収集
Write-Host "=== システム情報 ==="
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion
python --version
pip --version

Write-Host "=== ディスク容量 ==="
Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, @{Name="Size(GB)";Expression={[math]::Round($_.Size/1GB,2)}}, @{Name="FreeSpace(GB)";Expression={[math]::Round($_.FreeSpace/1GB,2)}}

Write-Host "=== 実行ポリシー ==="
Get-ExecutionPolicy
```

**macOS（bash）:**
```bash
#!/bin/bash
echo "=== システム情報 ==="
sw_vers
python3 --version
pip3 --version

echo "=== ディスク容量 ==="
df -h

echo "=== 権限確認 ==="
whoami
groups
```

---

## 📞 **サポートが必要な場合**

OS固有の問題報告テンプレート：

```
## OS固有問題報告

### システム情報
- OS: [Windows 10 21H2 / macOS Monterey 12.3 など]
- アーキテクチャ: [x64 / arm64]
- ユーザー権限: [管理者 / 標準ユーザー]

### セキュリティ設定
- Windows: [Defender有効/無効、実行ポリシー]
- macOS: [Gatekeeper設定、SIPステータス]

### エラーの詳細
[OS固有のエラーメッセージをコピペ]

### 試した解決方法
- [ ] 除外設定追加
- [ ] 権限変更
- [ ] 実行ポリシー変更
- [ ] 一時ディレクトリでのテスト
```

---

## 📚 関連リソース

- **[トラブルシューティング目次](TROUBLESHOOTING.md)** - 他の問題も確認
- **[Python環境問題](TROUBLESHOOTING_PYTHON.md)** - Python固有の問題
- **[クイックスタートガイド](QUICKSTART.md)** - 正しいセットアップ

---

**OS固有の問題が解決することを願っています！ 💻✨**