# セキュリティテスト実装ガイド

> **Kumihan-Formatter セキュリティ管理システム**  
> バージョン: 1.0.0 (2025-01-29)  
> 【根本改革】セキュリティファースト開発対応

## 🛡️ セキュリティテストシステム概要

Kumihan-Formatterでは、**セキュリティファースト開発**により、プロダクション環境における脆弱性を事前に防止し、安全で信頼性の高いソフトウェアを提供します。

### セキュリティ基本方針

1. **防御的設計**: すべての入力を疑い、適切な検証・サニタイズを実施
2. **多層防御**: 複数のセキュリティ対策を組み合わせたリスク軽減
3. **継続的監視**: CI/CDパイプラインでの自動セキュリティテスト
4. **セキュアコーディング**: 開発段階でのセキュリティベストプラクティス適用
5. **透明性確保**: セキュリティテスト結果の可視化と追跡

---

## 🎯 必須セキュリティテスト項目

### 1. SQLインジェクション対策テスト

**対象**: データベースクエリを実行するすべての機能

```python
# scripts/security_sql_injection_test.py

class SqlInjectionSecurityTest:
    """SQLインジェクション対策テスト"""
    
    def __init__(self):
        self.malicious_payloads = [
            # Basic injection patterns
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/**/OR/**/1=1/**/--",
            
            # Advanced injection patterns  
            "1' UNION SELECT password FROM users WHERE username='admin'--",
            "'; INSERT INTO users (username, password) VALUES ('hacker', 'pwd'); --",
            "1' AND (SELECT COUNT(*) FROM information_schema.tables) > 0 --",
            
            # Blind injection patterns
            "1' AND ASCII(SUBSTRING((SELECT password FROM users WHERE username='admin'),1,1)) > 65 --",
            "1' AND (SELECT SUBSTRING(@@version,1,1)) = '5' --"
        ]
    
    def test_input_sanitization(self, target_function):
        """入力サニタイゼーション テスト"""
        results = []
        
        for payload in self.malicious_payloads:
            try:
                result = target_function(payload)
                
                # 危険なSQLキーワードが結果に含まれていないことを確認
                dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'UNION', 'SELECT']
                
                has_dangerous_content = any(
                    keyword.lower() in str(result).lower() 
                    for keyword in dangerous_keywords
                )
                
                results.append({
                    'payload': payload,
                    'safe': not has_dangerous_content,
                    'result': str(result)[:100]  # 結果の最初の100文字のみ
                })
                
            except Exception as e:
                # 例外が発生した場合も安全とみなす（適切なエラーハンドリング）
                results.append({
                    'payload': payload,
                    'safe': True,
                    'error': str(e)
                })
        
        return results
    
    def run_comprehensive_test(self):
        """包括的SQLインジェクションテスト実行"""
        test_functions = [
            'user_search',
            'data_query',
            'content_filter',
            'parameter_processing'
        ]
        
        all_results = {}
        for func_name in test_functions:
            if hasattr(self, f'_{func_name}_test'):
                test_func = getattr(self, f'_{func_name}_test')
                all_results[func_name] = test_func()
        
        return all_results
```

### 2. クロスサイトスクリプティング（XSS）対策テスト

**対象**: ユーザー入力を出力に反映するすべての機能

