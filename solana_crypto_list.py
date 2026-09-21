"""Legacy source-checkout launcher for refreshing the Solana list."""

import sys

from matrixcrypto.lists import main

if __name__ == "__main__":
    raise SystemExit(main(["--ecosystem", "solana", *sys.argv[1:]]))
