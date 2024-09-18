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
from abc import ABC, abstractmethod
from json import dumps, loads
from typing import Any, Dict, Union

from ..model.database import BasicCRUD, travelCRUD


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
    _instance = None
    
    def __new__(cls): # host:str=,port:int=
        if cls._instance is None:
            cls._instance = super(ServerConfig,cls).__new__(cls)
            cls._instance.host = 'localhost'
            cls._instance.port = 8181
        return cls._instance

class HTTPserver:
    def __init__(self, crud: BasicCRUD):
        self.config = ServerConfig()
        self.crud = crud
        self.handler_factory = RequestHandlerFactory(self.crud,)
    
    def start(self):
        from socket import AF_INET, SOCK_STREAM, socket
        with socket(AF_INET,SOCK_STREAM) as active_socket:
            active_socket.bind((self.config.host,self.config.port))
            active_socket.listen()
            print(f"Server listening on {self.config.host}:{self.config.port}.")
            while True:
                conn,addr = active_socket.accept()
                with conn:
                    print(f"Connected by {addr}.")
                    data = conn.recv(1024) #standard buffer size for messaging and simple file-transfer -> for big-files change to 8192bytes or more
                    if not data: 
                        break
                    response = self.handle_request(data.decode('utf-8'))
                    conn.sendall(response.encode('utf-8'))
    
    def handle_request(self,request:str) -> str:
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
                print(f"Passed on {line=}.")
        if single_carrier_return_idx < len(request_lines) -1:
            body = '\n'.join(request_lines[single_carrier_return_idx+1:])
        
        try:
            handler = self.handler_factory.create_handler(method)
            request_data= {'path':path,'headers':headers,'body':body}
            if method == 'POST':
                request_data['booking'] = loads(body)
            result = handler.handle_request(request_data)
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