import time
import random
from typing import List, Tuple
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataGenerator:
    """
    時系列データを生成するクラス。
    """

    def __init__(self, num_series: int = 1, data_points: int = 100) -> None:
        """
        DataGeneratorのコンストラクタ。

        Args:
            num_series (int): 生成する時系列データの数。
            data_points (int): 各時系列データのデータポイント数。
        """
        self.num_series = num_series
        self.data_points = data_points
        self.data: pd.DataFrame = self._generate_data()

    def _generate_data(self) -> pd.DataFrame:
        """
        ランダムな時系列データを生成する。

        Returns:
            pd.DataFrame: 生成された時系列データ。
        """
        try:
            data = {}
            for i in range(self.num_series):
                data[f'series_{i+1}'] = np.random.randn(self.data_points).cumsum()
            df = pd.DataFrame(data)
            return df
        except Exception as e:
            logger.error(f"データ生成中にエラーが発生しました: {e}")
            raise

    def get_data(self) -> pd.DataFrame:
        """
        生成された時系列データを取得する。

        Returns:
            pd.DataFrame: 時系列データ。
        """
        return self.data

    def update_data(self, new_points: int = 10) -> None:
        """
        既存のデータに新しいデータポイントを追加する。

        Args:
            new_points (int): 追加するデータポイント数。
        """
        try:
            new_data = {}
            for i in range(self.num_series):
                new_data[f'series_{i+1}'] = np.random.randn(new_points).cumsum() + self.data[f'series_{i+1}'].iloc[-1]
            new_df = pd.DataFrame(new_data, index=range(len(self.data), len(self.data) + new_points))
            self.data = pd.concat([self.data, new_df])
        except Exception as e:
            logger.error(f"データ更新中にエラーが発生しました: {e}")
            raise

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    generator = DataGenerator(num_series=3, data_points=50)
    print(generator.get_data().head())
    generator.update_data(new_points=20)
    print(generator.get_data().tail())
