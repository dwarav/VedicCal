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

# Constants for Calculations
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

VARJYAM_STARTS = [
    50, 24, 30, 40, 14, 21, 30, 20, 32,  # 1-9
    30, 20, 18, 22, 20, 14, 14, 10, 14,  # 10-18
    20, 24, 20, 10, 10, 18, 16, 24, 30   # 19-27
]

AMRIT_STARTS = [
    42, 48, 54, 52, 38, 35, 54, 44, 56,  # 1-9
    54, 44, 48, 42, 46, 34, 32, 38, 38,  # 10-18
    40, 48, 52, 38, 38, 42, 36, 48, 56   # 19-27
]

RAHU_KEY = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
YAMA_KEY = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
GULI_KEY = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}

DUR_KEY = {
    6: [14], 0: [9, 12], 1: [2, 4], 2: [8], 3: [5, 12], 4: [4, 9], 5: [1, 6]
}

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

YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma", "Dhriti",
    "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi",
    "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
    "Brahma", "Indra", "Vaidhriti"
]

KARANAS = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garija", "Vanija", "Vishti", 
    "Shakuni", "Chatushpada", "Naga", "Kimstughna"
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
    """Robust Sunrise/Set calculation."""
    rsmi_rise = swe.CALC_RISE | swe.BIT_DISC_CENTER
    rsmi_set = swe.CALC_SET | swe.BIT_DISC_CENTER
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
# PANCHANG ELEMENT LOGIC
# ==========================================

def get_sign(long): return int(long / 30) % 12

def normalize_angle(angle): return angle % 360

def get_tithi_details(jd):
    s, m = get_planet_positions(jd)
    diff = normalize_angle(m - s)
    return int(diff / 12), diff

def get_nakshatra_details(jd):
    _, m = get_planet_positions(jd)
    return int(m / 13.333333333), m

def get_yoga_details(jd):
    s, m = get_planet_positions(jd)
    total = normalize_angle(s + m)
    return int(total / 13.333333333), total

def get_karana_details(jd):
    s, m = get_planet_positions(jd)
    diff = normalize_angle(m - s)
    return int(diff / 6), diff

def get_karana_name(k_index):
    # Map 0-59 index to name
    if k_index == 0: return KARANAS[10] # Kimstughna
    if k_index >= 57: return KARANAS[k_index - 50] # Shakuni, Chatushpada, Naga
    return KARANAS[(k_index - 1) % 7]

# ==========================================
# EVENT FINDER
# ==========================================

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

def get_day_events(jd_sunrise, jd_next_sunrise, check_func, name_list, total_count, is_karana=False):
    """
    Generic function to find ALL events occurring between Sunrise and Next Sunrise.
    Returns a list of dicts: {'name': str, 'start': jd, 'end': jd}
    """
    events = []
    
    # 1. Get current element at Sunrise
    curr_idx, _ = check_func(jd_sunrise)
    
    # 2. Find when this current element ends
    # We look backwards to find start, forwards to find end
    # Backwards search (limited to 2 days prior to be safe)
    start_jd = find_event_time(jd_sunrise - 2.0, check_func, (curr_idx - 1) % total_count)
    if not start_jd: start_jd = jd_sunrise # Fallback if unknown
    
    current_search_jd = jd_sunrise
    
    # Loop to find all transitions until next sunrise
    while True:
        # Find end of current index
        end_jd = find_event_time(current_search_jd, check_func, curr_idx)
        
        # Determine Name
        if is_karana:
            name = get_karana_name(curr_idx)
        else:
            name = name_list[curr_idx]
            
        events.append({
            'name': name,
            'start': start_jd,
            'end': end_jd # Can be None if it doesn't end in search window
        })
        
        # Break if the element ends AFTER next sunrise or doesn't end
        if end_jd is None or end_jd >= jd_next_sunrise:
            break
            
        # Setup for next loop
        start_jd = end_jd
        current_search_jd = end_jd + 0.001 # Move slightly forward
        curr_idx = (curr_idx + 1) % total_count
        
    return events

# ==========================================
# MAIN LOGIC
# ==========================================

