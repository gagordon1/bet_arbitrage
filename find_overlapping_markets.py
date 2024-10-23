from typing import TypedDict, List, Tuple, Dict
from nlp_functions import get_k_similar_questions, encode_questions
from betting_markets import BinaryMarketMetaData
import torch # type: ignore

SIMILARITY_CUTOFF = .8

QuestionMap = Dict[str, List[BinaryMarketMetaData]]

# Function to normalize a question (e.g., lowercasing, stripping punctuation)
def normalize_question(question):
    """Normalize the question by converting to lowercase and stripping punctuation."""
    return question.lower().strip()

def most_similar_question(question : str, similar_questions : List[Tuple[str, float]]) -> str | bool:
    """Given a list of suggested similar questions, return the semantically equivalent question, False otherwise"""
    # naive method - TBU update with openai api call
    if len(similar_questions) > 0:
        if similar_questions[0][1] > SIMILARITY_CUTOFF:
            return similar_questions[0][0]
    return False

def question_exists(question :str, existing_questions : List[str], existing_questions_embedding : torch.Tensor, k : int = 5) -> str | bool:
    """
    Checks whether a question exists in the question map, returning the unique question it maps to if so, false otherwise 
    """
    [similar_questions, similar_ids] = get_k_similar_questions(question, existing_questions, existing_questions_embedding, k)
    return most_similar_question(question, similar_questions)

def map_questions_across_platforms(questions_by_platform : List[List[BinaryMarketMetaData]]) -> QuestionMap:
    # Dictionary to store normalized questions as keys and list of platform/question IDs as values
    question_map : QuestionMap = {}
    count = 0
    for platform_questions in questions_by_platform:
        print("Processing Platform Data for platform " + str(count) + "...")
        #only check questions from other platforms
        existing_questions = list(question_map.keys())
        existing_questions_embedding = encode_questions(existing_questions)
        for question in platform_questions:
            normalized_question = normalize_question(question["question"])
            unique_question = question_exists(normalized_question, existing_questions, existing_questions_embedding)
            if type(unique_question) == str:
                question_map[unique_question].append(question)
            else:
                question_map[normalized_question] = [question]
        count += 1
    return question_map

def get_best_match_by_platform(question_map : QuestionMap) -> QuestionMap:

    output : QuestionMap = {}
    for question in question_map:
        entry = question_map[question]
        unique_platforms = {i["platform"] for i in entry}
        if len(unique_platforms) > 1:
            new_entry = []
            for platform in unique_platforms:
                platform_questions = [i["question"] for i in entry if i["platform"] == platform]
                platform_ids = [i["id"] for i in entry if i["platform"] == platform]         
                [(best_question, score)], [(best_id, score)] = get_k_similar_questions(question, platform_questions, encode_questions(platform_questions), 1, question_ids=platform_ids)
                new_entry.append(next(i for i in entry if i["id"] == best_id))
            entry = new_entry
        output[question] = entry
    return output



if __name__ == "__main__":
    pass