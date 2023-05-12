import unittest
from excel_reader import ExcelReader
import yaml
import logging

def read_yaml(path: str) -> dict | None:
    with open(path, "r", encoding="utf-8") as f:
        try: 
            return yaml.safe_load(f)
        except yaml.YAMLError as exc:
            # https://pyyaml.org/wiki/PyYAMLDocumentation#:~:text=YAMLError,%3A22)
            if hasattr(exc, "problem_mark"):
                mark = exc.problem_mark
                logging.error(f' --- Invalid YAML structure or syntax at position: ({mark.line + 1}:{mark.column + 1})')

class TestExcelReader(unittest.TestCase):
    
    def test_wrong_path_excel(self):
        sources = read_yaml("./config_templates/wrong_path_excel.yaml")
        for metadata in sources.values():
            with self.assertRaises(FileNotFoundError):
                _ = ExcelReader(metadata["path"])


if __name__ == "__main__":
    unittest.main()