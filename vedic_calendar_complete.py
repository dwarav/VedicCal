"""
Comprehensive Vedic Calendar with Complete Muhurta Timings
Calculates: Tithi, Nakshatra, Masa, Vaara, Yoga, Karana
Plus: Amruthakala, Rahukalam, Yamagandam, Varjyam, Durmuhurta, 
      Brahma Muhurta, Vijaya Muhurta with start/end times
"""

import swisseph as swe
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List
import requests
import json
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

# ==================== Constants ====================

TITHI_NAMES = {
    'Shukla': [
        "Pratipada/Padyami", "Dwitiya/Vidiya", "Tritiya/Tadiya", "ChaturthChavithii", "Panchami",
        "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
        "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima"
    ],
    'Krishna': [
        "Pratipada/Padyami", "Dwitiya/Vidiya", "Tritiya/Tadiya", "Chaturthi/Chavithi", "Panchami",
        "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
        "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
    ]
}

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",
    "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus",
    "Sun", "Moon", "Mars", "Rahu", "Jupiter",
    "Saturn", "Mercury"
]

MASA_NAMES = [
    "Chaitra", "Vaisakha", "Jyaishtha", "Ashadha",
    "Shravana", "Bhadrapada", "Ashwina", "Kartika",
    "Margashirsha", "Pausha", "Magha", "Phalguna"
]

VAARA_NAMES = [
    "Ravivara", "Somavara", "Mangalavara", "Budhavara", "Guruvara", "Shukravara", "Shanivara"
]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti"
]

KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja",
    "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"
]

# ==================== Helper Functions ====================

def detect_user_location() -> Optional[Dict]:
    """Detect current location using IP geolocation"""
    try:
        response = requests.get('http://ip-api.com/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon'),
                    'city': data.get('city', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'timezone': data.get('timezone', 'UTC'),
                }
    except:
        try:
            response = requests.get('https://ipapi.co/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'city': data.get('city', 'Unknown'),
                    'country': data.get('country_name', 'Unknown'),
                    'timezone': data.get('timezone', 'UTC'),
                }
        except:
            pass
    return None


def geocode_location(name: str) -> Optional[Dict]:
    """Resolve a free-text location name to latitude/longitude using
    OpenStreetMap Nominatim. Returns same shape as `detect_user_location()`.
    """
    try:
        url = 'https://nominatim.openstreetmap.org/search'
        params = {'q': name, 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'VedicCal/1.0 (+https://github.com/)'}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                item = data[0]
                display = item.get('display_name', '')
                # Best-effort split for city/country
                parts = [p.strip() for p in display.split(',')]
                city = parts[0] if parts else display
                country = parts[-1] if len(parts) > 1 else ''
                lat = float(item.get('lat'))
                lon = float(item.get('lon'))

                # Try to determine timezone locally if timezonefinder is installed
                tzname = None
                try:
                    from timezonefinder import TimezoneFinder
                    tf = TimezoneFinder()
                    tzname = tf.timezone_at(lng=lon, lat=lat)
                except Exception:
                    tzname = None

                # If timezonefinder not available or failed, try Nominatim reverse with extratags
                if not tzname:
                    try:
                        rev_url = 'https://nominatim.openstreetmap.org/reverse'
                        rev_params = {'lat': lat, 'lon': lon, 'format': 'json', 'extratags': 1}
                        rev_headers = {'User-Agent': 'VedicCal/1.0 (+https://github.com/)'}
                        rev_resp = requests.get(rev_url, params=rev_params, headers=rev_headers, timeout=5)
                        if rev_resp.status_code == 200:
                            rev_data = rev_resp.json()
                            et = rev_data.get('extratags') or {}
                            tz_try = et.get('timezone') or et.get('time_zone')
                            if tz_try:
                                tzname = tz_try
                    except Exception:
                        tzname = None

                # Final fallback: if tzname not available, compute a rough offset
                # based on longitude and provide a tzinfo object.
                if not tzname:
                    try:
                        # rough offset hours from longitude (not DST-aware)
                        offset_hours = int(round(lon / 15.0))
                        tzinfo_fallback = timezone(timedelta(hours=offset_hours))
                    except Exception:
                        tzinfo_fallback = timezone.utc
                    tz_field = tzinfo_fallback
                else:
                    tz_field = tzname

                return {
                    'latitude': lat,
                    'longitude': lon,
                    'city': city,
                    'country': country,
                    'timezone': tz_field
                }
    except Exception:
        pass
    return None

def get_julian_day(dt: datetime, tz: Optional[object] = None) -> float:
    """Convert a local `dt` to Julian Day in UT.

    - `tz` may be:
      - a tz database name string (e.g. 'Asia/Kolkata')
      - a `datetime.tzinfo` instance (e.g. timezone(timedelta(hours=5,minutes=30)))
      - None: then system local timezone is used.
    - Returns JD for UT (UTC) to be passed to Swiss Ephemeris.
    """
    # Make dt timezone-aware
    if dt.tzinfo is None:
        if tz is None:
            dt = dt.astimezone()
        else:
            # tz can be a tzinfo or a string
            if isinstance(tz, str):
                if ZoneInfo is not None:
                    try:
                        tzinfo = ZoneInfo(tz)
                    except Exception:
                        tzinfo = None
                else:
                    tzinfo = None
            elif isinstance(tz, timezone) or hasattr(tz, 'utcoffset'):
                tzinfo = tz
            else:
                tzinfo = None

            if tzinfo is not None:
                dt = dt.replace(tzinfo=tzinfo)
            else:
                # fallback to system local
                dt = dt.astimezone()

    # Convert to UTC
    dt_utc = dt.astimezone(timezone.utc)
    year, month, day = dt_utc.year, dt_utc.month, dt_utc.day
    hour = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(year, month, day, hour)

