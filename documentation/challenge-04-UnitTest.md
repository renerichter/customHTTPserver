# Challenge 04 -- Custom Unit Testing Framework

## The Challenge

- Implement your own **basic unit testing framework** from scratch, mimicking some functionality of `unittest` or `pytest`. Then, use it to test your CRUD application.
- This will demonstrate your deep understanding of testing concepts and building tools from the ground up.

## The UML Diagram

???

## The Solution

classes 

MockCursor -> execute, ...
MockDatabaseConnection -> enter,exit
MockDB -> cursor


TestCase -> init, run; assertions

TestSuite -> add_test, run

TestTravelCrud(TestCase) -> setUp,test_create_schema, test_insert_...
# -> tests on real class, but with all fake data and interfaces


