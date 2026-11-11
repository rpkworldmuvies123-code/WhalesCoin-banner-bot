import unittest
from unittest.mock import patch

import bot


SAMPLE = [
    {"rank": 1, "name": "Bitcoin", "symbol": "BTC", "price": 60000,
     "change": 2.5, "market_cap": 1_000_000, "volume": 100_000},
    {"rank": 2, "name": "Ethereum", "symbol": "ETH", "price": 3000,
     "change": -1.2, "market_cap": 500_000, "volume": 200_000},
    {"rank": 3, "name": "Example", "symbol": "EX", "price": 0.005,
     "change": 12.0, "market_cap": 10_000, "volume": 50_000},
]


class BotLogicTests(unittest.TestCase):
    def test_shayari_is_hindi(self):
        self.assertTrue(any(ord(ch) >= 0x0900 and ord(ch) <= 0x097F for ch in bot.shayari()))

    def test_top_gainers_sorted_by_24h_change(self):
        text = bot.highlight_text("gainers", SAMPLE)
        self.assertLess(text.index("Example"), text.index("Bitcoin"))
        self.assertIn("TOP GAINERS", text)

    def test_trending_is_explicitly_volume_ranked(self):
        text = bot.highlight_text("trending", SAMPLE)
        self.assertLess(text.index("Ethereum"), text.index("Bitcoin"))
        self.assertIn("TOP 10 BY 24H VOLUME", text)

    def test_coin_detail_includes_price_and_change(self):
        detail = bot.coin_detail("BTC", SAMPLE)
        self.assertIn("Bitcoin (BTC)", detail)
        self.assertIn("$60,000.00", detail)
        self.assertIn("+2.50%", detail)

    def test_unknown_coin_returns_none(self):
        self.assertIsNone(bot.coin_detail("NOPE", SAMPLE))

    def test_get_tickers_sorts_and_limits_to_top_50(self):
        payload = [
            {"rank": i, "name": f"Coin{i}", "symbol": f"C{i}",
             "quotes": {"USD": {"price": 1, "percent_change_24h": 0,
                                "market_cap": 100, "volume_24h": 10}}}
            for i in range(60, 0, -1)
        ]
        with patch.object(bot, "api_get", return_value=payload):
            rows = bot.get_tickers()
        self.assertEqual(len(rows), 50)
        self.assertEqual(rows[0]["rank"], 1)
        self.assertEqual(rows[-1]["rank"], 50)


if __name__ == "__main__":
    unittest.main()
