"""Special block parsing utilities for Kumihan-Formatter

This module handles parsing of special block types including code blocks,
tables, and other special formatting elements.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .block_parser import BlockParser

from ..ast_nodes import Node, NodeBuilder, paragraph


class SpecialBlockParser:
    """Parser for special block types"""

    def __init__(self, block_parser: "BlockParser") -> None:
        self.block_parser = block_parser

    def parse_code_block(self, lines: list[str], start_index: int) -> tuple[Node, int]:
        """Parse a code block

        ;;;記法は削除されました（Phase 1）
        この機能は新記法で置き換えられます
        """
        from kumihan_formatter.core.ast_nodes.factories import error_node

        return (
            error_node(";;;記法は削除されました（Phase 1）"),
            start_index + 1,
        )

    def parse_details_block(self, summary_text: str, content: str) -> Node:
        """Parse a details/summary block"""
        builder = NodeBuilder("details")
        builder.attribute("summary", summary_text)

        # Parse content
        content_node = paragraph(content) if content.strip() else paragraph("")
        builder.content([content_node])

        return builder.build()

    def parse_table_block(self, lines: list[str], start_index: int) -> tuple[Node, int]:
        """Parse a table block

        ;;;記法は削除されました（Phase 1）
        この機能は新記法で置き換えられます
        """
        from kumihan_formatter.core.ast_nodes.factories import error_node

        return (
            error_node(";;;記法は削除されました（Phase 1）"),
            start_index + 1,
        )

    def _parse_table_content(self, lines: list[str]) -> Node:
        """Parse table content into table structure"""
        # Simple table parsing: assume CSV-like format or pipe-separated
        rows = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Support both pipe-separated and comma-separated formats
            if "|" in line:
                # Pipe-separated format: | col1 | col2 | col3 |
                cells = [cell.strip() for cell in line.split("|")[1:-1]]
            elif "," in line:
                # Comma-separated format: col1, col2, col3
                cells = [cell.strip() for cell in line.split(",")]
            else:
                # Single column
                cells = [line]

            if cells:  # Only add non-empty rows
                rows.append(cells)

        if not rows:
            raise ValueError("テーブルに有効な行がありません")

        # Build table node using NodeBuilder
        builder = NodeBuilder("table")

        # Assume first row is header if it looks like header
        # (contains non-numeric data or is formatted differently)
        has_header = len(rows) > 1 and self._looks_like_header(rows[0])

        table_content = []

        if has_header:
            # Create header row
            header_builder = NodeBuilder("thead")
            header_row_builder = NodeBuilder("tr")
            header_cells = []
            for cell in rows[0]:
                cell_builder = NodeBuilder("th").content(cell)
                header_cells.append(cell_builder.build())
            header_row_builder.content(header_cells)
            header_builder.content([header_row_builder.build()])
            table_content.append(header_builder.build())

            # Process data rows
            if len(rows) > 1:
                tbody_builder = NodeBuilder("tbody")
                data_rows = []
                for row in rows[1:]:
                    row_builder = NodeBuilder("tr")
                    row_cells = []
                    for cell in row:
                        cell_builder = NodeBuilder("td").content(cell)
                        row_cells.append(cell_builder.build())
                    row_builder.content(row_cells)
                    data_rows.append(row_builder.build())
                tbody_builder.content(data_rows)
                table_content.append(tbody_builder.build())
        else:
            # All rows are data rows
            tbody_builder = NodeBuilder("tbody")
            data_rows = []
            for row in rows:
                row_builder = NodeBuilder("tr")
                row_cells = []
                for cell in row:
                    cell_builder = NodeBuilder("td").content(cell)
                    row_cells.append(cell_builder.build())
                row_builder.content(row_cells)
                data_rows.append(row_builder.build())
            tbody_builder.content(data_rows)
            table_content.append(tbody_builder.build())

        builder.content(table_content)
        return builder.build()

    def _looks_like_header(self, row: list[str]) -> bool:
        """Check if a row looks like a header row"""
        # Enhanced heuristic with more precise numeric detection
        header_indicators = ["名前", "項目", "内容", "値", "説明", "タイトル", "種類"]

        # Check for header indicator words
        for cell in row:
            if any(indicator in cell for indicator in header_indicators):
                return True

        # Count numeric vs non-numeric cells
        numeric_count = 0
        for cell in row:
            cell = cell.strip()
            if not cell:  # Empty cell
                continue

            # More strict numeric pattern validation
            if self._is_numeric_value(cell):
                numeric_count += 1

        # If more than 70% of cells are numeric, likely a data row
        non_empty_cells = len([cell for cell in row if cell.strip()])
        if non_empty_cells == 0:
            return False

        numeric_ratio = numeric_count / non_empty_cells
        return numeric_ratio <= 0.7

    def _is_numeric_value(self, value: str) -> bool:
        """Check if a value is purely numeric"""
        value = value.strip()
        if not value:
            return False

        # Remove common numeric formatting
        cleaned = (
            value.replace(",", "").replace(".", "").replace("-", "").replace("+", "")
        )

        # Check for pure digits or float patterns
        try:
            float(value.replace(",", ""))
            return True
        except ValueError:
            pass

        # Check for percentage
        if value.endswith("%") and cleaned[:-1].isdigit():
            return True

        # Check for currency patterns (simple)
        if value.startswith(("¥", "$", "€")) and cleaned[1:].isdigit():
            return True

        return cleaned.isdigit()
