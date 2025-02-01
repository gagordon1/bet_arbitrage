from sentence_transformers import SentenceTransformer, util # type: ignore
from BetOpportunity import BetOpportunity
import torch # type: ignore
from typing import List, Tuple, TypedDict
from openai import OpenAI
import os
from dotenv import load_dotenv
from constants import *
import json
import logging

class BetOpportunityTitles(TypedDict):
    id : str
    market_1_question : str
    market_2_question : str

class SemanticEquivalence:
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
        
def filter_bet_opportunities_with_llm_semantic_equivalence(bet_opportunities : list[BetOpportunityTitles], model : LLM) -> tuple[set[str], float]:
    """given a list of bet opportunity metadata (id and question titles), returns a list of bet opportunity ids with valid semantic equivalence

    Args:
        bet_opportunities (list[BetOpportunityTitles]): given a list of bet opportunities by with id and question titles

    Returns:
        set[str]: set of bet opportunity ids that are semantically equivalent
        float: cost of the llm operation
    """
    ENTRIES_PER_LLM_REQUEST = 50
    load_dotenv()
    batches = [bet_opportunities[i:i+ENTRIES_PER_LLM_REQUEST] for i in range(0, len(bet_opportunities), ENTRIES_PER_LLM_REQUEST)]
    api_key_name = LLM_INFO[model]["api_key_name"]
    base_url = LLM_INFO[model]["base_url"]
    model_name = LLM_INFO[model]["model_name"]
    prompt_prefix = """for the below list, return a list of ids where market_1_question is semantically equivalent to market_2_question 
    i.e. they mean precisely the same thing. Return as a valid json list of strings for the valid ids. 
    In your response include no extra explanation or text just the list 
    Example response: 
    [
        "id1",
        "id2",
        "id3"
    ]
    are Do not include json formatting indicators such as "```json". If there
     are no valid ids, just return "[]" \n"""
    
    out = set()
    cost = 0.0
    client = OpenAI(
            api_key=os.environ.get(api_key_name),
            base_url= base_url
        )
    for batch in batches:
        prompt = f"{prompt_prefix}{batch}"
        # logging.info("PROMPT:\n" +"---"*10 + "\n" + prompt)
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=model_name,
            )
            content = chat_completion.choices[0].message.content
            usage = chat_completion.usage
            if content:
                logging.info("RESPONSE:\n" + "---"*10 + "\n" + content)
                out.update(set(json.loads(content)))
            if usage:
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens
                logging.info(f"Prompt tokens: {prompt_tokens}\n Completion tokens: {completion_tokens}")

                cost += prompt_tokens * LLM_INFO[model]["cost_per_1m_input_tokens"] /10**6
                cost += completion_tokens * LLM_INFO[model]["cost_per_1m_output_tokens"] /10**6
        except json.decoder.JSONDecodeError as e:
            logging.error(f"Json parsing error for prompt:\n {prompt}\nError message: {e}\nRaw response: {chat_completion} ")

    return out, cost
