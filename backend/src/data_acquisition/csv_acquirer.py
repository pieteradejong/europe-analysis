"""
CSV Data Acquirer

This module provides functionality for acquiring demographic data from CSV files.
"""

import csv
import logging
from pathlib import Path
from typing import Any

from .base import AcquisitionResult, DataAcquirer

logger = logging.getLogger(__name__)


class CSVAcquirer(DataAcquirer):
    """
    Acquires data from CSV files with flexible schema detection.

    Supports various CSV formats and automatically detects column structure.
    """

    def __init__(
        self,
        source: str,
        encoding: str = "utf-8",
        delimiter: str = ",",
        has_header: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize CSV acquirer.

        Args:
            source: Path to CSV file
            encoding: File encoding (default: utf-8)
            delimiter: CSV delimiter (default: comma)
            has_header: Whether CSV has header row (default: True)
            **kwargs: Additional parameters
        """
        super().__init__(source, **kwargs)
        self.encoding = encoding
        self.delimiter = delimiter
        self.has_header = has_header
        self.file_path = Path(source)

    def validate_source(self) -> bool:
        """
        Validate that the CSV file exists and is readable.

        Returns:
            True if file is valid, False otherwise
        """
        if not self.file_path.exists():
            self.logger.error("CSV file does not exist: %s", self.source)
            return False

        if not self.file_path.is_file():
            self.logger.error("Source is not a file: %s", self.source)
            return False

        if not self.file_path.suffix.lower() == ".csv":
            self.logger.warning("File does not have .csv extension: %s", self.source)

        return True

    def acquire(self) -> AcquisitionResult:  # noqa: PLR0912, PLR0915
        """
        Acquire data from CSV file.

        Returns:
            AcquisitionResult containing the CSV data as list of dictionaries
        """
        if not self.validate_source():
            return AcquisitionResult(
                success=False,
                error=f"Invalid CSV source: {self.source}",
            )

        try:
            data: list[dict[str, Any]] = []
            metadata: dict[str, Any] = {
                "file_path": str(self.file_path),
                "file_size": self.file_path.stat().st_size,
                "encoding": self.encoding,
                "delimiter": self.delimiter,
                "has_header": self.has_header,
            }

            with open(self.file_path, encoding=self.encoding, newline="") as csvfile:
                # Try to detect delimiter if not specified
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                if not self.delimiter:
                    try:
                        self.delimiter = sniffer.sniff(sample).delimiter
                        metadata["detected_delimiter"] = self.delimiter
                    except csv.Error:
                        self.delimiter = ","  # Default fallback

                reader = csv.DictReader(csvfile, delimiter=self.delimiter)

                # If no header, create generic column names
                if not self.has_header:
                    # Read first row to get column count
                    first_row = next(reader, None)
                    if first_row:
                        # Convert to list and create generic headers
                        reader = csv.DictReader(
                            csvfile,
                            delimiter=self.delimiter,
                            fieldnames=[f"column_{i}" for i in range(len(first_row))],
                        )
                        # Reset to beginning
                        csvfile.seek(0)
                        reader = csv.DictReader(
                            csvfile,
                            delimiter=self.delimiter,
                            fieldnames=[f"column_{i}" for i in range(len(first_row))],
                        )

                for _row_num, row in enumerate(reader, start=1):
                    # Clean up values (strip whitespace, handle empty strings)
                    cleaned_row: dict[str, Any] = {}
                    for key, value in row.items():
                        if value is not None:
                            cleaned_value = value.strip()
                            # Try to convert to number if possible
                            try:
                                if "." in cleaned_value:
                                    cleaned_row[key.strip()] = float(cleaned_value)
                                else:
                                    cleaned_row[key.strip()] = int(cleaned_value)
                            except ValueError:
                                cleaned_row[key.strip()] = (
                                    cleaned_value if cleaned_value else None
                                )
                        else:
                            cleaned_row[key.strip()] = None

                    data.append(cleaned_row)

                metadata["rows_read"] = len(data)
                metadata["columns"] = list(data[0].keys()) if data else []

            self.logger.info(
                "Successfully acquired %d records from CSV: %s", len(data), self.source
            )

            return AcquisitionResult(
                success=True,
                data=data,
                metadata=metadata,
                records_count=len(data),
            )

        except PermissionError:
            error_msg = f"Permission denied reading CSV file: {self.source}"
            self.logger.error(error_msg)
            return AcquisitionResult(success=False, error=error_msg)

        except UnicodeDecodeError as e:
            error_msg = f"Encoding error reading CSV file: {self.source} - {e}"
            self.logger.error(error_msg)
            return AcquisitionResult(success=False, error=error_msg)

        except csv.Error as e:
            error_msg = f"CSV parsing error: {self.source} - {e}"
            self.logger.error(error_msg)
            return AcquisitionResult(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"Unexpected error reading CSV file: {self.source} - {e}"
            self.logger.error(error_msg, exc_info=True)
            return AcquisitionResult(success=False, error=error_msg)
