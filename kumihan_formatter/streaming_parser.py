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


class StreamingParser:
    """
    JSONストリームを解析し、特定のJSONパスに一致する値を抽出するクラス。
    """

    def __init__(
        self,
        json_path: str,
        *,
        max_depth: int = 10,
        debug: bool = False,
        use_list_parser: bool = True,
    ) -> None:
        """
        StreamingParserの新しいインスタンスを初期化します。

        Args:
            json_path (str): 抽出するJSONパス。
            max_depth (int, optional): 解析するJSONの最大深度。デフォルトは10。
            debug (bool, optional): デバッグモードを有効にするかどうか。デフォルトはFalse。
            use_list_parser (bool, optional): ListParserを使用するかどうか。デフォルトはTrue。
        """
        self.json_path = json_path
        self.max_depth = max_depth
        self.debug = debug
        self.use_list_parser = use_list_parser
        self.current_path: List[Union[str, int]] = []
        self.results: List[Any] = []
        self.buffer = ""
        self.brace_count = 0
        self.in_string = False
        self.string_start = 0
        self.string_quote = ""
        self.list_level = 0
        self.list_start = -1
        self.list_end = -1
        self.list_buffer = ""
        self.escaped = False

    def reset(self) -> None:
        """
        パーサーの状態をリセットします。
        """
        self.current_path = []
        self.results = []
        self.buffer = ""
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

    def _handle_object_start(self, char: str, index: int) -> None:
        """
        オブジェクトの開始を処理します。

        Args:
            char (str): 現在の文字。
            index (int): 現在のインデックス。
        """
        self._debug_print(f"Object start at {index}, buffer: {self.buffer}")
        self.brace_count += 1
        self.buffer = ""

    def _handle_object_end(self, char: str, index: int) -> None:
        """
        オブジェクトの終了を処理します。

        Args:
            char (str): 現在の文字。
            index (int): 現在のインデックス。
        """
        self._debug_print(f"Object end at {index}, buffer: {self.buffer}")
        if self.brace_count > 0:
            self.brace_count -= 1
        else:
            raise ValueError("Unmatched closing brace }")

        if self._path_matches():
            # パスの深さを考慮して、正しいオブジェクトの終了を検出
            if len(self.current_path) <= len(extract_json_path(self.json_path)):
                # バッファに値がある場合は、それも結果に追加
                if self.buffer.strip():
                    self._add_result(self.buffer.strip())
                else:
                    # 空のオブジェクトを結果に追加
                    self._add_result({})

        if self.current_path:
            self.current_path.pop()
        self.buffer = ""

    def _handle_string(self, char: str, index: int) -> None:
        """
        文字列を処理します。

        Args:
            char (str): 現在の文字。
            index (int): 現在のインデックス。
        """
        if self.in_string:
            if char == self.string_quote and not self.escaped:
                self._debug_print(f"String end at {index}")
                self.in_string = False
                self.string_quote = ""
                string_value = self.buffer[self.string_start + 1 : index]
                string_value = remove_quotes(string_value)

                if self._path_matches():
                    self._add_result(string_value)

                self.buffer = ""
            self.escaped = char == "\\" and not self.escaped
        else:
            if char in ['"', "'"]:
                self._debug_print(f"String start at {index}")
                self.in_string = True
                self.string_start = index
                self.string_quote = char
                self.escaped = False

    def _handle_colon(self, char: str, index: int) -> None:
        """
        コロンを処理します。

        Args:
            char (str): 現在の文字。
            index (int): 現在のインデックス。
        """
        if not self.in_string:
            key = self.buffer.strip()
            key = remove_quotes(key)
            self._debug_print(f"Key found: {key} at {index}")
            self.current_path.append(key)
            self.buffer = ""

    def _handle_comma(self, char: str, index: int) -> None:
        """
        カンマを処理します。

        Args:
            char (str): 現在の文字。
            index (int): 現在のインデックス。
        """
        if not self.in_string:
            if self._path_matches():
                value = self.buffer.strip()
                if value:
                    try:
                        value = eval(value)  # 数値、真偽値、nullを評価
                    except (NameError, SyntaxError):
                        pass  # 評価できない場合は文字列として扱う
                    self._add_result(value)
            self.buffer = ""

    def _handle_list_start(self, char: str, index: int) -> None:
        """
        リストの開始を処理します。

        Args:
            char (str): 現在の文字。
            index (int): 現在のインデックス。
        """
        if not self.in_string:
            if self.list_level == 0:
                self.list_start = index
            self.list_level += 1
            self._debug_print(f"List start at {index}, level: {self.list_level}")

            if self.list_level == 1 and self.use_list_parser:
                self.list_buffer = ""  # リストバッファを初期化
            self.list_buffer += char  # リストバッファに文字を追加

    def _handle_list_end(self, char: str, index: int) -> None:
        """
        リストの終了を処理します。

        Args:
            char (str): 現在の文字。
            index (int): 現在のインデックス。
        """
        if not self.in_string:
            self.list_level -= 1
            self._debug_print(f"List end at {index}, level: {self.list_level}")
            self.list_buffer += char  # リストバッファに文字を追加

            if self.list_level == 0:
                self.list_end = index
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
                self.list_buffer += char  # ネストされたリストの場合はバッファに追加

            if self.current_path and isinstance(self.current_path[-1], int):
                self.current_path.pop()

    def parse(self, chunk: str) -> List[Any]:
        """
        JSONストリームのチャンクを解析します。

        Args:
            chunk (str): 解析するJSONストリームのチャンク。

        Returns:
            List[Any]: 抽出された値のリスト。
        """
        for i, char in enumerate(chunk):
            if self.in_string:
                self._handle_string(char, i)
            elif self.list_level > 0:
                (
                    self._handle_list_end(char, i)
                    if char == "]"
                    else self._handle_list_start(char, i) if char == "[" else None
                )
                if self.use_list_parser:
                    self.list_buffer += char
            else:
                if char == "{":
                    self._handle_object_start(char, i)
                elif char == "}":
                    self._handle_object_end(char, i)
                elif char == '"' or char == "'":
                    self._handle_string(char, i)
                elif char == ":":
                    self._handle_colon(char, i)
                elif char == ",":
                    self._handle_comma(char, i)
                elif char == "[":
                    self._handle_list_start(char, i)
                elif char == "]":
                    self._handle_list_end(char, i)
                else:
                    self.buffer += char
        return self.results

    def finish(self) -> List[Any]:
        """
        解析を完了し、抽出された値のリストを返します。

        Returns:
            List[Any]: 抽出された値のリスト。
        """
        # 最後にバッファに残っているデータを処理
        if self.buffer.strip() and self._path_matches():
            try:
                value = eval(self.buffer.strip())  # 数値、真偽値、nullを評価
            except (NameError, SyntaxError):
                value = self.buffer.strip()  # 評価できない場合は文字列として扱う
            self._add_result(value)

        return self.results
