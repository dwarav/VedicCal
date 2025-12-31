import swisseph as swe
import os
from datetime import datetime, timedelta
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# ================= CONFIG =================

# 1. Define the specific path on Hostinger
SERVER_EPHE_PATH = '/home/u285716465/domains/dwara.org/public_html/vedic/ephe'

# 2. Check if we are on the server
if os.path.exists(SERVER_EPHE_PATH):
    EPHEMERIS_PATH = SERVER_EPHE_PATH
else:
    # 3. Fallback: Use the local relative path
    # os.path.dirname(__file__) ensures it works even if you run the script from a different folder
    EPHEMERIS_PATH = os.path.join(os.path.dirname(__file__), 'ephe')
    
SIDEREAL_MODE = swe.SIDM_LAHIRI 
VARJYAM_GHATIS = 4.0
AMRIT_GHATIS = 4.0

# ================= TABLES =================
RASHIS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"]
VARJYAM_STARTS = [50, 24, 30, 40, 14, 21, 30, 20, 32, 30, 20, 18, 22, 20, 14, 14, 10, 14, 20, 24, 20, 10, 10, 18, 16, 24, 30]
AMRIT_STARTS = [42, 48, 54, 52, 38, 35, 54, 44, 56, 54, 44, 48, 42, 46, 34, 32, 38, 38, 40, 48, 52, 38, 38, 42, 36, 48, 56]
RAHU_KEY = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
YAMA_KEY = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
GULI_KEY = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}

TITHIS = [
    "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi", "Shukla Panchami", "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami", "Shukla Navami", "Shukla Dashami", "Shukla Ekadashi", "Shukla Dwadashi", "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima",
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi", "Krishna Panchami", "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami", "Krishna Navami", "Krishna Dashami", "Krishna Ekadashi", "Krishna Dwadashi", "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya"
]
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]
YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"
]
KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Garija", "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"]

# ================= HELPERS =================
def setup_swisseph():
    swe.set_ephe_path(EPHEMERIS_PATH)
    swe.set_sid_mode(SIDEREAL_MODE)

def get_location(name):
    try:
        geolocator = Nominatim(user_agent="panchang_web")
        loc = geolocator.geocode(name)
        if not loc: return None
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
        return {'name': loc.address, 'lat': loc.latitude, 'lon': loc.longitude, 'tz': pytz.timezone(tz_str)}
    except: return None

def jd_from_dt(dt_local):
    dt_utc = dt_local.astimezone(pytz.utc)
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0)

def dt_from_jd(jd, tz):
    y, m, d, h_dec = swe.revjul(jd)
    h = int(h_dec)
    mins = (h_dec - h) * 60
    mi = int(mins)
    sec = int((mins - mi) * 60)
    try:
        return datetime(int(y), int(m), int(d), h, mi, sec, tzinfo=pytz.utc).astimezone(tz)
    except: return None

def calc_sun(jd, lat, lon):
    geopos = (float(lon), float(lat), 0.0)
    jd_search = jd - 0.375 # Start 3AM
    rise = swe.rise_trans(jd_search, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER, geopos)[1][0]
    set_ = swe.rise_trans(jd_search, swe.SUN, swe.CALC_SET | swe.BIT_DISC_CENTER, geopos)[1][0]
    return rise, set_

def get_pos(jd):
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    return swe.calc_ut(jd, swe.SUN, flags)[0][0], swe.calc_ut(jd, swe.MOON, flags)[0][0]

# ================= CALCULATORS =================
def get_events(start_jd, end_jd, func, names, count, is_karana=False):
    events = []
    curr_idx, _ = func(start_jd)
    
    # Check if this started earlier
    s_jd = find_trans(start_jd - 1.5, func, (curr_idx - 1) % count) or start_jd
    
    curr_search = start_jd
    while True:
        e_jd = find_trans(curr_search, func, curr_idx)
        name = get_karana_name(curr_idx) if is_karana else names[curr_idx]
        
        events.append({'name': name, 'start': s_jd, 'end': e_jd})
        
        if not e_jd or e_jd >= end_jd: break
        
        s_jd = e_jd
        curr_search = e_jd + 0.002
        curr_idx = (curr_idx + 1) % count
    return events

