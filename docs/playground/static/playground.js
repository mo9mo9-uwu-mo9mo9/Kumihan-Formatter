/**
 * Kumihan Formatter Playground - Main JavaScript (統合版)
 * Issue #580 - ドキュメント改善 Phase 2
 *
 * JavaScript分割ファイル統合（300行制限対応）
 */

// Kumihanプレイグラウンドのメインクラス
class KumihanPlayground {
    constructor() {
        this.inputArea = null;
        this.outputArea = null;
        this.metricsData = {};
        this.initializeComponents();
    }

    initializeComponents() {
        this.inputArea = document.getElementById('input-area');
        this.outputArea = document.getElementById('output-area');
        this.setupEventListeners();
    }

    setupEventListeners() {
        if (this.inputArea) {
            this.inputArea.addEventListener('input', this.debounce(this.handleInput.bind(this), 300));
        }
    }

    // 入力処理
    handleInput(event) {
        const text = event.target.value;
        this.convertText(text);
        this.sendGAEvent('playground_input', { length: text.length });
    }

    // テキスト変換API呼び出し
    async convertText(text) {
        try {
            const response = await fetch('/api/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });
            
            const result = await response.json();
            if (this.outputArea) {
                this.outputArea.innerHTML = result.converted_text;
            }
            
            this.checkForMermaidContent(result.converted_text);
        } catch (error) {
            console.error('変換エラー:', error);
        }
    }

    // Mermaid図表の検出と処理
    checkForMermaidContent(content) {
        const mermaidPattern = /```mermaid\n([\s\S]*?)\n```/g;
        const matches = content.match(mermaidPattern);
        
        if (matches && typeof mermaid !== 'undefined') {
            mermaid.initialize({ startOnLoad: true });
            mermaid.contentLoaded();
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

    // Google Analytics イベント送信
    sendGAEvent(eventName, parameters = {}) {
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, parameters);
        }
    }

    // Mermaid図表生成
    generateMermaidDiagram(content) {
        const mermaidContainer = document.querySelector('.mermaid-container');
        if (mermaidContainer && typeof mermaid !== 'undefined') {
            mermaidContainer.innerHTML = content;
            mermaid.init(undefined, mermaidContainer);
        }
    }
}

// Mermaidキーワード定義
const mermaidKeywords = [
    'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
    'stateDiagram', 'erDiagram', 'journey', 'gantt',
    'pie', 'gitgraph', 'C4Context', 'C4Container'
];

// 分割ファイルの動的読み込み
document.addEventListener('DOMContentLoaded', () => {
    // メインクラス初期化
    window.kumihanPlayground = new KumihanPlayground();
    
    // メイン機能スクリプト読み込み
    const scripts = [
        'playground-core.js',
        'playground-features.js',
        'playground-metrics.js'
    ];

    scripts.forEach(scriptName => {
        const script = document.createElement('script');
        script.src = `/static/${scriptName}`;
        script.async = false; // 順序保持
        document.head.appendChild(script);
    });
});