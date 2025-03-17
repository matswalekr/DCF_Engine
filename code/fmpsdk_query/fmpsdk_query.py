import fmpsdk
from typing import Any, List, Union, Callable
from functools import wraps

# Load the necessary functions to load the API keys from .env file
import os
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), "../../keys.env")
load_dotenv(dotenv_path=dotenv_path)

class FMPSDK_Query_Handler():
    """
    Query handler for queries on FMPSDK.\n
    The resulting instance is a handler with necessary methods to query the API.\n
    As a result, the handler should be a monoid (even though not enforced).\n
    Note that there is only a limited number of calls due to limited API keys.\n
    """

    def __init__(self)-> None:
        # get the API_KEYS from the .env file
        self.API_Keys = os.getenv("FMPSDK_API_KEYS").split(",") 
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
        """
        Function to return the competitors of the given ticker.\n
        \n
        Args:\n
        \n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the competitors are searched for.\n
        \n
        number: int = 5\n
        _______________________________\n
        Number of competitors to be returned.\n
        Default: 5\n
        \n
        lower_multiple: float = 0.6\n
        _______________________________\n
        Lower multiple of the market cap of the given ticker to filter the competitors.\n
        Default: 0.6\n
        \n
        upper_multiple: float = 1.4\n
        _______________________________\n
        Upper multiple of the market cap of the given ticker to filter the competitors.\n
        Default: 1.4\n
        \n
        Returns:\n
        \n
        List[str]\n
        _______________________________\n
        List of competitors'tickers of the given ticker.\n
        """
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
    def general_information(self, ticker:str)-> str:
        pass
    
    @api_error_wrapper
    def price(self, ticker:str) -> float:
        """
        Function to return the price of the given ticker.\n
        \n
        Args:\n
        \n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the price is searched for.\n
        \n
        Returns:\n
        \n
        float\n
        _______________________________\n
        Price of the given ticker.\n
        """
        return float(fmpsdk.company_profile(apikey=self.API_KEY, symbol=ticker)[0]["price"])

    @api_error_wrapper
    def last_divident(self, ticker:str) -> float:
        """
        Function to return the last divident of the given ticker.\n
        \n
        Args:\n
        \n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the last divident is searched for.\n
        \n
        Returns:\n
        \n
        float\n
        _______________________________\n
        Last divident of the given ticker.\n
        """
        return float(fmpsdk.company_profile(apikey=self.API_KEY, symbol=ticker)[0]["lastDiv"])

    @api_error_wrapper
    def average_volume(self, ticker:str) -> int:
        """
        Function to return the average volume of the given ticker.\n
        \n
        Args:\n
        \n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the average volume is searched for.\n
        \n
        Returns:\n
        \n
        int\n
        _______________________________\n
        Average volume of the given ticker.\n"""
        return int(fmpsdk.company_profile(apikey=self.API_KEY, symbol=ticker)[0]["volAvg"])

    @api_error_wrapper
    def market_cap(self, ticker:str) -> int:
        """
        Function to return the market cap of the given ticker.\n
        \n
        Args:\n
        \n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the market cap is searched for.\n
        \n
        Returns:\n
        \n
        int\n
        _______________________________\n
        Market cap of the given ticker.\n
        """
        return int(fmpsdk.company_profile(apikey=self.API_KEY, symbol= ticker)[0]["mktCap"])

    @api_error_wrapper
    def number_shares(self, ticker:str) -> int:
        """
        Function to return the number of shares outstanding of the given ticker.\n
        \n
        Args:\n
        \n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the number of shares outstanding is searched for.\n
        \n
        Returns:\n
        \n
        int\n
        _______________________________\n
        Number of shares outstanding of the given ticker.\n
        """
        market_cap = self.market_cap(ticker = ticker)
        price = self.price(ticker = ticker)
        return int(market_cap/price)

    @api_error_wrapper
    def company_profile(self, ticker:str) -> dict:
        """
        Function to return the company profile of the given ticker.\n
        \n
        Args:\n
        \n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the company profile is searched for.\n
        \n
        Returns:\n
        \n
        dict\n
        _______________________________\n
        Company profile of the given ticker from FMPSDK.\n
        This dictionary includes various information about the company.\n
        """
        return fmpsdk.company_profile(apikey=self.API_KEY, symbol=ticker)[0]

    @api_error_wrapper
    def industry(self, ticker:str) -> Union[str, None]:
        """
        Function to return the industry of the given ticker.\n
        \n
        Args:\n
        \n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the industry is searched for.\n
        \n
        Returns:\n
        \n
        str\n
        _______________________________\n
        Industry of the given ticker.\n
        """
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
        """
        Function to return the currency a given ticker is traded in.\n
        \n
        Args:\n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the currency is searched for.\n
        \n
        Returns:\n
        Union[str, None]\n
        _______________________________\n
        Currency of the given ticker as a string.\n
        Returns None if the currency is not found.\n
        """
        try:
            return str(fmpsdk.company_profile(apikey=self.API_KEY, symbol= ticker)[0]["currency"])
        except (KeyError,IndexError):
            return None

    @api_error_wrapper
    def country(self, ticker:str)-> str:
        """
        Function to return the country a given ticker is traded in.\n
        \n
        Args:\n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the country is searched for.\n
        \n
        Returns:\n
        Union[str, None]\n
        _______________________________\n
        Country of the given ticker as a string.\n
        Returns None if the country is not found.\n
        """
        return self.company_profile(ticker = ticker)['country']

    @api_error_wrapper
    def stock_exchange(self, ticker:str)-> str:
        """
        Function to return the stock exchange a given ticker is traded in.\n
        \n
        Args:\n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the stock exchange is searched for.\n
        \n
        Returns:\n
        str\n
        _______________________________\n
        Stock exchange of the given ticker as a string.\n
        """
        return self.company_profile(ticker = ticker)['exchange']

    @api_error_wrapper
    def company_description(self, ticker:str)-> str:
        """
        Function to return the description of the company of a given ticker.\n
        \n
        Args:\n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the description is searched for.\n
        \n
        Returns:\n
        str\n
        _______________________________\n
        Description of the company of the given ticker.\n
        """
        return self.company_profile(ticker = ticker)['description']

    @api_error_wrapper
    def website(self, ticker:str)-> str:
        """
        Function to return the website of the company of a given ticker.\n
        \n
        Args:\n
        ticker: str \n
        _______________________________\n
        Ticker of the company of which the website is searched for.\n
        \n
        Returns:\n
        str\n
        _______________________________\n
        Website of the company of the given ticker as a string.\n
        """
        return self.competitors(ticker = ticker)['website']
    

def main()-> None:
    query = FMPSDK_Query_Handler()

    print(query.competitors("AAPL", lower_multiple=0))

if __name__ == "__main__":
    main()