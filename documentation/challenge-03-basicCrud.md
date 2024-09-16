# Challenge 03 -- Basic CRUD Application without Frameworks

## The Challenge

- Build a **basic CRUD (Create, Read, Update, Delete) system** to manage travel bookings using **PostgreSQL**. You’ll interact directly with PostgreSQL by writing raw SQL queries without using any ORM frameworks.
- Use Python’s built-in `psycopg2` library to:
    - Establish connections to the PostgreSQL database.
    - Execute **raw SQL queries** for managing bookings.
    - Ensure transactional consistency using manual `BEGIN`, `COMMIT`, and `ROLLBACK` SQL commands.
- Demonstrate manual handling of database connections, query execution, and safe use of transactions, especially focusing on:
    - Preventing SQL injection.
    - Managing **concurrent transactions** and dealing with potential issues like deadlocks.

## The UML Diagram

???

## The Solution

Setup basic postgresql server using [Docker-Compose script](../app/model/docker-compose.yml) as shown below. Run via `docker-compose -f docker-compose.yaml up`.

```docker-compose
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: postgres_sqlalchemy_playground
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: mypassword
      POSTGRES_DB: sqlalchemy1
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/my/path/to/customHTTPserver/postgresDB/data
volumes:
  postgres_data:
```
