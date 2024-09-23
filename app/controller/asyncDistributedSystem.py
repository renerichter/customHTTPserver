import asyncio
import time
from abc import ABC, abstractmethod
from asyncio import StreamReader, StreamWriter
from logging import Logger, getLogger
from random import randint
from time import perf_counter
from typing import Any, Dict, List, Tuple

import psutil

from ..model.database import DatabaseConnection, cachedTravelCRUD
from .asyncHttpServer import AsyncHttpServer
from .logger import LoggerSetup, RequestContext
from .names import CreativeNamer
from .taskQueue import TaskQueue


class asyncNode:
    def __init__(self,crud:cachedTravelCRUD,host:str,port:int,node_name:str,node_id:int,parent_logger:Logger,nbr_qworkers:int=3,qsize:int=5):
        self.host = host
        self.port = port
        self._crud = crud
        self._httpServer = None
        self._thread = None
        self._name = node_name
        self._id = node_id
        self._logger = parent_logger.getChild(f"Node-{self._id:02d}")
        self.task_queue = TaskQueue(self._logger,f"LocalTQ-Node{self._id}",nworkers=nbr_qworkers,qsize=qsize)
        
    
    async def start(self):
        await self.task_queue.start()
        self._httpServer=AsyncHttpServer(self._crud,self.task_queue,self.host,self.port,self._logger)
        self._thread = asyncio.create_task(self._httpServer.start())
        self._logger.info(self)
    
    async def stop(self):
        if self._httpServer:
            await self._httpServer.stop()
        if self._thread:
            await self._thread
        await self.task_queue.stop()
        
        self._logger.info("%s\n------->>-------Bye 😜------->>-------\n",self)

    
    async def health_check(self) -> bool:
        try:
            cpu_usage = psutil.cpu_percent(interval=1) 
            mem_available = psutil.virtual_memory().available /1024/1024
            return cpu_usage < 90 and mem_available > 100
        except Exception as e: 
            self._logger.error("Health check failed for node %s on port %d: %s",self._name,self.port,str(e),exc_info=True)
            return False
        
    async def health_report(self):
        start_time=time.perf_counter()
        cpu_usage = psutil.cpu_percent(interval=1) 
        mem_usage = psutil.virtual_memory().percent
        mem_available = psutil.virtual_memory().available / (1024 * 1024)
        disk_usage = psutil.disk_usage('/').percent        
        
        await asyncio.sleep(0.1)
        # health check latency
        latency = (time.perf_counter() -start_time)*1000 #ms
        
        return {
            "cpu_usage": cpu_usage,
            "ram_usage": mem_usage,
            "ram_available": mem_available,
            "disk_usage": disk_usage,
            "latency_ms": latency
        }
    
    def get_node_info(self)->Dict[str,Any]:
        return {'name': self._name, 
                'host': self.host,
                'port': self.port,
                'id':   self._id,
                'crud': str(self._crud),
                'http': str(self._httpServer),
                'thread': str(self._thread)
                }

    
    def __str__(self):
        return f"Node ~*>{self._name}<*~ running on {self.host}:{self.port}"

class asyncLoadBalancer(ABC):
    @abstractmethod
    def get_next_node(self,context: RequestContext) -> asyncNode:
        pass

    @abstractmethod
    def update_nodes_list(self,new_nodes:List[asyncNode]):
        pass
    
    @abstractmethod
    async def do_health_checks(self)->List[asyncNode]:
        pass

    @abstractmethod
    async def get_health_reports(self) -> Dict[str,Dict[str,Any]]:
        pass

class asyncRoundRobinBalancer(asyncLoadBalancer):
    def __init__(self,nodes:List[asyncNode],parent_logger:Logger):
        self._nodes = nodes
        self._current_idx = 0
        self._name = f"LB-RR-{randint(0,9)}"
        self._logger = parent_logger.getChild(self._name)
    
    def get_next_node(self,context: RequestContext) -> asyncNode:
        start_time = perf_counter()
        if len(self._nodes) == 0:
            self._logger.error("No Nodes for routing left.")
            raise ValueError("No Nodes for routing left")
        node = self._nodes[self._current_idx]
        self._current_idx = (self._current_idx + 1)%len(self._nodes)
        context.add_response_time(self._name,perf_counter()-start_time)
        return node

    def update_nodes_list(self,new_nodes:List[asyncNode]):
        self._nodes = new_nodes
        self._current_idx = self._current_idx % len(new_nodes)

    async def do_health_checks(self)->List[asyncNode]:
        death_book:List[asyncNode] = []
        for node in self._nodes: 
            if not await node.health_check():
                death_book.append(node)
        
        for node in death_book:
            self._nodes.remove(node)
        return death_book
    
    async def get_health_reports(self) -> Dict[str, Dict[str, Any]]:
        reports:Dict[str, Dict[str, Any]] = {}
        for node in self._nodes:
            reports[node.get_node_info()['name']] = await node.health_report()
        return reports
            


