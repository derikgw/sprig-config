import yaml
from pathlib import Path


def load_config(config_dir: Path):
    """Load base application.yml into a dict."""
    config_file = Path(config_dir) / "application.yml"

    if not config_file.exists():
        raise FileNotFoundError(f"{config_file} does not exist")

    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
