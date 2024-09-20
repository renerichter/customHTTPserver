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
from logging import INFO, basicConfig, getLogger
from socket import AF_INET, SOCK_STREAM, socket
from typing import Any, Dict, Optional, Union

from ..model.database import BasicCRUD, travelCRUD
from .httpServer import RequestHandlerFactory, ServerConfig
from .taskQueue import TaskQueue

basicConfig(level=INFO)
logger = getLogger(__name__)

class AsyncHttpServer:
    def __init__(self, crud: BasicCRUD,task_queue:TaskQueue,host:Optional[str]=None,port:Optional[int]=None):
        self.config = ServerConfig(host,port)
        self.crud = crud
        self.task_queue = task_queue
        self.handler_factory = RequestHandlerFactory(self.crud,)
        self._running = False

    async def start(self):
        self._server = await asyncio.start_server(self.handle_request,self.config._instance.host,self.config._instance.port)
        async with self._server:
            await self._server.serve_forever()
    
    async def stop(self):
        if self._server:
            logger.info("Stopping server...")
            self._server.close()
            await self._server.wait_closed()
    
    async def handle_request(self,reader:StreamReader,writer:StreamWriter) -> str:
        data = await reader.read(1024)
        message = data.decode()
        addr = writer.get_extra_info('peername')
        logger.info("Received %r from %r",message,addr)
        
        response = await self.process_request(message)
        logger.info("Sending back response: %r",response)
        writer.write(response.encode())
        writer.drain()
        await writer.wait_closed()
        
    async def process_request(self,request: str)->str:
        request_lines = request.split('\n')
        method, path, _ = request_lines[0].split()
        headers = {}
        body = ''
        single_carrier_return_idx = request_lines.index('\r') if '\r' in request_lines else -1
        print(request_lines)
        for line in request_lines[1:single_carrier_return_idx]:
            try:
                key,value = line.split(':',1)
                headers[key.lower()] = value.strip()
            except:
                logger.info("Passed on Line: %s",line)
        if single_carrier_return_idx < len(request_lines) -1:
            body = '\n'.join(request_lines[single_carrier_return_idx+1:])
        
        try:
            handler = self.handler_factory.create_handler(method)
            request_data= {'path':path,'headers':headers,'body':body}
            if method == 'POST':
                request_data['booking'] = loads(body)
                await self.task_queue.add_task(self.send_confirmation,request_data['booking'])
            result = handler.handle_request(request_data)
            
            await self.task_queue.add_task(self.send_confirmation,content,address)
            
            return self.create_response(200,result)
        except Exception as e:
            return self.create_response(500,str(e))
    
    def create_response(self, status_code: int, body: str) -> str:
        status_messages = {200: 'OK', 500: 'Internal Server Error'}
        headers = [
            f"HTTP/1.1 {status_code} {status_messages.get(status_code)}",
            "Content Type: application/json",
            f"Content-Length: {len(body)}",
            "Connection: close"
        ]
        return '\r\n'.join(headers) + '\r\n\r\n' + body

    async def send_confirmation(self,booking_id:str,address:str):
        await asyncio.sleep(1)  # Simulate some processing time
        logger.info("Sent confirmation msg for database-change on %s to %s.",booking_id,address)
