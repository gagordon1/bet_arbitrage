from typing import TypedDict
import json
from QuestionMap import QuestionMap
import pandas as pd #type: ignore
from BettingPlatform import Polymarket, Kalshi, BettingPlatform, BinaryMarket, BinaryMarketMetadata
from datetime import datetime, timezone
from OrderBook import OrderBook
from constants import *
from BetOpportunity import BetOpportunity
from SemanticEquivalence import filter_bet_opportunities_with_llm_semantic_equivalence, BetOpportunityTitles
import uuid

class MarketData(TypedDict):
    betting_platform: BettingPlatform
    questions_filepath : str

BET_OPPORTUNITIES_FILE = BET_OPPORTUNITIES_JSON_PATH+ ACTIVE_BET_OPPORTUNITIES_JSON_FILENAME

class BetOpportunityOrderBooks:
    def __init__(self, 
                market_1_yes_orderbook : OrderBook,
                market_1_no_orderbook : OrderBook,
                market_2_yes_orderbook : OrderBook,
                market_2_no_orderbook : OrderBook):
        self.m1_yes_ob = market_1_yes_orderbook
        self.m1_no_ob = market_1_no_orderbook
        self.m2_yes_ob = market_2_yes_orderbook
        self.m2_no_ob = market_2_no_orderbook

    def to_json(self):
        return {
            "market_1_yes_orderbook" : self.m1_yes_ob.to_json(),
            "market_1_no_orderbook" : self.m1_no_ob.to_json(),
            "market_2_yes_orderbook" : self.m2_yes_ob.to_json(),
            "market_2_no_orderbook" : self.m2_no_ob.to_json()
        }
    