def find_trans(start, func, target):
    t1, t2 = start, start + 2.0
    curr = t1
    found = False
    while curr < t2:
        if func(curr)[0] != func(curr + 1/24.0)[0] and func(curr)[0] == target:
            t1, t2 = curr, curr + 1/24.0
            found = True
            break
        curr += 1/24.0
    if not found: return None
    while (t2 - t1) > 0.00001:
        mid = (t1 + t2)/2
        if func(mid)[0] == target: t1 = mid
        else: t2 = mid
    return t2

def get_karana_name(k):
    if k == 0: return KARANAS[10]
    if k >= 57: return KARANAS[k - 50]
    return KARANAS[(k - 1) % 7]

# ================= MAIN API =================
def fetch_panchang(loc_str, date_str):
    setup_swisseph()
    loc = get_location(loc_str)
    if not loc: return {"error": "Location not found"}
    
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    tz = loc['tz']
    jd_noon = jd_from_dt(tz.localize(datetime(dt.year, dt.month, dt.day, 12, 0)))
    
    rise, set_ = calc_sun(jd_noon, loc['lat'], loc['lon'])
    rise_next, _ = calc_sun(jd_noon + 1, loc['lat'], loc['lon'])
    
    # Lambdas
    fn_tithi = lambda j: (int((get_pos(j)[1] - get_pos(j)[0]) % 360 / 12), 0)
    fn_nak = lambda j: (int(get_pos(j)[1] / 13.333333333), 0)
    fn_yoga = lambda j: (int((get_pos(j)[1] + get_pos(j)[0]) % 360 / 13.333333333), 0)
    fn_karana = lambda j: (int((get_pos(j)[1] - get_pos(j)[0]) % 360 / 6), 0)
    
    # Calculate Events
    data = {
        "meta": {
            "location": loc['name'],
            "date": dt_from_jd(rise, tz).strftime("%A, %d %B %Y"),
            "sunrise": dt_from_jd(rise, tz).strftime("%H:%M:%S"),
            "sunset": dt_from_jd(set_, tz).strftime("%H:%M:%S"),
            "tz": str(tz)
        },
        "tithi": get_events(rise, rise_next, fn_tithi, TITHIS, 30),
        "nakshatra": get_events(rise, rise_next, fn_nak, NAKSHATRAS, 27),
        "yoga": get_events(rise, rise_next, fn_yoga, YOGAS, 27),
        "karana": get_events(rise, rise_next, fn_karana, [], 60, True),
        "timings": {}
    }
    
    # Helper to format dict times
    def fmt_dt(jd): return dt_from_jd(jd, tz).strftime("%d-%b %H:%M") if jd else "..."
    
    # Format List Data
    for k in ['tithi', 'nakshatra', 'yoga', 'karana']:
        for item in data[k]:
            item['start_fmt'] = fmt_dt(item['start'])
            item['end_fmt'] = fmt_dt(item['end'])

    # Timings
    w_idx = dt_from_jd(rise, tz).weekday()
    day_len = set_ - rise
    
    def get_kalam(k_map):
        s = rise + ((k_map[w_idx]-1) * (day_len/8))
        return f"{fmt_dt(s).split(' ')[1]} - {fmt_dt(s + day_len/8).split(' ')[1]}"
        
    data['timings']['rahu'] = get_kalam(RAHU_KEY)
    data['timings']['yama'] = get_kalam(YAMA_KEY)
    data['timings']['guli'] = get_kalam(GULI_KEY)
    
    # Varjyam/Amrit (Based on sunrise nakshatra)
    nak_idx = NAKSHATRAS.index(data['nakshatra'][0]['name'])
    nk_start = data['nakshatra'][0]['start']
    
    v_s = nk_start + (VARJYAM_STARTS[nak_idx]/60.0)
    data['timings']['varjyam'] = f"{fmt_dt(v_s)} - {fmt_dt(v_s + 4/60.0)}"
    
    a_s = nk_start + (AMRIT_STARTS[nak_idx]/60.0)
    data['timings']['amrit'] = f"{fmt_dt(a_s)} - {fmt_dt(a_s + 4/60.0)}"

    return data