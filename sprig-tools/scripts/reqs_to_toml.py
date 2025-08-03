#!/usr/bin/env python3
import sys
from pathlib import Path
from sprigtools.reqs_to_toml import convert_requirements_to_toml

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: reqs_to_toml.py <requirements.txt> [--output <file>]")
        sys.exit(1)

    req_file = Path(sys.argv[1])
    output_file = None
    if "--output" in sys.argv:
        out_idx = sys.argv.index("--output") + 1
        if out_idx < len(sys.argv):
            output_file = Path(sys.argv[out_idx])

    toml_block = convert_requirements_to_toml(req_file)

    if output_file:
        output_file.write_text(toml_block)
        print(f"✅ TOML dev dependencies written to {output_file}")
    else:
        print(toml_block)
