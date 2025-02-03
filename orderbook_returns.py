from OrderBook import OrderBook, Order
from typing import TypedDict

class Returns(TypedDict):
    yes_contracts : float
    no_contracts : float
    returns : float

def get_effective_price(asks : list[Order], contracts : float) -> float | None:
    """Given an orderbook and a number of contracts to buy, get the effective price.

    Args:
        orderbook (Order): list of sorted orders in increasing price
        contracts (int): number of contracts to buy
    
    Returns: 
        float | None : effective price of the transaction, None if insufficient available asks to complete the transaction
    """
    if len(asks) == 0:
        return None
    else:
        ask = asks[0]
        remaining_asks = asks[1:]
        price, size = ask['price'], ask['size']
        if size >= contracts:
            return price
        remaining_contracts = contracts - size
        effective_price_remaining = get_effective_price(remaining_asks, remaining_contracts)
        if effective_price_remaining == None:
            return None
        else:
            return (price * size + effective_price_remaining * remaining_contracts) / (size + remaining_contracts)
        
def get_max_return(m1: OrderBook, m2 : OrderBook) -> tuple[float, float]:
    """Buying yes contracts on m1 and m2, returns the contract size to get the best return you could achieve.

    Args:
        m1 (OrderBook): orderbook for yes contracts on market 1
        m2 (OrderBook): orderbook for no contracts on market 2

    Returns:
        tuple[float, float]: number of contracts to buy and return
    """
    size = min(m1.get_best_ask()['size'], m2.get_best_ask()['size'])
    price_m1 = m1.get_best_ask()['price']
    price_m2 = m2.get_best_ask()['price']
    return size, 1 / (price_m1 + price_m2)

        
def get_market_return(m1 : OrderBook, m2 : OrderBook, yes_contracts : float, no_contracts : float ) -> float | None:
    """Gets return of two markets. buys yes contracts on first market and no contracts on second market

    Args:
        m1 (OrderBook): market 1 orderbook
        m2 (OrderBook): market 2 orderbook

    Returns:
        float | None: return of the trade, None if error
    """
    m1_yes_ep = get_effective_price(m1.get_sorted_asks(), yes_contracts)
    m2_no_ep = get_effective_price(m2.get_sorted_asks(), no_contracts)
    if m1_yes_ep and m2_no_ep:
        return 1 / (m1_yes_ep + m2_no_ep) - 1
    else:
        return None

def get_return_size_aware(yes_contracts : float, no_contracts : float,
                      market_1_yes_orderbook : OrderBook,
                      market_1_no_orderbook : OrderBook,
                      market_2_yes_orderbook : OrderBook,
                      market_2_no_orderbook : OrderBook
                ) -> float:
    # try buy yes on market 1 and no on market 2
    return_1 = get_market_return(market_1_yes_orderbook, market_2_no_orderbook, yes_contracts, no_contracts)
    # try buy yes on market 2 and no on market 1
    return_2 = get_market_return(market_2_yes_orderbook, market_1_no_orderbook, yes_contracts, no_contracts)
    if return_1 and return_2:
        return max(return_1, return_2)
    elif return_1:
        return return_1
    elif return_2:
        return return_2
    return -1.0

if __name__ == "__main__":
    # orders : list[Order] = [{'price': 0.65, 'size': 50.0}, {'price': 0.67, 'size': 200.0}, {'price': 0.98, 'size': 590.0}, {'price': 0.99, 'size': 7400.0}]
    # contracts = 300.0
    # test_price = (50*.65 + 200*.67 + .98 * 50) / (50 + 200 +50)
    # effective_price = get_effective_price(orders, contracts)
    # logging.info(test_price, effective_price)
    # assert test_price == effective_price
    pass