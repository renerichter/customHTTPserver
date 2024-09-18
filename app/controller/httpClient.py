from typing import Any, Dict, Optional
from uuid import uuid4

from requests import get, post


class TestHTTPServer:
    def __init__(self,url:str,port:int):
        self.base_url = f"{url}:{port}"
    
    def get_booking(self,booking_id:Optional[str]=None):
        url = f"{self.base_url}/booking"
        if booking_id:
            url+= f"/{booking_id}"
        response = get(url)
        print(f"GET Response: {response.status_code}")
        print(response.json())
    
    def create_booking(self,booking_data:Dict[str,Any]):
        url = f"{self.base_url}/booking"
        headers = {"Content-Type": "application/json"}
        response = post(url, json=booking_data,headers=headers)
        print(f"POST Response: {response.status_code}")
        print(response.text)

if __name__ == '__main__':
    client = TestHTTPServer("http://localhost",8181)
    #client.get_booking()
    #client.get_booking('fb6b3247-7a34-48d3-8611-99dd0eb600b1')
    
    new_booking:Dict[str,Any] = {
        "booking_id": str(uuid4()),
        "customer_id": str(uuid4()),
        "customer_name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "booking_date": "2024-09-17",
        "travel_date": "2024-10-01",
        "return_date": "2024-10-12",
        "destination": "Paris",
        "departure_city": "New York",
        "flight_number": "AB123",
        "hotel_name": "Paris Hotel",
        "room_type": "Deluxe",
        "total_price": 1500.00,
        "payment_status": "Paid",
        "payment_method": "Credit Card",
        "travel_agency": "Foo Travelers",
        "special_requests": "No special request",
        "loyalty_program_number": 'LP123a8',
    }
    client.create_booking(new_booking)
    print("nice")