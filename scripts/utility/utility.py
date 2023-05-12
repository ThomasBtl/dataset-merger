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