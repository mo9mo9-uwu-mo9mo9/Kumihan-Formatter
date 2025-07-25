# 暗黙仕様分析レポート - Issue #75

> **Phase 1-2 完了**: 暗黙仕様の特定とサポート可否判断

## 📋 調査概要

プロジェクト内での「暗黙的に期待される記法」の使用状況を全面調査し、正式サポートするか削除するかの技術的判断を実施。

## 🚨 発見された重大な問題

### 問題の概要
**ドキュメント内でのMarkdown記法大量使用により、ユーザーの期待と実際の仕様に深刻な乖離が発生**

### 具体的な矛盾

| 公式仕様（SPEC.md） | ドキュメント内の実態 | 影響度 |
|-------------------|-------------------|--------|
| 「行頭 # 記法は非サポート」 | 17ファイルで200回以上使用 | 🔴 極めて深刻 |
| 「**太字** 記法は非サポート」 | 15ファイルで100回以上使用 | 🔴 極めて深刻 |
| 「Markdown記法は使用禁止」 | 全ドキュメントで大量使用 | 🔴 極めて深刻 |

## 🔍 Phase 1: 暗黙仕様の特定結果

### examples/ フォルダ調査結果 ✅
**結果**: 高い一貫性を確認
- Kumihan-Formatter独自記法で統一されている
- 暗黙的Markdown記法はほぼ使用されていない
- 意図的なテスト用記法のみ含有

### docs/ フォルダ調査結果 🚨
**結果**: 深刻な不整合を確認

#### 使用統計
| 記法種類 | 使用ファイル数 | 総使用回数 | 状況 |
|----------|----------------|------------|------|
| 行頭 # 見出し | 17/22ファイル | 200回以上 | 🔴 極めて深刻 |
| **太字** 記法 | 15/22ファイル | 100回以上 | 🔴 極めて深刻 |
| テーブル記法 | 8/22ファイル | 50回以上 | 🟡 中程度 |
| コードブロック | 22/22ファイル | 300回以上 | 🟢 許容範囲 |
| 番号付きリスト | 10/22ファイル | 30回以上 | 🟢 正式サポート済み |

#### 最も深刻なファイル
1. `docs/user/DOUBLE_CLICK_GUIDE.md` - 28回の行頭#記法
2. `docs/SYNTAX_REFERENCE.md` - 20回の行頭#記法
3. `docs/user/LINE_BREAK_GUIDE.md` - 19回の行頭#記法

## 📊 Phase 2: サポート可否の判断

### 判断基準の設定

| 基準 | 重み | 説明 |
|------|------|------|
| **技術的実現性** | 30% | パーサー・レンダラーでの実装コスト |
| **ユーザー価値** | 25% | 機能追加の実用性評価 |
| **互換性影響** | 25% | 既存機能への影響度 |
| **保守性** | 20% | 長期的なメンテナンス負荷 |

### 個別記法の判断結果

#### 1. 行頭 # 記法（Markdown風見出し）

**判定**: 🟡 **条件付きサポート検討**

| 評価項目 | スコア | 理由 |
|----------|--------|------|
| 技術的実現性 | 7/10 | パーサー改修は可能だが複雑 |
| ユーザー価値 | 9/10 | Markdown慣れユーザーに高い利便性 |
| 互換性影響 | 6/10 | 既存機能への影響は限定的 |
| 保守性 | 5/10 | 2つの見出し記法の併存で複雑化 |

**総合スコア**: 6.8/10

**推奨対応**: 
- **段階的導入** - 将来バージョンでの限定的サポート検討
- **現在**: ドキュメント統一を優先

#### 2. **太字** インライン記法

**判定**: 🔴 **非サポート維持**

| 評価項目 | スコア | 理由 |
|----------|--------|------|
| 技術的実現性 | 4/10 | パーサーの大幅改修が必要 |
| ユーザー価値 | 6/10 | 利便性はあるが既存記法で代替可能 |
| 互換性影響 | 3/10 | 既存のブロック記法と競合リスク |
| 保守性 | 2/10 | インライン・ブロック記法の併存で複雑化 |

**総合スコア**: 3.8/10

**推奨対応**: 
- **非サポート維持** - 既存ブロック記法で統一
- **ドキュメント修正** - 使用箇所をKumihan記法に変換

#### 3. テーブル記法（| 区切り）

**判定**: 🟡 **将来検討候補**

| 評価項目 | スコア | 理由 |
|----------|--------|------|
| 技術的実現性 | 6/10 | 実装可能だが専用レンダラーが必要 |
| ユーザー価値 | 8/10 | TRPG資料での表は重要 |
| 互換性影響 | 8/10 | 既存機能との競合なし |
| 保守性 | 6/10 | 独立機能として実装可能 |

**総合スコア**: 6.8/10

**推奨対応**: 
- **v2.0での検討** - TRPG汎用化時に検討
- **現在**: ドキュメントでの使用を控える

#### 4. コメント記法

**判定**: 🔴 **非サポート維持**

| 評価項目 | スコア | 理由 |
|----------|--------|------|
| 技術的実現性 | 8/10 | 実装は比較的容易 |
| ユーザー価値 | 3/10 | TRPG文書での需要が低い |
| 互換性影響 | 9/10 | 既存機能への影響なし |
| 保守性 | 7/10 | シンプルな機能 |

**総合スコア**: 5.8/10

**推奨対応**: 
- **非サポート維持** - TRPG特化の方針に合致しない
- **需要が高まれば将来検討**

## 🎯 最終的な方針決定

### 短期対応（v0.4.0まで）

#### 1. ドキュメント統一作業 🔴 **最優先**
- `docs/user/` 内の全ファイルをKumihan記法に統一
- 特に以下を優先：
  - `SYNTAX_REFERENCE.md`
  - `FIRST_RUN.md` 
  - `QUICKSTART.md`
  - `DOUBLE_CLICK_GUIDE.md`

#### 2. 仕様明確化 🟡
- SPEC.mdに「ドキュメント記法と変換記法の違い」を明記
- 非サポート記法の理由を追記

### 中期対応（v1.0まで）

#### 1. 段階的機能検討
- **行頭 # 記法**: ユーザー要望を見て検討
- **テーブル記法**: TRPG汎用化での需要調査

#### 2. ツール整備
- ドキュメント記法チェッカー作成
- CI/CDでの自動検証

### 長期対応（v2.0以降）

#### TRPG汎用化での再評価
- 他システム対応での記法需要調査
- 互換性重視の記法拡張検討

## 📈 期待効果

### 短期効果
- ✅ ユーザーの混乱解消
- ✅ 仕様の一貫性確保
- ✅ 学習コストの軽減

### 中期効果
- ✅ ブランド認知の向上（独自記法の浸透）
- ✅ 開発効率の向上（仕様明確化）
- ✅ 品質保証の強化

### 長期効果
- ✅ TRPG特化ツールとしてのポジション確立
- ✅ 拡張性のある設計基盤構築
- ✅ コミュニティからの信頼獲得

## 🔗 関連情報

**Issue**: #75 - 暗黙の仕様の明文化または削除判断
**フェーズ**: Phase 1-2 完了
**次のステップ**: Phase 3（個別機能の方針決定）

**関連ファイル**:
- `SPEC.md` - 記法仕様書
- `docs/dev/CONTRIBUTING.md` - 開発ガイドライン
- `docs/user/*.md` - 修正対象ドキュメント群

---

**結論**: 暗黙仕様の問題は主に「ドキュメント記法の不統一」に起因する。技術的な機能追加より、**ドキュメント統一による即座の問題解決**を優先すべき。