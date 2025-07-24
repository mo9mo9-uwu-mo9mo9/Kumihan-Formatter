/**
 * Kumihan Formatter Playground - Core JavaScript
 * Issue #580 - ドキュメント改善 Phase 2
 *
 * メインクラスと基本機能
 */

class KumihanPlayground {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.conversionCount = 0;
        this.errorCount = 0;
        this.lastProcessingTime = 0;

        this.init();
    }

    init() {
        // DOM要素の取得
        this.input = document.getElementById('kumihan-input');
        this.preview = document.getElementById('preview-content');
        this.charCount = document.getElementById('char-count');
        this.processingTime = document.getElementById('processing-time');

        // Mermaid設定
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose'
        });

        // イベントリスナーの設定
        this.setupEventListeners();

        // セッション開始を記録
        this.recordSessionStart();

        // GA4イベント送信
        this.sendGAEvent('session_start', {
            session_id: this.sessionId
        });
    }

    setupEventListeners() {
        // リアルタイム変換
        this.input.addEventListener('input', this.debounce(this.handleInput.bind(this), 300));

        // ボタンイベント
        document.getElementById('sample-btn').addEventListener('click', this.loadSample.bind(this));
        document.getElementById('clear-btn').addEventListener('click', this.clearContent.bind(this));
        document.getElementById('metrics-btn').addEventListener('click', this.toggleMetrics.bind(this));
        document.getElementById('syntax-help-btn').addEventListener('click', this.showSyntaxHelp.bind(this));
        document.getElementById('fullscreen-btn').addEventListener('click', this.toggleFullscreen.bind(this));

        // Mermaidトグル
        const mermaidToggle = document.getElementById('mermaid-toggle');
        if (mermaidToggle) {
            mermaidToggle.addEventListener('click', this.toggleMermaid.bind(this));
        }

        // メトリクス閉じるボタン
        const metricsClose = document.getElementById('metrics-close');
        if (metricsClose) {
            metricsClose.addEventListener('click', this.closeMetrics.bind(this));
        }

        // キーボードショートカット
        document.addEventListener('keydown', this.handleKeyboard.bind(this));
    }

    handleInput(event) {
        const text = event.target.value;

        // 文字数更新
        this.updateCharCount(text.length);

        // プレビュー更新
        if (text.trim()) {
            this.convertText(text);
        } else {
            this.showPlaceholder();
        }

        // Mermaid図表チェック
        this.checkForMermaidContent(text);
    }

    async convertText(text) {
        const startTime = performance.now();

        try {
            const response = await fetch('/api/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            const data = await response.json();
            const endTime = performance.now();
            const processingTime = endTime - startTime;

            if (data.success) {
                this.preview.innerHTML = data.html;
                this.preview.classList.add('fade-in');

                // 処理時間表示
                this.processingTime.textContent = `${processingTime.toFixed(1)}ms`;
                this.lastProcessingTime = processingTime;

                this.conversionCount++;

                // GA4イベント
                this.sendGAEvent('conversion_success', {
                    processing_time: processingTime,
                    input_length: text.length,
                    session_id: this.sessionId
                });

            } else {
                this.showError(data.error || '変換エラーが発生しました');
                this.errorCount++;

                // GA4エラーイベント
                this.sendGAEvent('conversion_error', {
                    error_message: data.error,
                    session_id: this.sessionId
                });
            }

        } catch (error) {
            console.error('Conversion failed:', error);
            this.showError('ネットワークエラーが発生しました');
            this.errorCount++;
        }
    }

    updateCharCount(count) {
        this.charCount.textContent = `${count}文字`;

        // 文字数に応じて色を変更
        if (count > 5000) {
            this.charCount.style.color = '#dc3545';
        } else if (count > 2000) {
            this.charCount.style.color = '#ffc107';
        } else {
            this.charCount.style.color = '#6c757d';
        }
    }

    showPlaceholder() {
        this.preview.innerHTML = `
            <div class="placeholder">
                <p>👈 左側にKumihan記法を入力すると、ここにリアルタイムプレビューが表示されます</p>
            </div>
        `;
        this.processingTime.textContent = '-';
    }

    showError(message) {
        this.preview.innerHTML = `
            <div class="error">
                <strong>エラー:</strong> ${message}
            </div>
        `;
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    sendGAEvent(eventName, parameters) {
        if (typeof gtag === 'function') {
            gtag('event', eventName, parameters);
        }
    }

    // デバウンス関数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// プレイグラウンド初期化
document.addEventListener('DOMContentLoaded', () => {
    new KumihanPlayground();
});
