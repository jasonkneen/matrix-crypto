"""Refresh cryptocurrency lists from the public CoinGecko API."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import requests

MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"
DEFAULT_FILES = {
    "all": "crypto_list.json",
    "solana": "solana_ecosystem_crypto_list.json",
    "ethereum": "ethereum_ecosystem_crypto_list.json",
}


def fetch_list(ecosystem: str, limit: int) -> list[dict[str, str]]:
    params: dict[str, Any] = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": "false",
    }
    if ecosystem != "all":
        params["category"] = f"{ecosystem}-ecosystem"
    response = requests.get(MARKETS_URL, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list) or not data:
        raise ValueError("CoinGecko returned no coins")
    return [
        {"id": coin["id"], "ticker": coin["symbol"].upper(), "name": coin["name"]}
        for coin in data
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch a cryptocurrency list from CoinGecko"
    )
    parser.add_argument("--ecosystem", choices=DEFAULT_FILES, default="all")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=Path, help="Destination JSON file")
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 250:
        parser.error("--limit must be between 1 and 250")
    output = args.output or Path(DEFAULT_FILES[args.ecosystem])
    try:
        cryptos = fetch_list(args.ecosystem, args.limit)
        output.write_text(
            json.dumps({"cryptos": cryptos}, indent=2) + "\n", encoding="utf-8"
        )
    except (requests.RequestException, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"matrixcrypto-update-list: {exc}", file=sys.stderr)
        return 1
    print(f"Saved {len(cryptos)} cryptocurrencies to {output}")
    return 0
