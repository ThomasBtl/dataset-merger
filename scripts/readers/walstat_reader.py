import pandas as pd
import logging
import requests
from .reader import Reader

class WalstatReader(Reader):

    def __init__(self) -> None:
        self.base_url = "https://opendata.iweps.be/api/data/json/"
        self.df = pd.DataFrame() # Empty dataframe.

    def load_subset(self, look_in: str, look_for: str | list[str] | None = None, options: dict = {}) -> pd.DataFrame:
        # look_for must be of type list here.
        if not isinstance(look_for, list):
            look_for = [look_for]

        # Check if there is a period to consider for this indicator
        period = options.get("period", None)
        if period :
            period = period.get(look_in, None)

        struct = {"ins" : []}
        
        # NOTE : If we try to fetch for more than 1 period then it will not work.
        # If there is a period set in the config file, it is better to rename the columns anyway.
        struct["valeur"] = []
        if "columns_names" in options.keys():
            for col in options["columns_names"].get(look_in, []) :
                struct[col] = []
                struct.pop("valeur", None)

        df = pd.DataFrame(data=struct)
        for ins in look_for:
            url = self.base_url + f'{look_in}/ins={ins}' + ("+period=last" if not period else '')
            try :
                response = requests.get(url)
                response.raise_for_status() # If status is != 2xx raise an error.
                
                # Is the page content empty
                if response.status_code == 204:
                    raise ValueError("No Content")
                
                response = response.json()
                data = [
                    ins,
                    *list(map(lambda y: y['valeur'], filter(lambda x : int(x['periode'].split('/')[-1]) in period, response) if period else response)) 
                ]

                df.loc[len(df)] = data

            except Exception as e:
                logging.warning(f'ins={ins} raised an error')
                logging.error(e)
        
        return df
    
    def load_values(self, look_in: str, look_for: str | list[str] | None = None, at_index: int = 1, options: dict = {}) -> pd.DataFrame:
        return super().load_values(look_in, look_for, at_index, options)
