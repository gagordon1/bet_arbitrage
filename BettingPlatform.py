import requests #type: ignore
import json
from typing import TypedDict, Tuple, List, Any
from dateutil import parser #type: ignore
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

POLYMARKET_REQUEST_LIMIT = 500

class PolymarketGetMarketsResponse(TypedDict):
    data: List[Any]
    next_cursor: str
    limit: int
    count: int

def is_timezone_aware(dt: datetime) -> bool:
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

class BinaryMarketMetadata:
    def __init__(self,
        platform : str,
        question : str,
        id : str,
        yes_id : str | None,
        no_id : str | None,
    ): 
        self.platform = platform
        self.question = question
        self.id = id
        self.yes_id = yes_id
        self.no_id = no_id
    # Method to convert the object to a JSON-compatible dictionary
    def to_json(self) -> dict:
        return {
            'platform': self.platform,
            'question': self.question,
            'id': self.id,
            'yes_id': self.yes_id,
            'no_id': self.no_id,
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
        )

class BinaryMarket:
    def __init__(
            self,
            platform : str, 
            question : str, 
            id : str, 
            yes_id : str | None,
            no_id : str | None,
            yes_ask : float | None,
            no_ask : float | None,
            yes_bid : float | None,
            no_bid : float | None,
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
            'no_bid': self.no_bid
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
            no_bid=data.get('no_bid')
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
            out.append(BinaryMarket(
                "Polymarket",
                data[i].question,
                data[i].id,
                data[i].yes_id,
                data[i].no_id,
                yes_prices[i][1],
                no_prices[i][1],
                yes_prices[i][0],
                yes_prices[i][0]
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
                        end_date = parser.parse(market["end_date_iso"]) 
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
                                next((t["token_id"] for t in tokens if t["outcome"] == "No"),None)
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

    def get_batch_market_data(self, data : List[BinaryMarketMetadata]) -> List[BinaryMarket]:
        api, config = self.login_to_kalshi()
        config.host = self.host
        out : List[BinaryMarket] = []
        ids = [x.id for x in data]
        for i in range(0, len(ids), KALSHI_REQUEST_LIMIT):
            batch = ids[i:i+KALSHI_REQUEST_LIMIT]
            response = api.get_markets(limit = KALSHI_REQUEST_LIMIT, tickers = ",".join(batch))
            markets = response.markets
            for m in markets:
                out.append(
                    BinaryMarket(
                        self.platform_name,
                        m.title,
                        m.ticker,
                        None,
                        None,
                        float(m.yes_ask)/100,
                        float(m.no_ask)/100,
                        float(m.yes_bid)/100,
                        float(m.no_bid)/100
                    )
                )
        return out
    
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
                q = BinaryMarketMetadata(
                    self.platform_name,
                    market.title,
                    market.ticker,
                    None,
                    None
                )
                questions.append(q)
                question_count += 1
                if question_count == n:
                    return questions
        return questions

class BetOpportunity:

    def __init__(self, question : str, market_1 : BinaryMarket, market_2 : BinaryMarket, last_update : datetime):
        self.question = question
        self.market_1 = market_1
        self.market_2 = market_2
        self.last_update = last_update

    def __str__(self) -> str:
        return (f"Bet Opportunity on Question: {self.question}\n"
                f"BettingPlatform 1:\n{self.market_1}\n\n"
                f"BettingPlatform 2:\n{self.market_2}\n\n")
    
    def calculate_absolute_return(self, yes_contracts : int, no_contracts : int) -> Tuple[float, float]:
        """calculates the absolute return for the binary market bet opportunity

        Args:
            yes_contracts (int): number of yes contracts to purchase
            no_contracts (int): number of no contracts to purchase

        Raises:
            ValueError: if incomplete data

        Returns:
            Tuple[float, float]: absolute return if market resolves to yes, absolute return if market resolves to no   
        """
        market_1_yes_ask = self.market_1.yes_ask
        market_2_yes_ask = self.market_2.yes_ask
        market_1_no_ask = self.market_1.no_ask
        market_2_no_ask = self.market_2.no_ask
        if market_1_yes_ask and market_2_no_ask and market_1_no_ask and market_2_yes_ask:
            best_yes_price = min(market_1_yes_ask, market_2_yes_ask)
            best_no_price = min(market_1_no_ask, market_2_no_ask)
            investment = best_yes_price*yes_contracts + best_no_price*no_contracts
            return  no_contracts / investment - 1, no_contracts / investment - 1
        else:
            raise ValueError("One or more price data missing")
        
    def to_json(self):
        return {
            'question': self.question,
            'market_1': self.market_1.to_json(),
            'market_2': self.market_2.to_json(),
            'last_update': self.last_update.isoformat()  # Convert datetime to ISO 8601 string
        }

    # Method to instantiate a BetOpportunity object from a dictionary
    @classmethod
    def from_json(cls, data):
        market_1 = BinaryMarket.from_json(data['market_1'])
        market_2 = BinaryMarket.from_json(data['market_2'])
        last_update = datetime.fromisoformat(data['last_update'])  # Convert back to datetime
        return cls(
            question=data['question'],
            market_1=market_1,
            market_2=market_2,
            last_update=last_update
        )

    
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