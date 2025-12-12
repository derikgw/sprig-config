"""
Full merge provenance test.

Purpose:
    Validate that ConfigLoader correctly merges configuration across
    base, imports, and profile overlays, and that _meta accurately
    describes the sources and merge order.

This test uses existing files under tests/config/.
"""

from pathlib import Path
from sprigconfig.config_loader import ConfigLoader


def test_full_mergÍe_provenance():
    """
    End-to-end verification of merge correctness and _meta integrity.
    """

    # Arrange
    config_dir = Path(__file__).parent / "config"
    loader = ConfigLoader(config_dir=config_dir, profile="dev")

    # Act
    config = loader.load()
    meta = config["sprigconfig"]["_meta"]

    # ------------------------------------------------------------------
    # 1️⃣  _meta integrity checks (absolute path accuracy)
    # ------------------------------------------------------------------
    expected_sources = {
        str((config_dir / "application.yml").resolve()),
        str((config_dir / "application-dev.yml").resolve()),
        str((config_dir / "imports/common.yml").resolve()),
        str((config_dir / "imports/job-default.yml").resolve()),
    }

    actual_sources = set(meta["sources"])
    missing = expected_sources - actual_sources
    unexpected = actual_sources - expected_sources

    assert not missing, f"Missing expected sources from _meta: {missing}"
    assert not unexpected, f"Unexpected extra sources in _meta: {unexpected}"

    # Every source listed actually exists
    for src in meta["sources"]:
        path = Path(src)
        assert path.exists(), f"_meta lists missing file: {path}"

    # Import trace exists and is ordered
    trace = meta.get("import_trace", [])
    assert isinstance(trace, list) and len(trace) >= 2
    trace_files = [
        Path(t["file"]).name if isinstance(t, dict) and "file" in t else str(t)
        for t in trace
    ]
    assert "application.yml" in trace_files
    assert "application-dev.yml" in trace_files
    assert trace_files.index("application.yml") < trace_files.index("application-dev.yml")

    # ------------------------------------------------------------------
    # 2️⃣  Merge behavior checks (real app overlay verification)
    # ------------------------------------------------------------------
    base_profile = "base"
    final_profile = config["app"]["profile"]
    assert base_profile != final_profile, "Expected overlay to override app.profile"
    assert final_profile == "dev", f"Expected profile 'dev', got {final_profile}"
    assert config["app"]["debug_mode"] is True, "Expected debug_mode=True from overlay"

    # ------------------------------------------------------------------
    # 3️⃣  Sanity: nothing unexpected disappeared
    # ------------------------------------------------------------------
    assert "app" in config
    assert "sprigconfig" in config, "Expected sprigconfig namespace present after merge"
    assert "_meta" in config["sprigconfig"], "Expected _meta block within sprigconfig namespace"


    # ------------------------------------------------------------------
    # 4️⃣  _meta truthfulness
    # ------------------------------------------------------------------
    assert meta["profile"] == "dev"
    assert config["sprigconfig"]["_meta"] == meta

    for key in ("profile", "sources", "import_trace"):
        assert key in meta, f"Missing expected _meta key: {key}"

    print("\n✅ Full merge provenance verified successfully.")
