import asyncio
from abc import ABC, abstractmethod
from asyncio import StreamReader, StreamWriter
from logging import INFO, basicConfig, getLogger
from threading import Thread
from typing import Any, Dict, List

from ..model.database import DatabaseConnection, cachedTravelCRUD
from .httpServer import HTTPserver
from .names import CreativeNamer
from .taskQueue import TaskQueue

basicConfig(level=INFO)
logger = getLogger(__name__)

class Node:
    def __init__(self,crud:cachedTravelCRUD,host:str,port:int,node_name:str,node_id:int):
        self._host = host
        self._port = port
        self._crud = crud
        self._httpServer = None
        self._thread = None
        self._name = node_name
        self._id = node_id
    
    def start(self):
        self._httpServer=HTTPserver(self._crud,self._host,self._port)
        self._thread = Thread(target=self._httpServer.start)
        print(self)
        self._thread.start()
    
    def stop(self):
        if self._httpServer:
            print("Node {self._name} here again -> ",end="");
            self._httpServer.stop()
        if self._thread:
            self._thread.join()
        print("\n----------------Bye 😜----------------\n")
        
    def __str__(self):
        res = f"Hiho, node ~*>{self._name}<*~ here. 👋"
        res += "\n------------------------------------\n"
        res += f"> Running on {self._host}:{self._port}.\n"
        res += f"> Using crud={self._crud} and server-type={self._httpServer}.\n"
        res += f"> **Thread-Status**={self._thread}\n"
        res += "\n------------------------------------\n"
        return res
    
    def get_short_info(self):
        print(f"Node {self._name} with ID={self._id}.")

class NodeConnection:
    def __init__(self,host:str,port:int):
        self._host = host
        self._port = port
        self._reader:StreamReader = None
        self._writer:StreamWriter = None
        
    async def connect(self):
        self._reader,self._writer = await asyncio.open_connection(self._host,self._port)
    
    async def close(self):
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()

    def is_open(self):
        # Check if the writer exists and is not closing
        return self._writer is not None and not self._writer.is_closing()

class LoadBalancer(ABC):
    @abstractmethod
    def get_next_node(self) -> NodeConnection:
        pass

    @abstractmethod
    def update_nodes_list(self,new_connections:List[NodeConnection]):
        pass

class RoundRobinBalancer(LoadBalancer):
    def __init__(self,node_connections:List[NodeConnection]):
        self._connections = node_connections
        self._current_idx = 0
    
    def get_next_node(self) -> NodeConnection:
        if len(self._connections) == 0:
            logger.error("No Nodes for routing left.")
            raise ValueError("No Nodes for routing left")
        connection = self._connections[self._current_idx]
        self._current_idx = (self._current_idx + 1)%len(self._connections)
        return connection

    def update_nodes_list(self,new_connections:List[NodeConnection]):
        self._connections = new_connections
        self._current_idx = self._current_idx % len(new_connections)

class RandomBalancer(LoadBalancer):
    pass

class WeightedRoundRobin(LoadBalancer):
    pass