def get_planet_position(jd: float, planet: int) -> Dict:
    """Get sidereal planet position"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    result = swe.calc_ut(jd, planet, flags)
    return {
        'longitude': result[0][0],
        'speed': result[0][3]
    }

def calculate_sunrise_sunset(jd: float, lat: float, lon: float) -> Dict:
    """Calculate sunrise and sunset"""
    try:
        swe.set_topo(lon, lat, 0)

        rise = swe.rise_trans(jd, swe.SUN, geopos=(lon, lat, 0), 
                             rsmi=swe.CALC_RISE | swe.BIT_DISC_CENTER)
        sunset = swe.rise_trans(jd, swe.SUN, geopos=(lon, lat, 0), 
                               rsmi=swe.CALC_SET | swe.BIT_DISC_CENTER)

        if rise[0] >= 0 and sunset[0] >= 0:
            sunrise_cal = swe.revjul(rise[1][0])
            sunset_cal = swe.revjul(sunset[1][0])

            sr_h = int(sunrise_cal[3])
            sr_m = int((sunrise_cal[3] - sr_h) * 60)
            sr_s = int(((sunrise_cal[3] - sr_h) * 60 - sr_m) * 60)

            ss_h = int(sunset_cal[3])
            ss_m = int((sunset_cal[3] - ss_h) * 60)
            ss_s = int(((sunset_cal[3] - ss_h) * 60 - ss_m) * 60)

            sunrise_datetime = datetime(int(sunrise_cal[0]), int(sunrise_cal[1]), 
                                       int(sunrise_cal[2]), sr_h, sr_m, sr_s)
            sunset_datetime = datetime(int(sunset_cal[0]), int(sunset_cal[1]), 
                                      int(sunset_cal[2]), ss_h, ss_m, ss_s)

            return {
                'sunrise': sunrise_datetime,
                'sunset': sunset_datetime,
                'sunrise_str': f"{sr_h:02d}:{sr_m:02d}:{sr_s:02d}",
                'sunset_str': f"{ss_h:02d}:{ss_m:02d}:{ss_s:02d}"
            }
    except:
        pass

    return {
        'sunrise': None,
        'sunset': None,
        'sunrise_str': 'N/A',
        'sunset_str': 'N/A'
    }


def calculate_moonrise_moonset(jd: float, lat: float, lon: float) -> Dict:
    """Calculate moonrise and moonset times using Swiss Ephemeris"""
    try:
        swe.set_topo(lon, lat, 0)

        rise = swe.rise_trans(jd, swe.MOON, geopos=(lon, lat, 0), rsmi=swe.CALC_RISE)
        set_ = swe.rise_trans(jd, swe.MOON, geopos=(lon, lat, 0), rsmi=swe.CALC_SET)

        if rise[0] >= 0 and set_[0] >= 0:
            rise_cal = swe.revjul(rise[1][0])
            set_cal = swe.revjul(set_[1][0])

            r_h = int(rise_cal[3])
            r_m = int((rise_cal[3] - r_h) * 60)
            r_s = int(((rise_cal[3] - r_h) * 60 - r_m) * 60)

            s_h = int(set_cal[3])
            s_m = int((set_cal[3] - s_h) * 60)
            s_s = int(((set_cal[3] - s_h) * 60 - s_m) * 60)

            moonrise_datetime = datetime(int(rise_cal[0]), int(rise_cal[1]), int(rise_cal[2]), r_h, r_m, r_s)
            moonset_datetime = datetime(int(set_cal[0]), int(set_cal[1]), int(set_cal[2]), s_h, s_m, s_s)

            # Fix day wrapping: if moonset is before moonrise, add 1 day to moonset
            if moonset_datetime < moonrise_datetime:
                moonset_datetime = moonset_datetime + timedelta(days=1)

            return {
                'moonrise': moonrise_datetime,
                'moonset': moonset_datetime,
                'moonrise_str': f"{r_h:02d}:{r_m:02d}:{r_s:02d}",
                'moonset_str': f"{s_h:02d}:{s_m:02d}:{s_s:02d}"
            }
    except:
        pass

    return {
        'moonrise': None,
        'moonset': None,
        'moonrise_str': 'N/A',
        'moonset_str': 'N/A'
    }

def calculate_tithi_transition_times(jd: float) -> Dict:
    """Calculate tithi start and end times by finding elongation boundaries"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # Current tithi
    sun = get_planet_position(jd, swe.SUN)
    moon = get_planet_position(jd, swe.MOON)
    elongation = (moon['longitude'] - sun['longitude']) % 360
    tithi_idx = int(elongation / 12) + 1
    
    # Find when current tithi started (previous 12-degree boundary)
    tithi_start_elongation = (tithi_idx - 1) * 12
    tithi_end_elongation = tithi_idx * 12
    
    # Binary search for tithi start time
    jd_start = jd - 1
    jd_end = jd
    tolerance = 1.0 / 1440  # 1 minute tolerance
    
    while (jd_end - jd_start) > tolerance:
        jd_mid = (jd_start + jd_end) / 2
        sun_mid = get_planet_position(jd_mid, swe.SUN)
        moon_mid = get_planet_position(jd_mid, swe.MOON)
        elongation_mid = (moon_mid['longitude'] - sun_mid['longitude']) % 360
        
        if elongation_mid < tithi_start_elongation:
            jd_start = jd_mid
        else:
            jd_end = jd_mid
    
    tithi_start_jd = jd_end
    
    # Binary search for tithi end time
    jd_start = jd
    jd_end = jd + 1
    
    while (jd_end - jd_start) > tolerance:
        jd_mid = (jd_start + jd_end) / 2
        sun_mid = get_planet_position(jd_mid, swe.SUN)
        moon_mid = get_planet_position(jd_mid, swe.MOON)
        elongation_mid = (moon_mid['longitude'] - sun_mid['longitude']) % 360
        
        if elongation_mid < tithi_end_elongation:
            jd_start = jd_mid
        else:
            jd_end = jd_mid
    
    tithi_end_jd = jd_end
    
    # Convert JD to datetime
    def jd_to_datetime(jd_val):
        cal = swe.revjul(jd_val)
        h = int(cal[3])
        m = int((cal[3] - h) * 60)
        s = int(((cal[3] - h) * 60 - m) * 60)
        return datetime(int(cal[0]), int(cal[1]), int(cal[2]), h, m, s)
    
    start_time = jd_to_datetime(tithi_start_jd)
    end_time = jd_to_datetime(tithi_end_jd)
    
    return {
        'start_date': start_time.strftime("%Y-%m-%d"),
        'start_time': start_time.strftime("%H:%M:%S"),
        'end_date': end_time.strftime("%Y-%m-%d"),
        'end_time': end_time.strftime("%H:%M:%S"),
        'duration_minutes': int((tithi_end_jd - tithi_start_jd) * 24 * 60)
    }

