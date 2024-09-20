from logging import INFO, basicConfig, getLogger
from threading import Thread
from typing import Any, Dict

from app.controller.distibutedSystem import DistributedBookingSystem
from app.controller.httpServer import HTTPserver
#from app.controller.httpClient import HttpClient
from app.controller.parser import ParserFactory
from app.controller.taskQueue import TaskQueue
from app.model.booking import BookingAnalyzer, BookingManager
from app.model.cache import LruCache
from app.model.database import PostgresqlDB, cachedTravelCRUD, travelCRUD

test_booking = False
test_getRequest = False
test_crud = False
test_httpServer = False
test_cache = False
test_LoadBalancing = False
test_TaskQueue = True

basicConfig(level=INFO)
logger = getLogger(__name__)

postgres_db_params:Dict[str,Any]={
            'host': 'localhost',
            'port': 5432,
            'dbname': 'sqlalchemy1',
            'user': 'admin',
            'password': 'mypassword'
        }

def test_booking_func()->None:
    logger.info('Booking-Class test: Started.')
    parser_factory = ParserFactory()
    file_path = 'data/travel_bookings.csv'
    parser = parser_factory.getParser('csv')
    booking_manager = BookingManager()
    booking_manager.add_bookings(parser.parse_complete(file_path))
    bookings = booking_manager.get_all_bookings()
    booking_analyzer = BookingAnalyzer()
    dep_cities=booking_analyzer.bookings_per_departure_city(bookings)
    print(dep_cities)
    logger.info('Booking-Class test: Done.')

def test_getRequest_func()->None:
    logger.info('getRequest test: Started.')
    parser_factory = ParserFactory()
    parser = parser_factory.getParser('json')
    url_api = "api.open-meteo.com"
    # weather at mount fuji
    #weather_query = "/v1/forecast?latitude=35.21&longitude=138.43&current_weather=true"
    #client = HttpClient(url_api)
    #result = client.get(weather_query)
    result = '{"latitude":35.2,"longitude":138.4375,"generationtime_ms":0.06496906280517578,"utc_offset_seconds":0,"timezone":"GMT","timezone_abbreviation":"GMT","elevation":730.0,"current_weather_units":{"time":"iso8601","interval":"seconds","temperature":"°C","windspeed":"km/h","winddirection":"°","is_day":"","weathercode":"wmo code"},"current_weather":{"time":"2024-09-13T13:15","interval":900,"temperature":21.3,"windspeed":3.3,"winddirection":264,"is_day":0,"weathercode":0}}'
    parsed_result= parser.parse_one(result)
    print(parsed_result)
    logger.info('getRequest test: Done.')

def test_crud_func()->None:
    logger.info('Crud test: Started.')
    parser_factory = ParserFactory()
    db_params=postgres_db_params
    crud = travelCRUD(PostgresqlDB,db_params,'bookings')
    
    file_path = 'data/travel_bookings.csv'
    parser = parser_factory.getParser('csv')
    booking_manager = BookingManager()
    booking_manager.add_bookings(parser.parse_complete(file_path))
    booking_keys, booking_values = booking_manager.all_bookings_to_list()
    
    if crud.check_table_exists():
        crud.delete_database()
    # create basic schema
    crud.create_schema()
    
    # insert data
    crud.insert_data_from_list(booking_values)
    
    # update 1 row
    crud.update_payment_status('fb6b3247-7a34-48d3-8611-99dd0eb600b1','Paid')
    
    # delete 1 entry
    crud.delete_booking('625cd3c9-0116-452f-816c-91aa6e236110')
    logger.info('Crud test: Done.')

def test_httpServer_func()->None:
    logger.info('HttpServer test: Started.')
    db_params=postgres_db_params
    crud = travelCRUD(PostgresqlDB,db_params,'bookings')
    server = HTTPserver(crud)
    server.start()
    logger.info('HttpServer test: Ended.')
 
def test_cache_func()->None:
    logger.info('Cache test: Started.')
    db_params=postgres_db_params
    cachedCrud = cachedTravelCRUD(PostgresqlDB,db_params,'bookings',False,LruCache(20,30))
    server = HTTPserver(cachedCrud)
    server.start()
    logger.info('Cache test: Done.')

def test_LoadBalancing_func()->None:
    logger.info('LoadBalancing test: Started.')
    db = PostgresqlDB
    db_params = postgres_db_params
    table_name = 'bookings'
    #cache = LruCache(20,30)
    host="localhost"
    # make sure port range isn't used -> in bash `lsof -i -P -n | grep LISTEN``

    base_port=8181
    distributed_system = DistributedBookingSystem(host,base_port,db,db_params,table_name)
    
    for i in range(1,6):
        distributed_system.add_node(host,base_port+i)
    distributed_system.set_load_balancer("roundrobin")
    
    distributed_system.run()
    #running_system = Thread(target=distributed_system.run)
    #running_system.start()
    #print(running_system.is_alive())
    print(distributed_system.get_status())
    logger.info('LoadBalancing test: Done.')

def test_TaskQueue_func()->None:
    logger.info('TaskQueue test: Started.')
    db = PostgresqlDB
    db_params = postgres_db_params
    table_name = 'bookings'
    host="localhost"
    base_port=8181
    task_queue = TaskQueue(3,20)
    distributed_system = DistributedBookingSystem(host,base_port,db,db_params,table_name,task_queue)
    
    for i in range(1,6):
        distributed_system.add_node(host,base_port+i)
    distributed_system.set_load_balancer("roundrobin")
    
    distributed_system.run()
    
    print(distributed_system.get_status())
    logger.info('TaskQueue test: Done.')

if __name__ == '__main__':
    print("こんにちは！元気ですか?")
    # do something
    
    if test_booking:        test_booking_func()
    if test_getRequest:     test_getRequest_func()
    if test_crud:           test_crud_func()
    if test_httpServer:     test_httpServer_func()
    if test_cache:          test_cache_func()
    if test_LoadBalancing:  test_LoadBalancing_func()
    if test_TaskQueue:      pass

    print("'Elegance is the elimination of excess.' – Bruce Lee")
