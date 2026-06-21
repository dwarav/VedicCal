import swisseph as swe
from datetime import datetime, timedelta
import pytz
import copy

from ..config import EPHEMERIS_PATH, SIDEREAL_MODE
from ..constants.mappings import (
    RASHIS, NAKSHATRAS, TITHIS, YOGAS, KARANAS,
    DASHA_ORDER, DASHA_YEARS, CHALDEAN_MAP, NUMEROLOGY_DATA,
    RASI_LORDS_MAP, NAK_LORDS, PLANET_RELATIONSHIPS,
    NAMA_AKSHARA, GANAS, YONIS, NADIS, VARNA, VASHYA, TATVA
)
from ..constants.astrology import (
    KUNDLI_PREDICTIONS, FAV_POINTS, RASHI_ICONS, NAK_ICONS, PLANET_ICONS, TITHI_ICONS
)
from .core import (
    setup_swisseph, jd_from_dt, dt_from_jd, calc_sun_rise_set, 
    get_pos, get_samvat_details, find_trans
)

# ================= SHODASHVARGA CALCULATIONS =================
def get_varga_sign(degree, rashi_idx, varga_num):
    """
    Calculates the sign index in a specific Varga (Divisional Chart) for a given planetary position.
    
    Args:
        degree (float): Degree of the planet within the sign (0-30).
        rashi_idx (int): Rashi index (0-11).
        varga_num (int): The division number (e.g., 9 for Navamsa, 7 for Saptamsa).
        
    Returns:
        int: The resulting sign index (0-11) in the divisional chart.
    """
    quality = rashi_idx % 3 
    is_odd = (rashi_idx % 2 == 0) # 0=Aries (Odd), 1=Taurus (Even)
    
    if varga_num == 1: return rashi_idx
    if varga_num == 2: # Hora (Parivritti / Cyclic)
        # Each sign has 2 Horas of 15 degrees each.
        # They cycle continuously from Aries.
        hora_idx = 0 if degree < 15 else 1
        # Formula: (Sign Index * 2) + Hora Index
        start_sign = (rashi_idx * 2) + hora_idx
        return start_sign % 12
    if varga_num == 3: # Drekkana
        part = int(degree / 10) 
        return (rashi_idx + (part * 4)) % 12
    if varga_num == 4: # Chaturthamsha
        part = int(degree / 7.5) 
        return (rashi_idx + (part * 3)) % 12
    if varga_num == 7: # Saptamsha
        part = int(degree / (30/7))
        start_sign = rashi_idx if is_odd else (rashi_idx + 6)
        return (start_sign + part) % 12
    if varga_num == 9: # Navamsa
        part = int(degree / (30/9)) # 3 deg 20 min
        if quality == 0: start = rashi_idx # Moveable
        elif quality == 1: start = (rashi_idx + 8) % 12 # Fixed
        else: start = (rashi_idx + 4) % 12 # Dual
        return (start + part) % 12
    if varga_num == 10: # Dashamsha
        part = int(degree / 3)
        start = rashi_idx if is_odd else (rashi_idx + 8)
        return (start + part) % 12
    if varga_num == 12: # Dwadashamsha
        part = int(degree / 2.5)
        return (rashi_idx + part) % 12
    if varga_num == 16: # Shodashamsha
        part = int(degree / (30/16))
        if quality == 0: start = 0 # Aries
        elif quality == 1: start = 4 # Leo
        else: start = 8 # Sagittarius
        return (start + part) % 12
    if varga_num == 20: # Vimshamsha
        part = int(degree / (30/20))
        if quality == 0: start = 0 # Moveable -> Aries
        elif quality == 1: start = 8 # Fixed -> Sagittarius
        else: start = 4 # Dual -> Leo
        return (start + part) % 12
    if varga_num == 24: # Chaturvimshamsha
        part = int(degree / (30/24))
        start = 4 if is_odd else 3 # Leo / Cancer
        return (start + part) % 12
    if varga_num == 27: # Saptavimshamsha or Bhamsa
        part = int(degree / (30/27))
        start = 0 if is_odd else 3 # Aries / Cancer
        return (start + part) % 12
    if varga_num == 30: # Trimshamsha
        d = degree
        if is_odd:
            if d < 5: return 0 # Mars
            elif d < 10: return 10 # Saturn
            elif d < 18: return 8 # Jupiter
            elif d < 25: return 2 # Mercury
            else: return 6 # Venus
        else:
            if d < 5: return 1 # Venus
            elif d < 12: return 5 # Mercury
            elif d < 20: return 11 # Jupiter
            elif d < 25: return 9 # Saturn
            else: return 7 # Mars
    if varga_num == 40: # Khavedamsha
        part = int(degree / (30/40))
        start = 0 if is_odd else 6 # Aries / Libra
        return (start + part) % 12
    if varga_num == 45: # Akshavedamsha
        part = int(degree / (30/45))
        if quality == 0: start = 0
        elif quality == 1: start = 4
        else: start = 8
        return (start + part) % 12
    if varga_num == 60: # Shashtiamsha
        part = int(degree / 0.5)
        return (rashi_idx + part) % 12
    return rashi_idx 

