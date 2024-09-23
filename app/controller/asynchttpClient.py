import asyncio
from random import choices, random
from time import sleep
from typing import Any, Dict, Optional

import aiohttp
from names import CreativeNamer

test_cache = False

class TestAsyncHttpServer:
    def __init__(self,url:str,port:int):
        self.base_url = f"{url}:{port}"
    
    async def get_booking(self,booking_id:Optional[str]=None):
        url = f"{self.base_url}/booking"
        if booking_id:
            url+= f"/{booking_id}"
        headers = {'Connection':'close'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url,headers=headers) as response:
                print(f"GET Response: {response.status}")
                response_data = await response.json()
                print(response_data)
                return response_data
    
    async def create_booking(self,booking_data:Dict[str,Any]):
        url = f"{self.base_url}/booking"
        headers = {"Content-Type": "application/json"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url,json=booking_data,headers=headers) as response:
                print(f"POST Response: {response.status}")
                response_text = await response.text()
                print(response.text)
                return response_text

async def main():
    client_name  = CreativeNamer().create_name(2)
    print(f"Hello. This is {client_name}. Let's go!")
    client = TestAsyncHttpServer("http://localhost",8181)
    booking_ids = [{'booking_id': 'cda20bf0-06f0-47ee-ad46-c5ed670af9e0'}, {'booking_id': 'cc8bdf28-b1ea-4eb2-ba3f-8450e59e6b12'}, {'booking_id': 'cc19b04b-e132-44bf-8285-39def237ed4d'}, {'booking_id': 'd36930fe-4dff-492e-b3d4-d214c50a2569'}, {'booking_id': '806d75c2-1108-4171-9104-da40c639cc0c'}, {'booking_id': 'b93735c7-a51a-42e8-ac89-171896196fdf'}, {'booking_id': '74aad089-1a84-4e82-8d87-6d73eeacd903'}, {'booking_id': 'e2c03140-e3d0-4811-9162-c7cf705e77b0'}, {'booking_id': '9a9b0691-9517-4ab8-bcc6-ddbdefccd5d3'}, {'booking_id': '8bb2d138-28b6-44a9-bf3e-a0a9b0ecef29'}, {'booking_id': 'fb6b3247-7a34-48d3-8611-99dd0eb600b1'}, {'booking_id': 'ef84b5f1-ceff-4e1c-a158-934afaea0fa5'}, {'booking_id': '625cd3c9-0116-452f-816c-91aa6e236110'}, {'booking_id': '70d43d5e-e844-47d4-9757-a8db84ad5a4b'}, {'booking_id': 'f4ac0f92-0a66-40e1-86c0-c7c086ef6791'}, {'booking_id': '89433e64-9f13-4106-b6e5-5ab7514c8061'}, {'booking_id': '85b75ed0-b299-4dde-9f1b-2aac4d9439c2'}, {'booking_id': 'd321f4ff-9912-41ec-98c3-cd3a52cc7098'}, {'booking_id': 'a1313ea6-4861-4b9c-ac04-afd954133bc6'}, {'booking_id': 'df022341-b963-488c-842e-bdc31f3dce54'}, {'booking_id': 'f483f384-56d8-4b3d-8286-052d40d822c2'}, {'booking_id': 'b22c7796-457a-4d57-bc02-a2ae6d103133'}, {'booking_id': '990d6f1e-0c15-4855-ab3f-48494f96c096'}, {'booking_id': '4175b4d5-2d21-4348-af9d-ebfb221b33a6'}, {'booking_id': '011744c5-a647-49cf-82fd-f2f31d200c25'}, {'booking_id': '68fd9550-c449-419c-a227-fb24d7a786cb'}, {'booking_id': 'e0b43755-6155-47e8-8714-0ebb8a88c642'}, {'booking_id': 'b46c5ff8-839a-4b4c-aabd-47417e021a2e'}, {'booking_id': '54702c3a-6261-4e3a-9f66-edf6e6018803'}, {'booking_id': '1d9823ac-e594-45da-817c-be584aea8e4a'}, {'booking_id': 'e6a9e8f6-12d1-4ae7-a63b-7b7aaea512a9'}, {'booking_id': '2bb2ed74-bf59-46b7-a45c-896f9720aedd'}, {'booking_id': 'c9f09dbb-df89-4025-86e7-050fce0c4279'}, {'booking_id': 'e487070f-16b3-43bd-ba2a-cf4ead98c1af'}, {'booking_id': '8f003119-b1a0-4acd-96ff-ce95205c3740'}, {'booking_id': '4e5d78a7-b845-4b92-b87c-a29f82b71bbb'}, {'booking_id': 'a9f27e1a-395d-4d7f-b16a-635ccbcc4819'}, {'booking_id': 'b7772128-6276-47ff-b0eb-286562d1ba6e'}, {'booking_id': '7e6c19a2-e225-488e-80c8-8da09b549410'}, {'booking_id': '9b568bcc-ec67-4e9f-9207-053a9dc99ffb'}, {'booking_id': '5a612756-df47-4889-9d48-92fd1c8d973e'}, {'booking_id': '7cf74c12-48c9-4522-8757-c642955b5acc'}, {'booking_id': '169e46f6-6c81-47b0-a65d-91683a80cfbc'}, {'booking_id': '5622338c-2dd2-47a0-bca3-fe3658180790'}, {'booking_id': 'e19dab2b-a8f5-42ef-928b-ecb9dc953a55'}, {'booking_id': '3187af2b-4396-44b6-9179-37560a32c71a'}, {'booking_id': '71fcb408-678c-4de1-9133-565c2c0fa46b'}, {'booking_id': 'd8fbff4c-d14c-4a6f-9229-f5f38848c47f'}, {'booking_id': '9467163b-cb1b-4dd4-ab2d-9b09a457c317'}, {'booking_id': '0db66751-a605-4943-8661-60c5213beafe'}]
    #client.get_booking()
    booking_length = 30
    booking_ids_used = [{'booking_id': 'cda20bf0-06f0-47ee-ad46-c5ed670af9e0'},]*booking_length if test_cache else choices(booking_ids,k=booking_length)
        
    for i in range(booking_length):
        sleep(0.5+random()*5)
        await client.get_booking(booking_ids_used[i]['booking_id'])
        print(f"{client_name}--->R{i:02}--->✅")
    print(booking_ids_used)
    
    # new_booking:Dict[str,Any] = {
    #     "booking_id": str(uuid4()),
    #     "customer_id": str(uuid4()),
    #     "customer_name": "John Doe",
    #     "email": "john@example.com",
    #     "phone": "1234567890",
    #     "booking_date": "2024-09-17",
    #     "travel_date": "2024-10-01",
    #     "return_date": "2024-10-12",
    #     "destination": "Paris",
    #     "departure_city": "New York",
    #     "flight_number": "AB123",
    #     "hotel_name": "Paris Hotel",
    #     "room_type": "Deluxe",
    #     "total_price": 1500.00,
    #     "payment_status": "Paid",
    #     "payment_method": "Credit Card",
    #     "travel_agency": "Foo Travelers",
    #     "special_requests": "No special request",
    #     "loyalty_program_number": 'LP123a8',
    # }
    # client.create_booking(new_booking)

if __name__ == '__main__':
    asyncio.run(main())
    print("nice")
    
    
    
    
