from QuestionData import QuestionData, BetOpportunityOrderBooks
from BetOpportunity import BetOpportunity
from constants import *
from orderbook_returns import get_return_size_aware
import logging

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    # format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
    format="%(levelname)s - %(message)s",  # Log format
)

def sort_bet_opportunities(sort_key : BetOpportunitySortKey, ops : list[BetOpportunity]) -> list[BetOpportunity]:

    def lambda_func(x : BetOpportunity):
        if sort_key == BetOpportunitySortKey.parity_return:
            return sum(x.absolute_return)
        elif sort_key == BetOpportunitySortKey.parity_return_annualized:
            if all([isinstance(y, float) for y in x.annualized_return]):
                return sum(x.annualized_return) #type: ignore
            else:
                return -1
        else: 
            return -1
        
    if sort_key in BET_OPPORTUNITIES_SORT:
        logging.info(sort_key)
        ops.sort( 
            key=lambda_func,
            reverse = True
        )
    return ops

def save_active_question_data_for_all_markets():
    """For all markets in the system, pulls all active question data
    """
    qdata = QuestionData()
    qdata.save_active_markets_to_json()

def generate_and_save_question_map():
    """Using market metadata, generates a map mapping questions to semantically equivalent questions on betting platforms 
    """
    logging.info(f"building question map with question similarity cutoff {SIMILARITY_CUTOFF}")
    qdata = QuestionData()
    qmap = qdata.build_question_map([BETTING_PLATFORM_DATA[x]["question_filepath"] for x in BETTING_PLATFORM_DATA])
    qdata.save_question_map_to_json(qmap, QUESTION_MAP_JSON_BASE_PATH + ACTIVE_MAP_JSON_FILENAME)

def get_bet_opportunities(sort : (BetOpportunitySortKey | None) = None) -> list[BetOpportunity]:
    """Returns current data set of bet opportunities

    Returns:
        list[BetOpportunity]: Current bet opportunities
    """
    qdata = QuestionData()
    ops = qdata.get_bet_opportunities()
    if sort:
        return sort_bet_opportunities(sort, ops)
    else:
        return ops

def refresh_bet_opportunities(sort : BetOpportunitySortKey | None = None, qdata : QuestionData | None = None) -> list[BetOpportunity]:
    """Refreshes bet opportunites with latest non-orderbook aware market data

    Args:
        sort (BetOpportunitySortKey | None, optional): sort key. Defaults to None.
        qdata (QuestionData | None, optional): instantiated question data. Defaults to None.

    Returns:
        list[BetOpportunity]: opportunities, sorted if specified
    """
    logging.info("Refreshing all bet opportunities...")
    if qdata == None:
        qdata = QuestionData()
    updated_data = qdata.get_updated_bet_opportunity_data()
    qdata.save_bet_opportunities(updated_data)
    if sort:
        return sort_bet_opportunities(sort, updated_data)
    else:
        return updated_data

def build_bet_opportunities(llm_check = False, llm_model = LLM.deepseek_v2) -> tuple[list[BetOpportunity], float]:
    """Using the latest question map saved, builds a list of bet opportunities

    Args:
        llm_check (bool, optional): if true, uses a large language model to filter bet opportunities such that every pair of markets have semantically equivalent titles. Defaults to False.

    Returns:
        tuple[list[BetOpportunity], float]: list of bet opportunities and cost of the llm operation
    """
    logging.info("building list of bet opportunities from question map...")
    qdata = QuestionData()
    question_map = qdata.open_question_map_json(QUESTION_MAP_JSON_BASE_PATH + ACTIVE_MAP_JSON_FILENAME)
    bet_opportunities, llm_cost = qdata.get_bet_opportunities_from_question_map(question_map, llm_check=llm_check, llm_model=llm_model)
    qdata.save_bet_opportunities(bet_opportunities)
    return bet_opportunities, llm_cost

def delete_bet_opportunity(id : str) -> tuple[bool, list[BetOpportunity]]:
    """Given an id for a bet opportunity, attempts to delete it

    Args:
        id (str): unique id of the bet opportunity

    Returns:
        tuple[bool, list[BetOpportunity]]: flag for if deleted, list of updated bet opportunities
    """
    qdata = QuestionData()
    return qdata.delete_bet_opportunity(id)

def get_bet_opportunity_orderbooks(id : str) -> tuple[BetOpportunity, BetOpportunityOrderBooks]:
   qdata = QuestionData() 
   bet_opportunity = qdata.get_bet_opportunity(id)
   orderbooks = qdata.get_orderbooks(bet_opportunity)
   return (bet_opportunity, orderbooks)

def get_top_n_opportunities(
        n : int = 20, 
        final_sort = BetOpportunitySortKey.parity_return_orderbook_aware_annualized,
        initial_sort = BetOpportunitySortKey.parity_return) -> list[tuple[BetOpportunity, float]]:
    """Refreshes market data for top n highest return bet opportunite, sorting by final sort
    Algorithm initially sorts by a non-orderbook-aware method as an optimization, then for the top opportunites pulls orderbook
    data for each finding the top n opportunities

    Args:
        n (int, optional): length of opportunities to return. Defaults to 20.
        final_sort (valid sort type, optional): final method to sort on (generally orderbook aware). Defaults to BetOpportunitySortKey.parity_return_orderbook_aware_annualized.
        initial_sort (valid sort type, optional): initial method to sort on (non-orderbook aware optimization). Defaults to BetOpportunitySortKey.parity_return.

    Returns:
        list[BetOpportunity]: list of the top n bet opportunites
    """
    BET_SIZE = 10
    qdata = QuestionData()
    ops = refresh_bet_opportunities(sort=initial_sort, qdata=qdata)
    top_n_ops = ops[:n]
    out : list[tuple[BetOpportunity, float]] = []
    for op in top_n_ops:
        orderbooks = qdata.get_orderbooks(op)
        m1_yes = orderbooks.m1_yes_ob
        m1_no = orderbooks.m1_no_ob
        m2_yes = orderbooks.m2_yes_ob
        m2_no = orderbooks.m2_no_ob
        op_return = get_return_size_aware(BET_SIZE, BET_SIZE, m1_yes, m1_no, m2_yes, m2_no)
        out.append((op, op_return))
    return sorted(out, key= lambda x : x[1], reverse=True)

if __name__ == "__main__":
    # save_active_question_data_for_all_markets()
    # generate_and_save_question_map()
    # ops, cost = build_bet_opportunities(llm_check=True, llm_model = LLM.openai_4o_mini)
    # logging.info(f"LLM cost: ${round(cost,5)}")
    # refresh_bet_opportunities()
    # build_bet_opportunities()
    # refresh_bet_opportunities(sort = BetOpportunitySortKey.parity_return_orderbook_aware)
    top_n = get_top_n_opportunities(n = 100)
    for op, r in top_n:
        market_1_platform = op.market_1.platform
        market_2_platform = op.market_2.platform
        market_1_name = op.market_1.question
        market_2_name = op.market_2.question
        logging.info("-----"*5)
        logging.info(f"Market 1 Platform / Question: {market_1_platform} /  {market_1_name}\nMarket 2 Platform / Question: {market_2_platform} / {market_2_name}\nOrderbook size aware return: {r}")