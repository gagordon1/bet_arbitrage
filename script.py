from get_markets import *

markets = {
    "Will Donald Trump win the presidency?": ["PRES-2024-DJT", "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"]
}

for market in markets:
    kalshi_id = markets[market][0]
    polymarket_id = markets[market][1]
    kalshi_market = get_kalshi_market(kalshi_id)
    polymarket_market = get_polymarket_market(polymarket_id)
    print(kalshi_market)
    print(polymarket_market)