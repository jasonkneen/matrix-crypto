"""Legacy source-checkout launcher for refreshing the Ethereum list."""

import sys

from matrixcrypto.lists import main

if __name__ == "__main__":
    raise SystemExit(main(["--ecosystem", "ethereum", *sys.argv[1:]]))
