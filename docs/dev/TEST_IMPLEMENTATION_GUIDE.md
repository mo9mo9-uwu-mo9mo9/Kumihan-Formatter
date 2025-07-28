# テスト戦略v2.0 実装ガイド

> **即座に実行可能な実装手順** - 段階的移行による安全な品質改善

---

## 🚀 Phase 1: 即座に実行（今日）

### 1.1 新テスト実行確認

```bash
# 新しいテストディレクトリの確認
ls -la tests_v2/

# Contract Tests実行
PYTHONPATH=. python -m pytest tests_v2/contracts/ -v

# Integration Tests実行
PYTHONPATH=. python -m pytest tests_v2/integration/ -v
```

### 1.2 新CI設定の有効化

```bash
# 新しいワークフロー確認
git add .github/workflows/test-v2.yml
git commit -m "feat: Test Strategy v2.0 - Contract-First Testing導入"
git push origin <current-branch>
```

---

## 📋 Phase 2: Contract Tests拡張（1週間以内）

### 2.1 CLI Contract Test

```python
# tests_v2/contracts/test_cli_contract.py
def test_convert_command_contract():
    """convert コマンドの基本契約"""
    # Given: 有効な入力ファイル
    input_file = create_test_file("basic.txt", ";;;太字;;;テスト;;;")

    # When: convert実行
    result = subprocess.run([
        "python", "-m", "kumihan_formatter",
        "convert", input_file
    ], capture_output=True)

    # Then: 成功する
    assert result.returncode == 0
    assert Path(input_file).with_suffix('.html').exists()
```

### 2.2 Renderer Contract Test

```python
# tests_v2/contracts/test_renderer_contract.py
def test_html_renderer_contract():
    """HTMLレンダラーの基本契約"""
    from kumihan_formatter.core.rendering.main_renderer import MainRenderer

    # Given: 解析済みデータ
    parsed_data = create_parsed_data()

    # When: レンダリング実行
    renderer = MainRenderer()
    html_output = renderer.render(parsed_data)

    # Then: 有効なHTMLが生成される
    assert "<html>" in html_output
    assert "</html>" in html_output
    assert len(html_output) > 100  # 最小限のコンテンツ
```

---

## 🔄 Phase 3: Integration Tests拡張

### 3.1 エラーシナリオテスト

```python
# tests_v2/integration/test_error_scenarios.py
class TestErrorScenarios:
    def test_file_permission_error_handling(self):
        """ファイル権限エラーのハンドリング"""

    def test_large_file_memory_management(self):
        """大容量ファイルのメモリ管理"""

    def test_encoding_detection_pipeline(self):
        """エンコーディング検出パイプライン"""
```

### 3.2 プラットフォーム固有テスト

```python
# tests_v2/integration/test_platform_specific.py
@pytest.mark.skipif(sys.platform != "win32", reason="Windows専用")
def test_windows_path_handling():
    """Windowsパス処理の統合テスト"""

@pytest.mark.skipif(sys.platform != "darwin", reason="macOS専用")
def test_macos_unicode_handling():
    """macOS Unicode処理の統合テスト"""
```

---

## ⚡ Phase 4: 旧テスト削除（安全な移行）

### 4.1 検証期間（1週間）

```bash
# 新テストの品質確認
pytest tests_v2/ --cov=kumihan_formatter --cov-report=term-missing

# 新旧テスト並行実行による比較
pytest tests_v2/ -v > new_test_results.txt
pytest tests/unit/ -v > old_test_results.txt

# 結果比較
echo "新テスト成功率: $(grep -c PASSED new_test_results.txt)"
echo "旧テスト成功率: $(grep -c PASSED old_test_results.txt)"
```

### 4.2 段階的削除

```bash
# Step 1: 旧テストを無効化ディレクトリに移動
mkdir tests/_archived_v1
git mv tests/unit tests/_archived_v1/
git mv tests/integration tests/_archived_v1/

# Step 2: CI設定更新
# pytest tests/ → pytest tests_v2/

# Step 3: 最終確認後の完全削除
git rm -r tests/_archived_v1/
```

