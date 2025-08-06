# Kumihan記法システム

## 実装済み記法
### 基本記法
- `#装飾名# 内容` - インライン形式
- `#装飾名#\n内容\n##` - ブロック形式

### 実用例
```
;;;見出し1
シナリオタイトル
;;;

このシナリオは...

;;;太字
重要な情報
;;;
```

## 将来実装予定記法
### 脚注記法（基本検証のみ実装）
- `((content))` → 巻末移動処理

### 傍注記法（未実装）
- `｜content《reading》` → ルビ表現

## システム構成
- `KeywordParser` - キーワード解析
- `MarkerParser` - マーカー解析  
- `BlockParser` - ブロック処理
- `SyntaxValidator` - 構文検証

## 記法検証コマンド
```bash
python -m kumihan_formatter check-syntax file.txt
```

## 開発状況
- Phase 4完了: レンダラー対応完全実装
- Phase 3完了: キーワードシステム移行完了
- 次期アップデート: 脚注・傍注記法の完全実装予定