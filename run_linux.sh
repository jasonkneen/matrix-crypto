#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PYTHON_BIN="${MATRIX_CRYPTO_PYTHON:-python3}"
if ! "${PYTHON_BIN}" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
    if [[ -z "${MATRIX_CRYPTO_PYTHON:-}" ]] && command -v python3.12 >/dev/null 2>&1; then
        PYTHON_BIN=python3.12
    fi
fi
if ! "${PYTHON_BIN}" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
    echo "Python 3.12 or newer is required." >&2
    exit 1
fi

if [[ ! -d venv ]]; then
    "${PYTHON_BIN}" -m venv venv
elif ! venv/bin/python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
    echo "Existing venv uses an older Python. Remove it and rerun this script." >&2
    exit 1
fi

venv/bin/python -m pip install -e .
exec venv/bin/matrixcrypto "$@"
