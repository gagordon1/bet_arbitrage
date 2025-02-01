import unittest
from typing import TypedDict
from OrderBook import Order
from orderbook_returns import get_effective_price

class TestEffectivePrice(unittest.TestCase):
    def test_empty_orderbook(self):
        """Test that an empty orderbook returns None."""
        self.assertIsNone(get_effective_price([], 50))

    def test_single_order_large(self):
        """Test a single order that exceeds the required contracts returns its price."""
        asks : list[Order] = [{"price": 10.0, "size": 100}]
        self.assertEqual(get_effective_price(asks, 50), 10.0)

    def test_single_order_exact(self):
        """Test a single order exactly equal to the required contracts returns its price.
        """
        asks : list[Order] = [{"price": 10.0, "size": 50}]
        self.assertEqual(get_effective_price(asks, 50), 10.0)

    def test_multiple_orders(self):
        """Test that the effective price is computed as the weighted average when multiple orders are used.
        
        Example: Two orders:
          - Order 1: price=10, size=30
          - Order 2: price=12, size=30
        For 40 contracts: use full first order (30 contracts at 10)
        and 10 contracts from second order (10 contracts at 12)
        Expected effective price = (10*30 + 12*10) / 40 = (300 + 120) / 40 = 10.5
        """
        asks : list[Order] = [
            {"price": 10.0, "size": 30},
            {"price": 12.0, "size": 30}
        ]
        self.assertEqual(get_effective_price(asks, 40), 10.5)

    def test_insufficient_orders(self):
        """Test that if the total available size is insufficient, the function returns None."""
        asks: list[Order] = [{"price": 10.0, "size": 20}]
        self.assertIsNone(get_effective_price(asks, 50))

    def test_exact_multiple_orders(self):
        """Test a case with multiple orders that exactly meet the required contracts.
        
        Example: Two orders:
          - Order 1: price=10, size=30
          - Order 2: price=12, size=20
        For 50 contracts: expected effective price = (10*30 + 12*20) / 50 = 10.8
        """
        asks : list[Order] = [
            {"price": 10.0, "size": 30},
            {"price": 12.0, "size": 20}
        ]
        self.assertEqual(get_effective_price(asks, 50), 10.8)

if __name__ == "__main__":
    unittest.main()
