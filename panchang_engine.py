import swisseph as swe
from datetime import datetime, timedelta, date
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import os
import math
import urllib.parse

# ================= CONFIG =================
SERVER_EPHE_PATH = '/home/u285716465/domains/dwara.org/public_html/vedic/ephe'
if os.path.exists(SERVER_EPHE_PATH):
    EPHEMERIS_PATH = SERVER_EPHE_PATH
else:
    EPHEMERIS_PATH = os.path.join(os.path.dirname(__file__), 'ephe')

SIDEREAL_MODE = swe.SIDM_LAHIRI

# ================= DATA CONSTANTS =================
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
RASHIS = ["Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)", "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrishchika (Scorpio)", "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"]
PADA_NAMES = [f"{n} Pada {i+1}" for n in NAKSHATRAS for i in range(4)]

# --- ICONS ---
RASHI_ICONS = {"Mesha (Aries)": "♈", "Vrishabha (Taurus)": "♉", "Mithuna (Gemini)": "♊", "Karka (Cancer)": "♋", "Simha (Leo)": "♌", "Kanya (Virgo)": "♍", "Tula (Libra)": "♎", "Vrishchika (Scorpio)": "♏", "Dhanu (Sagittarius)": "♐", "Makara (Capricorn)": "♑", "Kumbha (Aquarius)": "♒", "Meena (Pisces)": "♓"}
NAK_ICONS = {"Ashwini": "🐴", "Bharani": "🐘", "Krittika": "🔥", "Rohini": "🐍", "Mrigashira": "🦌", "Ardra": "💧", "Punarvasu": "🏹", "Pushya": "🌸", "Ashlesha": "🐍", "Magha": "👑", "Purva Phalguni": "🛋️", "Uttara Phalguni": "🛏️", "Hasta": "🖐️", "Chitra": "✨", "Swati": "🌬️", "Vishakha": "⚖️", "Anuradha": "🌸", "Jyeshtha": "🌂", "Mula": "🌿", "Purva Ashadha": "🌊", "Uttara Ashadha": "🐘", "Shravana": "👂", "Dhanishta": "🥁", "Shatabhisha": "⭕", "Purva Bhadrapada": "🦁", "Uttara Bhadrapada": "🐮", "Revati": "🐟"}
TITHI_ICONS = {"Shukla Pratipada": "🌒", "Shukla Dwitiya": "🌒", "Shukla Tritiya": "🌓", "Shukla Chaturthi": "🌓", "Shukla Panchami": "🌔", "Shukla Shashthi": "🌔", "Shukla Saptami": "🌔", "Shukla Ashtami": "🌓", "Shukla Navami": "🌔", "Shukla Dashami": "🌔", "Shukla Ekadashi": "¾", "Shukla Dwadashi": "🌖", "Shukla Trayodashi": "🌖", "Shukla Chaturdashi": "🌖", "Purnima": "🌕", "Krishna Pratipada": "🌖", "Krishna Dwitiya": "🌖", "Krishna Tritiya": "🌗", "Krishna Chaturthi": "🌗", "Krishna Panchami": "🌗", "Krishna Shashthi": "🌘", "Krishna Saptami": "🌘", "Krishna Ashtami": "🌗", "Krishna Navami": "🌘", "Krishna Dashami": "🌘", "Krishna Ekadashi": "🌘", "Krishna Dwadashi": "🌘", "Krishna Trayodashi": "🌘", "Krishna Chaturdashi": "🌘", "Amavasya": "🌑"}

VARJYAM_STARTS = [50, 24, 30, 40, 14, 21, 30, 20, 32, 30, 20, 18, 22, 20, 14, 14, 10, 14, 20, 24, 20, 10, 10, 18, 16, 24, 30]
AMRIT_STARTS = [42, 48, 54, 52, 38, 35, 54, 44, 56, 54, 44, 48, 42, 46, 34, 32, 38, 38, 40, 48, 52, 38, 38, 42, 36, 48, 56]
RAHU_KEY = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
YAMA_KEY = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
GULI_KEY = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}

