import yaml

class YamlParser:
    def parse(self, text: str):
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as e:
            mark = getattr(e, "problem_mark", None)
            if mark is None:
                raise ValueError("Invalid YAML syntax") from None
            raise ValueError(
                f"Invalid YAML syntax at line {mark.line + 1}, column {mark.column + 1}"
            ) from None
