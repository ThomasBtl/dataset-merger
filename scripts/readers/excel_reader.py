import pandas as pd
from .reader import Reader
import logging
import os
import numpy as np

class ExcelReader(Reader):

    def __init__(self, path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(f'--- ExcelReader --- __init__ --- {path} was not found')
        
        self.path = path
        self.df = pd.DataFrame() # Empty dataframe.

    def load_subset(self, look_in: str, look_for: str | list[str] | None = None, options: dict = {}) -> pd.DataFrame:
        try:

            if options:
                skiprows = options.get("skiprows", None)
                title_row_index = options.get("title_row_index", 1) - 1
            
            if skiprows:
                if isinstance(skiprows, list):
                    skiprows = range(skiprows[0], skiprows[1])
                else:
                    # Pandas's read_excel method can interprete int value as skiprow but does not have the same behaviour as we want it to have
                    # If an int is encoced, parse it as a list
                    skiprows = [skiprows - 1]

            # A list can be interpreted by pandas's read_excel method.
            # To avoid loading multiple sheets incorrectly, only consider the first element of the list to be the sheet to retreived.
            if isinstance(look_in, list):
                look_in = look_in[0]

            self.df = pd.read_excel(self.path, sheet_name=look_in, usecols=look_for, skiprows=skiprows, header=title_row_index)
            # self.df["date"] = self.df["date"].astype(str)
            self.df = self.df.replace(np.nan, 0)
            return self.df
        except ValueError as ve:
            logging.error(ve)

    def load_values(self, look_in: str, look_for: str | list[str], at_index: list[int] | None = [], options: dict = {}) -> pd.DataFrame:
        try:

            # If no option for title row index is given, we consider that the titles of the columns are placed at row index 1.
            title_row_index = options["title_row_index"] if options and "title_row_index" in options.keys() else 1

            # A list can be interpreted by pandas's read_excel method.
            # To avoid loading multiple sheets incorrectly, only consider the first element of the list to be the sheet to retreived.
            if isinstance(look_in, list):
                look_in = look_in[0]

            df = pd.read_excel(self.path, sheet_name=look_in, usecols=look_for, skiprows=range(0, title_row_index - 1))

            # Note that this will only work if the row is located lower in the documents than the column name.
            # It seems logical that the title of the columns will be placed at a row strictily before the rows containing the actual data so this code is based on this hypothesis.
            df = df.iloc[[index - title_row_index - 1 for index in at_index]]

            if options.get("transpose", False):
                return df.T
            return df
        except ValueError as ve:
            logging.error(ve)