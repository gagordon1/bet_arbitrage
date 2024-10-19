import requests
import json
from typing import Literal, List
from dateutil import parser
from datetime import datetime

BettingPlaform = Literal["Polymarket", "Kalshi"]

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

def get_kalshi_market(market_id: str) -> BinaryMarket:

    election_ids = {"PRES-2024-DJT", "PRESPARTYMI-24-R", "PRESPARTYPA-24-R", "POPVOTE-24-D", "PRESPARTYNC-24-R", "SENATETX-24-R","PRESPARTYWI-24-R"}
    base_url = "https://trading-api.kalshi.com/trade-api/v2"
    if market_id in election_ids:
        base_url = "https://api.elections.kalshi.com/trade-api/v2/markets/"
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

def get_polymarket_market(market_id: str) -> BinaryMarket:
    polymarket_endpoint = "https://clob.polymarket.com/"
    # get_market information
    response = requests.get(polymarket_endpoint + "markets/" + market_id)
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
            response = requests.get(polymarket_endpoint + "price/", params)
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

class MarketInterface:
    def get_market(self, market_id: str) -> BinaryMarket:
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_markets(self, n: int) -> List[str]:
        raise NotImplementedError("Subclasses must implement this method")

class Polymarket(MarketInterface):

    def get_market(self, market_id:str) -> BinaryMarket:
        return get_polymarket_market(market_id)
    
    def get_markets(self, n : int) -> List[str]:
        raise NotImplementedError("TBU")
    
class Kalshi(MarketInterface):

    def get_market(self, market_id:str) -> BinaryMarket:
        return get_kalshi_market(market_id)
    
    def get_markets(self, n : int) -> List[str]:
        raise NotImplementedError("TBU")

if __name__ == "__main__":
    pass