# 1. TITHI BASED FESTIVALS
FESTIVAL_DB = {
    # Chaitra
    (0, 0, 0): "Ugadi / Gudi Padwa", (0, 0, 8): "Rama Navami", (0, 0, 14): "Hanuman Jayanti",
    # Vaishakha
    (1, 0, 2): "Akshaya Tritiya", (1, 0, 14): "Buddha Purnima",
    # Jyeshtha
    (2, 0, 9): "Ganga Dussehra", (2, 0, 14): "Vat Savitri Vrat",
    # Ashadha
    (3, 0, 1): "Jagannath Rath Yatra", (3, 0, 10): "Devshayani Ekadashi", (3, 0, 14): "Guru Purnima",
    # Shravana
    (4, 0, 4): "Nag Panchami", (4, 0, 14): "Raksha Bandhan", (4, 1, 7): "Janmashtami",
    # Bhadrapada
    (5, 0, 3): "Ganesh Chaturthi", (5, 0, 13): "Anant Chaturdashi", (5, 1, 14): "Mahalaya Amavasya",
    # Ashwina
    (6, 0, 0): "Navratri Ghatasthapana", (6, 0, 9): "Dussehra", (6, 0, 14): "Sharad Purnima",
    (6, 1, 3): "Karwa Chauth", (6, 1, 12): "Dhanteras", (6, 1, 14): "Diwali",
    # Kartika
    (7, 0, 0): "Govardhan Puja", (7, 0, 1): "Bhai Dooj", (7, 0, 10): "Tulsi Vivah", (7, 0, 14): "Kartik Purnima",
    # Margashirsha
    (8, 0, 10): "Gita Jayanti", (8, 0, 14): "Dattatreya Jayanti",
    # Magha
    (10, 0, 4): "Vasant Panchami", (10, 0, 6): "Ratha Saptami", (10, 1, 13): "Maha Shivaratri",
    # Phalguna
    (11, 0, 14): "Holi"
}

# 2. GREGORIAN FIXED DATE FESTIVALS
GREGORIAN_FESTIVALS = {
    (1, 1): "New Year's Day", (1, 14): "Makara Sankranti", (1, 26): "Republic Day India",
    (2, 14): "Valentine's Day", (3, 8): "Women's Day", (4, 14): "Ambedkar Jayanti",
    (5, 1): "Labor Day", (6, 21): "International Yoga Day", (8, 15): "Independence Day India",
    (10, 2): "Gandhi Jayanti", (11, 14): "Children's Day", (12, 25): "Christmas"
}

# 3. RELIABLE STATIC IMAGE MAP
FESTIVAL_IMAGES_STATIC = {
    "Ugadi": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Ugadi_Pachadi.jpg/320px-Ugadi_Pachadi.jpg",
    "Rama Navami": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Rama_Pattabhishekam.jpg/320px-Rama_Pattabhishekam.jpg",
    "Hanuman": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Hanuman_idol.jpg/320px-Hanuman_idol.jpg",
    "Akshaya Tritiya": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Goddess_Lakshmi.jpg/320px-Goddess_Lakshmi.jpg",
    "Guru Purnima": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Veda_Vyasa.jpg/320px-Veda_Vyasa.jpg",
    "Raksha Bandhan": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Rakhi.jpg/320px-Rakhi.jpg",
    "Janmashtami": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Krishna_holding_Govardhan.jpg/320px-Krishna_holding_Govardhan.jpg",
    "Ganesh": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Lalbaugcha_Raja.jpg/320px-Lalbaugcha_Raja.jpg",
    "Vinayaka": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Lalbaugcha_Raja.jpg/320px-Lalbaugcha_Raja.jpg",
    "Sankashti": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Lalbaugcha_Raja.jpg/320px-Lalbaugcha_Raja.jpg",
    "Navratri": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Durga_Puja_pandal.jpg/320px-Durga_Puja_pandal.jpg",
    "Durga": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Durga_Puja_pandal.jpg/320px-Durga_Puja_pandal.jpg",
    "Dussehra": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Ravana_effigy.jpg/320px-Ravana_effigy.jpg",
    "Diwali": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Diwali_lamps.jpg/320px-Diwali_lamps.jpg",
    "Shivaratri": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Shiva_lingam.jpg/320px-Shiva_lingam.jpg",
    "Holi": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Holi_Dahan.jpg/320px-Holi_Dahan.jpg",
    "Ekadashi": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Vishnu.jpg/320px-Vishnu.jpg",
    "Pradosh": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Nandi_bull.jpg/320px-Nandi_bull.jpg",
    "Sankranti": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Makara_Sankranti.jpg/320px-Makara_Sankranti.jpg",
    "Sashti": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Murugan.jpg/320px-Murugan.jpg",
    "Karthigai": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Murugan.jpg/320px-Murugan.jpg",
    "Rohini": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Krishna_holding_Govardhan.jpg/320px-Krishna_holding_Govardhan.jpg",
    "Amavasya": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Diwali_lamps.jpg/320px-Diwali_lamps.jpg",
    "Purnima": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Vishnu.jpg/320px-Vishnu.jpg",
    "Christmas": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Christmas_tree.jpg/320px-Christmas_tree.jpg",
    "Republic": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/India_Gate.jpg/320px-India_Gate.jpg",
    "Independence": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/India_Gate.jpg/320px-India_Gate.jpg",
    "Yoga": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Yoga_class_Rishikesh.jpg/320px-Yoga_class_Rishikesh.jpg"
}

