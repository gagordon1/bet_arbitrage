from QuestionData import QuestionData
from BettingPlatform import BetOpportunity
from constants import *
from datetime import datetime

def pull_active_question_data_for_all_markets():
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

def get_bet_opportunities() -> list[BetOpportunity]:
    """Returns current data set of bet opportunities

    Returns:
        list[BetOpportunity]: Current bet opportunities
    """
    qdata = QuestionData()
    return qdata.read_bet_opportunities_from_json(BET_OPPORTUNITIES_JSON_PATH+ ACTIVE_BET_OPPORTUNITIES_JSON_FILENAME)

def refresh_bet_opportunities() -> list[BetOpportunity]:
    """For existing bet opportunities, refreshes market data, updates database

    Returns:
        list[BetOpportunity]: array of bet opportunities with refreshed market data
    """
    qdata = QuestionData()
    active_bet_ops_file = BET_OPPORTUNITIES_JSON_PATH+ ACTIVE_BET_OPPORTUNITIES_JSON_FILENAME
    updated_data = qdata.get_updated_bet_opportunity_data(active_bet_ops_file)
    qdata.save_bet_opportunities_to_json(updated_data, active_bet_ops_file)
    return updated_data

def build_bet_opportunities() -> list[BetOpportunity]:
    """Reads the latest question map data and generates bet opportunites, saving the updated and returning the data

    Returns:
        list[BetOpportunity]: list of bet opportunities
    """
    qdata = QuestionData()
    question_map = qdata.open_question_map_json(QUESTION_MAP_JSON_BASE_PATH + ACTIVE_MAP_JSON_FILENAME)
    bet_opportunities = qdata.get_bet_opportunities_from_question_map(question_map)
    qdata.save_bet_opportunities_to_json(bet_opportunities, BET_OPPORTUNITIES_JSON_PATH+ ACTIVE_BET_OPPORTUNITIES_JSON_FILENAME)
    return bet_opportunities

if __name__ == "__main__":
    # pull_latest_question_data_for_all_markets()
    # generate_and_save_question_map()
    refresh_bet_opportunities()
    # build_bet_opportunities()
    