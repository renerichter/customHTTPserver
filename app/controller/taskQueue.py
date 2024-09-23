import asyncio
from asyncio import Queue, TimeoutError
from dataclasses import dataclass
from logging import Logger
from random import randint
from typing import Any, Callable, List, Optional


@dataclass
class Task:
    func: Callable[...,Any]
    args: tuple[Any]
    kwargs: dict[str,Any]
    retries: int = 0
    max_retries: int = 3
    delay: float = 1.0
    dependent_task: Optional['Task'] = None
    
class TaskQueue:
    def __init__(self,parent_logger:Logger,name:str="",nworkers:int=3,qsize:int=20):
        self._nworkers = nworkers
        self._queue:Queue[Any] = Queue(qsize)
        self._workers:List[Any] = []
        self.is_running = False
        self._name = name if name else f"TQ-{randint(0,99999):05d}"
        self._logger = parent_logger.getChild(self._name)

    async def add_task(self,func:Callable[...,Any],*args:Any,**kwargs:Any):
        task = Task(func,args,kwargs)
        await self._queue.put(task)
        self._logger.info("Added task to queue: %s",func.__name__)

    async def run_worker(self, worker_id: int):
        while self.is_running:
            try:
                task = await asyncio.wait_for(self._queue.get(),timeout=1.0)    
            except TimeoutError:
                continue
            
            self._logger.info("Worker %s processing task: %s",worker_id,task.func.__name__)
            try:
                result = await task.func(*task.args,**task.kwargs)
                self._logger.info("Worker %s completed task: %s",worker_id,task.func.__name__)
                
                if task.dependent_task:
                    await self._queue.put(task.dependent_task)
                    self._logger.info("Queued dependent task: %s",task.dependent_task.func.__name__)
                return result
            except Exception as e:
                self._logger.error("Error in task %s: %s",task.func.__name__,str(e),exc_info=True)#self._logger.error(format_exc())
                if task.retries < task.max_retries:
                    task.retries += 1
                    task.delay *= 2
                    self._logger.info("Retrying task %s in %d seconds (attempt: %d/%d)",task.func.__name__,task.delay,task.retries,task.max_retries)
                    await asyncio.sleep(task.delay)
                    await self._queue.put(task)
                else:
                    self._logger.error("Task %s failed after %d retries",task.func.__name__,task.max_retries)
            finally:
                self._queue.task_done()

    async def start(self):    
        self.is_running = True
        self.workers = [asyncio.create_task(self.run_worker(i)) for i in range(self._nworkers)]
        self._logger.info("Started %d workers",self._nworkers)
    
    async def stop(self):
        self.is_running = False
        await self._queue.join()
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self.workers,return_exceptions=True)
        self._logger.info("All workers stopped")