def calculate_nakshatra_transition_times(jd: float) -> Dict:
    """Calculate nakshatra start and end times by finding longitude boundaries"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # Current nakshatra
    moon = get_planet_position(jd, swe.MOON)
    moon_long = moon['longitude']
    nakshatra_idx = int(moon_long / (360.0 / 27.0))
    
    # Find when current nakshatra started
    nakshatra_start_long = nakshatra_idx * (360.0 / 27.0)
    nakshatra_end_long = (nakshatra_idx + 1) * (360.0 / 27.0)
    
    # Binary search for nakshatra start time
    jd_start = jd - 1
    jd_end = jd
    tolerance = 1.0 / 1440  # 1 minute tolerance
    
    while (jd_end - jd_start) > tolerance:
        jd_mid = (jd_start + jd_end) / 2
        moon_mid = get_planet_position(jd_mid, swe.MOON)
        moon_long_mid = moon_mid['longitude']
        
        if moon_long_mid < nakshatra_start_long:
            jd_start = jd_mid
        else:
            jd_end = jd_mid
    
    nakshatra_start_jd = jd_end
    
    # Binary search for nakshatra end time
    jd_start = jd
    jd_end = jd + 1
    
    while (jd_end - jd_start) > tolerance:
        jd_mid = (jd_start + jd_end) / 2
        moon_mid = get_planet_position(jd_mid, swe.MOON)
        moon_long_mid = moon_mid['longitude']
        
        if moon_long_mid < nakshatra_end_long:
            jd_start = jd_mid
        else:
            jd_end = jd_mid
    
    nakshatra_end_jd = jd_end
    
    # Convert JD to datetime
    def jd_to_datetime(jd_val):
        cal = swe.revjul(jd_val)
        h = int(cal[3])
        m = int((cal[3] - h) * 60)
        s = int(((cal[3] - h) * 60 - m) * 60)
        return datetime(int(cal[0]), int(cal[1]), int(cal[2]), h, m, s)
    
    start_time = jd_to_datetime(nakshatra_start_jd)
    end_time = jd_to_datetime(nakshatra_end_jd)
    
    return {
        'start_date': start_time.strftime("%Y-%m-%d"),
        'start_time': start_time.strftime("%H:%M:%S"),
        'end_date': end_time.strftime("%Y-%m-%d"),
        'end_time': end_time.strftime("%H:%M:%S"),
        'duration_minutes': int((nakshatra_end_jd - nakshatra_start_jd) * 24 * 60)
    }

# ==================== Vedic Calculations ====================

def calculate_tithi(jd: float) -> Dict:
    """Calculate Tithi with start and end times"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    sun = get_planet_position(jd, swe.SUN)
    moon = get_planet_position(jd, swe.MOON)

    elongation = (moon['longitude'] - sun['longitude']) % 360
    tithi_idx = int(elongation / 12) + 1
    tithi_fraction = (elongation % 12) / 12

    paksha = 'Shukla' if tithi_idx <= 15 else 'Krishna'
    day_in_paksha = tithi_idx if tithi_idx <= 15 else tithi_idx - 15

    tithi_name = f" {TITHI_NAMES[paksha][(day_in_paksha - 1) % 15]}"

    # Get tithi transition times
    try:
        transition_times = calculate_tithi_transition_times(jd)
        start_date = transition_times['start_date']
        start_time = transition_times['start_time']
        end_date = transition_times['end_date']
        end_time = transition_times['end_time']
        duration = transition_times['duration_minutes']
    except:
        start_date = 'N/A'
        start_time = 'N/A'
        end_date = 'N/A'
        end_time = 'N/A'
        duration = 0

    return {
        'number': tithi_idx,
        'name': tithi_name,
        'paksha': paksha,
        'day': day_in_paksha,
        'fraction': round(tithi_fraction, 4),
        'start_date': start_date,
        'start_time': start_time,
        'end_date': end_date,
        'end_time': end_time,
        'duration_minutes': duration
    }

def calculate_nakshatra(jd: float) -> Dict:
    """Calculate Nakshatra with start and end times"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    moon = get_planet_position(jd, swe.MOON)
    moon_long = moon['longitude']

    nakshatra_num = int(moon_long / (360.0 / 27.0))
    fraction = (moon_long % (360.0 / 27.0)) / (360.0 / 27.0)
    pada = int(fraction * 4) + 1

    # Get nakshatra transition times
    try:
        transition_times = calculate_nakshatra_transition_times(jd)
        start_date = transition_times['start_date']
        start_time = transition_times['start_time']
        end_date = transition_times['end_date']
        end_time = transition_times['end_time']
        duration = transition_times['duration_minutes']
    except:
        start_date = 'N/A'
        start_time = 'N/A'
        end_date = 'N/A'
        end_time = 'N/A'
        duration = 0

    return {
        'number': nakshatra_num + 1,
        'name': NAKSHATRA_NAMES[nakshatra_num],
        'lord': NAKSHATRA_LORDS[nakshatra_num],
        'pada': pada,
        'fraction': round(fraction, 4),
        'start_date': start_date,
        'start_time': start_time,
        'end_date': end_date,
        'end_time': end_time,
        'duration_minutes': duration
    }

def calculate_masa(jd: float) -> Dict:
    """Calculate Masa"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    sun = get_planet_position(jd, swe.SUN)
    rasi_num = int(sun['longitude'] / 30)
    masa_num = (rasi_num + 1) % 12

    return {
        'number': masa_num + 1,
        'name': MASA_NAMES[masa_num]
    }

def calculate_vaara(jd: float) -> Dict:
    """Calculate Vaara (Day of week)"""
    day_num = int((jd + 1.5) % 7)
    return {
        'number': day_num + 1,
        'name': VAARA_NAMES[day_num]
    }

def calculate_yoga_transition_times(jd: float) -> Dict:
    """Calculate yoga start and end times by finding longitude sum boundaries"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # Current yoga
    sun = get_planet_position(jd, swe.SUN)
    moon = get_planet_position(jd, swe.MOON)
    yoga_sum = (sun['longitude'] + moon['longitude']) % 360
    yoga_idx = int(yoga_sum / (360.0 / 27.0))
    
    # Find when current yoga started (previous boundary)
    yoga_start_sum = yoga_idx * (360.0 / 27.0)
    yoga_end_sum = (yoga_idx + 1) * (360.0 / 27.0)
    
    # Binary search for yoga start time
    jd_start = jd - 1
    jd_end = jd
    tolerance = 1.0 / 1440  # 1 minute tolerance
    
    while (jd_end - jd_start) > tolerance:
        jd_mid = (jd_start + jd_end) / 2
        sun_mid = get_planet_position(jd_mid, swe.SUN)
        moon_mid = get_planet_position(jd_mid, swe.MOON)
        yoga_sum_mid = (sun_mid['longitude'] + moon_mid['longitude']) % 360
        
        if yoga_sum_mid < yoga_start_sum:
            jd_start = jd_mid
        else:
            jd_end = jd_mid
    
    yoga_start_jd = jd_end
    
    # Binary search for yoga end time
    jd_start = jd
    jd_end = jd + 1
    
    while (jd_end - jd_start) > tolerance:
        jd_mid = (jd_start + jd_end) / 2
        sun_mid = get_planet_position(jd_mid, swe.SUN)
        moon_mid = get_planet_position(jd_mid, swe.MOON)
        yoga_sum_mid = (sun_mid['longitude'] + moon_mid['longitude']) % 360
        
        if yoga_sum_mid < yoga_end_sum:
            jd_start = jd_mid
        else:
            jd_end = jd_mid
    
    yoga_end_jd = jd_end
    
    # Convert JD to datetime
    def jd_to_datetime(jd_val):
        cal = swe.revjul(jd_val)
        h = int(cal[3])
        m = int((cal[3] - h) * 60)
        s = int(((cal[3] - h) * 60 - m) * 60)
        return datetime(int(cal[0]), int(cal[1]), int(cal[2]), h, m, s)
    
    start_time = jd_to_datetime(yoga_start_jd)
    end_time = jd_to_datetime(yoga_end_jd)
    
    return {
        'start_date': start_time.strftime("%Y-%m-%d"),
        'start_time': start_time.strftime("%H:%M:%S"),
        'end_date': end_time.strftime("%Y-%m-%d"),
        'end_time': end_time.strftime("%H:%M:%S"),
        'duration_minutes': int((yoga_end_jd - yoga_start_jd) * 24 * 60)
    }

def calculate_yoga(jd: float) -> Dict:
    """Calculate Yoga with start and end times"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    sun = get_planet_position(jd, swe.SUN)
    moon = get_planet_position(jd, swe.MOON)

    yoga_sum = (sun['longitude'] + moon['longitude']) % 360
    yoga_num = int(yoga_sum / (360.0 / 27.0))
    fraction = (yoga_sum % (360.0 / 27.0)) / (360.0 / 27.0)

    # Get yoga transition times
    try:
        transition_times = calculate_yoga_transition_times(jd)
        start_date = transition_times['start_date']
        start_time = transition_times['start_time']
        end_date = transition_times['end_date']
        end_time = transition_times['end_time']
        duration = transition_times['duration_minutes']
    except:
        start_date = 'N/A'
        start_time = 'N/A'
        end_date = 'N/A'
        end_time = 'N/A'
        duration = 0

    return {
        'number': yoga_num + 1,
        'name': YOGA_NAMES[yoga_num],
        'fraction': round(fraction, 4),
        'start_date': start_date,
        'start_time': start_time,
        'end_date': end_date,
        'end_time': end_time,
        'duration_minutes': duration
    }

