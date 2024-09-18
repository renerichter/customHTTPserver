from typing import Any, Dict

from app.controller.httpServer import HTTPserver
#from app.controller.httpClient import HttpClient
from app.controller.parser import ParserFactory
from app.model.booking import BookingAnalyzer, BookingManager
from app.model.cache import LruCache
from app.model.database import PostgresqlDB, cachedTravelCRUD, travelCRUD

test_booking = False
test_getRequest = False
test_crud = False
test_unitTest = False
test_httpServer = False
test_Cache = True


if __name__ == '__main__':
    print("こんにちは！元気ですか?")
    # do something
    parser_factory = ParserFactory()
    if test_booking:
        file_path = 'data/travel_bookings.csv'
        parser = parser_factory.getParser('csv')
        booking_manager = BookingManager()
        booking_manager.add_bookings(parser.parse_complete(file_path))
        bookings = booking_manager.get_all_bookings()
        booking_analyzer = BookingAnalyzer()
        dep_cities=booking_analyzer.bookings_per_departure_city(bookings)
        print(dep_cities)
    if test_getRequest:
        parser = parser_factory.getParser('json')
        url_api = "api.open-meteo.com"
        # weather at mount fuji
        #weather_query = "/v1/forecast?latitude=35.21&longitude=138.43&current_weather=true"
        #client = HttpClient(url_api)
        #result = client.get(weather_query)
        result = '{"latitude":35.2,"longitude":138.4375,"generationtime_ms":0.06496906280517578,"utc_offset_seconds":0,"timezone":"GMT","timezone_abbreviation":"GMT","elevation":730.0,"current_weather_units":{"time":"iso8601","interval":"seconds","temperature":"°C","windspeed":"km/h","winddirection":"°","is_day":"","weathercode":"wmo code"},"current_weather":{"time":"2024-09-13T13:15","interval":900,"temperature":21.3,"windspeed":3.3,"winddirection":264,"is_day":0,"weathercode":0}}'
        parsed_result= parser.parse_one(result)
        print(parsed_result)
    if test_crud:
        db_params:Dict[str,Any]={
            'host': 'localhost',
            'port': 5432,
            'dbname': 'sqlalchemy1',
            'user': 'admin',
            'password': 'mypassword'
        }
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
        
    if test_httpServer:
        db_params:Dict[str,Any]={
            'host': 'localhost',
            'port': 5432,
            'dbname': 'sqlalchemy1',
            'user': 'admin',
            'password': 'mypassword'
        }
        crud = travelCRUD(PostgresqlDB,db_params,'bookings')
        server = HTTPserver(crud)
        server.start()

    if test_Cache:
        db_params:Dict[str,Any]={
            'host': 'localhost',
            'port': 5432,
            'dbname': 'sqlalchemy1',
            'user': 'admin',
            'password': 'mypassword'
        }
        cachedCrud = cachedTravelCRUD(PostgresqlDB,db_params,'bookings',False,LruCache(20,30))
        server = HTTPserver(cachedCrud)
        server.start()
    print("'Elegance is the elimination of excess.' – Bruce Lee")
