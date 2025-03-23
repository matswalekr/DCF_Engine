from fmpsdk_query import FMPSDK_Query_Handler
from yfinance_query import Yfinance_Query_Handler
from wrds_query import WRDS_Query_Handler
from database_query import DATABASE_QUERY_HANDLER
import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from typing import Tuple

def get_latest_second_latest(statement: pd.DataFrame, column: str)->Tuple[pd.DataFrame, pd.DataFrame]:
    """Returns a tuple of (latest_value, second_latest_value)"""
    sorted_statement = statement.sort_index(level="year", ascending=False).loc[column]
    latest_value = sorted_statement.groupby("ticker").first()
    second_latest_value = sorted_statement.groupby("ticker").nth(1).droplevel("year")
    return (latest_value, second_latest_value)


def main()-> None:

    fmpsdk_query_handler = FMPSDK_Query_Handler()
    yfinance_query_handler = Yfinance_Query_Handler()
    wrds_query_handler = WRDS_Query_Handler()
    database_query_handler = DATABASE_QUERY_HANDLER()


    ticker = "AAPL"

    #competitors = fmpsdk_query_handler.competitors(ticker = ticker, lower_multiple=0)
    competitors = ["GOOGL", "DELL", "MSFT", "NFLX"]

    if database_query_handler.get_ratios(tickers = competitors) is None:

        balance_sheets: pd.DataFrame = wrds_query_handler.balance_sheet(tickers = competitors, years = [2024, 2023,2022])
        income_statements: pd.DataFrame = wrds_query_handler.income_statement(tickers = competitors, years = [2024, 2023,2022])

        today = datetime.now()
        latest_share_prices = yfinance_query_handler.ticker_prices_daily(tickers = competitors, 
                                                                         end = datetime.now(),
                                                                         start = today - relativedelta(days = 3))["Close"].iloc[0]
        
        shares_outstanding: pd.DataFrame = yfinance_query_handler.number_shares_outstanding(tickers = competitors)


        # Create a new dataframe to hold the information
        df = pd.DataFrame(index = competitors)

        # Add the data for the latest share prices
        df["Share Price"] = latest_share_prices
        df["Shares outstanding"] = shares_outstanding

        # Market value of equities
        df["Equity Value"] = df["Share Price"] * df["Shares outstanding"] / 1_000_000 # In million USD

        # Get the necessary information from wrds
        latest_revenue, second_latest_revenues = get_latest_second_latest(income_statements, "revenues")
        latest_cash, second_latest_cash = get_latest_second_latest(balance_sheets, "cashandequivalents")
        latest_total_debt, second_latest_total_debt = [current_debt + non_current_debt 
                                                       for current_debt, non_current_debt in
                                                        zip(get_latest_second_latest(balance_sheets, "currentdebt"),  
                                                              get_latest_second_latest(balance_sheets, "longtermdebt"))]

        latest_ebitda, second_latest_ebitda = [ebit + dna 
                                               for ebit, dna in
                                               zip(get_latest_second_latest(income_statements, "ebit"),
                                                   get_latest_second_latest(income_statements, "depreciationandamortisation"))]

        # Assign the revenues
        df["Revenues FY0"] = latest_revenue
        df["Revenues FY-1"] = second_latest_revenues
    
        # Assign the EBITDA
        df["EBITDA FY0"] = latest_ebitda
        df["EBITDA FY-1"] = second_latest_ebitda

        # Calculate and assign the enterprise value
        df ["Enterprise FY0"] = df["Equity Value"] + latest_total_debt - latest_cash
        df ["Enterprise FY-1"] = df["Equity Value"] + second_latest_total_debt - second_latest_cash

        # Calculate and assign the EV/revenues
        df["EV/Revenues FY0"] = df["Enterprise FY0"] / df["Revenues FY0"]
        df["EV/Revenues FY-1"] = df["Enterprise FY-1"] / df["Revenues FY-1"]

        # Calculate and assign the EV/EBITDA
        df["EV/EBITDA FY0"] = df["Enterprise FY0"] / df["EBITDA FY0"]
        df["EV/EBITDA FY-1"] = df["Enterprise FY-1"] / df["EBITDA FY-1"]

        df["Long name"] = [yfinance_query_handler.company_name(ticker = ticker) for ticker in df.index]

        # Format the dataframe such that it matches the needed format
        df_formated = df[["Long name", "Equity Value", "Enterprise FY0", 
                        "EV/Revenues FY-1", "EV/Revenues FY0",
                        "EV/EBITDA FY-1", "EV/EBITDA FY0"]]

        return df_formated

if __name__ == "__main__":
    main()