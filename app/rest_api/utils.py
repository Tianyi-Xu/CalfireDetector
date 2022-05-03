from geopy.geocoders import Nominatim

def get_coordinates(loc):
    """Takes a location (address, city, county, or zip code) and returns the lat and long"""
    geolocator = Nominatim(user_agent="fire-alert")
    location = geolocator.geocode(loc)

    print(location.address, location.latitude, location.longitude)
    return location.latitude, location.longitude