# ================= CORE FUNCTIONS =================

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

# ================= CALCULATORS =================

def calc_sun_rise_set(jd, lat, lon):
    geopos = (float(lon), float(lat), 0.0)
    jd_search = jd - 0.375
    rise = swe.rise_trans(jd_search, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER, geopos)[1][0]
    set_ = swe.rise_trans(jd_search, swe.SUN, swe.CALC_SET | swe.BIT_DISC_CENTER, geopos)[1][0]
    return rise, set_

def calc_moon_rise_set(jd_start, lat, lon):
    geopos = (float(lon), float(lat), 0.0)
    jd_search = jd_start - 0.5
    res_rise = swe.rise_trans(jd_search, swe.MOON, swe.CALC_RISE | swe.BIT_DISC_CENTER, geopos)
    res_set = swe.rise_trans(jd_search, swe.MOON, swe.CALC_SET | swe.BIT_DISC_CENTER, geopos)
    return res_rise[1][0], res_set[1][0]

def get_pos(jd):
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    return swe.calc_ut(jd, swe.SUN, flags)[0][0], swe.calc_ut(jd, swe.MOON, flags)[0][0]

def get_events(start_jd, end_jd, func, names, count, is_karana=False):
    events = []
    curr_idx, _ = func(start_jd)
    s_jd = find_trans(start_jd - 1.5, func, (curr_idx - 1) % count) or start_jd
    curr_search = start_jd
    while True:
        e_jd = find_trans(curr_search, func, curr_idx)
        name = get_karana_name(curr_idx) if is_karana else names[curr_idx]
        events.append({'name': name, 'start': s_jd, 'end': e_jd, 'index': curr_idx})
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

def fmt_duration(jd_start, jd_end):
    duration_days = jd_end - jd_start
    total_seconds = int(duration_days * 24 * 3600)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d} Hours {minutes:02d} Mins {seconds:02d} Secs"

# ================= HELPER CALCULATORS =================

def get_tamil_yoga(weekday_idx, nak_idx):
    marana_combos = [(6, 1), (0, 13), (1, 20), (2, 18), (3, 9), (4, 10), (5, 26)]
    amrita_combos = [(6, 12), (0, 21), (1, 6), (2, 23), (3, 7), (4, 26), (5, 3)]
    key = (weekday_idx, nak_idx)
    if key in marana_combos: return "Marana"
    if key in amrita_combos: return "Amrita"
    return "Siddha"

def get_sarvartha_siddhi(weekday_idx, nak_idx):
    ss_map = {
        6: [12, 7, 18, 11, 20, 25, 0], 0: [21, 3, 4, 7, 16], 1: [0, 2, 4, 8],
        2: [3, 16, 12, 2, 4], 3: [7, 16, 2, 6, 26], 4: [26, 16, 0, 6, 21], 5: [3, 14, 21]
    }
    return nak_idx in ss_map.get(weekday_idx, [])

def get_netram_jeevan(nak_idx):
    n = nak_idx + 1
    rem = n % 9
    netram = 0
    if rem in [3, 4, 5, 6]: netram = 1
    elif rem in [7, 8, 0]: netram = 2
    jeevan = 1 if netram > 0 else 0 
    net_str = ["Zero Eyes", "One Eye", "Two Eyes"][netram]
    jee_str = "Full Life" if jeevan else "Empty Life"
    return net_str, jee_str

def get_baana_type(sun_nak_idx, nak_idx):
    dist = (nak_idx - sun_nak_idx) % 9
    baana_map = {
        0: "Sthira (Good)", 1: "Roga (Bad)", 2: "Agni (Bad)", 
        3: "Raja (Good)", 4: "Chora (Bad)", 5: "Mrityu (Bad)",
        6: "Sthira (Good)", 7: "Sthira (Good)", 8: "Sthira (Good)"
    }
    return baana_map.get(dist, "Sthira")

