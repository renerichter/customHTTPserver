from abc import abstractmethod
from typing import Any, List


class Parser:
    @abstractmethod
    def parse_one(self, file_path: str) -> List[str] | Any:
        pass
    
    @abstractmethod
    def parse_complete(self,file_path:str)->List[str]:
        pass

class CsvParser(Parser):
    def __init__(self):
        pass
    
    def parse_one(self, file_path: str,skip_header:bool=False) -> List[str] | Any:
        # make sure that a string for the path is given
        assert isinstance(file_path,str), "File path must be of type string"
        
        # catch if the file not exists
        try:
            with open(file_path,"r") as f:
                if skip_header: next(f)
                # use a generator pattern to save storage, in case of big files
                for csv_line in f:
                    yield csv_line.strip().split(",")
        except FileNotFoundError:
            raise ValueError(f"File {file_path} not found.")
    
    def parse_complete(self,file_path:str)->List[List[str]]:
        return list(self.parse_one(file_path,skip_header=True))
                                