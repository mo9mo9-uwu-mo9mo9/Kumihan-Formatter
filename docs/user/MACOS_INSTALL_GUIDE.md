# macOS インストールガイド

> Kumihan Formatter の macOS 向けインストール手順

## システム要件

- **対応OS**: macOS 10.13 (High Sierra) 以降
- **アーキテクチャ**: Apple Silicon (M1/M2/M3) 対応
- **ディスク容量**: 約 50MB の空き容量

## インストール手順

### 方法 1: DMG ファイルからのインストール（推奨）

1. **ダウンロード**
   - GitHub Releases から `KumihanFormatter-1.0.0.dmg` をダウンロード

2. **DMG ファイルを開く**
   - ダウンロードした DMG ファイルをダブルクリック
   - Finder でボリュームが開きます

3. **アプリケーションフォルダにコピー**
   - `Kumihan Formatter.app` を `Applications` フォルダにドラッグ&ドロップ
   - コピーが完了するまで待機

4. **DMG のアンマウント**
   - Finder サイドバーの DMG ボリュームを右クリック → 取り出し

### 方法 2: .app ファイルの直接使用

1. **ダウンロード**
   - GitHub Releases から `Kumihan Formatter.app` をダウンロード

2. **配置**
   - ダウンロードした .app ファイルを任意の場所に配置
   - Applications フォルダへの配置を推奨

## 初回起動時の注意

### セキュリティ警告への対処

macOS のセキュリティ機能により、初回起動時に警告が表示される場合があります。

#### ケース 1: 「開発元が未確認」警告

```
"Kumihan Formatter" は、開発元が未確認のため開けません。
```

**対処法:**
1. アプリケーションを右クリック
2. 「開く」をクリック
3. 再度表示される警告で「開く」をクリック

#### ケース 2: 「インターネットからダウンロード」警告

```
"Kumihan Formatter" はインターネットからダウンロードされたため開けません。
```

**対処法:**
1. システム設定 → プライバシーとセキュリティ
2. 「一般」タブで「このまま開く」をクリック

### Gatekeeper の無効化（上級者向け）

**注意**: セキュリティリスクを理解した上で実行してください。

```bash
# 特定アプリの隔離属性を削除
sudo xattr -rd com.apple.quarantine "/Applications/Kumihan Formatter.app"
```

## 使用方法

### 1. アプリケーションの起動

- Applications フォルダから `Kumihan Formatter` をダブルクリック
- または Spotlight で「Kumihan」と検索して起動

### 2. ファイルの変換

1. **ファイル選択**
   - 「ファイルを選択」ボタンでテキストファイルを選択
   - または「フォルダを選択」で一括変換

2. **テンプレート選択**
   - 用途に応じたテンプレートを選択
   - カスタムテンプレートの使用も可能

3. **変換実行**
   - 「変換開始」ボタンで HTML 変換を実行
   - 進捗バーで処理状況を確認

### 3. 出力ファイルの確認

- 変換完了後、指定したフォルダに HTML ファイルが生成
- ブラウザで開いて結果を確認

## アンインストール

### 完全削除手順

1. **アプリケーションの削除**
   - Applications フォルダから `Kumihan Formatter.app` をゴミ箱に移動

2. **設定ファイルの削除**（任意）
   ```bash
   # ユーザー設定ファイル
   rm -rf ~/Library/Preferences/com.kumihan.formatter.plist

   # アプリケーションサポートファイル
   rm -rf ~/Library/Application\ Support/KumihanFormatter/
   ```

## トラブルシューティング

### よくある問題

#### 1. アプリケーションが起動しない

**症状**: ダブルクリックしても何も起こらない

**対処法**:
- ターミナルから起動してエラーメッセージを確認:
  ```bash
  "/Applications/Kumihan Formatter.app/Contents/MacOS/Kumihan Formatter"
  ```

#### 2. ファイル選択ダイアログが表示されない

**症状**: ボタンをクリックしてもダイアログが開かない

**対処法**:
- システム設定 → プライバシーとセキュリティ → ファイルとフォルダ
- Kumihan Formatter の権限を確認

#### 3. 変換に失敗する

**症状**: エラーメッセージが表示される

**対処法**:
- 入力ファイルの文字エンコーディングを確認（UTF-8 推奨）
- ファイルパスに日本語や特殊文字が含まれていないか確認

### ログファイルの確認

問題の詳細調査が必要な場合：

```bash
# アプリケーションログ
cat ~/Library/Logs/KumihanFormatter/app.log

# システムログ（Kumihan Formatter 関連）
log show --predicate 'process == "Kumihan Formatter"' --last 1h
```

## 技術サポート

### サポート窓口

- **GitHub Issues**: [問題報告・機能要望](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)
- **ドキュメント**: [詳細マニュアル](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/docs)

### 問題報告時の情報

以下の情報を含めてください：

1. **システム情報**
   ```bash
   system_profiler SPSoftwareDataType | grep "System Version"
   ```

2. **エラーメッセージ**
   - 表示されたエラーメッセージの完全なテキスト

3. **再現手順**
   - 問題が発生する具体的な操作手順

## 更新とアップグレード

### 新バージョンの確認

- GitHub Releases ページで最新版を確認
- アプリ内の「バージョン情報」で現在のバージョンを確認

### アップデート手順

1. 新しい DMG ファイルをダウンロード
2. 既存のアプリケーションを新バージョンで置き換え
3. 設定は自動的に引き継がれます

## 関連ドキュメント

- [基本的な使用方法](QUICKSTART.md)
- [設定ガイド](CONFIG_GUIDE.md)
- [記法リファレンス](SYNTAX_REFERENCE.md)
- [FAQ](FAQ.md)