def get_calculated_timings(nak_events, weekday_idx, sun_nak_idx):
    # ANANDADI YOGAS CYCLE
    ANANDADI_YOGAS = [
        "Ananda", "Kaladanda", "Dhumra", "Prajapati", "Soumya", "Dhwalka", "Dhwaja",
        "Srivatsa", "Vajra", "Mudgara", "Chhatra", "Mitra", "Manasa", "Padma",
        "Lumba", "Utpata", "Mrityu", "Kana", "Siddhi", "Shubha", "Amrita",
        "Musala", "Gada", "Matanga", "Rakshasa", "Chara", "Sthira", "Pravardhamana"
    ]
    ananda_offset = {6:0, 0:22, 1:18, 2:14, 3:10, 4:6, 5:2}
    
    def fmt_event(ev_list, type_fn):
        res = []
        for e in ev_list:
            val = type_fn(e['index'])
            end_t = dt_from_jd(e['end'], pytz.utc).strftime('%I:%M %p') if e['end'] else "Full Night"
            res.append(f"{val} upto {end_t}")
        return " | ".join(res)

    anandadi_str = fmt_event(nak_events, lambda idx: ANANDADI_YOGAS[(idx + ananda_offset[weekday_idx]) % 28])
    tamil_str = fmt_event(nak_events, lambda idx: get_tamil_yoga(weekday_idx, idx))
    baana_str = fmt_event(nak_events, lambda idx: get_baana_type(sun_nak_idx, idx))
    
    n, j = get_netram_jeevan(nak_events[0]['index'])
    
    ss_found = []
    for e in nak_events:
        if get_sarvartha_siddhi(weekday_idx, e['index']):
            ss_found.append("Whole Day" if not e['end'] else f"upto {dt_from_jd(e['end'], pytz.utc).strftime('%I:%M %p')}")
    sarvartha_str = ", ".join(ss_found) if ss_found else "None"

    return {
        "anandadi": anandadi_str, "tamil": tamil_str, "sarvartha": sarvartha_str,
        "baana": baana_str, "netrama": n, "jeevanama": j, "vidaal": "None"
    }

def get_samvat_details(dt):
    year = dt.year
    is_after_new_year = dt.month > 4 or (dt.month == 4 and dt.day > 14)
    vikram = year + 57 if is_after_new_year else year + 56
    shaka = year - 78 if is_after_new_year else year - 79
    return {"vikram": vikram, "shaka": shaka, "gujarati": vikram, "samvatsara": "Pingala/Kalayukta"}

def get_ritu_ayana_details(jd):
    sun_trop = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
    if (sun_trop >= 270 and sun_trop < 360) or (sun_trop >= 0 and sun_trop < 90):
        ayana = "Uttarayana"; vedic_ayana = "Dakshinayana"
    else:
        ayana = "Dakshinayana"; vedic_ayana = "Uttarayana"
    norm_sun = sun_trop % 360
    if 270 <= norm_sun < 330: ritu = "Shishir (Winter)"
    elif 330 <= norm_sun < 360 or 0 <= norm_sun < 30: ritu = "Vasant (Spring)"
    elif 30 <= norm_sun < 90: ritu = "Grishma (Summer)"
    elif 90 <= norm_sun < 150: ritu = "Varsha (Monsoon)"
    elif 150 <= norm_sun < 210: ritu = "Sharad (Autumn)"
    else: ritu = "Hemant (Prewinter)"
    vedic_ritu = "Hemant (Prewinter)" if ritu == "Shishir (Winter)" else ritu
    return {"ritu": ritu, "vedic_ritu": vedic_ritu, "ayana": ayana, "vedic_ayana": vedic_ayana}

def calculate_muhurtas(rise, set_, rise_next, weekday_idx):
    day_len = set_ - rise
    night_len = rise_next - set_
    one_muhurta_day = day_len / 15.0
    one_muhurta_night = night_len / 15.0
    
    brahma_start = rise - (2 * one_muhurta_night)
    brahma_end = rise - (1 * one_muhurta_night)
    pratah_start = brahma_start
    pratah_end = rise
    
    abhijit_start = rise + (7 * one_muhurta_day)
    abhijit_end = rise + (8 * one_muhurta_day)
    abhijit_res = (abhijit_start, abhijit_end)

    vijaya_start = rise + (10 * one_muhurta_day)
    vijaya_end = rise + (11 * one_muhurta_day)
    godhuli_start = set_ - (12.0/(24*60))
    godhuli_end = set_ + (12.0/(24*60))
    sayahna_start = set_
    sayahna_end = set_ + one_muhurta_night
    nishita_start = set_ + (7 * one_muhurta_night)
    nishita_end = set_ + (8 * one_muhurta_night)
    
    DUR_MAP = {6: [14], 0: [8, 9], 1: [2, 4], 2: [8], 3: [5, 12], 4: [4, 9], 5: [1]}
    dur_times = []
    for seg in DUR_MAP[weekday_idx]:
        s = rise + ((seg-1)*one_muhurta_day)
        e = rise + (seg)*one_muhurta_day
        dur_times.append((s, e))
        
    return {
        "brahma": (brahma_start, brahma_end),
        "pratah": (pratah_start, pratah_end),
        "abhijit": abhijit_res,
        "vijaya": (vijaya_start, vijaya_end),
        "godhuli": (godhuli_start, godhuli_end),
        "sayahna": (sayahna_start, sayahna_end),
        "nishita": (nishita_start, nishita_end),
        "dur_day": dur_times
    }

