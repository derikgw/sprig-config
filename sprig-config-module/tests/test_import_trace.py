import yaml
from pathlib import Path
from sprigconfig.config_loader import ConfigLoader


def _load_import_list(path: Path):
    """Helper: load YAML and return the raw 'imports:' list."""
    data = yaml.safe_load(path.read_text())
    return data.get("imports", []) if isinstance(data, dict) else []


def test_import_trace_structure(full_config_dir):
    """import_trace should exist and contain well-formed entries."""
    cfg = ConfigLoader(config_dir=full_config_dir, profile="dev").load()
    trace = cfg.get("sprigconfig._meta.import_trace")

    assert isinstance(trace, list)
    assert len(trace) > 0

    for entry in trace:
        assert "file" in entry
        assert "imported_by" in entry   # root = None
        assert "import_key" in entry    # root = None
        assert "depth" in entry
        assert "order" in entry

        assert isinstance(entry["depth"], int)
        assert isinstance(entry["order"], int)


def test_import_trace_direct_imports(full_config_dir):
    """
    application.yml -> direct imports/*.yml

    All direct imports should list application.yml as imported_by.
    """
    cfg = ConfigLoader(config_dir=full_config_dir, profile="dev").load()
    trace = cfg.get("sprigconfig._meta.import_trace")

    root_entry = next(e for e in trace if e["imported_by"] is None)
    root_file = root_entry["file"]

    expected_imports = _load_import_list(full_config_dir / "application.yml")

    for imp in expected_imports:
        imp_path = (full_config_dir / imp).resolve()
        assert any(
            e["file"] == str(imp_path) and e["imported_by"] == root_file
            for e in trace
        ), f"Missing direct import: {imp}"


def test_import_trace_nested_imports(full_config_dir):
    """
    Validate actual import structure:

    application.yml
      -> job-default.yml
      -> common.yml

    No nested import exists in the real config set.
    """
    cfg = ConfigLoader(config_dir=full_config_dir, profile="dev").load()
    trace = cfg.get("sprigconfig._meta.import_trace")

    root = next(e for e in trace if e["imported_by"] is None)
    job = next(e for e in trace if "job-default.yml" in e["file"])
    common = next(e for e in trace if "common.yml" in e["file"])

    # Both are direct children of application.yml
    assert job["imported_by"] == root["file"]
    assert common["imported_by"] == root["file"]

    # Depth for both is root depth + 1
    assert job["depth"] == root["depth"] + 1
    assert common["depth"] == root["depth"] + 1


def test_import_trace_preserves_order(full_config_dir):
    """import_trace.order must be strictly increasing."""
    cfg = ConfigLoader(config_dir=full_config_dir, profile="dev").load()
    trace = cfg.get("sprigconfig._meta.import_trace")

    orders = [e["order"] for e in trace]
    assert orders == sorted(orders), "import_trace.order is not increasing"


def test_sources_and_import_trace_align(full_config_dir):
    """
    sources[] should match import_trace[] order exactly.
    """
    cfg = ConfigLoader(config_dir=full_config_dir, profile="dev").load()

    sources = cfg.get("sprigconfig._meta.sources")
    trace = cfg.get("sprigconfig._meta.import_trace")

    trace_files = [e["file"] for e in sorted(trace, key=lambda x: x["order"])]

    assert sources == trace_files


def test_import_trace_import_key(full_config_dir):
    """
    import_key should match the literal YAML list entry.
    """
    cfg = ConfigLoader(config_dir=full_config_dir, profile="dev").load()
    trace = cfg.get("sprigconfig._meta.import_trace")

    job_entry = next(e for e in trace if "job-default.yml" in e["file"])

    expected_keys = _load_import_list(full_config_dir / "application.yml")

    assert job_entry["import_key"] in expected_keys
