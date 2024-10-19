import requests
import json
from typing import TypedDict, Literal, List, Any
from dateutil import parser
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import kalshi_python
from kalshi_python.models import *
from pprint import pprint


BettingPlaform = Literal["Polymarket", "Kalshi"]

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
                 platform: BettingPlaform,
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
        return (
                "platform: " + self.platform +
                "\nname: "+ self.market_name + 
                "\nyes ask: " + str(self.yes_ask) + 
                "\nno ask: " + str(self.no_ask) + 
                "\nend date: " + str(self.end_date)
                )
    
    
class Market:
    def get_market(self, market_id: str) -> BinaryMarket:
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_active_markets(self, n: int) -> List[List]:
        raise NotImplementedError("Subclasses must implement this method")
    
    def save_active_markets(self, filename:str, n: int) -> None:
        all_markets = self.get_active_markets(n)
        with open(filename, 'w') as json_file:
            json.dump(all_markets, json_file)

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
                        elif end_date > datetime.now(timezone.utc):
                            entry = [market["question"], market["condition_id"]]
                            questions.append(entry)
                            question_count += 1
            except KeyError:
                break
        return questions
    
class Kalshi(Market):

    def get_market(self, market_id:str) -> BinaryMarket:
        election_ids = {"PRES-2024-DJT", "PRESPARTYMI-24-R", "PRESPARTYPA-24-R", "POPVOTE-24-D", "PRESPARTYNC-24-R", "SENATETX-24-R","PRESPARTYWI-24-R"}
        base_url = KALSHI_NON_ELECTION_ENDPOINT
        if market_id in election_ids:
            base_url = KALSHI_ELECTION_ENDPOINT
        url = base_url + market_id
        headers = {"accept": "application/json"}
        response = requests.get(url, headers=headers)
        
        response_dict = json.loads(response.text)
        market = response_dict["market"]
        return BinaryMarket(
            platform="Kalshi",
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
        config.host = KALSHI_NON_ELECTION_ENDPOINT
        kalshi_api = kalshi_python.ApiInstance(
            email=os.getenv("KALSHI_EMAIL"),
            password=os.getenv("KALSHI_PASSWORD"),
            configuration=config,
        )
        kalshi_api.auto_login_if_possible()
        question_count = 0
        for host in [KALSHI_ELECTION_ENDPOINT, KALSHI_NON_ELECTION_ENDPOINT]:
            config.host = host
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
                    print(question_count)
                    if question_count == n:
                        return questions
        return questions

if __name__ == "__main__":
    # polymarket = Polymarket()
    # print("Pulling Polymarket markets...")
    # polymarket.save_active_markets("question_data/polymarket_questions.json", None)
    
    print("Pulling Kalshi markets...")
    kalshi = Kalshi()
    kalshi.save_active_markets("question_data/kalshi_questions.json", None)
    
    
