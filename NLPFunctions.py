from sentence_transformers import SentenceTransformer, util # type: ignore
import torch # type: ignore
from typing import List, Tuple


class NLPFunctions:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def encode_questions(self, question_list : List[str]) -> torch.Tensor:
        # Encode the list of existing questions
        question_list_embeddings = self.model.encode(question_list, convert_to_tensor=True)
        return question_list_embeddings

    def get_k_similar_questions(self, question: str, question_list : List[str],question_list_embeddings: torch.Tensor, k: int, question_ids : (List[str] | None) = None) -> List[List[Tuple[str, float]]]:
        """
        Get the top-k semantically similar questions from a list of existing questions.
        
        :param question: The input question.
        :param question_list: A list of questions to compare against.
        :param question_list_embeddings: Vector representation of the list of questions to compare against.
        :param k: The number of top similar questions to return.
        :return: A 2x2 list of list of tuples containing the top-k similar questions and their similarity scores along with similar for question ids if provided, empty list otherwise
        """
        if question_list == []:
            return [[], []]
        # Encode the input question
        question_embedding = self.model.encode(question, convert_to_tensor=True)
        
        # Compute the cosine similarities
        similarities = util.pytorch_cos_sim(question_embedding, question_list_embeddings)[0]
        
        # Get the top-k most similar questions
        top_k_indices = similarities.topk(k=min(similarities.size(0),k)).indices.tolist()
        
        # Create a list of the top-k most similar questions with their similarity scores
        top_k_similar_questions = [(question_list[i], similarities[i].item()) for i in top_k_indices]
        
        if question_ids != None:
            top_k_similar_question_ids = [(question_ids[i], similarities[i].item()) for i in top_k_indices]
        
        if question_ids == None:
            return [top_k_similar_questions, []]
        else:
            return [top_k_similar_questions, top_k_similar_question_ids]