# --- NUMEROLOGY & HOROSCOPE CALCULATION ---
def get_numerology(dob, name):
    """
    Calculates numerology numbers: Radical (Birth Day), Destiny (Full Date), and Name Number.
    """
    day = dob.day
    while day > 9: day = sum(int(d) for d in str(day))
    radical_num = day
    total_sum = sum(int(d) for d in dob.strftime("%d%m%Y"))
    while total_sum > 9: total_sum = sum(int(d) for d in str(total_sum))
    destiny_num = total_sum
    name_sum = 0
    if name:
        for char in name.upper():
            if char in CHALDEAN_MAP:
                name_sum += CHALDEAN_MAP[char]
    while name_sum > 9: name_sum = sum(int(d) for d in str(name_sum))
    name_num = name_sum
    evil_num = NUMEROLOGY_DATA[radical_num]["enemy"]
    neutral_num = NUMEROLOGY_DATA[radical_num]["neutral"]
    friendly_num = NUMEROLOGY_DATA[radical_num]["friend"]
    radical_ruler = NUMEROLOGY_DATA[radical_num]["ruler"]
    return {"radical_num": radical_num, "destiny_num": destiny_num, "name_num": name_num, "evil_num": evil_num, "neutral_num": neutral_num, "friendly_num": friendly_num, "radical_ruler": radical_ruler}

# --- DOSHA CALCULATION ---
def calculate_doshas(planet_positions, lagna_rashi, moon_rashi):
    """
    Checks for common doshas like Mangal Dosha, Kalsarpa Dosha, and Pitra Dosha.
    """
    p_houses = {p['planet']: p['house'] for p in planet_positions}
    dosha_report = []
    
    # Mangal Dosha Check
    mars_house = p_houses.get('Mars')
    if mars_house in [1, 2, 4, 7, 8, 12]:
        dosha_report.append({"name": "Mangal Dosha", "status": "Present", "desc": "Mars is placed in a sensitive house (1, 2, 4, 7, 8, 12). This may cause delays or disharmony in marriage.", "remedy": "Perform Kumbh Vivah or worship Lord Hanuman."})
    else:
        dosha_report.append({ "name": "Mangal Dosha", "status": "Absent", "desc": "No Mangal Dosha present.", "remedy": "None needed." })
        
    # Kalsarpa Dosha (Simplified Check)
    dosha_report.append({ "name": "Kalsarpa Dosha", "status": "Absent", "desc": "Planets are not hemmed between Rahu and Ketu.", "remedy": "None needed." })
    
    # Pitra Dosha Check
    sun_h = p_houses.get('Sun')
    moon_h = p_houses.get('Moon')
    rahu_h = p_houses.get('Rahu')
    ketu_h = p_houses.get('Ketu')
    is_pitra = False
    if sun_h == 9 or moon_h == 9: is_pitra = True
    if sun_h == rahu_h or sun_h == ketu_h: is_pitra = True
    if moon_h == rahu_h or moon_h == ketu_h: is_pitra = True
    if is_pitra:
        dosha_report.append({"name": "Pitra Dosha", "status": "Present", "desc": "Sun/Moon afflicted by Nodes or 9th house affliction indicates ancestral debt.", "remedy": "Perform Shradh/Tarpan for ancestors or donate food on Amavasya."})
    else:
        dosha_report.append({ "name": "Pitra Dosha", "status": "Absent", "desc": "No major Pitra Dosha detected.", "remedy": "None needed." })
    return dosha_report

