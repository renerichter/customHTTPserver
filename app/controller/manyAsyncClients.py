from subprocess import Popen
from typing import Any, List


def spawn_clients(n_clients:int):
    print("Assuming to be running in Archive-top path.")
    processes:List[Popen[Any]] = []
    for _ in range(n_clients):
        process:Popen[Any] = Popen(['python','./app/controller/asynchttpClient.py'])
        processes.append(process)
        
    for process in processes:
        process.wait()

if __name__ == '__main__':
    n_clients = 2
    spawn_clients(n_clients)

