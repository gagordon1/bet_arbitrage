import requests #type: ignore
import json
from typing import TypedDict, Tuple, List, Any
from dateutil import parser #type: ignore
from datetime import datetime, timezone
from OrderBook import OrderBook, Order, OrderbookData
from constants import *
from external_apis.kalshi import KalshiAPI
from dotenv import load_dotenv
import os
import logging

class PolymarketGetMarketsResponse(TypedDict):
    data: List[Any]
    next_cursor: str
    limit: int
    count: int

def is_timezone_aware(dt: datetime) -> bool:
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

def valid_prices(yes_ask : float,
            no_ask : float,
            yes_bid : float,
            no_bid : float) -> bool:
    def convertible_to_float(value : Any) -> bool:
        try:
            float(value)
            return True
        except:
            return False
    
    valid_prices = True
    for price in [yes_ask, no_ask, yes_bid, no_bid]:
        if not convertible_to_float(price):
            valid_prices = False
            break
    return valid_prices

class BinaryMarketMetadata:
    def __init__(self,
        platform : str,
        question : str,
        id : str,
        yes_id : str | None,
        no_id : str | None,
        end_date : datetime
    ): 
        self.platform = platform
        self.question = question
        self.id = id
        self.yes_id = yes_id
        self.no_id = no_id
        self.end_date = end_date
    # Method to convert the object to a JSON-compatible dictionary
    def to_json(self) -> dict:
        return {
            'platform': self.platform,
            'question': self.question,
            'id': self.id,
            'yes_id': self.yes_id,
            'no_id': self.no_id,
            'end_date' : self.end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

    # Method to instantiate a BinaryMarket object from a dictionary
    @classmethod
    def from_json(cls, data):
        return cls(
            platform=data['platform'],
            question=data['question'],
            id=data['id'],
            yes_id=data.get('yes_id'),
            no_id=data.get('no_id'),
            end_date = parser.parse(data.get("end_date")).astimezone(timezone.utc)
        )

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
            end_date : datetime,
            can_close_early : bool | None = None
        ):
        self.platform = platform
        self.question = question
        self.id = id
        self.yes_id = yes_id
        self.no_id = no_id
        self.yes_ask = float(yes_ask)
        self.no_ask = float(no_ask)
        self.yes_bid = float(yes_bid)
        self.no_bid = float(no_bid)
        self.end_date = end_date
        self.can_close_early = can_close_early
    
    def __str__(self) -> str:
        return (f"Platform: {self.platform}, BettingPlatform: {self.platform}\n"
                f"  Yes Bid: {self.yes_bid}, Yes Ask: {self.yes_ask}\n"
                f"  No Bid: {self.no_bid}, No Ask: {self.no_ask}\n")
                # f"  End Date: {self.end_date}")
   
    # Method to convert the object to a JSON-compatible dictionary
    def to_json(self) -> dict:
        return {
            'platform': self.platform,
            'question': self.question,
            'id': self.id,
            'yes_id': self.yes_id,
            'no_id': self.no_id,
            'yes_ask': self.yes_ask,
            'no_ask': self.no_ask,
            'yes_bid': self.yes_bid,
            'no_bid': self.no_bid,
            'end_date' : self.end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'can_close_early' : self.can_close_early
        }

    # Method to instantiate a BinaryMarket object from a dictionary
    @classmethod
    def from_json(cls, data):
        return cls(
            platform=data['platform'],
            question=data['question'],
            id=data['id'],
            yes_id=data.get('yes_id'),
            no_id=data.get('no_id'),
            yes_ask=data.get('yes_ask'),
            no_ask=data.get('no_ask'),
            yes_bid=data.get('yes_bid'),
            no_bid=data.get('no_bid'),
            end_date = parser.parse(data.get("end_date")).astimezone(timezone.utc),
            can_close_early = data.get('can_close_early')
        )
        
