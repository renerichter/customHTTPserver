from datetime import date
from typing import Any, List, Optional, Tuple

from pydantic import BaseModel


class Booking(BaseModel):
    booking_id:str
    customer_id:str
    customer_name:str
    email:str
    phone: str
    booking_date: date
    travel_date: date
    return_date: Optional[date] 
    destination: str
    departure_city: str
    flight_number: str
    hotel_name: str
    room_type: str
    total_price: float
    payment_status: str
    payment_method: str
    travel_agency: Optional[str]
    special_requests: Optional[str]
    loyalty_program_number: Optional[str]
    
    def get_as_dict(self):
        return self.model_dump()
    
    def get_keys_as_list(self)->List[Any]: 
        model_dict = self.get_as_dict()
        return model_dict.keys()
        
    def get_values_as_list(self)->List[Any]:
        model_dict = self.get_as_dict()
        return list(model_dict.values())
    
    class Config:
        arbitrary_types_allowed = True
        anystr_strip_whitespace = True

class BookingManager:
    def __init__(self,bookings:List[Booking]=[])->None:
        self._bookings:List[Booking] = bookings
        self._booking_fields:List[str] = list(Booking.model_fields.keys())
    
    def add_bookings(self,bookings:List[List[str]])->None:
        assert isinstance(bookings[0][0],str), "No list of strings given or degree of list nesting not matching"
        self._bookings+=[Booking(**dict(zip(self._booking_fields,item))) for item in bookings]
    
    def add_booking(self,booking:List[str])->None:
        self._bookings.append(Booking(*booking))
    
    def get_all_bookings(self)->List[Booking]:
        return self._bookings
    
    def to_list(self,idx):
        return [self._bookings[idx].get_keys_as_list(),self._bookings[idx].get_values_as_list()]
    
    def all_bookings_to_list(self):
        new_keys=self._bookings[0].get_keys_as_list()
        new_values=[booking.get_values_as_list() for booking in self._bookings]
        return new_keys,new_values
        

class BookingAnalyzer:
    def bookings_per_departure_city(self,bookings:List[Booking])->List[tuple[str,Any]]:
        city_counter:dict[str,Any] = {}
        for book in bookings:
            city_counter[book.departure_city] = city_counter.get(book.departure_city,0)+1
        
        # sort from biggest to smallest
        return sorted(city_counter.items(),key=lambda item: item[1],reverse=True) 
    
    def average_booking_price(self):
        pass
    
    def most_frequent_destination(self):
        pass