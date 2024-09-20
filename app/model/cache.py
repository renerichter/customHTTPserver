from abc import ABC, abstractmethod
from collections import OrderedDict
from time import time
from typing import Any, Optional


class Cache(ABC):
    @abstractmethod
    def __init__(self,capacity:int,age_limit:int):
        pass
    
    @abstractmethod
    def get(self,key:str) -> Optional[str]:
        pass
    
    @abstractmethod
    def put(self,key:str,value:str):
        pass
    
    @abstractmethod
    def invalidate(self,key:str):
        pass
    
    @abstractmethod
    def clear(self):
        pass

class LruCache(Cache):
    def __init__(self, capacity: int,age_limit:int):
        self.cache:OrderedDict[str,Any]=OrderedDict()
        self.capacity = capacity
        self.age_limit = age_limit
    
    def get(self,key:str) -> Optional[str]:
        if key in self.cache and time()-self.cache[key][1] <= self.age_limit:
            self.cache.move_to_end(key)
            return self.cache[key][0]
        else:
            return None
    
    def put(self,key:str,value:str):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value,time()
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
    
    def invalidate(self,key:str):
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        self.cache.clear()
