from app.controller.csvParser import CsvParser
from app.model.booking import Booking, BookingAnalyzer, BookingManager

if __name__ == '__main__':
    print("こんにちは！元気ですか?")
    # do something
    file_path = 'data/travel_bookings.csv'
    csv_parser = CsvParser()
    booking_manager = BookingManager()
    booking_manager.add_bookings(csv_parser.parse_complete(file_path))
    bookings = booking_manager.get_all_bookings()
    booking_analyzer = BookingAnalyzer()
    dep_cities=booking_analyzer.bookings_per_departure_city(bookings)
    print(dep_cities)
    
    print("'Elegance is the elimination of excess.' – Bruce Lee")
    


