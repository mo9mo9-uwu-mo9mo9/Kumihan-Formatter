"""
FileIOHandlerのテスト

Test coverage targets:
- ファイル読み取り: 90%
- ファイル書き込み: 85%
- エンコーディング処理: 95%
- エラーハンドリング: 90%
"""

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from kumihan_formatter.core.file_io_handler import FileIOHandler


class TestFileIOHandler:
    """FileIOHandlerクラスのテスト"""

    def test_write_text_file_success_utf8(self):
        """UTF-8でのファイル書き込み成功テスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            test_path = Path(f.name)

        content = "Test Content"

        # When
        FileIOHandler.write_text_file(test_path, content)

        # Then
        with open(test_path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content

        # Cleanup
        time.sleep(0.1)  # Windows環境でのI/O競合状態を回避
        try:
            test_path.unlink()
        except (OSError, PermissionError):
            pass  # Windows環境でファイル削除に失敗することがある

    def test_write_text_file_success_custom_encoding(self):
        """カスタムエンコーディングでのファイル書き込み成功テスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            test_path = Path(f.name)

        content = "Test content"
        encoding = "ascii"

        # When
        FileIOHandler.write_text_file(test_path, content, encoding)

        # Then
        with open(test_path, "r", encoding=encoding) as f:
            result = f.read()
        assert result == content

        # Cleanup
        time.sleep(0.1)  # Windows環境でのI/O競合状態を回避
        try:
            test_path.unlink()
        except (OSError, PermissionError):
            pass  # Windows環境でファイル削除に失敗することがある

    @patch("builtins.open")
    def test_write_text_file_unicode_encode_error_fallback(self, mock_file_open):
        """UnicodeEncodeErrorのフォールバック処理テスト"""
        # Given
        test_path = Path("test.txt")
        content = "Test Content"

        # Create a mock file that raises UnicodeEncodeError on write
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=False)
        mock_file.write.side_effect = UnicodeEncodeError("ascii", "test", 0, 1, "error")

        # Second call should succeed
        mock_file_success = mock_open().return_value
        mock_file_open.side_effect = [mock_file, mock_file_success]

        with patch("kumihan_formatter.core.file_io_handler.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # When
            FileIOHandler.write_text_file(test_path, content, "ascii")

            # Then
            assert mock_file_open.call_count == 2
            mock_log.warning.assert_called_once()

    @patch("builtins.open")
    def test_write_text_file_utf8_bom_fallback(self, mock_file_open):
        """UTF-8 BOMフォールバック処理テスト"""
        # Given
        test_path = Path("test.txt")
        content = "Test Content"

        # First call raises Exception, second (UTF-8-sig) succeeds
        mock_file_open.side_effect = [OSError("Write error"), mock_open().return_value]

        with patch("kumihan_formatter.core.file_io_handler.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # When
            FileIOHandler.write_text_file(test_path, content, "utf-8")

            # Then
            assert mock_file_open.call_count == 2
            # UTF-8-sigでの呼び出しを確認
            mock_file_open.assert_any_call(
                test_path, "w", encoding="utf-8-sig", errors="replace"
            )

    @patch("builtins.open")
    def test_write_text_file_non_utf8_exception_reraise(self, mock_file_open):
        """非UTF-8エンコーディングでの例外再発生テスト"""
        # Given
        test_path = Path("test.txt")
        content = "Test content"

        mock_file_open.side_effect = OSError("Write error")

        # When & Then
        with pytest.raises(OSError):
            FileIOHandler.write_text_file(test_path, content, "ascii")

    def test_read_text_file_success_utf8(self):
        """UTF-8でのファイル読み取り成功テスト"""
        # Given
        content = "Test Content"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            test_path = Path(f.name)

        # When
        result = FileIOHandler.read_text_file(test_path)

        # Then
        assert result == content

        # Cleanup
        time.sleep(0.1)  # Windows環境でのI/O競合状態を回避
        try:
            test_path.unlink()
        except (OSError, PermissionError):
            pass  # Windows環境でファイル削除に失敗することがある

    @patch("kumihan_formatter.core.encoding_detector.EncodingDetector.detect")
    def test_read_text_file_confident_detection_success(self, mock_detect):
        """確信度の高いエンコーディング検出での読み取り成功テスト"""
        # Given
        content = "Test content"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            test_path = Path(f.name)

        mock_detect.return_value = ("utf-8", True)

        # When
        result = FileIOHandler.read_text_file(test_path)

        # Then
        assert result == content
        mock_detect.assert_called_once_with(test_path)

        # Cleanup
        time.sleep(0.1)  # Windows環境でのI/O競合状態を回避
        try:
            test_path.unlink()
        except (OSError, PermissionError):
            pass  # Windows環境でファイル削除に失敗することがある

    @patch("kumihan_formatter.core.encoding_detector.EncodingDetector.detect")
    @patch("builtins.open")
    def test_read_text_file_detection_fallback_to_specified(
        self, mock_open_func, mock_detect
    ):
        """検出エンコーディング失敗時の指定エンコーディングフォールバックテスト"""
        # Given
        test_path = Path("test.txt")
        content = "Test content"

        mock_detect.return_value = ("shift_jis", True)

        # First open (detected encoding) fails, second (specified) succeeds
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=False)
        mock_file.read.return_value = content
        mock_open_func.side_effect = [
            UnicodeDecodeError("shift_jis", b"", 0, 1, "error"),
            mock_file,
        ]

        # When
        result = FileIOHandler.read_text_file(test_path, "utf-8")

        # Then
        assert result == content
        assert mock_open_func.call_count == 2

    @patch("kumihan_formatter.core.encoding_detector.EncodingDetector.detect")
    @patch("builtins.open")
    @patch("sys.platform", "win32")
    def test_read_text_file_platform_fallback_windows(
        self, mock_open_func, mock_detect
    ):
        """Windows環境でのプラットフォームフォールバックテスト"""
        # Given
        test_path = Path("test.txt")
        content = "Test content"

        mock_detect.return_value = ("utf-8", False)

        # First two opens fail, third (cp932) succeeds
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=False)
        mock_file.read.return_value = content
        mock_open_func.side_effect = [
            UnicodeDecodeError("utf-8", b"", 0, 1, "error"),  # detected
            UnicodeDecodeError("utf-8", b"", 0, 1, "error"),  # specified
            mock_file,  # cp932 fallback
        ]

        # When
        result = FileIOHandler.read_text_file(test_path)

        # Then
        assert result == content
        assert mock_open_func.call_count == 3
        # cp932での呼び出しを確認
        mock_open_func.assert_any_call(test_path, "r", encoding="cp932")

    @patch("kumihan_formatter.core.encoding_detector.EncodingDetector.detect")
    @patch("builtins.open")
    @patch("sys.platform", "linux")
    def test_read_text_file_platform_fallback_linux(self, mock_open_func, mock_detect):
        """Linux環境でのプラットフォームフォールバック（無し）テスト"""
        # Given
        test_path = Path("test.txt")
        content = "Test content"

        mock_detect.return_value = ("utf-8", False)

        # First two opens fail, third (error replacement) succeeds
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=False)
        mock_file.read.return_value = content
        mock_open_func.side_effect = [
            UnicodeDecodeError("utf-8", b"", 0, 1, "error"),  # detected
            mock_file,  # error replacement (always succeeds)
        ]

        # When
        result = FileIOHandler.read_text_file(test_path)

        # Then
        assert result == content
        assert mock_open_func.call_count == 2
        # エラー置換での呼び出しを確認
        mock_open_func.assert_any_call(
            test_path, "r", encoding="utf-8", errors="replace"
        )

    @patch("kumihan_formatter.core.encoding_detector.EncodingDetector.detect")
    @patch("builtins.open")
    def test_read_text_file_final_error_replacement(self, mock_open_func, mock_detect):
        """最終手段のエラー置換読み取りテスト"""
        # Given
        test_path = Path("test.txt")
        content = "Test content with �"  # 置換文字含む

        mock_detect.return_value = ("utf-8", False)

        # All attempts fail except final error replacement
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=False)
        mock_file.read.return_value = content
        mock_open_func.side_effect = [
            UnicodeDecodeError("utf-8", b"", 0, 1, "error"),  # detected
            mock_file,  # error replacement (always succeeds)
        ]

        with patch("kumihan_formatter.core.file_io_handler.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # When
            result = FileIOHandler.read_text_file(test_path)

            # Then
            assert result == content
            mock_log.warning.assert_called_once()

    def test_try_detected_encoding_confident_success(self):
        """確信度の高い検出エンコーディングでの読み取り成功テスト"""
        # Given
        content = "Test content"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            test_path = Path(f.name)

        with patch("kumihan_formatter.core.file_io_handler.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # When
            result = FileIOHandler._try_detected_encoding(
                test_path, "utf-8", True, "utf-8", mock_log
            )

            # Then
            assert result == content

        # Cleanup
        time.sleep(0.1)  # Windows環境でのI/O競合状態を回避
        try:
            test_path.unlink()
        except (OSError, PermissionError):
            pass  # Windows環境でファイル削除に失敗することがある

    def test_try_detected_encoding_not_confident_utf8_fallback(self):
        """確信度の低い検出でのUTF-8フォールバックテスト"""
        # Given
        content = "Test content"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            test_path = Path(f.name)

        with patch("kumihan_formatter.core.file_io_handler.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # When
            result = FileIOHandler._try_detected_encoding(
                test_path, "shift_jis", False, "utf-8", mock_log
            )

            # Then
            assert result == content  # UTF-8で読めるため成功

        # Cleanup
        time.sleep(0.1)  # Windows環境でのI/O競合状態を回避
        try:
            test_path.unlink()
        except (OSError, PermissionError):
            pass  # Windows環境でファイル削除に失敗することがある

    @patch("builtins.open")
    def test_try_detected_encoding_decode_error(self, mock_open_func):
        """検出エンコーディングでのデコードエラーテスト"""
        # Given
        test_path = Path("test.txt")
        mock_open_func.side_effect = UnicodeDecodeError("shift_jis", b"", 0, 1, "error")

        with patch("kumihan_formatter.core.file_io_handler.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # When
            result = FileIOHandler._try_detected_encoding(
                test_path, "shift_jis", True, "utf-8", mock_log
            )

            # Then
            assert result is None
            mock_log.debug.assert_called_once()

    def test_try_specified_encoding_different_success(self):
        """指定エンコーディングが検出と異なる場合の成功テスト"""
        # Given
        content = "Test content"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            test_path = Path(f.name)

        with patch("kumihan_formatter.core.file_io_handler.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # When
            result = FileIOHandler._try_specified_encoding(
                test_path, "utf-8", "shift_jis", mock_log
            )

            # Then
            assert result == content

        # Cleanup
        time.sleep(0.1)  # Windows環境でのI/O競合状態を回避
        try:
            test_path.unlink()
        except (OSError, PermissionError):
            pass  # Windows環境でファイル削除に失敗することがある

    def test_try_specified_encoding_same_as_detected(self):
        """指定エンコーディングが検出と同じ場合のスキップテスト"""
        # Given
        test_path = Path("test.txt")

        with patch("kumihan_formatter.core.file_io_handler.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # When
            result = FileIOHandler._try_specified_encoding(
                test_path, "utf-8", "utf-8", mock_log
            )

            # Then
            assert result is None

    @patch("builtins.open")
    def test_try_specified_encoding_decode_error(self, mock_open_func):
        """指定エンコーディングでのデコードエラーテスト"""
        # Given
        test_path = Path("test.txt")
        mock_open_func.side_effect = UnicodeDecodeError("ascii", b"", 0, 1, "error")

        with patch("kumihan_formatter.core.file_io_handler.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # When
            result = FileIOHandler._try_specified_encoding(
                test_path, "ascii", "utf-8", mock_log
            )

            # Then
            assert result is None
            mock_log.debug.assert_called_once()

    @patch("sys.platform", "win32")
    def test_try_platform_fallbacks_windows_success(self):
        """Windows環境でのプラットフォームフォールバック成功テスト"""
        # Given
        content = "Test content"
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="cp932"
            ) as f:
                f.write(content)
                test_path = Path(f.name)
        except (UnicodeEncodeError, LookupError):
            # cp932が利用できない環境ではutf-8でファイルを作成
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as f:
                f.write(content)
                test_path = Path(f.name)

        with patch("kumihan_formatter.core.file_io_handler.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # When
            result = FileIOHandler._try_platform_fallbacks(test_path, mock_log)

            # Then
            assert result == content

        # Cleanup
        time.sleep(0.1)  # Windows環境でのI/O競合状態を回避
        try:
            test_path.unlink()
        except (OSError, PermissionError):
            pass  # Windows環境でファイル削除に失敗することがある

    @patch("sys.platform", "linux")
    def test_try_platform_fallbacks_linux_no_fallbacks(self):
        """Linux環境でのプラットフォームフォールバック（無し）テスト"""
        # Given
        test_path = Path("test.txt")

        with patch("kumihan_formatter.core.file_io_handler.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # When
            result = FileIOHandler._try_platform_fallbacks(test_path, mock_log)

            # Then
            assert result is None

    def test_read_with_error_replacement_success(self):
        """エラー置換読み取りの成功テスト"""
        # Given
        content = "Test content"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            test_path = Path(f.name)

        with patch("kumihan_formatter.core.file_io_handler.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # When
            result = FileIOHandler._read_with_error_replacement(test_path, mock_log)

            # Then
            assert result == content
            mock_log.warning.assert_called_once()

        # Cleanup
        time.sleep(0.1)  # Windows環境でのI/O競合状態を回避
        try:
            test_path.unlink()
        except (OSError, PermissionError):
            pass  # Windows環境でファイル削除に失敗することがある

    def test_comprehensive_encoding_flow(self):
        """包括的なエンコーディングフローテスト"""
        # Given
        content = "Test Content"

        # UTF-8ファイルを作成
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            test_path = Path(f.name)

        # When
        result = FileIOHandler.read_text_file(test_path)

        # Then
        assert result == content

        # ファイルを書き直し
        new_content = "New Test Content"
        FileIOHandler.write_text_file(test_path, new_content)

        # 再読み込み
        result2 = FileIOHandler.read_text_file(test_path)
        assert result2 == new_content

        # Cleanup
        time.sleep(0.1)  # Windows環境でのI/O競合状態を回避
        try:
            test_path.unlink()
        except (OSError, PermissionError):
            pass  # Windows環境でファイル削除に失敗することがある
