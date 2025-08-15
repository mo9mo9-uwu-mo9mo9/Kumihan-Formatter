import os
import datetime
from typing import List, Dict, Tuple, Optional
from gemini_reports.code_analyzer import analyze_code, list_python_files
from gemini_reports.quality_checker import load_threshold_config, check_quality_thresholds
import argparse
import logging
from gemini_reports.halstead import calculate_halstead_metrics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_enhanced_html_dashboard(directory: str, threshold_config_path: Optional[str] = None) -> None:
    """
    Generates an enhanced HTML dashboard report for Python code quality.

    Args:
        directory (str): The directory to analyze.
        threshold_config_path (Optional[str]): Path to the threshold configuration file.
    """
    try:
        logging.info(f"Starting enhanced report generation for directory: {directory}")
        python_files = list_python_files(directory)
        logging.info(f"Found {len(python_files)} Python files.")

        threshold_config = load_threshold_config(threshold_config_path)
        logging.info(f"Loaded threshold configuration: {threshold_config}")

        report_data: List[Dict[str, str]] = []
        for filepath in python_files:
            try:
                n1, n2, N1, N2, vocabulary, length, calculated_length, volume, difficulty, effort, time, bugs = analyze_code(filepath)
                metrics = {
                    "volume": volume,
                    "difficulty": difficulty,
                    "effort": effort,
                    "time": time,
                    "bugs": bugs
                }
                threshold_results = check_quality_thresholds(metrics, threshold_config)

                report_data.append({
                    "filepath": filepath,
                    "n1": str(n1),
                    "n2": str(n2),
                    "N1": str(N1),
                    "N2": str(N2),
                    "vocabulary": str(vocabulary),
                    "length": str(length),
                    "calculated_length": str(calculated_length),
                    "volume": str(volume),
                    "difficulty": str(difficulty),
                    "effort": str(effort),
                    "time": str(time),
                    "bugs": str(bugs),
                    "volume_exceeds": str(threshold_results["volume"]),
                    "difficulty_exceeds": str(threshold_results["difficulty"]),
                    "effort_exceeds": str(threshold_results["effort"]),
                    "time_exceeds": str(threshold_results["time"]),
                    "bugs_exceeds": str(threshold_results["bugs"]),
                })
            except Exception as e:
                logging.error(f"Error processing file {filepath}: {e}")

        # Generate HTML report
        html_content = generate_html(report_data)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"quality_report_{timestamp}.html"
        report_path = os.path.join(directory, report_filename)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logging.info(f"Enhanced report generated at: {report_path}")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def generate_html(report_data: List[Dict[str, str]]) -> str:
    """
    Generates an HTML report from the report data.

    Args:
        report_data (List[Dict[str, str]]): A list of dictionaries containing the report data.

    Returns:
        str: The HTML content of the report.
    """
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Code Quality Report</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid black;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            .exceeds-true {
                background-color: #ffcccc; /* Light red */
            }
            .exceeds-false {
                background-color: #ccffcc; /* Light green */
            }
        </style>
    </head>
    <body>
        <h1>Code Quality Report</h1>
        <table>
            <thead>
                <tr>
                    <th>Filepath</th>
                    <th>n1</th>
                    <th>n2</th>
                    <th>N1</th>
                    <th>N2</th>
                    <th>Vocabulary</th>
                    <th>Length</th>
                    <th>Calculated Length</th>
                    <th>Volume</th>
                    <th>Difficulty</th>
                    <th>Effort</th>
                    <th>Time</th>
                    <th>Bugs</th>
                    <th>Volume Exceeds</th>
                    <th>Difficulty Exceeds</th>
                    <th>Effort Exceeds</th>
                    <th>Time Exceeds</th>
                    <th>Bugs Exceeds</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </body>
    </html>
    """

    table_rows = ""
    for data in report_data:
        table_rows += f"""
        <tr>
            <td>{data["filepath"]}</td>
            <td>{data["n1"]}</td>
            <td>{data["n2"]}</td>
            <td>{data["N1"]}</td>
            <td>{data["N2"]}</td>
            <td>{data["vocabulary"]}</td>
            <td>{data["length"]}</td>
            <td>{data["calculated_length"]}</td>
            <td>{data["volume"]}</td>
            <td>{data["difficulty"]}</td>
            <td>{data["effort"]}</td>
            <td>{data["time"]}</td>
            <td>{data["bugs"]}</td>
            <td class="exceeds-{str(data["volume_exceeds"]).lower()}">{data["volume_exceeds"]}</td>
            <td class="exceeds-{str(data["difficulty_exceeds"]).lower()}">{data["difficulty_exceeds"]}</td>
            <td class="exceeds-{str(data["effort_exceeds"]).lower()}">{data["effort_exceeds"]}</td>
            <td class="exceeds-{str(data["time_exceeds"]).lower()}">{data["time_exceeds"]}</td>
            <td class="exceeds-{str(data["bugs_exceeds"]).lower()}">{data["bugs_exceeds"]}</td>
        </tr>
        """

    return html_template.format(table_rows=table_rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate code quality reports.")
    parser.add_argument("directory", help="The directory to analyze.")
    parser.add_argument("--threshold-config", help="Path to the threshold configuration file.", required=False)
    args = parser.parse_args()

    generate_enhanced_html_dashboard(args.directory, args.threshold_config)
