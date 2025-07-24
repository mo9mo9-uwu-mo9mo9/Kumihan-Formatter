# 🎮 Kumihan Formatter Playground

> **Issue #580 - ドキュメント改善 Phase 2**
> リアルタイムプレビュー機能とDX指標収集を実現

## 🌟 概要

Kumihan記法のリアルタイムプレビュー機能を提供するWebベースのプレイグラウンドです。

### 主要機能

- **⚡ リアルタイムプレビュー**: 入力と同時にHTML変換結果を表示
- **📊 Mermaid図表**: アーキテクチャ図を自動生成
- **📈 DX指標ダッシュボード**: 使用統計・パフォーマンス測定
- **🔍 Google Analytics 4**: 利用データの詳細分析

## 🚀 クイックスタート

### 1. 起動方法

```bash
# プロジェクトルートから
python docs/playground/start_playground.py

# または、playgroundディレクトリから
cd docs/playground
python start_playground.py
```

### 2. アクセス

起動後、自動的にブラウザで `http://localhost:8080` が開かれます。

## 🎯 使用方法

### 基本操作

1. **左パネル**: Kumihan記法を入力
2. **右パネル**: リアルタイムでHTMLプレビューを表示
3. **サンプル**: 「サンプル表示」ボタンで記法例を確認
4. **統計**: 「統計表示」ボタンでDX指標を確認

### キーボードショートカット

- `Ctrl + Enter`: 変換実行
- `Ctrl + L`: 内容クリア
- `Ctrl + M`: メトリクス表示切り替え

### サンプル記法

```kumihan
;;;見出し;;; メインタイトル ;;;

* リスト項目1
  * ネストしたアイテム
* リスト項目2

((脚注のテスト))

｜漢字《かんじ》のルビ表現
```

## 📊 DX指標について

### 収集データ

- **セッション数**: プレイグラウンド利用回数
- **変換実行数**: リアルタイム変換の実行回数
- **平均処理時間**: 変換処理のパフォーマンス
- **エラー率**: 変換失敗の割合

### データ活用

- オンボーディング時間63%短縮の測定
- 開発者満足度40%向上の評価指標
- 理解度・定着率90%向上の定量化

## 🎨 技術構成

### バックエンド
- **FastAPI**: RESTful API サーバー
- **Uvicorn**: ASGI Webサーバー
- **Jinja2**: HTMLテンプレートエンジン

### フロントエンド
- **Vanilla JavaScript**: リアルタイム機能
- **Mermaid.js**: 図表レンダリング
- **CSS Grid**: レスポンシブレイアウト

### 分析
- **Google Analytics 4**: 利用データ分析
- **内蔵メトリクス**: パフォーマンス測定

## 🔧 開発者向け情報

### ファイル構成

```
docs/playground/
├── server.py              # FastAPIサーバー
├── start_playground.py    # 起動スクリプト
├── templates/
│   └── playground.html    # メインテンプレート
├── static/
│   ├── playground.css     # スタイルシート
│   └── playground.js      # JavaScript機能
└── README.md             # このファイル
```

### API エンドポイント

- `GET /`: プレイグラウンドページ
- `POST /api/convert`: Kumihan記法変換
- `POST /api/metrics/session`: セッション記録
- `GET /api/metrics/summary`: 統計サマリー
- `GET /health`: ヘルスチェック

### カスタマイズ

1. **テーマ変更**: `static/playground.css` を編集
2. **機能追加**: `static/playground.js` を拡張
3. **API拡張**: `server.py` にエンドポイント追加

## 📈 期待される成果

### 定量的目標

- **オンボーディング時間**: 63%短縮
- **開発者満足度**: 40%向上
- **理解度・定着率**: 90%向上

### 定性的効果

- Kumihan記法の学習コストを大幅に削減
- リアルタイムフィードバックによる開発体験向上
- 継続的な改善サイクルの実現

## 🐛 トラブルシューティング

### よくある問題

**Q: サーバーが起動しない**
```bash
# 依存関係を手動インストール
pip install fastapi uvicorn jinja2

# ポート8080が使用中の場合
lsof -ti:8080 | xargs kill
```

**Q: 変換が動作しない**
- プロジェクトルートから起動しているか確認
- kumihan_formatterモジュールがインポート可能か確認

**Q: ブラウザが開かない**
- 手動で `http://localhost:8080` にアクセス

## 📝 ライセンス

プロジェクトライセンスに準拠

---

**🎮 Kumihan Formatter Playground で効率的な記法学習を始めましょう！**