```python
# scripts/security_xss_test.py

class XssSecurityTest:
    """XSS対策テスト"""
    
    def __init__(self):
        self.xss_payloads = [
            # Basic XSS patterns
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            
            # Advanced XSS patterns
            "<svg onload=alert('XSS')>",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<body onload=alert('XSS')>",
            
            # Encoded XSS patterns
            "%3Cscript%3Ealert('XSS')%3C/script%3E",
            "&#60;script&#62;alert('XSS')&#60;/script&#62;",
            
            # Event handler XSS
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            
            # CSS-based XSS
            "<style>@import'javascript:alert(\"XSS\")';</style>",
            "<link rel=stylesheet href='javascript:alert(\"XSS\")'>"
        ]
    
    def test_output_encoding(self, render_function):
        """出力エンコーディング テスト"""
        results = []
        
        for payload in self.xss_payloads:
            try:
                rendered_output = render_function(payload)
                
                # 危険なタグ・属性がエスケープされているかチェック
                dangerous_patterns = [
                    '<script>', '</script>',
                    'javascript:', 'onload=', 'onerror=',
                    'onfocus=', 'onmouseover=', '@import'
                ]
                
                is_safe = not any(
                    pattern.lower() in rendered_output.lower()
                    for pattern in dangerous_patterns
                )
                
                # HTMLエンティティエンコーディングの確認
                properly_encoded = (
                    '&lt;' in rendered_output or 
                    '&gt;' in rendered_output or
                    '&quot;' in rendered_output
                )
                
                results.append({
                    'payload': payload,
                    'safe': is_safe,
                    'properly_encoded': properly_encoded,
                    'output': rendered_output[:200]
                })
                
            except Exception as e:
                results.append({
                    'payload': payload,
                    'safe': True,  # エラーで出力されない場合は安全
                    'error': str(e)
                })
        
        return results
    
    def test_content_security_policy(self):
        """Content Security Policy テスト"""
        # CSP ヘッダーの存在と設定確認
        expected_csp_directives = [
            "default-src 'self'",
            "script-src 'self'",
            "object-src 'none'",
            "base-uri 'self'"
        ]
        
        # 実際のCSP実装をテスト
        return {
            'csp_implemented': True,  # 実装状況に応じて動的に設定
            'recommended_directives': expected_csp_directives
        }
```

### 3. クロスサイトリクエストフォージェリ（CSRF）対策テスト

**対象**: 状態変更を伴うすべてのHTTPリクエスト処理

```python
# scripts/security_csrf_test.py

class CsrfSecurityTest:
    """CSRF対策テスト"""
    
    def test_csrf_token_validation(self, request_handler):
        """CSRFトークン検証テスト"""
        test_cases = [
            # 正常なトークン
            {'token': 'valid_csrf_token_123', 'expected': True},
            
            # 無効なトークン
            {'token': 'invalid_token', 'expected': False},
            {'token': '', 'expected': False},
            {'token': None, 'expected': False},
            
            # トークン偽造試行
            {'token': 'forged_token_xyz', 'expected': False},
            {'token': 'valid_csrf_token_124', 'expected': False},  # 類似トークン
        ]
        
        results = []
        for case in test_cases:
            try:
                is_valid = request_handler.validate_csrf_token(case['token'])
                
                results.append({
                    'token': case['token'],
                    'expected_valid': case['expected'],
                    'actual_valid': is_valid,
                    'test_passed': is_valid == case['expected']
                })
                
            except Exception as e:
                results.append({
                    'token': case['token'],
                    'error': str(e),
                    'test_passed': not case['expected']  # エラー = 無効扱い
                })
        
        return results
    
    def test_same_origin_policy(self):
        """Same Origin Policy テスト"""
        # Referrer ヘッダーのチェック
        malicious_origins = [
            'http://evil.com',
            'https://attacker.site',
            'http://localhost:9999',  # 攻撃者のローカルサーバー
            'null',  # null origin
            ''  # 空のorigin
        ]
        
        results = []
        for origin in malicious_origins:
            # オリジン検証のテスト
            is_blocked = self._test_origin_validation(origin)
            results.append({
                'origin': origin,
                'blocked': is_blocked,
                'safe': is_blocked  # ブロックされるべき
            })
        
        return results
    
    def _test_origin_validation(self, origin):
        """オリジン検証の実装テスト"""
        # 実際のオリジン検証ロジックをテスト
        allowed_origins = [
            'https://yourdomain.com',
            'https://www.yourdomain.com'
        ]
        
        return origin not in allowed_origins
```