def calculate_karana(jd: float) -> Dict:
    """Calculate Karana"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    sun = get_planet_position(jd, swe.SUN)
    moon = get_planet_position(jd, swe.MOON)

    elongation = (moon['longitude'] - sun['longitude']) % 360
    karana_num = int(elongation / 6)
    karana_idx = karana_num % 11

    return {
        'number': karana_num + 1,
        'name': KARANA_NAMES[min(karana_idx, 10)]
    }

def calculate_karana_transition_times(jd: float) -> Dict:
    """Calculate karana start and end times by finding elongation boundaries"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # Current karana
    sun = get_planet_position(jd, swe.SUN)
    moon = get_planet_position(jd, swe.MOON)
    elongation = (moon['longitude'] - sun['longitude']) % 360
    karana_num = int(elongation / 6)
    
    # Find when current karana started (previous 6-degree boundary)
    karana_start_elongation = karana_num * 6
    karana_end_elongation = (karana_num + 1) * 6
    
    # Binary search for karana start time
    jd_start = jd - 1
    jd_end = jd
    tolerance = 1.0 / 1440  # 1 minute tolerance
    
    while (jd_end - jd_start) > tolerance:
        jd_mid = (jd_start + jd_end) / 2
        sun_mid = get_planet_position(jd_mid, swe.SUN)
        moon_mid = get_planet_position(jd_mid, swe.MOON)
        elongation_mid = (moon_mid['longitude'] - sun_mid['longitude']) % 360
        
        if elongation_mid < karana_start_elongation:
            jd_start = jd_mid
        else:
            jd_end = jd_mid
    
    karana_start_jd = jd_end
    
    # Binary search for karana end time
    jd_start = jd
    jd_end = jd + 1
    
    while (jd_end - jd_start) > tolerance:
        jd_mid = (jd_start + jd_end) / 2
        sun_mid = get_planet_position(jd_mid, swe.SUN)
        moon_mid = get_planet_position(jd_mid, swe.MOON)
        elongation_mid = (moon_mid['longitude'] - sun_mid['longitude']) % 360
        
        if elongation_mid < karana_end_elongation:
            jd_start = jd_mid
        else:
            jd_end = jd_mid
    
    karana_end_jd = jd_end
    
    # Convert JD to datetime
    def jd_to_datetime(jd_val):
        cal = swe.revjul(jd_val)
        h = int(cal[3])
        m = int((cal[3] - h) * 60)
        s = int(((cal[3] - h) * 60 - m) * 60)
        return datetime(int(cal[0]), int(cal[1]), int(cal[2]), h, m, s)
    
    start_time = jd_to_datetime(karana_start_jd)
    end_time = jd_to_datetime(karana_end_jd)
    
    return {
        'start_date': start_time.strftime("%Y-%m-%d"),
        'start_time': start_time.strftime("%H:%M:%S"),
        'end_date': end_time.strftime("%Y-%m-%d"),
        'end_time': end_time.strftime("%H:%M:%S"),
        'duration_minutes': int((karana_end_jd - karana_start_jd) * 24 * 60)
    }

