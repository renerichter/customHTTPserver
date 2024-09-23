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
from asyncio import StreamReader, StreamWriter
from json import loads as json_loads
from logging import Logger
from random import randint
from time import perf_counter
from typing import Any, Dict, Optional

from ..model.database import BasicCRUD
from .httpServer import RequestHandlerFactory, ServerConfig
from .logger import RequestContext
from .taskQueue import TaskQueue


class AsyncHttpServer:
    def __init__(self, crud: BasicCRUD,task_queue:TaskQueue,host:Optional[str],port:Optional[int],parent_logger:Logger):
        self.config = ServerConfig(host,port)
        self.host = host
        self.port = port
        self.crud = crud
        self.task_queue = task_queue
        self.handler_factory = RequestHandlerFactory(self.crud,)
        self._running = False
        self._name = f"asyncHS-{randint(0,99999):05d}"
        self._logger = parent_logger.getChild(self._name)

    async def start(self):
        self._server = await asyncio.start_server(self.handle_request,self.host,self.port)
        async with self._server:
            await self._server.serve_forever()
    
    async def stop(self):
        if self._server:
            self._logger.info("Stopping server...")
            self._server.close()
            await self._server.wait_closed()
    
    async def handle_request(self,reader:StreamReader,writer:StreamWriter):
        start_time=perf_counter()
        data = await reader.read(1024)
        message = data.decode()
        addr = writer.get_extra_info('peername')
        self._logger.info("Received %r from %r",message,addr)
        
        response = await self.process_request(message)
        await self.task_queue.add_task(self.send_confirmation,response,addr)
        self._logger.info("Sending back response: %r",response)
        writer.write(response.encode())
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
                self._logger.info("Passed on Line: %s",line)
        if single_carrier_return_idx < len(request_lines) -1:
            body = '\n'.join(request_lines[single_carrier_return_idx+1:])
        context = RequestContext()
        context.request_method = method
        context.request_path = path
        
        try:
            handler = self.handler_factory.create_handler(method)
            request_data:Dict[str,Any]= {'path':path,'headers':headers,'body':body}
            if method == 'POST':
                request_data['booking'] = json_loads(body)
                await self.task_queue.add_task(self.send_confirmation,request_data['booking'])
            result = handler.handle_request(request_data)
            self._logger.debug("Request processed",extra={'trace_context': context.to_dict()})
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
        self._logger.info("Sent confirmation msg for database-change to %s.",address)
        return 0