def get_nivas_shool_details(jd, weekday_idx, tithi_idx, nak_idx):
    SHOOL_DIR = {0: "West", 1: "East", 2: "North", 3: "North", 4: "South", 5: "West", 6: "East"}
    disha_shool = SHOOL_DIR[weekday_idx]
    
    tithi_num = (tithi_idx % 15) + 1
    weekday_num = ((weekday_idx + 1) % 7) + 1
    agni_calc = (tithi_num + weekday_num + 1) % 4
    AGNI_LOC = {0: "Earth (Prithvi) - Good", 3: "Earth (Prithvi) - Good", 1: "Sky (Akasha) - Bad", 2: "Netherworld (Patala) - Bad"}
    agnivasa = AGNI_LOC[agni_calc]
    
    SHIVA_VASA = {
        1: "Nandi", 2: "Gauri", 3: "Sabha", 4: "Krida", 5: "Kailash", 6: "Vrishabha", 7: "Bhojana",
        8: "Nandi", 9: "Gauri", 10: "Sabha", 11: "Krida", 12: "Kailash", 13: "Vrishabha", 14: "Bhojana",
        15: "Kailash/Smashana"
    }
    shivavasa = SHIVA_VASA.get(tithi_num, "Kailash")
    
    return {
        "homahuti": "Agni" if tithi_num % 2 != 0 else "Shiva",
        "disha_shool": disha_shool,
        "agnivasa_1": agnivasa,
        "agnivasa_2": "",
        "nakshatra_shool": "None",
        "chandra_vasa": "East" if tithi_num in [1,6,11] else "South",
        "shivavasa_1": f"on {shivavasa}",
        "shivavasa_2": "",
        "rahu_vasa": "South-West",
        "kumbha_chakra": "West"
    }

def get_epoch_details(jd, dt):
    ayanamsha = swe.get_ayanamsa(jd)
    kaliyuga_year = dt.year + 3101
    shaka_year = dt.year - 78
    mjd = jd - 2400000.5
    ahargana = int(jd - 588465.5)
    return {
        "kaliyuga": f"{kaliyuga_year} Years",
        "ayanamsha": f"{ayanamsha:.6f}",
        "kali_ahargana": f"{ahargana} Days",
        "rata_die": f"{int(jd - 1721424.5)}",
        "julian_date": dt.strftime("%B %d, %Y CE"),
        "julian_day": f"{jd:.2f}",
        "civil_date": f"{dt.strftime('%d %B')}, {shaka_year} Shaka",
        "mjd": f"{mjd:.2f}",
        "nirayana_date": f"{dt.strftime('%d %B')}, {shaka_year} Shaka"
    }

def get_chandrabalam_tarabalam_details(moon_rashi_idx, day_nak_idx):
    good_rashis = []
    for r_idx, r_name in enumerate(RASHIS):
        diff = (moon_rashi_idx - r_idx) % 12 + 1
        if diff not in [6, 8, 12]:
            good_rashis.append({"name": r_name.split(' ')[0], "icon": RASHI_ICONS[r_name]})
            
    good_naks = []
    for n_idx, n_name in enumerate(NAKSHATRAS):
        dist = (day_nak_idx - n_idx) % 9 + 1
        if dist in [2, 4, 6, 8, 9]:
            good_naks.append({"name": n_name, "icon": NAK_ICONS.get(n_name, "")})
            
    return {
        "chandrabalam": {
            "good_rashis": good_rashis,
            "ashtama_chandra": ["Ashtama Chandra check required"]
        },
        "tarabalam": {
            "period_1": {"time": "Whole Day", "nakshatras": good_naks},
            "period_2": {"time": "", "nakshatras": []}
        }
    }

def get_panchaka_rahita_details(lagnas, tithi_idx, nak_idx, weekday_idx):
    panchaka_list = []
    V_WEEKDAY = {6:1, 0:2, 1:3, 2:4, 3:5, 4:6, 5:7}
    v_wd = V_WEEKDAY[weekday_idx]
    tithi_num = tithi_idx + 1
    nak_num = nak_idx + 1
    
    for lagna in lagnas:
        rashi_name = lagna['name']
        for i, r in enumerate(RASHIS):
            if r.startswith(rashi_name):
                lagna_num = i + 1
                break
        
        total = tithi_num + v_wd + nak_num + lagna_num
        remainder = total % 9
        
        if remainder == 1: status, label = False, "Mrityu Panchaka"
        elif remainder == 2: status, label = False, "Agni Panchaka"
        elif remainder == 4: status, label = False, "Raja Panchaka"
        elif remainder == 6: status, label = False, "Chora Panchaka"
        elif remainder == 8: status, label = False, "Roga Panchaka"
        else: status, label = True, "Good Muhurta"
        
        panchaka_list.append({
            "label": label,
            "times": f"{lagna['start']} to {lagna['end']}",
            "is_good": status
        })
    return panchaka_list