# --- DASHA CALCULATION ---
def get_formatted_duration(total_days):
    """Formats days into Years, Months, Days string."""
    years = int(total_days / 365.25)
    remaining_days = total_days % 365.25
    months = int(remaining_days / 30.44)
    days = int(remaining_days % 30.44)
    parts = []
    if years > 0: parts.append(f"{years}y")
    if months > 0: parts.append(f"{months}m")
    if days > 0: parts.append(f"{days}d")
    return " ".join(parts) if parts else "0d"

def calculate_antardashas(mahadasha_lord, mahadasha_start_date, birth_date=None):
    """
    Calculates Antardashas (Sub-periods) for a given Mahadasha.
    """
    sub_periods = []
    start_idx = DASHA_ORDER.index(mahadasha_lord)
    current_sub_date = mahadasha_start_date
    m_years = DASHA_YEARS[mahadasha_lord]
    for i in range(9):
        sub_lord_idx = (start_idx + i) % 9
        sub_lord = DASHA_ORDER[sub_lord_idx]
        s_years = DASHA_YEARS[sub_lord]
        days_duration = (m_years * s_years * 365.25) / 120.0
        end_sub_date = current_sub_date + timedelta(days=days_duration)
        
        # Adjust for birth date (don't show periods before birth)
        if birth_date:
            if end_sub_date < birth_date:
                current_sub_date = end_sub_date
                continue 
            if current_sub_date < birth_date:
                actual_start = birth_date
                actual_duration = (end_sub_date - actual_start).days
                sub_periods.append({"lord": sub_lord, "start": actual_start.strftime("%d-%b-%Y"), "end": end_sub_date.strftime("%d-%b-%Y"), "duration": get_formatted_duration(actual_duration)})
                current_sub_date = end_sub_date
                continue
        sub_periods.append({"lord": sub_lord, "start": current_sub_date.strftime("%d-%b-%Y"), "end": end_sub_date.strftime("%d-%b-%Y"), "duration": get_formatted_duration(days_duration)})
        current_sub_date = end_sub_date
    return sub_periods

def calculate_vimshottari_dasha(moon_long, birth_date):
    """
    Calculates Vimshottari Dasha periods starting from birth.
    
    Args:
        moon_long (float): Moon's longitude at birth.
        birth_date (datetime): Birth datetime.
        
    Returns:
        list: List of Mahadasha dictionaries with Antardasha details.
    """
    nak_span = 13.333333333333333
    nak_idx = int(moon_long / nak_span)
    degrees_in_nak = moon_long % nak_span
    fraction_passed = degrees_in_nak / nak_span
    
    # Current Dasha Lord at birth
    dasha_lord_idx = nak_idx % 9
    start_lord = DASHA_ORDER[dasha_lord_idx]
    total_years = DASHA_YEARS[start_lord]
    years_passed = total_years * fraction_passed
    years_remaining = total_years - years_passed
    
    # Calculate start date of the current Mahadasha (before birth)
    theoretical_start_days = years_passed * 365.25
    theoretical_start_date = birth_date - timedelta(days=theoretical_start_days)
    first_dasha_end_date = theoretical_start_date + timedelta(days=total_years * 365.25)
    
    dasha_list = []
    # First Dasha (from birth to end of period)
    dasha_list.append({"lord": start_lord, "start": birth_date.strftime("%d-%b-%Y"), "end": first_dasha_end_date.strftime("%d-%b-%Y"), "duration": get_formatted_duration(years_remaining * 365.25), "antardashas": calculate_antardashas(start_lord, theoretical_start_date, birth_date=birth_date)})
    
    current_date = first_dasha_end_date
    # Next Dashas
    for i in range(1, 9):
        next_idx = (dasha_lord_idx + i) % 9
        lord = DASHA_ORDER[next_idx]
        duration_years = DASHA_YEARS[lord]
        end_date = current_date + timedelta(days=duration_years * 365.25)
        dasha_list.append({"lord": lord, "start": current_date.strftime("%d-%b-%Y"), "end": end_date.strftime("%d-%b-%Y"), "duration": f"{duration_years} Years", "antardashas": calculate_antardashas(lord, current_date)})
        current_date = end_date
    return dasha_list

