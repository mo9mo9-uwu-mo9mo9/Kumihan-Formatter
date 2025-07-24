/**
 * Kumihan Formatter Playground - Main JavaScript (統合版)
 * Issue #580 - ドキュメント改善 Phase 2
 *
 * JavaScript分割ファイル統合（300行制限対応）
 */

// 分割ファイルの動的読み込み
document.addEventListener('DOMContentLoaded', () => {
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
