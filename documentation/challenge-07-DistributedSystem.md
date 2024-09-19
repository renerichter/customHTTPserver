# Challenge 07 -- Manual Distributed System Simulation

## The Challenge

- Design and implement a **simple distributed booking system** using **Python’s `socket` library**. Simulate multiple nodes (instances of your HTTP server) and manually handle the distribution of bookings across these nodes with basic load balancing (round-robin or random).
- This task requires understanding of distributed system concepts without relying on any external libraries or frameworks

## The UML Diagram

???

## The Solution

### Basic Idea

- hardware-abstraction = Node (runs instance of HTTP-server)
- LoadBalancer -> RoundRobin, Random, WeightedRoundRobin -> decides where to send request
- DistributedBookingSystem -> distributes requests among nodes
- central DB, connected to by all nodes individually -> concurrency!