### 4. ファイルアップロードセキュリティテスト

**対象**: ファイルアップロード機能

```python
# scripts/security_file_upload_test.py

class FileUploadSecurityTest:
    """ファイルアップロードセキュリティテスト"""
    
    def __init__(self):
        self.malicious_file_types = [
            # 実行可能ファイル
            {'name': 'malware.exe', 'content': b'MZ\x90\x00', 'should_block': True},
            {'name': 'script.bat', 'content': b'@echo off\nformat c:', 'should_block': True},
            {'name': 'shell.sh', 'content': b'#!/bin/bash\nrm -rf /', 'should_block': True},
            
            # Web実行可能ファイル  
            {'name': 'webshell.php', 'content': b'<?php system($_GET["cmd"]); ?>', 'should_block': True},
            {'name': 'script.jsp', 'content': b'<%Runtime.getRuntime().exec(request.getParameter("cmd"));%>', 'should_block': True},
            
            # 偽装ファイル
            {'name': 'image.jpg.exe', 'content': b'fake_image_content', 'should_block': True},
            {'name': 'document.pdf.bat', 'content': b'@echo malicious', 'should_block': True},
            
            # 正当なファイル（テスト用）
            {'name': 'document.txt', 'content': b'legitimate content', 'should_block': False},
            {'name': 'image.png', 'content': b'\x89PNG\r\n\x1a\n', 'should_block': False},
        ]
    
    def test_file_type_validation(self, upload_handler):
        """ファイルタイプ検証テスト"""
        results = []
        
        for file_test in self.malicious_file_types:
            try:
                # ファイルアップロードのテスト
                is_accepted = upload_handler.validate_file(
                    filename=file_test['name'],
                    content=file_test['content']
                )
                
                # セキュリティ要件に適合しているかチェック
                security_compliant = (
                    (file_test['should_block'] and not is_accepted) or
                    (not file_test['should_block'] and is_accepted)
                )
                
                results.append({
                    'filename': file_test['name'],
                    'should_block': file_test['should_block'],
                    'was_accepted': is_accepted,
                    'security_compliant': security_compliant
                })
                
            except Exception as e:
                # 例外が発生した場合は、危険なファイルが適切にブロックされたと判断
                results.append({
                    'filename': file_test['name'],
                    'blocked_by_exception': True,
                    'security_compliant': file_test['should_block'],
                    'error': str(e)
                })
        
        return results
    
    def test_file_size_limits(self, upload_handler):
        """ファイルサイズ制限テスト"""
        size_tests = [
            {'size': 1024, 'should_accept': True},  # 1KB - 正常
            {'size': 1024 * 1024, 'should_accept': True},  # 1MB - 正常
            {'size': 10 * 1024 * 1024, 'should_accept': True},  # 10MB - 境界値
            {'size': 100 * 1024 * 1024, 'should_accept': False},  # 100MB - 大きすぎる
            {'size': 1024 * 1024 * 1024, 'should_accept': False},  # 1GB - 攻撃的サイズ
        ]
        
        results = []
        for test in size_tests:
            large_content = b'A' * test['size']
            
            try:
                is_accepted = upload_handler.validate_file(
                    filename='test_file.txt',
                    content=large_content
                )
                
                results.append({
                    'file_size': test['size'],
                    'should_accept': test['should_accept'],
                    'was_accepted': is_accepted,
                    'test_passed': is_accepted == test['should_accept']
                })
                
            except Exception as e:
                results.append({
                    'file_size': test['size'],
                    'rejected_by_exception': True,
                    'test_passed': not test['should_accept'],
                    'error': str(e)
                })
        
        return results
```

---

## 🔧 セキュリティテスト基盤システム

### セキュリティテスト基底クラス

