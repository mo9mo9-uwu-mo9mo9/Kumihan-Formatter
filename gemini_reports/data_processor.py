from typing import Any, Union


class DataProcessor:
    """
    Processes raw data into a structured format suitable for reporting.

    This class provides methods for loading, transforming, and aggregating
    data records.
    """

    def __init__(self) -> None:
        """
        Initializes the DataProcessor.
        """
        self.processed_records: list[dict[str, Any]] = []

    def load_raw_data(self, raw_data: list[dict[str, Any]]) -> None:
        """
        Loads raw data into the processor.

        Args:
            raw_data: A list of dictionaries, where each dictionary represents a record.
        """
        self.processed_records = raw_data

    def process_records(self, key_to_extract: str) -> list[dict[str, Any]]:
        """
        Processes the loaded records, extracting a specific key and adding a status.

        Each record will have an 'extracted_value' field based on `key_to_extract`
        and a 'status' indicating if the key was found.

        Args:
            key_to_extract: The key whose value should be extracted and included
                            in the processed record.

        Returns:
            A list of processed records, each with an 'extracted_value' and 'status'.
        """
        processed_list: list[dict[str, Any]] = []
        for record in self.processed_records:
            processed_record: dict[str, Any] = record.copy()
            extracted_value: Any = record.get(key_to_extract)
            processed_record['extracted_value'] = extracted_value
            processed_record['status'] = 'processed' if extracted_value is not None else 'missing_key'
            processed_list.append(processed_record)
        return processed_list

    def aggregate_data(self, data: list[dict[str, Any]], group_by_key: str) -> dict[str, Union[int, float]]:
        """
        Aggregates data based on a specified key, counting occurrences.

        Args:
            data: A list of dictionaries to aggregate.
            group_by_key: The key to group by. The values associated with this key
                          will become the keys in the aggregation result.

        Returns:
            A dictionary where keys are the unique string representations of values
            from `group_by_key` and values are their counts (integers).
        """
        aggregation: dict[str, Union[int, float]] = {}
        for record in data:
            key_value: Any = record.get(group_by_key)
            if key_value is not None:
                # Convert key_value to string for dictionary key consistency
                key_str: str = str(key_value)
                aggregation[key_str] = aggregation.get(key_str, 0) + 1
        return aggregation
