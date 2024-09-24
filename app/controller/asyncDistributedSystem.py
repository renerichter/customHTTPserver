import asyncio
import datetime
import json
import time
from abc import ABC, abstractmethod
from asyncio import StreamReader, StreamWriter
from logging import Logger, getLogger
from time import perf_counter, time
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import paho.mqtt.client as mqtt
import psutil

from ..model.database import DatabaseConnection, cachedTravelCRUD
from .asyncHttpServer import AsyncHttpServer
from .logger import LoggerSetup, RequestContext
from .monitoring import DashboardDisplay, PerformanceParams
from .names import CreativeNamer
from .taskQueue import TaskQueue


class asyncNode:
    def __init__(self,crud:cachedTravelCRUD,host:str,port:int,node_name:str,node_id:int,parent_logger:Logger,nbr_qworkers:int=3,qsize:int=5,broker_addr:str='localhost'):
        self.host = host
        self.port = port
        self._crud = crud
        self._httpServer = None
        self._thread = None
        self._special_name = node_name
        self._id = node_id
        self._name = f"aNode-{self._id[:8]}"
        self._logger = parent_logger.getChild(self._name)
        self.task_queue = TaskQueue(self._logger,f"LocalTQ-{self._name}",nworkers=nbr_qworkers,qsize=qsize)
        self.broker_address = broker_addr
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect(self.broker_address,keepalive=120)
        self.is_running=False
    
    async def start(self):
        await self.task_queue.start()
        self._httpServer=AsyncHttpServer(self._crud,self.task_queue,self.host,self.port,self._logger)
        self._thread = asyncio.create_task(self._httpServer.start())
        self._logger.info(self)
        self.health_task=asyncio.create_task(self.publish_health())
        return self.get_info()
    
    async def stop(self):
        if self._httpServer:
            await self._httpServer.stop()
        if self._thread:
            await self._thread
        await self.task_queue.stop()
        
        self.is_running=False
        if self.health_task:
            self.health_task.cancel()
        self._logger.info("%s\n------->>-------Bye 😜------->>-------\n",self)

    
    async def health_check(self) -> bool:
        try:
            cpu_usage = psutil.cpu_percent(interval=1) 
            mem_available = psutil.virtual_memory().available /1024/1024
            return cpu_usage < 90 and mem_available > 100
        except Exception as e: 
            self._logger.error("Health check failed for node %s on port %d: %s",self._name,self.port,str(e),exc_info=True)
            return False
        
    async def health_report(self)->Dict[str,Any]:
        start_time=perf_counter()
        cpu_usage = psutil.cpu_percent(interval=1) 
        mem_usage = psutil.virtual_memory().percent
        mem_available = psutil.virtual_memory().available / (1024 * 1024)
        disk_usage = psutil.disk_usage('/').percent        
        
        await asyncio.sleep(0.1)
        # health check latency
        latency = (perf_counter() -start_time)*1000 #ms
        
        return {
            "name": self._name,
            "id": self._id,
            "cpu_usage": cpu_usage,
            "ram_usage": mem_usage,
            "ram_available": mem_available,
            "disk_usage": disk_usage,
            "latency_ms": latency
        }
    
    def get_info(self)->Dict[str,Any]:
        return {'name': self._name, 
                'id':   self._id,
                'host': self.host,
                'port': self.port,
                'crud': self._crud.get_info(),
                'http': self._httpServer.get_info(),
                'thread': str(self._thread),
                'logger': str(self._logger)
                }
    async def publish_health(self):
        while True:
            if not self.mqtt_client.is_connected():
                self.mqtt_client.connect(self.broker_address,keepalive=120)
            self.mqtt_client.publish(f"health/{self._id}",json.dumps(await self.health_report()))
            await asyncio.sleep(10)

    
    def __str__(self):
        return f"Node ~*>{self._special_name}<*~ (ID={self._id}) running on {self.host}:{self.port}"

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
    def __init__(self,nodes:List[asyncNode],parent_logger:Logger,broker_addr:str='localhost'):
        self._nodes = nodes
        self._current_idx = 0
        self._id=str(uuid4())
        self._name = f"LB-RR-{self._id[:8]}"
        self._logger = parent_logger.getChild(self._name)
        self._performance = PerformanceParams(self._name,str(self._id),40)
        self.is_running = False
        self.broker_address = broker_addr
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect(self.broker_address,keepalive=120)
    
    def start(self):
        self.health_task = asyncio.create_task(self.publish_health())
        self.is_running=True
    
    def stop(self):
        self.is_running=False
        if self.health_task:
            self.health_task.cancel()
    
    def get_next_node(self,context: RequestContext) -> asyncNode:
        start_time = perf_counter()
        self._performance.add_request_time(time())
        if len(self._nodes) == 0:
            self._logger.error("No Nodes for routing left.")
            raise ValueError("No Nodes for routing left")
        node = self._nodes[self._current_idx]
        response_time = perf_counter()-start_time
        self._current_idx = (self._current_idx + 1)%len(self._nodes)
        context.add_response_time(self._name,response_time)
        self._performance.add_response_time(response_time)
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
            reports[node.get_info()['name']] = await node.health_report()
        return reports

    def get_info(self)->Dict[str,Any]:
        return {'name':self._name,
                'id': self._id,
                'current_idx': self._current_idx,
                'performance_params': self._performance,
                'nodes': [str(node) for node in self._nodes],
                'logger': str(self._logger)}

    async def publish_health(self):
        while True:
            if not self.mqtt_client.is_connected():
                self.mqtt_client.connect(self.broker_address,keepalive=120)
            self.mqtt_client.publish(f"health/{self._id}",json.dumps(self._performance.get_perf_report()))
            await asyncio.sleep(10)