def get_udaya_lagna_details(jd_start, jd_end, tz, lat, lon):
    lagnas = []
    swe.set_ephe_path(EPHEMERIS_PATH)
    swe.set_sid_mode(SIDEREAL_MODE)
    curr_jd = jd_start
    last_sign_idx = -1
    lagna_start_jd = jd_start
    step = 1.0 / (24 * 60) 

    while curr_jd < jd_end:
        try:
            trop_asc = swe.houses(curr_jd, lat, lon, b'P')[0][0]
            ayan = swe.get_ayanamsa(curr_jd)
            sid_asc = (trop_asc - ayan) % 360
            curr_sign_idx = int(sid_asc / 30)

            if last_sign_idx != -1 and curr_sign_idx != last_sign_idx:
                rashi_name = RASHIS[last_sign_idx]
                icon = RASHI_ICONS.get(rashi_name, "")
                lagnas.append({
                    "name": rashi_name.split(' ')[0], 
                    "icon": icon,
                    "start": dt_from_jd(lagna_start_jd, tz).strftime("%I:%M %p"),
                    "end": dt_from_jd(curr_jd, tz).strftime("%I:%M %p")
                })
                lagna_start_jd = curr_jd
            last_sign_idx = curr_sign_idx
        except: pass
        curr_jd += step

    if last_sign_idx != -1:
        rashi_name = RASHIS[last_sign_idx]
        icon = RASHI_ICONS.get(rashi_name, "")
        lagnas.append({
            "name": rashi_name.split(' ')[0],
            "icon": icon,
            "start": dt_from_jd(lagna_start_jd, tz).strftime("%I:%M %p"),
            "end": dt_from_jd(jd_end, tz).strftime("%I:%M %p")
        })
    return lagnas

def get_festivals_details(jd, tithi_idx, sun_long, dt_obj, nak_idx, moon_rashi_idx):
    paksha_code = 0 if tithi_idx < 15 else 1
    tithi_in_paksha = tithi_idx % 15
    sun_sign_idx = int(sun_long / 30)
    lunar_month_idx = (sun_sign_idx + 1) % 12 
    
    festivals = []
    
    def get_image_url(name):
        for key, url in FESTIVAL_IMAGES_STATIC.items():
            if key in name:
                return url
        seed = sum(ord(c) for c in name)
        safe_name = urllib.parse.quote(name)
        return f"https://image.pollinations.ai/prompt/Hindu%20festival%20{safe_name}%20devotional%20art?width=300&height=200&nologo=true&seed={seed}"

    def add_fest(name):
        if not any(f['name'] == name for f in festivals):
            festivals.append({"name": name, "image_url": get_image_url(name)})

    # 1. Tithi Based (Static DB)
    key = (lunar_month_idx, paksha_code, tithi_in_paksha)
    if key in FESTIVAL_DB: add_fest(FESTIVAL_DB[key])
        
    # 2. Gregorian DB
    greg_key = (dt_obj.month, dt_obj.day)
    if greg_key in GREGORIAN_FESTIVALS: add_fest(GREGORIAN_FESTIVALS[greg_key])
        
    # 3. Recurring Upavas Logic (The "All Upavas" Part)
    # Vinayaka Chaturthi: Shukla (0), Tithi 3 (4th tithi)
    if paksha_code == 0 and tithi_in_paksha == 3: add_fest("Vinayaka Chaturthi")
    
    # Sankashti Chaturthi: Krishna (1), Tithi 3 (4th tithi)
    if paksha_code == 1 and tithi_in_paksha == 3: add_fest("Sankashti Chaturthi")
    
    # Skanda Sashti: Shukla (0), Tithi 5 (6th tithi)
    if paksha_code == 0 and tithi_in_paksha == 5: add_fest("Skanda Sashti")
    
    # Masik Durgashtami: Shukla (0), Tithi 7 (8th tithi)
    if paksha_code == 0 and tithi_in_paksha == 7: add_fest("Masik Durgashtami")
    
    # Kalashtami: Krishna (1), Tithi 7 (8th tithi)
    if paksha_code == 1 and tithi_in_paksha == 7: add_fest("Kalashtami")
    
    # Ekadashi: Tithi 10 (11th tithi) - Both Pakshas
    if tithi_in_paksha == 10:
        prefix = "Shukla" if paksha_code == 0 else "Krishna"
        add_fest(f"{prefix} Ekadashi")
        
    # Pradosh Vrat: Tithi 12 (13th tithi) - Both Pakshas
    if tithi_in_paksha == 12: add_fest("Pradosh Vrat")
    
    # Masik Shivaratri: Krishna (1), Tithi 13 (14th tithi)
    if paksha_code == 1 and tithi_in_paksha == 13: add_fest("Masik Shivaratri")
    
    # Amavasya: Tithi 29 (30th tithi - Index 14 in Krishna, but careful with array)
    if paksha_code == 1 and tithi_in_paksha == 14: add_fest("Amavasya / Darsha Amavasya")
    
    # Purnima: Shukla 14
    if paksha_code == 0 and tithi_in_paksha == 14: add_fest("Purnima / Satyanarayan Puja")
    
    # Karthigai: Krittika Nakshatra (Index 2)
    if nak_idx == 2: add_fest("Masik Karthigai")
    
    # Rohini Vrat: Rohini Nakshatra (Index 3)
    if nak_idx == 3: add_fest("Rohini Vrat")

    return festivals

