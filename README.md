# **DCF_Engine**

## Overview
This file helps to create DCFs for listed companies of the S&P500 index. The DCF will be returned in an Excel file that can be further modified according to the user's estimations. The DCF uses a perpetuity with constant growth rate at the end of the period.

The Excel also shows other valuation methods such as comparable multiples and historic market valuations.

Note that the Excel file is mainly controlled through the "Assumptions" sheet. Further changes can be made to the other sheets, but they may need to be unlocked or unhidden.

For usage, the [dcf_initialiser](/code/dcf_initialiser.py) needs to be updated with the **company's Ticker**, the **Ticker of its competitors**, the **historic years** to take into account and the **years to forecast** for the DCF.

## Assumptions
The DCF is build on the following assumptions:
- **Growth of sales**:  Average throughout the historic period
- **Risk-free rate**:   10 year US treasury bills
- **Market return**:    Average return of S&P500 throughout the historic period
- **Beta Equity**:      Calculated based on other assumptions
- **Financial Ratios**: Average of the last years

## Problems & Work-to-be-done
While the code works, the Excel usually has problems. It raises a warning when opening and does not include the full Football field chart with all its info. This problem is likely due to the libraries used and not the code itself. This may be changed in the future.

So far, the code still expects hardcoded names in the [dcf_initialised](dcf_initialiser.py) file, as well as the duration of the forecast. In the future, this will be moved to the command line.  
In addition, the competitors need to be manually inputted and are not generated automatically. While the [fmpsdk](code/fmpsdk_query/fmpsdk_query.py) code has a method to query competitors, it does not work reliably and should not be used without manual double-checking.  
In the future, a database of the info should be established such that the financial data for companies does not need to be queried every time again.


## Dependencies
As the code queries multiple APIs for the necessary information, it has many dependencies. This includes the following unusual ones:  
- **wrds** (Wharton financial data for research projects) (Requires a valid account)  
- **yfinance**   
- **fmpsdk** (Requires valid, but free account)
- **pycel** and **openpyxl** (two libraries used for the interaction with excel)
