#!/bin/sh
set -eu

if [ -z "${CI_COMMIT_TAG:-}" ]; then
    echo "CI_COMMIT_TAG is not set."
    exit 1
fi

echo "🔍 Checking release tag against pyproject.toml..."
PYPROJECT_VERSION="$(poetry version -s)"
TAG_VERSION="$(printf '%s' "${CI_COMMIT_TAG}" | sed -E 's/^[Vv]//')"
STABLE_VERSION_REGEX='^[0-9]+\.[0-9]+\.[0-9]+$'

echo "📦 pyproject.toml version: ${PYPROJECT_VERSION}"
echo "🏷️ Git tag: ${CI_COMMIT_TAG}"

if ! printf '%s' "${TAG_VERSION}" | grep -Eq "${STABLE_VERSION_REGEX}"; then
    echo "❌ Invalid release tag: ${CI_COMMIT_TAG}. Use a stable semver tag like 1.2.3 or v1.2.3."
    exit 1
fi

if ! printf '%s' "${PYPROJECT_VERSION}" | grep -Eq "${STABLE_VERSION_REGEX}"; then
    echo "❌ pyproject.toml version must be a stable semver (X.Y.Z) for PyPI publish; got ${PYPROJECT_VERSION}."
    exit 1
fi

if [ "${PYPROJECT_VERSION}" != "${TAG_VERSION}" ]; then
    echo "❌ Version mismatch: expected ${PYPROJECT_VERSION} (or v${PYPROJECT_VERSION}), got ${CI_COMMIT_TAG}."
    exit 1
fi
