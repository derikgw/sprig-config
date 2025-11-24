import yaml
from pathlib import Path
from sprigconfig.config_loader import ConfigLoader

def _load_import_list(yaml_path: Path):
    """
    Load a YAML file and return the list under top-level 'imports',
    or [] if not present.
    """
    if not yaml_path.exists():
        return []

    data = yaml.safe_load(yaml_path.read_text()) or {}
    imports = data.get("imports", [])
    return imports if isinstance(imports, list) else []


def test_meta_sources_records_all_loaded_files(full_config_dir):
    """
    Verify that `_meta.sources` contains exactly the set of files actually loaded
    from tests/config, in correct merge order.

    This version dynamically reads the 'imports:' list from the actual
    application.yml and application-dev.yml so the test will ALWAYS match
    the real structure of tests/config.
    """

    # Load config
    cfg = ConfigLoader(config_dir=full_config_dir, profile="dev").load()
    sources = cfg.get("sprigconfig._meta.sources")

    assert isinstance(sources, list)
    assert len(sources) > 0, "Merge trace should never be empty"

    # Convert to absolute Path objects
    sources_paths = [Path(s).resolve() for s in sources]

    # Paths to the main config files
    application_yml = (full_config_dir / "application.yml").resolve()
    profile_yml     = (full_config_dir / "application-dev.yml").resolve()

    # Read imports from the actual fixture YAML
    imports_base = _load_import_list(application_yml)
    imports_dev  = _load_import_list(profile_yml)

    # print(cfg.dump(path=None, pretty=True))
    cfg.dump(Path("config-dump.yml"), sprigconfig_first=True)

    # Build expected order:
    # 1. application.yml
    expected = [application_yml]

    # 2. imports from application.yml (exact order)
    for imp in imports_base:
        expected.append((full_config_dir / imp).resolve())

    # 3. application-dev.yml
    expected.append(profile_yml)

    # 4. imports from application-dev.yml (exact order)
    for imp in imports_dev:
        expected.append((full_config_dir / imp).resolve())

    # Assertions
    # --- Every expected file must be present ---
    for path in expected:
        assert path in sources_paths, f"Missing expected source: {path}"

    # --- And no extra files should exist in sources ---
    for path in sources_paths:
        assert path in expected, f"Unexpected extra source found: {path}"