class DistributedBookingSystem:
    def __init__(self,host:str,port:int,db:DatabaseConnection, db_params: Dict[str,Any], table_name:str, task_queue:TaskQueue):
        self._host = host
        self._port = port
        self._nodes:List[Node]=[]
        self._nodes_connection:List[NodeConnection]=[]
        self._load_balancer: LoadBalancer = None
        self._db = db
        self._db_params = db_params
        self._table_name = table_name
        self._namer = CreativeNamer()
        self._server = None
        self._is_running = False
    
    def add_node(self,host:str,port:int):
        crud = cachedTravelCRUD(self._db,self._db_params,self._table_name)
        node_id = len(self._nodes)
        node = Node(crud,host,port,self._namer.create_name(1),node_id)
        node_connection = NodeConnection(host,port)
        self._nodes.append(node)
        self._nodes_connection.append(node_connection)
        if self._load_balancer:
            self._load_balancer.update_nodes_list(self._nodes_connection)
        
    async def delete_node(self,node_id:int):    
        if ~ await self.stop_node(node_id):
            del self._nodes[node_id]
            del self._nodes_connection[node_id]
            
    async def stop_node(self,node_id:int):
        if node_id >= len(self._nodes):
            print(f"---- ERROR ----\nNode ID={node_id} not found.")
            return 1
        else:
            print(f">>> Stopping node {self._nodes[node_id].get_short_info()}...")
            self._nodes[node_id].stop()
            await self._nodes_connection[node_id].close()
            return 0
    
    async def start(self):        
        for node in self._nodes:  
            node.start()
        
        logger.info("DBS --> Starting up...")
        await asyncio.gather(*[nc.connect() for nc in self._nodes_connection])
        
        await self._task_queue.start()
        self._server = await asyncio.start_server(self.handle_connection,self._host,self._port)
        self._is_running = True
        logger.info(f"DBS ---> {["","Is running and "][self._is_running]}Listening on {self._host}:{self._port}.")
        
        async with self._server:
            await self._server.serve_forever()    
    
    def set_load_balancer(self,balancer_type:str):
        match balancer_type:
            case "roundrobin":
                self._load_balancer = RoundRobinBalancer(self._nodes_connection)
            case _:
                self._load_balancer = RoundRobinBalancer(self._nodes_connection)
                logger.info("No logger given or given logger name: %s unknown. Chose default balancer roundrobin.",balancer_type)
    
    def run(self):
        asyncio.run(self.start())
    
    async def stop(self):
        print(f"DistributedBookingSystem ---> Stopping all Nodes...")
        self._is_running = False
        await self._task_queue.stop()
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        await asyncio.gather(*[node.close() for node in self.nodes])
        
        for node in self._nodes:
            node.stop()

    async def handle_connection(self,reader: StreamReader, writer:StreamWriter):
        node_connection=self._load_balancer.get_next_node()
        logger.info("-------------- Active node=%d.----------",node_connection._port)
        if not node_connection.is_open():
            await node_connection.connect()
        await self._task_queue.add_task_and_dependency(self.handle_client,self.send_confirmation,reader,writer,node_connection)
    
    async def handle_client(self,reader:StreamReader,writer:StreamWriter,node_connection:NodeConnection):
        try:            
            client_task = asyncio.create_task(self.forward_data(reader,node_connection._writer,'R0'))
            node_task = asyncio.create_task(self.forward_data(node_connection._reader,writer,'W0'))
            
            _, pending = await asyncio.wait([client_task,node_task],return_when=asyncio.FIRST_COMPLETED)
            
            for task in pending:
                task.cancel()
            
            # try:
            #     await asyncio.wait_for(asyncio.gather(client_task, node_task), timeout=0.2)
            # except asyncio.TimeoutError:
            #     print("Tasks took too long, closing connections")
        except Exception as e: 
            logger.error("Error handling client request: %s",str(e),exc_info=True)
            raise
        finally: 
            writer.close()
            await writer.wait_closed()
            await node_connection.close()
    
    async def forward_data(self,reader:StreamReader,writer:StreamWriter):
        try:
            while True:
                data = await reader.read(1024)
                if not data: 
                    break
                writer.write(data)
                await writer.drain()
        except Exception as e:
            logger.error("Error forwarding data: %s",str(e),exc_info=True)

    async def schedule_information_sending(self,booking_id:str):
        await self._task_queue.add_task(self.send_confirmation,booking_id)
    
    async def send_confirmation(self,booking_id:str):
        """TODO: need logic here!"""
        
        

    def get_status(self):
        #  [b for b in dir(a) if b.startswith("_") and not b.startswith("__")]
        res="--------- DistributedBookingSystem -----------\n"
        res+=f"|\t>Running on {self._host}:{self._port}.\n"
        res+=f"|\t>Managing {len(self._nodes)} Nodes and {len(self._nodes_connection)}.\n"
        res+=f"|\t>Using Loadbalancer type {type(self._load_balancer)}.\n"
        res+=f"|\t>Status Server is runnning = {self._is_running}.\n"
        res+="--------- DistributedBookingSystem -----------\n"
        return res