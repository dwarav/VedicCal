import swisseph as swe
import math
from datetime import datetime, timedelta
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# ==========================================
# CONFIGURATION
# ==========================================
EPHEMERIS_PATH = './ephe' 
SIDEREAL_MODE = swe.SIDM_LAHIRI 

# Constants
VARJYAM_DURATION_GHATIS = 4.0 # 96 mins
AMRIT_DURATION_GHATIS = 4.0   # 96 mins

# ==========================================
# VEDIC DATA TABLES
# ==========================================

RASHIS = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)",
    "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrishchika (Scorpio)",
    "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"
]

# Varjyam Start Ghatis (from Nakshatra Start)
VARJYAM_STARTS = [
    50, 24, 30, 40, 14, 21, 30, 20, 32,  # 1-9 (Ashwini to Ashlesha)
    30, 20, 18, 22, 20, 14, 14, 10, 14,  # 10-18 (Magha to Jyeshtha)
    20, 24, 20, 10, 10, 18, 16, 24, 30   # 19-27 (Mula to Revati)
]

# Amrit Kalam Start Ghatis (from Nakshatra Start)
# Source: Standard Vedic Tables
AMRIT_STARTS = [
    42, 48, 54, 52, 38, 35, 54, 44, 56,  # 1-9
    54, 44, 48, 42, 46, 34, 32, 38, 38,  # 10-18
    40, 48, 52, 38, 38, 42, 36, 48, 56   # 19-27
]

# Kalam Calculations (Weekday based)
# Format: {Weekday_Index: Octant_Index (1-8)}
RAHU_KEY = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
YAMA_KEY = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
GULI_KEY = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}

# Dur Muhurtam Segments (15 parts of day)
DUR_KEY = {
    6: [14],       # Sunday
    0: [9, 12],    # Monday
    1: [2, 4],     # Tuesday
    2: [8],        # Wednesday
    3: [5, 12],    # Thursday
    4: [4, 9],     # Friday
    5: [1, 6]      # Saturday
}

# Names
TITHIS = [
    "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi", "Shukla Panchami",
    "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami", "Shukla Navami", "Shukla Dashami",
    "Shukla Ekadashi", "Shukla Dwadashi", "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima",
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi", "Krishna Panchami",
    "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami", "Krishna Navami", "Krishna Dashami",
    "Krishna Ekadashi", "Krishna Dwadashi", "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya"
]
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati"
]

# ==========================================
# CORE FUNCTIONS
# ==========================================

def setup_swisseph():
    swe.set_ephe_path(EPHEMERIS_PATH)
    swe.set_sid_mode(SIDEREAL_MODE)

def get_location_data(location_name):
    geolocator = Nominatim(user_agent="panchang_calculator")
    location = geolocator.geocode(location_name)
    if not location: raise ValueError("Location not found")
    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    return {'name': location.address, 'lat': location.latitude, 'lon': location.longitude, 'tz': pytz.timezone(tz_str)}

def get_julian_day(dt_local):
    dt_utc = dt_local.astimezone(pytz.utc)
    return swe.julday(int(dt_utc.year), int(dt_utc.month), int(dt_utc.day), 
                      dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0)

def get_local_time_from_jd(jd, timezone_obj):
    year_fl, month_fl, day_fl, hour_dec = swe.revjul(jd)
    year, month, day = int(year_fl), int(month_fl), int(day_fl)
    
    hour = int(hour_dec)
    minute_dec = (hour_dec - hour) * 60
    minute = int(minute_dec)
    second = int((minute_dec - minute) * 60)
    
    if second >= 60: second = 0; minute += 1
    if minute >= 60: minute = 0; hour += 1
    if hour >= 24: 
        return (datetime(year, month, day, 0, 0, 0, tzinfo=pytz.utc) + timedelta(days=1)).astimezone(timezone_obj)

    try:
        return datetime(year, month, day, hour, minute, second, tzinfo=pytz.utc).astimezone(timezone_obj)
    except ValueError: return None

