from fmpsdk_query import FMPSDK_Query_Handler
from yfinance_query import Yfinance_Query_Handler
from wrds_query import WRDS_Query_Handler
from database_query import Database_Query_Handler
from Excel_Engine import open_excel, Excel_write
#from gpt_query import LLM_Query_Handler

from datetime import datetime
from dateutil.relativedelta import relativedelta

from typing import List, Tuple, Optional, Any, Union
import pandas as pd
import warnings
import os

# Customer Exception for when financial statements where not found
class FinancialStatementsNotFoundError(Exception):
    pass

# Global definition of the historic years that is visible to all functions
historic_years: List[int] = []

# Global definition of the competitors. Updated in the get_competitor_info
competitors: List[str] = []

def get_latest_second_latest(statement: pd.DataFrame, column: str,)->Tuple[pd.DataFrame, pd.DataFrame]:
    """Returns a tuple of (latest_value, second_latest_value)"""

    assert(isinstance(statement, pd.DataFrame)), f"The statement given to get_latest_second_latest was not of type pd.DataFrame, but of {type(statement)}.\n"
    assert(isinstance(column, str)), f"The column given to get_latest_second_latest was not of type str, but of {type(column)}.\n"

    sorted_statement = statement.sort_index(level="year", ascending=False).loc[column]
    latest_value = sorted_statement.groupby("ticker").first()
    second_latest_value = sorted_statement.groupby("ticker").nth(1).droplevel("year")
    return (latest_value, second_latest_value)

def get_competitor_info(ticker: str)-> Optional[pd.DataFrame]:
    
    """
    Gets the info of competitors for the comparison of multiples.
    Gets the latest year according to the latest year found of the main stock.
    Returns None if no competitor info was found.
    """
    # Use the global competitors
    global competitors

    assert(isinstance(ticker, str)), f"The ticker given to the function get_competitor_info was not of type str, but of type {type(ticker)}.\n"

    fmpsdk_query_handler   = FMPSDK_Query_Handler()
    yfinance_query_handler = Yfinance_Query_Handler()
    wrds_query_handler     = WRDS_Query_Handler()
    database_query_handler = Database_Query_Handler()

    # Often problems with fmpsdk. Manually input tickers.
    if len(competitors) == 0:
        competitors_found: List[str] = fmpsdk_query_handler.competitors(ticker = ticker, lower_multiple=0.1)

        # Check for competitors programatically, if this works, update global competitors list.
        # If this fails, fall back to the manually inputted competitors
        # If this list is empty, return an error
        if len(competitors_found) == 0:
            if len(competitors) == 0:
                warnings.warn(f"No competitors of {ticker} found.\nMight be problem with fmpsdk. Input tickers manually.", UserWarning)
                return None
        else:
            competitors = competitors_found

    if database_query_handler.get_ratios(tickers = competitors) is None:

        # Get the latest year found of the main ticker
        global historic_years
        latest_year: int = historic_years[0]

        years: List[int] = [latest_year, latest_year-1, latest_year-2]

        balance_sheets: pd.DataFrame = wrds_query_handler.balance_sheet(tickers = competitors, years = years)
        income_statements: pd.DataFrame = wrds_query_handler.income_statement(tickers = competitors, years = years)

        today = datetime.now()

        latest_share_prices: pd.DataFrame = yfinance_query_handler.ticker_prices_daily(tickers = competitors, 
                                                                         end = today,
                                                                         start = today - relativedelta(days = 3))["Close"].iloc[0]
        
        shares_outstanding: pd.DataFrame  = yfinance_query_handler.number_shares_outstanding(tickers = competitors)


        # Create a new dataframe to hold the information
        df = pd.DataFrame(index = competitors)

        # Add the data for the latest share prices
        df["Share Price"]        = latest_share_prices
        df["Shares outstanding"] = shares_outstanding

        # Market value of equities
        df["Equity Value"] = df["Share Price"] * df["Shares outstanding"] / 1_000_000 # In million USD

        # Get the necessary information from wrds
        latest_revenue, second_latest_revenues      = get_latest_second_latest(income_statements, "revenues")
        latest_cash, second_latest_cash             = get_latest_second_latest(balance_sheets, "cashandequivalents")
        latest_total_debt, second_latest_total_debt = [current_debt + non_current_debt for current_debt, non_current_debt in
                                                        zip(get_latest_second_latest(balance_sheets, "currentdebt"),  
                                                              get_latest_second_latest(balance_sheets, "longtermdebt"))]

        latest_ebitda, second_latest_ebitda         = [ebit + dna for ebit, dna in
                                                        zip(get_latest_second_latest(income_statements, "ebit"),
                                                            get_latest_second_latest(income_statements, "depreciationandamortisation"))]

        # Assign the revenues
        df["Revenues FY0"]  = latest_revenue
        df["Revenues FY-1"] = second_latest_revenues
    
        # Assign the EBITDA
        df["EBITDA FY0"]  = latest_ebitda
        df["EBITDA FY-1"] = second_latest_ebitda

        # Calculate and assign the enterprise value
        df ["Enterprise FY0"]  = df["Equity Value"] + latest_total_debt - latest_cash
        df ["Enterprise FY-1"] = df["Equity Value"] + second_latest_total_debt - second_latest_cash

        # Calculate and assign the EV/revenues
        df["EV/Revenues FY0"]  = df["Enterprise FY0"] / df["Revenues FY0"]
        df["EV/Revenues FY-1"] = df["Enterprise FY-1"] / df["Revenues FY-1"]

        # Calculate and assign the EV/EBITDA
        df["EV/EBITDA FY0"]  = df["Enterprise FY0"] / df["EBITDA FY0"]
        df["EV/EBITDA FY-1"] = df["Enterprise FY-1"] / df["EBITDA FY-1"]

        df["Long name"] = [yfinance_query_handler.company_name(ticker = ticker) for ticker in df.index]

        # Format the dataframe such that it matches the needed format
        df_formated = df[["Long name", "Equity Value", "Enterprise FY0", 
                        "EV/Revenues FY-1", "EV/Revenues FY0",
                        "EV/EBITDA FY-1", "EV/EBITDA FY0"]]

        return df_formated