class BettingPlatform:
    def get_batch_market_data(self, data : (List[BinaryMarketMetadata] | List[BinaryMarket]) ) -> List[BinaryMarket]:
        """Given a list of binary market metadata objects, returns a list of binary market data objects containing the metadata plus latest market data

        Args:
            data (List[BinaryMarketMetadata]): array of metadata binary markets

        Returns:
            List[BinaryMarket]: array of binary market data containing latest market data
        """
        raise NotImplementedError("Subclasses must implement this method")

    def get_active_markets(self, n: (int | None)) -> List[BinaryMarketMetadata]:
        """Gets active markets for a betting platform

        Args:
            n (int  |  None): optional limit for testing purposes

        Returns:
            List[BinaryMarketMetadata]: active markets in a list
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_orderbooks(self, data : (BinaryMarketMetadata | BinaryMarket)) -> list[OrderBook]:
        """Gets the yes and no orderbooks for a market

        Args:
            data (BinaryMarketMetadata | BinaryMarket): a binary market

        Returns:
            tuple[OrderBook, OrderBook]: yes orderbook, no orderbook
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def save_active_markets(self, filename:str, n: int | None) -> None:
        all_markets = self.get_active_markets(n)
        with open(filename, 'w') as json_file:
            json.dump([a.to_json() for a in all_markets], json_file, indent = 4)

class BookParams(TypedDict):
    token_id : str
    side : str # BUY | SELL

class Polymarket(BettingPlatform):

    def generate_book_params(self, token_ids : List[str]) -> List[BookParams]:
        out : List[BookParams] = []
        for t in token_ids:
            for side in ["BUY", "SELL"]:
                out.append({"token_id" : t, "side" : side})
        return out
    
    def get_orderbooks(self, data : (BinaryMarketMetadata | BinaryMarket)) -> list[OrderBook]:
        #TBU
        
        out = []
        for id in [data.yes_id, data.no_id]:
            params = {
                "token_id" : id
            }
            response = requests.get(POLYMARKET_ENDPOINT + "book", params = params)
            response_dict = json.loads(response.text)
            bids : list[Order] = [{"price" : float(x["price"]), "size" : float(x["size"])} for x in response_dict["bids"]]
            asks  : list[Order] = [{"price" : float(x["price"]), "size" : float(x["size"])} for x in response_dict["asks"]]
            orderbook_data : OrderbookData = {
                "bids" : bids,
                "asks" : asks
            }
            out.append(OrderBook(orderbook_data))

        return out


    def get_prices(self, token_ids : List[str]) -> List[Tuple[float | None,float | None]]:
        out : List[Tuple[float | None, float | None]] = []
        token_batch_size = POLYMARKET_REQUEST_LIMIT // 2
        for i in range(0,len(token_ids), token_batch_size):
            ts = token_ids[i:i+token_batch_size]
            bp = self.generate_book_params(ts)
            response = requests.post(POLYMARKET_ENDPOINT + "prices", json = bp) 
            response_dict = json.loads(response.text)
            for t in ts:
                if t in response_dict:
                    out.append((response_dict[t]["BUY"], response_dict[t]["SELL"]))
                else:
                    out.append((None, None))
        return out

    def get_batch_market_data(self, data : List[BinaryMarketMetadata]) -> List[BinaryMarket]:
        yes_ids : List[str] = [x.yes_id for x in data] #type: ignore 
        no_ids : List[str] = [x.no_id for x in data] #type: ignore
        yes_prices = []
        for i in range(0,len(yes_ids), POLYMARKET_REQUEST_LIMIT):
            ids = yes_ids[i:i+POLYMARKET_REQUEST_LIMIT]
            yes_prices.extend(self.get_prices(ids))

        no_prices = []
        for i in range(0,len(no_ids), POLYMARKET_REQUEST_LIMIT):
            ids = no_ids[i:i+POLYMARKET_REQUEST_LIMIT]
            no_prices.extend(self.get_prices(ids))
        
        out : List[BinaryMarket] = []
        for i in range(len(data)):
            yes_ask = yes_prices[i][1]
            no_ask = no_prices[i][1]
            yes_bid = yes_prices[i][0]
            no_bid = no_prices[i][0]
            if valid_prices(yes_ask, no_ask, yes_bid, no_bid):
                out.append(BinaryMarket(
                    "Polymarket",
                    data[i].question,
                    data[i].id,
                    data[i].yes_id,
                    data[i].no_id,
                    float(yes_ask),
                    float(no_ask),
                    float(yes_bid),
                    float(no_bid),
                    data[i].end_date
                ))
        return out
    
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
                        end_date = parser.parse(market["end_date_iso"]).astimezone(timezone.utc)
                        if question_count == n:
                            return questions
                        #check if end date is after now
                        elif end_date > datetime.now(timezone.utc) and market["condition_id"] != "":
                            tokens = market["tokens"]
                            entry = BinaryMarketMetadata(
                                "Polymarket",
                                market["question"],
                                market["condition_id"],
                                next((t["token_id"] for t in tokens if t["outcome"] == "Yes"),None),
                                next((t["token_id"] for t in tokens if t["outcome"] == "No"),None),
                                end_date
                            )
                            questions.append(entry)
                            question_count += 1
            except KeyError:
                break
        return questions
    
