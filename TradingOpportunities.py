import logging
from QuestionData import QuestionData, BetOpportunityOrderBooks
from BetOpportunity import BetOpportunity
from constants import *


logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


class BetDataManager:
    """Handles data collection and bet opportunity construction."""

    def __init__(self):
        self.qdata = QuestionData()

    def save_active_question_data_for_all_markets(self):
        """Fetches all active question data from the system."""
        self.qdata.save_active_markets_to_json()

    def generate_and_save_question_map(self):
        """Creates a mapping of equivalent questions across betting platforms."""
        logging.info(f"Building question map with similarity cutoff {SIMILARITY_CUTOFF}")
        qmap = self.qdata.build_question_map(
            [BETTING_PLATFORM_DATA[x]["question_filepath"] for x in BETTING_PLATFORM_DATA]
        )
        self.qdata.save_question_map_to_json(qmap, QUESTION_MAP_JSON_BASE_PATH + ACTIVE_MAP_JSON_FILENAME)

    def build_bet_opportunities(self, llm_check=False, llm_model=LLM.deepseek_v2) -> tuple[list[BetOpportunity], float]:
        """Builds bet opportunities using the latest question map."""
        logging.info("Building bet opportunities from question map...")
        question_map = self.qdata.open_question_map_json(QUESTION_MAP_JSON_BASE_PATH + ACTIVE_MAP_JSON_FILENAME)
        bet_opportunities, llm_cost = self.qdata.get_bet_opportunities_from_question_map(
            question_map, llm_check=llm_check, llm_model=llm_model
        )
        self.qdata.save_bet_opportunities(bet_opportunities)
        return bet_opportunities, llm_cost

    def refresh_bet_opportunities(self) -> list[BetOpportunity]:
        """Refreshes bet opportunities with the latest market data."""
        logging.info("Refreshing all bet opportunities...")
        updated_data = self.qdata.get_updated_bet_opportunity_data()
        self.qdata.save_bet_opportunities(updated_data)
        return updated_data


class BetArbitrageAnalyzer:
    """Handles sorting, ranking, and retrieving actionable bet opportunities."""

    def __init__(self):
        self.qdata = QuestionData()

    def sort_bet_opportunities(
        self, sort_key: BetOpportunitySortKey, ops: list[BetOpportunity], n: int | None = None
    ) -> list[BetOpportunity]:
        """Sorts bet opportunities based on a given metric."""
        def lambda_func(x: BetOpportunity):
            if sort_key == BetOpportunitySortKey.parity_return:
                return sum(x.absolute_return)
            elif sort_key == BetOpportunitySortKey.parity_return_annualized:
                if all(isinstance(y, float) for y in x.annualized_return):
                    return sum(x.annualized_return)  # type: ignore
                return -1
            return -1

        if sort_key in BET_OPPORTUNITIES_SORT:
            logging.info(f"Sorting by {sort_key}")
            ops.sort(key=lambda_func, reverse=True)

        return ops[:n] if n else ops

    def get_bet_opportunities(self, sort: BetOpportunitySortKey | None = None) -> list[BetOpportunity]:
        """Returns the latest bet opportunities."""
        ops = self.qdata.get_bet_opportunities()
        return self.sort_bet_opportunities(sort, ops) if sort else ops

    def get_bet_opportunity_orderbooks(self, bet_id: str) -> tuple[BetOpportunity, BetOpportunityOrderBooks]:
        """Retrieves orderbooks for a given bet opportunity."""
        bet_opportunity = self.qdata.get_bet_opportunity(bet_id)
        orderbooks = self.qdata.get_orderbooks(bet_opportunity)
        return bet_opportunity, orderbooks
    
    def get_orderbooks(self, bet_opportunity : BetOpportunity) -> BetOpportunityOrderBooks:
        return self.qdata.get_orderbooks(bet_opportunity)

    def delete_bet_opportunity(self, bet_id: str) -> tuple[bool, list[BetOpportunity]]:
        """Deletes a bet opportunity by ID."""
        return self.qdata.delete_bet_opportunity(bet_id)


if __name__ == "__main__":
    # **Step 1: Data Setup**
    data_manager = BetDataManager()
    # data_manager.save_active_question_data_for_all_markets()
    # data_manager.generate_and_save_question_map()
    bet_ops, cost = data_manager.build_bet_opportunities(llm_check=True, llm_model=LLM.openai_4o )
    logging.info(f"LLM cost: ${round(cost, 5)}")

    # **Step 2: Get Actionables**
    # analyzer = BetArbitrageAnalyzer()
    # top_n = analyzer.get_top_n_opportunities(n=50)

    # for op, r in top_n:
    #     if r > 1:
    #         logging.info("-----" * 5)
    #         logging.info(
    #             f"Market 1 Platform / Question: {op.market_1.platform} / {op.market_1.question}\n"
    #             f"Market 2 Platform / Question: {op.market_2.platform} / {op.market_2.question}\n"
    #             f"Orderbook size aware return: {r}"
            # )
    pass