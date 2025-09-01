import io
import sys
from kumihan_formatter.ui.console_ui import ConsoleUI, get_console_ui


def _capture(fn):
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        fn()
    finally:
        sys.stdout = old
    return buf.getvalue()


def test_console_ui_basic_methods_no_error():
    ui = ConsoleUI()
    out = _capture(lambda: ui.info("情報", details="詳細"))
    assert "[INFO]" in out

    out = _capture(lambda: ui.warning("注意"))
    assert "[WARN]" in out

    out = _capture(lambda: ui.error("失敗"))
    assert "[ERROR]" in out

    out = _capture(lambda: ui.success("完了", "OK"))
    assert "[OK]" in out

    out = _capture(lambda: ui.dim("進捗"))
    assert "[..]" in out


def test_console_ui_domain_helpers():
    ui = ConsoleUI()
    out = _capture(lambda: ui.sample_generation("/tmp/out.html"))
    assert "/tmp/out.html" in out

    out = _capture(lambda: ui.sample_complete("/tmp/out.html", txt_name="a.txt", html_name="b.html", image_count=3))
    assert "サンプル生成完了" in out
    assert "a.txt" in out and "b.html" in out and "3" in out


def test_get_console_ui_singleton():
    a = get_console_ui()
    b = get_console_ui()
    assert a is b