def get_sudarshana_chakra(planetary_positions, lagna_rashi_idx, moon_rashi_idx, sun_rashi_idx):
    """
    Constructs the Sudarshana Chakra (Comparison of Lagna, Moon, and Sun charts).
    """
    charts = {}
    def build_chart(reference_sign_idx):
        chart = {str(i): [] for i in range(1, 13)} 
        for planet in planetary_positions:
            try:
                p_rasi_idx = RASHIS.index(planet['rasi'])
                house_num = (p_rasi_idx - reference_sign_idx + 12) % 12 + 1
                chart[str(house_num)].append(planet['symbol']) 
            except Exception: pass
        return chart
    charts['lagna_chart'] = build_chart(lagna_rashi_idx)
    charts['moon_chart'] = build_chart(moon_rashi_idx)
    charts['sun_chart'] = build_chart(sun_rashi_idx)
    return charts

def get_planet_relationship(planet_name, rasi_lord, rasi_idx):
    """
    Determines if a planet is in Friend's, Enemy's, or Neutral sign
    based on Naisargika Mitra (Natural Friendship).
    """
    if planet_name == 'Ascendant': return '-'
    if planet_name not in PLANET_RELATIONSHIPS: return 'Neutral'
    own_signs = {'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5], 'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10], 'Rahu': [10], 'Ketu': [7]}
    if rasi_idx in own_signs.get(planet_name, []): return 'Own Sign'
    rels = PLANET_RELATIONSHIPS[planet_name]
    if rasi_lord in rels['Friends']: return 'Friend'
    if rasi_lord in rels['Enemies']: return 'Enemy'
    return 'Neutral'

