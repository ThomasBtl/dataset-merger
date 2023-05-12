from readers.excel_reader import ExcelReader
from readers.walstat_reader import WalstatReader
from readers.json_reader import JsonReader
from readers.reader import Reader
from utility import utility
import pandas as pd
import json
import numpy as np
import collections.abc
import copy

#https://stackoverflow.com/a/3233356
def deep_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

# Special json encoder for numpy type
# https://stackoverflow.com/a/57915246
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


def is_sources_valid(sources: dict) -> bool:

    """Function that verify if the yaml is valid

    Raises:
        ValueError: If mandatory keys have not been found for an entry
        SyntaxError: If one of the arguments of an entry is not of valid type

    Returns:
        bool: Return True if the sources file is valid. Raise an error otherwise.
    """

    mandatory_keys = [
        "type",
        "source_type",
        "look_in"
    ]

    # Iterate over every entries of the sources file.
    for key, entry in sources.items():
        if not all(k in entry.keys() for k in mandatory_keys):
            raise SyntaxError(f' --- sources.yaml --- entry {key} is missing some mandatory keys')

        valid_type = [
            "frame",
            "cells"
        ]

        if not isinstance(entry["type"], str) and entry["type"] not in valid_type:
            raise ValueError(f' --- sources.yaml - entry {key} --- {entry["type"]} is not of valid type')
        
        valid_source_type = [
            "xls",
            "walstat"
        ]

        if not isinstance(entry["source_type"], str) and entry["source_type"] not in valid_source_type:
            raise ValueError(f' --- sources.yaml - entry {key} --- {entry["source_type"]} is not of valid type')
        
        if not isinstance(entry["look_in"], list):
            for li in entry["look_in"]:
                if not isinstance(li, str) or not isinstance(entry["look_in"][li], str):
                    raise ValueError(f' --- sources.yaml - entry {key} --- {entry["look_in"]} is not of valid type')
            raise SyntaxError(f' --- sources.yaml - entry {key} --- {entry["look_in"]} is not of valid type')

        if entry["source_type"] == "xls":
            if "path" not in entry.keys():
                raise ValueError(f' --- sources.yaml --- entry {key} is of type \'xls\' but does not have attribute \'path\'')
            
            if entry["type"] == "cells" and "rows" not in entry.keys():
                raise SyntaxError(f' --- sources.yaml --- entry {key} is missing "rows" argument')

    return True

def modify_ins(df: pd.DataFrame) -> None:
    """Function that replace old ins code by new one

    Args:
        df (pd.DataFrame): The dataframe to modify. Modify in place.
    """
    ins_correspondance = [
        (55022, 58001),
        (56011, 58002),
        (56085, 58003),
        (56087, 58004),
        (52063, 55085),
        (52043, 55086),
        (55010, 51067),
        (55039, 51068),
        (55023, 51069),
        (54007, 57096),
        (54010, 57097)
    ]
    for old, new in ins_correspondance :
        df['ins'].replace(old, new, inplace=True)


def get_reader(source: object) -> Reader:
    """Function that return a specific reader depending on the source given.

    Args:
        source (object): A source object that follows the documented structure of sources.yaml.

    Returns:
        Reader: A reader to use in order to fetch data from source.
    """
    source_type = source["source_type"] # We know that such key exists because the .yaml file has been verify and "source_type" is a mandatoy key.
    if (source_type == "xls"):
        return ExcelReader(source["path"])
    
    if (source_type == "walstat"):
        return WalstatReader()
    
    if (source_type == "json"):
        return JsonReader(source["path"])

def fetch_data(reader: Reader, sheet_metadata: object, source_metadata: object, fetch_type: str) -> pd.DataFrame:
    """Function that fetch data from a source via a specific reader.

    Args:
        reader (Reader): The reader used to fetch data.
        sheet_metadata (object): Data concerning the current sheet.
        source_metadata (object): Data concerning the current source.
        fetch_type (str): The type of fetching to make (either "frame" or "cells").

    Returns:
        pd.Dataframe: A pandas DataFrame containing all the data that has been asked to fetch.
    """
    look_in = list(sheet_metadata.keys())[0]
    look_for = list(sheet_metadata.values())[0]
    options = source_metadata.get("options", None)

    if (fetch_type == "frame"):
        return reader.load_subset(look_in=look_in, look_for=look_for, options=options)
    
    if (fetch_type == "cells"):
        at_index = source_metadata.get("rows", [])
        return reader.load_values(look_in=look_in, look_for=look_for, at_index=at_index, options=options)

