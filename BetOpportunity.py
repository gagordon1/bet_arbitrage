from datetime import datetime, timezone, timedelta
from BettingPlatform import BinaryMarket
from constants import *
import logging


class BetOpportunity:

    def __init__(self, question : str, market_1 : BinaryMarket, market_2 : BinaryMarket, last_update : datetime, id :str):
        self.question = question
        self.id = id
        self.market_1 = market_1
        self.market_2 = market_2
        self.last_update = last_update
        self.refresh_return_calculations()

    def __str__(self) -> str:
        return (f"Bet Opportunity on Question: {self.question}\n"
                f"BettingPlatform 1:\n{self.market_1}\n\n"
                f"BettingPlatform 2:\n{self.market_2}\n\n")
    
    def refresh_return_calculations(self):
        self.absolute_return  : list[float] = self.calculate_absolute_return(1,1)
        self.annualized_return : list[float | None] = self.calculate_annualized_return(1,1)
    
    def calculate_absolute_return(self, yes_contracts : int, no_contracts : int) -> list[float]:
        """calculates the absolute return for the binary market bet opportunity

        Args:
            yes_contracts (int): number of yes contracts to purchase
            no_contracts (int): number of no contracts to purchase

        Raises:
            ValueError: if incomplete data

        Returns:
            List[float, float]: absolute return if market resolves to yes, absolute return if market resolves to no   
        """
        market_1_yes_ask = self.market_1.yes_ask
        market_2_yes_ask = self.market_2.yes_ask
        market_1_no_ask = self.market_1.no_ask
        market_2_no_ask = self.market_2.no_ask
        best_yes_price = min(market_1_yes_ask, market_2_yes_ask)
        best_no_price = min(market_1_no_ask, market_2_no_ask)
        investment = best_yes_price*yes_contracts + best_no_price*no_contracts
        return  [yes_contracts / investment - 1, no_contracts / investment - 1]  
    
    def calculate_annualized_return(self, yes_contracts : int, no_contracts : int) -> list[float | None]:
        yes_return, no_return = self.calculate_absolute_return(yes_contracts, no_contracts)
        latest_close_time = min(self.market_1.end_date, self.market_2.end_date)  #optimistically uses the earlier of the two markets
        now = datetime.now().astimezone(timezone.utc)
        
        difference = latest_close_time.timestamp() - now.timestamp()
        result = MS_IN_ONE_YEAR / difference
        try:
            yes_return_annualized = (1+yes_return)**result - 1
            no_return_annualized = (1+no_return)**result - 1
        except OverflowError:
            logging.info(f"Overflow error for yes / no return: {yes_return}/{no_return} and annualization exponent of {result}")
            return [None, None]
        if isinstance(yes_return_annualized, complex) or isinstance(yes_return_annualized, complex):
            return [None, None]
        return [yes_return_annualized, no_return_annualized]
    
    def to_json(self):
        return {
            'question': self.question,
            'id' : self.id,
            'market_1': self.market_1.to_json(),
            'market_2': self.market_2.to_json(),
            'absolute_return' : self.absolute_return,
            'annualized_return' : self.annualized_return,
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
            last_update=last_update,
            id = data["id"]
        )