from sentence_transformers import SentenceTransformer, util
import torch
from typing import List, Tuple

# Load the Sentence-BERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

def encode_questions(question_list : List[str]) -> torch.Tensor:
    # Encode the list of existing questions
    question_list_embeddings = model.encode(question_list, convert_to_tensor=True)
    return question_list_embeddings

def get_k_similar_questions(question: str, question_list : List[str],question_list_embeddings: torch.Tensor, k: int) -> List[Tuple[str, float]]:
    """
    Get the top-k semantically similar questions from a list of existing questions.
    
    :param question: The input question.
    :param question_list: A list of questions to compare against.
    :param question_list_embeddings: Vector representation of the list of questions to compare against.
    :param k: The number of top similar questions to return.
    :return: A list of tuples containing the top-k similar questions and their similarity scores.
    """
    if question_list == []:
        return []
    # Encode the input question
    question_embedding = model.encode(question, convert_to_tensor=True)
    
    # Compute the cosine similarities
    similarities = util.pytorch_cos_sim(question_embedding, question_list_embeddings)[0]
    
    # Get the top-k most similar questions
    top_k_indices = similarities.topk(k=min(similarities.size(0),k)).indices.tolist()
    
    # Create a list of the top-k most similar questions with their similarity scores
    top_k_similar_questions = [(question_list[i], similarities[i].item()) for i in top_k_indices]
    
    return top_k_similar_questions