def calculate_karana_with_transitions(jd: float) -> Dict:
    """Calculate Karana with start and end times"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    sun = get_planet_position(jd, swe.SUN)
    moon = get_planet_position(jd, swe.MOON)

    elongation = (moon['longitude'] - sun['longitude']) % 360
    karana_num = int(elongation / 6)
    karana_idx = karana_num % 11
    fraction = (elongation % 6) / 6

    # Get karana transition times
    try:
        transition_times = calculate_karana_transition_times(jd)
        start_date = transition_times['start_date']
        start_time = transition_times['start_time']
        end_date = transition_times['end_date']
        end_time = transition_times['end_time']
        duration = transition_times['duration_minutes']
    except:
        start_date = 'N/A'
        start_time = 'N/A'
        end_date = 'N/A'
        end_time = 'N/A'
        duration = 0

    return {
        'number': karana_num + 1,
        'name': KARANA_NAMES[min(karana_idx, 10)],
        'fraction': round(fraction, 4),
        'start_date': start_date,
        'start_time': start_time,
        'end_date': end_date,
        'end_time': end_time,
        'duration_minutes': duration
    }

# ==================== Muhurta Calculations ====================

def calculate_brahma_muhurta(jd: float, lat: float, lon: float) -> Dict:
    """
    Calculate Brahma Muhurta using Swiss Ephemeris sunrise/sunset times.

    Approach:
    - Use `calculate_sunrise_sunset` (which calls Swiss Ephemeris) to get
      the exact sunrise for `jd` and the previous day's sunset (jd-1).
    - Use the traditional definition: Brahma Muhurta = 48 minutes before
      sunrise (2 ghatikas). Returning start/end, datetimes and duration.

    Parameters:
    - `jd`: Julian Day for the date for which to compute Brahma Muhurta
    - `lat`, `lon`: geographic coordinates required by Swiss Ephemeris
    """
    # Get today's sunrise/sunset via Swiss Ephemeris helper
    sun_times = calculate_sunrise_sunset(jd, lat, lon)
    sunrise = sun_times.get('sunrise')
    sunset = sun_times.get('sunset')

    # Get previous day's sunset (jd - 1)
    prev_sun_times = calculate_sunrise_sunset(jd - 1, lat, lon)
    prev_sunset = prev_sun_times.get('sunset')

    # Fallback if Swiss Ephemeris failed to produce times
    if sunrise is None:
        # As a safe fallback, use current system approximation (unlikely)
        now = datetime.now()
        sunrise = now.replace(hour=6, minute=0, second=0)
    if prev_sunset is None:
        # If previous sunset not available, estimate as 12 hours before sunrise
        prev_sunset = sunrise - timedelta(hours=12)

    # Traditional rule requested: start = sunrise - 96 minutes, end = sunrise - 48 minutes
    brahma_start = sunrise - timedelta(minutes=96)
    brahma_end = sunrise - timedelta(minutes=48)
    brahma_duration_minutes = int((brahma_end - brahma_start).total_seconds() / 60)

    return {
        'name': 'Brahma Muhurta',
        'meaning': '48 minutes before sunrise (2 ghatikas) - Best for meditation',
        'start': brahma_start.strftime("%H:%M:%S"),
        'end': brahma_end.strftime("%H:%M:%S"),
        'start_time': brahma_start,
        'end_time': brahma_end,
        'duration_minutes': brahma_duration_minutes,
        'auspiciousness': 'Most Auspicious',
        'sunrise_used': sunrise.strftime("%Y-%m-%d %H:%M:%S"),
        'prev_sunset_used': prev_sunset.strftime("%Y-%m-%d %H:%M:%S")
    }

def calculate_amruthakala(sunrise: datetime, sunset: datetime, vaara: int, amrita_kala_index: int = 4) -> Dict:
    """
    Calculate Amruthakala by dividing daytime (sunrise->sunset) into 8 equal
    kalas and returning the Nth segment as Amruthakala.

    Parameters:
    - `sunrise`, `sunset`: datetimes for the day
    - `vaara`: day-of-week index (1..7) used for annotation
    - `amrita_kala_index`: which kala (1..8) to treat as Amruthakala (default 4)

    Returns a dict with start/end, duration, kala index and kala length.
    """
    # Ensure sunrise < sunset
    if sunrise is None or sunset is None or sunset <= sunrise:
        # invalid inputs; return a safe default
        return {
            'name': 'Amruthakala',
            'meaning': 'N/A - could not compute sunrise/sunset',
            'start': 'N/A',
            'end': 'N/A',
            'start_time': None,
            'end_time': None,
            'duration_minutes': 0,
            'auspiciousness': 'Unknown',
            'vaara': VAARA_NAMES[vaara - 1] if 1 <= vaara <= 7 else 'Unknown',
            'kala_index': amrita_kala_index,
            'kala_length_minutes': 0
        }

    # Compute day duration in minutes and kala length
    day_minutes = (sunset - sunrise).total_seconds() / 60.0
    kala_length_minutes = day_minutes / 8.0

    # Clamp requested index to 1..8
    idx = max(1, min(8, int(amrita_kala_index)))

    amrutha_start = sunrise + timedelta(minutes=kala_length_minutes * (idx - 1))
    amrutha_end = sunrise + timedelta(minutes=kala_length_minutes * idx)

    # Safety clamp within sunrise/sunset
    if amrutha_start < sunrise:
        amrutha_start = sunrise
    if amrutha_end > sunset:
        amrutha_end = sunset

    duration_minutes = int((amrutha_end - amrutha_start).total_seconds() / 60)

    return {
        'name': 'Amruthakala',
        'meaning': f'Amritakala (Kala #{idx}) - Auspicious period',
        'start': amrutha_start.strftime("%H:%M:%S"),
        'end': amrutha_end.strftime("%H:%M:%S"),
        'start_time': amrutha_start,
        'end_time': amrutha_end,
        'duration_minutes': duration_minutes,
        'auspiciousness': 'Very Auspicious',
        'vaara': VAARA_NAMES[vaara - 1] if 1 <= vaara <= 7 else 'Unknown',
        'kala_index': idx,
        'kala_length_minutes': round(kala_length_minutes, 2)
    }

def calculate_rahukalam(sunrise: datetime, sunset: datetime, vaara: int) -> Dict:
    """
    Rahukalam: Inauspicious period lasting 1.5 hours (90 minutes)
    Time depends on the day of week
    """
    # Divide daytime (sunrise->sunset) into 8 equal kalas
    # Rahukalam index table (0-based index for the 8 slots) by weekday
    # Sunday..Saturday => [6,0,7,5,4,3,2]
    rahukalam_table = [6, 0, 7, 5, 4, 3, 2]

    # Safety checks
    if sunrise is None or sunset is None or sunset <= sunrise:
        return {
            'name': 'Rahukalam',
            'meaning': 'N/A - could not compute sunrise/sunset',
            'start': 'N/A',
            'end': 'N/A',
            'start_time': None,
            'end_time': None,
            'duration_minutes': 0,
            'auspiciousness': 'Unknown',
            'vaara': VAARA_NAMES[vaara - 1] if 1 <= vaara <= 7 else 'Unknown'
        }

    day_seconds = (sunset - sunrise).total_seconds()
    kala_seconds = day_seconds / 8.0

    # Convert vaara (1..7) to 0-based and clamp
    idx = max(0, min(6, vaara - 1))
    slot_index = rahukalam_table[idx]

    rahukalam_start = sunrise + timedelta(seconds=kala_seconds * slot_index)
    rahukalam_end = rahukalam_start + timedelta(seconds=kala_seconds)
    if rahukalam_end > sunset:
        rahukalam_end = sunset

    return {
        'name': 'Rahukalam',
        'meaning': 'Inauspicious time - Avoid important activities',
        'start': rahukalam_start.strftime("%H:%M:%S"),
        'end': rahukalam_end.strftime("%H:%M:%S"),
        'start_time': rahukalam_start,
        'end_time': rahukalam_end,
        'duration_minutes': int((rahukalam_end - rahukalam_start).total_seconds() / 60),
        'auspiciousness': 'Inauspicious',
        'vaara': VAARA_NAMES[idx],
        'slot_index': slot_index,
        'kala_length_minutes': round(kala_seconds / 60.0, 2)
    }

def calculate_yamagandam(sunrise: datetime, sunset: datetime, vaara: int) -> Dict:
    """
    Yamagandam (Yama Ghantaka): Inauspicious period lasting 48 minutes
    Time depends on the day of week
    """
    # Use daytime/8 segmentation like Rahukalam.
    # Yamagandam index table (0-based slots) by weekday Sunday..Saturday
    # Table: [1,6,4,3,2,5,0]
    yamagandam_table = [1, 6, 4, 3, 2, 5, 0]

    # Safety checks
    if sunrise is None or sunset is None or sunset <= sunrise:
        return {
            'name': 'Yamagandam',
            'meaning': 'N/A - could not compute sunrise/sunset',
            'start': 'N/A',
            'end': 'N/A',
            'start_time': None,
            'end_time': None,
            'duration_minutes': 0,
            'auspiciousness': 'Unknown',
            'vaara': VAARA_NAMES[vaara - 1] if 1 <= vaara <= 7 else 'Unknown'
        }

    day_seconds = (sunset - sunrise).total_seconds()
    kala_seconds = day_seconds / 8.0

    # Convert vaara to 0-based index and clamp
    idx = max(0, min(6, vaara - 1))
    slot_index = yamagandam_table[idx]

    yamagandam_start = sunrise + timedelta(seconds=kala_seconds * slot_index)
    yamagandam_end = yamagandam_start + timedelta(seconds=kala_seconds)
    if yamagandam_end > sunset:
        yamagandam_end = sunset

    duration_minutes = int((yamagandam_end - yamagandam_start).total_seconds() / 60)

    return {
        'name': 'Yamagandam',
        'meaning': 'Time of death-god - Inauspicious for important deeds',
        'start': yamagandam_start.strftime("%H:%M:%S"),
        'end': yamagandam_end.strftime("%H:%M:%S"),
        'start_time': yamagandam_start,
        'end_time': yamagandam_end,
        'duration_minutes': duration_minutes,
        'auspiciousness': 'Inauspicious',
        'vaara': VAARA_NAMES[idx],
        'slot_index': slot_index,
        'kala_length_minutes': round(kala_seconds / 60.0, 2)
    }

def calculate_varjyam(jd: float, k_table: Optional[Dict[int, int]] = None) -> Dict:
    """
    Calculate Varjyam for the nakshatra that covers the given Julian Day `jd`.

    Algorithm:
    - Use Swiss Ephemeris (via existing helpers) to find the current nakshatra
      for `jd` and its precise start and end times (`calculate_nakshatra` and
      `calculate_nakshatra_transition_times`).
    - If the nakshatra is in the "no Varjyam" list, return a clear N/A.
    - Otherwise compute the varjyam start as:
          varjyam_start = nakshatra_start + k * (nakshatra_span / 6)
      where `k` is a nakshatra-specific index provided in `k_table`.
    - Varjyam duration is fixed at 96 minutes; clamp end to nakshatra end
      if it exceeds the nakshatra span.

    Parameters:
    - `jd`: Julian Day at which to evaluate the nakshatra
    - `k_table`: optional mapping {nakshatra_index: k}. If not provided,
      a conservative default (k=0 for all nakshatras that allow Varjyam)
      is used. Nakshatras that do not have Varjyam are set to `None`.
    """
    # Determine current nakshatra number and transition times
    try:
        nak = calculate_nakshatra(jd)
        nak_idx = nak['number'] - 1  # 0-based
        nak_name = nak['name']
    except Exception:
        return {
            'name': 'Varjyam',
            'meaning': 'N/A - could not determine nakshatra',
            'start': 'N/A',
            'end': 'N/A',
            'start_time': None,
            'end_time': None,
            'duration_minutes': 0,
            'auspiciousness': 'Unknown'
        }

    # Nakshatras that traditionally do NOT have Varjyam (0-based indices)
    no_varjyam_indices = {0, 9, 17, 18, 19, 20}  # Ashwini, Magha, Jyeshtha, Mula, PurvaAsh, UttaraAsh

    if nak_idx in no_varjyam_indices:
        return {
            'name': 'Varjyam',
            'meaning': f'No Varjyam for nakshatra {nak_name}',
            'start': 'N/A',
            'end': 'N/A',
            'start_time': None,
            'end_time': None,
            'duration_minutes': 0,
            'auspiciousness': 'N/A',
            'nakshatra': nak_name,
            'nakshatra_index': nak_idx
        }

    # Default k_table: conservative default uses k=0 for allowed nakshatras
    if k_table is None:
        k_table = {i: 0 for i in range(27)}
        for ni in no_varjyam_indices:
            k_table[ni] = None

    k = k_table.get(nak_idx)
    if k is None:
        return {
            'name': 'Varjyam',
            'meaning': f'No Varjyam for nakshatra {nak_name}',
            'start': 'N/A',
            'end': 'N/A',
            'start_time': None,
            'end_time': None,
            'duration_minutes': 0,
            'auspiciousness': 'N/A',
            'nakshatra': nak_name,
            'nakshatra_index': nak_idx
        }

    # Get precise nakshatra start/end times
    try:
        trans = calculate_nakshatra_transition_times(jd)
        nak_start_str = trans['start_time']
        nak_end_str = trans['end_time']
        # convert strings to datetime if needed (they are str in function)
        if isinstance(nak_start_str, str):
            nak_start = datetime.strptime(trans['start_date'] + ' ' + trans['start_time'], "%Y-%m-%d %H:%M:%S")
            nak_end = datetime.strptime(trans['end_date'] + ' ' + trans['end_time'], "%Y-%m-%d %H:%M:%S")
        else:
            nak_start = trans.get('start_time')
            nak_end = trans.get('end_time')
    except Exception:
        return {
            'name': 'Varjyam',
            'meaning': 'N/A - could not compute nakshatra transition times',
            'start': 'N/A',
            'end': 'N/A',
            'start_time': None,
            'end_time': None,
            'duration_minutes': 0,
            'auspiciousness': 'Unknown',
            'nakshatra': nak_name,
            'nakshatra_index': nak_idx
        }

    nak_span = (nak_end - nak_start).total_seconds()
    # Divide nakshatra span into 6 parts as per algorithm
    part_seconds = nak_span / 6.0 if nak_span > 0 else 0

    varjyam_start = nak_start + timedelta(seconds=part_seconds * k)
    varjyam_end = varjyam_start + timedelta(minutes=96)

    # Clamp varjyam_end to nakshatra end if it exceeds
    if varjyam_end > nak_end:
        varjyam_end = nak_end

    duration_minutes = int((varjyam_end - varjyam_start).total_seconds() / 60)

    return {
        'name': 'Varjyam',
        'meaning': f'Varjyam for nakshatra {nak_name} (k={k})',
        'start': varjyam_start.strftime("%H:%M:%S"),
        'end': varjyam_end.strftime("%H:%M:%S"),
        'start_time': varjyam_start,
        'end_time': varjyam_end,
        'duration_minutes': duration_minutes,
        'auspiciousness': 'Inauspicious',
        'nakshatra': nak_name,
        'nakshatra_index': nak_idx,
        'k_used': k,
        'nakshatra_start': nak_start.strftime("%Y-%m-%d %H:%M:%S"),
        'nakshatra_end': nak_end.strftime("%Y-%m-%d %H:%M:%S"),
        'part_seconds': part_seconds
    }

def calculate_durmuhurta(sunrise: datetime, sunset: datetime, vaara: int) -> Dict:
    """
    Durmuhurta (Durmuhurtham) using traditional weekday offsets based on
    local sunrise. Returns one or two 48-minute intervals depending on weekday.

    Rules implemented (minutes after sunrise):
    - Sunday, Monday, Wednesday, Thursday, Friday:
        1) Start = +2:40 (160)  End = +3:28 (208)
        2) Start = +7:12 (432)  End = +8:00 (480)
    - Tuesday: single interval Start = +5:36 (336) End = +6:24 (384)
    - Saturday: single interval Start = +4:25 (265) End = +5:13 (313)

    Note: Durations are 48 minutes each (per provided specification).
    """
    # Safety check
    if sunrise is None:
        return {
            'name': 'Durmuhurta',
            'meaning': 'N/A - sunrise not available',
            'periods': [],
            'auspiciousness': 'Unknown'
        }

    # Map Vaara (1=Sunday .. 7=Saturday) to rules
    # We'll produce periods as list of dicts with 48-minute durations
    periods = []

    # Helper to append a period given start minute offset
    def add_period(offset_minutes: int, number: int):
        start = sunrise + timedelta(minutes=offset_minutes)
        end = start + timedelta(minutes=48)
        # Clamp end to sunset
        if end > sunset:
            end = sunset
        periods.append({
            'number': number,
            'start': start.strftime("%H:%M:%S"),
            'end': end.strftime("%H:%M:%S"),
            'start_time': start,
            'end_time': end,
            'duration_minutes': int((end - start).total_seconds() / 60)
        })

    # Vaara mapping: 1=Sunday,2=Monday,...7=Saturday
    if vaara in (1, 2, 4, 5, 6):
        # Sunday(1), Monday(2), Wednesday(4), Thursday(5), Friday(6)
        # First Durmuhurta: +160 to +208
        add_period(160, 1)
        # Second Durmuhurta: +432 to +480
        add_period(432, 2)
    elif vaara == 3:
        # Tuesday: single interval +336 to +384
        add_period(336, 1)
    elif vaara == 7:
        # Saturday: single interval +265 to +313
        add_period(265, 1)
    else:
        # Unexpected vaara; fallback to two intervals similar to most days
        add_period(160, 1)
        add_period(432, 2)

    return {
        'name': 'Durmuhurta',
        'meaning': 'Inauspicious period - Avoid new ventures',
        'periods': periods,
        'auspiciousness': 'Inauspicious'
    }

def calculate_vijaya_muhurta(sunrise: datetime, sunset: datetime) -> Dict:
    """
    Vijaya Muhurta using day/15 division.

    Algorithm:
    - Divide daylight (sunrise->sunset) into 15 equal muhurtas.
    - Vijaya is the 11th muhurtam: start = sunrise + 10*(day/15), end = sunrise + 11*(day/15).
    """
    if sunrise is None or sunset is None or sunset <= sunrise:
        return {
            'name': 'Vijaya Muhurta',
            'meaning': 'N/A - could not compute sunrise/sunset',
            'start': 'N/A',
            'end': 'N/A',
            'start_time': None,
            'end_time': None,
            'duration_minutes': 0,
            'auspiciousness': 'Unknown',
            'use_for': None
        }

    day_seconds = (sunset - sunrise).total_seconds()
    muhurt_seconds = day_seconds / 15.0

    vijaya_start = sunrise + timedelta(seconds=muhurt_seconds * 10)
    vijaya_end = sunrise + timedelta(seconds=muhurt_seconds * 11)

    # Clamp within sunrise/sunset
    if vijaya_start < sunrise:
        vijaya_start = sunrise
    if vijaya_end > sunset:
        vijaya_end = sunset

    duration_minutes = int((vijaya_end - vijaya_start).total_seconds() / 60)

    return {
        'name': 'Vijaya Muhurta',
        'meaning': 'Victory time - Excellent for auspicious activities',
        'start': vijaya_start.strftime("%H:%M:%S"),
        'end': vijaya_end.strftime("%H:%M:%S"),
        'start_time': vijaya_start,
        'end_time': vijaya_end,
        'duration_minutes': duration_minutes,
        'auspiciousness': 'Highly Auspicious',
        'use_for': 'Starting new projects, travel, business, marriage',
        'muhurt_seconds': muhurt_seconds
    }

# ==================== Complete Panchanga + Muhurta ====================

def calculate_complete_panchanga(location: Dict, dt: Optional[datetime] = None) -> Dict:
    """Calculate complete Panchanga with all Muhurta timings"""

    if dt is None:
        dt = datetime.now()

    # Pass location timezone (if available) to get accurate UT Julian Day
    tzname = location.get('timezone') if location and isinstance(location, dict) else None
    jd = get_julian_day(dt, tzname)

    # Basic Vedic elements
    tithi = calculate_tithi(jd)
    nakshatra = calculate_nakshatra(jd)
    masa = calculate_masa(jd)
    vaara = calculate_vaara(jd)
    yoga = calculate_yoga(jd)
    karana = calculate_karana_with_transitions(jd)

    # Sunrise/Sunset
    sun_times = calculate_sunrise_sunset(jd, location['latitude'], location['longitude'])

    if sun_times['sunrise'] is None:
        return {'error': 'Could not calculate sunrise/sunset'}

    sunrise = sun_times['sunrise']
    sunset = sun_times['sunset']

    # Calculate all Muhurta timings (Brahma Muhurta uses Swiss Ephemeris directly)
    brahma_muhurta = calculate_brahma_muhurta(jd, location['latitude'], location['longitude'])
    amruthakala = calculate_amruthakala(sunrise, sunset, vaara['number'])
    rahukalam = calculate_rahukalam(sunrise, sunset, vaara['number'])
    yamagandam = calculate_yamagandam(sunrise, sunset, vaara['number'])
    varjyam = calculate_varjyam(jd)
    durmuhurta = calculate_durmuhurta(sunrise, sunset, vaara['number'])
    vijaya_muhurta = calculate_vijaya_muhurta(sunrise, sunset)

    # Moonrise / Moonset
    moon_times = calculate_moonrise_moonset(jd, location['latitude'], location['longitude'])
    moonrise = moon_times.get('moonrise')
    moonset = moon_times.get('moonset')

    complete_panchanga = {
        'date': dt.strftime("%Y-%m-%d"),
        'time': dt.strftime("%H:%M:%S"),
        'location': {
            'city': location.get('city', 'Unknown'),
            'country': location.get('country', 'Unknown'),
            'latitude': location['latitude'],
            'longitude': location['longitude'],
            'timezone': location.get('timezone', 'UTC')
        },

        # Vedic Calendar Elements
        'vedic_elements': {
            'tithi': tithi,
            'nakshatra': nakshatra,
            'masa': masa,
            'vaara': vaara,
            'yoga': yoga,
            'karana': karana
        },

        # Day Times
        'day_times': {
            'sunrise': sun_times['sunrise_str'],
            'sunset': sun_times['sunset_str'],
            'sunrise_datetime': sunrise.isoformat(),
            'sunset_datetime': sunset.isoformat(),
            'moonrise': moon_times.get('moonrise_str'),
            'moonset': moon_times.get('moonset_str'),
            'moonrise_datetime': moonrise.isoformat() if moonrise else None,
            'moonset_datetime': moonset.isoformat() if moonset else None
        },

        # Muhurta Timings
        'muhurta_timings': {
            'brahma_muhurta': brahma_muhurta,
            'amruthakala': amruthakala,
            'rahukalam': rahukalam,
            'yamagandam': yamagandam,
            'varjyam': varjyam,
            'durmuhurta': durmuhurta,
            'vijaya_muhurta': vijaya_muhurta
        },

        # Auspiciousness Summary
        'auspiciousness_summary': {
            'best_times': [
                {'name': 'Brahma Muhurta', 'time': brahma_muhurta['start'] + ' - ' + brahma_muhurta['end']},
                {'name': 'Amruthakala', 'time': amruthakala['start'] + ' - ' + amruthakala['end']},
                {'name': 'Vijaya Muhurta', 'time': vijaya_muhurta['start'] + ' - ' + vijaya_muhurta['end']}
            ],
            'avoid_times': [
                {'name': 'Rahukalam', 'time': rahukalam['start'] + ' - ' + rahukalam['end']},
                {'name': 'Yamagandam', 'time': yamagandam['start'] + ' - ' + yamagandam['end']},
                {'name': 'Varjyam', 'time': varjyam['start'] + ' - ' + varjyam['end']},
                {'name': 'Durmuhurta', 'time': 'Multiple periods'}
            ]
        }
    }

    return complete_panchanga

def print_complete_panchanga(panchanga: Dict):
    """Pretty print complete Panchanga with Muhurta"""

    print("\n" + "="*80)
    print(f"COMPLETE VEDIC CALENDAR & MUHURTA TIMINGS")
    print(f"Date: {panchanga['date']} {panchanga['time']}")
    print(f"Location: {panchanga['location']['city']}, {panchanga['location']['country']}")
    print("="*80)

    # Vedic Elements
    print("\n[VEDIC CALENDAR ELEMENTS]:")
    print("-" * 80)

    v = panchanga['vedic_elements']
    print(f"Tithi:     {v['tithi']['paksha']:12} {v['tithi']['name']:20} (#{v['tithi']['number']}/30)")
    if v['tithi'].get('start_date') and v['tithi']['start_date'] != 'N/A':
        print(f"           Start: {v['tithi']['start_date']} {v['tithi']['start_time']}")
        print(f"           End:   {v['tithi']['end_date']} {v['tithi']['end_time']}")
        print(f"           Duration: {v['tithi']['duration_minutes']} minutes")
    print(f"Nakshatra: {v['nakshatra']['name']:20} Pada {v['nakshatra']['pada']} | Lord: {v['nakshatra']['lord']}")
    if v['nakshatra'].get('start_date') and v['nakshatra']['start_date'] != 'N/A':
        print(f"           Start: {v['nakshatra']['start_date']} {v['nakshatra']['start_time']}")
        print(f"           End:   {v['nakshatra']['end_date']} {v['nakshatra']['end_time']}")
        print(f"           Duration: {v['nakshatra']['duration_minutes']} minutes")
    print(f"Masa:      {v['masa']['name']:20} (#{v['masa']['number']}/12)")
    print(f"Vaara:     {v['vaara']['name']:20}")
    print(f"Yoga:      {v['yoga']['name']:20} (#{v['yoga']['number']}/27)")
    if v['yoga'].get('start_date') and v['yoga']['start_date'] != 'N/A':
        print(f"           Start: {v['yoga']['start_date']} {v['yoga']['start_time']}")
        print(f"           End:   {v['yoga']['end_date']} {v['yoga']['end_time']}")
        print(f"           Duration: {v['yoga']['duration_minutes']} minutes")
    print(f"Karana:    {v['karana']['name']:20} (#{v['karana']['number']})")

    # Day Times
    print("\n[DAY TIMES]:")
    print("-" * 80)
    print(f"Sunrise:   {panchanga['day_times']['sunrise']}")
    print(f"Sunset:    {panchanga['day_times']['sunset']}")
    # Moon times
    if panchanga['day_times'].get('moonrise'):
        print(f"Moonrise:  {panchanga['day_times']['moonrise']}")
    else:
        print(f"Moonrise:  N/A")
    if panchanga['day_times'].get('moonset'):
        print(f"Moonset:   {panchanga['day_times']['moonset']}")
    else:
        print(f"Moonset:   N/A")

    # Auspicious Muhurtas
    m = panchanga['muhurta_timings']
    print("\n[AUSPICIOUS MUHURTAS]:")
    print("-" * 80)
    print(f"Brahma Muhurta:   {m['brahma_muhurta']['start']} - {m['brahma_muhurta']['end']}")
    print(f"  {m['brahma_muhurta']['meaning']}")
    print(f"Amruthakala:      {m['amruthakala']['start']} - {m['amruthakala']['end']}")
    print(f"  {m['amruthakala']['meaning']}")
    print(f"Vijaya Muhurta:   {m['vijaya_muhurta']['start']} - {m['vijaya_muhurta']['end']}")
    print(f"  {m['vijaya_muhurta']['meaning']}")

    # Inauspicious Times
    print("\n[INAUSPICIOUS TIMES (Avoid)]:")
    print("-" * 80)
    print(f"Rahukalam:        {m['rahukalam']['start']} - {m['rahukalam']['end']} ({m['rahukalam']['duration_minutes']} min)")
    print(f"  {m['rahukalam']['meaning']}")
    print(f"Yamagandam:       {m['yamagandam']['start']} - {m['yamagandam']['end']} ({m['yamagandam']['duration_minutes']} min)")
    print(f"  {m['yamagandam']['meaning']}")
    print(f"Varjyam:          {m['varjyam']['start']} - {m['varjyam']['end']} ({m['varjyam']['duration_minutes']} min)")
    print(f"  {m['varjyam']['meaning']}")
    # Durmuhurta: print 0/1/2 periods as available
    d_periods = m['durmuhurta'].get('periods', [])
    if not d_periods:
        print(f"Durmuhurta:       N/A")
    elif len(d_periods) == 1:
        print(f"Durmuhurta:       1 period ({d_periods[0]['duration_minutes']} minutes)")
        print(f"  Period 1: {d_periods[0]['start']} - {d_periods[0]['end']}")
    else:
        # print all available periods
        print(f"Durmuhurta:       {len(d_periods)} periods")
        for p in d_periods:
            print(f"  Period {p['number']}: {p['start']} - {p['end']}")

    print("\n" + "="*80)

# ==================== Main Program ====================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("COMPREHENSIVE VEDIC CALENDAR WITH MUHURTA TIMINGS")
    print("="*80)

    # Detect location (default) but allow user to enter a location name
    location = detect_user_location()

    if location:
        tz_display = location.get('timezone')
        # For tzinfo objects show offset, for names show name
        if tz_display and hasattr(tz_display, 'utcoffset'):
            try:
                off = tz_display.utcoffset(datetime.now())
                tz_str = f"UTC{int(off.total_seconds()//3600):+d}"
            except Exception:
                tz_str = str(tz_display)
        else:
            tz_str = str(tz_display)

        print(f"\n[Location Detected]: {location.get('city','Unknown')}, {location.get('country','Unknown')} (tz={tz_str})")
        try:
            print(f"Latitude: {location['latitude']:.4f}°, Longitude: {location['longitude']:.4f}°")
        except Exception:
            pass
    else:
        # default fallback
        print("\nUsing default location: Delhi, India (tz=Asia/Kolkata)")
        location = {
            'latitude': 28.7041,
            'longitude': 77.1025,
            'city': 'Delhi',
            'country': 'India',
            'timezone': 'Asia/Kolkata'
        }

    # Allow user to override detected/default location by entering a place name
    try:
        user_loc = input("\nEnter a location name to use instead of detected/default (press Enter to keep current): ").strip()
    except Exception:
        user_loc = ''

    if user_loc:
        geocoded = geocode_location(user_loc)
        if geocoded:
            location = geocoded
            print(f"Using geocoded location: {location.get('city','')}, {location.get('country','')}")
            try:
                print(f"Latitude: {location['latitude']:.4f}°, Longitude: {location['longitude']:.4f}°")
            except Exception:
                pass
        else:
            print("Could not resolve the location name — continuing with detected/default location.")

    # Calculate for today at 06:00:00
    dt = datetime.now().replace(hour=6, minute=0, second=0)
    panchanga = calculate_complete_panchanga(location, dt)
    print_complete_panchanga(panchanga)

    # Save to JSON
    with open('complete_panchanga.json', 'w') as f:
        # Convert datetime objects to strings for JSON serialization
        panchanga_copy = panchanga.copy()
        json.dump(panchanga_copy, f, indent=2, default=str)

    print("\n[OK] Complete Panchanga saved to: complete_panchanga.json")

    # Offer to calculate for different dates
    while True:
        choice = input("\nCalculate for different date? (y/n): ").lower()
        if choice == 'y':
            try:
                date_str = input("Enter date (YYYY-MM-DD): ")
                time_str = input("Enter time (HH:MM:SS, optional): ").strip() or "06:00:00"

                dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                panchanga = calculate_complete_panchanga(location, dt)
                print_complete_panchanga(panchanga)

                # Save to JSON
                with open('complete_panchanga.json', 'w') as f:
                    # Convert datetime objects to strings for JSON serialization
                    panchanga_copy = panchanga.copy()
                    json.dump(panchanga_copy, f, indent=2, default=str)

            except ValueError as e:
                print(f"Invalid input: {e}")
        else:
            break

    swe.close()
    print("\nThank you for using Vedic Calendar Calculator!")
    
