from strategies.TradingStrategy import TradingStrategy
from TradeExecution import TradeExecution
from TradingOpportunities import BetArbitrageAnalyzer
from BetOpportunity import BetOpportunity
from orderbook_returns import get_return_size_aware
from utils import get_annualized_return
from constants import *
import logging

# parameters
MIN_RETURN = .07
N = 200
BET_SIZE = 20

class ArbitrageV1(TradingStrategy):
    def __init__(self):
        self.bet_arbitrage_analyzer = BetArbitrageAnalyzer()
    
    def run(self):
        for op, r in self.get_top_n_opportunities(n=N, bet_size=BET_SIZE):
            annualized_return = get_annualized_return(r, max(op.market_1.end_date,op.market_2.end_date))
            if annualized_return > MIN_RETURN:
                logging.info(
                    f"----------------------------------\n"
                    f"\nMarket 1 Platform / Question: {op.market_1.platform} / {op.market_1.question}"
                    f"\nMarket 2 Platform / Question: {op.market_2.platform} / {op.market_2.question}"
                    f"\nOrderbook size aware return: {r}"
                )
    
    def get_top_n_opportunities(
        self,
        n: int = 20,
        final_sort: BetOpportunitySortKey = BetOpportunitySortKey.parity_return_orderbook_aware_annualized,
        initial_sort: BetOpportunitySortKey = BetOpportunitySortKey.parity_return_annualized,
        bet_size : float  = 100
    ) -> list[tuple[BetOpportunity, float]]:
        """Finds the top N highest-return bet opportunities."""
        top_n_ops = self.bet_arbitrage_analyzer.get_bet_opportunities(sort=initial_sort)[:n]
        out: list[tuple[BetOpportunity, float]] = []

        for op in top_n_ops:
            orderbooks = self.bet_arbitrage_analyzer.get_orderbooks(op)
            m1_yes = orderbooks.m1_yes_ob
            m1_no = orderbooks.m1_no_ob
            m2_yes = orderbooks.m2_yes_ob
            m2_no = orderbooks.m2_no_ob
            op_return = get_return_size_aware(bet_size, bet_size, m1_yes, m1_no, m2_yes, m2_no)
            out.append((op, op_return))

        return sorted(out, key=lambda x: x[1], reverse=True)