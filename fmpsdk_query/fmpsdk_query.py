import fmpsdk
from typing import Any, List, Union, Callable
from functools import wraps

# Load the necessary functions to load the API keys from .env file
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="keys.env")

class FMPSDK_Query_Handler():
    """
    Query handler for queries on FMPSDK
    Note that there is only a limited number of calls due to limited API keys
    """

    
    def __init__(self)-> None:
        # get the API_KEYS from the .env file
        self.API_Keys = os.getenv("API_KEYS", "").split(",") 
        if not self.API_Keys or self.API_Keys == [""]:
            raise ValueError("No API keys found in environment variables")
        
        key_ptr = 0
        self.API_KEY:str = self.API_Keys[key_ptr]

    @staticmethod
    def api_error_wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapped_function(self, *args, **kwargs) -> Any:
            data: Any = func(self, *args, **kwargs)
            try:
                if "error" in data:
                    if self.key_ptr < len(self.API_Keys) - 1:
                        self.key_ptr += 1
                        self.API_KEY = self.API_Keys[self.key_ptr]
                        return func(self, *args, **kwargs)
                    else:
                        raise ValueError("Used all API Keys")
                else:
                    return data
            except TypeError:
                return data

        return wrapped_function

    @api_error_wrapper
    def competitors(self, ticker: str, number: int = 5, lower_multiple:float = 0.6, upper_multiple:float = 1.4)-> List[str]:
        
        industry = self.industry(ticker = ticker)

        market_cap = self.market_cap(ticker = ticker)

        competitors_ =  fmpsdk.stock_screener(apikey = self.API_KEY,
                                          market_cap_lower_than = upper_multiple * market_cap,
                                          market_cap_more_than = lower_multiple * market_cap,
                                          industry=industry)
        
        competitors_ = [competitor["symbol"] for competitor in competitors_]
        if ticker in competitors_:
            competitors_.remove(ticker)
        return competitors_
    
    @api_error_wrapper
    def general_infor(self, ticker:str)-> str:
        pass
    
    @api_error_wrapper
    def price(self, ticker:str) -> float:

        return float(fmpsdk.company_profile(apikey=self.API_KEY, symbol=ticker)[0]["price"])

    @api_error_wrapper
    def last_divident(self, ticker:str) -> float:

        return float(fmpsdk.company_profile(apikey=self.API_KEY, symbol=ticker)[0]["lastDiv"])

    @api_error_wrapper
    def average_volume(self, ticker:str) -> int:

        return int(fmpsdk.company_profile(apikey=self.API_KEY, symbol=ticker)[0]["volAvg"])

    @api_error_wrapper
    def market_cap(self, ticker:str) -> int:

        return int(fmpsdk.company_profile(apikey=self.API_KEY, symbol= ticker)[0]["mktCap"])

    @api_error_wrapper
    def number_shares(self, ticker:str) -> int:
        market_cap = self.market_cap(ticker = ticker)
        price = self.price(ticker = ticker)
        return int(market_cap/price)

    @api_error_wrapper
    def company_profile(self, ticker:str) -> dict:

        return fmpsdk.company_profile(apikey=self.API_KEY, symbol=ticker)[0]

    @api_error_wrapper
    def industry(self, ticker:str) -> Union[str, None]:

        try:
            raw_industry = fmpsdk.company_profile(apikey=self.API_KEY, symbol=ticker)[0]["industry"]
            industry = str(raw_industry).replace(" -", "")
            match industry:
                case "Airlines, Airports & Air Services":
                    return "Airports & Air Services"
                case _:
                    return industry
        except (KeyError, IndexError):
            return None

    @api_error_wrapper
    def currency(self, ticker:str) -> Union[str, None]:

        try:
            return str(fmpsdk.company_profile(apikey=self.API_KEY, symbol= ticker)[0]["currency"])
        except (KeyError,IndexError):
            return None

    @api_error_wrapper
    def country(self, ticker:str)-> str:
        return self.company_profile(ticker = ticker)['country']

    @api_error_wrapper
    def stock_exchange(self, ticker:str)-> str:
        return self.company_profile(ticker = ticker)['exchange']

    @api_error_wrapper
    def company_description(self, ticker:str)-> str:
        return self.company_profile(ticker = ticker)['description']

    @api_error_wrapper
    def website(self, ticker:str)-> str:

        return self.competitors(ticker = ticker)['website']
    

def main()-> None:
    query = FMPSDK_Query_Handler()

    print(query.competitors("AAPL", lower_multiple=0))

if __name__ == "__main__":
    main()