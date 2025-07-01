# ブランチ保護説明書

## experimental/macos-app-packaging-317

**重要**: このブランチは削除しないでください。

### 目的
Issue #317「macOS向け.app形式パッケージング対応」の完全実装とプロトタイプ保存

### 内容
- macOS向けGUIアプリケーションの完全実装
- .app形式とDMG配布パッケージの作成システム
- セキュリティ対応（コード署名・公証）準備
- 完全なユーザーサポート体制

### 技術的成果物

#### 実行可能ファイル
- `Kumihan Formatter.app` (37MB) - Apple Silicon対応
- `KumihanFormatter-1.0.0.dmg` (19MB) - 配布用パッケージ

#### 実装ファイル
- `kumihan_formatter/gui_launcher.py` - GUIアプリケーション
- `pyinstaller/kumihan_formatter_macos.spec` - ビルド設定
- `scripts/build_macos.sh` - 自動ビルド
- `scripts/create_dmg.sh` - DMG作成
- `scripts/security_setup.sh` - セキュリティ対応
- `assets/icon.icns` - アプリアイコン

#### ドキュメント
- `docs/user/MACOS_INSTALL_GUIDE.md` - インストール手順
- `docs/user/MACOS_SECURITY_GUIDE.md` - セキュリティガイド
- `docs/user/MACOS_TROUBLESHOOTING.md` - トラブルシューティング

### 技術仕様
- **対象OS**: macOS 10.13 (High Sierra) 以降
- **アーキテクチャ**: Apple Silicon (ARM64)
- **GUI**: Tkinter（macOS最適化済み）
- **配布形式**: .app + .dmg
- **セキュリティ**: 署名・公証対応準備完了

### 今後の利用方法

#### 開発継続時
```bash
git checkout experimental/macos-app-packaging-317
# 必要に応じて機能追加・改善
```

#### 本ブランチへの統合時
```bash
git checkout main
git merge experimental/macos-app-packaging-317
# または選択的な cherry-pick
```

### 重要な注意事項

1. **ブランチ保護**: このブランチは実験成果の保存用です
2. **品質基準**: 試作品レベル（一部品質チェックをスキップ）
3. **統合準備**: 本格統合時は品質改善が必要
4. **アーキテクチャ制限**: 現在はApple Silicon版のみ

### 関連Issue
- [Issue #317](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues/317) - macOS向け.app形式パッケージング対応

### コミット情報
- **最終コミット**: `dda91f5`
- **作成日**: 2025-07-01
- **実装者**: Claude Code との協同開発

---

**このブランチはv1.0リリースの重要な技術基盤として保護されています。**
