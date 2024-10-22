from typing import List
import json
from find_overlapping_markets import map_questions_across_platforms, QuestionMap
import pandas as pd
from pprint import pprint

class QuestionData:

    def build_multiplatform_question_dataset(self, filepaths : List[str], platform_names : List[str], output_file : str):

        questions_by_platform = []
        for i in range(len(filepaths)):
            with open(filepaths[i], "r") as f:
                platform_questions = json.load(f)
                questions_by_platform.append(
                    [platform_names[i], platform_questions]
                )
        cross_platform_matches = map_questions_across_platforms(questions_by_platform)
        with open(output_file, "w") as f:
            json.dump(cross_platform_matches, f, indent=4)

    def json_to_excel(self, json_file: str, excel_file: str):
        """
        Converts a JSON file of QuestionMap to an Excel file.
        
        :param json_file: The path to the JSON file.
        :param excel_file: The path where the Excel file will be saved.
        """
        # Load the JSON file
        with open(json_file, 'r') as f:
            question_map: QuestionMap = json.load(f)

        # Prepare the rows for the Excel file
        rows = []

        # Iterate over the QuestionMap and flatten the structure
        for question, mappings in question_map.items():
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
        print(f"Data successfully written to {excel_file}")

if __name__ == "__main__":
    filepaths = [
        "question_data/kalshi_questions.json", 
        "question_data/polymarket_questions.json"
        ]
    platform_names = [
        "Kalshi", 
        "Polymarket"
        ]

    #test data
    # filepaths = [
    #     "question_data/test/platform_1_semantically_unique_yes_no_questions.json",
    #     "question_data/test/platform_2_semantically_unique_yes_no_questions.json",
    #     "question_data/test/platform_3_semantically_unique_yes_no_questions.json",
    #     ]
    # platform_names = [
    #     "Platform 1",
    #     "Platform 2",
    #     "Platform 3",
    # ]
    json_output_file = "overlapping_market_data/overlapping_market_data.json"
    excel_output_file = "overlapping_market_data/overlapping_market_data.xlsx"

    qdata = QuestionData()
    qdata.build_multiplatform_question_dataset(filepaths, platform_names, json_output_file)
    qdata.json_to_excel(json_output_file, excel_output_file)