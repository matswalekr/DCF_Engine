import pandas as pd
import yfinance as yf
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import numpy as np
import math
from typing import Union, Literal, Tuple, List, Dict

class Yfinance_Query_Handler():
    bond_ticker = {
        5: "^FVX",
        10: "^TNX",
        30: "^TYX" 
    }
    @staticmethod
    def stock(ticker:str)->yf.Ticker:
        return yf.Ticker(ticker)
    
    def industry(self, ticker:str)-> str:
        stock = Yfinance_Query_Handler.stock(ticker)

        industry = stock.info.get("industry")

        return industry
    
    def sector(self, ticker:str)-> str:
        stock = Yfinance_Query_Handler.stock(ticker)

        sector = stock.info.get("sector")

        return sector 
    
    def website(self, ticker:str)-> str:
        stock = Yfinance_Query_Handler.stock(ticker)

        link = stock.info.get("website")

        return link     
    
    def historic_data(self, ticker: str, period: str = None, start: date = None, end: date = None, interval:str = None)->pd.DataFrame:
        stock = Yfinance_Query_Handler.stock(ticker)
        params = {
        "period": period,
        "start": start,
        "end": end,
        "interval": interval
        }
        filtered_params = {key: value for key, value in params.items() if value is not None}
        history = stock.history(**filtered_params)
        history["Ticker"] = ticker
        return history
    
    def dividends(self, ticker:str)-> pd.DataFrame:
        stock = Yfinance_Query_Handler.stock(ticker)
        dividends = stock.dividends
        dividends["Ticker"] = ticker
        return dividends
    
    def major_holder(self, ticker:str)-> pd.DataFrame:
        stock = Yfinance_Query_Handler.stock(ticker)
        major_holders = stock.major_holders
        major_holders["Ticker"] = ticker
        return major_holders
    
    def analyst_recommendations(self, ticker)-> pd.DataFrame:
        stock = Yfinance_Query_Handler.stock(ticker)
        recommendations = stock.recommendations
        recommendations["Ticker"] = ticker
        return recommendations
     
    def analyst_target(self, ticker)-> pd.DataFrame:
        stock = Yfinance_Query_Handler.stock(ticker)
        recommendations_summary = stock.recommendations_summary
        recommendations_summary["Ticker"] = ticker
        return recommendations_summary

    def sp500_prices_daily(self, start: date, end: date)->pd.DataFrame:
        
        return self.ticker_prices_daily(ticker = "^GSPC", start=start, end=end)
    
    def ticker_prices_daily(self,start: Union[date, str], end: Union[date, str], ticker:str = None, tickers:List[str] = None)->pd.DataFrame:
        # Define the S&P 500 ticker
        # Download daily prices
        assert (ticker or tickers), "No tickers were given"
        assert (not (ticker and tickers)), "Can't give ticker and tickers to ticker_prices_daily"
        if isinstance(start, date):
            start = start.strftime("%Y-%m-%d")

        if isinstance(end, date):
            end = end.strftime("%Y-%m-%d")

        if ticker:
            stock_data = yf.download(ticker, start=start, end=end, interval="1d")
        if tickers:
            stock_data = yf.download(tickers, start=start, end=end, interval="1d")

        return stock_data


    def beta_quity(self, ticker: str, time_frame_years: int)-> float:

        if time_frame_years <= 0:
            raise ValueError(f"The years to calculate must be positive, not {time_frame_years}")
        
        # End = Yesterday, start = X years before yesterday
        end = datetime.now() - relativedelta(days=-1)
        start = end - relativedelta(years=time_frame_years)

        # Convert to strings in right formal
        end = end.strftime("%Y-%m-%d")
        start = start.strftime("%Y-%m-%d")

        # get the stock data
        stock_data = self.ticker_prices_daily(ticker = ticker, start = start, end = end)
        print(stock_data)

        if stock_data.empty:
            raise ValueError(f"No data found for the stock {ticker} between the dates {end} - {start}")
        
        market_data = self.sp500_prices_daily(start = start, end = end)

        if market_data.empty:
            raise ValueError(f"No data found for the S&P500 between the dates {end} - {start}")
        
        # calculate the returns (change in price)
        stock_returns = stock_data["Adj Close"].pct_change().dropna()
        market_returns = market_data["Adj Close"].pct_change().dropna()

        # Align the data to make sure no data mismatches
        aligned_data = pd.concat([stock_returns, market_returns], axis=1, join="inner")
        aligned_data.columns = ["Stock", "Market"]

        # calculate covariance and variance
        covariance_matrix = np.cov(aligned_data["Stock"], aligned_data["Market"])

        covariance = covariance_matrix[0, 1]  # Covariance between stock and market
        market_variance = covariance_matrix[1,1]  # Variance of market returns

        # Calculate beta
        beta: float = covariance / market_variance

        return beta
    
    def snp500_return(self, time_frame_years: int)-> float: 
        """
        Calculate the average annualized return of the S&P 500 over a specified time frame.
        
        :param time_frame_years: Number of years to look back for the calculation.
        :return: The annualized return as a float.
        """
        if time_frame_years <= 0:
            raise ValueError(f"The years to calculate must be positive, not {time_frame_years}")
        
        # End = Today, start = X years before today
        end = datetime.now()
        start = end - relativedelta(years=time_frame_years)

        # Convert to strings in right formal
        end = end.strftime("%Y-%m-%d")
        start = start.strftime("%Y-%m-%d")

        prices_snp500 = self.sp500_prices_daily(start=start, end = end)["Adj Close"]
    
        if prices_snp500.empty:
            raise ValueError(f"No data found for the dates {start} - {end}")

        price_today = prices_snp500.iloc[-1,0]
        prices_beginning_timeframe = prices_snp500.iloc[0,0]

        relative_change_prices = (price_today-prices_beginning_timeframe)/prices_beginning_timeframe

        annualised_change_prices = math.pow(relative_change_prices, 1/time_frame_years)

        return annualised_change_prices-1

    def us_treasury_bond_data(self, start: Union[date, str], end: Union[date, str], duration: Literal[5,10,30])->pd.DataFrame:
        """
        Returns a dataframe of the corresponding US-treasury bond prices in the date range
        Current bonds available are for duration 5, 10 and 30 years
        If the dates are given as strings, use notation YYYY-MM-DD"""

        if isinstance(start, date):
            start = start.strftime("%Y-%m-%d")

        if isinstance(end, date):
            end = end.strftime("%Y-%m-%d")

        try:
            ticker = self.bond_ticker[duration]

        except ValueError:
            raise ValueError(f"No US treasury bond of duration {duration} found")
        
        data_bonds = yf.download(ticker, start=start, end=end)

        return data_bonds
        
    def risk_free_rate(self)->float:
        """
        Calculates the risk free rate using the yield of 10 years US-treasury bills"""
        end = datetime.now()
        start = end - relativedelta(days = 10)

        # Convert to strings in right formal
        end = end.strftime("%Y-%m-%d")
        start = start.strftime("%Y-%m-%d")

        bond_data: pd.DataFrame = self.us_treasury_bond_data(duration=10, start = start, end = end)
        last_yield: float = float(bond_data["Close"].iloc[-1, 0])

        yield_to_maturity: float = last_yield / 100

        return yield_to_maturity

    def prices_52_weeks(self, ticker: str)->pd.DataFrame:

        # End = Today, start = X years before today
        end = datetime.now()
        start = end - relativedelta(weeks=52)

        # Convert to strings in right formal
        end = end.strftime("%Y-%m-%d")
        start = start.strftime("%Y-%m-%d")

        stock_prices = self.ticker_prices_daily(ticker = ticker, start = start, end = end)

        return stock_prices

    def high_low_52_weeks(self, ticker:str)-> Tuple[float, float]:
        """
        Returns the highest and lowest stock prices of the last 52 weeks
        Returns (max, min)"""

        daily_prices: pd.DataFrame = self.prices_52_weeks(ticker = ticker)

        end_of_day_prices: pd.DataFrame = daily_prices["Close"]

        max_price: float = end_of_day_prices.max().iloc[0]
        min_price: float = end_of_day_prices.min().iloc[0]

        return (max_price, min_price)
    
    def company_name(seld, ticker: str)-> str:
        """
        Returns the official name of a company using its ticker"""

        ticker_ = yf.Ticker(ticker)

        company_name = ticker_.info.get("longName", None) # None is default

        return company_name

    def number_shares_outstanding(self, ticker: str = None, tickers: List[str] = None)->Dict[str, int]:
        """Returns the number of shares outstanding\n
        Mainly used for multiple tickers"""

        assert (ticker or tickers), "No tickers were given"

        if ticker:
            Warning.warn(f"Yfinance function number_shares_outstanding(ticker = {ticker}) used for 1 ticker.\n Ususally used for multiple tickers", UserWarning)
            tickers = [ticker]

        return_dict: Dict[str, int] = {}        
        
        for ticker in tickers:
            t = yf.Ticker(ticker)
            shares_outstanding = t.info.get("sharesOutstanding")
            return_dict[ticker] = shares_outstanding

        return return_dict


def main()->None:
    query = Yfinance_Query_Handler()

    print(query.beta_quity(ticker = "AAPL",time_frame_years= 10))

if __name__ == "__main__":
    main()