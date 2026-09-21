# Matrix Crypto

Matrix Crypto fills a terminal with falling cryptocurrency tickers and USD prices. Prices come from CoinGecko's public API. An offline mode displays tickers without making network requests. No API key or `.env` file is required to run the app.

![Matrix Crypto terminal display](https://raw.githubusercontent.com/bigsk1/matrix-crypto/main/img/matrix.png)

## Requirements

- Python 3.12 or newer
- A terminal with color support
- Network access for live prices; offline mode works without it

On Windows, the `windows-curses` dependency is installed automatically.

## Install

Install from [PyPI](https://pypi.org/project/matrixcrypto/) in a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install matrixcrypto
matrixcrypto
```

On Windows, use `py -3.12 -m venv .venv`, activate with `.venv\Scripts\activate`, then run `python -m pip install matrixcrypto` and `matrixcrypto`.

With uv:

```bash
uv venv --python 3.12
uv pip install matrixcrypto
source .venv/bin/activate
matrixcrypto
```

Press any key, including Ctrl+C, to exit.

## Commands

| Command | Purpose |
| --- | --- |
| `matrixcrypto` | Show tickers with live USD prices. |
| `matrixcrypto-offline` | Show tickers without fetching prices. |
| `matrixcrypto-update-list` | Save a current coin list from CoinGecko. |

Examples:

```bash
matrixcrypto --bg-color red --crypto-color yellow --eth
matrixcrypto --solana
matrixcrypto --offline
matrixcrypto-offline
matrixcrypto --config ./my-cryptos.json
```

`--bg-color` and `--crypto-color` accept `red`, `green`, `blue`, `yellow`, `cyan`, `magenta`, and `white`. The `--solana` and `--eth` options select bundled ecosystem lists. Run `matrixcrypto --help` for all options.

The app requests prices about every 75 seconds. If a coin has no current price, or CoinGecko rate-limits a request, the display shows `N/A` until a later request succeeds.

## Custom coin lists

Pass a JSON file with `--config` to choose the displayed coins:

```json
{
  "cryptos": [
    {"id": "bitcoin", "ticker": "BTC", "name": "Bitcoin"},
    {"id": "ethereum", "ticker": "ETH", "name": "Ethereum"}
  ]
}
```

Each `id` is a CoinGecko coin ID. The package includes default, Solana, Ethereum, and offline lists. The offline default contains 12 tickers; a custom list can contain any supported coins.

Bundled lists are snapshots from the release date. To generate a current list in the working directory:

```bash
matrixcrypto-update-list --ecosystem all --output crypto_list.json
matrixcrypto-update-list --ecosystem solana --output solana.json
matrixcrypto-update-list --ecosystem ethereum --output ethereum.json
matrixcrypto --config ./crypto_list.json
```

The updater defaults to 20 coins; `--limit` changes that number. If an API request fails, the updater leaves the existing output file unchanged.

## Run from source

```bash
git clone https://github.com/bigsk1/matrix-crypto.git
cd matrix-crypto
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
matrixcrypto
```

The repository also includes `run_linux.sh` and `run_windows.bat`, which create a local virtual environment for a source checkout. The Linux repository installer, `install.sh`, provides the legacy `matrixc` command.

Maintainers can use the [release guide](https://github.com/bigsk1/matrix-crypto/blob/main/RELEASING.md). Matrix Crypto is licensed under [MIT](https://github.com/bigsk1/matrix-crypto/blob/main/LICENSE.md).
