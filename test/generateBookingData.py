import random
from csv import writer as csvWriter
from datetime import timedelta

from faker import Faker

# Initialize Faker object
fake = Faker()

# Define the number of rows for the dataset
num_records = 100

# Define possible values for specific fields
destinations = ['Paris (France)', 'Tokyo (Japan)', 'New York (USA)', 'Berlin (Germany)', 'Sydney (Australia)']
departure_cities = ['Los Angeles (USA)', 'London (UK)', 'Toronto (Canada)', 'Dubai (UAE)', 'Singapore']
room_types = ['Deluxe Suite', 'Standard Room', 'Family Room', 'Penthouse', 'Economy Room']
payment_methods = ['Credit Card', 'PayPal', 'Bank Transfer', 'Cryptocurrency']
payment_statuses = ['Paid', 'Pending', 'Cancelled']
special_requests = ['Vegetarian meal', 'Window seat', 'Late check-out', 'Early check-in', 'No special request']

# Create CSV file and write header
with open('../data/travel_bookings.csv', mode='w', newline='') as file:
    writer = csvWriter(file)
    
    # Write the header row
    writer.writerow(['Booking ID', 'Customer ID', 'Customer Name', 'Email', 'Phone', 'Booking Date', 'Travel Date', 
                     'Return Date', 'Destination', 'Departure City', 'Flight Number', 'Hotel Name', 'Room Type', 
                     'Total Price', 'Payment Status', 'Payment Method', 'Travel Agency', 'Special Requests', 'Loyalty Program Number'])

    # Write each booking row
    for _ in range(num_records):
        booking_id = fake.uuid4()
        customer_id = fake.uuid4()
        customer_name = fake.name()
        email = fake.email()
        phone = fake.phone_number()
        booking_date = fake.date_this_year()
        travel_date = fake.date_between(start_date=booking_date, end_date=booking_date + timedelta(days=30))
        return_date = fake.date_between(start_date=travel_date, end_date=travel_date+timedelta(days=15))
        destination = random.choice(destinations)
        departure_city = random.choice(departure_cities)
        flight_number = f"{fake.random_uppercase_letter()}{fake.random_uppercase_letter()}{random.randint(100, 999)}"
        hotel_name = fake.company().replace(",","") + ' Hotel'
        room_type = random.choice(room_types)
        total_price = round(random.uniform(500, 5000), 2)
        payment_status = random.choice(payment_statuses)
        payment_method = random.choice(payment_methods)
        travel_agency = fake.company()
        special_request = random.choice(special_requests)
        loyalty_program_number = fake.bothify(text='LP#####')
        
        # Write the row to CSV
        writer.writerow([booking_id, customer_id, customer_name, email, phone, booking_date, travel_date, 
                         return_date, destination, departure_city, flight_number, hotel_name, room_type, 
                         total_price, payment_status, payment_method, travel_agency, special_request, loyalty_program_number])

print(f"Generated {num_records} travel bookings and saved to 'travel_bookings.csv'")