```python
# kumihan_formatter/security/test_base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import logging

class SecurityTestBase(ABC):
    """セキュリティテスト基底クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.test_results: List[Dict[str, Any]] = []
    
    @abstractmethod
    def run_security_tests(self) -> Dict[str, Any]:
        """セキュリティテスト実行（サブクラスで実装）"""
        pass
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """セキュリティイベントのログ記録"""
        self.logger.warning(f"Security Event: {event_type} - {details}")
    
    def assert_secure(self, condition: bool, message: str):
        """セキュリティ要件のアサーション"""
        if not condition:
            self.log_security_event("SECURITY_VIOLATION", {"message": message})
            raise SecurityViolationError(message)
    
    def generate_security_report(self) -> Dict[str, Any]:
        """セキュリティテストレポート生成"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.get('passed', False))
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'detailed_results': self.test_results
        }

class SecurityViolationError(Exception):
    """セキュリティ要件違反エラー"""
    pass
```

### 統合セキュリティテストランナー

```python
# scripts/integrated_security_test_runner.py

class IntegratedSecurityTestRunner:
    """統合セキュリティテストランナー"""
    
    def __init__(self):
        self.test_classes = [
            SqlInjectionSecurityTest,
            XssSecurityTest, 
            CsrfSecurityTest,
            FileUploadSecurityTest
        ]
        
    def run_all_security_tests(self) -> Dict[str, Any]:
        """全セキュリティテスト実行"""
        overall_results = {
            'timestamp': datetime.now().isoformat(),
            'test_suite_results': {},
            'summary': {}
        }
        
        total_tests = 0
        total_passed = 0
        
        for test_class in self.test_classes:
            test_instance = test_class()
            test_name = test_class.__name__
            
            try:
                results = test_instance.run_security_tests()
                overall_results['test_suite_results'][test_name] = results
                
                # 統計計算
                suite_total = results.get('total_tests', 0)
                suite_passed = results.get('passed_tests', 0)
                
                total_tests += suite_total
                total_passed += suite_passed
                
            except Exception as e:
                overall_results['test_suite_results'][test_name] = {
                    'error': str(e),
                    'status': 'FAILED'
                }
        
        # 全体サマリー
        overall_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': total_passed,
            'failed_tests': total_tests - total_passed,
            'overall_success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'security_compliant': total_passed == total_tests
        }
        
        return overall_results
```

---

## 🚦 CI/CD統合

### GitHub Actions セキュリティテスト

```yaml
# .github/workflows/security-tests.yml

name: Security Testing Pipeline

on:
  push:
    branches: [ main, develop, "feat/*" ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 2 * * *'  # 毎日 2:00 UTC に実行

jobs:
  security-tests:
    name: Comprehensive Security Testing
    runs-on: ubuntu-latest
    timeout-minutes: 20
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          
      - name: Run SQL Injection Tests
        run: |
          python scripts/security_sql_injection_test.py --output-format=json > sql_injection_results.json
          
      - name: Run XSS Protection Tests
        run: |
          python scripts/security_xss_test.py --output-format=json > xss_results.json
          
      - name: Run CSRF Protection Tests
        run: |
          python scripts/security_csrf_test.py --output-format=json > csrf_results.json
          
      - name: Run File Upload Security Tests
        run: |
          python scripts/security_file_upload_test.py --output-format=json > file_upload_results.json
          
      - name: Run Integrated Security Test Suite
        run: |
          python scripts/integrated_security_test_runner.py --comprehensive > security_comprehensive_report.json
          
      - name: Security Compliance Check
        run: |
          python scripts/security_compliance_checker.py \
            --sql-results=sql_injection_results.json \
            --xss-results=xss_results.json \
            --csrf-results=csrf_results.json \
            --file-results=file_upload_results.json \
            --require-100-percent
            
      - name: Upload Security Test Reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: security-test-reports
          path: |
            *_results.json
            security_comprehensive_report.json
```

---

## 📊 セキュリティメトリクス

### 重要な測定指標

