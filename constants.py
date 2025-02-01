from enum import Enum
from typing import TypedDict

POLYMARKET_ENDPOINT = "https://clob.polymarket.com/"

KALSHI_ENDPOINT = "https://api.elections.kalshi.com/trade-api/v2"

KALSHI_REQUEST_LIMIT = 100

POLYMARKET_REQUEST_LIMIT = 500

SIMILARITY_CUTOFF = .70

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

class LLM(str,Enum):
    openai_4o_mini = "gpt-4o-mini"
    openai_4o = "gpt-4o"
    openai_o1 = "o1-preview"
    openai_o1_mini = "o1-mini"
    deepseek_r1 = "deepseek-reasoner"
    deepseek_v2 = "deepseek-chat"

class LLMInfoDict(TypedDict):
    base_url : str
    model_name : str
    api_key_name : str
    cost_per_1m_input_tokens : float
    cost_per_1m_output_tokens : float

LLM_INFO : dict[Enum, LLMInfoDict] = {
    LLM.deepseek_r1 : {
        "base_url" : "https://api.deepseek.com",
        "model_name" : "deepseek-reasoner", 
        "api_key_name" : "DEEPSEEK_API_KEY",
        "cost_per_1m_input_tokens" : .14,
        "cost_per_1m_output_tokens" : .55
    },
    LLM.deepseek_v2 : {
        "base_url" : "https://api.deepseek.com",
        "model_name" : "deepseek-chat", 
        "api_key_name" : "DEEPSEEK_API_KEY",
        "cost_per_1m_input_tokens" : .014,
        "cost_per_1m_output_tokens" : .14
    },
    LLM.openai_4o : {
        "base_url" : "https://api.openai.com/v1/",
        "model_name" : "gpt-4o", 
        "api_key_name" : "OPENAI_API_KEY",
        "cost_per_1m_input_tokens" : 2.5,
        "cost_per_1m_output_tokens" : 10.0
    },
    LLM.openai_4o_mini : {
        "base_url" : "https://api.openai.com/v1/",
        "model_name" : "gpt-4o-mini", 
        "api_key_name" : "OPENAI_API_KEY",
        "cost_per_1m_input_tokens" : .15,
        "cost_per_1m_output_tokens" : .6
    }

}

class BetOpportunitySortKey(str, Enum):
    parity_return = "parity return"
    parity_return_annualized = "parity return annualized"
    parity_return_orderbook_aware = "parity return orderbook aware"
    parity_return_orderbook_aware_annualized = "parity return orderbook aware annualized"
