from typing import Optional, List, Dict, Union
from enum import Enum

class FileFormat(Enum):
    JSON = "json"
    CSV = "csv"
    YAML = "yaml"

class StoreError(Exception):
    """Custom error type for store operations"""
    def __init__(self, message: str, filename: str, original_error: Optional[Exception] = None):
        self.message = message
        self.filename = filename
        self.original_error = original_error
        super().__init__(f"{message} - File: {filename}" + 
                        (f" - Original error: {str(original_error)}" if original_error else ""))

class DocumentStore:
    """
    Interface for a multi-format document store
    """

    def save(self, key: str, data: Union[Dict, List], format: FileFormat) -> None:
        """Save a file with a given key and format"""
        pass

    def load(self, key: str, format: FileFormat) -> Optional[Union[Dict, List]]:
        """Load a file by its key and format"""
        pass

    def delete(self, key: str) -> None:
        """Delete a file by its key"""
        pass

    def list_keys(self) -> List[str]:
        """List all keys in the document store"""
        return []

    def list_files(self) -> List[str]:
        """List all files in the document store"""
        return []

import os
import json
import csv
import yaml
from typing import Optional, List, Dict, Union
from enum import Enum

class LocalFSStore(DocumentStore):
    def __init__(self, base_path: str):
        """
        Initialize the document store with a base directory.
        """
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def _get_file_path(self, key: str, format: FileFormat) -> str:
        """Helper to construct file path."""
        return os.path.join(self.base_path, f"{key}.{format.value}")

    def save(self, key: str, data: Union[Dict, List], format: FileFormat) -> None:
        """
        Save a file with a given key and format.
        """
        file_path = self._get_file_path(key, format)
        if format == FileFormat.JSON:
            with open(file_path, 'w') as f:
                json.dump(data, f)
        elif format == FileFormat.CSV:
            if isinstance(data, list) and all(isinstance(row, dict) for row in data):
                with open(file_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
            else:
                raise ValueError("CSV data must be a list of dictionaries.")
        elif format == FileFormat.YAML:
            with open(file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def load(self, key: str, format: FileFormat) -> Optional[Union[Dict, List]]:
        """
        Load a file by its key and format.
        """
        file_path = self._get_file_path(key, format)
        if not os.path.exists(file_path):
            return None

        try:
            if format == FileFormat.JSON:
                with open(file_path, 'r') as f:
                    return json.load(f)
            elif format == FileFormat.CSV:
                with open(file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    return [{k: int(v) if v.isdigit() else v for k, v in row.items()} 
                       for row in reader]
            elif format == FileFormat.YAML:
                with open(file_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            raise StoreError(
                message="Failed to load file",
                filename=file_path,
                original_error=e
            )

    def delete(self, key: str) -> None:
        """
        Delete all files with the given key in any format.
        """
        for format in FileFormat:
            file_path = self._get_file_path(key, format)
            if os.path.exists(file_path):
                os.remove(file_path)

    def list_keys(self) -> List[str]:
        """
        List all unique keys in the document store, irrespective of format.
        """
        files = os.listdir(self.base_path)
        keys = {os.path.splitext(filename)[0] for filename in files}
        return list(keys)

    def list_files(self) -> List[str]:
        """List all files in the document store"""
        return os.listdir(self.base_path)