import unittest
import tempfile
import shutil
from pathlib import Path

from internal.store import LocalFSStore, FileFormat


class TestLocalFSStore(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory for the test."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = LocalFSStore(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_save_and_load_json(self):
        """Test saving and loading a JSON file."""
        key = "test_json"
        data = {"name": "Test", "value": 42}
        self.store.save(key, data, FileFormat.JSON)

        loaded_data = self.store.load(key, FileFormat.JSON)
        self.assertEqual(data, loaded_data)

    def test_save_and_load_csv(self):
        """Test saving and loading a CSV file."""
        key = "test_csv"
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        self.store.save(key, data, FileFormat.CSV)

        loaded_data = self.store.load(key, FileFormat.CSV)
        self.assertEqual(data, loaded_data)

    def test_save_and_load_yaml(self):
        """Test saving and loading a YAML file."""
        key = "test_yaml"
        data = {"title": "Test YAML", "enabled": True}
        self.store.save(key, data, FileFormat.YAML)

        loaded_data = self.store.load(key, FileFormat.YAML)
        self.assertEqual(data, loaded_data)

    def test_list_keys(self):
        """Test listing keys."""
        self.store.save("key1", {"key": "value1"}, FileFormat.JSON)
        self.store.save("key2", [{"row": 1}], FileFormat.CSV)
        self.store.save("key3", {"key": "value3"}, FileFormat.YAML)

        keys = self.store.list_keys()
        self.assertCountEqual(keys, ["key1", "key2", "key3"])

    def test_delete_file(self):
        """Test deleting files."""
        key = "key_to_delete"
        self.store.save(key, {"key": "value"}, FileFormat.JSON)

        self.assertIn(key, self.store.list_keys())
        self.store.delete(key)
        self.assertNotIn(key, self.store.list_keys())

    def test_nonexistent_load(self):
        """Test loading a nonexistent file."""
        loaded_data = self.store.load("nonexistent_key", FileFormat.JSON)
        self.assertIsNone(loaded_data)

    def test_invalid_csv_data(self):
        """Test saving invalid CSV data."""
        key = "invalid_csv"
        data = {"not": "a list"}

        with self.assertRaises(ValueError):
            self.store.save(key, data, FileFormat.CSV)


if __name__ == "__main__":
    unittest.main()
