from abc import abstractmethod
from functools import wraps
from traceback import TracebackException
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from psycopg2 import connect, extensions

from .booking import BookingManager
from .cache import Cache, LruCache


class DatabaseConnection:
    def __init__(self,host:str,port:int,dbname:str,user:str,password:str)->None:
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.conn = None

    @abstractmethod
    def __enter__(self) -> Callable[...,Any]:
        pass

    @abstractmethod
    def __exit__(self,exc_type:Optional[Type[BaseException]],exc_val:Optional[BaseException],exc_tb:Optional[TracebackException]) -> None:
        pass
 
class PostgresqlDB(DatabaseConnection):

    def __enter__(self) -> Callable[...,extensions.connection]:
        self.conn = connect(host=self.host,
                            port=self.port, 
                            dbname = self.dbname,
                            user=self.user,
                            password=self.password)
        print('Connection established')
        return self.conn

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackException | None) -> None:
        if exc_type: 
            self.conn.rollback()
            print(f'Exception {exc_type} happened. Rollback done. Nothing commited.')
        else: 
            self.conn.commit()
            print('Commit successfully done.')
        self.conn.close()
        print('Connection closed.')

class BasicCRUD:
    
    @staticmethod
    def db_operation(autocommit:Optional[Any]=None) -> Callable[...,Any]:
        def decorator(func:Callable[...,Any])->Any:
            """Cursor wrapping and secure closing"""
            @wraps(func)
            def wrapper(self,*args,**kwargs):
                # pointer to database -> allows to apply queries
                with self.db(**self.db_params) as active_db:
                    if autocommit: active_db.autocommit = True # -> needed for drop
                    cur = active_db.cursor()
                    try: 
                        result = func(self,cur,*args,**kwargs)
                        if cur.rowcount >=0:
                            print(f"{cur.rowcount} rows affected by transformation.")
                    except Exception as e:
                        result = f"Error during DB operation: {e}."
                        print(result)
                    finally:
                        # close the cursor to free up memory and resources associated with it after finished querying -> helps prevent memory leaks and keeps database interactions clean
                        self.executed_queries_history = getattr(cur, 'executed_queries', None)
                        cur.close()
                        if autocommit: active_db.autocommit = False
                return result if result else None
            return wrapper
            
        if callable(autocommit):
            func = autocommit
            autocommit = None
            return decorator(func)
        
        return decorator

