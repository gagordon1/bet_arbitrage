from typing import List, TypedDict, Dict
import json
from find_overlapping_markets import map_questions_across_platforms, QuestionMap, get_best_match_by_platform
import pandas as pd
from pprint import pprint
from betting_markets import Polymarket, Kalshi, Market, BinaryMarket, BinaryMarketMetadata, BetOpportunity, KALSHI_ELECTION_ENDPOINT, KALSHI_NON_ELECTION_ENDPOINT

class MarketData(TypedDict):
    market: Market
    questions_filepath : str


class QuestionData:

    def __init__(self):
        self.kalshi = Kalshi(host = KALSHI_NON_ELECTION_ENDPOINT, platform_name="Kalshi")
        self.kalshi_election = Kalshi(host = KALSHI_ELECTION_ENDPOINT, platform_name= "Kalshi-Election")
        self.polymarket = Polymarket()
        self.markets : Dict[str , MarketData] = {
            "Kalshi": {
                "market" : self.kalshi,
                "questions_filepath" : "question_data/kalshi.json"
            },
            "Kalshi-Election":{
                "market" : self.kalshi_election,
                "questions_filepath" : "question_data/kalshi_election.json"
            },
            "Polymarket" :{
                "market" : self.polymarket,
                "questions_filepath" : "question_data/polymarket.json"
            }
        }

    def open_question_map_json(self, json_file : str) -> QuestionMap:
         with open(json_file, 'r') as f:
            question_map: QuestionMap = json.load(f)
            return question_map

    def save_active_markets_to_json(self):
        for market_name in self.markets:
            print("collecting data for "+ market_name + " ...")
            market = self.markets[market_name]["market"]
            market.save_active_markets(self.markets[market_name]["questions_filepath"], None)

    def build_multiplatform_question_dataset(self, filepaths : List[str], output_file : str):

        questions_by_platform : List[List[BinaryMarketMetadata]] = []
        for i in range(len(filepaths)):
            with open(filepaths[i], "r") as f:
                platform_questions = json.load(f)
                questions_by_platform.append(
                    platform_questions
                )
        cross_platform_matches = map_questions_across_platforms(questions_by_platform)
        print("Mapping all questions across platforms to a semantically unique question...")
        cross_platform_matches = get_best_match_by_platform(cross_platform_matches)
        print("Finding most semantically equivalent question for each platform for each question...")
        with open(output_file, "w") as f:
            json.dump(cross_platform_matches, f, indent=4)
    
    def read_bet_opportunities_from_json(self, json_file: str) -> List[BetOpportunity]:
        with open(json_file, 'r') as f:
            bet_opportunities = json.load(f)
        return bet_opportunities

    def get_bet_opportunities(self, question_map: QuestionMap, n : (int | None) = None) -> List[BetOpportunity]: 
        """
        Given a question map pulls market data for each question across platforms

        :param question_map: a question map object
        """

        # first get data by platform
        question_metadata_by_platform : Dict[str , List[BinaryMarketMetadata]] = {}

        for _, market_data in question_map.items():
            for market in market_data:
                platform = market["platform"]
                if platform in question_metadata_by_platform:
                    question_metadata_by_platform[platform].append(market)
                else:
                    question_metadata_by_platform[platform]= [market]
        
        question_data_by_platform : Dict[str , List[BinaryMarketMetadata]] = {}

        for platform , question_data in question_metadata_by_platform.items():
            market = self.markets[platform]["market"]
            binary_markets = market.get_batch_markets_by_ids(
                [i["id"] for i in question_data], 
                [i["yes_id"] for i in question_data],
                [i["no_id"] for i in question_data],
            )
        # then match each to it's respective pairs using the question map

        return []

    def question_map_json_to_excel(self, json_file: str, excel_file: str):
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
                    'Platform': entry['platform'],
                    'Mapped Question': entry['question'],
                    'Question ID': entry['id'],
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
        "question_data/kalshi_election.json", 
        "question_data/polymarket.json"
        ]
    platform_names = [
        "Kalshi", 
        "Kalshi-Election",
        "Polymarket"
    ]
    
    json_output_file = "overlapping_market_data/overlapping_market_data.json"
    excel_output_file = "overlapping_market_data/overlapping_market_data.xlsx"

    bet_opportunities_output_file = "bet_opportunities_data/bet_opportunities_10-22-24.json"
    bet_opportunities_output_excel_file = "bet_opportunities_data/bet_opportunities_10-22-24.xlsx"

    qdata = QuestionData()
    # qdata.save_active_markets_to_json()
    # qdata.build_multiplatform_question_dataset(filepaths, json_output_file)
    # qdata.question_map_json_to_excel(json_output_file, excel_output_file)
    data = qdata.open_question_map_json(json_output_file)
    qdata.get_bet_opportunities(data)
    