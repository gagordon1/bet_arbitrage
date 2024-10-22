from typing import List
import json
from find_overlapping_markets import map_questions_across_platforms

class QuestionData:

    def build_cross_platform_question_dataset(self, filepaths : List[str], platform_names : List[str], output_file : str):

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

if __name__ == "__main__":
    # filepaths = ["question_data/kalshi_questions.json", "question_data/polymarket_questions.json"]
    # platform_names = ["Kalshi", "Polymarket"]

    #test data
    filepaths = [
        "question_data/test/platform_1_semantically_unique_yes_no_questions.json",
        "question_data/test/platform_2_semantically_unique_yes_no_questions.json",
        "question_data/test/platform_3_semantically_unique_yes_no_questions.json",
        ]
    platform_names = [
        "Platform 1",
        "Platform 2",
        "Platform 3",
    ]
    output_file = "overlapping_market_data/overlapping_market_data.json"

    qdata = QuestionData()
    qdata.build_cross_platform_question_dataset(filepaths, platform_names, output_file)