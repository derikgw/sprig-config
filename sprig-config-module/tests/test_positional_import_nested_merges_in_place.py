from pathlib import Path
from sprigconfig.config_loader import ConfigLoader

def test_positional_import_nested_merges_in_place():
    """
    Verifies that nested imports merge relative to their position in the parent.
    Expected structure: etl.jobs.etl.jobs.foo == "bar"
    """
    config_dir = Path(__file__).parent / "config"
    loader = ConfigLoader(config_dir=config_dir, profile="nested")
    config = loader.load()

    assert config["etl"]["jobs"]["etl"]["jobs"]["foo"] == "bar", (
        "Expected nested import to merge relative to its parent node, "
        "resulting in etl.jobs.etl.jobs.foo"
    )
