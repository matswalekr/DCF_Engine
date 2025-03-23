from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Any, List
import ast

class Generalised_LLM_Query_Handler():
    """
    Class to query data from Chat GPT\n
    args:\n
    _______________________________\n
    
    model_name: str = "meta-llama/Llama-2-7b-chat-hf"\n
    _______________________________\n
    Specifies which LLM model to use. Currently available:\n
    - gpt2\n
    - EleutherAI/gpt-neo-1.3B\n
    - meta-llama/Llama-2-7b-chat-hf\n
    """

    def __init__(self, model_name: str = "gpt2")->None:

        self.model_name = model_name

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

    def prompt(self, prompt:str)-> Any:
        """Function to prompt an LLM"""
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
        output = self.model.generate(input_ids, max_length=50)

        # Decode and return the output of the model
        return self.tokenizer.decode(output[0], skip_special_tokens=True)


class LLM_Query_Handler(Generalised_LLM_Query_Handler):
    """
    Class to query financial data from a LLM\n
    args:\n
    _______________________________\n
    
    model_name: str = "meta-llama/Llama-2-7b-chat-hf"\n
    _______________________________\n
    Specifies which LLM model to use. Currently available:\n
    - gpt2\n
    - EleutherAI/gpt-neo-1.3B\n
    - meta-llama/Llama-2-7b-chat-hf\n
    """

    def __init__(self, model_name: str = "gpt2")->None:
        super().__init__(model_name= model_name) 

        gpt_config="You are a financial analyst at a very reputable firm. Your job is too help with very important valuations.\
            The work is very important, so make sure not to make a single mistake.\
            You may use information from the web, but only if explicitly told so. Always explain when you do this.\
            Make sure to always double check your work and only answer when you are absolutely sure. A lot depends on you!\
            If you are not sure, always explain this."
        
    def get_competitors(self, ticker: str)-> List[str]:
        """
        This function returns a list of the tickers of competitors of a company.
        """
        
        competitors_query: str = f"\
            You are now tasked to do a valuation on a US company with the ticker {ticker}.\
            You will be do a comparable multiple analysis using a tool in python. Your task is to identify the companies 5-8 main competitors.\
            A competitor is a firm that caters to the same needs for clients. Usually, these firms operate in the same sector, but this is not always true.\
            If possible, you need to select companies of the same market size. \
            It would also be good to find firms in different solution lifecycles. But this is not very important and should only be done when you have multiple competitors you can choose from.\
            Very important: All competitors need to be listed on the US stock exchanges!\
            You should then select the tickers of these companies and return them in the format of a list in python. Do not return any other information!\
            In conclusion you need to: find 5-8 competitors of {ticker} from the US and return them in a python list format.\
            We need to count on you! Your job is very important and could loose us a lot of money! Dont make a mistake!"
        
        answer: str = self.prompt(prompt=competitors_query)

        competitors_list: List[str] =  ast.literal_eval(answer) # Parses the listlike string back to a list

        return competitors_list
