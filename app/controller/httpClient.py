from http.client import HTTPSConnection
from typing import Any, List

from ..controller.parser import ParserFactory


class HttpClient:
    def __init__(self,api_url:str):
        self._api_url = api_url
        self._connection = HTTPSConnection(api_url)
        self._parser = ParserFactory().getParser('json')
    
    def get(self,query:str) -> List[Any]:
        self._connection.request("GET",query)
        self._response = self._connection.getresponse()
        self.data = self._response.read().decode('utf-8')
        self.data = self._parser(self.data)
        self._connection.close()
        return self.data
        

        
        
        
