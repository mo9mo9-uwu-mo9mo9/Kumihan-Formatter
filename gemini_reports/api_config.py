from typing import Optional

class ApiConfig:
    """API設定を保持するクラス"""

    def __init__(self, api_key: Optional[str] = None, api_url: str = "https://example.com/api") -> None:
        """
        初期化処理

        Args:
            api_key: APIキー (オプション)
            api_url: APIのURL
        """
        self.api_key = api_key
        self.api_url = api_url

    def get_api_url(self) -> str:
        """APIのURLを返す"""
        return self.api_url

    def get_api_key(self) -> Optional[str]:
        """APIキーを返す"""
        return self.api_key
