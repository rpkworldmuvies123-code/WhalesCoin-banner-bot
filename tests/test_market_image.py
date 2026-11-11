import os
import unittest
from PIL import Image

from market_image import build_caption, render_highlight, select_top_five


ROWS = [
    {"name":"Bitcoin","symbol":"BTC","price":60000,"change":-0.3,"volume":900},
    {"name":"Quack AI","symbol":"QUACK","price":0.2,"change":269.5,"volume":500},
    {"name":"Ethereum","symbol":"ETH","price":3000,"change":-0.2,"volume":800},
    {"name":"Quantus","symbol":"QNT","price":1.2,"change":3.5,"volume":700},
    {"name":"Pudgy Penguins","symbol":"PENGU","price":0.04,"change":-0.6,"volume":600},
    {"name":"Solana","symbol":"SOL","price":140,"change":1.0,"volume":400},
]


class MarketImageTests(unittest.TestCase):
    def test_trending_is_volume_ranked_and_limited_to_five(self):
        chosen = select_top_five("trending", ROWS)
        self.assertEqual(len(chosen), 5)
        self.assertEqual(chosen[0]["symbol"], "BTC")

    def test_gainers_is_change_ranked_and_limited_to_five(self):
        chosen = select_top_five("gainers", ROWS)
        self.assertEqual(len(chosen), 5)
        self.assertEqual(chosen[0]["symbol"], "QUACK")

    def test_render_creates_1600_by_900_png(self):
        path = render_highlight("trending", ROWS)
        try:
            with Image.open(path) as image:
                self.assertEqual(image.size, (1600, 900))
                self.assertEqual(image.format, "PNG")
        finally:
            os.unlink(path)

    def test_caption_mentions_data_source_and_disclaimer(self):
        caption = build_caption("trending", ROWS)
        self.assertIn("CoinPaprika", caption)
        self.assertIn("not financial advice", caption)


if __name__ == "__main__":
    unittest.main()
