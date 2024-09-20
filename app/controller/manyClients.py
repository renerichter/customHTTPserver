from subprocess import Popen


def spawn_clients(n_clients:int):
    print("Assuming to be running in Archive-top path.")
    processes = []
    for _ in range(n_clients):
        process = Popen(['python','./app/controller/httpClient.py'])
        processes.append(process)
        
    for process in processes:
        process.wait()

if __name__ == '__main__':
    n_clients = 10
    spawn_clients(n_clients)

