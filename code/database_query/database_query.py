import sqlite3
import pandas as pd

class Generalised_Database_Query_Handler():

    def __init__(self, db:str)->None:
        self.db_name = db
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

    def query(self, query:str)->pd.DataFrame:
        """Handles a query in SQL on the databse"""

        self.cursor.execute(_sql = query)

        data = self.cursor.fetchall()

        return data
    
    def update_db(self, query: str, save:bool = True)->None:
        """Function to update the structure of the database"""

        self.cursor.execute(_sql = query)

        if save:
            self.conn.commit()
        
    def __del__(self)->None:
        self.conn.close()


class Database_Query_Handler(Generalised_Database_Query_Handler):

    def __init__(self)->None:
        db = "examp.db"    
        super().__init__(db = db)

    def get_balance_sheet(*args, **kwargs)->pd.DataFrame:
        return None
    
    def get_ratios(*args, **kwargs)->pd.DataFrame:
        return None
    
    
