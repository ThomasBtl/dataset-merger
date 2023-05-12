from abc import ABC, abstractmethod
import pandas as pd

class Reader(ABC):
    
    @abstractmethod
    def load_subset(self, look_in: str, look_for: str | list[str] | None = None, options: dict = {}) -> pd.DataFrame:
        pass

    @abstractmethod
    def load_values(self, look_in: str, look_for: str | list[str] | None = None, at_index: list[int] | None = [], options: dict= {}) -> pd.DataFrame:
        pass