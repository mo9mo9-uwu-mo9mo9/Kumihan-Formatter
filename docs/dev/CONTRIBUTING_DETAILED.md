# 詳細な開発ガイドライン

このファイルには、CONTRIBUTING.mdから分離された詳細な開発手順と説明が含まれています。

## 詳細な作業手順

### Issue駆動開発の詳細手順

#### 手順
1. **Issue確認・分析**
   - 既存Issueの確認、または新規Issue作成
   - 作業内容と範囲の明確化

2. **作業開始**
   ```bash
   # 作業中ラベル付与
   gh issue edit {ISSUE_NUMBER} --add-label "作業中"

   # ブランチ作成
   git checkout -b fix/issue-{番号}-{概要}
   # または
   git checkout -b feature/issue-{番号}-{概要}
   ```

3. **実装・テスト**
   - **TDD実践**: Red-Green-Refactorサイクルで実装
     1. テストリスト作成（実装予定機能のシナリオリスト）
     2. Red: 失敗するテストを一つ作成
     3. Green: 最小限の実装でテストを通す
     4. Refactor: 設計を改善
     5. 2-4を繰り返し

4. **完了処理**
   ```bash
   # コミット・プッシュ
   git add .
   git commit -m "fix: Issue #XXX の概要"
   git push -u origin ブランチ名

   # PR作成
   gh pr create --title "タイトル" --body "Closes #XXX"

   # レビュー・マージ
   # Issue完了報告・クローズ
   ```

## PR作成の詳細手順

```bash
gh pr create --title "適切なタイトル" --body "$(cat <<'EOF'
## Summary
変更内容の概要

## Changes
- 変更点1
- 変更点2

## Test plan
- [ ] テスト項目1
- [ ] テスト項目2

## Review Request
@claude 以下の方針でレビューをお願いします：
- 1コミット＝1レビューで各コミットを個別に確認
- TDD原則に従った実装であるかチェック
- コーディング規約への準拠確認

Closes #XXX (該当する場合)
EOF
)"
```

## デバッグ手順の詳細

### GUIアプリケーションのデバッグ
```bash
# デバッグモードで起動
KUMIHAN_GUI_DEBUG=true python3 -m kumihan_formatter.gui_launcher

# ログビューアーを使用してリアルタイムでログを確認
# 「ログ」ボタンからアクセス可能
```

### CLI版のデバッグ
```bash
# 開発ログを有効化
KUMIHAN_DEV_LOG=true kumihan convert input.txt output.txt

# ログファイル確認
cat /tmp/kumihan_formatter/dev_log_*.log
```

この内容は[CONTRIBUTING.md](../../CONTRIBUTING.md)から移動されました。
