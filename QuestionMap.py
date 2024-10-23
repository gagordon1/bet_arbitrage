from typing import TypedDict, List, Tuple, Dict
from NLPFunctions import NLPFunctions
from BettingPlatform import BinaryMarketMetadata
import torch # type: ignore

SIMILARITY_CUTOFF = .8

class QuestionMap:
    def __init__(self):
        self.map : Dict[str, List[BinaryMarketMetadata]] = {}
    
    @classmethod
    def from_json(cls, data):
        out_map  = QuestionMap()
        for question, entry in data.items():
            out_map[question] = [BinaryMarketMetadata.from_json(e) for e in entry]
        return out_map

    
    def to_json(self) -> dict:
        out : dict = {}
        for question, entry in self.items():
            out[question] = [e.to_json() for e in entry]
        return out
    
    def keys(self):
        return self.map.keys()
    
    def items(self):
        return self.map.items()
    
    def __getitem__(self, key : str) -> List[BinaryMarketMetadata]:
        return self.map[key]
    
    def __setitem__(self, key: str, value : List[BinaryMarketMetadata]):
        self.map[key]= value

    # Function to normalize a question (e.g., lowercasing, stripping punctuation)
    def normalize_question(self, question):
        """Normalize the question by converting to lowercase and stripping punctuation."""
        return question.lower().strip()

    def most_similar_question(self, question : str, similar_questions : List[Tuple[str, float]]) -> str | bool:
        """Given a list of suggested similar questions, return the semantically equivalent question, False otherwise"""
        # naive method - TBU update with openai api call
        if len(similar_questions) > 0:
            if similar_questions[0][1] > SIMILARITY_CUTOFF:
                return similar_questions[0][0]
        return False

    def question_exists(self, nlp : NLPFunctions, question :str, existing_questions : List[str], existing_questions_embedding : torch.Tensor, k : int = 5) -> str | bool:
        """
        Checks whether a question exists in the question map, returning the unique question it maps to if so, false otherwise 
        """
        [similar_questions, similar_ids] = nlp.get_k_similar_questions(question, existing_questions, existing_questions_embedding, k)
        return self.most_similar_question(question, similar_questions)

    def map_questions_across_platforms(self, questions_by_platform : List[List[BinaryMarketMetadata]]):
        """Given a list of lists of market metadata, creates the question map which maps each unique, normalized question in the provided data
            to a list of similar BinaryMarketMetadata based on semantic equivalence of the market question

        Args:
            questions_by_platform (List[List[BinaryMarketMetadata]]): contains a list of binarymarketmetadata for each platform
        """
        # Dictionary to store normalized questions as keys and list of platform/question IDs as values
        count = 0
        nlp = NLPFunctions()
        for platform_questions in questions_by_platform:
            print("Processing Platform Data for platform " + str(count) + "...")
            #only check questions from other platforms
            existing_questions = list(self.keys())
            existing_questions_embedding = nlp.encode_questions(existing_questions)
            for question in platform_questions:
                normalized_question = self.normalize_question(question.question)
                unique_question = self.question_exists(nlp, normalized_question, existing_questions, existing_questions_embedding)
                if type(unique_question) == str:
                    self[unique_question].append(question)
                else:
                    self[normalized_question] = [question]
            count += 1

    def get_best_match_by_platform(self):
        """Updates the question map that such that it has, for each question, ensured only one best match for each platform

        Args:
            question_map (QuestionMap): maps questions to list of similar questions across platforms
        """
        nlp = NLPFunctions()
        new_map : Dict[str, List[BinaryMarketMetadata]] = {}
        for question, entry in self.items():
            unique_platforms = {i.platform for i in entry}
            if len(unique_platforms) > 1:
                new_entry = []
                for platform in unique_platforms:
                    platform_questions = [i.question for i in entry if i.platform == platform]
                    platform_ids = [i.id for i in entry if i.platform == platform]         
                    [(best_question, score)], [(best_id, score)] = nlp.get_k_similar_questions(question, platform_questions, nlp.encode_questions(platform_questions), 1, question_ids=platform_ids)
                    new_entry.append(next(i for i in entry if i.id == best_id))
                entry = new_entry
            new_map[question] = entry
        self.map = new_map
        



if __name__ == "__main__":
    pass