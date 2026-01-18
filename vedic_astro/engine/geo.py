from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

def get_location(name):
    """
    Fetches the latitude, longitude, and timezone for a given location name.

    Args:
        name (str): The name of the location (e.g., "New York", "Chennai").

    Returns:
        dict: A dictionary containing 'name', 'lat', 'lon', and 'tz' (timezone object),
              or None if the location could not be found.
    """
    try:
        # User agent is required by Nominatim
        geolocator = Nominatim(user_agent="dwara_panchang_final_v16", timeout=5)
        loc = geolocator.geocode(name)
        if not loc: return None
        
        # Find timezone based on coordinates
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
        
        return {
            'name': loc.address, 
            'lat': loc.latitude, 
            'lon': loc.longitude, 
            'tz': pytz.timezone(tz_str)
        }
    except: 
        return None