def dataToArray(data: pd.DataFrame, outer_key: str | None = None) -> pd.DataFrame:
    """Function that reduce all columns of a DataFrame into one containing an array of python dict.

    Args:
        data (pd.DataFrame): The dataframe to reduce

    Returns:
        pd.DataFrame: A reduced dataframe
    """
    def transform(serie):
        array_data = []
        for x in serie.index:
            array_data.append({
                "key" : x,
                "value" : serie[x]
            }) 
        return array_data

    if outer_key is not None:
        data["values"] = [transform(x) for _, x in data.loc[:, data.columns != outer_key].iterrows()]
    else :
        data["values"] = [transform(x) for _, x in data.loc[:, ].iterrows()]
    
    indexes = ['values'] + ([outer_key] if outer_key is not None else [])
    return data[indexes]


def main(sources: object) -> None:
    structure = {
        "communes" : {}
    }
    for source in sources.values():

        # Get the reader to use.
        reader = get_reader(source)

        # For the source, iterate over each specify sheets.
        sheets = source["look_in"] # sheets is a list of key-value pair.
        fetch_type = source["type"]
        outer_key = source.get("outer_group_on", None)

        group_source = None
        for sheet in sheets:
            data = fetch_data(reader, sheet, source, fetch_type)

            # Should columns be renamed.
            columns_to_rename = source.get("options", {}).get("columns_rename", None)
            if columns_to_rename:
                if (type(columns_to_rename) == dict) :  
                    sheet_name = list(sheet.keys())[0]
                    if sheet_name in columns_to_rename.keys():
                        data.rename(columns=columns_to_rename[sheet_name], inplace=True)
                else :
                    data = data.set_axis(columns_to_rename, axis=1)

            # Group sheets together.
            if group_source is None :
                group_source = data
            else:
                group_source = group_source.merge(data, left_on=source["inner_group_on"], right_on=source["inner_group_on"]) # If multiple sheets has been given, the attribute inner_group_on must be set.

        to_array = source.get("to_array", False)
        
        if (outer_key is not None):
            modify_ins(group_source)

        if (to_array) :
            group_source = dataToArray(group_source, outer_key)

        if outer_key is not None:
            group_source.set_index(outer_key, drop=True, inplace=True)

        data_json = group_source.T.to_dict()
        
        hirarchies = source.get("hierarchy", [])
        new_hierarchy = {}
        level_hierarchy = new_hierarchy
        for hirarchy in hirarchies:
            level_hierarchy[hirarchy] = {}
            level_hierarchy = level_hierarchy[hirarchy]
    
        if fetch_type == "frame":
            entry_keys = list(structure["communes"].keys())
            is_first = len(entry_keys) == 0
            for key, value in data_json.items():
                if key in entry_keys:
                    entry_keys.remove(key)
                level_hierarchy.update(value)

                if is_first :
                    structure["communes"][key] = {}

                if key in structure["communes"]:
                    structure["communes"][key].update(copy.deepcopy(new_hierarchy))

                level_hierarchy.update({})

            # Remove excess entry keys
            for i in entry_keys:
                del structure["communes"][i]
        else:
            for key in structure["communes"]:
                level_hierarchy.update(list(data_json.values())[0])
                deep_update(structure["communes"][key], new_hierarchy)

    # Write into json format
    with open("../data-export/json/raw-data.json", 'w') as f:
        json.dump(structure, fp=f, cls=NpEncoder)

if __name__ == "__main__":
    sources = utility.read_yaml("./sources.yaml")
    assert is_sources_valid(sources)

    main(sources)
