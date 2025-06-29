# CLAUDE.md

> Kumihan‑Formatter – Claude Code 指示ファイル\
> **目的**: Claude Code に開発ガイドラインの要点を渡す\
> **バージョン**: 0.4.0 (2025‑06‑29)

# インポート
@./PREAMBLE.md  &#x20;
@./CONTRIBUTING.md

---

## 1️⃣ 必須運用

### 前提

- 本 Project は日本語にて開発を行っているため、返答には必ず日本語を使用する。

### セッション管理

- Claude Code の `{{session.turn}}` プレースホルダを利用し、出力冒頭の `<every_chat>` テンプレート内で自動インクリメント。
- `{{session.turn}} >= 10` で **必ず** `/clear` を実行しセッションをリセット。

例:

```markdown
<every_chat>
## Claude Code 運用5原則
...（実際のPREAMBLE.mdの内容）

# {{session.turn}} times.
</every_chat>
```

### 守るべきファイル/フォルダ

| 種別       | パス                            | 理由           |
| -------- | ----------------------------- | ------------ |
| アンカーファイル | `CLAUDE.md`                   | Claude 指示の中心 |
| 設定       | `.claude/`                    | セッションキー等の機密  |
| ローカル設定   | `.claude/settings.local.json` | 個人環境依存       |

**禁止**: 上記を Git へ push・削除・改名する行為。

---

## 2️⃣ ドキュメント分割

| 情報          | ファイル/ディレクトリ       |
| ----------- | ----------------- |
| フォーマット仕様    | `SPEC.md`         |
| 開発フロー / ラベル | `CONTRIBUTING.md` |
| ユーザーマニュアル   | `docs/` (mkdocs)  |
| 変更履歴        | `CHANGELOG.md`    |

> 詳細は各ファイルを参照し、**CLAUDE.md には追記をしない** こと。

---

## 3️⃣ 更新手順

1. 追加情報が必要な場合は **別ファイル** を作成し `@filename` で参照。
2. 例外として、本ファイルの「必須運用」節に関連する改訂のみ直接編集。
3. 変更後は `make lint-docs` でリンク切れチェック。

---

開発を楽しみましょう 🎉

