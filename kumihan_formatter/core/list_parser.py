from typing import Any, List, Tuple


class ListParser:
    """
    ListParser クラスは、リスト形式の文字列を解析し、
    ネストされたリスト構造を構築するためのクラスです。
    """

    def __init__(self) -> None:
        """
        ListParser の新しいインスタンスを初期化します。
        """
        self.stack: List[List[Any]] = [[]]
        self.current_string: str = ""

    def parse_char(self, char: str) -> None:
        """
        入力文字列の次の文字を解析します。

        Args:
            char (str): 解析する文字。
        """
        if char == "[":
            self.start_list()
        elif char == "]":
            self.end_list()
        elif char == ",":
            self.add_string()
        else:
            self.current_string += char

    def start_list(self) -> None:
        """
        新しいリストを開始します。
        """
        self.add_string()
        new_list: List[Any] = []
        self.stack[-1].append(new_list)
        self.stack.append(new_list)

    def end_list(self) -> None:
        """
        現在のリストを終了します。
        """
        self.add_string()
        if len(self.stack) > 1:
            self.stack.pop()
        else:
            raise ValueError("Unmatched closing bracket ]")

    def add_string(self) -> None:
        """
        現在の文字列を現在のリストに追加します。
        """
        if self.current_string:
            self.stack[-1].append(self.current_string.strip())
            self.current_string = ""

    def get_result(self) -> List[Any]:
        """
        解析結果のリストを返します。

        Returns:
            List[Any]: 解析結果のリスト。
        """
        if len(self.stack) > 1:
            raise ValueError("Unclosed list")
        return self.stack[0]

    def parse(self, input_string: str) -> List[Any]:
        """
        入力文字列全体を解析します。

        Args:
            input_string (str): 解析する文字列。

        Returns:
            List[Any]: 解析結果のリスト。
        """
        for char in input_string:
            self.parse_char(char)
        return self.get_result()


def parse_list_string(input_string: str) -> List[Any]:
    """
    リスト形式の文字列を解析して、ネストされたリスト構造を返します。

    Args:
        input_string (str): 解析するリスト形式の文字列。

    Returns:
        List[Any]: 解析結果のリスト。
    """
    parser = ListParser()
    return parser.parse(input_string)


def find_outermost_list(input_string: str) -> Tuple[int, int]:
    """
    文字列中の最も外側のリストの開始インデックスと終了インデックスを検索します。

    Args:
        input_string (str): 検索する文字列。

    Returns:
        Tuple[int, int]: 最も外側のリストの開始インデックスと終了インデックス。
                         リストが見つからない場合は (-1, -1) を返します。
    """
    start_index = -1
    end_index = -1
    bracket_count = 0

    for i, char in enumerate(input_string):
        if char == "[":
            if bracket_count == 0:
                start_index = i
            bracket_count += 1
        elif char == "]":
            bracket_count -= 1
            if bracket_count == 0:
                end_index = i
                break

    return start_index, end_index
