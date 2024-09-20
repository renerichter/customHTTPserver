# Challenge 08 -- Custom Asynchronous Task Queue

## The Challenge

- Implement a **custom task queue** using Python’s built-in `queue` module to process bookings asynchronously. Simulate background tasks like sending booking confirmation emails after bookings are completed. The task queue should handle failures and retry logic.
- This tests your understanding of concurrent programming, task scheduling, and message-driven architectures without relying on pre-built solutions like `Celery`.

## The UML Diagram

???

## The Solution

### Files Changed

### Basic Idea

- Q1: Where is the bottle-neck and which tasks do need to be in a task-queue? 
    - `DistributedBookingSystem`
    - each `Node`
    - but problem: if taskQueue leads to DistributedBookingSystem task need to wait before execution then process could be clodes due to `asyncio.wait_for`-statement around `asyncio.gather` in `DistributedBookingSystem.handle_client`
    - so for now: 1 for DistributedBookingSystem
- On this addition also
    - ✅test caching -> what is in the cache and why is it not re-used -> test with all the same entries.
