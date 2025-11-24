# sprigconfig/cli.py

import argparse
import json
import sys
from pathlib import Path

from sprigconfig.config_loader import ConfigLoader
from sprigconfig.exceptions import ConfigLoadError
from sprigconfig.lazy_secret import LazySecret


def _render_pretty_yaml(data):
    """Render YAML using block-style formatting."""
    import yaml
    return yaml.dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )


def _extract_data_for_dump(config, reveal_secrets: bool):
    """
    Convert Config object to a dumpable structure.
    If reveal_secrets=True, LazySecret values are decrypted (unsafe).
    """
    def walk(node):
        if isinstance(node, LazySecret):
            if reveal_secrets:
                return node.get()
            return "ENC(**REDACTED**)"
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(dict(config))  # Config implements dict-like behavior


def run_dump(config_dir: Path, profile: str, reveal_secrets: bool,
             output_file: Path | None, fmt: str):
    """
    Perform the actual dump process.
    """
    try:
        loader = ConfigLoader(config_dir=config_dir, profile=profile)
        config = loader.load()
    except ConfigLoadError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    # Prepare output structure
    output = _extract_data_for_dump(config, reveal_secrets=reveal_secrets)

    if fmt == "json":
        rendered = json.dumps(output, indent=2)
    else:
        rendered = _render_pretty_yaml(output)

    if output_file:
        output_file.write_text(rendered, encoding="utf-8")
        print(f"Config written to {output_file}")
    else:
        print(rendered)


def main():
    parser = argparse.ArgumentParser(
        prog="sprigconfig",
        description="SprigConfig command-line utilities",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ----------------------------------------------------------------------
    # dump command
    # ----------------------------------------------------------------------
    dump = sub.add_parser(
        "dump",
        help="Dump merged configuration for inspection/debugging",
        description=(
            "Load, merge, and pretty-print the final resolved configuration.\n\n"
            "Examples:\n"
            "  sprigconfig dump --config-dir=config --profile=dev\n"
            "  sprigconfig dump --config-dir=config --profile=prod --secrets\n"
            "  sprigconfig dump --config-dir=config --profile=test --output-format=json\n"
            "  sprigconfig dump --config-dir=config --profile=dev --output out.yml\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    dump.add_argument(
        "--config-dir",
        required=True,
        type=Path,
        help="Directory containing application.yml and optional profile overlays",
    )

    dump.add_argument(
        "--profile",
        required=True,
        help="Active profile to load (dev, test, prod, etc.)",
    )

    dump.add_argument(
        "--secrets",
        action="store_true",
        help="Reveal decrypted LazySecret values (UNSAFE!)",
    )

    dump.add_argument(
        "--output",
        type=Path,
        help="Write output to a file instead of stdout",
    )

    dump.add_argument(
        "--output-format",
        choices=["yaml"],
        default="yaml",
        help="Output format (default: yaml)",
    )

    args = parser.parse_args()

    if args.command == "dump":
        run_dump(
            config_dir=args.config_dir,
            profile=args.profile,
            reveal_secrets=args.secrets,
            output_file=args.output,
            fmt=args.output_format,
        )

if __name__ == "__main__":
    main()
