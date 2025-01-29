POLYMARKET_ENDPOINT = "https://clob.polymarket.com/"

KALSHI_ENDPOINT = "https://api.elections.kalshi.com/trade-api/v2"

KALSHI_REQUEST_LIMIT = 100

POLYMARKET_REQUEST_LIMIT = 500

SIMILARITY_CUTOFF = .85

BETTING_PLATFORM_DATA = {
        "Kalshi" : {
            "question_filepath" :  "question_data/kalshi.json",
        }, 
        "Polymarket" : {
            "question_filepath" : "question_data/polymarket.json",
        },  
}

QUESTION_MAP_JSON_BASE_PATH = "question_map_data/"

ACTIVE_MAP_JSON_FILENAME = "active.json"

BET_OPPORTUNITIES_JSON_PATH = "bet_opportunity_data/"

ACTIVE_BET_OPPORTUNITIES_JSON_FILENAME = "active.json"

PARITY_RETURN_SORT = "parity_return"

PARITY_RETURN_ANNUALIZED_SORT ="parity_return_annualized"

BET_OPPORTUNITIES_SORT = {PARITY_RETURN_SORT, PARITY_RETURN_ANNUALIZED_SORT}

PREDICTIT_HOST = "https://www.predictit.org/api/marketdata/"

MS_IN_ONE_YEAR = 365*24*60*60