class QuestionData:

    def __init__(self):
        kalshi = Kalshi(host = KALSHI_ENDPOINT, platform_name= "Kalshi")
        polymarket = Polymarket()
        self.betting_platforms : dict[str , MarketData] = {
            "Kalshi":{
                "betting_platform" : kalshi,
                "questions_filepath" : BETTING_PLATFORM_DATA["Kalshi"]["question_filepath"]
            },
            "Polymarket" :{
                "betting_platform" : polymarket,
                "questions_filepath" : BETTING_PLATFORM_DATA["Polymarket"]["question_filepath"]
            }
        }

    def open_question_map_json(self, json_file : str) -> QuestionMap:
         with open(json_file, 'r') as f:
            question_map_json = json.load(f)
            return QuestionMap.from_json(question_map_json)

    def delete_bet_opportunity(self, id : str) -> tuple[bool, list[BetOpportunity]]:
        bet_opportunities = self.get_bet_opportunities()
        to_delete_index = None
        for i in range(len(bet_opportunities)):
            if bet_opportunities[i].id == id:
                to_delete_index = i
                break
        
        if to_delete_index != None:
            bet_opportunities.pop(to_delete_index)
            self.save_bet_opportunities(bet_opportunities)
            return True, bet_opportunities
        else:
            return False, bet_opportunities

    def save_active_markets_to_json(self):
        """For each platform in the data set, gets all active markets and saves them lists of binary market metadata
        """
        for market_name in self.betting_platforms:
            print("collecting data for "+ market_name + " ...")
            market = self.betting_platforms[market_name]["betting_platform"]
            market.save_active_markets(self.betting_platforms[market_name]["questions_filepath"], None)

    def read_binary_market_metadata_json(self, filepath : str ) -> list[BinaryMarketMetadata]:
        with open(filepath, "r") as json_file:
            metadata = json.load(json_file)
            return [BinaryMarketMetadata.from_json(m) for m in metadata]

    def build_question_map(self, filepaths : list[str]) -> QuestionMap:
        """Given a list of filepaths representing where arrays of binary market metadata are stored, uses nlp
            to map each unique question across all platforms to a list of markets that are semantically equivalent 

        Args:
            filepaths (list[str]): list of filepaths to binary markets

        Returns:
            QuestionMap: maps each unique question across platforms to a list of markets that are semantically equivalent
        """
        questions_by_platform : list[list[BinaryMarketMetadata]] = []
        for filepath in filepaths:
            platform_questions = self.read_binary_market_metadata_json(filepath)
            questions_by_platform.append(platform_questions)
        
        qmap = QuestionMap()
        qmap.map_questions_across_platforms(questions_by_platform)
        print("Mapping all questions across platforms to a semantically unique question...")
        qmap.get_best_match_by_platform()
        print("Finding most semantically equivalent question for each platform for each question...")
        return qmap
    
    def save_question_map_to_json(self, question_map : QuestionMap, filepath : str) -> None:
        with open(filepath, 'w') as f:
            json.dump(question_map.to_json(), f, indent = 4)

    def get_bet_opportunities(self) -> list[BetOpportunity]:
        json_file = BET_OPPORTUNITIES_FILE
        with open(json_file, 'r') as f:
            bet_opportunities = json.load(f)
            return [BetOpportunity.from_json(bo) for bo in bet_opportunities]

    def get_bet_opportunities_from_question_map(self, question_map: QuestionMap, n : (int | None) = None, llm_check = False) -> tuple[list[BetOpportunity], float]: 
        """Given a QuestionMap, gets a list of bet opportunities

        Args:
            question_map (QuestionMap): maps normalized, unique questions across all platforms to a list of semantically equivalent binary markets across platforms
            n (int  |  None, optional): limit for testing Defaults to None.

        Returns:
            list[BetOpportunity]: a list of bet opportunities containing latest market information for two markets
        """
        # first get data by platform
        question_metadata_by_platform : dict[str , list[BinaryMarketMetadata]] = {}

        for _, market_data in question_map.items():
            for market in market_data:
                platform = market.platform
                if platform in question_metadata_by_platform:
                    question_metadata_by_platform[platform].append(market)
                else:
                    question_metadata_by_platform[platform]= [market]
        
        question_data_by_platform : dict[str , list[BinaryMarket]] = {}
        for platform , question_data in question_metadata_by_platform.items():
            market = self.betting_platforms[platform]["betting_platform"]
            binary_markets = market.get_batch_market_data(question_data)
            question_data_by_platform[platform] = binary_markets

        # convert to unique ids mapping to object to optimize
        id_to_question_map : dict[str, BinaryMarket] = {}
        for _, question_data in question_data_by_platform.items():
            for q in question_data: 
                id_to_question_map[q.id] = q

        # then match each to its respective pairs using the question map
        out : list[BetOpportunity] = []
        for q, similar_questions in question_map.items():
            if len(similar_questions) > 1:
                for i in range(len(similar_questions)):
                    for j in range(i+1, len(similar_questions)):           
                        mdata1 = similar_questions[i]
                        mdata2 = similar_questions[j]
                        if mdata1.id in id_to_question_map and mdata2.id in id_to_question_map:
                            updated_market_1 = id_to_question_map[mdata1.id]
                            updated_market_2 = id_to_question_map[mdata2.id]
                            bo_id = str(uuid.uuid4())
                            out.append(
                                BetOpportunity(
                                    q,
                                    updated_market_1,
                                    updated_market_2,
                                    datetime.now(timezone.utc),
                                    bo_id
                                )
                            )
        # check market title equivalence
        if llm_check:
            # further guarantee name semantic equivalence using an LLM
            print("filtering for semantic equivalence via llm...")
            titles : list[BetOpportunityTitles] = [{"id" : x.id, 
                    "market_1_question" : x.market_1.question, 
                    "market_2_question" : x.market_2.question} for x in out]
            valid_ids, llm_cost = filter_bet_opportunities_with_llm_semantic_equivalence(bet_opportunities=titles)
            return list(filter(lambda x: x.id in valid_ids, out)), llm_cost
        return out, 0.0

    def get_updated_bet_opportunity_data(self) -> list[BetOpportunity]:
        """Given the path to a bet opportunities json file, 
            - reads it
            - refreshes it with latest market data
            - returns as a list of bet opportunities 

        Args:
            bet_opportunities_file (str): path to a json file containing the bet opportunities

        Returns:
            list[BetOpportunity]: updated bet opportunities with latest market data
        """
        bet_opportunities = self.get_bet_opportunities()

        binary_market_by_platform : dict[str, list[BinaryMarket]] = {}

        # organize markets by platform
        for bo in bet_opportunities:
            for binary_market in [bo.market_1, bo.market_2]:
                platform = binary_market.platform
                if platform in binary_market_by_platform:
                    binary_market_by_platform[platform].append(binary_market)
                else:
                    binary_market_by_platform[platform] = [binary_market]
        
        #map each market id to its updated market 
        updated_market_map : dict[str, BinaryMarket] = {}
        for platform in binary_market_by_platform:
            binary_markets = binary_market_by_platform[platform]
            updated_markets = self.betting_platforms[platform]["betting_platform"].get_batch_market_data(binary_markets)
            for m in updated_markets:
                updated_market_map[m.id] = m

        out : list[BetOpportunity] = []
        for bo in bet_opportunities:
            market_id_1 = bo.market_1.id
            market_id_2 = bo.market_2.id
            #only add if both updatedfe
            if market_id_1 in updated_market_map and market_id_2 in updated_market_map:
                bo.market_1 = updated_market_map[market_id_1]
                bo.market_2 = updated_market_map[market_id_2]
                bo.last_update = datetime.now(timezone.utc)
                bo.refresh_return_calculations()
                out.append(bo)
            elif market_id_1 in updated_market_map:
                print("Could not get market date for platform {} market {}".format(bo.market_2.platform, market_id_2))
            elif market_id_2 in updated_market_map:
                print("Could not get market date for platform {} market {}".format(bo.market_1.platform, market_id_1))
            else:
                print("Could not get market data for question {}".format(bo.question))
        return out
    
    def save_bet_opportunities(self, bet_opportunities : list[BetOpportunity]) -> None:
        to_save = [bo.to_json() for bo in bet_opportunities]
        filepath = BET_OPPORTUNITIES_FILE
        with open(filepath, "w") as json_file:
            json.dump(to_save, json_file, indent = 4)
        print(f"Bet opportunities saved to {filepath}")

    def get_bet_opportunity(self, id : str) -> BetOpportunity:
        return [x for x in self.get_bet_opportunities() if x.id == id].pop(0)
    
    def get_orderbooks(self, bet_opportunity : BetOpportunity) -> BetOpportunityOrderBooks:
        m1_platform = bet_opportunity.market_1.platform
        m2_platform = bet_opportunity.market_2.platform
        m1_yes_orderbook, m1_no_orderbook = self.betting_platforms[m1_platform]["betting_platform"].get_orderbooks(bet_opportunity.market_1)
        m2_yes_orderbook, m2_no_orderbook = self.betting_platforms[m2_platform]["betting_platform"].get_orderbooks(bet_opportunity.market_2)

        return BetOpportunityOrderBooks(
            m1_yes_orderbook,
            m1_no_orderbook,
            m2_yes_orderbook,
            m2_no_orderbook,
        )

if __name__ == "__main__":
    # qdata = QuestionData()
    # qdata.save_active_markets_to_json()
    pass