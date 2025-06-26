"""パーサーのテスト"""

import pytest
from kumihan_formatter.parser import parse, Node


def test_parse_empty():
    """空文字列のパース"""
    assert parse("") == []


def test_parse_paragraph():
    """段落のパース"""
    text = """これは最初の段落です。
段落内の改行も保持されます。

これは2つ目の段落です。"""
    
    result = parse(text)
    assert len(result) == 2
    assert result[0].type == "p"
    assert result[1].type == "p"


def test_parse_list():
    """リストのパース"""
    text = """- 項目1
- 項目2
- 項目3"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "ul"
    assert len(result[0].content) == 3
    assert all(item.type == "li" for item in result[0].content)


def test_parse_nakaguro_list():
    """中黒リストのパース"""
    text = """・項目1
・項目2
・項目3"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "ul"
    assert len(result[0].content) == 3
    assert all(item.type == "li" for item in result[0].content)
    assert result[0].content[0].content == "項目1"
    assert result[0].content[1].content == "項目2"
    assert result[0].content[2].content == "項目3"


def test_parse_mixed_list_types():
    """ハイフンと中黒リストの混在"""
    text = """- ハイフン項目1
・中黒項目1
- ハイフン項目2
・中黒項目2"""
    
    result = parse(text)
    # 現在の実装では、混在しても1つのリストとして認識される
    assert len(result) == 1
    assert result[0].type == "ul"
    assert len(result[0].content) == 4
    assert result[0].content[0].content == "ハイフン項目1"
    assert result[0].content[1].content == "中黒項目1"
    assert result[0].content[2].content == "ハイフン項目2"
    assert result[0].content[3].content == "中黒項目2"


def test_parse_nakaguro_list_with_keywords():
    """中黒リストのキーワード付き"""
    text = """・;;;太字;;; 太字の項目
・;;;枠線;;; 枠線付きの項目
・;;;太字+ハイライト color=#f0fff0;;; 複合マーカーの項目"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "ul"
    assert len(result[0].content) == 3
    # 各項目の内容をチェック
    item1 = result[0].content[0]
    assert item1.type == "li"
    assert "strong" in str(item1.content)
    
    item2 = result[0].content[1]
    assert item2.type == "li"
    assert "box" in str(item2.content)
    
    item3 = result[0].content[2]
    assert item3.type == "li"
    assert "highlight" in str(item3.content)


def test_parse_single_block_marker():
    """単一ブロックマーカーのパース"""
    text = """;;;太字
これは太字のテキストです。
;;;

;;;枠線
枠線で囲まれたテキスト
;;;"""
    
    result = parse(text)
    assert len(result) == 2
    assert result[0].type == "strong"
    assert result[1].type == "div"
    assert result[1].attributes["class"] == "box"


def test_parse_compound_block_marker():
    """複合ブロックマーカーのパース"""
    text = """;;;見出し2+太字
こんにちは
;;;"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "h2"
    # ネストされた構造を確認
    assert len(result[0].content) == 1
    assert result[0].content[0].type == "strong"




def test_parse_error_unknown_keyword():
    """未知のキーワードのエラー処理"""
    text = """;;;不明なキーワード
テキスト
;;;"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "error"
    assert "未知のキーワード" in result[0].attributes["message"]


def test_parse_error_missing_closing_marker():
    """閉じマーカー不足のエラー処理"""
    text = """;;;太字
閉じマーカーなし"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "error"
    assert "閉じマーカー ';;;' が見つかりません" in result[0].attributes["message"]


def test_parse_error_unknown_keyword_with_suggestions():
    """未知のキーワードで候補提案のテスト"""
    text = """;;;太文字
テキスト
;;;"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "error"
    assert "未知のキーワード: 太文字" in result[0].attributes["message"]
    assert "候補: 太字" in result[0].attributes["message"]


def test_parse_error_compound_unknown_keyword_with_suggestions():
    """複合キーワードで未知キーワードの候補提案テスト"""
    text = """;;;見出し1+太文字
テキスト
;;;"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "error"
    assert "未知のキーワード" in result[0].attributes["message"]
    assert "太文字" in result[0].attributes["message"]
    assert "候補: 太字" in result[0].attributes["message"]


def test_parse_error_detailed_closing_marker_message():
    """閉じマーカー不足の詳細エラーメッセージテスト"""
    text = """;;;見出し2+太字
閉じマーカーなし"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "error"
    assert "閉じマーカー ';;;' が見つかりません" in result[0].attributes["message"]


def test_parse_comments_ignored():
    """コメント行が無視されることのテスト"""
    text = """# これはコメントです
