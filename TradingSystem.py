import time
import logging
from TradingOpportunities import BetDataManager, BetArbitrageAnalyzer
from constants import Strategy
from strategies.arbitrage_1 import ArbitrageV1

STRATEGIES = {
    Strategy.arbitrage_1 : ArbitrageV1
}


logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


class BetTradingSystem:
    """Continuously updates betting data and opportunities."""

    def __init__(self, refresh_interval: int = 300):
        """
        Args:
            refresh_interval (int): How often to refresh opportunities (seconds).
        """
        self.refresh_interval = refresh_interval
        self.refresh_count = 0
        self.data_manager = BetDataManager()
        self.analyzer = BetArbitrageAnalyzer()

    def run(self, strategy : Strategy):
        """Continuously refreshes bet opportunities."""
        while True:
            
            self.run_strategy(strategy)
            time.sleep(self.refresh_interval)  # Wait before next refresh
    
    def run_strategy(self, strategy : Strategy):
        logging.info("Refreshing market data...")
        self.data_manager.refresh_bet_opportunities()
        STRATEGIES[strategy]().run()

if __name__ == "__main__":
    trading_system = BetTradingSystem(refresh_interval=300)  # Refresh every 5 minutes
    # trading_system.run(Strategy.arbitrage_1)
    trading_system.run_strategy(Strategy.arbitrage_1)
