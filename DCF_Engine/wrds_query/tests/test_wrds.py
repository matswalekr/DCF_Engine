import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from wrds_query import WRDS_Query_Handler
import pandas as pd
import unittest
from typing import Any


class Test_WRDS_QUERY_HANDLER(unittest.TestCase):
    def setUp(self)-> None:
        self.query_ = WRDS_Query_Handler()


    def test_accounting(self)-> None:
        tickers = ["MSFT", "TSLA", "GOOGL"]
        years = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
        #ticker = "MSFT"
        #year = 2021

        for ticker in tickers:
            for year in years:
                data: pd.DataFrame = self.query_.income_statement(ticker = ticker, year = year)
                self.assertFalse(data.empty)

        self.accounting(data = data, ticker = ticker, year = year)
    

    def accounting(self, data: pd.DataFrame, ticker: str, year: int) -> None:
        
        def get_values(row:str)-> Any:
            output: int = data.loc[row, (ticker, year)]
            if output is None:
                return 0
            else:
                return output


        self.assertEqual(get_values("revenues")- get_values("cogs"), get_values("grossmargin"))

        self.assertEqual(get_values("grossmargin") - (get_values("sellinggeneralandadministrativeexpense") + get_values("depreciationandamortisation")), get_values("operatingincome"))

        self.assertEqual(get_values("operatingincome") + get_values("nonoperationalresult") + get_values("specialitems"), get_values("ebit"))

        self.assertEqual(get_values("ebit")- get_values("netinterest"), get_values("ebt"))

        self.assertEqual(get_values("ebt") - get_values("tax"), get_values("incomebeforeextraordinary"))

    def main():
        conn = WRDS_Query_Handler()
        print(conn.income_statement(tickers = ["MSFT", "TSLA"], years = [2022, 2021]))

    if __name__ == "__main__":
        main()