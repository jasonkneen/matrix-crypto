import contextlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from matrixcrypto import app, lists


class ConfigTests(unittest.TestCase):
    def test_all_bundled_lists_are_available(self):
        for filename in (
            "crypto_list.json",
            "solana_ecosystem_crypto_list.json",
            "ethereum_ecosystem_crypto_list.json",
            "offline_crypto_list.json",
        ):
            with self.subTest(filename=filename):
                self.assertTrue(app.load_cryptos(filename))

    def test_custom_list_rejects_empty_list(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.json"
            path.write_text('{"cryptos": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "at least one crypto"):
                app.load_cryptos(path)

    def test_main_uses_packaged_list_from_any_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch("matrixcrypto.app.curses.wrapper") as wrapper,
                contextlib.chdir(directory),
            ):
                self.assertEqual(app.main(["--offline"]), 0)
            self.assertTrue(wrapper.called)
            self.assertTrue(wrapper.call_args.args[1])
            self.assertTrue(wrapper.call_args.args[3])


class PriceTests(unittest.TestCase):
    def test_prices_are_formatted_and_missing_ids_remain_unavailable(self):
        cryptos = [
            {"id": "bitcoin", "ticker": "BTC"},
            {"id": "ethereum", "ticker": "ETH"},
            {"id": "missing", "ticker": "MISSING"},
        ]
        response = Mock()
        response.json.return_value = {
            "bitcoin": {"usd": 1234.56},
            "ethereum": {"usd": 12.345},
        }
        with patch("matrixcrypto.app.requests.get", return_value=response) as get:
            self.assertTrue(app.fetch_current_prices(cryptos))
        self.assertEqual(get.call_args.kwargs["timeout"], 20)
        self.assertEqual(cryptos[0]["price"], "1,235")
        self.assertEqual(cryptos[1]["price"], "12.35")
        self.assertNotIn("price", cryptos[2])

    def test_api_error_clears_stale_price(self):
        cryptos = [{"id": "bitcoin", "ticker": "BTC", "price": "10.00"}]
        with patch("matrixcrypto.app.requests.get", side_effect=requests.Timeout):
            self.assertFalse(app.fetch_current_prices(cryptos))
        self.assertNotIn("price", cryptos[0])


class ListUpdaterTests(unittest.TestCase):
    def test_failed_request_does_not_overwrite_list(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "coins.json"
            output.write_text("existing", encoding="utf-8")
            with patch("matrixcrypto.lists.requests.get", side_effect=requests.Timeout):
                self.assertEqual(lists.main(["--output", str(output)]), 1)
            self.assertEqual(output.read_text(encoding="utf-8"), "existing")

    def test_successful_request_writes_selected_ecosystem(self):
        response = Mock()
        response.json.return_value = [
            {"id": "solana", "symbol": "sol", "name": "Solana"}
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "coins.json"
            with patch("matrixcrypto.lists.requests.get", return_value=response) as get:
                self.assertEqual(
                    lists.main(["--ecosystem", "solana", "--output", str(output)]),
                    0,
                )
            self.assertEqual(
                get.call_args.kwargs["params"]["category"], "solana-ecosystem"
            )
            self.assertEqual(
                json.loads(output.read_text())["cryptos"][0]["ticker"], "SOL"
            )


if __name__ == "__main__":
    unittest.main()
