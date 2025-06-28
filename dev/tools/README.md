# Kumihan記法 開発ツール

このディレクトリには、Kumihan記法の開発・メンテナンスに役立つツールが含まれています。

## 🛠️ 利用可能なツール

### 1. 構文エラー自動修正ツール (`auto_fix_syntax.py`)

今回の修正作業で特定されたエラーパターンを自動で修正します。

**使用方法:**
```bash
# 単一ファイルの修正
python dev/tools/auto_fix_syntax.py examples/templates/basic-scenario.txt

# 複数ファイルの一括修正
python dev/tools/auto_fix_syntax.py examples/**/*.txt

# 特定ディレクトリの全ファイル修正
python dev/tools/auto_fix_syntax.py examples/templates/*.txt
```

**修正可能なエラー:**
- ✅ 見出しブロックの閉じマーカー不足
- ✅ 不要な重複 `;;;` マーカー
- ✅ Color属性の順序エラー (`ハイライト+太字` → `太字+ハイライト`)
- ✅ 問題のある独立マーカー

**安全機能:**
- 自動的にバックアップファイル（`.backup`）を作成
- 修正内容の詳細レポート表示
- 変更がない場合はファイルを変更しない

### 2. 構文エラー診断・分析ツール (`syntax_diagnostic.py`)

ファイルの構文エラーを分析して、エラーパターンの統計と修正提案を提供します。

**使用方法:**
```bash
# 単一ファイルの診断
python dev/tools/syntax_diagnostic.py examples/templates/basic-scenario.txt

# ディレクトリ全体の診断
python dev/tools/syntax_diagnostic.py examples/
```

**機能:**
- 📊 エラーパターンの統計分析
- 🔧 自動修正可能性の評価
- 📋 ファイル別詳細エラーリスト
- 📝 診断レポートの自動保存

### 3. 既存の構文チェッカー (`syntax_validator.py`)

従来からある構文チェッカーです。

```bash
python dev/tools/syntax_validator.py examples/templates/*.txt
```

## 🎯 推奨ワークフロー

### 新しいKumihan記法ファイルを作成する場合:

1. **ファイル作成**
   ```bash
   # 新しいファイルを作成
   vim new_scenario.txt
   ```

2. **構文チェック**
   ```bash
   # エラーの有無を確認
   python dev/tools/syntax_validator.py new_scenario.txt
   ```

3. **自動修正（必要に応じて）**
   ```bash
   # 一般的なエラーを自動修正
   python dev/tools/auto_fix_syntax.py new_scenario.txt
   ```

4. **最終確認**
   ```bash
   # 修正後の再チェック
   python -m kumihan_formatter.cli new_scenario.txt -o test_output/
   ```

### 大量のファイルをメンテナンスする場合:

1. **全体診断**
   ```bash
   # まずエラーの全体像を把握
   python dev/tools/syntax_diagnostic.py examples/
   ```

2. **一括自動修正**
   ```bash
   # 修正可能なエラーを一括処理
   python dev/tools/auto_fix_syntax.py examples/**/*.txt
   ```

3. **結果確認**
   ```bash
   # 修正結果を再診断
   python dev/tools/syntax_diagnostic.py examples/
   ```

## 📈 今後の拡張予定

### 自動修正機能の拡張
- [ ] より複雑な構文エラーの対応
- [ ] ユーザー設定による修正ルールのカスタマイズ
- [ ] 修正の取り消し機能

### 診断機能の強化
- [ ] エラーの重要度分類
- [ ] 修正優先度の提案
- [ ] ベストプラクティスの提案

### 統合機能
- [ ] CLI への自動修正オプション統合
- [ ] VS Code 拡張での自動修正
- [ ] CI/CD パイプラインでの自動チェック

## 🤝 コントリビューション

新しいエラーパターンを発見した場合:

1. `syntax_diagnostic.py` に検出ロジックを追加
2. `auto_fix_syntax.py` に対応する修正ロジックを追加
3. テストケースを `dev/tests/` に追加

エラーパターンの追加は、実際の問題を解決するために開発されたこれらのツールの実用性をさらに高めます。