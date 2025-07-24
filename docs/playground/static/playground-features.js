/**
 * Kumihan Formatter Playground - Feature JavaScript
 * Issue #580 - ドキュメント改善 Phase 2
 *
 * 機能別メソッド（サンプル、Mermaid、メトリクス等）
 */

// KumihanPlaygroundクラスの機能拡張
KumihanPlayground.prototype.loadSample = function() {
    const sample = `;;;見出し;;; Kumihan記法サンプル ;;;

このサンプルでは、Kumihan記法の基本機能を紹介します。

* **基本リスト**
  * ネストしたアイテム1
  * ネストしたアイテム2
    * さらにネストしたアイテム

* **装飾機能**
  * ;;;強調;;; 重要なテキスト ;;;
  * ;;;下線;;; アンダーライン ;;;

* **ルビ機能**
  * ｜漢字《かんじ》
  * ｜日本語《にほんご》

((これは脚注の例です。文末に表示されます。))

---

**今日の日付**: ${new Date().toLocaleDateString('ja-JP')}
**処理時刻**: ${new Date().toLocaleTimeString('ja-JP')}`;

    this.input.value = sample;
    this.handleInput({ target: this.input });

    // GA4イベント
    this.sendGAEvent('sample_loaded', {
        session_id: this.sessionId
    });
};

KumihanPlayground.prototype.clearContent = function() {
    this.input.value = '';
    this.showPlaceholder();
    this.updateCharCount(0);

    // GA4イベント
    this.sendGAEvent('content_cleared', {
        session_id: this.sessionId
    });
};

KumihanPlayground.prototype.checkForMermaidContent = function(text) {
    // Mermaid図表が必要そうなキーワードをチェック
    const mermaidKeywords = [
        'アーキテクチャ', 'フローチャート', '構成図', 'システム図',
        'architecture', 'flowchart', 'diagram', 'graph'
    ];

    const shouldShowMermaid = mermaidKeywords.some(keyword =>
        text.toLowerCase().includes(keyword.toLowerCase())
    );

    if (shouldShowMermaid && text.length > 100) {
        this.generateMermaidDiagram(text);
    }
};

KumihanPlayground.prototype.generateMermaidDiagram = function(text) {
    // テキスト内容に基づいてMermaid図表を自動生成
    const mermaidContainer = document.getElementById('mermaid-container');
    const mermaidContent = document.getElementById('mermaid-content');

    // 簡単なフローチャート生成例
    const mermaidCode = `
graph TD
    A[Kumihan記法入力] --> B[パース処理]
    B --> C[HTML変換]
    C --> D[プレビュー表示]
    D --> E[Mermaid図表生成]
    E --> F[完了]

    style A fill:#e1f5fe
    style F fill:#c8e6c9
    `;

    mermaidContent.innerHTML = `<div class="mermaid">${mermaidCode}</div>`;
    mermaidContainer.style.display = 'block';

    // Mermaidを再初期化
    mermaid.init(undefined, mermaidContent.querySelector('.mermaid'));
};

KumihanPlayground.prototype.toggleMermaid = function() {
    const container = document.getElementById('mermaid-container');
    const toggle = document.getElementById('mermaid-toggle');

    if (container.style.display === 'none') {
        container.style.display = 'block';
        toggle.textContent = '図表を隠す';
    } else {
        container.style.display = 'none';
        toggle.textContent = '図表を表示';
    }
};

KumihanPlayground.prototype.showSyntaxHelp = function() {
    alert(`Kumihan記法ヘルプ

基本記法:
;;;装飾名;;; 内容 ;;;  - 装飾ブロック
* リスト項目            - リストアイテム
｜漢字《かんじ》       - ルビ
((脚注内容))           - 脚注

詳細はドキュメントをご確認ください。`);
};

KumihanPlayground.prototype.toggleFullscreen = function() {
    const preview = document.querySelector('.preview-panel');

    if (!document.fullscreenElement) {
        preview.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
};

KumihanPlayground.prototype.handleKeyboard = function(event) {
    // Ctrl+Enter: 変換実行
    if (event.ctrlKey && event.key === 'Enter') {
        event.preventDefault();
        this.handleInput({ target: this.input });
    }

    // Ctrl+L: クリア
    if (event.ctrlKey && event.key === 'l') {
        event.preventDefault();
        this.clearContent();
    }

    // Ctrl+M: メトリクス表示
    if (event.ctrlKey && event.key === 'm') {
        event.preventDefault();
        this.toggleMetrics();
    }
};
