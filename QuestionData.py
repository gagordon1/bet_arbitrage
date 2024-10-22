from typing import List, TypedDict, Literal
import json
from find_overlapping_markets import map_questions_across_platforms, QuestionEntry, QuestionMap, get_best_match_by_platform
import pandas as pd
from pprint import pprint
from betting_markets import Polymarket, Kalshi, MarketData, BetOpportunity, BinaryMarket, KALSHI_ELECTION_ENDPOINT, KALSHI_NON_ELECTION_ENDPOINT

class QuestionData:

    def __init__(self):
        self.kalshi = Kalshi(host = KALSHI_NON_ELECTION_ENDPOINT, platform_name="Kalshi")
        self.kalshi_election = Kalshi(host = KALSHI_ELECTION_ENDPOINT, platform_name= "Kalshi-Election")
        self.polymarket = Polymarket()
        self.markets : List[MarketData] = [
            {
                "market" : self.kalshi,
                "market_name" : "Kalshi",
                "questions_filepath" : "question_data/kalshi.json"
            },
            {
                "market" : self.kalshi_election,
                "market_name" : "Kalshi-Election",
                "questions_filepath" : "question_data/kalshi_election.json"
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

    def get_market(self, platform_name : str, question_id : str) -> BinaryMarket | None:
        for marketdata in self.markets:
            if marketdata["market_name"] == platform_name:
                return marketdata["market"].get_market(question_id)
            
    # Function to save the list of BetOpportunity objects to JSON
    def save_bet_opportunities_to_json(self, bet_opportunities: List[BetOpportunity], file_name: str) -> None:
        with open(file_name, 'w') as f:
            json.dump(bet_opportunities, f, indent=4)
            print(f"Bet opportunities saved to {file_name}")
    
    def read_bet_opportunities_from_json(self, json_file: str) -> List[BetOpportunity]:
        with open(json_file, 'r') as f:
            bet_opportunities = json.load(f)
        return bet_opportunities

    # Function to save the list of BetOpportunity objects to Excel
    def save_bet_opportunities_to_excel(self, bet_opportunities: List[BetOpportunity], excel_file: str) -> None:
        rows = []

        # Flatten the BetOpportunity objects into rows for Excel
        for bet in bet_opportunities:
            rows.append(bet.to_dict())

        # Convert to DataFrame and save to Excel
        df = pd.DataFrame(rows)
        df.to_excel(excel_file, index=False)
        print(f"Bet opportunities saved to {excel_file}")

    def get_bet_opportunities(self, question_map: QuestionMap, n : (int | None) = None) -> List[BetOpportunity]: 
        """
        Given a question map pulls market data for each question across platforms

        :param question_map: a question map object
        """
        bet_opportunities : List[BetOpportunity]= []
        count = 0
        for question in question_map:
            question_entries = question_map[question]
            #check if market exists across multiple platforms
            if len(question_entries) > 1:
                for i in range(len(question_entries)):
                    for j in range(i+1, len(question_entries)):
                        market_1_entry : QuestionEntry = question_entries[i]
                        market_2_entry : QuestionEntry = question_entries[j]
                        try:
                            market_1 = self.get_market(market_1_entry["platform_name"], market_1_entry["question_id"])
                            market_2 = self.get_market(market_2_entry["platform_name"], market_2_entry["question_id"])
                            if market_1 and market_2:
                                bet_opportunity = BetOpportunity(question, market_1, market_2)
                                bet_opportunities.append(bet_opportunity)
                                count +=1
                                print(str(bet_opportunity) + "\n" + "---"*10)
                                if n != None and count == n:
                                    # for testing
                                    return bet_opportunities
                        except:
                            print("Could not get market data for question " + question)
        return bet_opportunities

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
    # qdata.build_multiplatform_question_dataset(filepaths, platform_names, json_output_file)
    # qdata.question_map_json_to_excel(json_output_file, excel_output_file)
    print("opening question map...")
    question_map = qdata.open_question_map_json(json_output_file)
    print("retrieving bet opportunities...")
    bet_opportunities = qdata.get_bet_opportunities(question_map)
    print("saving bet opportunities as json...")
    qdata.save_bet_opportunities_to_json(bet_opportunities, bet_opportunities_output_file)
    # qdata.save_bet_opportunities_to_excel(bet_opportunities, bet_opportunities_output_excel_file)
    # pprint(bet_opportunities)