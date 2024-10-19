from get_markets import *

markets = {
    "Will Donald Trump win the presidency?": ["PRES-2024-DJT", "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"]
}

def get_return(yes_contracts : float, yes_price : float, no_contracts: float, no_price : float) -> tuple[float,float]:
    investment = yes_contracts*yes_price + no_contracts*no_price
    return (yes_contracts / investment, no_contracts / investment)


for market in markets:
    kalshi_id = markets[market][0]
    polymarket_id = markets[market][1]
    kalshi_market = get_kalshi_market(kalshi_id)
    polymarket_market = get_polymarket_market(polymarket_id)
    min_yes_ask = min(kalshi_market.yes_ask, polymarket_market.yes_ask)
    min_no_ask = min(kalshi_market.no_ask, polymarket_market.no_ask)
    max_settle_time = max(kalshi_market.end_date, polymarket_market.end_date)

    returns = get_return(500, min_yes_ask, 1000, min_no_ask)