---

## 📊 品質測定・モニタリング

### 定量的メトリクス

```bash
# 実行時間測定
time pytest tests_v2/contracts/ -q
time pytest tests_v2/integration/ -q

# 成功率測定
pytest tests_v2/ --tb=no | grep -E "(passed|failed|error)"

# カバレッジ測定（必要最小限）
pytest tests_v2/ --cov=kumihan_formatter --cov-report=term --cov-fail-under=60
```

### 品質ダッシュボード

```markdown
## 📈 Test Strategy v2.0 ダッシュボード

| メトリクス | 目標 | 現在 | 状態 |
|-----------|------|------|------|
| CI実行時間 | 3分以内 | _分_秒 | ⏱️ |
| Contract Tests | 100%成功 | _% | 📋 |
| Integration Tests | 95%成功 | _% | 🔄 |
| 開発阻害時間 | 週2時間以内 | _時間/週 | 🚀 |
```

---

## 🛠️ 実装のベストプラクティス

### Contract Test作成指針

```python
# ✅ Good - 契約に集中
def test_parser_contract():
    result = parser.parse(";;;太字;;;内容;;;")
    assert "太字" in str(result)  # 契約: 太字として認識

# ❌ Bad - 実装詳細をテスト
def test_parser_implementation():
    result = parser.parse(";;;太字;;;内容;;;")
    assert result.type == "BoldNode"  # 実装詳細
    assert result.children[0].text == "内容"  # 内部構造
```

### Integration Test作成指針

```python
# ✅ Good - E2Eフローに集中
def test_conversion_pipeline():
    # ファイル入力 → CLI実行 → 出力確認
    input_file = create_test_file(content)
    subprocess.run(["python", "-m", "kumihan_formatter", "convert", input_file])
    assert output_exists_and_valid()

# ❌ Bad - 単体テストの集合
def test_each_component_separately():
    test_parser()
    test_renderer()
    test_file_writer()  # これらは個別にテストすべきでない
```

---

## 🚨 トラブルシューティング

### よくある問題と対策

| 問題 | 症状 | 対策 |
|------|------|------|
| **Import Error** | `ModuleNotFoundError` | `PYTHONPATH=.` を追加 |
| **Timeout** | テストがハング | `--timeout=30` 設定確認 |
| **Path Issues** | ファイルが見つからない | 絶対パス使用、temp directory活用 |
| **Platform Differences** | OS別の動作差異 | `@pytest.mark.skipif` でOS限定 |

### デバッグ手順

```bash
# 詳細ログでテスト実行
KUMIHAN_LOG_LEVEL=DEBUG pytest tests_v2/contracts/test_parser_contract.py -v -s

# 特定テストのみ実行
pytest tests_v2/contracts/test_parser_contract.py::TestParserContract::test_basic_bold_syntax_contract -v

# 失敗時の詳細表示
pytest tests_v2/ --tb=long --show-capture=all
```

---

## 📅 マイルストーン・チェックリスト

### Week 1: 基盤構築
- [ ] 新テストディレクトリ作成
- [ ] 最初のContract Test動作確認
- [ ] 新CI設定動作確認
- [ ] チームレビュー完了

### Week 2: Contract Tests実装
- [ ] Parser Contract Test完成
- [ ] CLI Contract Test完成
- [ ] Renderer Contract Test完成
- [ ] 全Contract Tests 100%成功

### Week 3-4: Integration Tests実装
- [ ] 基本パイプラインテスト完成
- [ ] エラーシナリオテスト完成
- [ ] プラットフォーム固有テスト完成
- [ ] パフォーマンステスト完成

### Week 5: 移行完了
- [ ] 新テスト品質確認完了
- [ ] 旧テスト無効化完了
- [ ] CI設定更新完了
- [ ] ドキュメント更新完了

---

**このガイドに従って段階的に実装することで、品質を保ちながら効率的なテスト体制を構築できます。**
