# macOS セキュリティ対応ガイド

> Kumihan Formatter の macOS 向けアプリケーションのセキュリティ対応手順

## 概要

macOS でアプリケーションを配布する際に必要なセキュリティ対応について説明します。

## 必要な準備

### 1. Apple Developer Program への登録

- **必須**: Apple Developer Program (年額 $99) への登録
- **目的**: コード署名証明書の取得と公証サービスの利用

### 2. Developer ID Certificate の取得

1. [Apple Developer Portal](https://developer.apple.com/) にログイン
2. Certificates, Identifiers & Profiles に移動
3. **Developer ID Application** 証明書を作成
4. 証明書をダウンロードして Keychain Access にインストール

## セキュリティ対応の流れ

### ステップ 1: コード署名

```bash
# アプリケーションの署名
codesign --sign "Developer ID Application: Your Name (TEAMID)" \
    --force \
    --verbose \
    --options runtime \
    --timestamp \
    --deep \
    "dist/Kumihan Formatter.app"

# 署名の確認
codesign --verify --verbose "dist/Kumihan Formatter.app"
```

### ステップ 2: DMG ファイルの署名

```bash
# DMG ファイルの署名
codesign --sign "Developer ID Application: Your Name (TEAMID)" \
    --force \
    --verbose \
    --timestamp \
    "dist/KumihanFormatter-1.0.0.dmg"

# 署名の確認
codesign --verify --verbose "dist/KumihanFormatter-1.0.0.dmg"
```

### ステップ 3: Apple 公証サービスへの送信

```bash
# 公証サービスに送信
xcrun notarytool submit "dist/KumihanFormatter-1.0.0.dmg" \
    --apple-id "your@email.com" \
    --team-id "YOURTEAMID" \
    --wait

# 公証完了後、ステープル処理
xcrun stapler staple "dist/KumihanFormatter-1.0.0.dmg"
```

## 自動化スクリプト

プロジェクトには自動化スクリプトが含まれています：

```bash
# セキュリティ対応スクリプトの実行
chmod +x scripts/security_setup.sh
./scripts/security_setup.sh
```

## 注意事項

### セキュリティ警告の解決

- **署名なし**: 「"Kumihan Formatter" は、開発元が未確認のため開けません」
- **公証なし**: 「"Kumihan Formatter" はインターネットからダウンロードされたため開けません」

### 対処法

1. **完全なセキュリティ対応**: コード署名 + 公証
2. **部分的対応**: コード署名のみ（一部警告は残る）
3. **ユーザー対応**: 右クリック → 開く で実行可能

## 証明書の管理

### 証明書の確認

```bash
# 利用可能な証明書の一覧
security find-identity -p codesigning -v
```

### 証明書の有効期限

- **Developer ID Certificate**: 5年間有効
- **更新**: 期限前に Apple Developer Portal で更新

## トラブルシューティング

### よくある問題

1. **証明書が見つからない**
   - Keychain Access で証明書を確認
   - Apple Developer Portal で証明書の状態を確認

2. **公証に失敗する**
   - Team ID とApple ID の確認
   - App Store Connect での 2 要素認証設定

3. **Gatekeeper エラー**
   - 署名と公証の両方が必要
   - staple 処理の実行確認

### デバッグコマンド

```bash
# 詳細な署名情報の表示
codesign -dv --verbose=4 "dist/Kumihan Formatter.app"

# 公証状態の確認
xcrun stapler validate "dist/KumihanFormatter-1.0.0.dmg"

# システムポリシーの確認
spctl --assess --verbose "dist/Kumihan Formatter.app"
```

## 参考資料

- [Apple Developer Documentation - Notarizing macOS Software](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Code Signing Guide](https://developer.apple.com/library/archive/documentation/Security/Conceptual/CodeSigningGuide/)
- [Gatekeeper and runtime protection](https://developer.apple.com/documentation/security/gatekeeper_and_runtime_protection)

## 配布時の推奨事項

1. **セキュリティ対応完了後の動作確認**
   - 異なる Mac での動作テスト
   - ダウンロード後の実行テスト

2. **ユーザー向け説明書の提供**
   - インストール手順
   - セキュリティ警告への対処法

3. **サポート体制の整備**
   - 問題報告の受付窓口
   - よくある質問への回答
