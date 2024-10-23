import requests
import json
from typing import TypedDict, Literal, List, Any
from dateutil import parser
from datetime import datetime, timezone
from dotenv import load_dotenv # type: ignore
import os
import kalshi_python # type: ignore
from kalshi_python.models import * # type: ignore
from pprint import pprint

POLYMARKET_ENDPOINT = "https://clob.polymarket.com/"

KALSHI_NON_ELECTION_ENDPOINT = "https://trading-api.kalshi.com/trade-api/v2"

KALSHI_ELECTION_ENDPOINT = "https://api.elections.kalshi.com/trade-api/v2"

KALSHI_REQUEST_LIMIT = 100

POLYMARKET_REQUEST_LIMIT = 100

class PolymarketGetMarketsResponse(TypedDict):
    data: List[Any]
    next_cursor: str
    limit: int
    count: int

def is_timezone_aware(dt: datetime) -> bool:
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

class BinaryMarketMetadata(TypedDict):
    platform : str
    question : str
    id : str
    yes_id : str | None
    no_id : str | None

class BinaryMarket:
    def __init__(
            self,
            platform : str, 
            question : str, 
            id : str, 
            yes_id : str | None,
            no_id : str | None,
            yes_ask : float,
            no_ask : float,
            yes_bid : float,
            no_bid : float,
        ):
        self.platform = platform
        self.question = question
        self.id = id
        self.yes_id = yes_id
        self.no_id = no_id
        self.yes_ask = yes_ask
        self.no_ask = no_ask
        self.yes_bid = yes_bid
        self.no_bid = no_bid
        
    
class Market:
    
    def get_batch_markets_by_ids(self, 
                                ids : List[str], 
                                 yes_ids : List[str | None],
                                 no_ids : List[str | None]) -> List[BinaryMarket]:
        raise NotImplementedError("Subclasses must implement this method")

    def get_active_markets(self, n: (int | None)) -> List[BinaryMarketMetadata]:
        raise NotImplementedError("Subclasses must implement this method")
    
    def save_active_markets(self, filename:str, n: int | None) -> None:
        all_markets = self.get_active_markets(n)
        with open(filename, 'w') as json_file:
            json.dump(all_markets, json_file, indent = 4)

class Polymarket(Market):

    def get_batch_markets_by_ids(self, 
                                 ids : List[str], 
                                 yes_ids : List[str | None],
                                 no_ids : List[str | None]) -> List[BinaryMarket]:
        raise NotImplementedError("TBU")
    
    def make_get_markets_request(self, cursor: str) -> PolymarketGetMarketsResponse:
        params = {
            "next_cursor" : cursor,
        }
        url = POLYMARKET_ENDPOINT + "markets"
        response = requests.get(url, params = params)
        response_dict : PolymarketGetMarketsResponse = json.loads(response.text)
        return response_dict
    
    def get_active_markets(self, n : int | None) -> List[BinaryMarketMetadata]:
        cursor = ""
        questions : List[BinaryMarketMetadata] = [] 
        question_count = 0
        while True:
            try:
                response = self.make_get_markets_request(cursor)
                next_cursor = response["next_cursor"]
                cursor = next_cursor
                for market in response["data"]:
                    end_date = market["end_date_iso"]
                    if end_date != None:
                        end_date = parser.parse(market["end_date_iso"]) 
                        if question_count == n:
                            return questions
                        #check if end date is after now
                        elif end_date > datetime.now(timezone.utc) and market["condition_id"] != "":
                            tokens = market["tokens"]
                            entry : BinaryMarketMetadata = {
                                "platform" : "Polymarket",
                                "question" : market["question"],
                                "id" : market["condition_id"],
                                "yes_id" : next((t["token_id"] for t in tokens if t["outcome"] == "Yes"),None),
                                "no_id" : next((t["token_id"] for t in tokens if t["outcome"] == "No"),None)
                            } 
                            questions.append(entry)
                            question_count += 1
            except KeyError:
                break
        return questions
    
class Kalshi(Market):

    def __init__(self, host : str, platform_name : str):
        self.host = host # election endpoint is different
        self.platform_name = platform_name

    def get_batch_markets_by_ids(self, 
                                 ids : List[str], 
                                 yes_ids : List[str | None],
                                 no_ids : List[str | None]) -> List[BinaryMarket]:
        raise NotImplementedError("TBU")
    
    def login_to_kalshi(self):
        load_dotenv()
        config = kalshi_python.Configuration()
        config.host = KALSHI_NON_ELECTION_ENDPOINT
        kalshi_api = kalshi_python.ApiInstance(
            email=os.getenv("KALSHI_EMAIL"),
            password=os.getenv("KALSHI_PASSWORD"),
            configuration=config,
        )
        kalshi_api.auto_login_if_possible()
        return kalshi_api, config
    
    def get_active_markets(self, n : int | None) -> List[BinaryMarketMetadata]:
        
        kalshi_api, config = self.login_to_kalshi()
        questions : List[BinaryMarketMetadata] = []
        question_count = 0
        config.host = self.host
        cursor = None
        cursors = set()
        while True:
            response = kalshi_api.market_api.get_markets(limit=KALSHI_REQUEST_LIMIT, status = "open", cursor = cursor)
            cursor = response.cursor
            markets = response.markets
            #stop if cursor encountered twice
            if cursor in cursors:
                break
            else:
                cursors.add(cursor)
            for market in markets:
                q : BinaryMarketMetadata = {
                    "platform" : self.platform_name,
                    "question" : market.title,
                    "id" : market.ticker,
                    "yes_id" : None,
                    "no_id" : None
                }
                questions.append(q)
                question_count += 1
                if question_count == n:
                    return questions
        return questions

class BetOpportunity:

    def __init__(self, question : str, market_1 : BinaryMarket, market_2 : BinaryMarket):
        self.question = question
        self.market_1 = market_1
        self.market_2 = market_2

    def __str__(self) -> str:
        return (f"Bet Opportunity on Question: {self.question}\n"
                f"Market 1:\n{self.market_1}\n\n"
                f"Market 2:\n{self.market_2}\n\n"
                f"Est. Return: {self.calculate_return()}")
    
    def calculate_return(self) -> float:
        best_yes_price = min(self.market_1.yes_ask, self.market_2.yes_ask)
        best_no_price = min(self.market_1.no_ask, self.market_2.no_ask)
        # assumes buys 1 yes contract and 1 no contract
        investment = best_yes_price + best_no_price
        return 1 / investment - 1
    
    def calculate_orderbook_aware_return(self, investment : float) -> float:
        #TBU
        return 0.0

if __name__ == "__main__":
    # polymarket = Polymarket()
    # print("Pulling Polymarket markets...")
    # polymarket.save_active_markets("question_data/polymarket_questions.json", None)
    
    # print("Pulling Kalshi markets...")
    # kalshi = Kalshi()
    # kalshi.save_active_markets("question_data/kalshi_questions.json", None)
    pass