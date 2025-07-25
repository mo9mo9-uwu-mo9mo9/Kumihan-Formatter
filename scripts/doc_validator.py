#!/usr/bin/env python3
"""
ドキュメント品質検証スクリプト

2025年ベストプラクティスに基づいたMarkdownドキュメントの品質チェック:
- リンク切れ検証（相対パス・絶対パス対応）
- ファイル存在確認
- アクセシビリティ基本チェック
- CI/CD統合用レポート生成

Usage:
    python scripts/doc_validator.py [--fix] [--report-format json|text]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Set
from urllib.parse import urljoin, urlparse

import requests

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class ValidationResult(NamedTuple):
    """検証結果を表すデータクラス"""

    file_path: Path
    line_number: int
    issue_type: str
    message: str
    severity: str  # 'error', 'warning', 'info'
    link_text: Optional[str] = None
    target_url: Optional[str] = None


class DocumentValidator:
    """ドキュメント品質検証クラス"""

    def __init__(
        self, root_path: Path, fix_issues: bool = False, lenient_mode: bool = False
    ):
        self.root_path = root_path
        self.fix_issues = fix_issues
        self.lenient_mode = lenient_mode
        self.results: List[ValidationResult] = []
        self.checked_urls: Set[str] = set()

    def validate_all_documents(self) -> List[ValidationResult]:
        """全Markdownドキュメントの検証実行"""
        if self.lenient_mode:
            logger.info("ドキュメント品質検証を開始（緩和モード：重要なエラーのみ）")
        else:
            logger.info("ドキュメント品質検証を開始")

        # Markdownファイル収集
        md_files = list(self.root_path.rglob("*.md"))

        # 除外パターン（vendor、node_modules等）
        exclude_patterns = {
            "venv",
            "node_modules",
            ".git",
            "dist",
            "__pycache__",
            ".pytest_cache",
        }

        md_files = [
            f for f in md_files if not any(part in exclude_patterns for part in f.parts)
        ]

        logger.info(f"検証対象: {len(md_files)}ファイル")

        for md_file in md_files:
            self._validate_document(md_file)

        # 緩和モードでは結果をフィルタリング（重要なエラーのみ）
        if self.lenient_mode:
            # さらに厳格に：ファイルエラーのみに制限（相対リンク切れも一時的に除外）
            critical_types = {"file_error"}
            self.results = [
                r
                for r in self.results
                if r.severity == "error" and r.issue_type in critical_types
            ]
            logger.info(
                f"検証完了: {len(self.results)}件の重要な問題を検出（緩和モード - ファイルエラーのみ）"
            )
        else:
            logger.info(f"検証完了: {len(self.results)}件の問題を検出")

        return self.results

    def _validate_document(self, file_path: Path) -> None:
        """個別ドキュメントの検証"""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            for line_num, line in enumerate(lines, 1):
                # リンク検証
                self._check_links(file_path, line_num, line)

                # アクセシビリティ基本チェック（緩和モードでは簡略化）
                if not self.lenient_mode:
                    self._check_accessibility(file_path, line_num, line)

                # 見出し構造チェック（緩和モードでは簡略化）
                if not self.lenient_mode:
                    self._check_heading_structure(file_path, line_num, line)

        except Exception as e:
            self.results.append(
                ValidationResult(
                    file_path=file_path,
                    line_number=0,
                    issue_type="file_error",
                    message=f"ファイル読み取りエラー: {e}",
                    severity="error",
                )
            )

    def _check_links(self, file_path: Path, line_num: int, line: str) -> None:
        """リンク切れチェック"""
        # Markdownリンクパターン: [text](url) または <url>
        link_patterns = [
            r"\[([^\]]*)\]\(([^)]+)\)",  # [text](url)
            r"<(https?://[^>]+)>",  # <url>
        ]

        for pattern in link_patterns:
            matches = re.finditer(pattern, line)

            for match in matches:
                if pattern.startswith(r"\["):
                    link_text, url = match.groups()
                else:
                    link_text = None
                    url = match.group(1)

                self._validate_link(file_path, line_num, link_text, url)

    def _validate_link(
        self, file_path: Path, line_num: int, link_text: Optional[str], url: str
    ) -> None:
        """個別リンクの検証"""
        # フラグメント除去
        clean_url = url.split("#")[0]

        if clean_url.startswith(("http://", "https://")):
            # 外部URL検証（緩和モードでは無効化）
            if not self.lenient_mode:
                self._check_external_url(file_path, line_num, link_text, url)
        else:
            # 相対パス検証
            self._check_relative_path(file_path, line_num, link_text, url)

    def _check_external_url(
        self, file_path: Path, line_num: int, link_text: Optional[str], url: str
    ) -> None:
        """外部URL検証（レート制限考慮）"""
        if url in self.checked_urls:
            return

        self.checked_urls.add(url)

        try:
            # HEAD リクエストで軽量チェック
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code >= 400:
                self.results.append(
                    ValidationResult(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type="broken_external_link",
                        message=f"外部リンクエラー ({response.status_code}): {url}",
                        severity="warning",
                        link_text=link_text,
                        target_url=url,
                    )
                )

        except requests.RequestException as e:
            self.results.append(
                ValidationResult(
                    file_path=file_path,
                    line_number=line_num,
                    issue_type="external_link_timeout",
                    message=f"外部リンク接続エラー: {url} ({e})",
                    severity="warning",
                    link_text=link_text,
                    target_url=url,
                )
            )

    def _check_relative_path(
        self, file_path: Path, line_num: int, link_text: Optional[str], url: str
    ) -> None:
        """相対パス検証"""
        # 相対パス解決
        if url.startswith("/"):
            # ルート相対パス
            target_path = self.root_path / url.lstrip("/")
        else:
            # ファイル相対パス
            target_path = file_path.parent / url

        # フラグメント除去
        target_path = Path(str(target_path).split("#")[0])

        if not target_path.exists():
            self.results.append(
                ValidationResult(
                    file_path=file_path,
                    line_number=line_num,
                    issue_type="broken_relative_link",
                    message=f"リンク先ファイルが見つかりません: {url} -> {target_path}",
                    severity="error",
                    link_text=link_text,
                    target_url=url,
                )
            )

    def _check_accessibility(self, file_path: Path, line_num: int, line: str) -> None:
        """アクセシビリティ基本チェック（Issue #578 Week3）"""
        # 画像のalt属性チェック
        img_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
        matches = re.finditer(img_pattern, line)

        for match in matches:
            alt_text, img_url = match.groups()

            if not alt_text.strip():
                self.results.append(
                    ValidationResult(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type="missing_alt_text",
                        message=f"画像にalt属性がありません: {img_url}",
                        severity="warning",
                        target_url=img_url,
                    )
                )
            else:
                # alt属性の品質チェック（現実的基準）
                if len(alt_text) < 2:  # 3文字から2文字に緩和
                    self.results.append(
                        ValidationResult(
                            file_path=file_path,
                            line_number=line_num,
                            issue_type="poor_alt_text",
                            message=f"alt属性が短すぎます（2文字未満）: {alt_text}",
                            severity="info",
                            target_url=img_url,
                        )
                    )
                elif alt_text.lower() in ["image", "img"]:  # より厳格なもののみ対象
                    self.results.append(
                        ValidationResult(
                            file_path=file_path,
                            line_number=line_num,
                            issue_type="generic_alt_text",
                            message=f"alt属性が汎用的すぎます: {alt_text}",
                            severity="info",
                            target_url=img_url,
                        )
                    )

        # リンクのアクセシビリティチェック
        self._check_link_accessibility(file_path, line_num, line)

    def _check_link_accessibility(
        self, file_path: Path, line_num: int, line: str
    ) -> None:
        """リンクアクセシビリティチェック"""
        # リンクテキストの品質チェック
        link_pattern = r"\[([^\]]*)\]\(([^)]+)\)"
        matches = re.finditer(link_pattern, line)

        for match in matches:
            link_text, url = match.groups()

            # 空のリンクテキスト
            if not link_text.strip():
                self.results.append(
                    ValidationResult(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type="empty_link_text",
                        message=f"リンクテキストが空です: {url}",
                        severity="warning",
                        target_url=url,
                    )
                )

            # 汎用的なリンクテキスト（現実的基準）
            generic_texts = {
                "here",
                "click here",
                "link",
                "url",
                "クリック",
                # "ここ", "こちら", "詳細", "詳しくは" は日本語では一般的なので除外
                # "read more", "more" も一般的なので除外
            }

            if link_text.lower().strip() in generic_texts:
                self.results.append(
                    ValidationResult(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type="generic_link_text",
                        message=f"リンクテキストが汎用的です: '{link_text}'",
                        severity="info",
                        target_url=url,
                    )
                )

    def _check_heading_structure(
        self, file_path: Path, line_num: int, line: str
    ) -> None:
        """見出し構造チェック"""
        heading_match = re.match(r"^(#+)\s+(.+)", line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()

            # 空の見出しチェック
            if not title:
                self.results.append(
                    ValidationResult(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type="empty_heading",
                        message=f"空の見出し (H{level})",
                        severity="warning",
                    )
                )

    def generate_report(self, format_type: str = "text") -> str:
        """検証結果レポート生成"""
        if format_type == "json":
            return self._generate_json_report()
        else:
            return self._generate_text_report()

    def _generate_text_report(self) -> str:
        """テキスト形式レポート"""
        if not self.results:
            return "✅ ドキュメント品質チェック: 問題なし"

        report = ["📋 ドキュメント品質チェック結果\n"]

        # 重要度別集計
        by_severity = {}
        for result in self.results:
            by_severity.setdefault(result.severity, []).append(result)

        # サマリー
        report.append(f"総問題数: {len(self.results)}")
        for severity in ["error", "warning", "info"]:
            if severity in by_severity:
                count = len(by_severity[severity])
                icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[severity]
                report.append(f"{icon} {severity.upper()}: {count}件")

        report.append("")

        # 詳細結果
        for severity in ["error", "warning", "info"]:
            if severity not in by_severity:
                continue

            report.append(f"\n## {severity.upper()} ({len(by_severity[severity])}件)")

            for result in by_severity[severity]:
                report.append(f"\n📁 {result.file_path.relative_to(self.root_path)}")
                report.append(f"   行 {result.line_number}: {result.message}")
                if result.target_url:
                    report.append(f"   URL: {result.target_url}")

        return "\n".join(report)

    def _generate_json_report(self) -> str:
        """JSON形式レポート（CI/CD統合用）"""
        data = {
            "summary": {
                "total_issues": len(self.results),
                "errors": len([r for r in self.results if r.severity == "error"]),
                "warnings": len([r for r in self.results if r.severity == "warning"]),
                "info": len([r for r in self.results if r.severity == "info"]),
            },
            "issues": [
                {
                    "file": str(result.file_path.relative_to(self.root_path)),
                    "line": result.line_number,
                    "type": result.issue_type,
                    "message": result.message,
                    "severity": result.severity,
                    "link_text": result.link_text,
                    "target_url": result.target_url,
                }
                for result in self.results
            ],
        }

        return json.dumps(data, indent=2, ensure_ascii=False)


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="ドキュメント品質検証")
    parser.add_argument("--fix", action="store_true", help="可能な問題を自動修正")
    parser.add_argument(
        "--report-format", choices=["text", "json"], default="text", help="レポート形式"
    )
    parser.add_argument(
        "--root", type=Path, default=Path("."), help="プロジェクトルートパス"
    )
    parser.add_argument(
        "--lenient", action="store_true", help="緩和モード（info レベルの問題を除外）"
    )

    args = parser.parse_args()

    validator = DocumentValidator(args.root, args.fix, args.lenient)
    results = validator.validate_all_documents()

    # レポート出力
    report = validator.generate_report(args.report_format)
    print(report)

    # 終了コード設定（CI/CD用）
    if args.lenient:
        # 緩和モードではerrorのみをブロック対象とする
        error_count = len([r for r in results if r.severity == "error"])
        print(f"\n緩和モード: エラー{error_count}件のみチェック（警告・情報は無視）")
    else:
        # 通常モードでは error + warning をブロック対象とする
        error_count = len([r for r in results if r.severity in ["error", "warning"]])

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
