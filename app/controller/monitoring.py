import asyncio
import os
from time import time
from typing import Any, Callable, Dict, List

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table


class PerformanceParams:
      
    
    def __init__(self,device_name:str,device_id:str,max_avg_length:int):
        self.device_name = device_name
        self.device_id = device_id
        self.max_avg_list_length = max_avg_length
        self.request_times:List[float] = []
        self.response_times:List[float] = []
        self.start_time = time()
        self.avg_requests_per_second:float = -1.0
        self.avg_response_time:float = -1.0
        self.last_update = time()
        self.uptime:str = ""
        self.uptime_raw:float=-1.0
    
    def add_request_time(self,request_time:float):
        self.add_perf_property(self.request_times,request_time)
    
    def add_response_time(self,response_time:float):
        self.add_perf_property(self.response_times,response_time)
    
    def add_perf_property(self,list_object:List[float],time_record:float):
        if len(list_object)>self.max_avg_list_length:
            list_object.pop(0)
        list_object.append(time_record)
        self.last_update = time()
    
    def calculate_average(self,list_object:List[float]):
        average = sum(list_object)/len(list_object)
        return average
    
    def calculate_averages(self):
        if len(self.request_times)>1:
            self.avg_requests_per_second = len(self.request_times)/(self.request_times[-1]-self.request_times[0])
        if len(self.response_times)>0:
            self.avg_response_time = self.calculate_average(self.response_times)
    
    def fmt_uptime(self,uptime_raw:float)->str:
        days = int(uptime_raw//86400)
        uptime = uptime_raw -days*86400
        hours = int(uptime //3600)
        uptime -= hours*3600
        minutes = int(uptime // 60)
        uptime -= minutes * 60
        seconds = int(round(uptime,0))
        uptime = f"{days} days {hours} hours {minutes} minutes {seconds} seconds"
        return uptime
    
    def calculate_uptime(self,start_time:float):
        uptime_raw = time()-start_time
        uptime = self.fmt_uptime(uptime_raw)
        return uptime,uptime_raw
    
    def get_perf_report(self)->Dict[str,Any]:
        self.calculate_averages()
        self.uptime,self.uptime_raw=self.calculate_uptime(self.start_time)
        return {'name': self.device_name,
                'id': self.device_id,
                'avg_requests_per_second': self.avg_requests_per_second,
                'avg_response_time': self.avg_response_time,
                'uptime': self.uptime,
                'uptime_raw': self.uptime_raw
                }
        

class CacheParams(PerformanceParams):
    def __init__(self, device_name: str, device_id: str, max_avg_length: int):
        super().__init__(device_name, device_id, max_avg_length)
        self.cache_hits:int = 0
        self.cache_misses:int=0
        self.hit_miss_ratio:int=-1
    
    def add_cache_hit(self):
        self.cache_hits+=1
        self.last_update = time()
        
    def add_cache_miss(self):
        self.cache_misses+=1
        self.last_update = time()
    
    def calculate_hit_miss_ratio(self):
        self.hit_miss_ratio = int(self.cache_hits/self.cache_misses*100)
        
    def get_perf_report(self) -> Dict[str, Any]:
        self.calculate_hit_miss_ratio()
        base_report:Dict[str,Any] = super().get_perf_report()
        cache_report:Dict[str,Any]={'cache_hits':self.cache_hits,
                  'cache_misses': self.cache_misses,
                  'cache_hit_miss_ratio': self.hit_miss_ratio}
        report = {**base_report,**cache_report}
        return report

class DashboardDisplay:
    def __init__(self,update_func:Callable[...,Any],main_device:str):
        self.update_func = update_func
        self.console = Console()
        self.is_running=False
        self.metrics:Dict[str,Any]={}
        self.main_device = main_device
        self.refresh_counter = 0
        
    
    def create_dashboard(self,metrics:Dict[str,Any]):
        layout = Layout(name='main',size=1)
        layout.split_column(
            Layout(Panel(f"{self.main_device} Dashboard", style="bold magenta"),size=3),
            Layout(self.create_metrics_table(metrics)),
            Layout(Panel(f"Last updated: {metrics['last_updated']}, Refresh#: {self.refresh_counter}",style='italic'),size=3))
        return layout

    def create_metrics_table(self, metrics:Dict[str,Any]):
        table = Table(show_header=False,expand=True)
        table.add_column("Metric",style="cyan",no_wrap=True)
        table.add_column("Value",style="green",no_wrap=False)
        table.add_row("Requests per Second",f"{metrics['avg_requests_per_second']:.2f}")
        table.add_row("AVG Response Time",f"{metrics['avg_response_time']:.2f} ms")
        #if 'cache_hit_miss_ratio' in metrics:
        table.add_row("Cache Hit Ratio",f"{metrics['cache_hit_miss_ratio']}% (Hits: {metrics['cache_hits']}, Misses: {metrics['cache_misses']})")
        table.add_row("Avg Node properties",f"CPU={metrics['node_cpu']}%, RAM={metrics['node_ram']}%, DISK={metrics['node_disk']}%, LATENCY={metrics['node_latency']:.2f} ms")
        table.add_row("Services Used in Analysis",f"{metrics['used_services']}")
        
        table.add_row("HTTP Server Uptime",metrics['uptime'])
        return table

    async def update_display(self):
        while True:
            self.refresh_counter+=1
            print("in Display")
            self.metrics = self.update_func()
            #self.console.clear()
            os.system("cls" if os.name == "nt" else "clear")
            dashboard = self.create_dashboard(self.metrics)
            self.console.print(dashboard)
            await asyncio.sleep(5)
    
    def start(self):
        self.health_task=asyncio.create_task(self.update_display())
        self.is_running=True
    
    def stop(self):
        self.is_running=False
        if self.health_task:
            self.health_task.cancel()
        