# 効率的リファクタリング・ガイド

> **目的**: Token無駄遣いを防ぎ、効率的な開発を実現する
> **対象**: 300行制限違反・ファイル分割・コード整理

## 🚨 問題の背景

### Issue #509: Token無駄遣い事例
- **問題**: 既存テストファイル分割時に、ゼロから書き直してしまった
- **影響**: 10,000+ tokenの無駄遣い（本来は1,000-2,000 tokenで済む）
- **原因**: 既存コード活用よりも新規作成を選択

## 💡 解決策

### 1. 既存コード分割の正しい手順

#### ❌ 間違った方法（Token無駄遣い）
```bash
# 既存のtest_convert_command.py（406行）を分割する場合
# 1. 新しいテストファイルを作成
# 2. ゼロからテストケースを書き直し
# 3. 既存ロジックを再実装
```

#### ✅ 正しい方法（Token効率化）
```bash
# 1. 既存ファイルの内容確認
wc -l tests/test_convert_command.py  # 406行

# 2. 分割ポイントの特定
# - line 1-135: 基本機能テスト
# - line 136-270: 高度機能テスト
# - line 271-406: 統合テスト

# 3. 機械的な分割実行
head -n 135 tests/test_convert_command.py > tests/test_convert_command_basic.py
sed -n '136,270p' tests/test_convert_command.py > tests/test_convert_command_advanced.py
tail -n +271 tests/test_convert_command.py > tests/test_convert_command_integration.py

# 4. import文の調整（最小限）
# 各ファイルの先頭に必要なimport文を追加

# 5. 元ファイルの削除
rm tests/test_convert_command.py
```

### 2. 300行制限違反の効率的修正

#### 修正手順テンプレート
```bash
# Step 1: 違反確認
python3 scripts/check_file_size.py --max-lines=300

# Step 2: 対象ファイルの分析
TARGET_FILE="large_file.py"
wc -l $TARGET_FILE
grep -n "^class\|^def\|^import" $TARGET_FILE  # 分割ポイント確認

# Step 3: 分割ポイントの決定
# - 機能別（クラス単位）
# - 責任別（Single Responsibility）
# - 依存関係考慮（import最小化）

# Step 4: 機械的分割実行
# ファイル1: 基本機能
# ファイル2: 高度機能
# ファイル3: ユーティリティ

# Step 5: 動作確認
make test
```

### 3. 分割作業のベストプラクティス

#### 分割前チェックリスト
- [ ] 既存コードの機能・構造を理解
- [ ] 分割ポイントを明確に特定
- [ ] 新規作成ではなく移動で済むことを確認
- [ ] 必要なimport文を特定

#### 分割実行時の注意点
- **コードの再利用**: 既存コードをそのまま活用
- **最小限の修正**: import文の調整のみ
- **機能保持**: 既存の動作を変更しない
- **テスト保護**: 既存テストロジックを保持

#### 分割後チェックリスト
- [ ] 全ファイルが300行制限を満たしている
- [ ] テストが通る
- [ ] 既存機能が保持されている
- [ ] 不要な新規コードが含まれていない

## 📊 効率化の効果

### Token使用量比較
| 作業方法 | Token使用量 | 作業時間 | 品質 |
|----------|-------------|----------|------|
| **効率的分割** | 1,000-2,000 | 10-15分 | 高 |
| **無駄な再作成** | 10,000+ | 60-90分 | 低 |

### 効率化による利益
- **Token節約**: 80-90%削減
- **時間短縮**: 75%短縮
- **品質向上**: 既存動作保証
- **メンテナンス性**: 構造保持

## 🔧 自動化スクリプト例

### ファイル分割支援スクリプト
```bash
#!/bin/bash
# split_file.sh - 効率的なファイル分割支援

TARGET_FILE=$1
SPLIT_LINES=${2:-135}  # デフォルト分割行数

if [ ! -f "$TARGET_FILE" ]; then
    echo "❌ ファイルが存在しません: $TARGET_FILE"
    exit 1
fi

TOTAL_LINES=$(wc -l < "$TARGET_FILE")
echo "📊 分割対象: $TARGET_FILE ($TOTAL_LINES 行)"

# 分割ポイント提案
echo "💡 分割ポイント提案:"
echo "- Part 1: 1-$SPLIT_LINES"
echo "- Part 2: $((SPLIT_LINES+1))-$((SPLIT_LINES*2))"
echo "- Part 3: $((SPLIT_LINES*2+1))-$TOTAL_LINES"

# 確認
read -p "分割を実行しますか？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 分割実行中..."
    # 実際の分割処理
else
    echo "❌ 分割をキャンセルしました"
fi
```

## 🎯 今後の改善目標

### 短期目標（1-2週間）
- [ ] 全開発者への効率化ルール周知
- [ ] 分割作業の自動化スクリプト整備
- [ ] Token使用量のモニタリング導入

### 中期目標（1-2ヶ月）
- [ ] 効率化メトリクスの収集・分析
- [ ] ベストプラクティス事例の蓄積
- [ ] 新人向けトレーニング資料作成

### 長期目標（3-6ヶ月）
- [ ] AI支援開発の最適化
- [ ] 自動リファクタリングツールの導入
- [ ] 品質とスピードの両立実現

---

**重要**: このガイドラインは継続的に更新され、実際の開発経験に基づいて改善されます。
