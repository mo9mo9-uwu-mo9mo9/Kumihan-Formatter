import ast
import math
from typing import Tuple


def calculate_halstead_metrics(source_code: str) -> Tuple[int, int, int, int, float, float, float, float, float]:
    """
    Calculate Halstead Complexity Metrics for a given source code.

    Args:
        source_code (str): The source code to analyze.

    Returns:
        Tuple[int, int, int, int, float, float, float, float, float]: A tuple containing:
            - n1: Number of distinct operators
            - n2: Number of distinct operands
            - N1: Total number of operators
            - N2: Total number of operands
            - Vocabulary: n1 + n2
            - Length: N1 + N2
            - Calculated length: n1 * log2(n1) + n2 * log2(n2)
            - Volume: Length * log2(Vocabulary)
            - Difficulty: (n1 / 2) * (N2 / n2)
            - Effort: Difficulty * Volume
            - Time: Effort / 18
            - Bugs: Volume / 3000
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0

    operators = []
    operands = []

    class HalsteadVisitor(ast.NodeVisitor):
        def visit_BinOp(self, node):
            operators.append(type(node.op))
            self.generic_visit(node)

        def visit_UnaryOp(self, node):
            operators.append(type(node.op))
            self.generic_visit(node)

        def visit_Compare(self, node):
            for op in node.ops:
                operators.append(type(op))
            self.generic_visit(node)

        def visit_BoolOp(self, node):
            operators.append(type(node.op))
            self.generic_visit(node)

        def visit_Name(self, node):
            operands.append(node.id)

        def visit_Num(self, node):
            operands.append(node.n)

        def visit_Constant(self, node):
            operands.append(node.value)

        def visit_Attribute(self, node):
            operands.append(node.attr)

    visitor = HalsteadVisitor()
    visitor.visit(tree)

    n1 = len(set(operators))
    n2 = len(set(operands))
    N1 = len(operators)
    N2 = len(operands)

    vocabulary = n1 + n2
    length = N1 + N2

    if n1 > 0 and n2 > 0:
        calculated_length = n1 * math.log2(n1) + n2 * math.log2(n2)
        difficulty = (n1 / 2) * (N2 / n2)
    else:
        calculated_length = 0.0
        difficulty = 0.0

    volume = length * math.log2(vocabulary) if vocabulary > 0 else 0.0
    effort = difficulty * volume
    time = effort / 18 if effort > 0 else 0.0
    bugs = volume / 3000 if volume > 0 else 0.0

    return n1, n2, N1, N2, vocabulary, length, calculated_length, volume, difficulty, effort, time, bugs
