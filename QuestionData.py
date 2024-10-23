from typing import List, TypedDict, Dict
import json
from QuestionMap import QuestionMap
import pandas as pd #type: ignore
from pprint import pprint
from BettingPlatform import Polymarket, Kalshi, BettingPlatform, BinaryMarket, BinaryMarketMetadata, BetOpportunity, KALSHI_ELECTION_ENDPOINT, KALSHI_NON_ELECTION_ENDPOINT
from datetime import datetime

class MarketData(TypedDict):
    betting_platform: BettingPlatform
    questions_filepath : str


class QuestionData:

    def __init__(self):
        self.kalshi = Kalshi(host = KALSHI_NON_ELECTION_ENDPOINT, platform_name="Kalshi")
        self.kalshi_election = Kalshi(host = KALSHI_ELECTION_ENDPOINT, platform_name= "Kalshi-Election")
        self.polymarket = Polymarket()
        self.betting_platforms : Dict[str , MarketData] = {
            "Kalshi": {
                "betting_platform" : self.kalshi,
                "questions_filepath" : "question_data/kalshi.json"
            },
            "Kalshi-Election":{
                "betting_platform" : self.kalshi_election,
                "questions_filepath" : "question_data/kalshi_election.json"
            },
            "Polymarket" :{
                "betting_platform" : self.polymarket,
                "questions_filepath" : "question_data/polymarket.json"
            }
        }

    def open_question_map_json(self, json_file : str) -> QuestionMap:
         with open(json_file, 'r') as f:
            question_map_json = json.load(f)
            return QuestionMap.from_json(question_map_json)

    def save_active_markets_to_json(self):
        for market_name in self.betting_platforms:
            print("collecting data for "+ market_name + " ...")
            market = self.betting_platforms[market_name]["betting_platform"]
            market.save_active_markets(self.betting_platforms[market_name]["questions_filepath"], None)

    def read_binary_market_metadata_json(self, filepath : str ) -> List[BinaryMarketMetadata]:
        with open(filepath, "r") as json_file:
            metadata = json.load(json_file)
            return [BinaryMarketMetadata.from_json(m) for m in metadata]

    def build_question_map(self, filepaths : List[str]) -> QuestionMap:
        """Given a list of filepaths representing where arrays of binary market metadata are stored, uses nlp
            to map each unique question across all platforms to a list of markets that are semantically equivalent 

        Args:
            filepaths (List[str]): list of filepaths to binary markets

        Returns:
            QuestionMap: maps each unique question across platforms to a list of markets that are semantically equivalent
        """
        questions_by_platform : List[List[BinaryMarketMetadata]] = []
        for filepath in filepaths:
            platform_questions = self.read_binary_market_metadata_json(filepath)
            questions_by_platform.append(platform_questions)
        
        qmap = QuestionMap()
        qmap.map_questions_across_platforms(questions_by_platform)
        print("Mapping all questions across platforms to a semantically unique question...")
        qmap.get_best_match_by_platform()
        print("Finding most semantically equivalent question for each platform for each question...")
        return qmap
    
    def save_question_map_to_json(self, question_map : QuestionMap, filepath : str) -> None:
        with open(filepath, 'w') as f:
            json.dump(question_map.to_json(), f, indent = 4)

    def read_bet_opportunities_from_json(self, json_file: str) -> List[BetOpportunity]:
        with open(json_file, 'r') as f:
            bet_opportunities = json.load(f)
            return [BetOpportunity.from_json(bo) for bo in bet_opportunities]

    def get_bet_opportunities_from_question_map(self, question_map: QuestionMap, n : (int | None) = None) -> List[BetOpportunity]: 
        """Given a QuestionMap, gets a list of bet opportunities

        Args:
            question_map (QuestionMap): maps normalized, unique questions across all platforms to a list of semantically equivalent binary markets across platforms
            n (int  |  None, optional): limit for testing Defaults to None.

        Returns:
            List[BetOpportunity]: a list of bet opportunities containing latest market information for two markets
        """
        # first get data by platform
        question_metadata_by_platform : Dict[str , List[BinaryMarketMetadata]] = {}

        for _, market_data in question_map.items():
            for market in market_data:
                platform = market.platform
                if platform in question_metadata_by_platform:
                    question_metadata_by_platform[platform].append(market)
                else:
                    question_metadata_by_platform[platform]= [market]
        
        question_data_by_platform : Dict[str , List[BinaryMarket]] = {}
        for platform , question_data in question_metadata_by_platform.items():
            market = self.betting_platforms[platform]["betting_platform"]
            binary_markets = market.get_batch_market_data(question_data)
            question_data_by_platform[platform] = binary_markets

        # convert to unique ids mapping to object to optimize
        id_to_question_map : Dict[str, BinaryMarket] = {}
        for _, question_data in question_data_by_platform.items():
            for q in question_data: 
                id_to_question_map[q.id] = q

        # then match each to its respective pairs using the question map
        out : List[BetOpportunity] = []
        for q, similar_questions in question_map.items():
            if len(similar_questions) > 1:
                for i in range(len(similar_questions)):
                    for j in range(i+1, len(similar_questions)):           
                        mdata1 = similar_questions[i]
                        mdata2 = similar_questions[j]
                        out.append(
                            BetOpportunity(
                                q,
                                id_to_question_map[mdata1.id],
                                id_to_question_map[mdata2.id],
                                datetime.utcnow()
                            )
                        )
        return out

    def get_updated_bet_opportunity_data(self, bet_opportunities_file : str) -> List[BetOpportunity]:
        """Given the path to a bet opportunities json file, 
            - reads it
            - refreshes it with latest market data
            - returns as a list of bet opportunities 

        Args:
            bet_opportunities_file (str): path to a json file containing the bet opportunities

        Returns:
            List[BetOpportunity]: updated bet opportunities with latest market data
        """
        bet_opportunities = self.read_bet_opportunities_from_json(bet_opportunities_file)

        binary_market_by_platform : Dict[str, List[BinaryMarket]] = {}

        # organize markets by platform
        for bo in bet_opportunities:
            for binary_market in [bo.market_1, bo.market_2]:
                platform = binary_market.platform
                if platform in binary_market_by_platform:
                    binary_market_by_platform[platform].append(binary_market)
                else:
                    binary_market_by_platform[platform] = [binary_market]
        
        #map each market id to its updated market 
        updated_market_map : Dict[str, BinaryMarket] = {}
        for platform in binary_market_by_platform:
            binary_markets = binary_market_by_platform[platform]
            updated_markets = self.betting_platforms[platform]["betting_platform"].get_batch_market_data(binary_markets)
            for m in updated_markets:
                updated_market_map[m.id] = m

        out : List[BetOpportunity] = []
        for bo in bet_opportunities:
            market_id_1 = bo.market_1.id
            market_id_2 = bo.market_2.id
            #only add if both updatedfe
            if market_id_1 in updated_market_map and market_id_2 in updated_market_map:
                bo.market_1 = updated_market_map[market_id_1]
                bo.market_2 = updated_market_map[market_id_2]
                bo.last_update = datetime.utcnow()
                out.append(bo)
            elif market_id_1 in updated_market_map:
                print("Could not get market date for platform {} market {}".format(bo.market_2.platform, market_id_2))
            elif market_id_2 in updated_market_map:
                print("Could not get market date for platform {} market {}".format(bo.market_1.platform, market_id_1))
            else:
                print("Could not get market data for question {}".format(bo.question))
        return out

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
                    'Platform': entry.platform,
                    'Mapped Question': entry.question,
                    'Question ID': entry.id,
                    'Multi-platform?' : 1 if len(mappings) > 1 else 0
                })

        # Create a DataFrame from the rows
        df = pd.DataFrame(rows)

        # Save the DataFrame to an Excel file
        df.to_excel(excel_file, index=False)
        print("Successful mapping count: " + str(count))
        print(f"Data successfully written to {excel_file}")
     # Function to save the list of BetOpportunity objects to Excel
    
    def save_bet_opportunities_to_json(self, bet_opportunities : List[BetOpportunity], filepath : str) -> None:
        to_save = [bo.to_json() for bo in bet_opportunities]
        with open(filepath, "w") as json_file:
            json.dump(to_save, json_file, indent = 4)
        print(f"Bet opportunities saved to {filepath}")

    def save_bet_opportunities_to_excel(self, bet_opportunities: List[BetOpportunity], excel_file: (str | None) = None) -> None:
        
        def format_excel_filename():
            # Get today's date
            today = datetime.today()
            # Format the date in the required format
            formatted_date = today.strftime("%m-%d-%y")
            # Construct the file path and name
            filename = f"bet_opportunities_data/bet_opportunities_{formatted_date}.xlsx"
            return filename
        
        if excel_file == None:
            excel_file = format_excel_filename()

        rows = []

        # Flatten the BetOpportunity objects into rows for Excel
        for bet in bet_opportunities:
            rows.append(bet.to_json())

        # Convert to DataFrame and save to Excel
        df = pd.DataFrame(rows)
        df.to_excel(excel_file, index=False)
        print(f"Bet opportunities saved to {excel_file}")

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
    bet_opportunities_output_file_2 = "bet_opportunities_data/bet_opportunities_10-22-24-2.json"
    bet_opportunities_output_excel_file = "bet_opportunities_data/bet_opportunities_10-22-24.xlsx"

    qdata = QuestionData()
    # qdata.save_active_markets_to_json()
    # question_map = qdata.build_question_map(filepaths)
    # qdata.save_question_map_to_json(question_map, json_output_file)
    # qdata.question_map_json_to_excel(json_output_file, excel_output_file)
    data = qdata.open_question_map_json(json_output_file)
    bet_opportunities = qdata.get_bet_opportunities_from_question_map(data)
    qdata.save_bet_opportunities_to_json(bet_opportunities, bet_opportunities_output_file)
    updated  = qdata.get_updated_bet_opportunity_data(bet_opportunities_output_file)
    qdata.save_bet_opportunities_to_json(updated, bet_opportunities_output_file_2)