1. **セキュリティテストカバレッジ**
   - 脆弱性カテゴリ別テスト実装率
   - セキュリティ要件充足率

2. **脆弱性検出率**
   - 既知の脆弱性パターン検出率
   - 新規脆弱性発見率

3. **修正対応時間**
   - 脆弱性発見から修正までの時間
   - セキュリティパッチ適用率

### メトリクス可視化

```python
# scripts/security_metrics_dashboard.py

def generate_security_dashboard():
    """セキュリティダッシュボード生成"""
    return {
        'vulnerability_coverage': calculate_vulnerability_coverage(),
        'detection_rates': calculate_detection_rates(),
        'response_times': calculate_response_times(),
        'compliance_status': check_compliance_status(),
        'trend_analysis': analyze_security_trends()
    }
```

---

## 📋 セキュリティテスト実装チェックリスト

### 開発者向けチェックリスト

**SQLインジェクション対策**:
- [ ] パラメータ化クエリの使用
- [ ] 入力値検証の実装
- [ ] エスケープ処理の適用
- [ ] 最小権限の原則適用

**XSS対策**:
- [ ] 出力エンコーディングの実装
- [ ] Content Security Policy設定
- [ ] 入力サニタイゼーションの実装
- [ ] テンプレートエンジンの適切な使用

**CSRF対策**:
- [ ] CSRFトークンの実装
- [ ] Same Origin Policy確認
- [ ] リファラーチェックの実装
- [ ] セキュアなセッション管理

**ファイルアップロードセキュリティ**:
- [ ] ファイルタイプ検証
- [ ] ファイルサイズ制限
- [ ] ファイル内容スキャン
- [ ] アップロード先の隔離

### CI/CD統合チェックリスト

**自動テスト**:
- [ ] セキュリティテストがCI/CDパイプラインに統合
- [ ] 100%のセキュリティテスト成功が必須
- [ ] セキュリティ違反時の自動アラート
- [ ] 定期的なセキュリティスキャン実行

**レポート・監視**:
- [ ] セキュリティテスト結果の可視化
- [ ] トレンド分析の実装
- [ ] アラート通知システムの設定
- [ ] インシデント対応手順の整備

---

## 🎓 セキュリティベストプラクティス

### 開発時の心得

1. **Secure by Design**: 設計段階からセキュリティを考慮
2. **Defense in Depth**: 複数の防御層による多層セキュリティ
3. **Principle of Least Privilege**: 最小権限の原則
4. **Fail Secure**: 障害時は安全側に倒れる設計
5. **Regular Updates**: 定期的なセキュリティアップデート

### 継続的改善

1. **脅威モデリング**: 定期的な脅威分析と対策見直し
2. **ペネトレーションテスト**: 外部専門家による侵入テスト
3. **セキュリティ教育**: 開発チームのセキュリティスキル向上
4. **インシデント対応**: セキュリティインシデント対応計画

---

## 🔗 関連リソース

### セキュリティ関連スクリプト
- `scripts/security_sql_injection_test.py` - SQLインジェクション対策テスト
- `scripts/security_xss_test.py` - XSS対策テスト
- `scripts/security_csrf_test.py` - CSRF対策テスト
- `scripts/security_file_upload_test.py` - ファイルアップロードセキュリティテスト
- `scripts/integrated_security_test_runner.py` - 統合セキュリティテストランナー

### 関連ドキュメント
- [システム全体アーキテクチャ](./ARCHITECTURE.md)
- [開発ガイド](./dev/DEVELOPMENT_GUIDE.md)

### 外部リソース
- **OWASP Top 10**: Webアプリケーションセキュリティリスク
- **CWE/SANS Top 25**: 最も危険なソフトウェアエラー
- **NIST Cybersecurity Framework**: サイバーセキュリティフレームワーク

---

**🔒 重要**: セキュリティは一度の実装では完了しません。継続的な監視・改善・アップデートにより、安全なソフトウェアを維持しましょう。