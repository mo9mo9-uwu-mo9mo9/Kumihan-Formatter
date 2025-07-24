/**
 * Kumihan Formatter Playground - Metrics JavaScript
 * Issue #580 - ドキュメント改善 Phase 2
 *
 * DX指標関連機能
 */

// メトリクス機能の拡張
KumihanPlayground.prototype.toggleMetrics = async function() {
    const dashboard = document.getElementById('metrics-dashboard');

    if (dashboard.style.display === 'none') {
        await this.loadMetrics();
        dashboard.style.display = 'block';
    } else {
        dashboard.style.display = 'none';
    }
};

KumihanPlayground.prototype.loadMetrics = async function() {
    try {
        const response = await fetch('/api/metrics/summary');
        const data = await response.json();

        if (!data.error) {
            document.getElementById('session-count').textContent = data.total_sessions;
            document.getElementById('conversion-count').textContent = data.total_conversions;
            document.getElementById('avg-time').textContent = `${data.avg_processing_time.toFixed(1)}ms`;
            document.getElementById('error-rate').textContent = `${data.error_rate.toFixed(1)}%`;
        }

    } catch (error) {
        console.error('Failed to load metrics:', error);
    }
};

KumihanPlayground.prototype.closeMetrics = function() {
    document.getElementById('metrics-dashboard').style.display = 'none';
};

KumihanPlayground.prototype.recordSessionStart = async function() {
    try {
        await fetch('/api/metrics/session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: this.sessionId
            })
        });
    } catch (error) {
        console.error('Failed to record session:', error);
    }
};
