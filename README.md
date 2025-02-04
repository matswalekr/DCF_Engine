# **DCF_Engine**

## Usage
So far, the code still expects hardcoded names in the [dcf_initialised](dcf_initialiser.py) file, as well as the duration of the forecast. In the future, this will be moved to the command line.

## Problems
While the code works, the Excel usually has problems. It raises a warning when opening and does not include a full Football field chart. This may be changed in the future.


## Dependencies
As the code queries multiple APIs for the necessary information, it has many dependencies. This includes the following unusual ones:  
- **wrds** (Wharton financial data for research projects) (Requires a valid account)  
- **yfinance**   
- **fmpsdk** (Requires valid, but free account)
- **pycel** and **openpyxl** (two libraries used for the interaction with excel)