class asyncDistributedBookingSystem:
    def __init__(self,host:str,port:int,db:DatabaseConnection, db_params: Dict[str,Any], table_name:str,global_q_params:Tuple[int,int],q_params:Tuple[int,int],logger_setup:LoggerSetup,logger_level:str,broker_addr:Tuple[str,int]):
        self.host = host
        self.port = port
        self._nodes:List[asyncNode]=[]
        self._load_balancer: asyncLoadBalancer = None
        self._db = db
        self._db_params = db_params
        self._table_name = table_name
        self._namer = CreativeNamer()
        self._name = 'aDBS'
        self._id = str(uuid4())
        self._server = None
        self._is_running = False
        self._qparams = q_params
        self._logger_setup = logger_setup
        self._logger_level = logger_level
        
        # start logger
        self._logger_setup.setup_logging()
        self._logger:Logger=getLogger(self._name)
        
        # task queue
        self._global_task_queue = TaskQueue(self._logger,name="GlobalTaskQueue",nworkers=global_q_params[0],qsize=global_q_params[1])
        
        
        # mqtt
        self.mqtt_broker_host = broker_addr[0]
        self.mqtt_broker_port = broker_addr[1]
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.connect(self.mqtt_broker_host,self.mqtt_broker_port)
        
        # services and health_data
        self.services:Dict[str,Any] = {}
        self.health_data:Dict[str,Any] = {}
        
        # Dashboard
        self.performance = PerformanceParams(self._name,self._id,30)
        self.dashboard = DashboardDisplay(self.create_health_report,self._name)
    
    def add_node(self,host:str,port:int):
        crud = cachedTravelCRUD(self._db,self._db_params,self._table_name,parent_logger=self._logger)
        crud.start()
        node_id = self._id=str(uuid4())
        node = asyncNode(crud,host,port,self._namer.create_name(1),node_id,parent_logger=self._logger)
        self._nodes.append(node)
        
        if self._load_balancer:
            self._load_balancer.update_nodes_list(self._nodes)
        
    async def delete_node(self,node_idx:int):    
        if ~ await self.stop_node(node_idx):
            del self._nodes[node_idx]
            
    async def stop_node(self,node_idx:int):
        if node_idx >= len(self._nodes):
            self._logger.error(f"Node ID=%d not found",node_idx)
            return 1
        else:
            self._logger.info(">>> Stopping node %s...",self._nodes[node_idx])
            await self._nodes[node_idx].stop()
            return 0

    def set_load_balancer(self,balancer_type:str):
        match balancer_type:
            case "roundrobin":
                self._load_balancer = asyncRoundRobinBalancer(self._nodes,self._logger)
            case _:
                self._load_balancer = asyncRoundRobinBalancer(self._nodes,self._logger)
                self._logger.info("No logger given or given logger name: %s unknown. Chose default balancer roundrobin.",balancer_type)
        info=self._load_balancer.get_info()
        self.services[info['id']]=info['name']
        self._load_balancer.start()
        
    async def start(self):        
        self._logger.info("DBS --> Starting up...")
        await self._global_task_queue.start()
        
        # start nodes
        for node in self._nodes:
            start_res = await node.start()
            self.services[start_res['id']]=start_res['name']
            if start_res.get('crud',None):
                info=self._load_balancer.get_info()
                self.services[start_res['crud']['id']]=start_res['crud']['name']
                self.services[start_res['crud']['cache']['id']] =start_res['crud']['cache']['name']
            if start_res.get('http',None):
                self.services[start_res['http']['id']]=start_res['http']['name']

        self._server = await asyncio.start_server(self.handle_connection,self.host,self.port)
        self._is_running = True
        self._logger.info("DBS ---> Listening on %s:%d.",self.host,self.port)
        asyncio.create_task(self.health_check_routine())

        # subscribe to services
        for service_id in self.services.keys():
            self.mqtt_client.subscribe(f"health/{service_id}")
        
        # call new thread to stay in touch with broker
        self.mqtt_client.loop_start()
        
        # start dashboard
        self.dashboard.start()
        
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
            context.add_response_time(f"{node.get_info()['name']}-response",perf_counter()-context.start_time)
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
    

    def _on_message(self,client,userdata,message):
        service_id= message.topic.split("/")[1]
        self.health_data[service_id] = json.loads(message.payload.decode())
        self._logger.debug("Received health status from %s (ID=%s)",self.health_data[service_id]['name'],service_id)
        
    def calculate_average(self,in_list:list[float])->float:
        if len(in_list)>0:
            avg=self.performance.calculate_average(in_list)
        else:
            avg=-1.0
        return avg
    
    def create_health_report(self) -> Dict[str,Any]:
        # get data for DBS
        self.health_data[self._id] = self.performance.get_perf_report()
        
        avg_rps= []#meas at load_balancer
        avg_rest=[]#meas at aDBS
        cache_hit=[]# meas at cache
        cache_miss=[]# meas at cache
        cache_hm_ratio=[]# meas at cache
        http_uptime:List[float]=[]# at http
        node_cpu_usage = []
        node_ram_usage = []
        node_disk_usage = []
        node_latency = []
        used_services={}
        for s_id,s_val in self.health_data.items():
            used_services[s_id] = s_val['name']
            s_val_name=s_val.get('name','').lower()
            if 'http' in s_val_name:
                http_uptime.append(s_val['uptime_raw'])
            if 'cache' in s_val_name:
                cache_hit.append(s_val['cache_hits'])
                cache_miss.append(s_val['cache_misses'])
                cache_hm_ratio.append(s_val['cache_hit_miss_ratio'])
            if 'lb-' in s_val_name:
                avg_rps.append(s_val['avg_requests_per_second'])
            if 'dbs' in s_val_name:
                avg_rest.append(s_val['avg_response_time'])
            if 'anode' in s_val_name:
                node_cpu_usage.append(s_val['cpu_usage'])
                node_ram_usage.append(s_val['ram_usage'])
                node_disk_usage.append(s_val['disk_usage'])
                node_latency.append(s_val['latency_ms'])
                
                
        
        results:Dict[str,Any]={'rps':avg_rps,'resp':avg_rest,'hit':cache_hit,'miss':cache_miss,'hmratio':cache_hm_ratio,'uptime':http_uptime,'node_cpu':node_cpu_usage,'node_ram': node_ram_usage,'node_disk':node_disk_usage,'node_latency':node_latency}
        results = {key:self.performance.calculate_average(value) if len(value)>0  else -1.0 for key,value in results.items()}
        results['uptime']=str(results['uptime']) if results['uptime']==-1.0 else self.performance.fmt_uptime(results['uptime'])
        used_services_pp = ",".join([val for val in used_services.values()])
                
        return {'avg_requests_per_second': results['rps'],
                'avg_response_time': results['resp'],
                'cache_hits': results['hit'],
                'cache_misses': results['miss'],
                'cache_hit_miss_ratio': results['hmratio'],
                'uptime': results['uptime'],
                'node_ram': results['node_ram'],
                'node_disk': results['node_disk'],
                'node_cpu': results['node_cpu'],
                'node_latency': results['node_latency'],
                'last_updated': datetime.datetime.now().astimezone().isoformat(),
                'used_services':used_services_pp,
            }