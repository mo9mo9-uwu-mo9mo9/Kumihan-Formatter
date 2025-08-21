import logging
import os

# ロギング設定
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)

# データ生成設定 (例)
NUM_SERIES = 3
DATA_POINTS = 100
UPDATE_INTERVAL = 2  # 秒
