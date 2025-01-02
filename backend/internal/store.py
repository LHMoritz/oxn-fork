from typing import Optional, List, Dict, Union
from enum import Enum


class FileFormat(Enum):
    JSON = "json"
    CSV = "csv"
    YAML = "yaml"


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
        pass
    def list_files(self) -> List[str]:
        """List all files in the document store"""
        pass

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

        if format == FileFormat.JSON:
            with open(file_path, 'r') as f:
                return json.load(f)
        elif format == FileFormat.CSV:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                # some values are integers
                return [{k: int(v) if v.isdigit() else v for k, v in row.items()} 
                   for row in reader]
        elif format == FileFormat.YAML:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported format: {format}")

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


"""
OLD CODE
Purpose: Manages data storage.
Functionality: Provides methods to read/write data to an HDF5 store and manage a Trie structure for efficient lookups.
Connection: Used by various components to persist and retrieve experimental data.


Simple HDF5-based storage and JSON export

import pickle
import warnings
import json
import os
from pathlib import Path
import pandas as pd
from typing import List, Dict
from backend.internal.settings import STORAGE_NAME, TRIE_NAME, STORAGE_DIR

# silence warning that we cant use hex strings as key names
# we don't want table accessing by dot notation
# due to fixed format in hdf
from tables import NaturalNameWarning
warnings.filterwarnings("ignore", category=NaturalNameWarning)

# Global variable to store the configured output path
_configured_path = None

def configure_output_path(path: str) -> None:
    global _configured_path
    _configured_path = path

def _get_storage_path() -> Path:
    storage_dir = Path(_configured_path if _configured_path else STORAGE_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir / STORAGE_NAME

class Node:

    def __init__(self, character):
        self.character = character

        self.end = False
        self.children = {}


class Trie:
    def __init__(self, disk_name=TRIE_NAME):
        self.root = Node("")
        self.keys = []
        self.disk_name = disk_name
        if self.disk_name:
            self.deserialize()

    def insert(self, store_entry: str):
        node = self.root

        for character in store_entry:
            if character in node.children:
                node = node.children[character]
            else:
                new_node = Node(character)
                node.children[character] = new_node
                node = new_node
        node.end = True
        if self.disk_name:
            self.serialize()

    def depth_first_search(self, node, prefix):
        if node.end:
            self.keys.append(prefix + node.character)
        for child in node.children.values():
            self.depth_first_search(child, prefix + node.character)

    def query(self, item):
        self.keys = []
        node = self.root

        for character in item:
            if character in node.children:
                node = node.children[character]
            else:
                return []
        self.depth_first_search(node, item[:-1])

        return sorted(self.keys, reverse=True)

    def serialize(self):

        if self.disk_name:
            with open(self.disk_name, "wb") as fp:
                pickle.dump(self.root, fp)

    def deserialize(self):

        # trie might have not been serialized yet
        if self.disk_name:
            try:
                with open(self.disk_name, "rb") as fp:
                    self.root = pickle.load(fp)
            except FileNotFoundError:
                return


def construct_key(experiment_key, run_key, response_key):
    return experiment_key + "/" + run_key + "/" + response_key


def write_dataframe(dataframe, experiment_key, run_key, response_key) -> None:
    store_path = _get_storage_path()
    with pd.HDFStore(store_path) as store:
        key = construct_key(experiment_key, run_key, response_key)
        store.put(key=key, value=dataframe)
        trie = Trie()
        trie.insert(key)


def get_dataframe(key):
    trie = Trie()
    results = trie.query(key)
    if results:
        with pd.HDFStore(_get_storage_path()) as store:
            return store.get(key=key)


def annotate(key, **kwargs):
    with pd.HDFStore(_get_storage_path()) as store:
        store.get_storer(key).attrs.metadata = kwargs


def remove_dataframe(key) -> None:
    with pd.HDFStore(_get_storage_path()) as store:
        store.remove(key=key)


def consolidate_runs(experiment_key, response_variable) -> pd.DataFrame:
    trie = Trie()
    results = trie.query(experiment_key)
    results = [key for key in results if response_variable in key]
    dataframes = [get_dataframe(result) for result in results]
    if dataframes:
        return pd.concat(dataframes)


def list_keys_for_experiment(experiment_key) -> List[str]:
    trie = Trie()
    results = trie.query(item=experiment_key)
    return results


def list_keys_for_run(experiment_key, experiment_run) -> List[str]:
    trie = Trie()
    results = trie.query(experiment_key + experiment_run)
    return results


def list_all_dataframes():
    with pd.HDFStore(_get_storage_path()) as store:
        return store.keys(include="pandas")

def write_json_data(data, run_key, response_key, out_path=None) -> None:
    storage_dir = out_path if out_path else STORAGE_DIR
    Path(storage_dir).mkdir(parents=True, exist_ok=True)
    
    if isinstance(data, pd.DataFrame):
        data = data.to_dict(orient='records')
        
    filename = f"{run_key}_{response_key}.json"
    json_path = Path(storage_dir) / filename
    
    with open(json_path, 'x') as f:
        json.dump(data, f, indent=2)

"""