"""Terminal animation and optional CoinGecko price updates."""

from __future__ import annotations

import argparse
import curses
import json
import math
import random
import sys
import threading
import time
from importlib import resources
from pathlib import Path
from typing import Any

import requests

SETTINGS = {
    "ANIMATION_SPEED": 0.01,
    "BACKGROUND_PATTERN": (1, 2, 3, 1),
    "BACKGROUND_CHARS": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?/",
    "CRYPTO_DISPLAY_COUNT": 3,
    "CRYPTO_DISPLAY_CHANCE": 0.13,
    "BACKGROUND_COLUMN_LENGTH_RANGE": (0.3, 0.6),
    "CRYPTO_FALL_SPEED_RANGE": (0.12, 0.16),
    "BACKGROUND_CHANGE_CHANCE": 0.5,
    "BACKGROUND_FALL_SPEED_RANGE": (0.06, 0.1),
}

COLOR_MAP = {
    "red": curses.COLOR_RED,
    "green": curses.COLOR_GREEN,
    "blue": curses.COLOR_BLUE,
    "yellow": curses.COLOR_YELLOW,
    "cyan": curses.COLOR_CYAN,
    "magenta": curses.COLOR_MAGENTA,
    "white": curses.COLOR_WHITE,
}

PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"
PRICE_UPDATE_SECONDS = 75


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Matrix-style cryptocurrency terminal display"
    )
    parser.add_argument("--bg-color", choices=COLOR_MAP, default="green")
    parser.add_argument("--crypto-color", choices=COLOR_MAP, default="white")
    parser.add_argument(
        "--config", type=Path, help="Path to a custom cryptocurrency JSON list"
    )
    parser.add_argument(
        "--offline", action="store_true", help="Show tickers without fetching prices"
    )
    ecosystem = parser.add_mutually_exclusive_group()
    ecosystem.add_argument(
        "--solana", action="store_true", help="Use the Solana ecosystem list"
    )
    ecosystem.add_argument(
        "--eth", action="store_true", help="Use the Ethereum ecosystem list"
    )
    return parser.parse_args(argv)


def default_config_name(args: argparse.Namespace, offline: bool) -> str:
    if args.solana:
        return "solana_ecosystem_crypto_list.json"
    if args.eth:
        return "ethereum_ecosystem_crypto_list.json"
    if offline:
        return "offline_crypto_list.json"
    return "crypto_list.json"


def load_cryptos(config: Path | str) -> list[dict[str, Any]]:
    if isinstance(config, Path):
        with config.open(encoding="utf-8") as file:
            data = json.load(file)
    else:
        resource = resources.files("matrixcrypto").joinpath("data", config)
        with resource.open("r", encoding="utf-8") as file:
            data = json.load(file)

    if not isinstance(data, dict) or not isinstance(data.get("cryptos"), list):
        raise TypeError("Configuration must contain a 'cryptos' list")
    cryptos = data["cryptos"]
    if not cryptos or any(
        not isinstance(crypto, dict)
        or not isinstance(crypto.get("id"), str)
        or not isinstance(crypto.get("ticker"), str)
        for crypto in cryptos
    ):
        raise ValueError(
            "Configuration needs at least one crypto with string 'id' and 'ticker'"
        )
    return cryptos


def fetch_current_prices(cryptos: list[dict[str, Any]]) -> bool:
    ids = ",".join(crypto["id"] for crypto in cryptos)
    for crypto in cryptos:
        crypto.pop("price", None)
    try:
        response = requests.get(
            PRICE_URL,
            params={"ids": ids, "vs_currencies": "usd"},
            timeout=20,
        )
        response.raise_for_status()
        prices = response.json()
        if not isinstance(prices, dict):
            return False
        for crypto in cryptos:
            price_data = prices.get(crypto["id"])
            if not isinstance(price_data, dict):
                continue
            price = price_data.get("usd")
            if (
                isinstance(price, (int, float))
                and not isinstance(price, bool)
                and math.isfinite(price)
            ):
                crypto["price"] = f"{price:.2f}" if price < 1000 else f"{price:,.0f}"
        return True
    except (requests.RequestException, ValueError):
        return False


def update_prices_periodically(
    cryptos: list[dict[str, Any]], stop_event: threading.Event
) -> None:
    while not stop_event.is_set():
        fetch_current_prices(cryptos)
        stop_event.wait(PRICE_UPDATE_SECONDS)


def init_color_pairs(bg_color: str, crypto_color: str) -> None:
    curses.start_color()
    try:
        curses.use_default_colors()
        background = -1
    except curses.error:
        background = curses.COLOR_BLACK
    curses.init_pair(1, COLOR_MAP[bg_color], background)
    curses.init_pair(2, curses.COLOR_WHITE, background)
    curses.init_pair(3, COLOR_MAP[crypto_color], background)


