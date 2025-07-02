"""Kumihan-Formatter - テキストファイルをHTMLに自動組版するCLIツール"""

import os
import sys

# Set default encoding to UTF-8 for entire application
if sys.platform == "win32":
    # Windows specific encoding setup
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"

__version__ = "0.3.0"