# ============================================
# コメント行のテスト
# ============================================

通常の段落です。

# 段落の間のコメント

;;;太字
太字のテスト
;;;

# 最後のコメント"""
    
    result = parse(text)
    # コメント行は無視され、段落と太字ブロックのみが残る
    assert len(result) == 2
    assert result[0].type == "p"
    assert result[0].content == ["通常の段落です。"]
    assert result[1].type == "strong"
    assert result[1].content == ["太字のテスト"]


def test_parse_comments_with_spaces():
    """スペース付きコメント行のテスト"""
    text = """   # 先頭にスペースがあるコメント
	# タブ付きコメント
#スペースなしコメント

実際のコンテンツです。"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "p"
    assert result[0].content == ["実際のコンテンツです。"]


def test_parse_mixed_comments_and_content():
    """コメントとコンテンツの混在テスト"""
    text = """# ファイルヘッダー
# 作成者: テスト
# 日付: 2025-06-21

;;;見出し1
メインタイトル
;;;

# セクション1のコメント

通常の段落です。

# リストの説明
- 項目1
- 項目2

# 注意事項
;;;枠線
重要な情報
;;;

# フッター"""
    
    result = parse(text)
    # コメント行は無視され、見出し、段落、リスト、枠線のみ
    assert len(result) == 4


def test_keyword_list_single():
    """単一キーワード付きリストのテスト"""
    text = """- ;;;太字;;; 強調されたリスト項目
- ;;;枠線;;; 枠線で囲まれたリスト項目
- ;;;イタリック;;; 斜体のリスト項目"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "ul"
    assert len(result[0].content) == 3
    
    # 最初の項目：太字
    li1 = result[0].content[0]
    assert li1.type == "li"
    assert len(li1.content) == 1
    assert li1.content[0].type == "strong"
    assert li1.content[0].content == ["強調されたリスト項目"]
    
    # 2番目の項目：枠線
    li2 = result[0].content[1]
    assert li2.type == "li"
    assert len(li2.content) == 1
    assert li2.content[0].type == "div"
    assert li2.content[0].attributes["class"] == "box"
    assert li2.content[0].content == ["枠線で囲まれたリスト項目"]
    
    # 3番目の項目：イタリック
    li3 = result[0].content[2]
    assert li3.type == "li"
    assert len(li3.content) == 1
    assert li3.content[0].type == "em"
    assert li3.content[0].content == ["斜体のリスト項目"]


def test_keyword_list_compound():
    """複合キーワード付きリストのテスト"""
    text = """- ;;;太字+枠線;;; 太字かつ枠線のリスト項目
- ;;;見出し2+太字;;; 見出しかつ太字のリスト項目
- ;;;ハイライト color=#ff0+太字;;; 色付きハイライトと太字"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "ul"
    assert len(result[0].content) == 3
    
    # 最初の項目：太字+枠線
    li1 = result[0].content[0]
    assert li1.type == "li"
    assert len(li1.content) == 1
    # 外側が枠線、内側が太字
    assert li1.content[0].type == "div"
    assert li1.content[0].attributes["class"] == "box"
    assert li1.content[0].content[0].type == "strong"
    assert li1.content[0].content[0].content == ["太字かつ枠線のリスト項目"]
    
    # 2番目の項目：見出し2+太字
    li2 = result[0].content[1]
    assert li2.type == "li"
    assert len(li2.content) == 1
    # 外側が見出し、内側が太字
    assert li2.content[0].type == "h2"
    assert li2.content[0].content[0].type == "strong"
    assert li2.content[0].content[0].content == ["見出しかつ太字のリスト項目"]
    
    # 3番目の項目：ハイライト+太字（色指定）
    li3 = result[0].content[2]
    assert li3.type == "li"
    assert len(li3.content) == 1
    # 外側がハイライト、内側が太字
    assert li3.content[0].type == "div"
    assert li3.content[0].attributes["class"] == "highlight"
    assert li3.content[0].attributes.get("color") == "#ff0"
    assert li3.content[0].content[0].type == "strong"
    assert li3.content[0].content[0].content == ["色付きハイライトと太字"]


