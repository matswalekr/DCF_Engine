import wrds
import pandas as pd
import asyncio
from typing import List, Callable, Union
import time
from itertools import product
import warnings
import functools

# Load the necessary functions to load the API keys from .env file
import os
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), "../../keys.env")
load_dotenv(dotenv_path=dotenv_path)

def timeit(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Record start time
        result = func(*args, **kwargs)  # Call the original function
        end_time = time.time()  # Record end time
        print(f"Execution time of {func.__name__}: {end_time - start_time:.4f} seconds")
        return result
    return wrapper

def deprecated(func):
    """
    A decorator to mark functions as deprecated.
    Issues a DeprecationWarning when the function is called.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"{func.__name__} is deprecated and may be removed in the future.\nIt does currently not receive any updates",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)
    return wrapper

async def task_wrapper(function: Callable, *args):
    """
    Wrapper used to get the Exception of a async function as a value\n
    Returns (Exception, args)"""
    try:
        return await function(*args)
    except Exception as e:
        return (e, args)
    

class WRDS_Query_Handler():

    def __init__(self)->None:
        self.username: str = os.getenv("wrds_username", "")
        if not self.username:
            raise ValueError("No username found in environment variables")
        self.db = wrds.Connection(wrds_username = self.username)
        pd.set_option('future.no_silent_downcasting', True)

    def __del__(self)-> None:
        if self.db:
            self.db.close()

    @staticmethod
    def format(df: pd.DataFrame) -> pd.DataFrame:
        df = df.set_index(["ticker", "year"]).T

        return df

    @staticmethod
    def aggregate_many_tickers(function: Callable, **kwargs)-> pd.DataFrame:
        
        async def run_tasks():
            
            values = kwargs.values()

            tasks = [task_wrapper(function, *args) for args in product(*values)]

            return await asyncio.gather(*tasks, return_exceptions=True)

        results: List[Union[pd.DataFrame, Warning]] = asyncio.run(run_tasks())

        return_dfs: List[pd.DataFrame] = []

        for result in results:
            if isinstance(result, tuple):
                exception: Exception = result[0]
                args = result[1]
                warnings.warn(f"\nRunning the code for {args} raised the following exception: \n{exception}")
            elif isinstance(result, pd.DataFrame):
                    result.fillna(0,inplace = True)
                    return_dfs.append(result)          
            else:
                raise TypeError(f"When trying to calculate {function}({kwargs}), the unknown type {type(result)} was returnes")

        try:
            return pd.concat(return_dfs, ignore_index=True)

        # When there were no dataframes found, return an empty df
        except ValueError:
            return pd.DataFrame()

    def get_statement(self, function: Callable, ticker: str = None, year: int = None, tickers: List[str] = None, years: List[int] = None)-> pd.DataFrame:
        assert ticker or tickers, "No ticker provided"
        assert year or years, "No year provided"

        if ticker and year: 
            unformated_data: pd.DataFrame = asyncio.run(function(ticker, year))

        else:
            if ticker: tickers = [ticker]
            if year: years = [year]

            unformated_data: pd.DataFrame = self.aggregate_many_tickers(tickers = tickers, years = years, function = function)

        # Case when not data was found
        if unformated_data.empty:
            return unformated_data
        
        formated_data: pd.DataFrame = self.format(unformated_data)

        return formated_data

    async def fetch_gvkey(self, ticker: str)-> int:
        """
        Async fetch for gvkey of certain ticker"""

        query_find_gvkey = f"""
        SELECT gvkey 
        FROM comp.security where tic = '{ticker}' LIMIT 1
        """

        gvkey_df: pd.DataFrame = self.db.raw_sql(query_find_gvkey)  

        if not gvkey_df.empty:
            gvkey: str = gvkey_df.iloc[0]['gvkey']  # Extract the value from the DataFrame
        else:
            raise ValueError(f"No gvkey found for ticker {ticker}")
        
        return gvkey

    async def fetch_naicsh(self, ticker:str)-> str:
        gvkey:int = await self.fetch_gvkey(ticker = ticker)

        query_naicsh = f"""
        SELECT
            naicsh as NorthAmericaCode
        FROM comp.co_industry
        WHERE gvkey = '{gvkey}'
        AND consol = 'C'
        LIMIT 1
        """

        # Execute the query with parameters
        naicsh: pd.DataFrame = self.db.raw_sql(query_naicsh)
        if naicsh.empty:
            return None
        
        return str(naicsh.iloc[0,0])

    async def fetch_sich(self, ticker: str)->str:
        gvkey:int = await self.fetch_gvkey(ticker = ticker)

        query_sich = f"""
        SELECT
            sich as StandardIndustryCode
        FROM comp.co_industry
        WHERE gvkey = '{gvkey}'
        LIMIT 1
        """

        # Execute the query with parameters
        sich: pd.DataFrame = self.db.raw_sql(query_sich)

        if sich.empty:
            return None
        
        return str(sich.iloc[0,0])

    async def _income_statement(self, ticker: str, year: int)-> pd.DataFrame: 
        """ 
        async fetch for income statement of certain ticker and year
        """

        query_income_statement = f"""
        SELECT
            fyear AS Year,
            datadate AS Date,
            sale as Revenues,
            cogs as COGS,
            (sale-cogs) as GrossMargin,
            xsga as SellingGeneralAndAdministrativeExpense,
            (oibdp - oiadp) as DepreciationAndAmortisation,
            oiadp as OperatingIncome,
            nopi as NonOperationalResult,
            spi as SpecialItems,
            (pi+xint) as EBIT,
            (-xint) as NetInterest,
            pi as EBT,
            txt as Tax,
            ib as IncomeBeforeExtraordinary,
            tic as Ticker
        FROM comp.funda
        WHERE tic = '{ticker}'    -- Use placeholders for tickers
        AND fyear = {year}    -- Use placeholders for years
        AND indfmt = 'INDL'
        AND datafmt = 'STD'
        AND consol = 'C'
        """

        # Execute the query with parameters
        raw_income_statement: pd.DataFrame = self.db.raw_sql(query_income_statement)

        if not raw_income_statement.empty:
            return raw_income_statement
        else:
            raise ValueError(f"Income statement for {ticker} not found")

    async def _balance_sheet(self, ticker: str, year: int) -> pd.DataFrame:
        """
        Async fetch for balance sheet data"""

        query_balance_sheet = f"""
        SELECT
            fyear AS Year,
            datadate AS Date,
            tic as Ticker,
            che as CashAndEquivalents,
            rect as Receivables,
            invt as Inventories,
            aco as OtherCurrentAssets,
            act as TotalCurrentAssets,
            ppent as PropertyPlantEquipment,
            dpact as CumulatedDepreciationAndAmortization,
            ivaeq as InvestmentInEquity,
            ivao as InvestmentOther,
            intan as IntangibleAssets,
            ao as OtherAssets,
            at as TotalAssets,
            dlc as CurrentDebt,
            ap as TradePayables,
            txp as TaxPayables,
            lco as OtherCurrentLiabilities,
            lct as TotalCurrentLiabilities,
            dltt as LongTermDebt,
            txditc as DeferredTaxesNonCurrent,
            lo as OtherLiabilities,
            lt as TotalLiabilities,
            mib as NonControllingInterest,
            pstk as PreferredStock,
            ceq as CommonStock,
            seq as StockholdersEquity
        FROM comp.funda
        WHERE tic = '{ticker}'    -- Use placeholders for tickers
        AND fyear = {year}    -- Use placeholders for years
        AND indfmt = 'INDL'
        AND datafmt = 'STD'
        AND consol = 'C'
        """
        # Execute the query with parameters
        raw_balance_sheet: pd.DataFrame = self.db.raw_sql(query_balance_sheet)

        if not raw_balance_sheet.empty:
            return raw_balance_sheet
        else:
            raise ValueError(f"Balance Sheet for {ticker} not found")
    
    async def _cash_flow_statement(self, ticker: str, year: int)-> pd.DataFrame:

        query_cash_flow_statement = f"""
        SELECT
            fyear AS Year,
            datadate AS Date,
            tic as Ticker,
            ibc as IncomeBeforeExtraordinary,
            xidoc as ExtraordinaryItemsAndDiscontinued,
            dpc as DepreciationAndAmortization,
            txdc as DeferredTaxes,
            esub as EquityEarningsUnconsolidated,
            sppiv as NetResultSalePPE,
            fopo as OtherFundsOperations,
            (-recch) as IncreaseAccountReceivable,
            (-invch) as IncreaseInventory,
            apalch as IncreaseAccountsPayable,
            txach as IncreaseAccruedTaxes,
            aoloch as NetChangeOtherAssetsLiabilities,
            oancf as OperatingCashFlow,
            ivch as IncreaseInvestments,
            siv as SaleInvestments,
            ivstch as ChangeShortTermInvestment,
            capx as CapEX,
            sppe as SaleOfProperty,
            aqc as Aquisitions,
            ivaco as OtherInvestingActivities,
            ivncf as InvestingCashFlow,
            sstk as EquityIncrease,
            txbcof as TaxBenefitStockOptions,
            prstkc as EquityDecrease,
            dv as Dividend,
            dltis as LongTermDebIssunace,
            dltr as LongTermDebtReduction,
            dlcch as CurrentDebtChange,
            fiao as OtherFinanciangActivities,
            fincf as FinancingCashFlow,
            (fincf + ivncf + oancf) as NetChangeCash
        FROM comp.funda
        WHERE tic = '{ticker}'    -- Use placeholders for tickers
        AND fyear = {year}    -- Use placeholders for years
        AND indfmt = 'INDL'
        AND datafmt = 'STD'
        AND consol = 'C'
        """

        # Execute the query with parameters
        cash_flow_statement: pd.DataFrame = self.db.raw_sql(query_cash_flow_statement)

        if not cash_flow_statement.empty:
            return cash_flow_statement
        else:
            raise ValueError(f"Cash flow statement for {ticker} not found") 

    async def _businessdescription(self, ticker:str)->pd.DataFrame:
        """
        Returns a data frame of the industry of the company"""

        gvkey = await self.fetch_gvkey(ticker = ticker)

        query_description = f"""
        SELECT
            busdescl as BusinessDescription
        FROM comp.co_busdescl
        WHERE gvkey = '{gvkey}'
        LIMIT 1
        """

        # Execute the query with parameters
        description: pd.DataFrame = self.db.raw_sql(query_description)

        if not description.empty:
            description["Ticker"] = ticker
            return description
        else:
            raise ValueError(f"Company description for {ticker} not found") 

    async def _industry(self, ticker:str)-> pd.DataFrame:

        naics = await self.fetch_naicsh(ticker = ticker)

        if not naics:
            return None

        query_industry = f"""
        SELECT
            naicsdesc as SectorDescription
        FROM comp.r_naiccd
        WHERE naicscd = '{naics}'
        LIMIT 1
        """

        # Execute the query with parameters
        industry: pd.DataFrame = self.db.raw_sql(query_industry)

        if not industry.empty:
            industry["Ticker"] = ticker
            return industry
        else:
            raise ValueError(f"Industry for {ticker} not found") 

    @deprecated
    async def _credit_rating(self, ticker: str)-> str:
        """returns the credit rating of the company asyncronously"""
        gvkey = await self.fetch_gvkey(ticker = ticker)

        query_credit_rating = f"""
        SELECT spsticrm, datadate
        FROM comp_na_daily_all
        WHERE gvkey = '{gvkey}' AND
        splticrm IS NOT NULL
        ORDER BY datadate DESC
        LIMIT 1
        """

        credit_rating: pd.DataFrame = self.db.raw_sql(query_credit_rating)

        return credit_rating

    def income_statement(self, ticker: str = None, year: int = None, tickers: List[str] = None, years: List[int] = None)-> pd.DataFrame:
        """
        Returns financial income statement in simplified version
        All values in Million USD""" 

        return self.get_statement(function = self._income_statement, ticker = ticker, tickers = tickers, year = year, years = years)

    def balance_sheet(self, ticker: str = None, year: int = None, tickers: List[str] = None, years: List[int] = None)-> pd.DataFrame:
        """
        Returns financial balance sheet in simplified version
        All values in Million USD""" 

        
        return self.get_statement(function = self._balance_sheet, ticker = ticker, tickers = tickers, year = year, years = years)

    def cash_flow_statement(self, ticker: str = None, year: int = None, tickers: List[str] = None, years: List[int] = None)-> pd.DataFrame:
        """
        Returns a cash flow statement in simplified version
        All values in Million USD"""

        return self.get_statement(function = self._cash_flow_statement, ticker = ticker, tickers = tickers, year = year, years = years)

    def company_description(self, ticker: str = None, tickers: List[str] = None)-> pd.DataFrame:
        """
        Returns the company description of the company"""

        assert ticker or tickers, "No ticker provided"
        if ticker: 
            return asyncio.run(self._businessdescription(ticker = ticker))
        else:
            return self.aggregate_many_tickers(self._businessdescription, tickers = tickers)
        
    def industry(self, ticker: str = None, tickers: List[str] = None)-> pd.DataFrame:
        """
        Returns the industry of the company
        Uses Standard Industrial Classification from US office of management"""
        assert ticker or tickers, "No ticker provided"
        if ticker: 
            return asyncio.run(self._industry(ticker = ticker))
        else:
            return self.aggregate_many_tickers(self._industry, tickers = tickers)

    @deprecated
    def credit_rating(self,ticker:str)->str:
        return asyncio.run(self._credit_rating(ticker=ticker))

def main():
    query = WRDS_Query_Handler()
    #print(query.income_statement(tickers = "MSFT", year = 2014))
    print(query.credit_rating(ticker = "TSLA"))
    #print("\n\n")
    #print(query.income_statement(tickers = ["MSFT", "TSLA"], years = [2022, 2021]))


if __name__ == "__main__":
    main()