class asyncDistributedBookingSystem:
    def __init__(self,host:str,port:int,db:DatabaseConnection, db_params: Dict[str,Any], table_name:str,global_q_params:Tuple[int,int],q_params:Tuple[int,int],logger_setup:LoggerSetup,logger_level:str):
        self.host = host
        self.port = port
        self._nodes:List[asyncNode]=[]
        self._load_balancer: asyncLoadBalancer = None
        self._db = db
        self._db_params = db_params
        self._table_name = table_name
        self._namer = CreativeNamer()
        self._server = None
        self._is_running = False
        self._qparams = q_params
        self._logger_setup = logger_setup
        self._logger_level = logger_level
        
        # start logger
        self._logger_setup.setup_logging()
        self._logger=getLogger('DBS')
        
        # task queue
        self._global_task_queue = TaskQueue(self._logger,name="GlobalTaskQueue",nworkers=global_q_params[0],qsize=global_q_params[1])
    
    def add_node(self,host:str,port:int):
        crud = cachedTravelCRUD(self._db,self._db_params,self._table_name)
        node_id = len(self._nodes)
        node = asyncNode(crud,host,port,self._namer.create_name(1),node_id,parent_logger=self._logger)
        self._nodes.append(node)
        
        if self._load_balancer:
            self._load_balancer.update_nodes_list(self._nodes)
        
    async def delete_node(self,node_id:int):    
        if ~ await self.stop_node(node_id):
            del self._nodes[node_id]
            
    async def stop_node(self,node_id:int):
        if node_id >= len(self._nodes):
            self._logger.error(f"Node ID=%d not found",node_id)
            return 1
        else:
            self._logger.info(">>> Stopping node %s...",self._nodes[node_id])
            await self._nodes[node_id].stop()
            return 0

    def set_load_balancer(self,balancer_type:str):
        match balancer_type:
            case "roundrobin":
                self._load_balancer = asyncRoundRobinBalancer(self._nodes,self._logger)
            case _:
                self._load_balancer = asyncRoundRobinBalancer(self._nodes,self._logger)
                self._logger.info("No logger given or given logger name: %s unknown. Chose default balancer roundrobin.",balancer_type)
    
    async def start(self):        
        self._logger.info("DBS --> Starting up...")
        await self._global_task_queue.start()
        
        # start nodes
        for node in self._nodes:  
            await node.start()
        
        self._server = await asyncio.start_server(self.handle_connection,self.host,self.port)
        self._is_running = True
        self._logger.info("DBS ---> Listening on %s:%d.",self.host,self.port)
        asyncio.create_task(self.health_check_routine())

        async with self._server:
            await self._server.serve_forever()    

    async def stop(self):
        self._logger.info("DistributedBookingSystem ---> Stopping all Nodes...")
        self._is_running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        for node in self._nodes:
            await node.stop()
        
        await self._global_task_queue.stop()
        await self._logger_setup.stop_logging()


    async def handle_connection(self,reader: StreamReader, writer:StreamWriter):
        context = RequestContext()
        node=self._load_balancer.get_next_node(context)
        self._logger.info("-------------- Active node=%d.----------",node.port)
        try: 
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                #await self._global_task_queue.add_task(self.process_request,data,context,writer)
                response,context = await self.forward_data(data,node,context)
                writer.write(response)
                await writer.drain()
        except Exception as e: 
            self._logger.error("Error handling client request: %s",str(e),extra={'trace_context': context.to_dict()},exc_info=True)
            raise
        finally:
            writer.close()
            await writer.wait_closed()
            self._logger.info("Connection closed",extra={'trace_context': context.to_dict()})
    
    # async def process_request(self,data:bytes,context:RequestContext, writer:StreamWriter):
    #     node=self._load_balancer.get_next_node(context)
    #     self._logger.info("-------------- Active node=%d.----------",node.port)
    #     response,context = await self.forward_data(data,node,context)
    #     writer.write(response)
    #     await writer.drain()
    #     writer.close()
    #     await writer.wait_closed()
    
    async def forward_data(self,data:bytes,node:asyncNode,context:RequestContext):
        reader,writer = await asyncio.open_connection(node.host,node.port)
        try:
            writer.write(data)
            await writer.drain()
            response = await reader.read(1024)
            context.add_response_time(f"Node-{node.get_node_info()['id']:02d}-response",perf_counter()-context.start_time)
            self._logger.info("Received response: %s from node %s",response.decode(),node)
            return response,context
        finally:
            writer.close()
            await writer.wait_closed()
        
    async def replace_dead_nodes(self,dead_nodes:List[asyncNode]):
        for node in dead_nodes: 
            host,port = node.host, node.port
            await node.stop()
            self.add_node(host,port)

    async def health_check_routine(self):
        dead_nodes:List[asyncNode] = []
        while self._is_running:
            dead_nodes = await self._load_balancer.do_health_checks()
            if dead_nodes:
                await self.replace_dead_nodes(dead_nodes)
            health_reports = await self._load_balancer.get_health_reports()
            self._logger.info("Health Reports: %s",health_reports)
            await asyncio.sleep(60)
                    

    def get_status(self):
        #  [b for b in dir(a) if b.startswith("_") and not b.startswith("__")]
        res="--------- DistributedBookingSystem -----------\n"
        res+=f"|\t>Running on {self.host}:{self.port}.\n"
        res+=f"|\t>Managing {len(self._nodes)} Nodes and {len(self._nodes)}.\n"
        res+=f"|\t>Using Loadbalancer type {type(self._load_balancer)}.\n"
        res+=f"|\t>Status Server is runnning = {self._is_running}.\n"
        res+="--------- DistributedBookingSystem -----------\n"
        return res
    
