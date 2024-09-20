# Challenge 09 -- Custom Load Balancer Implementation

## The Challenge

- Build a **custom load balancer** from scratch that distributes incoming HTTP requests to multiple instances of your custom HTTP server (built in Task 5). Implement health checks to route traffic away from failing servers.
- This tests your ability to implement load balancing algorithms and system reliability measures without the help of established tools like HAProxy or NGINX

## The UML Diagram

same as [Challenge 08](./challenge-08-TaskQueue.md)

## The Solution

### Code Updates

- added `asyncNode.health_check` and `asyncNode.health_report` which get checked and reported by `asyncLoadBalancer` via `do_health_checks` and `get_health_reports` functions
- then added `health_check_routine` to `asyncDistributedBookingSystem.start()` to from time to time check on the `asynNode`s and replace them if necessary using `replace_dead_nodes` function
