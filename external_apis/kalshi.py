from kalshi.clients import KalshiHttpClient, Environment
from cryptography.hazmat.primitives import serialization
from typing import TypedDict
from constants import *

class KalshiOrderBookResponse(TypedDict):
    yes : list[list[int]]
    no: list[list[int]]

class KalshiGetMarketOrderbookResponse(TypedDict):
    orderbook : KalshiOrderBookResponse

class KalshiMarketResponse(TypedDict):
    title : str
    ticker : str
    expiration_time : str
    yes_ask : int
    yes_bid : int
    no_ask : int
    no_bid : int
    rules_primary : str

class KalshiGetMarketsResponse(TypedDict):
    cursor : str
    markets : list[KalshiMarketResponse]    

class KalshiAPI:

    def __init__(self, kalshi_api_key_id : str | None, kalshi_key_file : str | None):
        if not kalshi_api_key_id:
            raise Exception("kalshi key id not set.")
        if kalshi_key_file:
            with open(kalshi_key_file, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None  # Provide the password if your key is encrypted
                )
        else:        
            raise Exception(f"Error loading kalshi private key")
        
        self.client = KalshiHttpClient(key_id = kalshi_api_key_id, 
                                  private_key=private_key, #type:ignore
                                  environment=Environment.PROD)
    
    def get_market_orderbook(self, ticker : str) -> KalshiGetMarketOrderbookResponse:

        path = f"{self.client.markets_url}/{ticker}/orderbook"
        response : KalshiGetMarketOrderbookResponse = self.client.get(path)
        orderbook = response["orderbook"]
        out: KalshiGetMarketOrderbookResponse ={
            "orderbook" : {
                "yes" :[],
                "no" : []
            }
        }
        for side in ["no", "yes"]:
            if orderbook[side]:
                out["orderbook"][side] = orderbook[side]
        return out

    def get_markets(self, limit : int, status : str, cursor : str | None) -> KalshiGetMarketsResponse:
        response : KalshiGetMarketsResponse = self.client.get(self.client.markets_url, params ={
                "limit" : limit,
                "status" : status,
                "cursor" : cursor
            }) 
        return response 
    
    def get_batch_markets(self, limit : int, tickers : list[str]):
        response : KalshiGetMarketsResponse = self.client.get(self.client.markets_url, params ={
                "limit" : limit,
                "tickers" : ",".join(tickers)
            }) 
        return response

    
