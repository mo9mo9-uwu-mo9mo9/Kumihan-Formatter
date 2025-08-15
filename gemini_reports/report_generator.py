from typing import Any, Optional


class ReportGenerator:
    """
    Generates various reports based on processed data.

    This class handles loading data and generating different formats of reports,
    such as text reports, and provides functionality to save them.
    """

    def __init__(self, template_path: str) -> None:
        """
        Initializes the ReportGenerator with a template path.

        Args:
            template_path: The file path to the report template.
        """
        self.template_path: str = template_path
        self.report_data: Optional[dict[str, Any]] = None

    def load_data(self, data: dict[str, Any]) -> None:
        """
        Loads data into the generator for report generation.

        Args:
            data: A dictionary containing data for the report.
        """
        self.report_data = data

    def generate_text_report(self) -> str:
        """
        Generates a simple text report from the loaded data.

        Returns:
            A string containing the generated text report.

        Raises:
            ValueError: If no data has been loaded using `load_data()` method.
        """
        if self.report_data is None:
            raise ValueError("No data loaded. Call load_data() first.")

        report_lines: list[str] = [f"--- Report from {self.template_path} ---"]
        for key, value in self.report_data.items():
            report_lines.append(f"{key}: {value}")
        report_lines.append("--- End of Report ---")
        return "\n".join(report_lines)

    def save_report(self, report_content: str, output_path: str) -> None:
        """
        Saves the generated report content to a specified file.

        Args:
            report_content: The content of the report as a string.
            output_path: The file path where the report will be saved.

        Raises:
            IOError: If there is an error writing the report to the file.
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
        except IOError as e:
            print(f"Error saving report to {output_path}: {e}")
            raise