def calculate_sunrise_sunset(jd_start, lat, lon):
    """
    Robust Sunrise/Set calculation.
    FIX: Flags separated carefully to avoid bitwise collisions.
    """
    # Define Flags (No FLG_SWIEPH here to avoid conflict with CALC_SET)
    rsmi_rise = swe.CALC_RISE | swe.BIT_DISC_CENTER
    rsmi_set = swe.CALC_SET | swe.BIT_DISC_CENTER
    
    # Coordinates tuple
    geopos = (float(lon), float(lat), 0.0)
    
    # Start search from 3 AM to find MORNING rise
    jd_morning = jd_start - 0.375
    
    res_rise = swe.rise_trans(jd_morning, swe.SUN, rsmi_rise, geopos)
    res_set = swe.rise_trans(jd_morning, swe.SUN, rsmi_set, geopos)
    return res_rise[1][0], res_set[1][0]

def get_planet_positions(jd):
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    s_res = swe.calc_ut(jd, swe.SUN, flags)
    m_res = swe.calc_ut(jd, swe.MOON, flags)
    return s_res[0][0], m_res[0][0]

# ==========================================
# PANCHANG ALGORITHMS
# ==========================================

def get_sign(long):
    return int(long / 30) % 12

def get_tithi_details(jd):
    s, m = get_planet_positions(jd)
    diff = (m - s) % 360
    return int(diff / 12), diff

def get_nakshatra_details(jd):
    _, m = get_planet_positions(jd)
    return int(m / 13.333333333), m

def find_event_time(start_jd, check_func, target_idx):
    """Binary search for transition time."""
    t1, t2 = start_jd, start_jd + 2.0
    
    # Coarse search
    curr = t1
    bracket_found = False
    while curr < t2:
        idx_now, _ = check_func(curr)
        idx_next, _ = check_func(curr + 1/24.0)
        if idx_now != idx_next and idx_now == target_idx:
            t1, t2 = curr, curr + 1/24.0
            bracket_found = True
            break
        curr += 1/24.0
    
    if not bracket_found: return None
    
    # Fine search
    while (t2 - t1) > 0.00001: 
        mid = (t1 + t2) / 2
        idx, _ = check_func(mid)
        if idx == target_idx: t1 = mid
        else: t2 = mid
    return t2

# ==========================================
# TIMING CALCULATIONS
# ==========================================

def calculate_kalam(rise_jd, set_jd, weekday_idx):
    day_len = set_jd - rise_jd
    part_len = day_len / 8.0
    def get_period(octant):
        s = rise_jd + ((octant - 1) * part_len)
        return s, s + part_len
    return get_period(RAHU_KEY[weekday_idx]), get_period(YAMA_KEY[weekday_idx]), get_period(GULI_KEY[weekday_idx])

def calculate_dur_muhurtam(rise_jd, set_jd, weekday_idx):
    day_len = set_jd - rise_jd
    part_len = day_len / 15.0
    segments = DUR_KEY[weekday_idx]
    return [(rise_jd + ((s - 1) * part_len), rise_jd + (s * part_len)) for s in segments]

def calculate_nakshatra_timings(nak_start_jd, nak_index):
    """Calculates Varjyam and Amrit Kalam based on start ghatis."""
    
    # 1 Day = 60 Ghatis. 
    # Factor to convert Ghatis to Days = 1.0 / 60.0
    GHATI_TO_DAY = 1.0 / 60.0
    
    # Varjyam
    v_start_ghati = VARJYAM_STARTS[nak_index]
    v_start = nak_start_jd + (v_start_ghati * GHATI_TO_DAY)
    v_end = v_start + (VARJYAM_DURATION_GHATIS * GHATI_TO_DAY)
    
    # Amrit Kalam
    a_start_ghati = AMRIT_STARTS[nak_index]
    a_start = nak_start_jd + (a_start_ghati * GHATI_TO_DAY)
    a_end = a_start + (AMRIT_DURATION_GHATIS * GHATI_TO_DAY)
    
    return (v_start, v_end), (a_start, a_end)

# ==========================================
# MAIN
# ==========================================

