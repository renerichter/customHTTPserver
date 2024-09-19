from abc import ABC, abstractmethod
from threading import Thread
from typing import Any, Dict, List, Optional

from ..model.database import DatabaseConnection, travelCRUD
from .httpServer import HTTPserver
from .names import CreativeNamer


class Node:
    def __init__(self,crud:travelCRUD,host:str,port:int,node_name:str):
        self._host = host
        self._port = port
        self._crud = crud
        self._httpServer = None
        self._thread = None
        self._name = node_name
    
    def start(self):
        self._httpServer=HTTPserver(self._crud,self._host,self._port)
        self._thread = Thread(target=self._httpServer.start)
        self._thread.start()
    
    def stop(self):
        if self._httpServer:
            print("Node {self._name} here again -> ",end="");
            self._httpServer.stop()
        if self._thread:
            self._thread.join()
        print("\n----------------Bye 😜----------------\n")
        
    def __str__(self):
        res = "Hiho, node {self._name} here. 👋"
        res += "\n------------------------------------\n"
        res += "> Running on {self._host}:{self._port}.\n"
        res += "> Using crud={self._crud} and server-type={self._httpServer}."
        res += "> **Thread-Status**={self._thread}"
        res += "\n------------------------------------\n"
        return res

class LoadBalancer(ABC):
    @abstractmethod
    def get_next_node(self) -> Node:
        pass

class RoundRobinBalancer(LoadBalancer):
    def __init__(self,nodes:List[Node]):
        self._nodes = nodes
        self._current_idx = 0
    
    def get_next_node(self) -> Node:
        node = self._nodes[self._current_idx]
        self._current_idx = (self._current_idx + 1)%len(self._nodes)
        return node

class RandomBalancer(LoadBalancer):
    pass

class WeightedRoundRobin(LoadBalancer):
    pass

class DistributedBookingSystem:
    def __init__(self,db:DatabaseConnection, db_params: Dict[str,Any], table_name:str):
        self._nodes:List[Node] = []
        self._load_balancer: Optional[LoadBalancer] = None
        self._db = db
        self._db_params = db_params
        self._table_name = table_name
        self._namer = CreativeNamer()
    
    def add_node(self,host:str,port:int):
        crud = cachedTravelCRUD(self._db,self._db_params,self._table_name)
        node = Node(crud,host,port,self._namer.create_name(1))
    
    def start(self):
        pass
    
    def set_load_balancer(self):
        pass
    
    def stop(self):
        pass

    def handle_request(self,request:Dict[str,Any]):
        pass