class Kalshi(BettingPlatform):

    def __init__(self, host : str, platform_name : str):
        self.host = host # election endpoint is different
        self.platform_name = platform_name
        load_dotenv()
        kalshi_key_id = os.getenv("KALSHI_API_KEY_ID")
        kalshi_key_file = os.getenv("KALSHI_KEY_FILE")
        self.api = KalshiAPI(kalshi_key_id, kalshi_key_file)
    
    def get_orderbooks(self, data : (BinaryMarketMetadata | BinaryMarket)) -> list[OrderBook]:


        try:
        
            response = self.api.get_market_orderbook(ticker = data.id)
            
            yes_bids_response = response["orderbook"]["yes"]
            no_asks_response = response["orderbook"]["no"]

            yes_orderbook : OrderbookData = {
                "asks" : [{"price" : (100-float(x[0]))/100, "size" : float(x[1])} for x in no_asks_response],
                "bids" : [{"price" : float(x[0])/100, "size" : float(x[1])} for x in yes_bids_response]
            }

            no_orderbook : OrderbookData = {
                "asks" : [{"price" : (100-float(x[0]))/100, "size" : float(x[1])} for x in yes_bids_response],
                "bids" : [{"price" : float(x[0])/100, "size" : float(x[1])} for x in no_asks_response]
            }
            return [OrderBook(yes_orderbook), OrderBook(no_orderbook)]
        except:
            logging.info(f"error retrieving orderbook data for {data.platform} {data.id}")
            return [OrderBook(), OrderBook()] #returns empty orderbook data
        

    def get_batch_market_data(self, data : List[BinaryMarketMetadata]) -> List[BinaryMarket]:
        
        out : List[BinaryMarket] = []
        ids = [x.id for x in data]
        for i in range(0, len(ids), KALSHI_REQUEST_LIMIT):
            batch = ids[i:i+KALSHI_REQUEST_LIMIT]
            response = self.api.get_batch_markets(limit = KALSHI_REQUEST_LIMIT, tickers = batch) 
            markets = response["markets"] 
            for m in markets:
                if valid_prices(m["yes_ask"], m["no_ask"], m["yes_bid"], m["no_bid"]):
                    out.append(
                        BinaryMarket(
                            self.platform_name,
                            m["title"],
                            m["ticker"],
                            None,
                            None,
                            float(m["yes_ask"])/100,
                            float(m["no_ask"])/100,
                            float(m["yes_bid"])/100,
                            float(m["no_bid"])/100,
                            parser.parse(m["expiration_time"]).astimezone(timezone.utc)
                        )
                    )
        return out
    
    def get_active_markets(self, n : int | None) -> List[BinaryMarketMetadata]:
        
        questions : List[BinaryMarketMetadata] = []
        question_count = 0
        cursor = None
        cursors = set()
        while True:
            response = self.api.get_markets(limit = KALSHI_REQUEST_LIMIT,
                                            status="open",
                                            cursor=cursor)
            cursor = response["cursor"] #type: ignore
            markets = response["markets"] #type: ignore
            #stop if cursor encountered twice
            if cursor in cursors:
                break
            else:
                cursors.add(cursor)
            for market in markets:
                
                q = BinaryMarketMetadata(
                    self.platform_name,
                    market["title"],
                    market["ticker"],
                    None,
                    None,
                    parser.parse(market["expiration_time"]).astimezone(timezone.utc)
                )
                questions.append(q)
                question_count += 1
                if question_count == n:
                    return questions
        return questions



if __name__ == "__main__":
    # polymarket = Polymarket()
    # logging.info("Pulling Polymarket markets...")
    # polymarket.save_active_markets("question_data/polymarket_questions.json", None)
    
    # logging.info("Pulling Kalshi markets...")
    # kalshi = Kalshi()
    # kalshi.save_active_markets("question_data/kalshi_questions.json", None)
    # pm = Polymarket()
    # link = pm.get_link("0x9279e0735a365ab5fe94c671e172b9dc68e402fa9dab36db4d8e171785fcf40e")
    # logging.info(link)
    pass