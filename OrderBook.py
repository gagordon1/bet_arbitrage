from typing import TypedDict

class Order(TypedDict):
    price : float
    size : float

class OrderbookData(TypedDict):
    bids : list[Order] #sorted by price increasing
    asks : list[Order] #sorted by price decreasing

DEFAULT_ORDERBOOK_DATA : OrderbookData = {
    "asks" : [],
    "bids" : []
}

class OrderBook:
    def __init__(self, orderbook_data : OrderbookData = DEFAULT_ORDERBOOK_DATA):
        self.data = self.sort_orderbook_data(orderbook_data)

    def sort_orderbook_data(self, data : OrderbookData) -> OrderbookData:
        asks = data["asks"]
        bids = data["bids"]
        sorted_asks = sorted(asks, key = lambda x : x["price"])
        sorted_bids = sorted(bids, key = lambda x : x["price"], reverse=True)
        return {
            "asks" : sorted_asks,
            "bids" :  sorted_bids
        }

    def get_sorted_asks(self) -> list[Order]:
        return self.data["asks"]
    
    def get_sorted_bids(self) -> list[Order]:
        return self.data["bids"]

    def implied_ask_price(self, amount : float) -> float:
        return 0.0 #TBU

    def implied_bid_price(self, sale_amount : float) -> float:
        return 0.0 #TBU

    def get_best_ask(self) -> Order:
        return self.data["asks"][0]
    
    def get_best_bid(self) -> Order:
        return self.data["bids"][0]
    
    def __str__(self) -> str:
        return str(self.data)
    
    def to_json(self) -> OrderbookData:
        return self.data
    
    @classmethod
    def from_json(cls, data):
        return OrderBook(data)