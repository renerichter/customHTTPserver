from abc import abstractmethod
from typing import Any, Dict, List, Tuple, Union


class Parser:
    @abstractmethod
    def parse_one(self, source: str ) -> List[str] | Any:
        pass
    
    @abstractmethod
    def parse_complete(self,source:str|List[str])->List[List[str]]:
        pass

class CsvParser(Parser):
    def __init__(self,skip_header:bool=True):
        self.skip_header = skip_header
    
    def set_skip_header(self,skip_header:bool):
        self.skip_header = skip_header
    
    def parse_one(self, source: str) -> List[str] | Any:
        # make sure that a string for the path is given
        assert isinstance(source,str), "File path must be of type string"
        
        # catch if the file not exists
        try:
            with open(source,"r") as f:
                if self.skip_header: next(f)
                # use a generator pattern to save storage, in case of big files
                for csv_line in f:
                    yield csv_line.strip().split(",")
        except FileNotFoundError:
            raise ValueError(f"File {source} not found.")
    
    def parse_complete(self,source:str|List[str])->List[List[str]]:
        if isinstance(source,str):
            result = list(self.parse_one(source))
        else: 
            raise NotImplementedError("Parsing of lists of files not implemented for csvParser yet.")
        
        return result

class JsonParser(Parser):
    
    def _parse_string(self,idx:int) -> Tuple[str,int]:
        nidx = 0
        nidx+=idx
        while self.source[nidx] != '"':
            nidx+=1
        #nidx+=1
        return self.source[idx:nidx],nidx+1
    
    def _parse_array(self,idx:int) -> Tuple[List[Any],int]:
        nidx = 0
        nidx+=idx
        new_array = []
        while self.source[nidx] != ']':
            value,nidx = self._parse_value(nidx)
            new_array.append(value)
            if self.source[idx] == ',':
                nidx +=1
        return new_array, nidx+1
    
    def _parse_number(self,idx:int) -> Tuple[float,int]:
        nidx = 0
        nidx +=idx
        while self.source[nidx] in '0123456789.-eE':
            nidx+=1
        return float(self.source[idx:nidx]),nidx
    
    
    def _parse_value(self,idx:int) -> Tuple[Any,int]:
        nidx = 0
        nidx+=idx
        match self.source[nidx]:
            case '"':
                return self._parse_string(nidx+1)
            case '{':
                return self._parse_dict(nidx+1)
            case '[':
                return self._parse_array(nidx+1)
            case _ if self.source[nidx].isdigit() or self.source[nidx]=='-':
                return self._parse_number(nidx)
            case _ if self.source[nidx:nidx+4] == 'true':
                return True, nidx+4
            case _ if self.source[nidx:nidx+5] == 'false':
                return False, nidx+5
            case _ if self.source[nidx:nidx+4] == 'null':
                return None, nidx+4
            case _:
                raise ValueError(f"Unknown Datatype formatting entry-point found. Please check the raw string around {nidx=}.")
            
        
    def _parse_dict(self,idx:int) -> Tuple[Dict[Any,Any],int]:
        # searches for ':' 
        nidx=0
        nidx+=idx
        new_object:Dict[str,Any] = {}
        key,value = None,None
        while self.source[nidx] != '}':
            match self.source[nidx]:
                case '"': # assuming string keys (not tuple or numbers)
                    key,key_end_idx = self._parse_string(nidx+1)
                    nidx = key_end_idx
                case ':':
                    #nidx+=1
                    value,value_end_idx = self._parse_value(nidx+1)
                    nidx=value_end_idx
                    new_object[key]=value
                case ',':
                    nidx+=1
                case _:
                    raise ValueError(f"No matching case found in _parse_dict subroutine at {nidx=}.")
        return new_object,nidx
    
    def parse_one(self, source: str) -> List[str] | Any:
        self.source=source
        self.parsed_source , _ = self._parse_value(0)
        return self.parsed_source
        
    
    def parse_complete(self,source:str | List[str])->List[Any]:
        parsed_list:List[Any] = []
        for item in source:
            parsed_list.append(self.parse_one(item))
        return parsed_list
                             
class ParserFactory:
    def __init__(self,parser_history:List[Parser]=[]):
        self._parser_history = parser_history
    
    def getParser(self,parser:str) -> Parser:
        match parser:
            case 'csv': 
                parser = CsvParser()
            case 'json': 
                parser = JsonParser()
            case _:
                raise ValueError("Parser not existing.")
        self._parser_history.append(parser)
        return parser
    