class travelCRUD(BasicCRUD):
    def __init__(self,db:DatabaseConnection,db_params:Dict[str,Any],table_name:str,store_history:bool=False):
        self.db = db
        self.db_params = db_params
        self.table_name = table_name
        self.executed_queries_history:List[Any] = []
        self.fetch_results_history:List[Tuple[Any,Any]] = []
        self.store_history = store_history

    @BasicCRUD.db_operation
    def create_schema(self,cur):
        query = f"""CREATE TABLE IF NOT EXISTS {self.table_name}(
            booking_id UUID PRIMARY KEY,
            customer_id UUID NOT NULL,
            customer_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(50) NOT NULL,
            booking_date DATE NOT NULL,
            travel_date DATE NOT NULL,
            return_date DATE,
            destination VARCHAR(255),
            departure_city VARCHAR(255),
            flight_number VARCHAR(50),
            hotel_name VARCHAR(255),
            room_type VARCHAR(100),
            total_price NUMERIC(10, 2),
            payment_status VARCHAR(50),
            payment_method VARCHAR(50),
            travel_agency VARCHAR(255),
            special_requests TEXT,
            loyalty_program_number VARCHAR(50)
        );
        """
        cur.execute(query)
        print(f"Created table {self.table_name} successfully.")

    @BasicCRUD.db_operation
    def insert_data_from_list(self,cur,data:List[str]):
        """eg create_schema()"""
        query = f"""INSERT INTO {self.table_name} (booking_id, customer_id,customer_name, email,phone,booking_date,travel_date,return_date,destination,departure_city,flight_number,hotel_name,room_type,total_price, payment_status,payment_method,travel_agency,special_requests,loyalty_program_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cur.executemany(query,data)
        print(f"Inserted the data into {self.table_name} successfully.")
    
    @BasicCRUD.db_operation
    def get_email_addresses(self,cur):
        query = f"""
            SELECT DISTINCT email
            FROM {self.table_name}
            ORDER BY email ASC
            """
        cur.execute(query)
        result = cur.fetchall()
        if self.store_history: self.fetch_results_history.append((getattr(cur, 'executed_queries', None),result))
        return result
    
    @BasicCRUD.db_operation
    def get_booking_id(self,cur,booking_id:Optional[str]=None,page_size:int=50):
        if booking_id:
            query = f"""SELECT * 
                        FROM {self.table_name} 
                        WHERE booking_id = %s
                        """
            cur.execute(query,(booking_id,))
            result = cur.fetchone()
            result = BookingManager().convert_params_to_booking(result).json()
        else:
            query = f"""SELECT booking_id
                        FROM {self.table_name} 
                        LIMIT %s;
                        """
            cur.execute(query,(page_size,))
            result = cur.fetchall()
            result = [{'booking_id':res[0]} for res in result]
        if self.store_history: self.fetch_results_history.append((getattr(cur, 'executed_queries', None),result))
        return result
    
    @BasicCRUD.db_operation
    def update_payment_status(self,cur,booking_id:str,new_status:str):
        query = f"""UPDATE {self.table_name}
            SET payment_status = %s
            WHERE booking_id = %s
        """
        cur.execute(query,(booking_id,new_status))
        print(f"Payment status of booking {booking_id} set to {new_status}")    

    @BasicCRUD.db_operation
    def delete_booking(self,cur,booking_id:str):
        query= f"""DELETE FROM {self.table_name}
            WHERE booking_id = %s
        """
        cur.execute(query,(booking_id,))
        
    @BasicCRUD.db_operation
    def check_table_exists(self,cur):
        query=f"""SELECT 1 FROM pg_database WHERE datname = 'sqlalchemy1'"""
        #SELECT * FROM bookings LIMIT 1;
        cur.execute(query,(self.table_name,))
        result = cur.fetchone()
        if self.store_history: self.fetch_results_history.append((getattr(cur, 'executed_queries', None),result))
        print(f"Test for existance of Database {self.table_name} lead to {result=}.")
        return result
        
    @BasicCRUD.db_operation(autocommit=True)
    def delete_database(self,cur):
        query=f"""DROP DATABASE IF EXISTS {self.table_name}"""
        cur.execute(query)
        print(f"Database {self.table_name} dropped successfully, if it existed in the first place.")

class cachedTravelCRUD(travelCRUD):
    def __init__(self, db: DatabaseConnection, db_params: Dict[str, Any], table_name: str, store_history: bool = False,cache:Optional[Cache]=None):
        super().__init__(db, db_params, table_name, store_history)
        self.cache = cache if cache else LruCache(20,30)

    def get_booking_id(self,booking_id:Optional[str]=None,page_size:int=50):
        if booking_id:
            cached_booking = self.cache.get(booking_id)
            if cached_booking:
                print("Read from cache.")
                return cached_booking
            booking = super().get_booking_id(booking_id,page_size)
            print("Read from DB and wrote to cache.")
            if booking:
                self.cache.put(booking_id,booking)
            return booking
        else:
            print("Read from DB.")
            return super().get_booking_id(booking_id,page_size)
    
    def insert_data_from_list(self,data:List[str]):
        super().insert_data_from_list(data)
        for booking in data:
            booking_id = booking[0]
            self.cache.invalidate(booking_id)
            self.cache.put(booking_id,booking)

class CrudFactory:
    def __init__(self):
        pass
    def create_crud(self,crud:str,*params):
        crud_options = ["basic","travel","cachedTravel"]
        if crud == crud_options[0]:
            return BasicCRUD
        elif crud == crud_options[1]:
            return travelCRUD(*params)
        elif crud == crud_options[2]:
            return cachedTravelCRUD(*params)
        else:
            raise ValueError(f"Crud type not found. Maybe misspelled? The options are:\n>'{"' , '".join(crud_options)}'.")