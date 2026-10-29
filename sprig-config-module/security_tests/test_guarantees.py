"""Security guarantees exercised against the complete installed package."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from hypothesis import given, strategies as st

from sprigconfig import Config, ConfigLoader, ConfigLoadError
from sprigconfig.lazy_secret import LazySecret


safe_keys = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=12)
secret = LazySecret("ENC(synthetic-invalid-ciphertext)")
trees = st.recursive(
    st.one_of(st.none(), st.booleans(), st.integers(), st.just(secret)),
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.dictionaries(safe_keys, children, max_size=5),
    ),
    max_leaves=25,
)


def assert_redacted(original, rendered):
    if isinstance(original, LazySecret):
        assert rendered == "<LazySecret>"
    elif isinstance(original, dict):
        assert rendered.keys() == original.keys()
        for key in original:
            assert_redacted(original[key], rendered[key])
    elif isinstance(original, list):
        assert len(original) == len(rendered)
        for left, right in zip(original, rendered):
            assert_redacted(left, right)
    else:
        assert original == rendered


@given(trees)
def test_safe_serialization_never_decrypts_nested_secrets(tree):
    with patch.object(LazySecret, "get", side_effect=AssertionError("Unexpected decryption")):
        cfg = Config({"root": tree})
        assert_redacted({"root": tree}, cfg.to_dict())
        cfg.dump()  # Also verify the default YAML serialization path.


@given(st.text(max_size=100))
def test_secret_round_trip_requires_explicit_reveal(plaintext):
    key = Fernet.generate_key()
    token = Fernet(key).encrypt(plaintext.encode()).decode()
    cfg = Config({"secret": LazySecret(f"ENC({token})", key=key)})
    assert cfg.to_dict() == {"secret": "<LazySecret>"}
    assert cfg.to_dict(reveal_secrets=True) == {"secret": plaintext}


@given(st.integers(min_value=1, max_value=8), safe_keys)
def test_outside_imports_are_rejected(depth, filename):
    with TemporaryDirectory() as directory:
        base = Path(directory) / "config"
        base.mkdir()
        loader = ConfigLoader(base, "test")
        with pytest.raises(ConfigLoadError, match="Path traversal detected"):
            loader._resolve_import("../" * depth + filename + ".yaml")


@given(safe_keys)
def test_import_symlink_to_outside_file_is_rejected(filename):
    with TemporaryDirectory() as directory:
        root = Path(directory)
        base = root / "config"
        base.mkdir()
        outside = root / "outside.yaml"
        outside.write_text("synthetic: true\n")
        (base / f"imported-{filename}.yaml").symlink_to(outside)
        (base / "application.yaml").write_text(f"imports: [imported-{filename}]\n")
        with pytest.raises(ConfigLoadError, match="Path traversal detected"):
            ConfigLoader(base, "test").load()


@given(st.sampled_from(["..%2foutside.yaml", "．．/outside.yaml", r"..\outside.yaml"]))
def test_encoded_lookalikes_are_literal_in_directory_paths(filename):
    with TemporaryDirectory() as directory:
        base = Path(directory)
        candidate = base / filename
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text("synthetic: true\n")
        resolved = ConfigLoader(base, "test")._resolve_import(filename)
        assert resolved == candidate.resolve()
        assert resolved.is_relative_to(base.resolve())
