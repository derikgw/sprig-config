#!/usr/bin/env python3
import sys
from pathlib import Path
from sprigtools.reqs_to_toml import convert_requirements_to_toml
from urllib.parse import unquote

BASE_OUTPUT_DIR = Path.cwd().resolve()

def safe_output_path(user_input: str) -> Path:
    """
    Resolve a user-supplied output path safely under BASE_OUTPUT_DIR.
    Prevents path traversal and symlink escape.
    """
    decoded = unquote(user_input)

    base = BASE_OUTPUT_DIR
    candidate = (base / decoded).resolve()

    try:
        candidate.relative_to(base)
    except ValueError:
        raise SystemExit("❌ Path traversal detected in --output")

    return candidate

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: reqs_to_toml.py <requirements.txt> [--output <file>]")
        sys.exit(1)

    req_file = Path(sys.argv[1]).resolve()
    if not req_file.is_file():
        raise SystemExit(f"❌ Requirements file not found: {req_file}")

    output_file = None
    if "--output" in sys.argv:
        out_idx = sys.argv.index("--output") + 1
        if out_idx >= len(sys.argv):
            raise SystemExit("❌ --output requires a file path")

        output_file = safe_output_path(sys.argv[out_idx])

    toml_block = convert_requirements_to_toml(req_file)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(toml_block, encoding="utf-8")
        print(f"✅ TOML dev dependencies written to {output_file}")
    else:
        print(toml_block)
