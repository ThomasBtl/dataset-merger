from .reader import Reader
import json
import pandas as pd
import os

class JsonReader(Reader):

    def __init__(self, path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(f'--- JsonReader --- __init__ --- {path} was not found')
        
        self.path = path

    def load_subset(self, look_in: str, look_for: str | list[str] | None = None, options: dict | None = {}) -> pd.DataFrame:

        if not isinstance(look_for, list):
            look_for = look_for.replace(' ', '').split(',')

        with open(self.path) as f:
            data = json.load(f)

            new_data = {}
            if look_in == "all":
                if "all" in look_for :
                    new_data = data
                else :
                    for key, value in data.items():
                        new_data[key] = {}
                        for col in look_for:
                            new_data[key][col] = value.get(col, None)
            else:    
                if look_for == "all":
                    for entry in look_in:
                        new_data[entry] = data.get(entry, None)
                else :
                    for value in data[look_in].values():
                        new_data[look_in] = {}
                        for col in look_for:
                            new_data[look_in][col] = value.get(col, None)

            df = pd.DataFrame(data=new_data)
            
            if options.get("transpose", False):
                return df.T
            return df

    def load_values(self, look_in: str, look_for: str | list[str], at_index: list[int] | None = [], options: dict = {}) -> pd.DataFrame:
       
        with open(self.path) as f:
            data = json.load(f)

            if not isinstance(look_for, list):
                look_for = look_for.replace(' ', '').split(',')
            
            new_data = {
                look_in: {}
            }

            for col in look_for:
                new_data[look_in][col] = data[look_in][col] 

            df = pd.DataFrame(data=new_data, index=look_for)

            if options.get("transpose", False):
                return df.T
            return df
