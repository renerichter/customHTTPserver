# Challenge 11 -- Advanced Logging with Distributed Traceability

## The Challenge

### Goal

Implement a **distributed logging system** with support for **traceability** across multiple microservices (e.g., HTTP server, caching, load balancer). This should allow you to track requests end-to-end through the system and identify performance bottlenecks or errors.

### Requirements

- **End-to-End Request Traceability**: Implement **distributed tracing** by generating a unique **trace ID** for each incoming HTTP request. This trace ID should be passed through all components (HTTP server, caching system, load balancer) so that logs from each part of the system can be correlated.
    - Ensure the **trace ID** is included in logs for the HTTP server, load balancer, and cache interactions.
    - You can implement custom middleware in the HTTP server to generate or propagate the trace ID.
- **Structured and Contextual Logging**: All logs should be **structured** (e.g., JSON format) and contain contextual information such as:
    - **Timestamp**
    - **Request Method** (e.g., GET, POST)
    - **Request Path**
    - **Response Time** for each component (e.g., time spent in cache, time spent in the server, time for load balancer routing).
    - **Error Details** if applicable (e.g., 500 server errors, failed cache lookups).
- **Log Levels**: Implement different log levels (INFO, DEBUG, ERROR) for various components. Ensure error logs contain sufficient context to debug the issue (e.g., traceback for exceptions).
- **Log Aggregation**: Simulate a **log aggregation system** where logs from the distributed system (HTTP server, load balancer, cache) are collected into a central location (you can simulate this by writing logs from all services to a single file for this challenge). Optionally, consider using an external log management tool (like ELK stack or a simple file-based approach).

### Expected Output

- Logs must allow an administrator to **trace a single request** through the HTTP server, caching system, and load balancer using the unique trace ID.
- Example of a structured log entry:

  ```json
  {
    "timestamp": "2024-09-12T14:35:22.001Z",
    "trace_id": "abc123xyz",
    "service": "load_balancer",
    "level": "INFO",
    "method": "GET",
    "path": "/api/bookings",
    "response_time_ms": 15,
    "cache_hit": true
  }
  ```

- Logs should be **filterable** by trace ID to correlate multiple events.

## The UML Diagram

???

## The Solution

???
