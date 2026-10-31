import re
import tomllib

class TomlParser:
    def parse(self, text: str):
        try:
            return tomllib.loads(text)
        except tomllib.TOMLDecodeError as e:
            line = getattr(e, "lineno", None)
            column = getattr(e, "colno", None)
            if line is None or column is None:
                location = re.search(r"\(at line (\d+), column (\d+)\)$", str(e))
                if location is None:
                    raise ValueError("Invalid TOML syntax") from None
                line, column = location.groups()
            raise ValueError(
                f"Invalid TOML syntax at line {line}, column {column}"
            ) from None