def get_list_years(number_years: int)-> List[int]:
    """
    Returns a list of the number_years last years."""

    assert(isinstance(number_years, (int, float))), f"The number_years provided to get_list_years was not numeric, but of type {type(number_years)}.\n"

    current_year =  int(datetime.now().year)
    historic_years = [current_year - i for i in range(number_years)]

    return historic_years

def seed_years(doc:Excel_write, start_year: int, number_years:int)->None:
    """Writes the first years into the Excel document"""

    assert(isinstance(doc, Excel_write)),   f"The doc given to seed_years is not of type Excel_write, but of type {type(doc)}.\n"
    assert(isinstance(start_year, int)),    f"The start_year given to seed_years is not of type int, but of type {type(start_year)}.\n"
    assert(isinstance(number_years, int)),  f"The number_years given to seed_years is not of type int, but of type {type(number_years)}.\n"

    start_cell = "C2"
    sheet_name = "Income Statement Forecast"
    
    df = pd.DataFrame([year for year in range(start_year, start_year+1+number_years)], columns=["years"]).T
    
    doc.set_cells_pandas(start_cell = start_cell,sheet_name=sheet_name, df = df)

def get_latest_financial_statements(historic_years_number: int, ticker: str)->Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, int]:
    """
    Returns: (balance_sheet, income_statement, cashflow_statement, first_year)
    """
    assert(isinstance(historic_years_number, int)), f"The historic_years_number provided to get_latest_financial_statements is not of type int, but of type {type(historic_years_number)}.\n"
    assert(isinstance(ticker, str)),                f"The ticker provided to get_latest_financial_statements is not of type str, but of type {type(ticker)}.\n"

    def get_financial_statements(ticker:str, years: List[int])->Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Returns: (balance_sheet, income_statement, cashflow_statement)
        """

        wrds = WRDS_Query_Handler()

        # Catch warnings as errors
        with warnings.catch_warnings() as w:
            
            warnings.simplefilter("always")  # Catch Warnings

            balance_sheet: pd.DataFrame = wrds.balance_sheet(ticker = ticker, years = years)
            income_statement: pd.DataFrame = wrds.income_statement(ticker = ticker, years = years)
            cashflow_statement: pd.DataFrame = wrds.cash_flow_statement(ticker = ticker, years = years)

            if w:
                for warning_ in w:
                    print(warning_.message)
                raise FinancialStatementsNotFoundError
            else:
                return (balance_sheet, income_statement, cashflow_statement)
    
    global historic_years
    historic_years = get_list_years(historic_years_number)
    latest_year: int = historic_years[0]

    try:
        balance_sheet, income_statement, cash_flow_statement = get_financial_statements(ticker = ticker, years = historic_years)
    

    except Exception as _:
        # Exception raised if not yet released financial statements
        # Fall back to last year
        # If the error is persistent, then there is a problem with the query. In this case None is returned
        historic_years = get_list_years(historic_years_number + 1)[1::]
        latest_year -= 1 # Decrement the latest year
        try:
            balance_sheet, income_statement, cash_flow_statement = get_financial_statements(ticker = ticker, years = historic_years)
            warnings.warn(f"\nThe financial statements for {ticker} in year {datetime.now().year} are not available. Fall back on year {historic_years[0]}.\nThe financial statements might not yet be released.\n\n", 
                      UserWarning)
        except Exception as _:
            print(f"No financial Data could be found for company {ticker}")
            return (None, None, None, -1)


    return (balance_sheet, income_statement, cash_flow_statement, latest_year)

def check_years(historic_years_number: int, forecast_years_number: int)-> Tuple[int, int]:
    """Checks if the years used match the constraint of the Excel sheet.\n
    If they dont match, it warns the user and uses the respective minimum or maximum years\n
    Returns a tuple of (historic_years_number, forecast_years_number)"""

    assert(isinstance(historic_years_number, (int, float))), f"The historic_years_number give to check_years is not numeric, but of type {type(historic_years_number)}.\n"
    assert(isinstance(forecast_years_number, (int, float))), f"The forecast_years_number give to check_years is not numeric, but of type {type(forecast_years_number)}.\n"

    # Constraint from Excel template on how many years can be forecasted
    MAX_YEARS_FORECASTABLE: int = 10
    MAX_YEARS_HISTORIC: int = 10

    MIN_YEARS_HISTORIC: int = 3

    if forecast_years_number > MAX_YEARS_FORECASTABLE:
        warnings.warn(f"Trying to forecast {forecast_years_number} years, but the max years that can be forecasted are {MAX_YEARS_FORECASTABLE}.\nFall back to {MAX_YEARS_FORECASTABLE} years\n",
                      UserWarning)
        forecast_years_number = MAX_YEARS_FORECASTABLE
    elif forecast_years_number < 1:
        warnings.warn(f"Trying to forecast {forecast_years_number} years, but the min years that need to be forecasted is 1.\nFall back to 1 years\n",
                      UserWarning)
        forecast_years_number = 1

    if historic_years_number > MAX_YEARS_HISTORIC:
        warnings.warn(f"Trying to use {forecast_years_number} historic years, but the max historic years that can be used are {MAX_YEARS_HISTORIC}.\nFall back to {MAX_YEARS_HISTORIC} years\n",
                      UserWarning)
        historic_years_number = MAX_YEARS_HISTORIC
    elif historic_years_number < MIN_YEARS_HISTORIC:
        warnings.warn(f"Trying to use {forecast_years_number} historic years, but the min historic years that can be used are {MIN_YEARS_HISTORIC}.\nFall back to {MIN_YEARS_HISTORIC} years\n",
                      UserWarning)
        historic_years_number = MIN_YEARS_HISTORIC
    
    return (historic_years_number, forecast_years_number)

def prepare_and_save_excel(ticker: str, historic_years_number: int,forecast_years_number: int)->None:
    """
    Writes the DCF into the Excel document."""

    assert(isinstance(ticker, str)),                f"The ticker given to prepare_save_excel is not of type str, but of type {type(ticker)}.\n"
    assert(isinstance(historic_years_number, int)), f"The historic_years_number given to prepare_save_excel is not of type int, but of type {type(historic_years_number)}.\n"
    assert(isinstance(forecast_years_number, int)), f"The forecast_years_number given to prepare_save_excel is not of type int, but of type {type(forecast_years_number)}.\n"
    
    # Check if the years match the requirements of the excel template
    historic_years_number, forecast_years_number = check_years(historic_years_number = historic_years_number, forecast_years_number = forecast_years_number)

    balance_sheet, income_statement, cash_flow_statement, start_year = get_latest_financial_statements(ticker = ticker, historic_years_number = historic_years_number)

    # Case when this failed
    if balance_sheet is None:
        raise RuntimeError(f"No financial Statements for {ticker} found. DCF aborted.\n")

    name_of_file_inter: str = f"DCFs_folder/intermediateDCF/DCF_{ticker}_{start_year}.xlsx"
    name_file_final: str    = f"DCFs_folder/DCF_{ticker}_{start_year}.xls"


    yf_query_handler = Yfinance_Query_Handler()

    beta_equity: float      = yf_query_handler.beta_quity(ticker=ticker, time_frame_years=historic_years_number)
    risk_free_return: float = yf_query_handler.risk_free_rate()
    market_return: float    = yf_query_handler.snp500_return(time_frame_years = historic_years_number)
    industry: str           = yf_query_handler.industry(ticker = ticker)
    max_price, min_price    = yf_query_handler.high_low_52_weeks(ticker=ticker)
    name: str               = yf_query_handler.company_name(ticker = ticker)


    fmpsdk_query_handler = FMPSDK_Query_Handler()

    shares_outstanding: int = fmpsdk_query_handler.number_shares(ticker = ticker)


    competitor_info: Optional[pd.DataFrame] = get_competitor_info(ticker = ticker)

    with open_excel(path = "resources/DCF_template.xltm", mode = "w") as doc:

        # Reset the path to match the output file
        doc.path = name_of_file_inter

        doc["Ticker"]             = ticker
        doc["Forecasted_Years"]   = historic_years_number
        doc["Start_Year"]         = start_year
        doc["Years_Forecasted"]   = forecast_years_number
        doc["Beta_Equity"]        = beta_equity
        doc["Riskfree_Return"]    = risk_free_return
        doc["Market_Return"]      = market_return
        doc["Industry"]           = industry
        doc["Shares_Outstanding"] = shares_outstanding
        doc["High_Share_Price"]   = max_price
        doc["Low_Share_Price"]    = min_price
        doc["Name"]               = name


        doc.set_cells_pandas(start_cell = "C5", df = balance_sheet, sheet_name = "Balance Sheet Historic", index = False)
        doc.set_cells_pandas(start_cell="C5", df = income_statement, sheet_name = "Income Statement Historic", index = False)
        doc.set_cells_pandas(start_cell="C5", df = cash_flow_statement, sheet_name = "Cash flow statement Historic", index = False)

        # Case when competitor information was found
        if competitor_info is not None:
            doc.set_cells_pandas(start_cell="B23", df = competitor_info, sheet_name = "Comparable multiples", index = False)

        doc.save(path = name_file_final)

    print(f"\nFind the Excel containing the DCF under {name_file_final}.\n")

def main()-> None:
    def get_args(name: str, prompt: str, type)->Any:
        info_from_command: str = os.getenv(name)
        return type(info_from_command) if info_from_command is not None else type(input(prompt))

    # Get the important information by prompting the user
    print("\n")
    ticker:                str = get_args("ticker","Please select a ticker (Currently only NA supported): ", str).upper()
    historic_years_number: int = get_args("historic","Please select the number of historic years to consider: ", int)
    forecast_years_number: int = get_args("forecast","Please select the number of years to consider for the forecast: ", int)
    print("\n")

    # Run the program
    prepare_and_save_excel(
        ticker = ticker,
        historic_years_number = historic_years_number,
        forecast_years_number = forecast_years_number
    )


if __name__ == "__main__":
    main()