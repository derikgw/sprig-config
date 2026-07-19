#!/bin/sh
set -eu

BASE_VERSION="$(poetry version -s)"
PIPELINE_NUMBER="${CI_PIPELINE_IID:-${CI_PIPELINE_ID:-}}"

if [ -z "${PIPELINE_NUMBER}" ]; then
    echo "CI_PIPELINE_IID or CI_PIPELINE_ID must be set for TestPyPI branch publishes."
    exit 1
fi

case "${BASE_VERSION}" in
    *.dev*)
        echo "Base version ${BASE_VERSION} already includes a .dev suffix; refusing to stack another dev release."
        exit 1
        ;;
esac

TESTPYPI_VERSION="$(python3 - "${BASE_VERSION}" "${PIPELINE_NUMBER}" <<'PY'
import json
import re
import sys
import urllib.request
from urllib.error import URLError

base_version = sys.argv[1]
pipeline_number = int(sys.argv[2])
version_re = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:\.dev(\d+))?$")


def parse(version: str):
    match = version_re.fullmatch(version)
    if not match:
        return None
    major, minor, patch, dev = match.groups()
    return (int(major), int(minor), int(patch), int(dev) if dev is not None else None)


base_parsed = parse(base_version)
if base_parsed is None or base_parsed[3] is not None:
    print(f"Unsupported base version format: {base_version}", file=sys.stderr)
    sys.exit(1)

base_release = base_parsed[:3]
target_release = base_release
max_dev_for_target = -1

url = "https://test.pypi.org/pypi/sprig-config/json"
try:
    with urllib.request.urlopen(url, timeout=15) as response:
        payload = json.load(response)
except URLError as exc:
    print(
        f"⚠️  Could not query TestPyPI release metadata ({exc}). Falling back to CI run number only.",
        file=sys.stderr,
    )
    print(f"{base_release[0]}.{base_release[1]}.{base_release[2]}.dev{pipeline_number}")
    sys.exit(0)

for raw_version in payload.get("releases", {}):
    parsed = parse(raw_version)
    if parsed is None:
        continue
    release = parsed[:3]
    if release > target_release:
        target_release = release

for raw_version in payload.get("releases", {}):
    parsed = parse(raw_version)
    if parsed is None:
        continue
    release = parsed[:3]
    dev_num = parsed[3]
    if release == target_release and dev_num is not None and dev_num > max_dev_for_target:
        max_dev_for_target = dev_num

if target_release > base_release:
    print(
        "ℹ️  TestPyPI already has a higher base version "
        f"{target_release[0]}.{target_release[1]}.{target_release[2]}; "
        "using that base so this publish sorts as latest.",
        file=sys.stderr,
    )

next_dev = max(pipeline_number, max_dev_for_target + 1)
if max_dev_for_target >= 0 and next_dev != pipeline_number:
    print(
        f"ℹ️  Bumping dev suffix to {next_dev} to stay above existing "
        f"{target_release[0]}.{target_release[1]}.{target_release[2]}.dev{max_dev_for_target}.",
        file=sys.stderr,
    )

print(f"{target_release[0]}.{target_release[1]}.{target_release[2]}.dev{next_dev}")
PY
)"

echo "🔧 Preparing TestPyPI version from base version ${BASE_VERSION}..."
poetry version "${TESTPYPI_VERSION}" >/dev/null
echo "📦 TestPyPI version: $(poetry version -s)"
