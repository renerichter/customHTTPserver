from typing import Any, Callable, Dict, List, Optional, Tuple

from unit_test_framework import Asserter, TestCase, TestSuite

from app.model.database import DatabaseConnection, travelCRUD


class MockCursor:
    def __init__(self):
        self.executed_queries:List[Any] = []
        self.fetch_results = []
        self.rowcount=0
    
    def execute(self,query:str,params:Tuple[Any,...]=()):
        self.executed_queries.append((query,params))
        self.rowcount = 1
    
    def executemany(self,query:str,params:Tuple[Any,...]=()):
        self.executed_queries.append((query,params))
        self.rowcount = len(params) if params else 0
    
    def fetchall(self) ->Optional[List[Any]]:
        return self.fetch_results

    def fetchone(self) -> Optional[Any]:
        return self.fetch_results[0] if self.fetch_results else None

class MockDB:
    def __init__(self):
        self.mock_cursor = MockCursor()
    
    def cursor(self):
        return self.mock_cursor

class MockDatabaseConnection(DatabaseConnection):
    def __init__(self,**kwargs):
        self.cursor_instance = MockCursor()
        self.autocommit = False
    
    def __enter__(self) -> Callable[...,Any]:
        return self

    def __call__(self,**kwargs):
        return self

    def cursor(self):
        return self.cursor_instance
    
    def __exit__(self,exc_type,exc_val,exc_tb):
        pass

class TestTravelCrud(TestCase):
    def initialize(self):
        # get DB
        self.db_params: Dict[str,Any] = {'host':'localhost','port':5432}
        self.table_name = 'test_bookings'
        
        # 
        self.crud = travelCRUD(MockDatabaseConnection,self.db_params,self.table_name)
    
    def finalize(self):
        self.crud.db().cursor.executed_queries = []          
        self.crud.db().cursor.fetch_results = []          
    
    def test_create_schema(self):
        self.crud.create_schema()
        executed_query = self.crud.db().cursor.executed_queries[0][0]
        Asserter.assert_true("CREATE TABLE IF NOT EXISTS" in executed_query,"CREATE TABLE query not executed")
        Asserter.assert_true(self.table_name in executed_query, "Table name not in CREATE TABLE query")

if __name__ == '__main__':
    test_suite = TestSuite()
    test_methods = [method for method in dir(TestTravelCrud) if method.startswith('test_')]
    for method in test_methods:
        test_suite.add_test(TestTravelCrud(method))
    test_suite.do_tests()
    print("nice")