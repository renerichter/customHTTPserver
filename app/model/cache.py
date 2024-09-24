import asyncio
import json
from abc import ABC, abstractmethod
from collections import OrderedDict
from time import time
from typing import Any, Dict, Optional
from uuid import uuid4

import paho.mqtt.client as mqtt

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
    def __init__(self, capacity: int,age_limit:int,max_avg_length:int=500, broker_addr:str='localhost'):
        self.cache:OrderedDict[str,Any]=OrderedDict()
        self.capacity = capacity
        self.age_limit = age_limit
        self._id=str(uuid4())
        self._name = f"LRU-Cache-{self._id[:8]}"
        self.performance = CacheParams(self._name,str(self._id),max_avg_length)
        self.is_running =False
        self.broker_address = broker_addr
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect(self.broker_address,keepalive=120)
    
    def start(self):
        self.health_task=asyncio.create_task(self.publish_health())
        self.is_running=True
    
    def stop(self):
        self.is_running=False
        if self.health_task:
            self.health_task.cancel()
    
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
    
    def get_info(self)->Dict[str,Any]:
        return {'name':self._name,
                'id': self._id,
                'age_limit': self.age_limit,
                'capacity': self.capacity,
                'cache_fill': len(self.cache),
                'performance_params': self.performance
                }
    
    async def publish_health(self):
        while True:
            if not self.mqtt_client.is_connected():
                self.mqtt_client.connect(self.broker_address,keepalive=120)
            self.mqtt_client.publish(f"health/{self._id}",json.dumps(self.performance.get_perf_report()))
            await asyncio.sleep(10)