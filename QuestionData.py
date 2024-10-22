from typing import List, TypedDict, Literal
import json
from find_overlapping_markets import map_questions_across_platforms, QuestionMap, get_best_match_by_platform
import pandas as pd
from pprint import pprint
from betting_markets import Polymarket, Kalshi, Market, BettingPlaform

class MarketData(TypedDict):
    market: Market
    market_name : Literal["Polymarket", "Kalshi"]
    questions_filepath : str


class QuestionData:

    def __init__(self):
        self.kalshi = Kalshi()
        self.polymarket = Polymarket()
        self.markets : List[MarketData] = [
            {
                "market" : self.kalshi,
                "market_name" : "Kalshi",
                "questions_filepath" : "question_data/kalshi.json"
            },
            {
                "market" : self.polymarket,
                "market_name" : "Polymarket",
                "questions_filepath" : "question_data/polymarket.json"
            }
        ]

    def open_question_map_json(self, json_file : str) -> QuestionMap:
         with open(json_file, 'r') as f:
            question_map: QuestionMap = json.load(f)
            return question_map

    def save_active_markets_to_json(self):
        for marketdata in self.markets:
            print("collecting data for "+ marketdata["market_name"] + " ...")
            market = marketdata["market"]
            market.save_active_markets(marketdata["questions_filepath"], None)

    def build_multiplatform_question_dataset(self, filepaths : List[str], platform_names : List[str], output_file : str):

        questions_by_platform = []
        for i in range(len(filepaths)):
            with open(filepaths[i], "r") as f:
                platform_questions = json.load(f)
                questions_by_platform.append(
                    [platform_names[i], platform_questions]
                )
        cross_platform_matches = map_questions_across_platforms(questions_by_platform)
        print("Mapping all questions across platforms to a semantically unique question...")
        cross_platform_matches = get_best_match_by_platform(cross_platform_matches)
        print("Finding most semantically equivalent question for each platform for each question...")
        with open(output_file, "w") as f:
            json.dump(cross_platform_matches, f, indent=4)

    def json_to_excel(self, json_file: str, excel_file: str):
        """
        Converts a JSON file of QuestionMap to an Excel file.
        
        :param json_file: The path to the JSON file.
        :param excel_file: The path where the Excel file will be saved.
        """
        # Load the JSON file
        question_map = self.open_question_map_json(json_file)

        # Prepare the rows for the Excel file
        rows = []
        count = 0
        # Iterate over the QuestionMap and flatten the structure
        for question, mappings in question_map.items():
            mapping_len = len(mappings)
            if mapping_len > 1:
                count +=1
            for entry in mappings:
                rows.append({
                    'Question': question,
                    'Platform': entry['platform_name'],
                    'Mapped Question': entry['question'],
                    'Question ID': entry['question_id'],
                    'Multi-platform?' : 1 if len(mappings) > 1 else 0
                })

        # Create a DataFrame from the rows
        df = pd.DataFrame(rows)

        # Save the DataFrame to an Excel file
        df.to_excel(excel_file, index=False)
        print("Successful mapping count: " + str(count))
        print(f"Data successfully written to {excel_file}")

if __name__ == "__main__":
    filepaths = [
        "question_data/kalshi.json", 
        "question_data/polymarket.json"
        ]
    platform_names = [
        "Kalshi", 
        "Polymarket"
        ]
    
    json_output_file = "overlapping_market_data/overlapping_market_data.json"
    excel_output_file = "overlapping_market_data/overlapping_market_data.xlsx"

    qdata = QuestionData()
    # qdata.save_active_markets_to_json()
    qdata.build_multiplatform_question_dataset(filepaths, platform_names, json_output_file)
    qdata.json_to_excel(json_output_file, excel_output_file)