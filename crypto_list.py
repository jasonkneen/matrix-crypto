"""Legacy source-checkout launcher for refreshing the default list."""

import sys

from matrixcrypto.lists import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
