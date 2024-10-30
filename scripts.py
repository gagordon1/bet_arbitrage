from QuestionData import QuestionData, BetOpportunityOrderBooks
from BetOpportunity import BetOpportunity
from constants import *
from datetime import datetime
from pprint import pprint

def sort_bet_opportunities(sort_key : str, ops : list[BetOpportunity]) -> list[BetOpportunity]:

    def lambda_func(x : BetOpportunity):
        if sort_key == "parity_return":
            return sum(x.absolute_return)
        elif sort_key == "parity_return_annualized":
            if(type(x)==float for x in x.annualized_return):
                return sum(x.annualized_return) #type: ignore
            else:
                return -1
        else:
            return -1
        
    if sort_key in BET_OPPORTUNITIES_SORT:
        print(sort_key)
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
    qdata = QuestionData()
    qmap = qdata.build_question_map([BETTING_PLATFORM_DATA[x]["question_filepath"] for x in BETTING_PLATFORM_DATA])
    qdata.save_question_map_to_json(qmap, QUESTION_MAP_JSON_BASE_PATH + ACTIVE_MAP_JSON_FILENAME)

def get_bet_opportunities(sort : (str | None) = None) -> list[BetOpportunity]:
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

def refresh_bet_opportunities(sort : (str | None) = None) -> list[BetOpportunity]:
    """For existing bet opportunities, refreshes market data, updates database

    Returns:
        list[BetOpportunity]: array of bet opportunities with refreshed market data
    """
    qdata = QuestionData()
    updated_data = qdata.get_updated_bet_opportunity_data()
    qdata.save_bet_opportunities(updated_data)
    if sort:
        return sort_bet_opportunities(sort, updated_data)
    else:
        return updated_data

def build_bet_opportunities() -> list[BetOpportunity]:
    """Reads the latest question map data and generates bet opportunites, saving the updated and returning the data

    Returns:
        list[BetOpportunity]: list of bet opportunities
    """
    qdata = QuestionData()
    question_map = qdata.open_question_map_json(QUESTION_MAP_JSON_BASE_PATH + ACTIVE_MAP_JSON_FILENAME)
    bet_opportunities = qdata.get_bet_opportunities_from_question_map(question_map)
    qdata.save_bet_opportunities(bet_opportunities)
    return bet_opportunities

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

if __name__ == "__main__":
    # save_active_question_data_for_all_markets()
    # generate_and_save_question_map()
    build_bet_opportunities()
    # refresh_bet_opportunities()
    # build_bet_opportunities()
    # pass
    

    
    