class MatrixColumn:
    def __init__(self, height: int) -> None:
        self.height = height
        self.length = max(
            1, int(random.uniform(*SETTINGS["BACKGROUND_COLUMN_LENGTH_RANGE"]) * height)
        )
        self.chars = [
            random.choice(SETTINGS["BACKGROUND_CHARS"]) for _ in range(self.length)
        ]
        self.speed = random.uniform(*SETTINGS["BACKGROUND_FALL_SPEED_RANGE"])
        self.counter = 0.0
        self.top = -self.length

    def update(self, dt: float) -> None:
        self.counter += dt
        if self.counter < self.speed:
            return
        self.counter = 0.0
        self.top += 1
        if self.top >= self.height:
            self.top = -self.length
        if random.random() < SETTINGS["BACKGROUND_CHANGE_CHANCE"]:
            self.chars[random.randrange(self.length)] = random.choice(
                SETTINGS["BACKGROUND_CHARS"]
            )

    def draw(self, stdscr: Any, x: int) -> None:
        for index, char in enumerate(self.chars):
            y = self.top + index
            if 0 <= y < self.height:
                attr = (
                    curses.color_pair(2) | curses.A_BOLD
                    if index == self.length - 1
                    else curses.color_pair(1) | curses.A_DIM
                )
                safe_addstr(stdscr, y, x, char, attr)


class CryptoDisplay:
    def __init__(
        self, crypto: dict[str, Any], x: int, max_y: int, offline: bool
    ) -> None:
        self.crypto = crypto
        self.x = x
        self.y = 0
        self.max_y = max_y
        self.offline = offline
        self.speed = random.uniform(*SETTINGS["CRYPTO_FALL_SPEED_RANGE"])
        self.counter = 0.0

    def update(self, dt: float) -> None:
        self.counter += dt
        if self.counter >= self.speed:
            self.counter = 0.0
            self.y += 1

    def get_display_text(self) -> str:
        ticker = self.crypto["ticker"].upper()
        return (
            ticker if self.offline else f"{ticker} $ {self.crypto.get('price', 'N/A')}"
        )

    def is_offscreen(self) -> bool:
        return self.y >= self.max_y


def safe_addstr(stdscr: Any, y: int, x: int, text: str, attr: int) -> None:
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def build_columns(height: int, width: int) -> list[tuple[int, MatrixColumn]]:
    columns: list[tuple[int, MatrixColumn]] = []
    x = 0
    for index in range(width):
        if x >= width:
            break
        columns.append((x, MatrixColumn(height)))
        x += (
            1
            + SETTINGS["BACKGROUND_PATTERN"][
                index % len(SETTINGS["BACKGROUND_PATTERN"])
            ]
        )
    return columns


def run_screen(
    stdscr: Any, cryptos: list[dict[str, Any]], args: argparse.Namespace, offline: bool
) -> None:
    init_color_pairs(args.bg_color, args.crypto_color)
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)

    stop_event = threading.Event()
    if not offline:
        threading.Thread(
            target=update_prices_periodically, args=(cryptos, stop_event), daemon=True
        ).start()

    height, width = stdscr.getmaxyx()
    columns = build_columns(height, width)
    displays: list[CryptoDisplay] = []
    last_time = time.monotonic()

    try:
        while True:
            now = time.monotonic()
            dt = now - last_time
            last_time = now

            current_size = stdscr.getmaxyx()
            if current_size != (height, width):
                height, width = current_size
                columns = build_columns(height, width)
                displays.clear()

            stdscr.erase()
            for x, column in columns:
                column.update(dt)
                column.draw(stdscr, x)

            for display in displays[:]:
                display.update(dt)
                if display.is_offscreen():
                    displays.remove(display)
                    continue
                for index, char in enumerate(display.get_display_text()):
                    y = display.y + index
                    if y < height:
                        safe_addstr(
                            stdscr,
                            y,
                            display.x,
                            char,
                            curses.color_pair(3) | curses.A_BOLD,
                        )

            if (
                width
                and len(displays) < SETTINGS["CRYPTO_DISPLAY_COUNT"]
                and random.random() < SETTINGS["CRYPTO_DISPLAY_CHANCE"]
            ):
                displays.append(
                    CryptoDisplay(
                        random.choice(cryptos), random.randrange(width), height, offline
                    )
                )

            stdscr.refresh()
            if stdscr.getch() != -1:
                break
            time.sleep(SETTINGS["ANIMATION_SPEED"])
    finally:
        stop_event.set()


def main(argv: list[str] | None = None, *, offline: bool = False) -> int:
    args = parse_args(argv)
    offline = offline or args.offline
    try:
        cryptos = load_cryptos(args.config or default_config_name(args, offline))
    except (OSError, TypeError, ValueError) as exc:
        print(f"matrixcrypto: cannot load cryptocurrency list: {exc}", file=sys.stderr)
        return 1
    try:
        curses.wrapper(run_screen, cryptos, args, offline)
    except KeyboardInterrupt:
        pass
    return 0


def offline_main() -> int:
    return main(offline=True)
