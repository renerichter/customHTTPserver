# Challenge 12 -- Real-Time Monitoring with Custom Performance Metrics Dashboard

## The Challenge

--
### Goal
Build a **real-time monitoring system** that tracks performance metrics and displays them in a simple **dashboard**. The system should track key metrics like response times, request rates, cache hit/miss ratios, and system health across your HTTP server, caching, and load balancing components.

### Requirements

- **Custom Metrics Collection**:
    - Implement code to track and collect the following metrics:
        - **Average response time** for each request (across the system, including the HTTP server, cache lookup, and load balancer).
        - **Total requests per second** (measured at the load balancer and HTTP server).
        - **Cache hit/miss ratio** (measure the number of cache hits vs. misses to identify the efficiency of your cache).
        - **System uptime** (measure the total uptime of each component: HTTP server, cache, and load balancer).
  
- **Health Check Integration**:
    - Use the existing **health check endpoint** (from Task 9) and enhance it to return additional **performance and health data** (e.g., current memory usage, load balancer request queue size, cache size).
  
- **Metrics Dashboard**:
    - Build a **simple real-time dashboard** (can be a CLI-based or simple web-based interface) that displays the collected metrics.
    - Metrics should be refreshed periodically (e.g., every 5 seconds) and displayed in a **readable format**:
        - Average response time (in ms)
        - Requests per second
        - Cache hit/miss ratio
        - Uptime of each service
  
- **Alerting System** (Bonus):
    - Add an optional **alerting mechanism**: if certain thresholds are breached (e.g., average response time > 200ms or cache hit ratio < 50%), log a warning and send an alert to the console.

### Expected Output

- **Metrics Collected and Displayed** in real-time. Example:

  ```
  Real-Time Metrics Dashboard:
  -----------------------------------
  Requests per second: 120
  Average Response Time: 85 ms
  Cache Hit Ratio: 75% (Cache Hits: 300, Cache Misses: 100)
  HTTP Server Uptime: 2 days, 4 hours, 12 minutes
  Load Balancer Uptime: 2 days, 4 hours, 10 minutes
  -----------------------------------
  ```

- **Health Check Endpoint**: Should include uptime and memory usage.

  ```json
  {
    "status": "healthy",
    "uptime": "2 days 4 hours",
    "memory_usage_mb": 120,
    "cache_size_mb": 50
  }
  ```

## The UML Diagram

???

## The Solution

???