def calculate_panchang(location_name, date_str):
    setup_swisseph()
    print(f"\n{'='*70}\nVEDIC PANCHANG CALCULATOR (ADVANCED)\n{'='*70}")
    
    # 1. Init
    loc = get_location_data(location_name)
    tz = loc['tz']
    print(f"Location:  {loc['name']}")
    print(f"Coords:    {loc['lat']:.4f}, {loc['lon']:.4f}")
    
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    jd_noon = get_julian_day(tz.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 12, 0)))
    
    # 2. Sun Data (Today & Tomorrow for range)
    jd_rise, jd_set = calculate_sunrise_sunset(jd_noon, loc['lat'], loc['lon'])
    jd_rise_next, _ = calculate_sunrise_sunset(jd_noon + 1, loc['lat'], loc['lon'])
    
    dt_rise = get_local_time_from_jd(jd_rise, tz)
    dt_set = get_local_time_from_jd(jd_set, tz)
    
    print(f"Date:      {dt_rise.strftime('%A, %d %B %Y')}")
    print(f"Sunrise:   {dt_rise.strftime('%H:%M:%S')}")
    print(f"Sunset:    {dt_set.strftime('%H:%M:%S')}")
    print("-" * 70)
    
    # Format Helper
    def fmt_full(jd): return get_local_time_from_jd(jd, tz).strftime('%d-%b %H:%M:%S') if jd else "..."

    # ==========================
    # MULTI-EVENT CALCULATIONS
    # ==========================
    
    # Tithi
    tithi_events = get_day_events(jd_rise, jd_rise_next, 
                                  lambda j: (get_tithi_details(j)[0], 0), 
                                  TITHIS, 30)
    
    # Nakshatra
    nak_events = get_day_events(jd_rise, jd_rise_next, 
                                lambda j: (get_nakshatra_details(j)[0], 0), 
                                NAKSHATRAS, 27)

    # Yoga
    yoga_events = get_day_events(jd_rise, jd_rise_next, 
                                 lambda j: (get_yoga_details(j)[0], 0), 
                                 YOGAS, 27)
                                 
    # Karana
    karana_events = get_day_events(jd_rise, jd_rise_next, 
                                   lambda j: (get_karana_details(j)[0], 0), 
                                   [], 60, is_karana=True)

    # ==========================
    # DISPLAY LOOPS
    # ==========================

    print(f"[TITHI]")
    for e in tithi_events:
        print(f"  • {e['name']:<20} : {fmt_full(e['start'])}  to  {fmt_full(e['end'])}")

    print(f"\n[NAKSHATRA]")
    for e in nak_events:
        print(f"  • {e['name']:<20} : {fmt_full(e['start'])}  to  {fmt_full(e['end'])}")
        
    print(f"\n[YOGA]")
    for e in yoga_events:
        print(f"  • {e['name']:<20} : {fmt_full(e['start'])}  to  {fmt_full(e['end'])}")

    print(f"\n[KARANA]")
    for e in karana_events:
        print(f"  • {e['name']:<20} : {fmt_full(e['start'])}  to  {fmt_full(e['end'])}")

    print("-" * 70)

    # ==========================
    # CALCULATE SPECIAL TIMINGS
    # ==========================
    # Re-using previous logic for Kalam, but strictly based on Sunrise/Set
    weekday_idx = dt_rise.weekday()
    
    def get_kalam(key_map, parts=8):
        duration = jd_set - jd_rise
        part = duration / parts
        octant = key_map[weekday_idx]
        s = jd_rise + ((octant - 1) * part)
        return s, s + part

    rahu = get_kalam(RAHU_KEY)
    yama = get_kalam(YAMA_KEY)
    guli = get_kalam(GULI_KEY)
    
    # Varjyam & Amrit (Based on FIRST Nakshatra of the day usually, or iterating)
    # We will show for the Nakshatra active at Sunrise
    nak_sunrise = nak_events[0]
    nak_idx_sunrise = NAKSHATRAS.index(nak_sunrise['name'])
    
    def calc_period(start_jd, table, duration_ghatis):
        s_ghati = table[nak_idx_sunrise]
        s_jd = start_jd + (s_ghati / 60.0)
        e_jd = s_jd + (duration_ghatis / 60.0)
        return s_jd, e_jd

    print(f"[TIMINGS]")
    def fmt_time(jd): return get_local_time_from_jd(jd, tz).strftime('%H:%M')
    
    print(f"  Rahu Kalam    : {fmt_time(rahu[0])} - {fmt_time(rahu[1])}")
    print(f"  Yamaganda     : {fmt_time(yama[0])} - {fmt_time(yama[1])}")
    print(f"  Gulikai       : {fmt_time(guli[0])} - {fmt_time(guli[1])}")
    
    # Varjyam
    if nak_sunrise['start']:
        v_s, v_e = calc_period(nak_sunrise['start'], VARJYAM_STARTS, VARJYAM_DURATION_GHATIS)
        print(f"  Varjyam       : {fmt_time(v_s)} - {fmt_time(v_e)} (Based on {nak_sunrise['name']})")
        
        a_s, a_e = calc_period(nak_sunrise['start'], AMRIT_STARTS, AMRIT_DURATION_GHATIS)
        print(f"  Amrit Kalam   : {fmt_time(a_s)} - {fmt_time(a_e)}")
    else:
        print("  Varjyam/Amrit : Requires valid Nakshatra start time")
        
    print("=" * 70)

if __name__ == "__main__":
    try:
        calculate_panchang("Epsom, United Kingdom", "2025-12-31")
    except Exception as e:
        import traceback
        traceback.print_exc()