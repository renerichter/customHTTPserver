from abc import ABC, abstractmethod
from collections import OrderedDict
from random import randint
from time import perf_counter, time
from typing import Any, Optional

from ..controller.monitoring import CacheParams


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
    def __init__(self, capacity: int,age_limit:int,max_avg_length:int=500):
        self.cache:OrderedDict[str,Any]=OrderedDict()
        self.capacity = capacity
        self.age_limit = age_limit
        self._id = randint(0,99)
        self._name = f"LRU-Cache-{self._id:02d}"
        self.performance = CacheParams(self._name,str(self._id),max_avg_length)
    
    def get(self,key:str) -> Optional[str]:
        self.performance.add_request_time(time())
        if key in self.cache and time()-self.cache[key][1] <= self.age_limit:
            self.performance.add_cache_hit()
            self.cache.move_to_end(key)
            return self.cache[key][0]
        else:
            self.performance.add_cache_miss()
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
        self.cache.clear()
