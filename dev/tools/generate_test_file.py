"""テスト用記法網羅ファイル生成機能"""

import itertools
from pathlib import Path
from typing import List, Dict, Set


class TestFileGenerator:
    """テスト用ファイル生成クラス"""
    
    # デフォルトのブロックキーワード定義（Issue #21対応でインライン記法を除外）
    BLOCK_KEYWORDS = {
        "太字": {"tag": "strong", "category": "style"},
        "イタリック": {"tag": "em", "category": "style"},
        "枠線": {"tag": "div", "class": "box", "category": "container"},
        "ハイライト": {"tag": "div", "class": "highlight", "category": "container"},
        "見出し1": {"tag": "h1", "category": "heading"},
        "見出し2": {"tag": "h2", "category": "heading"},
        "見出し3": {"tag": "h3", "category": "heading"},
        "見出し4": {"tag": "h4", "category": "heading"},
        "見出し5": {"tag": "h5", "category": "heading"},
    }
    
    # ハイライト色のサンプル
    HIGHLIGHT_COLORS = ["#ff0", "#fdd", "#dfd", "#ddf", "#ffe", "#ffcccc"]
    
    def __init__(self, max_combinations: int = 1000):
        self.max_combinations = max_combinations
        self.generated_patterns: Set[str] = set()
        self.test_case_counter = 0
    
    def generate_header(self) -> str:
        """ファイルヘッダーを生成"""
        return """# Kumihan-Formatter テスト用記法網羅ファイル (自動生成)
# すべての記法組み合わせを網羅的にテストするために使用します
# 対象記法: ブロック記法、キーワード付きリスト、混在パターン

"""
    
    def _get_test_case_name(self, category: str, description: str) -> str:
        """テストケース名を生成"""
        self.test_case_counter += 1
        return f"[TEST-{self.test_case_counter:03d}] {category}: {description}"
    
    def _is_valid_combination(self, combo: tuple) -> bool:
        """組み合わせが有効かチェック（複数見出し組み合わせを除外）"""
        heading_count = 0
        for keyword in combo:
            if self.BLOCK_KEYWORDS[keyword]["category"] == "heading":
                heading_count += 1
        
        # 複数の見出しが含まれる組み合わせは無効
        return heading_count <= 1

    def generate_single_block_patterns(self) -> List[str]:
        """単一キーワードのブロック記法パターンを生成"""
        patterns = []
        
        for keyword, info in self.BLOCK_KEYWORDS.items():
            # 基本パターン
            pattern_id = f"single_{keyword}"
            if pattern_id not in self.generated_patterns:
                test_name = self._get_test_case_name("単一ブロック", keyword)
                patterns.append(f"""# {test_name}
;;;{keyword}
{keyword}のテストコンテンツです。
この記法は{info['tag']}タグに変換されます。
;;;

""")
                self.generated_patterns.add(pattern_id)
            
            # ハイライトの色指定パターン（全色を対象に拡張）
            if keyword == "ハイライト":
                for color in self.HIGHLIGHT_COLORS:  # 全色を使用
                    pattern_id = f"single_highlight_{color}"
                    if pattern_id not in self.generated_patterns:
                        test_name = self._get_test_case_name("色指定ハイライト", f"color={color}")
                        patterns.append(f"""# {test_name}
;;;ハイライト color={color}
色指定ハイライト（{color}）のテストです。
背景色が{color}で表示されます。
;;;

""")
                        self.generated_patterns.add(pattern_id)
        
        return patterns
    
    def generate_compound_block_patterns(self) -> List[str]:
        """複合キーワードのブロック記法パターンを生成"""
        patterns = []
        keywords = list(self.BLOCK_KEYWORDS.keys())
        
        # 2つの組み合わせ（有効なパターンのみ生成）
        for combo in itertools.combinations(keywords, 2):
            if not self._is_valid_combination(combo):
                continue  # 複数見出し組み合わせをスキップ
            
            pattern_id = f"compound_{'_'.join(sorted(combo))}"
            if pattern_id not in self.generated_patterns:
                combo_str = "+".join(combo)
                test_name = self._get_test_case_name("複合ブロック(2)", combo_str)
                patterns.append(f"""# {test_name}
;;;{combo_str}
{combo[0]}と{combo[1]}を組み合わせたテストです。
ネスト構造で適用されます。
;;;

""")
                self.generated_patterns.add(pattern_id)
        
        # 3つの組み合わせ（有効なパターンのみ生成）
        for combo in itertools.combinations(keywords, 3):
            if not self._is_valid_combination(combo):
                continue  # 複数見出し組み合わせをスキップ
            
            pattern_id = f"compound_{'_'.join(sorted(combo))}"
            if pattern_id not in self.generated_patterns:
                combo_str = "+".join(combo)
                test_name = self._get_test_case_name("複合ブロック(3)", combo_str)
                patterns.append(f"""# {test_name}
;;;{combo_str}
{combo[0]}、{combo[1]}、{combo[2]}の組み合わせです。
複雑なネスト構造のテストケースです。
;;;

""")
                self.generated_patterns.add(pattern_id)
        
        # 4つの組み合わせ（有効なパターンのみ生成）
        for combo in itertools.combinations(keywords, 4):
            if not self._is_valid_combination(combo):
                continue  # 複数見出し組み合わせをスキップ
            
            pattern_id = f"compound_{'_'.join(sorted(combo))}"
            if pattern_id not in self.generated_patterns:
                combo_str = "+".join(combo)
                test_name = self._get_test_case_name("複合ブロック(4)", combo_str)
                patterns.append(f"""# {test_name}
;;;{combo_str}
{len(combo)}つのキーワードを組み合わせた複合パターンです。
{', '.join(combo)}が同時に適用されます。
;;;

""")
                self.generated_patterns.add(pattern_id)
        
        # 5つ以上の組み合わせ（有効なサンプルのみ）
        for combo_size in range(5, len(keywords) + 1):
            valid_count = 0
            for combo in itertools.combinations(keywords, combo_size):
                if not self._is_valid_combination(combo):
                    continue  # 複数見出し組み合わせをスキップ
                
                if valid_count >= 5:  # 各サイズ最大5パターンまで
                    break
                    
                pattern_id = f"compound_{'_'.join(sorted(combo))}"
                if pattern_id not in self.generated_patterns:
                    combo_str = "+".join(combo)
                    test_name = self._get_test_case_name(f"複合ブロック({combo_size})", combo_str)
                    patterns.append(f"""# {test_name}
;;;{combo_str}
{len(combo)}つのキーワードを組み合わせた最大複合パターンです。
{', '.join(combo)}が同時に適用されます。
;;;

""")
                    self.generated_patterns.add(pattern_id)
                    valid_count += 1
        
        return patterns
    
    def generate_keyword_list_patterns(self) -> List[str]:
        """キーワード付きリストパターンを生成"""
        patterns = []
        keywords = list(self.BLOCK_KEYWORDS.keys())
        
        # 単一キーワード付きリスト（全キーワード）
        test_name = self._get_test_case_name("キーワード付きリスト", "単一キーワード全パターン")
        patterns.append(f"""# {test_name}
""")
        
        for keyword in keywords:  # 全キーワードを使用
            patterns.append(f"- :{keyword}: {keyword}を適用したリスト項目です\n")
        
        patterns.append("- 通常のリスト項目（キーワードなし）\n\n")
        
        # 2つの組み合わせ（有効なパターンのみ）
        test_name = self._get_test_case_name("キーワード付きリスト", "複合キーワード(2)有効パターン")
        patterns.append(f"""# {test_name}
""")
        
        for combo in itertools.combinations(keywords, 2):
            if not self._is_valid_combination(combo):
                continue  # 複数見出し組み合わせをスキップ
            combo_str = "+".join(combo)
            patterns.append(f"- :{combo_str}: {combo_str}を適用したリスト項目です\n")
        
        patterns.append("- 通常のリスト項目\n\n")
        
        # 3つの組み合わせ（有効なパターンのみ）
        test_name = self._get_test_case_name("キーワード付きリスト", "複合キーワード(3)有効パターン")
        patterns.append(f"""# {test_name}
""")
        
        for combo in itertools.combinations(keywords, 3):
            if not self._is_valid_combination(combo):
                continue  # 複数見出し組み合わせをスキップ
            combo_str = "+".join(combo)
            patterns.append(f"- :{combo_str}: {combo_str}を適用したリスト項目です\n")
        
        patterns.append("- 通常のリスト項目\n\n")
        
        # 4つの組み合わせ（有効な代表パターン）
        test_name = self._get_test_case_name("キーワード付きリスト", "複合キーワード(4)有効パターン")
        patterns.append(f"""# {test_name}
""")
        
        valid_count = 0
        for combo in itertools.combinations(keywords, 4):
            if not self._is_valid_combination(combo):
                continue  # 複数見出し組み合わせをスキップ
            if valid_count >= 20:  # 最初の20パターンのみ
                break
            combo_str = "+".join(combo)
            patterns.append(f"- :{combo_str}: {combo_str}を適用したリスト項目です\n")
            valid_count += 1
        
        patterns.append("- 通常のリスト項目\n\n")
        
        # 色指定付きリスト（全色）
        test_name = self._get_test_case_name("キーワード付きリスト", "色指定全パターン")
        patterns.append(f"""# {test_name}
""")
        
        for color in self.HIGHLIGHT_COLORS:  # 全色を使用
            patterns.append(f"- :ハイライト color={color}: 色指定（{color}）付きリスト項目\n")
        
        # 色指定+複合キーワード
        for color in self.HIGHLIGHT_COLORS[:3]:  # 最初の3色
            for combo in [("ハイライト", "太字"), ("ハイライト", "枠線"), ("ハイライト", "イタリック")]:
                combo_str = "+".join(combo)
                patterns.append(f"- :{combo_str} color={color}: {combo_str}+色指定（{color}）項目\n")
        
        patterns.append("\n")
        
        return patterns
    
    def generate_numbered_list_patterns(self) -> List[str]:
        """番号付きリストパターンを生成"""
        patterns = []
        
        # 基本的な番号付きリスト
        test_name = self._get_test_case_name("番号付きリスト", "基本パターン")
        patterns.append(f"""# {test_name}
1. 最初の番号付き項目
2. 2番目の番号付き項目
3. 3番目の番号付き項目
4. 4番目の番号付き項目
5. 5番目の番号付き項目

""")
        
        # 番号付きリストと箇条書きリストの混在
        test_name = self._get_test_case_name("番号付きリスト", "箇条書きとの混在")
        patterns.append(f"""# {test_name}
- 箇条書き項目1
- 箇条書き項目2
- 箇条書き項目3

1. 番号付き項目1
2. 番号付き項目2
3. 番号付き項目3

- 再び箇条書き項目
- 最後の箇条書き項目

""")
        
        # ブロック内の番号付きリスト
        test_name = self._get_test_case_name("番号付きリスト", "枠線ブロック内")
        patterns.append(f"""# {test_name}
;;;枠線
1. 枠線内の番号付き項目1
2. 枠線内の番号付き項目2
3. 枠線内の番号付き項目3
4. 枠線内の番号付き項目4
;;;

""")
        
        # ハイライトブロック内の番号付きリスト
        test_name = self._get_test_case_name("番号付きリスト", "ハイライトブロック内")
        patterns.append(f"""# {test_name}
;;;ハイライト color=#dfd
1. ハイライト内の番号付き項目1
2. ハイライト内の番号付き項目2
3. ハイライト内の番号付き項目3
;;;

""")
        
        # 複合ブロック内の番号付きリスト
        test_name = self._get_test_case_name("番号付きリスト", "複合ブロック内")
        patterns.append(f"""# {test_name}
;;;枠線+ハイライト color=#fdd
1. 複合ブロック内の番号付き項目1
2. 複合ブロック内の番号付き項目2
3. 複合ブロック内の番号付き項目3
;;;

""")
        
        # ブロック内での番号付きリストと箇条書きリストの混在
        test_name = self._get_test_case_name("番号付きリスト", "ブロック内混在")
        patterns.append(f"""# {test_name}
;;;枠線
説明テキストが最初にあります。

- 箇条書き項目1
- 箇条書き項目2

次に番号付きリストが続きます：

1. 番号付き項目1
2. 番号付き項目2
3. 番号付き項目3

最後に追加の説明テキストです。
;;;

""")
        
        # 見出しブロック内の番号付きリスト
        test_name = self._get_test_case_name("番号付きリスト", "見出しブロック内")
        patterns.append(f"""# {test_name}
;;;見出し2
1. 見出しブロック内の番号付き項目1
2. 見出しブロック内の番号付き項目2
;;;

""")
        
        # 複数のブロックでの番号付きリスト
        test_name = self._get_test_case_name("番号付きリスト", "複数ブロック")
        patterns.append(f"""# {test_name}
;;;枠線
1. 最初のブロック内番号付き項目1
2. 最初のブロック内番号付き項目2
;;;

;;;ハイライト color=#ffe
1. 2番目のブロック内番号付き項目1
2. 2番目のブロック内番号付き項目2
3. 2番目のブロック内番号付き項目3
;;;

通常の番号付きリスト：
1. ブロック外の番号付き項目1
2. ブロック外の番号付き項目2

""")
        
        # スペースインデント付き番号付きリスト
        test_name = self._get_test_case_name("番号付きリスト", "インデント付き")
        patterns.append(f"""# {test_name}
  1. インデント付き番号付き項目1
  2. インデント付き番号付き項目2
   3. 異なるインデント番号付き項目3
    4. さらに深いインデント番号付き項目4

""")
        
        return patterns
    
    def generate_mixed_patterns(self) -> List[str]:
        """混在パターンを生成"""
        patterns = []
        
        test_name = self._get_test_case_name("混在パターン", "基本的な記法混在")
        patterns.append(f"""# {test_name}

通常の段落テキストです。

;;;太字
太字ブロックの例
;;;

以下はリストです：

- 通常のリスト項目
- :枠線: 枠線付きリスト項目
- :太字+イタリック: 複合キーワード付きリスト項目
- 最後の通常項目

番号付きリストも含めます：

1. 最初の番号付き項目
2. 2番目の番号付き項目
3. 3番目の番号付き項目

;;;見出し2+ハイライト color=#dfd
見出しとハイライトの組み合わせ
;;;

別の段落テキストが続きます。

;;;枠線
枠線で囲まれたコンテンツ。
複数行のテキストを含むことができます。

改行も保持されます。
;;;

""")
        
        # エラーケースのテスト
        test_name = self._get_test_case_name("エラーケース", "無効なキーワード")
        patterns.append(f"""# {test_name}

;;;存在しないキーワード
このキーワードは定義されていないため、エラーとして表示されるはずです。
;;;

;;;見出し1+存在しないキーワード
一部のキーワードが無効な複合パターンです。
;;;

- :無効キーワード: 無効キーワード付きリスト項目
- :太字+無効キーワード: 複合で一部無効なリスト項目

""")
        
        return patterns
    
    def generate_performance_test_patterns(self) -> List[str]:
        """パフォーマンステスト用パターンを生成"""
        patterns = []
        
        # 大量のリスト項目テスト
        test_name = self._get_test_case_name("パフォーマンステスト", "大量リスト項目")
        patterns.append(f"""# {test_name}

""")
        
        for i in range(100):  # 100項目に増加
            keyword = list(self.BLOCK_KEYWORDS.keys())[i % len(self.BLOCK_KEYWORDS)]
            patterns.append(f"- :{keyword}: 項目{i+1}の内容です\n")
        
        patterns.append("\n")
        
        # 大量の番号付きリスト項目テスト
        test_name = self._get_test_case_name("パフォーマンステスト", "大量番号付きリスト")
        patterns.append(f"""# {test_name}

""")
        
        for i in range(50):  # 50項目の番号付きリスト
            patterns.append(f"{i+1}. 番号付き項目{i+1}の内容です\n")
        
        patterns.append("\n")
        
        # ブロック内大量番号付きリスト
        test_name = self._get_test_case_name("パフォーマンステスト", "ブロック内大量番号付きリスト")
        patterns.append(f"""# {test_name}
;;;枠線
""")
        
        for i in range(30):  # 30項目の番号付きリスト
            patterns.append(f"{i+1}. ブロック内番号付き項目{i+1}\n")
        
        patterns.append(";;;\n\n")
        
        # 長いコンテンツのブロック
        test_name = self._get_test_case_name("パフォーマンステスト", "長いコンテンツ")
        long_content = "この文章は長いコンテンツのテストです。" * 50  # 50倍に増加
        patterns.append(f"""# {test_name}
;;;枠線+太字
{long_content}
;;;

""")
        
        # 深いネストのテスト（有効な組み合わせのみ）
        test_name = self._get_test_case_name("パフォーマンステスト", "深いネスト")
        # 見出しを含まない有効な組み合わせを作成
        valid_keywords = [k for k, v in self.BLOCK_KEYWORDS.items() if v["category"] != "heading"]
        valid_keywords.append("見出し1")  # 見出しは1つだけ追加
        deep_combo = "+".join(valid_keywords)
        patterns.append(f"""# {test_name}
;;;{deep_combo}
{len(valid_keywords)}つのキーワードを組み合わせた深いネスト構造のテストです。
処理性能とネスト表示の確認を行います（有効な組み合わせのみ）。
;;;

""")
        
        return patterns
    
    def generate_image_patterns(self) -> List[str]:
        """画像記法のパターンを生成"""
        patterns = []
        patterns.append(f"\n# {self._get_test_case_name('画像記法', '基本パターン')}\n\n")
        
        # 各種画像拡張子のテスト
        extensions = ["png", "jpg", "jpeg", "gif", "webp", "svg"]
        for ext in extensions:
            pattern = f";;;test_image.{ext};;;\n\n"
            if pattern not in self.generated_patterns:
                patterns.append(pattern)
                self.generated_patterns.add(pattern)
        
        # 画像とテキストの混在
        patterns.append(f"\n# {self._get_test_case_name('画像記法', 'テキストとの混在')}\n\n")
        patterns.append("画像の前のテキスト\n\n")
        patterns.append(";;;sample_photo.png;;;\n\n")
        patterns.append("画像の後のテキスト\n\n")
        
        # 複数画像
        patterns.append(f"\n# {self._get_test_case_name('画像記法', '複数画像の連続')}\n\n")
        patterns.append(";;;image1.png;;;\n\n")
        patterns.append(";;;image2.jpg;;;\n\n")
        patterns.append(";;;image3.gif;;;\n\n")
        
        # 他の記法との組み合わせ
        patterns.append(f"\n# {self._get_test_case_name('画像記法', 'ブロック内での使用')}\n\n")
        patterns.append(";;;枠線\n重要な画像：\n\n;;;important.png;;;\n\nこの画像は重要です。\n;;;\n\n")
        
        # リスト内の画像
        patterns.append(f"\n# {self._get_test_case_name('画像記法', 'リスト内での使用')}\n\n")
        patterns.append("- 画像付きリスト項目\n")
        patterns.append("- ;;;icon.png;;;\n")
        patterns.append("- 次の項目\n\n")
        
        return patterns
    
    def generate_file(self, output_path: str = "test_patterns.txt") -> Path:
        """テストファイルを生成"""
        output_file = Path(output_path)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # ヘッダー
            f.write(self.generate_header())
            
            # 単一ブロック記法
            f.write("".join(self.generate_single_block_patterns()))
            
            # 複合ブロック記法
            f.write("".join(self.generate_compound_block_patterns()))
            
            # キーワード付きリスト
            f.write("".join(self.generate_keyword_list_patterns()))
            
            # 番号付きリスト
            f.write("".join(self.generate_numbered_list_patterns()))
            
            # 混在パターン
            f.write("".join(self.generate_mixed_patterns()))
            
            # 画像記法
            f.write("".join(self.generate_image_patterns()))
            
            # パフォーマンステスト
            f.write("".join(self.generate_performance_test_patterns()))
            
            # フッター
            f.write(f"""# テストファイル終了
# 生成パターン数: {len(self.generated_patterns)}
# テストケース総数: {self.test_case_counter}
# すべてのパターンが正常に処理されることを確認してください。
""")
        
        return output_file
    
    def get_statistics(self) -> Dict[str, int]:
        """生成統計を取得"""
        return {
            "total_patterns": len(self.generated_patterns),
            "test_cases": self.test_case_counter,
            "single_keywords": len(self.BLOCK_KEYWORDS),
            "highlight_colors": len(self.HIGHLIGHT_COLORS),
            "max_combinations": self.max_combinations,
        }


def main():
    """メイン関数"""
    generator = TestFileGenerator(max_combinations=1000)
    output_file = generator.generate_file("test_patterns.txt")
    stats = generator.get_statistics()
    
    print(f"テストファイルを生成しました: {output_file}")
    print(f"生成パターン数: {stats['total_patterns']}")
    print(f"テストケース総数: {stats['test_cases']}")
    print(f"単一キーワード数: {stats['single_keywords']}")
    print(f"ハイライト色数: {stats['highlight_colors']}")
    print(f"最大組み合わせ設定: {stats['max_combinations']}")


if __name__ == "__main__":
    main()