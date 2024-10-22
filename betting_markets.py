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


class PolymarketGetMarketsResponse(TypedDict):
    data: List[Any]
    next_cursor: str
    limit: int
    count: int

def is_timezone_aware(dt: datetime) -> bool:
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

class BinaryMarket:
    def __init__(self, 
                 platform: str,
                 market_name: str, 
                 yes_ask: float, 
                 yes_bid: float, 
                 no_ask: float, 
                 no_bid: float, 
                 end_date : datetime) -> None:
        self.platform = platform
        self.market_name = market_name
        self.yes_bid = yes_bid
        self.yes_ask = yes_ask
        self.no_ask = no_ask
        self.no_bid = no_bid
        self.end_date = end_date

    def __str__(self) -> str:
        return (f"Platform: {self.platform}, Market: {self.market_name}\n"
                f"  Yes Bid: {self.yes_bid}, Yes Ask: {self.yes_ask}\n"
                f"  No Bid: {self.no_bid}, No Ask: {self.no_ask}\n"
                f"  End Date: {self.end_date}")
    
class Market:
    def get_market(self, market_id: str) -> BinaryMarket:
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_active_markets(self, n: (int | None)) -> List[List]:
        raise NotImplementedError("Subclasses must implement this method")
    
    def save_active_markets(self, filename:str, n: int | None) -> None:
        all_markets = self.get_active_markets(n)
        with open(filename, 'w') as json_file:
            json.dump(all_markets, json_file, indent = 4)

class Polymarket(Market):

    def get_market(self, market_id:str) -> BinaryMarket:
        # get_market information
        response = requests.get(POLYMARKET_ENDPOINT + "markets/" + market_id)
        response_dict = json.loads(response.text)
        name = response_dict["question"]
        end_date = response_dict["end_date_iso"]
        
        tokens = response_dict["tokens"]
        yes_token = next((t["token_id"] for t in tokens if t["outcome"] == "Yes"),None)
        no_token = next((t["token_id"] for t in tokens if t["outcome"] == "No"),None)
        # get best bid and ask
        price_data = []
        for token in [yes_token, no_token]:
            for side in ["SELL", "BUY"]:
                params = {
                "token_id":token,
                "side": side
                }
                response = requests.get(POLYMARKET_ENDPOINT + "price/", params)
                response_dict = json.loads(response.text)
                price_data.append(response_dict["price"])

        return BinaryMarket(
            platform="Polymarket",
            market_name = name,
            yes_ask=float(price_data[0]),
            yes_bid= float(price_data[1]),
            no_ask= float(price_data[2]),
            no_bid= float(price_data[3]),
            end_date=parser.parse(end_date)
        )
    
    def get_active_markets(self, n : int | None) -> List[List]:
        def make_request(cursor: str) -> PolymarketGetMarketsResponse:
            url = POLYMARKET_ENDPOINT + "markets?next_cursor=" + cursor
            response = requests.get(url)
            response_dict : PolymarketGetMarketsResponse = json.loads(response.text)
            return response_dict
    
        cursor = ""
        questions : List[List] = [] 
        question_count = 0
        while True:
            try:
                response = make_request(cursor)
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
                            entry = [market["question"], market["condition_id"]]
                            questions.append(entry)
                            question_count += 1
            except KeyError:
                break
        return questions
    
class Kalshi(Market):

    def __init__(self, host : str, platform_name : str):
        self.host = host # election endpoint is different
        self.platform_name = platform_name

    def get_market(self, market_id:str) -> BinaryMarket:
        base_url = self.host
        url = base_url + "/markets/" + market_id
        headers = {"accept": "application/json"}
        response = requests.get(url, headers=headers)
        response_dict = json.loads(response.text)
        market = response_dict["market"]
        return BinaryMarket(
            platform=self.platform_name,
            market_name = market["title"],
            yes_ask=float(market["yes_ask"])/100,
            yes_bid=float(market["yes_bid"])/100,
            no_ask=float(market["no_ask"])/100,
            no_bid=float(market["no_bid"])/100,
            end_date=parser.parse(market["expected_expiration_time"])
        )
    
    def get_active_markets(self, n : int | None) -> List[List]:
        load_dotenv()
        questions = []
        config = kalshi_python.Configuration()

        #use non election endpoint to login
        config.host = KALSHI_NON_ELECTION_ENDPOINT
        kalshi_api = kalshi_python.ApiInstance(
            email=os.getenv("KALSHI_EMAIL"),
            password=os.getenv("KALSHI_PASSWORD"),
            configuration=config,
        )
        kalshi_api.auto_login_if_possible()
        question_count = 0
       
        config.host = self.host
        cursor = None
        cursors = set()
        while True:
            response = kalshi_api.market_api.get_markets(limit=100, status = "open", cursor = cursor)
            cursor = response.cursor
            markets = response.markets
            #stop if cursor encountered twice
            if cursor in cursors:
                break
            else:
                cursors.add(cursor)
            for market in markets:
                questions.append([market.title, market.ticker])
                question_count += 1
                if question_count == n:
                    return questions
        return questions

class MarketData(TypedDict):
    market: Market
    market_name : str
    questions_filepath : str

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
    
    def to_dict(self) -> dict[str, str | float]:
        return {
            "Question": self.question,
            "Market 1 Platform": self.market_1.platform,
            "Market 1 Name": self.market_1.market_name,
            "Market 1 Yes Ask": self.market_1.yes_ask,
            "Market 1 Yes Bid": self.market_1.yes_bid,
            "Market 1 No Ask": self.market_1.no_ask,
            "Market 1 No Bid": self.market_1.no_bid,
            "Market 1 End Date": self.market_1.end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "Market 2 Platform": self.market_2.platform,
            "Market 2 Name": self.market_2.market_name,
            "Market 2 Yes Ask": self.market_2.yes_ask,
            "Market 2 Yes Bid": self.market_2.yes_bid,
            "Market 2 No Ask": self.market_2.no_ask,
            "Market 2 No Bid": self.market_2.no_bid,
            "Market 2 End Date": self.market_2.end_date.strftime("%Y-%m-%d %H:%M:%S")
        }
    
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
