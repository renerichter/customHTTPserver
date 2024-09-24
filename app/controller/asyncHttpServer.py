""" ToDo list
- requests (Get, Post, ...)
    - needs running server ... at best async
- Server
    - init -> set config
    - start
    - end
- Connection to database
    - use existing connector
"""
import asyncio
import json
from abc import ABC, abstractmethod
from asyncio import StreamReader, StreamWriter
from logging import Logger
from time import perf_counter, time
from typing import Any, Dict, Optional, Union
from uuid import uuid4

import paho.mqtt.client as mqtt

from ..model.database import BasicCRUD
from .logger import RequestContext
from .monitoring import PerformanceParams
from .taskQueue import TaskQueue


class RequestHandler(ABC):
    @abstractmethod
    def handle_request(self,request: Dict[str,Any])->str:
        pass

class GetRequestHandler(RequestHandler):
    def __init__(self,crud: BasicCRUD):
        self.crud = crud
    
    def handle_request(self, request: Dict[str, Any]) -> str:
        booking_id = request.get('path').split('/')[-1]
        if booking_id:
            if "-" in booking_id:
                booking = self.crud.get_booking_id(booking_id)
                if booking:
                    return booking
                else:
                    return f"booking_id {booking_id} not found."
            else:
                all_booking_ids = self.crud.get_booking_id()
                return dumps(all_booking_ids)
        else:
            return "No route matched."
        
class PostRequestHandler(RequestHandler):
    def __init__(self, crud: BasicCRUD) -> None:
        self.crud = crud
    
    def handle_request(self, request: Dict[str, Any]) -> str:
        booking_data = request.get('booking')
        if booking_data:
            if not isinstance(booking_data,Union[tuple,list]): booking_data = [booking_data,]
            booking_list = [list(item.values()) for item in booking_data]
            self.crud.insert_data_from_list(booking_list)
            return "Booking created successfully"
        else:
            return "Invalid Booking data."

class RequestHandlerFactory:
    def __init__(self, crud: BasicCRUD):
        self.crud = crud
    
    def create_handler(self, method:str) -> RequestHandler:
        match method:
            case 'GET':
                return GetRequestHandler(self.crud)
            case 'POST':
                return PostRequestHandler(self.crud)
            case _:
                raise ValueError(f"Unsupported HTTP-method: {method}.")

class ServerConfig:
    _instance = {}
    
    def __new__(cls,host:Optional[str]=None,port:Optional[int]=None)->object: # host:str=,port:int=
        host = host if host else 'localhost'
        port = port if port else 8181
        key = (host,port)
        if key not in cls._instance:
            cls._instance[key] = super(ServerConfig,cls).__new__(cls)
            cls._instance[key].host = host
            cls._instance[key].port = port
        return cls._instance[key]

class AsyncHttpServer:
    def __init__(self, crud: BasicCRUD,task_queue:TaskQueue,host:Optional[str],port:Optional[int],parent_logger:Logger,broker_addr:str='localhost'):
        self.config = ServerConfig(host,port)
        self.host = host
        self.port = port
        self.crud = crud
        self.task_queue = task_queue
        self.handler_factory = RequestHandlerFactory(self.crud,)
        self._running = False
        self._id=str(uuid4())
        self._name = f"aHttpServer-{self._id[:8]}"
        self.logger = parent_logger.getChild(self._name)
        self._performance = PerformanceParams(self._name,self._name,40)
        self.broker_address = broker_addr
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect(self.broker_address,keepalive=120)
        
    async def start(self):
        self._server = await asyncio.start_server(self.handle_request,self.host,self.port)
        self.health_task=asyncio.create_task(self.publish_health())
        self.crud.start()
        self.is_running=True
        async with self._server:
            await self._server.serve_forever()
    
    async def stop(self):
        self.is_running=False
        if self.health_task:
            self.health_task.cancel()
        if self._server:
            self.logger.info("Stopping server...")
            self._server.close()
            await self._server.wait_closed()
    
    async def handle_request(self,reader:StreamReader,writer:StreamWriter):
        start_time=perf_counter()
        self._performance.add_request_time(time())
        data = await reader.read(1024)
        message = data.decode()
        addr = writer.get_extra_info('peername')
        self.logger.info("Received %r from %r",message,addr)
        
        response = await self.process_request(message)
        await self.task_queue.add_task(self.send_confirmation,response,addr)
        self.logger.info("Sending back response: %r",response)
        writer.write(response.encode())
        response_time = perf_counter()-start_time
        self._performance.add_response_time(response_time)
        await writer.drain()
        await writer.wait_closed()
        
    async def process_request(self,request: str)->str:
        request_lines = request.split('\n')
        method, path, _ = request_lines[0].split()        
        headers = {}
        body = ''
        single_carrier_return_idx = request_lines.index('\r') if '\r' in request_lines else -1
        #print(request_lines)
        for line in request_lines[1:single_carrier_return_idx]:
            try:
                key,value = line.split(':',1)
                headers[key.lower()] = value.strip()
            except:
                self.logger.info("Passed on Line: %s",line)
        if single_carrier_return_idx < len(request_lines) -1:
            body = '\n'.join(request_lines[single_carrier_return_idx+1:])
        context = RequestContext()
        context.request_method = method
        context.request_path = path
        
        try:
            handler = self.handler_factory.create_handler(method)
            request_data:Dict[str,Any]= {'path':path,'headers':headers,'body':body}
            if method == 'POST':
                request_data['booking'] = json.loads(body)
                await self.task_queue.add_task(self.send_confirmation,request_data['booking'])
            result = handler.handle_request(request_data)
            self.logger.debug("Request processed",extra={'trace_context': context.to_dict()})
            return self.create_response(200,result)
        except Exception as e:
            return self.create_response(500,str(e))
    
    def create_response(self, status_code: int, body: str) -> str:
        status_messages = {200: 'OK', 500: 'Internal Server Error'}
        headers = [
            f"HTTP/1.1 {status_code} {status_messages.get(status_code)}",
            "Content-Type: application/json",
            f"Content-Length: {len(body)}",
            "Connection: close"
        ]
        return '\r\n'.join(headers) + '\r\n\r\n' + body

    async def send_confirmation(self,booking_id:str,address:str)->int:
        await asyncio.sleep(1)  # Simulate some processing time
        self.logger.info("Sent confirmation msg for database-change to %s.",address)
        return 0
        return 0

    def get_info(self)->Dict[str,Any]:
        return {'name':self._name,
                'id':self._id,
                'host':self.host,
                'port': self.port,
                'crud': self.crud.get_info(),
                'task_queue': self.task_queue.get_info(),
                'is_running': self._running,
                'logger': str(self.logger),}

    async def publish_health(self):
        while True:
            if not self.mqtt_client.is_connected():
                self.mqtt_client.connect(self.broker_address,keepalive=120)
            self.mqtt_client.publish(f"health/{self._id}",json.dumps(self._performance.get_perf_report()))
            await asyncio.sleep(10)