def test_keyword_list_mixed_with_normal():
    """通常のリスト項目とキーワード付きリストの混在テスト"""
    text = """- 通常のリスト項目
- ;;;太字;;; 太字のリスト項目
- また通常の項目
- ;;;枠線;;; 枠線付きの項目"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "ul"
    assert len(result[0].content) == 4
    
    # 1番目：通常の項目
    assert result[0].content[0].type == "li"
    assert result[0].content[0].content == ["通常のリスト項目"]
    
    # 2番目：太字付き
    assert result[0].content[1].type == "li"
    assert result[0].content[1].content[0].type == "strong"
    
    # 3番目：通常の項目
    assert result[0].content[2].type == "li"
    assert result[0].content[2].content == ["また通常の項目"]
    
    # 4番目：枠線付き
    assert result[0].content[3].type == "li"
    assert result[0].content[3].content[0].type == "div"


def test_keyword_list_invalid_keyword():
    """無効なキーワード付きリストのテスト"""
    text = """- ;;;存在しないキーワード;;; テキスト
- ;;;太字+存在しない;;; 複合で一部無効"""
    
    result = parse(text)
    assert len(result) == 1
    assert result[0].type == "ul"
    assert len(result[0].content) == 2
    
    # 最初の項目：エラー
    li1 = result[0].content[0]
    assert li1.type == "li"
    assert li1.content[0].type == "error"
    assert "未知のキーワード" in li1.content[0].attributes["message"]
    
    # 2番目の項目：エラー（複合キーワードの一部が無効）
    li2 = result[0].content[1]
    assert li2.type == "li"
    assert li2.content[0].type == "error"
    assert "未知のキーワード" in li2.content[0].attributes["message"]


def test_numbered_list_basic():
    """基本的な番号付きリストのテスト"""
    text = """1. 項目1
2. 項目2
3. 項目3"""
    
    ast = parse(text)
    
    assert len(ast) == 1
    assert ast[0].type == "ol"
    assert len(ast[0].content) == 3
    
    # 各項目をチェック
    for i, item in enumerate(ast[0].content, 1):
        assert item.type == "li"
        assert len(item.content) == 1
        assert item.content[0] == f"項目{i}"


def test_numbered_list_mixed_with_bullet():
    """番号付きリストと箇条書きリストの混在テスト"""
    text = """- 箇条書き項目1
- 箇条書き項目2

1. 番号付き項目1
2. 番号付き項目2"""
    
    ast = parse(text)
    
    assert len(ast) == 2
    
    # 最初は箇条書きリスト
    assert ast[0].type == "ul"
    assert len(ast[0].content) == 2
    
    # 次は番号付きリスト
    assert ast[1].type == "ol"
    assert len(ast[1].content) == 2


def test_numbered_list_in_block():
    """ブロック内の番号付きリストのテスト"""
    text = """;;;枠線
1. ブロック内項目1
2. ブロック内項目2
;;;"""
    
    ast = parse(text)
    
    assert len(ast) == 1
    assert ast[0].type == "div"
    assert ast[0].attributes["class"] == "box"
    assert ast[0].attributes["contains_list"] == True


def test_numbered_list_with_space_indents():
    """スペースインデント付き番号付きリストのテスト"""
    text = """  1. インデント項目1
  2. インデント項目2
   3. 異なるインデント項目3"""
    
    ast = parse(text)
    
    assert len(ast) == 1
    assert ast[0].type == "ol"
    assert len(ast[0].content) == 3
    
    assert ast[0].content[0].content[0] == "インデント項目1"
    assert ast[0].content[1].content[0] == "インデント項目2"
    assert ast[0].content[2].content[0] == "異なるインデント項目3"


def test_escape_format_symbols():
    """フォーマット記号のエスケープテスト"""
    text = """###で始まる行は;;;に変換されます

通常の;;;は記号として扱われます

###太字

この行は ;;; 太字と表示されます"""
    
    result = parse(text)
    assert len(result) == 4
    
    # 最初の段落: エスケープされた ;;;
    assert result[0].type == "p"
    assert result[0].content[0] == ";;;で始まる行は;;;に変換されます"
    
    # 2番目の段落: 通常のテキスト内の ;;;
    assert result[1].type == "p"
    assert result[1].content[0] == "通常の;;;は記号として扱われます"
    
    # 3番目の段落: エスケープされた ;;;太字
    assert result[2].type == "p"
    assert result[2].content[0] == ";;;太字"
    
    # 4番目の段落: 通常のテキスト
    assert result[3].type == "p"
    assert result[3].content[0] == "この行は ;;; 太字と表示されます"