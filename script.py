from get_markets import *

markets = {
    "Will Donald Trump win the presidency?": ["PRES-2024-DJT", "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"],
    "Will Republicans win Michigan in the Presidential Election?": ["PRESPARTYMI-24-R", "0xbb01eefb24a38a9aa1921ec168d3049e7374b28a2540937d06b3ff2524d66627"],
    "Will Republicans win Pennsylvania in the Presidential Election?": ["PRESPARTYPA-24-R", "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"],
    "Will Kamala Harris win the Popular Vote in Presidential Election 2024?": ["POPVOTE-24-D", "0x265366ede72d73e137b2b9095a6cdc9be6149290caa295738a95e3d881ad0865"],
    "Will Republicans win North Carolina in Presidential Election 2024?": ["PRESPARTYNC-24-R", "0x773f3ca26bdf685da92d2a8a701dd98e4e8b46e0b5366cf09aed9eb8fb6fc189"],
    "Will Republicans win Texas in Senate Race 2024?": ["SENATETX-24-R", "0x9f41292bea56c1a5671306d4285d1912af1a23e62bae6e58e6c0dc517cc98d46"],
}

def get_return(yes_contracts : float, yes_price : float, no_contracts: float, no_price : float) -> tuple[float,float]:
    investment = yes_contracts*yes_price + no_contracts*no_price
    return (round(yes_contracts / investment - 1,3), round(no_contracts / investment - 1, 3))


for market in markets:
    print("---"*10)
    kalshi_id = markets[market][0]
    polymarket_id = markets[market][1]
    kalshi_market = get_kalshi_market(kalshi_id)
    print(kalshi_market)
    polymarket_market = get_polymarket_market(polymarket_id)
    
    print("---"*5)
    print(polymarket_market)
    min_yes_ask = min(kalshi_market.yes_ask, polymarket_market.yes_ask)
    min_no_ask = min(kalshi_market.no_ask, polymarket_market.no_ask)
    max_settle_time = max(kalshi_market.end_date, polymarket_market.end_date)
    returns = get_return(1, min_yes_ask, 1, min_no_ask)
    print("---"*5)
    print(returns)