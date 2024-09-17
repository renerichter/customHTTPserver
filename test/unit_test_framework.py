from sys import exit
from typing import Any, Callable, List, Tuple


class TestCase:
    def __init__(self,name: str):
        self.name = name
    
    def initialize(self):
        pass        

    def finalize(self):
        pass
        
    def run(self)->bool:
        try:
            self.initialize()
            method = getattr(self,self.name)
            method()
            self.finalize()
            print(f"Test {self.name} passed.")
            return True
        except AssertionError as e:
            print(f"Test {self.name} failed: {str(e)}")
            return False
        except Exception as e: 
            print(f"Error in test {self.name}: {str(e)}")
            return False
    
    
class TestSuite:
    def __init__(self):
        self.tests: List[TestCase] = []
    def add_test(self,test:TestCase):
        self.tests.append(test)
    def run(self) -> Tuple[int,int]:
        results = [test.run() for test in self.tests]
        total = len(results)
        passed = sum(results)
        return passed,total
    
    def do_tests(self):
        passed,total = self.run()
        print(f"Passed {passed} / {total} tests.")
        if passed<total:
            exit(1)
            
class Asserter:
    @staticmethod
    def assert_equal(actual: Any, expected: Any, message: str=""):
        assert actual == expected, f"Expected {expected}, but got {actual}. {message}"
    
    @staticmethod
    def assert_true(actual: Any, message: str=""):
        assert actual, message
        
    @staticmethod
    def assert_false(actual: Any, message: str=""):
        assert not actual, message
    
    @staticmethod
    def assert_raises(exception: Exception, callable: Callable[...,Any], *args, **kwargs):
        try: 
            callable(*args,**kwargs)
        except exception: 
            return
        except Exception as e:
            raise AssertionError(f"Excpected {exception.__name__}, but {type(e).__name__} was raised.")
        raise AssertionError(f"Expected {exception.__name__}, but no exception was raised.")