def calculate_panchang(location_name, date_str):
    setup_swisseph()
    print(f"\n{'='*60}\nVEDIC PANCHANG CALCULATOR\n{'='*60}")
    
    # 1. Init
    loc = get_location_data(location_name)
    tz = loc['tz']
    print(f"Location:  {loc['name']}")
    print(f"Coords:    {loc['lat']:.4f}, {loc['lon']:.4f}")
    
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    jd_noon = get_julian_day(tz.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 12, 0)))
    
    # 2. Sun Data
    jd_rise, jd_set = calculate_sunrise_sunset(jd_noon, loc['lat'], loc['lon'])
    dt_rise = get_local_time_from_jd(jd_rise, tz)
    dt_set = get_local_time_from_jd(jd_set, tz)
    weekday_idx = dt_rise.weekday() 
    
    s_long, m_long = get_planet_positions(jd_rise)
    
    # 3. Events
    tithi_idx, _ = get_tithi_details(jd_rise)
    jd_tithi_end = find_event_time(jd_rise, lambda j: (get_tithi_details(j)[0], 0), tithi_idx)
    
    nak_idx, _ = get_nakshatra_details(jd_rise)
    jd_nak_end = find_event_time(jd_rise, lambda j: (get_nakshatra_details(j)[0], 0), nak_idx)
    
    # Search backwards for Nakshatra start to calculate Amrit/Varjyam
    jd_nak_start = find_event_time(jd_rise - 1.5, lambda j: (get_nakshatra_details(j)[0], 0), (nak_idx - 1) % 27)

    # 4. Rashi
    sun_sign = RASHIS[get_sign(s_long)]
    moon_sign = RASHIS[get_sign(m_long)]
    
    # 5. Timings
    rahu, yama, guli = calculate_kalam(jd_rise, jd_set, weekday_idx)
    dur_muhurtams = calculate_dur_muhurtam(jd_rise, jd_set, weekday_idx)
    abhijit_start = jd_rise + ((jd_set - jd_rise) / 15.0 * 7)
    abhijit_end = abhijit_start + ((jd_set - jd_rise) / 15.0)
    
    varj_period, amrit_period = (None, None), (None, None)
    if jd_nak_start:
        varj_period, amrit_period = calculate_nakshatra_timings(jd_nak_start, nak_idx)

    # =================
    # FORMAT & PRINT
    # =================
    def fmt(jd): return get_local_time_from_jd(jd, tz).strftime('%H:%M') if jd else "---"
    def fmt_full(jd): return get_local_time_from_jd(jd, tz).strftime('%d-%b %H:%M') if jd else "---"

    print(f"Date:      {dt_rise.strftime('%A, %d %B %Y')}")
    print(f"Sunrise:   {dt_rise.strftime('%H:%M:%S')}")
    print(f"Sunset:    {dt_set.strftime('%H:%M:%S')}")
    print("-" * 60)
    
    print(f"[ASTRO DETAILS]")
    print(f"Sun Sign:  {sun_sign} ({swe.split_deg(s_long, swe.SPLIT_DEG_ZODIACAL)[0]}°)")
    print(f"Moon Sign: {moon_sign} ({swe.split_deg(m_long, swe.SPLIT_DEG_ZODIACAL)[0]}°)")
    print(f"Tithi:     {TITHIS[tithi_idx]}")
    print(f"           Ends at: {fmt_full(jd_tithi_end)}")
    print(f"Nakshatra: {NAKSHATRAS[nak_idx]}")
    print(f"           Ends at: {fmt_full(jd_nak_end)}")
    print("-" * 60)
    
    print(f"[INAUSPICIOUS PERIODS]")
    print(f"Rahu Kalam:    {fmt(rahu[0])} - {fmt(rahu[1])}")
    print(f"Yamaganda:     {fmt(yama[0])} - {fmt(yama[1])}")
    print(f"Gulikai:       {fmt(guli[0])} - {fmt(guli[1])}")
    print(f"Dur Muhurtam:  " + ", ".join([f"{fmt(d[0])}-{fmt(d[1])}" for d in dur_muhurtams]))
    
    if varj_period[0]:
        print(f"Varjyam:       {fmt_full(varj_period[0])} - {fmt_full(varj_period[1])}")
    else:
        print("Varjyam:       (Nakshatra start not found)")

    print("-" * 60)
    print(f"[AUSPICIOUS PERIODS]")
    print(f"Abhijit:       {fmt(abhijit_start)} - {fmt(abhijit_end)}")
    if weekday_idx == 2: print("               (Note: Abhijit typically avoided on Wednesdays)")

    if amrit_period[0]:
        print(f"Amrit Kalam:   {fmt_full(amrit_period[0])} - {fmt_full(amrit_period[1])}")
    else:
        print("Amrit Kalam:   (Nakshatra start not found)")
    print("=" * 60)

if __name__ == "__main__":
    try:
        calculate_panchang("Bangalore, India", "2025-12-31")
    except Exception as e:
        import traceback
        traceback.print_exc()