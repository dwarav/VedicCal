"""
FastAPI Sunrise & Sunset Calculator
Calculates sunrise, sunset, and solar times for any location with timezone support
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import pytz
from timezonefinder import TimezoneFinder
import math

app = FastAPI(title="Sunrise & Sunset Calculator API", version="1.0")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize timezone finder
tf = TimezoneFinder()


class LocationRequest(BaseModel):
    latitude: float
    longitude: float
    date: str = None  # Format: YYYY-MM-DD, defaults to today


class SunTimesResponse(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    date: str
    timezone: str
    gmt_offset: str
    sunrise: str
    sunset: str
    sunrise_ampm: str
    sunset_ampm: str
    solar_noon: str
    day_length: str
    civil_twilight_begin: str
    civil_twilight_end: str


def calculate_sunrise_sunset(latitude: float, longitude: float, date: datetime):
    """
    Calculate sunrise and sunset times using astronomical algorithms
    Returns times in UTC
    """
    # Convert to radians
    lat = math.radians(latitude)
    lon = math.radians(longitude)
    
    # Day of year (1-365)
    day_of_year = date.timetuple().tm_yday
    
    # Equation of Time (minutes)
    b = (360 / 365) * (day_of_year - 1)
    b_rad = math.radians(b)
    eot = 229.18 * (0.000075 + 0.001868 * math.cos(b_rad) - 
                    0.032077 * math.sin(b_rad) - 0.014615 * math.cos(2 * b_rad) - 
                    0.040849 * math.sin(2 * b_rad))
    
    # Solar declination (radians)
    declination = math.radians(23.44 * math.sin(math.radians(360 * (day_of_year - 81) / 365)))
    
    # Solar noon (minutes from midnight UTC)
    solar_noon_minutes = 720 - 4 * math.degrees(lon) - eot
    
    # Sunrise/Sunset calculation (horizon = -0.833 degrees for refraction)
    horizon = math.radians(-0.833)
    
    numerator = math.sin(horizon) - math.sin(lat) * math.sin(declination)
    denominator = math.cos(lat) * math.cos(declination)
    
    if abs(numerator / denominator) > 1:
        # Sun doesn't rise or set
        cos_h = numerator / denominator
    else:
        cos_h = numerator / denominator
    
    h = math.degrees(math.acos(cos_h))
    
    # Sunrise and sunset (minutes from midnight UTC)
    sunrise_minutes = solar_noon_minutes - 4 * h
    sunset_minutes = solar_noon_minutes + 4 * h
    
    # Convert to datetime
    base_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    sunrise_utc = base_date + timedelta(minutes=sunrise_minutes)
    sunset_utc = base_date + timedelta(minutes=sunset_minutes)
    solar_noon_utc = base_date + timedelta(minutes=solar_noon_minutes)
    
    # Civil twilight (sun 6 degrees below horizon)
    tw_angle = 6
    declination_deg = 23.44 * math.sin(math.radians(360 * (day_of_year - 81) / 365))
    cos_h_tw = (math.sin(math.radians(-tw_angle)) - 
                math.sin(lat) * math.sin(math.radians(declination_deg))) / (
                math.cos(lat) * math.cos(math.radians(declination_deg)))
    
    if abs(cos_h_tw) <= 1:
        h_tw = math.degrees(math.acos(cos_h_tw))
        twilight_begin_minutes = solar_noon_minutes - 4 * h_tw
        twilight_end_minutes = solar_noon_minutes + 4 * h_tw
        
        twilight_begin = base_date + timedelta(minutes=twilight_begin_minutes)
        twilight_end = base_date + timedelta(minutes=twilight_end_minutes)
    else:
        twilight_begin = sunrise_utc
        twilight_end = sunset_utc
    
    return {
        'sunrise': sunrise_utc,
        'sunset': sunset_utc,
        'solar_noon': solar_noon_utc,
        'twilight_begin': twilight_begin,
        'twilight_end': twilight_end
    }


def get_timezone_and_offset(latitude: float, longitude: float):
    """Get timezone name and current offset for coordinates"""
    try:
        tz_name = tf.timezone_at(lng=longitude, lat=latitude)
        if not tz_name:
            tz_name = "UTC"
        
        # Get current offset
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        offset = now.strftime('%z')
        
        # Format offset as UTC +/-HH:MM
        hours = int(offset[0:3])
        minutes = int(offset[3:5])
        gmt_offset = f"UTC {'+' if hours >= 0 else ''}{hours}:{minutes:02d}"
        
        return tz_name, gmt_offset
    except:
        return "UTC", "UTC +0:00"


def format_time_in_timezone(dt_utc: datetime, tz_name: str, am_pm: bool = False):
    """Convert UTC time to specified timezone"""
    tz = pytz.timezone(tz_name)
    dt_local = dt_utc.replace(tzinfo=pytz.UTC).astimezone(tz)
    
    if am_pm:
        return dt_local.strftime("%I:%M %p")
    else:
        return dt_local.strftime("%H:%M")


def get_ampm(dt_utc: datetime, tz_name: str):
    """Get AM/PM for a UTC time in specific timezone"""
    tz = pytz.timezone(tz_name)
    dt_local = dt_utc.replace(tzinfo=pytz.UTC).astimezone(tz)
    return dt_local.strftime("%p")


def format_duration(delta: timedelta):
    """Format timedelta as 'Xh Ym'"""
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}h {minutes}m"


@app.post("/api/sun-times", response_model=SunTimesResponse)
async def get_sun_times(request: LocationRequest):
    """
    Calculate sunrise, sunset, and solar times for a location
    
    Parameters:
    - latitude: float (e.g., 17.3667)
    - longitude: float (e.g., 81.7833)
    - date: string in YYYY-MM-DD format (optional, defaults to today)
    """
    try:
        # Validate coordinates
        if not (-90 <= request.latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= request.longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        
        # Parse date
        if request.date:
            calc_date = datetime.strptime(request.date, "%Y-%m-%d")
        else:
            calc_date = datetime.now()
        
        # Get timezone
        tz_name, gmt_offset = get_timezone_and_offset(request.latitude, request.longitude)
        
        # Calculate sun times
        times = calculate_sunrise_sunset(request.latitude, request.longitude, calc_date)
        
        # Format times in local timezone
        sunrise_time = format_time_in_timezone(times['sunrise'], tz_name)
        sunset_time = format_time_in_timezone(times['sunset'], tz_name)
        sunrise_ampm = get_ampm(times['sunrise'], tz_name)
        sunset_ampm = get_ampm(times['sunset'], tz_name)
        solar_noon_time = format_time_in_timezone(times['solar_noon'], tz_name)
        twilight_begin = format_time_in_timezone(times['twilight_begin'], tz_name)
        twilight_end = format_time_in_timezone(times['twilight_end'], tz_name)
        
        # Calculate day length
        day_length = format_duration(times['sunset'] - times['sunrise'])
        
        return SunTimesResponse(
            location_name=f"{request.latitude:.4f}, {request.longitude:.4f}",
            latitude=round(request.latitude, 4),
            longitude=round(request.longitude, 4),
            date=calc_date.strftime("%Y-%m-%d"),
            timezone=tz_name,
            gmt_offset=gmt_offset,
            sunrise=sunrise_time,
            sunset=sunset_time,
            sunrise_ampm=sunrise_ampm,
            sunset_ampm=sunset_ampm,
            solar_noon=solar_noon_time,
            day_length=day_length,
            civil_twilight_begin=twilight_begin,
            civil_twilight_end=twilight_end
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating sun times: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Sunrise & Sunset Calculator API"}


@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "name": "Sunrise & Sunset Calculator API",
        "version": "1.0",
        "endpoints": {
            "POST /api/sun-times": "Calculate sunrise/sunset times",
            "GET /api/health": "Health check"
        },
        "example": {
            "url": "/api/sun-times",
            "method": "POST",
            "body": {
                "latitude": 17.3667,
                "longitude": 81.7833,
                "date": "2025-12-25"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
