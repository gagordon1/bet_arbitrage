import json
import pandas as pd
from typing import List
from datetime import datetime

from betting_markets import BinaryMarket, BetOpportunity

# Custom encoder for handling BetOpportunity and BinaryMarket objects
class BetOpportunityEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BinaryMarket):
            return {
                "platform": obj.platform,
                "market_name": obj.market_name,
                "yes_ask": obj.yes_ask,
                "yes_bid": obj.yes_bid,
                "no_ask": obj.no_ask,
                "no_bid": obj.no_bid,
                "end_date": obj.end_date.strftime("%Y-%m-%d %H:%M:%S")  # Excel-friendly format
            }
        if isinstance(obj, BetOpportunity):
            return {
                "question": obj['question'],
                "market_1": obj['market_1'],
                "market_2": obj['market_2']
            }
        return super().default(obj)

# Function to save the list of BetOpportunity objects to Excel
def save_bet_opportunities_to_excel(bet_opportunities: List[BetOpportunity], excel_file: str) -> None:
    rows = []

    # Flatten the BetOpportunity objects into rows for Excel
    for bet in bet_opportunities:
        rows.append({
            "Question": bet["question"],
            "Market 1 Platform": bet["market_1"].platform,
            "Market 1 Name": bet["market_1"].market_name,
            "Market 1 Yes Ask": bet["market_1"].yes_ask,
            "Market 1 Yes Bid": bet["market_1"].yes_bid,
            "Market 1 No Ask": bet["market_1"].no_ask,
            "Market 1 No Bid": bet["market_1"].no_bid,
            "Market 1 End Date": bet["market_1"].end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "Market 2 Platform": bet["market_2"].platform,
            "Market 2 Name": bet["market_2"].market_name,
            "Market 2 Yes Ask": bet["market_2"].yes_ask,
            "Market 2 Yes Bid": bet["market_2"].yes_bid,
            "Market 2 No Ask": bet["market_2"].no_ask,
            "Market 2 No Bid": bet["market_2"].no_bid,
            "Market 2 End Date": bet["market_2"].end_date.strftime("%Y-%m-%d %H:%M:%S"),
        })

    # Convert to DataFrame and save to Excel
    df = pd.DataFrame(rows)
    df.to_excel(excel_file, index=False)
    print(f"Bet opportunities saved to {excel_file}")

# Example usage
if __name__ == "__main__":
    pass
