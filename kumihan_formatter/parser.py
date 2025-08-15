import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from kumihan_formatter.core.list_parser import ListParser, find_outermost_list
from kumihan_formatter.parser_utils import (
    extract_json_path,
    find_closing_brace,
    find_matching_quote,
    is_valid_json_path_character,
    remove_quotes,
)


class JsonParser:
    """
    JSON文字列から特定のパスの値を取得するパーサークラス。
    """

    def __init__(
        self,
        json_string: str,
        json_path: str,
        *,
        max_depth: int = 10,
        debug: bool = False,
        use_list_parser: bool = True,
    ) -> None:
        """
        JsonParserの新しいインスタンスを初期化します。

        Args:
            json_string (str): 解析するJSON文字列。
            json_path (str): 抽出するJSONパス。
            max_depth (int, optional): 解析するJSONの最大深度。デフォルトは10。
            debug (bool, optional): デバッグモードを有効にするかどうか。デフォルトはFalse。
            use_list_parser (bool, optional): ListParserを使用するかどうか。デフォルトはTrue。
        """
        self.json_string = json_string
        self.json_path = json_path
        self.max_depth = max_depth
        self.debug = debug
        self.use_list_parser = use_list_parser
        self.current_path: List[Union[str, int]] = []
        self.results: List[Any] = []
        self.index = 0
        self.brace_count = 0
        self.in_string = False
        self.string_start = 0
        self.string_quote = ""
        self.list_level = 0
        self.list_start = -1
        self.list_end = -1
        self.list_buffer = ""
        self.escaped = False

    def _debug_print(self, *args: Any) -> None:
        """
        デバッグモードが有効な場合に、デバッグ情報を出力します。

        Args:
            *args (Any): 出力するデバッグ情報。
        """
        if self.debug:
            print(*args)

    def _normalize_index(self, index: str) -> Union[str, int]:
        """
        インデックスを整数または文字列に正規化します。

        Args:
            index (str): 正規化するインデックス。

        Returns:
            Union[str, int]: 正規化されたインデックス。
        """
        try:
            return int(index)
        except ValueError:
            return index

    def _path_matches(self) -> bool:
        """
        現在のパスがJSONパスと一致するかどうかを確認します。

        Returns:
            bool: パスが一致する場合はTrue、そうでない場合はFalse。
        """
        expected_path = [
            self._normalize_index(part) for part in extract_json_path(self.json_path)
        ]
        return self.current_path == expected_path

    def _add_result(self, value: Any) -> None:
        """
        結果リストに値を追加します。

        Args:
            value (Any): 追加する値。
        """
        self.results.append(value)

    def parse(self) -> List[Any]:
        """
        JSON文字列を解析して、指定されたJSONパスに一致する値を抽出します。

        Returns:
            List[Any]: 抽出された値のリスト。
        """
        while self.index < len(self.json_string):
            char = self.json_string[self.index]

            if self.in_string:
                self._handle_string(char)
            elif self.list_level > 0:
                self._handle_list(char)
            else:
                if char == "{":
                    self._handle_object_start()
                elif char == "}":
                    self._handle_object_end()
                elif char == '"' or char == "'":
                    self._handle_string(char)
                elif char == ":":
                    self._handle_colon()
                elif char == ",":
                    self._handle_comma()
                elif char == "[":
                    self._handle_list_start()
                elif char == "]":
                    self._handle_list_end()

            self.index += 1

        return self.results

    def _handle_object_start(self) -> None:
        """
        オブジェクトの開始を処理します。
        """
        self._debug_print(f"Object start at {self.index}")
        self.brace_count += 1

    def _handle_object_end(self) -> None:
        """
        オブジェクトの終了を処理します。
        """
        self._debug_print(f"Object end at {self.index}")
        if self.brace_count > 0:
            self.brace_count -= 1
        else:
            raise ValueError("Unmatched closing brace }")

        if self.current_path:
            self.current_path.pop()

    def _handle_string(self, char: str) -> None:
        """
        文字列を処理します。

        Args:
            char (str): 現在の文字。
        """
        if not self.in_string:
            self._debug_print(f"String start at {self.index}")
            self.in_string = True
            self.string_start = self.index
            self.string_quote = char
            self.escaped = False
        else:
            if char == self.string_quote and not self.escaped:
                self._debug_print(f"String end at {self.index}")
                self.in_string = False
                string_value = self.json_string[self.string_start + 1 : self.index]
                string_value = remove_quotes(string_value)

                if self._path_matches():
                    self._add_result(string_value)
            self.escaped = char == "\\" and not self.escaped

    def _handle_colon(self) -> None:
        """
        コロンを処理します。
        """
        key_start = self.string_start + 1
        key_end = self.index - 1
        key = self.json_string[key_start:key_end]
        key = remove_quotes(key)
        self._debug_print(f"Key found: {key} at {self.index}")
        self.current_path.append(key)

    def _handle_comma(self) -> None:
        """
        カンマを処理します。
        """
        if self._path_matches():
            # カンマの前の値を取得
            value_start = self.string_start + 1
            value_end = self.index - 1
            value = self.json_string[value_start:value_end]
            value = remove_quotes(value)
            try:
                value = eval(value)  # 数値、真偽値、nullを評価
            except (NameError, SyntaxError):
                pass  # 評価できない場合は文字列として扱う
            self._add_result(value)

    def _handle_list_start(self) -> None:
        """
        リストの開始を処理します。
        """
        if self.list_level == 0:
            self.list_start = self.index
        self.list_level += 1
        self._debug_print(f"List start at {self.index}, level: {self.list_level}")

        if self.list_level == 1 and self.use_list_parser:
            self.list_buffer = ""  # リストバッファを初期化
        self.list_buffer += "["  # リストバッファに文字を追加

    def _handle_list_end(self) -> None:
        """
        リストの終了を処理します。
        """
        self.list_level -= 1
        self._debug_print(f"List end at {self.index}, level: {self.list_level}")
        self.list_buffer += "]"  # リストバッファに文字を追加

        if self.list_level == 0:
            self.list_end = self.index
            self._debug_print(
                f"Parsing list: {self.list_buffer}, start: {self.list_start}, end: {self.list_end}"
            )

            if self._path_matches():
                try:
                    # ListParserを使用してリストを解析
                    parser = ListParser()
                    parsed_list = parser.parse(self.list_buffer)
                    self._add_result(parsed_list)
                except Exception as e:
                    print(f"Error parsing list: {e}")
                    self._add_result(self.list_buffer)  # エラー時は文字列として追加

            self.list_buffer = ""  # リストバッファをクリア

        elif self.list_level > 0 and self.use_list_parser:
            self.list_buffer += "]"  # ネストされたリストの場合はバッファに追加

        if self.current_path and isinstance(self.current_path[-1], int):
            self.current_path.pop()

    def _handle_list(self, char: str) -> None:
        """
        リスト内の文字を処理します。

        Args:
            char (str): 現在の文字。
        """
        if char == "]":
            self._handle_list_end()
        elif char == "[":
            self._handle_list_start()

        if self.use_list_parser:
            self.list_buffer += char
