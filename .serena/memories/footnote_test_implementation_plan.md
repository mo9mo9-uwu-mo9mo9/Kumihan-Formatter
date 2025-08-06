# 脚注テスト実装計画

## 実装対象テストファイル

### 1. `tests/unit/test_footnote_keyword.py`
- KeywordDefinitions での脚注キーワード処理テスト
- 新記法 `# 脚注 #内容##` のパース検証
- special_handler="footnote" の動作確認

### 2. `tests/unit/test_footnote_rendering.py`  
- HTMLFormatter の _handle_footnote メソッドテスト
- FootnoteManager との連携テスト
- HTML出力の正確性検証

### 3. `tests/integration/test_footnote_integration.py`
- パーサー+レンダラーの一貫テスト
- 複数脚注の番号管理テスト
- 双方向リンク生成テスト

## 新記法テストケース

### 基本テストケース
```
# 脚注 #これは基本的な脚注です##
# 脚注 #HTMLタグを含む<strong>脚注</strong>##
# 脚注 #長い脚注内容のテストケースです。複数行にわたる場合や特殊文字が含まれる場合のテスト##
```

### HTML出力期待値
- 本文中: `<sup><a href="#footnote-1" id="footnote-ref-1" class="footnote-ref">[1]</a></sup>`
- 文書末尾: `<div class="footnotes"><ol><li id="footnote-1">内容 <a href="#footnote-ref-1" class="footnote-backref">↩</a></li></ol></div>`

## 重要な実装ポイント
- 旧記法テストは存在しないため削除作業不要
- プロジェクトのcode_style_conventions準拠
- 厳格な型ヒント・エラーハンドリング必須
- logger使用パターン統一