# --- Main Fetch Function ---
def fetch_panchang(loc_str, date_str):
    setup_swisseph()
    loc = get_location(loc_str)
    if not loc: return {"error": "Location not found"}
    
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    tz = loc['tz']
    jd_noon = jd_from_dt(tz.localize(datetime(dt.year, dt.month, dt.day, 12, 0)))
    
    rise, set_ = calc_sun_rise_set(jd_noon, loc['lat'], loc['lon'])
    moon_rise, moon_set = calc_moon_rise_set(jd_noon, loc['lat'], loc['lon'])
    rise_next, _ = calc_sun_rise_set(jd_noon + 1, loc['lat'], loc['lon'])
    
    sun_long, moon_long = get_pos(rise)
    
    moon_rashi_idx = int(moon_long / 30)
    sun_rashi_idx = int(sun_long / 30)
    w_idx = dt_from_jd(rise, tz).weekday()

    samvat = get_samvat_details(dt)
    ritu_ayana = get_ritu_ayana_details(rise)
    muhurtas = calculate_muhurtas(rise, set_, rise_next, w_idx)
    
    tithi_idx = int(((moon_long - sun_long) % 360) / 12)
    nak_idx = int(moon_long / 13.333333)
    sun_nak_idx = int(sun_long / 13.333333)
    
    nivas_shool = get_nivas_shool_details(jd_noon, w_idx, tithi_idx, nak_idx)
    epoch = get_epoch_details(jd_noon, dt)
    chandrabalam_tarabalam = get_chandrabalam_tarabalam_details(moon_rashi_idx, nak_idx)
    
    udaya_lagna = get_udaya_lagna_details(rise, rise_next, tz, loc['lat'], loc['lon'])
    panchaka_rahita = get_panchaka_rahita_details(udaya_lagna, tithi_idx, nak_idx, w_idx)
    
    # PASS EXTRA ARGS TO FESTIVAL FUNCTION
    festivals = get_festivals_details(rise, tithi_idx, sun_long, dt, nak_idx, moon_rashi_idx)
    
    dinamana = fmt_duration(rise, set_)
    ratrimana = fmt_duration(set_, rise_next)
    madhyahna_jd = rise + (set_ - rise) / 2

    def fmt_time_smart(jd):
        if not jd: return "---"
        d = dt_from_jd(jd, tz)
        if d.date() != dt.date(): return d.strftime("%I:%M %p, %d %b")
        return d.strftime("%I:%M %p")
        
    def fmt_range(start, end):
        return f"{fmt_time_smart(start)} - {fmt_time_smart(end)}"

    fn_tithi = lambda j: (int((get_pos(j)[1] - get_pos(j)[0]) % 360 / 12), 0)
    fn_nak = lambda j: (int(get_pos(j)[1] / 13.333333333), 0)
    fn_yoga = lambda j: (int((get_pos(j)[1] + get_pos(j)[0]) % 360 / 13.333333333), 0)
    fn_karana = lambda j: (int((get_pos(j)[1] - get_pos(j)[0]) % 360 / 6), 0)
    
    fn_moon_pada = lambda j: (int(get_pos(j)[1] / 3.333333333), 0)
    fn_sun_pada = lambda j: (int(get_pos(j)[0] / 3.333333333), 0)
    
    tithi_events = get_events(rise, rise_next, fn_tithi, TITHIS, 30)
    nak_events = get_events(rise, rise_next, fn_nak, NAKSHATRAS, 27)
    
    calc_timings = get_calculated_timings(nak_events, w_idx, sun_nak_idx)
    nk_start = nak_events[0]['start']

    data = {
        "meta": {
            "location": loc['name'],
            "date": dt_from_jd(rise, tz).strftime("%A, %d %B %Y"),
            "sunrise": fmt_time_smart(rise),
            "sunset": fmt_time_smart(set_),
            "moonrise": fmt_time_smart(moon_rise),
            "moonset": fmt_time_smart(moon_set),
        },
        "details": {
            "moonsign": RASHIS[moon_rashi_idx],
            "sunsign": RASHIS[sun_rashi_idx],
            "samvat": samvat,
            "ritu_ayana": ritu_ayana,
            "dinamana": dinamana,
            "ratrimana": ratrimana,
            "madhyahna": fmt_time_smart(madhyahna_jd),
            "nivas_shool": nivas_shool,
            "epoch": epoch,
            "chandrabalam_tarabalam": chandrabalam_tarabalam,
            "panchaka_rahita": panchaka_rahita,
            "udaya_lagna": udaya_lagna,
            "festivals": festivals
        },
        "tithi": tithi_events,
        "nakshatra": nak_events,
        "yoga": get_events(rise, rise_next, fn_yoga, YOGAS, 27),
        "karana": get_events(rise, rise_next, fn_karana, [], 60, True),
        "moon_pada": get_events(rise, rise_next, fn_moon_pada, PADA_NAMES, 108),
        "sun_pada": get_events(rise, rise_next, fn_sun_pada, PADA_NAMES, 108),
        "timings": {
            "brahma": fmt_range(*muhurtas["brahma"]),
            "pratah": fmt_range(*muhurtas["pratah"]),
            "vijaya": fmt_range(*muhurtas["vijaya"]),
            "godhuli": fmt_range(*muhurtas["godhuli"]),
            "sayahna": fmt_range(*muhurtas["sayahna"]),
            "nishita": fmt_range(*muhurtas["nishita"]),
            "dur_day": ", ".join([fmt_range(s, e) for s, e in muhurtas["dur_day"]]),
            "sarvartha": calc_timings["sarvartha"],
            "baana": calc_timings["baana"],
            "vidaal": calc_timings["vidaal"],
            "anandadi": calc_timings["anandadi"],
            "tamil": calc_timings["tamil"],
            "jeevanama": calc_timings["jeevanama"],
            "netrama": calc_timings["netrama"]
        }
    }
    
    if isinstance(muhurtas["abhijit"], tuple):
        data["timings"]["abhijit"] = fmt_range(*muhurtas["abhijit"])
    else:
        data["timings"]["abhijit"] = muhurtas["abhijit"]
    
    def fmt_dt(jd): return dt_from_jd(jd, tz).strftime("%I:%M %p, %d %b") if jd else "..."
    
    for item in data['tithi']:
        item['start_fmt'] = fmt_dt(item['start'])
        item['end_fmt'] = fmt_dt(item['end'])
        item['icon'] = TITHI_ICONS.get(item['name'], "🌑")

    for item in data['nakshatra']:
        item['start_fmt'] = fmt_dt(item['start'])
        item['end_fmt'] = fmt_dt(item['end'])
        item['icon'] = NAK_ICONS.get(item['name'], "✨")

    for k in ['yoga', 'karana', 'moon_pada', 'sun_pada']:
        for item in data[k]:
            item['start_fmt'] = fmt_dt(item['start'])
            item['end_fmt'] = fmt_dt(item['end'])

    day_len = set_ - rise
    def get_kalam(k_map):
        s = rise + ((k_map[w_idx]-1) * (day_len/8))
        return f"{dt_from_jd(s, tz).strftime('%I:%M %p')} - {dt_from_jd(s + day_len/8, tz).strftime('%I:%M %p')}"
        
    data['timings']['rahu'] = get_kalam(RAHU_KEY)
    data['timings']['yama'] = get_kalam(YAMA_KEY)
    data['timings']['guli'] = get_kalam(GULI_KEY)
    
    v_s = nk_start + (VARJYAM_STARTS[nak_idx]/60.0)
    data['timings']['varjyam'] = f"{dt_from_jd(v_s, tz).strftime('%I:%M %p')} - {dt_from_jd(v_s + 4/60.0, tz).strftime('%I:%M %p')}"
    a_s = nk_start + (AMRIT_STARTS[nak_idx]/60.0)
    data['timings']['amrit'] = f"{dt_from_jd(a_s, tz).strftime('%I:%M %p')} - {dt_from_jd(a_s + 4/60.0, tz).strftime('%I:%M %p')}"

    return data