def get_horoscope_by_birth_details(loc, date_str, time_str, name=""):
    """
    Main function to generate a full horoscope.
    
    Args:
        loc (dict): Location details.
        date_str (str): Birth date YYYY-MM-DD.
        time_str (str): Birth time HH:MM.
        name (str, optional): Name of the person.
        
    Returns:
        dict: Complete Kundli data including charts, planetary info, dashas, prediction, etc.
    """
    setup_swisseph()
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except Exception: return None
    tz = loc['tz']
    local_dt = tz.localize(dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    planet_map = {0: swe.SUN, 1: swe.MOON, 2: swe.MARS, 3: swe.MERCURY, 4: swe.JUPITER, 5: swe.VENUS, 6: swe.SATURN, 7: swe.MEAN_NODE, 8: swe.MEAN_NODE, 9: swe.URANUS, 10: swe.NEPTUNE, 11: swe.PLUTO}
    chart_data = {i: [] for i in range(12)} 
    navamsa_chart_data = {i: [] for i in range(12)}
    planetary_positions = [] 
    
    # Calculate Lagna (Ascendant)
    cusps, ascmc = swe.houses(jd, loc['lat'], loc['lon'], b'P')
    lagna_deg = ascmc[0]
    lagna_rashi = int(lagna_deg / 30)
    chart_data[lagna_rashi].append("Lagna")
    
    # Navamsa of Lagna — use the correct varga formula, same as planets
    lagna_navamsa_rashi = get_varga_sign(lagna_deg % 30, lagna_rashi, 9)
    navamsa_chart_data[lagna_navamsa_rashi].append("Lagna")
    
    def deg_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = int(((deg - d) * 60 - m) * 60)
        return f"{d:02d}° {m:02d}' {s:02d}\""
    def get_nak(long):
        nak_deg = 13.333333333333333
        idx = int(long / nak_deg)
        pada = int((long % nak_deg) / 3.333333333333333) + 1
        return NAKSHATRAS[idx], pada, idx
    
    moon_long = 0
    lnak, lpada, lnak_idx = get_nak(lagna_deg)
    
    # Calculate Shodashvarga for Lagna
    lagna_vargas = {}
    for v_num in [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]:
        v_sign_idx = get_varga_sign(lagna_deg % 30, lagna_rashi, v_num)
        lagna_vargas[f"D{v_num}"] = {"sign": RASHIS[v_sign_idx], "sign_id": v_sign_idx}
    planetary_positions.append({"planet": "Ascendant", "icon": "Asc", "symbol": "As", "is_retro": False, "position": deg_to_dms(lagna_deg), "degree": deg_to_dms(lagna_deg % 30), "rasi": RASHIS[lagna_rashi], "rasi_lord": RASI_LORDS_MAP[lagna_rashi], "nakshatra": f"{lnak} ({lpada})", "nak_lord": NAK_LORDS[lnak_idx % 9], "house": 1, "relationship": "-", "vargas": lagna_vargas})
    
    # Calculate Planet Positions
    p_names = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto"]
    p_symbols = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke", "Ur", "Ne", "Pl"]
    for i in range(12):
        body = planet_map[i]
        res = swe.calc_ut(jd, body, flags)
        deg = res[0][0]
        speed = res[0][3]
        is_retro = True if speed < 0 else False
        if i in [7, 8]: is_retro = True 
        if i == 8: deg = (deg + 180) % 360 # Ketu is opposite Rahu
        if i == 1: moon_long = deg
        
        rashi = int(deg / 30)
        p_name = p_names[i]
        chart_data[rashi].append(p_name)
        
        # Navamsa
        total_minutes = deg * 60
        navamsa_rashi_idx = int(total_minutes / 200) % 12
        navamsa_chart_data[navamsa_rashi_idx].append(p_name)
        
        nak, pada, nak_idx = get_nak(deg)
        house_num = (rashi - lagna_rashi + 12) % 12 + 1
        
        vargas = {}
        for v_num in [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]:
            v_sign_idx = get_varga_sign(deg % 30, rashi, v_num)
            vargas[f"D{v_num}"] = {"sign": RASHIS[v_sign_idx], "sign_id": v_sign_idx}
        planetary_positions.append({"planet": p_name, "icon": PLANET_ICONS.get(p_name, ""), "symbol": p_symbols[i], "is_retro": is_retro, "position": deg_to_dms(deg), "degree": deg_to_dms(deg % 30), "rasi": RASHIS[rashi], "rasi_lord": RASI_LORDS_MAP[rashi], "nakshatra": f"{nak} ({pada})", "nak_lord": NAK_LORDS[nak_idx % 9], "house": house_num, "relationship": get_planet_relationship(p_name, RASI_LORDS_MAP[rashi], rashi), "vargas": vargas})

    # Moon Chart
    moon_rashi_idx = int(moon_long / 30)
    chandra_chart_data = copy.deepcopy(chart_data)
    if "Lagna" in chandra_chart_data[lagna_rashi]: chandra_chart_data[lagna_rashi].remove("Lagna")
    chandra_chart_data[moon_rashi_idx].append("Lagna (Mo)")
    
    # Birth Details
    nak_idx = int(moon_long / 13.333333333333333)
    pada = int((moon_long % 13.333333333333333) / 3.333333333333333) + 1
    nak_str = f"{NAKSHATRAS[nak_idx]} ({pada} Pada)"
    def get_sign_start_end(jd_center, body_id, current_sign_idx, tz):
        target_next = (current_sign_idx + 1) % 12
        def check_sign_idx(t):
            pos = swe.calc_ut(t, body_id, flags)[0][0]
            return (int(pos / 30), 0)
        exit_jd = find_trans(jd_center, check_sign_idx, target_next)
        days_back = 35 if body_id == swe.SUN else 4
        search_start = jd_center - days_back
        entry_jd = find_trans(search_start, check_sign_idx, current_sign_idx)
        entry_str = dt_from_jd(entry_jd, tz).strftime("%d %b %Y, %I:%M %p") if entry_jd else "---"
        exit_str = dt_from_jd(exit_jd, tz).strftime("%d %b %Y, %I:%M %p") if exit_jd else "---"
        return entry_str, exit_str
    
    def get_nak_start_end(jd_center, current_nak_idx, tz):
        search_start = jd_center - 2.0
        def check_nak_idx(t):
            pos = swe.calc_ut(t, swe.MOON, flags)[0][0]
            return (int(pos / 13.333333333), 0)
        entry_jd = find_trans(search_start, check_nak_idx, current_nak_idx)
        next_nak = (current_nak_idx + 1) % 27
        exit_jd = find_trans(jd_center, check_nak_idx, next_nak)
        entry_str = dt_from_jd(entry_jd, tz).strftime("%d %b %Y, %I:%M %p") if entry_jd else "---"
        exit_str = dt_from_jd(exit_jd, tz).strftime("%d %b %Y, %I:%M %p") if exit_jd else "---"
        return entry_str, exit_str
        
    sun_long = swe.calc_ut(jd, swe.SUN, flags)[0][0]
    sun_rashi_idx = int(sun_long / 30)
    
    moon_entry, moon_exit = get_sign_start_end(jd, swe.MOON, moon_rashi_idx, tz)
    sun_entry, sun_exit = get_sign_start_end(jd, swe.SUN, sun_rashi_idx, tz)
    nak_entry, nak_exit = get_nak_start_end(jd, nak_idx, tz)
    timings = {"moon_sign_start": moon_entry, "moon_sign_end": moon_exit, "sun_sign_start": sun_entry, "sun_sign_end": sun_exit, "nak_start": nak_entry, "nak_end": nak_exit}
    
    ayan_val = swe.get_ayanamsa(jd)
    d = int(ayan_val); m = int((ayan_val - d) * 60); s = int(((ayan_val - d) * 60 - m) * 60)
    ayan_str = f"{d}° {m}' {s}\" (Lahiri)"
    
    gana_idx = 0 if nak_idx in GANAS["Deva"] else 1 if nak_idx in GANAS["Manushya"] else 2
    gana = ["Deva", "Manushya", "Rakshasa"][gana_idx]
    yoni = YONIS[nak_idx % 27]
    nadi_type = "Adi (Vata)" if nak_idx in NADIS["Adi (Vata)"] else "Madhya (Pitta)" if nak_idx in NADIS["Madhya (Pitta)"] else "Antya (Kapha)"
    moon_rashi_idx = int(moon_long / 30)
    varna = VARNA[moon_rashi_idx]
    vashya = VASHYA[moon_rashi_idx]
    tithi_idx_b = int(((moon_long - sun_long) % 360) / 12)
    birth_tithi = TITHIS[tithi_idx_b]
    samvat_details = get_samvat_details(dt)
    
    jd_noon = jd_from_dt(tz.localize(datetime(dt.year, dt.month, dt.day, 12, 0)))
    rise, set_ = calc_sun_rise_set(jd_noon, loc['lat'], loc['lon'])
    def fmt_time(jd_time):
        d = dt_from_jd(jd_time, tz)
        return d.strftime('%I:%M %p') if d else "---"
    sunrise_str = fmt_time(rise)
    sunset_str = fmt_time(set_)
    
    yoga_idx_b = int(((moon_long + sun_long) % 360) / 13.333333)
    birth_yoga = YOGAS[yoga_idx_b]
    
    karana_idx_b = int(((moon_long - sun_long) % 360) / 6)
    if karana_idx_b == 0: birth_karana = KARANAS[10]
    elif karana_idx_b >= 57: birth_karana = KARANAS[karana_idx_b - 50]
    else: birth_karana = KARANAS[(karana_idx_b - 1) % 7]
    
    tatva = TATVA[moon_rashi_idx]
    moon_house_num = (moon_rashi_idx - lagna_rashi + 12) % 12 + 1
    if moon_house_num in [1, 6, 11]: paya = "Gold (Swarna)"
    elif moon_house_num in [2, 5, 9]: paya = "Silver (Rajata)"
    elif moon_house_num in [3, 7, 10]: paya = "Copper (Tamra)"
    else: paya = "Iron (Loha)"
    
    if nak_idx < 9: yunja = "Poorva"
    elif nak_idx < 18: yunja = "Madhya"
    else: yunja = "Uttara"
    
    global_pada_idx = (nak_idx * 4) + (pada - 1)
    name_alphabet = NAMA_AKSHARA[global_pada_idx]
    
    nak_start_idx = nak_idx * 4
    nak_alphabets = NAMA_AKSHARA[nak_start_idx : nak_start_idx + 4]
    
    nak_lord = NAK_LORDS[nak_idx % 9]
    sign_lord = RASI_LORDS_MAP[moon_rashi_idx]
    lagna_lord = RASI_LORDS_MAP[lagna_rashi] 
    
    fav_data = FAV_POINTS.get(lagna_rashi, {})
    num_data = get_numerology(dt, name)
    fav_data.update(num_data)
    
    lagna_prediction = KUNDLI_PREDICTIONS.get(lagna_rashi, {"general": "", "career": "", "health": "", "marriage": ""})
    
    dasha_periods = calculate_vimshottari_dasha(moon_long, dt)
    dosha_details = calculate_doshas(planetary_positions, lagna_rashi, moon_rashi_idx)
    sudarshana_data = get_sudarshana_chakra(planetary_positions, lagna_rashi, moon_rashi_idx, sun_rashi_idx)
    
    kundli_details = {"gana": gana, "yoni": yoni, "nadi": nadi_type, "varna": varna, "vashya": vashya, "tithi": birth_tithi, "yoga": birth_yoga, "karana": birth_karana, "tatva": tatva, "paya": paya, "yunja": yunja, "name_alphabet": name_alphabet, "nak_alphabets": nak_alphabets, "nak_lord": nak_lord, "sign_lord": sign_lord, "fav": fav_data, "prediction": lagna_prediction, "timings": timings}
    
    kundali_table = []
    for h in range(1, 13):
        rashi_idx = (lagna_rashi + h - 1) % 12
        r_name = RASHIS[rashi_idx]
        r_lord = RASI_LORDS_MAP[rashi_idx]
        planets_in_house = [p for p in planetary_positions if p['house'] == h]
        kundali_table.append({"house": h, "rashi": r_name, "lord": r_lord, "planets": planets_in_house})
    
    shodashvarga_charts = {f"D{v}": {i: [] for i in range(12)} for v in [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]}
    for p in planetary_positions:
        p_name_display = p['planet']
        p_vargas = p.get('vargas', {})
        for v_key, v_data in p_vargas.items():
            if v_key in shodashvarga_charts:
                sign_idx = v_data['sign_id']
                shodashvarga_charts[v_key][sign_idx].append(p_name_display)
    
    varga_titles = {"D1": "Rashi (D1)", "D2": "Hora (D2)", "D3": "Drekkana (D3)", "D4": "Chaturthamsha (D4)", "D7": "Saptamsha (D7)", "D9": "Navamsa (D9)", "D10": "Dashamsha (D10)", "D12": "Dwadashamsha (D12)", "D16": "Shodashamsha (D16)", "D20": "Vimshamsha (D20)", "D24": "Chaturvimshamsha (D24)", "D27": "Saptavimshamsha (D27)", "D30": "Trimshamsha (D30)", "D40": "Khavedamsha (D40)", "D45": "Akshavedamsha (D45)", "D60": "Shashtiamsha (D60)"}
    
    return {"chart": chart_data, "navamsa_chart": navamsa_chart_data, "chandra_chart": chandra_chart_data, "lagna": RASHIS[lagna_rashi], "moon_sign": RASHIS[moon_rashi_idx], "nakshatra": nak_str, "ayanamsa_val": ayan_str, "planetary_positions": planetary_positions, "kundali_table": kundali_table, "kundli_details": kundli_details, "dasha_periods": dasha_periods, "dosha_details": dosha_details, "samvat": samvat_details, "lagna_lord": lagna_lord, "sunrise": sunrise_str, "sunset": sunset_str, "timezone": tz.zone, "sudarshana": sudarshana_data, "shodashvarga_charts": shodashvarga_charts, "varga_titles": varga_titles}
