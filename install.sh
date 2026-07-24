#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/bigsk1/matrix-crypto.git"
INSTALL_DIR="${MATRIX_CRYPTO_INSTALL_DIR:-${HOME}/.local/share/matrix-crypto}"
BIN_DIR="${HOME}/.local/bin"
COMMAND_NAME="matrixc"

info() {
    echo "==> $*"
}

error() {
    echo "error: $*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Matrix Crypto installer

Usage:
  curl -fsSL https://raw.githubusercontent.com/bigsk1/matrix-crypto/main/install.sh | bash

Environment variables:
  MATRIX_CRYPTO_INSTALL_DIR   Install location (default: ~/.local/share/matrix-crypto)

No API keys are required. Prices come from the free CoinGecko public API.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

if ! command -v git >/dev/null 2>&1; then
    error "git is required. Install it with your package manager (e.g. sudo apt install git)."
fi

if ! command -v python3 >/dev/null 2>&1; then
    error "python3 is required. Install Python 3.8+ with your package manager."
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'; then
    error "Python 3.8 or newer is required."
fi

if ! python3 -c 'import ensurepip' >/dev/null 2>&1; then
    py_version="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    error "python3-venv is required. On Debian/Ubuntu: sudo apt install python${py_version}-venv"
fi

if [[ -d "${INSTALL_DIR}/.git" ]]; then
    info "Updating existing installation in ${INSTALL_DIR}"
    git -C "${INSTALL_DIR}" pull --ff-only
else
    info "Installing Matrix Crypto to ${INSTALL_DIR}"
    mkdir -p "$(dirname "${INSTALL_DIR}")"
    git clone "${REPO_URL}" "${INSTALL_DIR}"
fi

if [[ ! -d "${INSTALL_DIR}/venv" ]]; then
    info "Creating virtual environment"
    python3 -m venv "${INSTALL_DIR}/venv"
fi

info "Installing Python dependencies"
"${INSTALL_DIR}/venv/bin/pip" install --upgrade pip -q
"${INSTALL_DIR}/venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt" -q

mkdir -p "${BIN_DIR}"
cat > "${BIN_DIR}/${COMMAND_NAME}" <<EOF
#!/usr/bin/env bash
INSTALL_DIR="${INSTALL_DIR}"
cd "\${INSTALL_DIR}" || exit 1
exec "\${INSTALL_DIR}/venv/bin/python" matrix_crypto.py "\$@"
EOF
chmod +x "${BIN_DIR}/${COMMAND_NAME}"

info "Installation complete"
echo
echo "Run Matrix Crypto with:"
echo "  ${COMMAND_NAME}"
echo
echo "Examples:"
echo "  ${COMMAND_NAME}"
echo "  ${COMMAND_NAME} --bg-color red --crypto-color yellow --eth"
echo
if [[ ":${PATH}:" != *":${BIN_DIR}:"* ]]; then
    echo "If '${COMMAND_NAME}' is not found, add this to your shell config:"
    echo "  export PATH=\"\${HOME}/.local/bin:\${PATH}\""
    echo
fi
