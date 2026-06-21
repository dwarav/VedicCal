import swisseph as swe
from datetime import datetime, timedelta, date
import pytz
import os
import urllib.parse
import calendar

from ..config import EPHEMERIS_PATH, SIDEREAL_MODE
from ..constants.mappings import (
    MONTHS, TITHIS, NAKSHATRAS, YOGAS, KARANAS, RASHIS, PADA_NAMES,
    VARJYAM_STARTS, AMRIT_STARTS,
    SAMVATSARA_NAMES, NAMA_AKSHARA, GANAS, YONIS, NADIS, VARNA, VASHYA, TATVA,
    RASI_LORDS_MAP, NAK_LORDS
)
from ..constants.festivals import FESTIVAL_DB, GREGORIAN_FESTIVALS, FESTIVAL_IMAGES_STATIC
from ..constants.astrology import (
    KUNDLI_PREDICTIONS, FAV_POINTS, NAK_ICONS, TITHI_ICONS, RASHI_ICONS,
    RAHU_KEY, YAMA_KEY, GULI_KEY
)

from .geo import get_location

# ================= CORE FUNCTIONS =================
def setup_swisseph():
    """
    Configures the Swiss Ephemeris path and sidereal mode.
    Must be called before any swisseph calculations.
    """
    swe.set_ephe_path(EPHEMERIS_PATH)
    swe.set_sid_mode(SIDEREAL_MODE)

def jd_from_dt(dt_local):
    """
    Converts a localized datetime object to Julian Day number.
    
    Args:
        dt_local (datetime): Datetime object with timezone info.
        
    Returns:
        float: Julian Day number (UT).
    """
    dt_utc = dt_local.astimezone(pytz.utc)
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0)

def dt_from_jd(jd, tz):
    """
    Converts a Julian Day number to a localized datetime object.
    
    Args:
        jd (float): Julian Day number.
        tz (pytz.timezone): Target timezone.
        
    Returns:
        datetime: Localized datetime object, or None if conversion fails.
    """
    if jd is None: return None
    y, m, d, h_dec = swe.revjul(jd)
    h = int(h_dec)
    mins = (h_dec - h) * 60
    mi = int(mins)
    sec = int((mins - mi) * 60)
    try:
        return datetime(int(y), int(m), int(d), h, mi, sec, tzinfo=pytz.utc).astimezone(tz)
    except Exception: return None

# ================= CALCULATORS =================
def calc_sun_rise_set(jd, lat, lon):
    """
    Calculates Sun rise and set times for a given date and location.
    
    Args:
        jd (float): Julian Day number for the date (usually noon).
        lat (float): Latitude.
        lon (float): Longitude.
        
    Returns:
        tuple: (rise_jd, set_jd) as float Julian Days.
    """
    if jd is None: return 0.0, 0.0
    geopos = (float(lon), float(lat), 0.0)
    jd_search = jd - 0.375 # Start search from previous night/early morning
    try:
        rise = swe.rise_trans(jd_search, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER, geopos)[1][0]
        set_ = swe.rise_trans(jd_search, swe.SUN, swe.CALC_SET | swe.BIT_DISC_CENTER, geopos)[1][0]
        return rise, set_
    except Exception: return 0.0, 0.0

def calc_moon_rise_set(jd_start, lat, lon):
    """
    Calculates Moon rise and set times for the given day.
    Checks the 24 hour period from midnight to find the correct rise/set.
    
    Args:
        jd_start (float): Julian Day (usually noon) of the target day.
        lat (float): Latitude.
        lon (float): Longitude.
        
    Returns:
        tuple: (rise_jd, set_jd).
    """
    if jd_start is None: return 0.0, 0.0
    geopos = (float(lon), float(lat), 0.0)
    
    # Start search from local midnight (approx jd_start - 0.5)
    jd_search_start = jd_start - 0.5
    
    try:
        # Get next rise after midnight
        res_rise = swe.rise_trans(jd_search_start, swe.MOON, swe.CALC_RISE | swe.BIT_DISC_CENTER, geopos)
        rise_time = res_rise[1][0]
        
        # Validation: check if the found rise time is within the target 24-hour day
        if rise_time > jd_search_start + 1.0:
             # No moonrise on this day, so try finding the most recent rise before midnight
             # to anchor the moonset calculation.
             res_rise_prev = list(swe.rise_trans(jd_search_start - 1.0, swe.MOON, swe.CALC_RISE | swe.BIT_DISC_CENTER, geopos))
             anchor_rise = res_rise_prev[1][0]
             rise_time = 0.0 # Indicate no rise today
        else:
             anchor_rise = rise_time
             
        # Additionally, if the time found is before the start of the day (rare, but just in case)
        if anchor_rise < jd_search_start and rise_time != 0.0:
             # Try next rise
             res_rise2 = swe.rise_trans(anchor_rise + 0.1, swe.MOON, swe.CALC_RISE | swe.BIT_DISC_CENTER, geopos)
             if res_rise2[1][0] < jd_search_start + 1.0:
                 anchor_rise = res_rise2[1][0]
                 rise_time = anchor_rise
             else:
                 rise_time = 0.0

        # Get the very next moonset AFTER our anchor rise time
        res_set = swe.rise_trans(anchor_rise, swe.MOON, swe.CALC_SET | swe.BIT_DISC_CENTER, geopos)
        set_time = res_set[1][0]
                 
        return rise_time, set_time
    except Exception: return 0.0, 0.0

def get_pos(jd):
    """
    Calculates the longitude of Sun and Moon at a given Julian Day.
    
    Args:
        jd (float): Julian Day.
        
    Returns:
        tuple: (sun_longitude, moon_longitude) in degrees.
    """
    if jd is None: return 0.0, 0.0
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    try:
        sun = swe.calc_ut(jd, swe.SUN, flags)[0][0]
        moon = swe.calc_ut(jd, swe.MOON, flags)[0][0]
        return sun, moon
    except Exception: return 0.0, 0.0

def get_events(start_jd, end_jd, func, names, count, is_karana=False):
    """
    Generic function to find start/end times of astrological events (Tithi, Yoga, etc.)
    within a time range.
    
    Args:
        start_jd (float): Start Julian Day.
        end_jd (float): End Julian Day.
        func (callable): Function taking jd and returning (index, 0).
        names (list): List of names corresponding to indices.
        count (int): Total number of possible values (e.g., 27 for Nakshatra).
        is_karana (bool): Special handling for Karana names.
        
    Returns:
        list: List of dictionaries with event details.
    """
    events = []
    if start_jd is None: return []
    try:
        curr_idx, _ = func(start_jd)
        # Find start of current event (look backwards)
        s_jd = find_trans(start_jd - 1.5, func, (curr_idx - 1) % count) or start_jd
        curr_search = start_jd
        loops = 0
        while loops < 10:
            e_jd = find_trans(curr_search, func, curr_idx)
            name = get_karana_name(curr_idx) if is_karana else names[curr_idx]
            events.append({'name': name, 'start': s_jd, 'end': e_jd, 'index': curr_idx})
            if not e_jd or e_jd >= end_jd: break
            s_jd = e_jd
            curr_search = e_jd + 0.002
            curr_idx = (curr_idx + 1) % count
            loops += 1
    except Exception: pass
    return events

def find_trans(start, func, target, limit=2.0):
    """
    Binary search implementation to find the exact time when an astrological value changes.
    Used for finding Tithi end times, Nakshatra changes, etc.
    """
    t1, t2 = start, start + limit
    curr = t1
    found = False
    while curr < t2:
        try:
            val = func(curr)[0]
            val_next = func(curr + 1/24.0)[0]
            # Check if value changes within this hour and matches target
            if val != val_next and val == target:
                t1, t2 = curr, curr + 1/24.0
                found = True
                break
        except Exception: pass
        curr += 1/24.0
    if not found: return None
    # Refine precision
    while (t2 - t1) > 0.00001:
        mid = (t1 + t2)/2
        try:
            if func(mid)[0] == target: t1 = mid
            else: t2 = mid
        except Exception: break
    return t2

def get_karana_name(k):
    """Helper to map Karana index to name."""
    if k == 0: return KARANAS[10] # Kimstughna
    if k >= 57: return KARANAS[k - 50] # Fixed Karanas at end
    return KARANAS[(k - 1) % 7] # Repeating movable Karanas

def fmt_duration(jd_start, jd_end):
    """Formats the duration between two JDs into readable string."""
    if jd_start is None or jd_end is None: return "---"
    duration_days = jd_end - jd_start
    total_seconds = int(duration_days * 24 * 3600)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d} Hours {minutes:02d} Mins {seconds:02d} Secs"

# --- HELPER: GET ENTRY/EXIT TIMES ---
def get_entry_exit_times(jd_ref, body_id, current_val, span_deg, tz):
    """Calculates when a planet enters and exits a specific angular division (sign/nakshatra)."""
    # Current value is 'current_val'. 
    # Entry time = End of (current_val - 1)
    # Exit time = End of (current_val)
    
    target_entry = current_val # We want to find when it BECAME current_val
    target_exit = current_val # We want to find when it LEAVES current_val
    
    # Check function for transitions
    def check_idx(t):
        pos = swe.calc_ut(t, body_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)[0][0]
        return (int(pos / span_deg), 0)

    # Determine search limits based on body
    limit = 2.0
    if body_id == swe.SUN: limit = 60.0
    elif body_id == swe.MOON: limit = 10.0
    
    # Find Exit (When it becomes next sign)
    exit_jd = find_trans(jd_ref, check_idx, target_exit, limit=limit) 
    
    # Find Entry (When it BECAME current sign, i.e., was prev sign before)
    # We search backwards for the transition from (current-1) to current.
    # find_trans logic: "find time T where func(T) == target".
    # But find_trans finds when it *switches* to target? 
    # "if val != val_next and val == target" -> This means at T it IS target, but at T+dt it calculates... wait.
    # line 177: if val != val_next and val == target:
    # This means at 'curr' it has value 'target', and at 'curr+1h' it has 'val_next' (implied different).
    # So it finds the END of 'target'.
    
    # So to find Entry of Current (Start of Current), we want to find END of Previous.
    # target for find_trans shoud be (current_val - 1)
    
    # Handle wrap around for signs (0-11) or Nakshatras (0-26)
    # If current is 0, prev is Max. 
    # Actually check_idx returns simple integer division.
    # For signs 0..11.
    # Use modulo logic inside check_idx? No, check_idx returns 0..11.
    
    prev_val = (current_val - 1) 
    if body_id == swe.MOON and span_deg == 13.333333: # Nakshatra
         if prev_val < 0: prev_val = 26
    elif span_deg == 30: # Sign
         if prev_val < 0: prev_val = 11
            
    days_back = 35 if body_id == swe.SUN else 5
    search_start = jd_ref - days_back
    
    # We want to find when "Previous" ended. i.e. when check_idx(t) was prev_val and changed.
    # find_trans returns the T where check_idx(T) == target (prev_val) AND check_idx(T+dt) != target.
    # So exactly what we want.
    
    # Search range for entry should also be large enough
    entry_jd = find_trans(search_start, check_idx, prev_val, limit=days_back + 2.0)
    
    entry_str = "---"
    exit_str = "---"
    if entry_jd:
        dt_ent = dt_from_jd(entry_jd, tz)
        if dt_ent: entry_str = dt_ent.strftime("%d %b, %I:%M %p")
    if exit_jd:
        dt_ex = dt_from_jd(exit_jd, tz)
        if dt_ex: exit_str = dt_ex.strftime("%d %b, %I:%M %p")
    return entry_str, exit_str


# ================= HELPER CALCULATORS =================
def get_tamil_yoga(weekday_idx, nak_idx):
    """Determines Tamil Yoga (Siddha/Amrita/Marana) based on weekday and Nakshatra."""
    marana_combos = [(6, 1), (0, 13), (1, 20), (2, 18), (3, 9), (4, 10), (5, 26)]
    amrita_combos = [(6, 12), (0, 21), (1, 6), (2, 23), (3, 7), (4, 26), (5, 3)]
    key = (weekday_idx, nak_idx)
    if key in marana_combos: return "Marana"
    if key in amrita_combos: return "Amrita"
    return "Siddha"

def get_sarvartha_siddhi(weekday_idx, nak_idx):
    """Checks for Sarvartha Siddhi Yoga."""
    ss_map = {6: [12, 7, 18, 11, 20, 25, 0], 0: [21, 3, 4, 7, 16], 1: [0, 2, 4, 8], 2: [3, 16, 12, 2, 4], 3: [7, 16, 2, 6, 26], 4: [26, 16, 0, 6, 21], 5: [3, 14, 21]}
    return nak_idx in ss_map.get(weekday_idx, [])

def get_vidaal_yoga(weekday_idx, nak_idx):
    """Checks for Vidaal Yoga (Inauspicious)."""
    bad_map = {6: [1, 13], 0: [13], 1: [20], 2: [18], 3: [9], 4: [10], 5: [26]}
    return nak_idx in bad_map.get(weekday_idx, [])

def get_tripushkara_yoga(tithi_events, nak_events, weekday_idx, start_jd, end_jd, tz):
    """Checks for Tripushkara Yoga based on Tithi, Nakshatra and Weekday overlap."""
    if weekday_idx not in [1, 5, 6]: return "None"
    valid_tithis = [1, 6, 11, 16, 21, 26] # Dwitiya, Saptami, Dwadashi
    valid_naks = [2, 6, 11, 15, 20, 24] # Krittika, Punarvasu, etc.
    timings = []
    for t in tithi_events:
        if t['index'] in valid_tithis:
            t_s = max(t['start'], start_jd)
            t_e = min(t['end'] if t['end'] else end_jd, end_jd)
            for n in nak_events:
                if n['index'] in valid_naks:
                    n_s = max(n['start'], start_jd)
                    n_e = min(n['end'] if n['end'] else end_jd, end_jd)
                    latest_start = max(t_s, n_s)
                    earliest_end = min(t_e, n_e)
                    if latest_start < earliest_end:
                        s_dt = dt_from_jd(latest_start, tz)
                        e_dt = dt_from_jd(earliest_end, tz)
                        base_date = dt_from_jd(start_jd, tz).date()
                        
                        s_str = s_dt.strftime('%b %d, %I:%M %p') if s_dt.date() != base_date else s_dt.strftime('%I:%M %p')
                        e_str = e_dt.strftime('%b %d, %I:%M %p') if e_dt.date() != base_date else e_dt.strftime('%I:%M %p')
                        timings.append(f"{s_str} - {e_str}")
    return ", ".join(timings) if timings else "None"

def get_netram_jeevan(nak_idx):
    """Calculates Netram and Jeevan numbers for the day's Nakshatra."""
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
    """Calculates Baana Dosha."""
    dist = (nak_idx - sun_nak_idx) % 9
    baana_map = {0: "Sthira (Good)", 1: "Roga (Bad)", 2: "Agni (Bad)", 3: "Raja (Good)", 4: "Chora (Bad)", 5: "Mrityu (Bad)", 6: "Sthira (Good)", 7: "Sthira (Good)", 8: "Sthira (Good)"}
    return baana_map.get(dist, "Sthira")

def get_calculated_timings(nak_events, weekday_idx, sun_nak_idx, tithi_events, start_jd, end_jd, tz):
    """Aggregates various special yoga timings (Anandadi, Tamil, Sarvartha, etc.)."""
    ANANDADI_YOGAS = ["Ananda", "Kaladanda", "Dhumra", "Prajapati", "Soumya", "Dhwalka", "Dhwaja", "Srivatsa", "Vajra", "Mudgara", "Chhatra", "Mitra", "Manasa", "Padma", "Lumba", "Utpata", "Mrityu", "Kana", "Siddhi", "Shubha", "Amrita", "Musala", "Gada", "Matanga", "Rakshasa", "Chara", "Sthira", "Pravardhamana"]
    ananda_offset = {6:0, 0:22, 1:18, 2:14, 3:10, 4:6, 5:2}
    base_date = dt_from_jd(start_jd, tz).date()
    def fmt_event(ev_list, type_fn):
        res = []
        for e in ev_list:
            val = type_fn(e['index'])
            d_end = dt_from_jd(e['end'], tz)
            if d_end and e['end']:
                end_t = d_end.strftime('%b %d, %I:%M %p') if d_end.date() != base_date else d_end.strftime('%I:%M %p')
            else:
                end_t = "Full Night"
            res.append(f"{val} upto {end_t}")
        return " | ".join(res)
    anandadi_str = fmt_event(nak_events, lambda idx: ANANDADI_YOGAS[(idx + ananda_offset[weekday_idx]) % 28])
    tamil_str = fmt_event(nak_events, lambda idx: get_tamil_yoga(weekday_idx, idx))
    baana_str = fmt_event(nak_events, lambda idx: get_baana_type(sun_nak_idx, idx))
    n, j = get_netram_jeevan(nak_events[0]['index']) if nak_events else ("---", "---")
    ss_found = []
    vidaal_found = []
    for e in nak_events:
        d_start = dt_from_jd(e['start'], tz)
        if d_start:
             start_t = d_start.strftime('%b %d, %I:%M %p') if d_start.date() != base_date else d_start.strftime('%I:%M %p')
        else:
             start_t = "..."
             
        d_end = dt_from_jd(e['end'], tz)
        if d_end and e['end']:
             end_t = d_end.strftime('%b %d, %I:%M %p') if d_end.date() != base_date else d_end.strftime('%I:%M %p')
        else:
             end_t = "Full Night"
        if get_sarvartha_siddhi(weekday_idx, e['index']): ss_found.append(f"{start_t} - {end_t}")
        if get_vidaal_yoga(weekday_idx, e['index']): vidaal_found.append(f"{start_t} - {end_t}")
    sarvartha_str = ", ".join(ss_found) if ss_found else "None"
    vidaal_str = ", ".join(vidaal_found) if vidaal_found else "None"
    tripushkara_str = get_tripushkara_yoga(tithi_events, nak_events, weekday_idx, start_jd, end_jd, tz)
    return {"anandadi": anandadi_str, "tamil": tamil_str, "sarvartha": sarvartha_str, "baana": baana_str, "netrama": n, "jeevanama": j, "tripushkara": tripushkara_str, "vidaal": vidaal_str}

def get_samvat_details(dt, lunar_month=None, tithi=None):
    """Calculates Vikram and Shaka Samvat years."""
    year = dt.year
    # For Solar Samvat (fixed date)
    is_after_solar_new_year = dt.month > 4 or (dt.month == 4 and dt.day > 14)
    vikram = year + 57 if is_after_solar_new_year else year + 56
    shaka = year - 78 if is_after_solar_new_year else year - 79
    
    # For Samvatsara name (Lunar transition on Ugadi - Chaitra Shukla Pratipada)
    # If we have lunar month and tithi, use them to decide.
    # Otherwise fallback to solar transition for backward compatibility.
    if lunar_month and tithi:
        # Chaitra Shukla Pratipada is the start of the new lunar year.
        # But wait, lunar_month 'Chaitra' starts with Krishna Paksha in Purnimanta, 
        # or Shukla Paksha in Amanta. The app uses Amanta (from lunar_month_idx_calc).
        # In Amanta, New Year is Chaitra Shukla Pratipada (Tithi 0).
        is_after_lunar_new_year = (lunar_month != "Phalguna" and lunar_month != "Magha") # Oversimplified
        # Detailed logic: Chaitra is the first month. 
        # If month is Chaitra and tithi >= 0, it's new year.
        # If month is Vaishakha etc, it's new year.
        # If month is Phalguna, it's old year.
        
        # In this app's MONTHS: ["Chaitra", "Vaishakha", ...]
        # Chaitra is index 0.
        try:
            m_idx = MONTHS.index(lunar_month)
            # Samvatsara changes at Chaitra Shukla Pratipada (Tithi 0)
            # So if m_idx > 0, or (m_idx == 0 and tithi_idx is handled elsewhere)
            # Actually, the samvat_idx calculation (shaka + 11) % 60 is standard for the START of the year.
            # Shaka year itself increments at Ugadi.
            
            # The current Shaka calculation (year - 78/79) is Solar.
            # We should probably calculate a 'Lunar Shaka' for the index.
            lunar_shaka = year - 78 if (m_idx > 0 or (m_idx == 0)) else year - 79
            # Wait, if m_idx is 0 (Chaitra), it's already the new Shaka year.
            # If m_idx is 11 (Phalguna), it's the old Shaka year.
            lunar_shaka = year - 78 if m_idx >= 0 and m_idx < 10 else year - 79 
            # This is still rough. Let's use the actual lunar month index.
            # If month is Chaitra, Vaishakha... up to Phalguna.
            # The year 2026: Ugadi is March 19.
            # Before March 19: Phalguna (m_idx 11). lunar_shaka = 2026 - 79 = 1947.
            # After March 19: Chaitra (m_idx 0). lunar_shaka = 2026 - 78 = 1948.
            
            # So: if m_idx == 11 (Phalguna) or (m_idx == 10 and current day is before transition)
            # Actually, just m_idx < 11 usually works if Chaitra is 0.
            # But wait, if it's Jan/Feb 2026, it's still Shaka 1947, and month is Magha/Phalguna.
            # So if m_idx is 10 or 11, it's definitely old year if it's early in Gregorian year.
            # If m_idx is 0, it's definitely new year.
            
            if m_idx < 10: # Chaitra (0) to Pausha (9)
                lunar_shaka = year - 78
            else: # Magha (10), Phalguna (11)
                # If Gregorian month is Jan/Feb/March, it's the old Shaka year.
                if dt.month <= 4:
                    lunar_shaka = year - 79
                else: 
                    # This case rarely happens (Phalguna in April/May)
                    lunar_shaka = year - 78
            
            samvat_idx = (lunar_shaka + 11) % 60
        except:
            samvat_idx = (shaka + 11) % 60
    else:
        samvat_idx = (shaka + 11) % 60
        
    samvat_name = SAMVATSARA_NAMES[samvat_idx]
    return {"vikram": vikram, "shaka": shaka, "samvatsara": samvat_name, "chandramasa": ""}

def get_ritu_ayana_details(jd):
    """Determines Ritu (Season) and Ayana (Solstice direction)."""
    sun_trop = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
    swe.set_sid_mode(SIDEREAL_MODE)
    sun_sid = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)[0][0]
    if (sun_trop >= 270 or sun_trop < 90): ayana = "Uttarayana (Drik)"
    else: ayana = "Dakshinayana (Drik)"
    if (sun_sid >= 270 or sun_sid < 90): vedic_ayana = "Uttarayana"
    else: vedic_ayana = "Dakshinayana"
    s = sun_sid % 360
    if 330 <= s < 360 or 0 <= s < 30: ritu = "Vasant (Spring)"
    elif 30 <= s < 90: ritu = "Grishma (Summer)"
    elif 90 <= s < 150: ritu = "Varsha (Monsoon)"
    elif 150 <= s < 210: ritu = "Sharad (Autumn)"
    elif 210 <= s < 270: ritu = "Hemant (Pre-Winter)"
    else: ritu = "Shishir (Winter)"
    return {"ritu": ritu, "vedic_ritu": ritu, "ayana": ayana, "vedic_ayana": vedic_ayana}

def calculate_muhurtas(rise, set_, rise_next, weekday_idx):
    """Calculates daily Muhurtas (Abhijit, Rahu Kalam, Brahma, etc.)."""
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
    # Durmuhurtham Offsets (0-based fractional start from Sunrise)
    # Alignment with Gantala Panchangam:
    # Sun: 16:24 (13.0)
    # Mon: 12:48 (8.5)
    # Tue: 08:48 (3.5)
    # Wed: 11:36 (7.0)
    # Thu: 10:00 (5.0)
    # Fri: 08:48 (3.5) & 12:48 (8.5)
    # Sat: 07:36 (2.0)
    DUR_OFFSETS = {
        6: [13.0], 
        0: [8.5], 
        1: [3.5], 
        2: [7.0], 
        3: [5.0], 
        4: [3.5, 8.5], 
        5: [2.0]
    }
    dur_times = []
    for offset in DUR_OFFSETS[weekday_idx]:
        s = rise + (offset * one_muhurta_day)
        # Durmuhurtham is typically 1 Muhurtha (48 mins approx)
        e = s + one_muhurta_day 
        dur_times.append((s, e))
    return {"brahma": (brahma_start, brahma_end), "pratah": (pratah_start, pratah_end), "abhijit": abhijit_res, "vijaya": (vijaya_start, vijaya_end), "godhuli": (godhuli_start, godhuli_end), "sayahna": (sayahna_start, sayahna_end), "nishita": (nishita_start, nishita_end), "dur_day": dur_times}

def get_nivas_shool_details(jd, weekday_idx, tithi_idx, nak_idx):
    """Calculates Shiva Vasa, Agni Vasa, Dishashool, etc. for travel/auspiciousness."""
    ds_map = {0: "East", 1: "North", 2: "North", 3: "South", 4: "West", 5: "East", 6: "West"}
    disha_shool = ds_map[weekday_idx]
    moon_long = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    moon_rashi_idx = int(moon_long / 30)
    cv_map = {0: "East", 4: "East", 8: "East", 1: "South", 5: "South", 9: "South", 2: "West", 6: "West", 10: "West", 3: "North", 7: "North", 11: "North"}
    chandra_vasa = cv_map[moon_rashi_idx]
    tithi_count = (tithi_idx % 30) + 1
    vedic_day = 1 if weekday_idx == 6 else (weekday_idx + 2) 
    agni_rem = (tithi_count + vedic_day + 1) % 4
    if agni_rem == 0 or agni_rem == 3: agnivasa = "Earth (Prithvi) - Auspicious"; homahuti_str = "Agni is Present (Good)"
    elif agni_rem == 1: agnivasa = "Sky (Akasha) - Inauspicious"; homahuti_str = "Agni in Sky (Bad)"
    else: agnivasa = "Netherworld (Patala) - Inauspicious"; homahuti_str = "Agni in Patala (Bad)"
    if tithi_count == 30: shiva_loc = "Smashana (Inauspicious)"
    else:
        if tithi_count in [1, 8, 15, 22, 29]: shiva_loc = "Nandi (Good)"
        elif tithi_count in [2, 9, 16, 23, 30]: 
             if tithi_count == 30: shiva_loc = "Smashana (Bad)"
             else: shiva_loc = "Gauri (Good)"
        elif tithi_count in [3, 10, 17, 24]: shiva_loc = "Sabha (Bad)"
        elif tithi_count in [4, 11, 18, 25]: shiva_loc = "Krida (Bad)"
        elif tithi_count in [5, 12, 19, 26]: shiva_loc = "Kailash (Good)"
        elif tithi_count in [6, 13, 20, 27]: shiva_loc = "Vrishabha (Good)"
        else: shiva_loc = "Bhojana (Bad)"
    if moon_rashi_idx in [0, 1, 2, 7]: bhadravasa = "Swarga (Heaven) - Auspicious" 
    elif moon_rashi_idx in [5, 6, 8, 9]: bhadravasa = "Patala (Netherworld) - Auspicious"
    else: bhadravasa = "Prithvi (Earth) - Inauspicious"
    # Python weekday: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    # Rahu Vasa: Mon:NW, Tue:N, Wed:NE, Thu:S, Fri:W, Sat:SE, Sun:SW
    rv_map = {0: "North-West", 1: "North", 2: "North-East", 3: "South", 4: "West", 5: "South-East", 6: "South-West"}
    rahu_vasa = rv_map[weekday_idx]
    sun_long = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    sun_rashi_idx = int(sun_long / 30)
    # Nakshatra Shool
    # East: 8, 17, 18, 19, 25, 26, 5 (Aslesha, Jyestha, Mula, P.Ashadha, U.Bhadra, Revati, Ardra)
    # South: 10, 11, 12, 13, 15, 16 (P.Phalguni, U.Phalguni, Hasta, Chitra, Vishakha, Anuradha)
    # West: 3, 6, 7, 21, 24, 20 (Rohini, Pushya, Punarvasu, U.Ashadha? Wait. Mapping varies.)
    
    # Simplified Nakshatra Shool Map (Commonly cited)
    # East: Jyeshta, P.Ashadha, Mula, P.Bhadra, U.Bhadra, Revati, Ardra, Aslesha
    # South: P.Phalguni, U.Phalguni, Hasta, Chitra, Swati, Visakha, Anuradha
    # West: Rohini, Pushya, Punarvasu, Mrigasira, Bharani, Krittika, Magha?
    # North: U.Ashadha, Sravana, Dhanishta, Satabhisha
    
    ns_map = {
        0: "South", 1: "West", 2: "East", 3: "West", 4: "West", 5: "East", 6: "West", 7: "West", 8: "East", # Ashwini..Aslesha
        9: "North", 10: "North", 11: "North", 12: "North", 13: "North", 14: "North", 15: "North", 16: "North", 17: "East", # Magha..Jyestha
        18: "East", 19: "East", 20: "South", 21: "South", 22: "South", 23: "South", 24: "East", 25: "East", 26: "East" # Mula..Revati
    }
    # NOTE: The above mapping is an approximation as variances exist. 
    # Providing a safe default if specific rule is not found.
    # Refined Map:
    # East: Jyestha (17), P.Ashadha (19), Mula (18), Ardra (5), Aslesha (8), U.Bhadra (25), Revati (26)
    # South: P.Phalguni (10), U.Phalguni (11), Hasta (12), Chitra (13), Swati (14), Visakha (15), Anuradha (16)
    # West: Rohini (3), Pushya (7), Punarvasu (6), Mrigasira (4), Bharani (1), Krittika (2), Magha (9)
    # North: Uttara Ashadha (20), Shravana (21), Dhanishta (22), Satabhisha (23), Ashwini (0), P.Bhadra (24)
    
    ns_refined = {
        17: "East", 19: "East", 18: "East", 5: "East", 8: "East", 25: "East", 26: "East",
        10: "South", 11: "South", 12: "South", 13: "South", 14: "South", 15: "South", 16: "South",
        3: "West", 7: "West", 6: "West", 4: "West", 1: "West", 2: "West", 9: "West",
        20: "North", 21: "North", 22: "North", 23: "North", 0: "North", 24: "North"
    }
    
    nakshatra_shool = ns_refined.get(nak_idx, "None")

    if sun_rashi_idx in [0, 1, 2]: kumbha_chakra = "West"
    elif sun_rashi_idx in [3, 4, 5]: kumbha_chakra = "North"
    elif sun_rashi_idx in [6, 7, 8]: kumbha_chakra = "East"
    else: kumbha_chakra = "South"

    return {
        "homahuti": homahuti_str, 
        "disha_shool": disha_shool, 
        "agnivasa_1": agnivasa, 
        "agnivasa_2": "", 
        "bhadravasa": bhadravasa, 
        "chandra_vasa": chandra_vasa, 
        "shivavasa_1": shiva_loc, 
        "shivavasa_2": "", 
        "rahu_vasa": rahu_vasa, 
        "kumbha_chakra": kumbha_chakra,
        "nakshatra_shool": nakshatra_shool
    }

def get_daily_nivas_details(jd_start, jd_end, weekday_idx, tithi_events, nak_events, moon_rashi_idx, sun_rashi_idx, sun_long, tz):
    """Calculates Nivas/Shool values for the entire day with timings."""
    
    # helper for formatting time
    base_date = dt_from_jd(jd_start, tz).date()
    def fmt_t(jd):
        dt = dt_from_jd(jd, tz)
        if not dt: return "..."
        if dt.date() != base_date:
             return dt.strftime('%b %d, %I:%M %p')
        return dt.strftime('%I:%M %p')

    # --- 1. Dishashool (Constant for Weekday) ---
    ds_map = {0: "East", 1: "North", 2: "North", 3: "South", 4: "West", 5: "East", 6: "West"}
    disha_shool = ds_map[weekday_idx]

    # --- 2. Rahu Vasa (Constant for Weekday) ---
    # Python weekday: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    rv_map = {0: "North-West", 1: "North", 2: "North-East", 3: "South", 4: "West", 5: "South-East", 6: "South-West"}
    rahu_vasa = rv_map[weekday_idx]
    
    # --- 3. Kumbha Chakra (Usually Constant, depends on Sun Sign) ---
    if sun_rashi_idx in [0, 1, 2]: kumbha_chakra = "West"
    elif sun_rashi_idx in [3, 4, 5]: kumbha_chakra = "North"
    elif sun_rashi_idx in [6, 7, 8]: kumbha_chakra = "East"
    else: kumbha_chakra = "South"
    # Technically Sun can change sign, but let's stick to noon/sunrise for simplicity unless critical.

    # --- Helper to process temporal events ---
    def process_events(events, calc_fn):
        res_strs = []
        for e in events:
            val = calc_fn(e['index'])
            start = max(e['start'], jd_start)
            end = min(e['end'] if e['end'] else jd_end, jd_end)
            if start < end:
                 # Check if this covers the whole relevant day (sunrise to next sunrise approx)
                 if e['start'] <= jd_start and (not e['end'] or e['end'] >= jd_end):
                     res_strs.append(f"{val} (Full Day)")
                 else:
                     s_t = fmt_t(start)
                     e_t = fmt_t(e['end']) if e['end'] else "Full Night"
                     res_strs.append(f"{val} ({s_t} - {e_t})")
        return " | ".join(res_strs)

    # --- 4. Homahuti (Depends on Tithi + Weekday) ---
    def calc_homahuti(t_idx):
        tithi_count = (t_idx % 30) + 1
        vedic_day = 1 if weekday_idx == 6 else (weekday_idx + 2) 
        agni_rem = (tithi_count + vedic_day + 1) % 4
        if agni_rem == 0 or agni_rem == 3: return "Agni is Present (Good)"
        elif agni_rem == 1: return "Agni in Sky (Bad)"
        else: return "Agni in Patala (Bad)"
    homahuti_str = process_events(tithi_events, calc_homahuti)

    # --- 5. Agnivasa (Same logic as Homahuti but different labels) ---
    def calc_agnivasa(t_idx):
        tithi_count = (t_idx % 30) + 1
        vedic_day = 1 if weekday_idx == 6 else (weekday_idx + 2) 
        agni_rem = (tithi_count + vedic_day + 1) % 4
        if agni_rem == 0 or agni_rem == 3: return "Earth (Prithvi) - Auspicious"
        elif agni_rem == 1: return "Sky (Akasha) - Inauspicious"
        else: return "Netherworld (Patala) - Inauspicious"
    agnivasa_str = process_events(tithi_events, calc_agnivasa)

    # --- 6. Shivavasa (Depends on Tithi) ---
    def calc_shivavasa(t_idx):
        tithi_count = (t_idx % 30) + 1
        if tithi_count == 30: return "Smashana (Inauspicious)"
        if tithi_count in [1, 8, 15, 22, 29]: return "Nandi (Good)"
        elif tithi_count in [2, 9, 16, 23, 30]: 
             if tithi_count == 30: return "Smashana (Bad)"
             else: return "Gauri (Good)"
        elif tithi_count in [3, 10, 17, 24]: return "Sabha (Bad)"
        elif tithi_count in [4, 11, 18, 25]: return "Krida (Bad)"
        elif tithi_count in [5, 12, 19, 26]: return "Kailash (Good)"
        elif tithi_count in [6, 13, 20, 27]: return "Vrishabha (Good)"
        else: return "Bhojana (Bad)"
    shivavasa_str = process_events(tithi_events, calc_shivavasa)

    # --- 7. Nakshatra Shool (Depends on Nakshatra) ---
    def calc_nak_shool(n_idx):
         ns_refined = {
            17: "East", 19: "East", 18: "East", 5: "East", 8: "East", 25: "East", 26: "East",
            10: "South", 11: "South", 12: "South", 13: "South", 14: "South", 15: "South", 16: "South",
            3: "West", 7: "West", 6: "West", 4: "West", 1: "West", 2: "West", 9: "West",
            20: "North", 21: "North", 22: "North", 23: "North", 0: "North", 24: "North"
        }
         return ns_refined.get(n_idx, "None")
    nak_shool_str = process_events(nak_events, calc_nak_shool)

    # --- 8. Chandra/Bhadra Vasa (Depends on Moon Rashi) ---
    # Need Moon Rashi events for the day.
    # We have moon_rashi_idx (at sunrise/noon) but need to check if it changes.
    # Re-calculate moon entry/exit to build events list
    # Reusing find_trans logic
    
    cv_map = {0: "East", 4: "East", 8: "East", 1: "South", 5: "South", 9: "South", 2: "West", 6: "West", 10: "West", 3: "North", 7: "North", 11: "North"}
    
    # Check current rashi end
    target_next = (moon_rashi_idx + 1) % 12
    def check_sign(t): return int(swe.calc_ut(t, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)[0][0] / 30)
    
    rashi_events = []
    # Current rashi
    r_end = find_trans(jd_start, check_sign, target_next)
    
    if not r_end or r_end >= jd_end:
        rashi_events.append({'index': moon_rashi_idx, 'start': jd_start, 'end': jd_end})
    else:
        rashi_events.append({'index': moon_rashi_idx, 'start': jd_start, 'end': r_end})
        # Next rashi
        rashi_events.append({'index': target_next, 'start': r_end, 'end': jd_end})
    
    def calc_chandra_vasa(r_idx): return cv_map.get(r_idx, "")
    chandra_vasa_str = process_events(rashi_events, calc_chandra_vasa)

    def calc_bhadravasa(r_idx):
        if r_idx in [0, 1, 2, 7]: return "Swarga (Heaven) - Auspicious" 
        elif r_idx in [5, 6, 8, 9]: return "Patala (Netherworld) - Auspicious"
        else: return "Prithvi (Earth) - Inauspicious"
    bhadra_vasa_str = process_events(rashi_events, calc_bhadravasa)

    return {
        "homahuti": homahuti_str, 
        "disha_shool": disha_shool, 
        "agnivasa_1": agnivasa_str, 
        "agnivasa_2": "", 
        "bhadravasa": bhadra_vasa_str, 
        "chandra_vasa": chandra_vasa_str, 
        "shivavasa_1": shivavasa_str, 
        "shivavasa_2": "", 
        "rahu_vasa": rahu_vasa, 
        "kumbha_chakra": kumbha_chakra,
        "nakshatra_shool": nak_shool_str,
        "valid_at": "" # Not used anymore
    }

def get_epoch_details(jd, dt):
    """Returns Kaliyuga year, Ayanamsha, and other epochal data."""
    ayanamsha = swe.get_ayanamsa(jd)
    kaliyuga_year = dt.year + 3101
    shaka_year = dt.year - 78
    mjd = jd - 2400000.5
    ahargana = int(jd - 588465.5)
    return {"kaliyuga": f"{kaliyuga_year} Years", "ayanamsha": f"{ayanamsha:.6f}", "kali_ahargana": f"{ahargana} Days", "rata_die": f"{int(jd - 1721424.5)}", "julian_date": dt.strftime("%B %d, %Y CE"), "julian_day": f"{jd:.2f}", "civil_date": f"{dt.strftime('%d %B')}, {shaka_year} Shaka", "mjd": f"{mjd:.2f}", "nirayana_date": f"{dt.strftime('%d %B')}, {shaka_year} Shaka"}

def get_chandrabalam_tarabalam_details(rashi_events, nak_events, tz, base_jd):
    """Calculates daily strength of Moon and constellations for the user (Period 1 & 2)."""
    
    # --- CHANDRABALAM (Moon Strength) ---
    # Good transits are 1, 3, 6, 7, 10, 11 from Birth Moon
    chandra_periods = {}
    
    for i, event in enumerate(rashi_events):
        moon_rashi_idx = event['index']
        good_rashis = []
        for r_idx, r_name in enumerate(RASHIS):
            # diff = (Current Moon - Birth Moon) % 12 + 1
            diff = (moon_rashi_idx - r_idx) % 12 + 1
            if diff in [1, 3, 6, 7, 10, 11]: 
                 good_rashis.append({"name": r_name.split(' ')[0], "icon": RASHI_ICONS.get(r_name, "")})

        # Format time label
        d_start = dt_from_jd(event['start'], tz)
        d_end = dt_from_jd(event['end'], tz)
        base_date = dt_from_jd(base_jd, tz).date()
        
        label = "Whole Day"
        if len(rashi_events) > 1:
            if not d_start: s_s = "..."
            else: s_s = d_start.strftime('%b %d, %I:%M %p') if d_start.date() != base_date else d_start.strftime('%I:%M %p')
            
            if not d_end: e_s = "..." 
            else: e_s = d_end.strftime('%b %d, %I:%M %p') if d_end.date() != base_date else d_end.strftime('%I:%M %p')
            
            label = f"{s_s} to {e_s}"
        
        chandra_periods[f"period_{i+1}"] = {"time": label, "good_rashis": good_rashis}

    if "period_1" not in chandra_periods: chandra_periods["period_1"] = {"time": "---", "good_rashis": []}

    # --- TARABALAM (Star Strength) ---
    # Good Taras are 2, 4, 6, 8, 9
    tara_periods = {}
    for i, event in enumerate(nak_events):
        day_nak_idx = event['index']
        good_naks = []
        for n_idx, n_name in enumerate(NAKSHATRAS):
            dist = (day_nak_idx - n_idx) % 9 + 1
            if dist in [2, 4, 6, 8, 9]: 
                good_naks.append({"name": n_name, "icon": NAK_ICONS.get(n_name, "")})
        
        # Format time label
        d_start = dt_from_jd(event['start'], tz)
        d_end = dt_from_jd(event['end'], tz)
        base_date = dt_from_jd(base_jd, tz).date()
        
        # Nicer label
        label = "Whole Day"
        if len(nak_events) > 1:
            if not d_start: s_s = "..."
            else: s_s = d_start.strftime('%b %d, %I:%M %p') if d_start.date() != base_date else d_start.strftime('%I:%M %p')
            
            if not d_end: e_s = "..." 
            else: e_s = d_end.strftime('%b %d, %I:%M %p') if d_end.date() != base_date else d_end.strftime('%I:%M %p')
            
            label = f"{s_s} to {e_s}"
            
        tara_periods[f"period_{i+1}"] = {"time": label, "nakshatras": good_naks}

    # Ensure at least structure exists if no events (unlikely)
    if "period_1" not in tara_periods: tara_periods["period_1"] = {"time": "---", "nakshatras": []}
    
    return {"chandrabalam": chandra_periods, "tarabalam": tara_periods}

def get_panchaka_rahita_details(lagnas, tithi_events, nak_events, weekday_idx):
    """Calculates Panchaka Rahita Muhurtha (Good/Bad Panchaka) based on Lagna timings."""
    panchaka_list = []
    V_WEEKDAY = {6:1, 0:2, 1:3, 2:4, 3:5, 4:6, 5:7}
    v_wd = V_WEEKDAY[weekday_idx]
    
    # Helper to find index at a given JD
    def get_idx_at(jd_target, events):
        for e in events:
             start = e.get('start') or 0 # handle None
             end = e.get('end') or 99999999
             if start <= jd_target <= end:
                 return e['index']
        return events[0]['index'] # fallback

    for lagna in lagnas:
        rashi_name = lagna['name']
        
        # Calculate Midpoint JD
        mid_jd = (lagna['start_jd'] + lagna['end_jd']) / 2
        
        # Find Tithi and Nakshatra at this midpoint
        tithi_idx = get_idx_at(mid_jd, tithi_events)
        nak_idx = get_idx_at(mid_jd, nak_events)

        tithi_num = tithi_idx + 1 # 1-based
        nak_num = nak_idx + 1 # 1-based

        lagna_num = 1
        for i, r in enumerate(RASHIS):
            if r.startswith(rashi_name): lagna_num = i + 1; break
            
        total = tithi_num + v_wd + nak_num + lagna_num
        remainder = total % 9
        
        if remainder == 1: status, label = False, "Mrityu Panchaka"
        elif remainder == 2: status, label = False, "Agni Panchaka"
        elif remainder == 4: status, label = False, "Raja Panchaka"
        elif remainder == 6: status, label = False, "Chora Panchaka"
        elif remainder == 8: status, label = False, "Roga Panchaka"
        else: status, label = True, "Good Muhurta"
        
        panchaka_list.append({"label": label, "times": f"{lagna['start']} to {lagna['end']}", "is_good": status})
    return panchaka_list

def get_udaya_lagna_details(jd_start, jd_end, tz, lat, lon):
    """Calculates the Ascendant (Lagna) changes throughout the day."""
    lagnas = []
    swe.set_ephe_path(EPHEMERIS_PATH)
    swe.set_sid_mode(SIDEREAL_MODE)
    curr_jd = jd_start
    last_sign_idx = -1
    lagna_start_jd = jd_start
    step = 1.0 / (24 * 60) 
    base_dt = dt_from_jd(jd_start, tz)
    base_date = base_dt.date() if base_dt else None
    def fmt_lagna_time(jd):
        dt = dt_from_jd(jd, tz)
        if not dt: return "---"
        if base_date and dt.date() != base_date: return dt.strftime("%d %b, %I:%M %p")
        return dt.strftime("%I:%M %p")
    while curr_jd < jd_end:
        try:
            trop_asc = swe.houses(curr_jd, lat, lon, b'P')[0][0]
            ayan = swe.get_ayanamsa(curr_jd)
            sid_asc = (trop_asc - ayan) % 360
            curr_sign_idx = int(sid_asc / 30)
            if last_sign_idx != -1 and curr_sign_idx != last_sign_idx:
                rashi_name = RASHIS[last_sign_idx]
                icon = RASHI_ICONS.get(rashi_name, "")
                lagnas.append({"name": rashi_name.split(' ')[0], "icon": icon, "start": fmt_lagna_time(lagna_start_jd), "end": fmt_lagna_time(curr_jd), "start_jd": lagna_start_jd, "end_jd": curr_jd})
                lagna_start_jd = curr_jd
            last_sign_idx = curr_sign_idx
        except Exception: pass
        curr_jd += step
    if last_sign_idx != -1:
        rashi_name = RASHIS[last_sign_idx]
        icon = RASHI_ICONS.get(rashi_name, "")
        lagnas.append({"name": rashi_name.split(' ')[0], "icon": icon, "start": fmt_lagna_time(lagna_start_jd), "end": fmt_lagna_time(jd_end), "start_jd": lagna_start_jd, "end_jd": jd_end})
    return lagnas

def get_festivals_details(jd, tithi_idx, sun_long, dt_obj, nak_idx, moon_rashi_idx):
    """Matches Tithi, Nakshatra, and Month to the Festival Database."""
    festivals = []
    def get_image_url(name):
        for key, url in FESTIVAL_IMAGES_STATIC.items():
            if key in name: 
                if url.startswith("/static"):
                    rel_path = url.lstrip("/")
                    # We are in vedic_astro/engine/core.py (2 levels down)
                    # rel_path is from root.
                    # We need to check if file exists in root.
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) # Root
                    abs_path = os.path.join(base_dir, rel_path)
                    if os.path.exists(abs_path): return url
                else: return url 
        seed = sum(ord(c) for c in name)
        safe_name = urllib.parse.quote(name)
        return f"https://image.pollinations.ai/prompt/Hindu%20festival%20{safe_name}%20devotional%20art?width=300&height=200&nologo=true&seed={seed}"
    def add_fest(name):
        if not any(f['name'] == name for f in festivals): festivals.append({"name": name, "image_url": get_image_url(name)})
    greg_key = (dt_obj.month, dt_obj.day)
    if greg_key in GREGORIAN_FESTIVALS: add_fest(GREGORIAN_FESTIVALS[greg_key])
    if tithi_idx >= 0:
        paksha_code = 0 if tithi_idx < 15 else 1
        tithi_in_paksha = tithi_idx % 15
        sun_rashi_at_new_moon = int((sun_long - (tithi_idx * 0.9856)) / 30)
        lunar_month_idx = (sun_rashi_at_new_moon + 1) % 12 
        key = (lunar_month_idx, paksha_code, tithi_in_paksha)
        if key in FESTIVAL_DB: add_fest(FESTIVAL_DB[key])
        if paksha_code == 0 and tithi_in_paksha == 3: add_fest("Vinayaka Chavithi (Masik)")
        if paksha_code == 1 and tithi_in_paksha == 3: add_fest("Sankashta Hara Chavithi")
        if paksha_code == 0 and tithi_in_paksha == 5: add_fest("Subrahmanya Shashti")
        if paksha_code == 0 and tithi_in_paksha == 7: add_fest("Durgashtami")
        if paksha_code == 1 and tithi_in_paksha == 7: add_fest("Kalashtami")
        if tithi_in_paksha == 10: prefix = "Shukla" if paksha_code == 0 else "Krishna"; add_fest(f"{prefix} Ekadashi")
        if tithi_in_paksha == 12: add_fest("Pradosham")
        if paksha_code == 1 and tithi_in_paksha == 13: add_fest("Masik Shivaratri")
        if paksha_code == 1 and tithi_in_paksha == 14: add_fest("Amavasya")
        if paksha_code == 0 and tithi_in_paksha == 14: add_fest("Purnima")
    if nak_idx >= 0:
        if nak_idx == 2: add_fest("Krittika (Karthigai)")
        if nak_idx == 3: add_fest("Rohini Vratam")
    return festivals

def fetch_month_day_data(loc, date_str):
    """
    Lightweight fetch function for the Month View.
    Returns only essential data (Tithi, Nakshatra, Festival status) to improve performance.
    """
    setup_swisseph()
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    tz = loc['tz']
    jd_noon = jd_from_dt(tz.localize(datetime(dt.year, dt.month, dt.day, 12, 0)))
    rise, _ = calc_sun_rise_set(jd_noon, loc['lat'], loc['lon'])
    rise_next, _ = calc_sun_rise_set(jd_noon + 1, loc['lat'], loc['lon'])
    sun_long, moon_long = get_pos(rise)
    tithi_at_sunrise_idx = int(((moon_long - sun_long) % 360) / 12)
    nak_idx_sunrise = int(moon_long / 13.333333)
    moon_rashi_idx = int(moon_long / 30)
    lunar_month_name, is_adika_month = get_chandramasa(jd_noon)
    if not lunar_month_name:
        # Fallback
        sun_rashi_new_moon = int((sun_long - (tithi_at_sunrise_idx * 1.0)) / 30)
        lunar_month_name = MONTHS[(sun_rashi_new_moon + 1) % 12]
        is_adika_month = False
    fn_tithi = lambda j: (int((get_pos(j)[1] - get_pos(j)[0]) % 360 / 12), 0)
    fn_nak = lambda j: (int(get_pos(j)[1] / 13.333333333), 0)
    tithi_events = get_events(rise, rise_next, fn_tithi, TITHIS, 30)
    nak_events = get_events(rise, rise_next, fn_nak, NAKSHATRAS, 27)
    tithis_to_check = {tithi_at_sunrise_idx}
    for e in tithi_events: tithis_to_check.add(e['index'])
    naks_to_check = {nak_idx_sunrise}
    for e in nak_events: naks_to_check.add(e['index'])
    all_festivals = []
    seen_fest_names = set()
    for t_idx in tithis_to_check:
        fests = get_festivals_details(rise, t_idx, sun_long, dt, -1, moon_rashi_idx)
        for f in fests:
            if f['name'] not in seen_fest_names:
                all_festivals.append(f)
                seen_fest_names.add(f['name'])
    for n_idx in naks_to_check:
        fests = get_festivals_details(rise, -1, sun_long, dt, n_idx, moon_rashi_idx)
        for f in fests:
            if f['name'] not in seen_fest_names:
                all_festivals.append(f)
                seen_fest_names.add(f['name'])
    festivals = all_festivals
    def fmt_dt(jd): 
        d = dt_from_jd(jd, tz)
        if not d: return "---"
        return d.strftime('%b %d, %I:%M %p') if d.date() != dt.date() else d.strftime('%I:%M %p')
    if not tithi_events or not nak_events:
        return {"error": "Could not compute tithi/nakshatra for this date"}
    t_item = tithi_events[0]
    tithi_name = t_item['name'].split(' ')[-1]
    tithi_icon = TITHI_ICONS.get(t_item['name'], "🌑")
    tithi_start = fmt_dt(t_item['start'])
    tithi_end = fmt_dt(t_item['end'])
    n_item = nak_events[0]
    nak_name = n_item['name']
    nak_end = fmt_dt(n_item['end'])
    festival_names = [f['name'] for f in festivals]
    return {
        "tithi": tithi_name, "tithi_icon": tithi_icon,
        "full_tithi_name": t_item['name'],  # e.g. "Shukla Panchami" (with Paksha prefix)
        "tithi_start": tithi_start, "tithi_end": tithi_end,
        "nakshatra": nak_name, "nak_end": nak_end,
        "nakshatra_idx": n_item['index'],
        "moon_rashi_idx": moon_rashi_idx,
        "is_festival": len(festivals) > 0,
        "festival_names": festival_names,
        "lunar_month": lunar_month_name,
        "is_adika": is_adika_month,
        "tithi_start_jd": t_item['start'], # Needed for muhurtha matching
        "tithi_end_jd": t_item['end'],
        "nak_end_jd": n_item['end']
    }

def get_chandramasa(jd_ref):
    """
    Returns the correct Telugu/Vedic lunar month name for the given Julian Day,
    including proper Adika Masa (intercalary month) detection.

    Algorithm (Amanta system):
      1. Find the previous Amavasya (New Moon) by searching backwards.
      2. Find the next Amavasya (New Moon) by searching forward.
      3. Check if the Sun changes Rashi (Sankranti) between those two Amavasyas.
         - If YES  → regular (Nija) month named after the Rashi the Sun enters.
         - If NO   → Adika (intercalary) month; the next month is Nija.

    Returns:
        tuple: (month_name: str, is_adika: bool)
            month_name is e.g. "Ashadha" or "Adika Ashadha"
            is_adika is True when the month is intercalary
    """
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

    def moon_sun_diff(jd):
        """Moon − Sun elongation in degrees [0, 360)."""
        sun = swe.calc_ut(jd, swe.SUN,  flags)[0][0]
        moon = swe.calc_ut(jd, swe.MOON, flags)[0][0]
        return (moon - sun) % 360

    def find_amavasya(start_jd, direction=1, max_days=35):
        """
        Finds the Julian Day of the nearest Amavasya (elongation ≈ 0°) by
        binary-searching in `direction` (+1 forward, -1 backward).
        """
        step = direction * (1.0 / 24)  # 1-hour steps
        curr = start_jd
        limit = start_jd + direction * max_days

        # Walk until the elongation crosses 0° (i.e. wraps around 360→0)
        prev_diff = moon_sun_diff(curr)
        while (direction == 1 and curr < limit) or (direction == -1 and curr > limit):
            curr += step
            diff = moon_sun_diff(curr)
            # Detect the crossing: elongation drops from ~360° side to ~0° side
            if direction == 1 and prev_diff > 350 and diff < 10:
                break
            if direction == -1 and prev_diff < 10 and diff > 350:
                break
            prev_diff = diff
        else:
            return None  # not found

        # Binary-search refine to within ~1 minute
        t1, t2 = (curr - step, curr) if direction == 1 else (curr, curr - step)
        for _ in range(30):
            mid = (t1 + t2) / 2
            d = moon_sun_diff(mid)
            if d < 180:  # still before new moon (elongation < 180 means waxing)
                t2 = mid
            else:
                t1 = mid
        return (t1 + t2) / 2

    def sun_rashi_at(jd):
        """Sidereal Sun Rashi index 0–11 at a given Julian Day."""
        return int(swe.calc_ut(jd, swe.SUN, flags)[0][0] / 30)

    def find_sankranti_between(jd_start, jd_end):
        """
        Returns the Julian Day of the Sun's sign change (Sankranti) within
        [jd_start, jd_end], or None if the Sun stays in the same Rashi.
        """
        r_start = sun_rashi_at(jd_start)
        r_end   = sun_rashi_at(jd_end)
        if r_start == r_end:
            return None  # No Sankranti → Adika Masa!
        # Binary search for the exact Sankranti moment
        t1, t2 = jd_start, jd_end
        for _ in range(40):
            mid = (t1 + t2) / 2
            if sun_rashi_at(mid) == r_start:
                t1 = mid
            else:
                t2 = mid
        return (t1 + t2) / 2

    try:
        prev_am = find_amavasya(jd_ref, direction=-1)
        if prev_am is None:
            prev_am = jd_ref - 15  # fallback

        next_am = find_amavasya(jd_ref, direction=1)
        if next_am is None:
            next_am = jd_ref + 15  # fallback

        sankranti_jd = find_sankranti_between(prev_am, next_am)

        if sankranti_jd is None:
            # No Sankranti in this lunar month → Adika Masa
            # Name it after the Rashi the Sun will enter in the NEXT lunar month
            next_next_am = find_amavasya(next_am + 1, direction=1)
            if next_next_am is None:
                next_next_am = next_am + 30
            sankranti_jd2 = find_sankranti_between(next_am, next_next_am)
            if sankranti_jd2:
                rashi_idx = sun_rashi_at(sankranti_jd2 + 0.5)
            else:
                rashi_idx = (sun_rashi_at(next_am) + 1) % 12
            month_name = f"Adika {MONTHS[rashi_idx % 12]}"
            return month_name, True
        else:
            # Normal month: named after the Rashi the Sun enters (the Sankranti sign)
            rashi_idx = sun_rashi_at(sankranti_jd + 0.5)  # just after Sankranti
            month_name = MONTHS[rashi_idx % 12]
            return month_name, False

    except Exception as e:
        print(f"[get_chandramasa] Error: {e}")
        # Graceful fallback to old approximation
        return None, False


def fetch_panchang(loc_str_or_dict, date_str):
    """
    Main Panchang calculation function.
    Returns comprehensive data including Tithi, Nakshatra, Yoga, Karana, Muhurtas, Rasi, etc.
    
    Args:
        loc_str_or_dict: Dictionary with loc details OR string name.
        date_str (str): Date in YYYY-MM-DD format.
        
    Returns:
        dict: Complete panchang data structure for the frontend.
    """
    setup_swisseph()
    if isinstance(loc_str_or_dict, dict): loc = loc_str_or_dict
    else: loc = get_location(loc_str_or_dict)
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
    day_len = set_ - rise
    def get_kalam(k_map):
        s = rise + ((k_map[w_idx]-1) * (day_len/8))
        d_start = dt_from_jd(s, tz)
        d_end = dt_from_jd(s + day_len/8, tz)
        if not d_start or not d_end: return "---"
        s_fmt = d_start.strftime('%b %d, %I:%M %p') if d_start.date() != dt.date() else d_start.strftime('%I:%M %p')
        e_fmt = d_end.strftime('%b %d, %I:%M %p') if d_end.date() != dt.date() else d_end.strftime('%I:%M %p')
        return f"{s_fmt} - {e_fmt}"
    rahu_time = get_kalam(RAHU_KEY)
    yama_time = get_kalam(YAMA_KEY)
    guli_time = get_kalam(GULI_KEY)
    
    # Restore Sunrise-based indices for general day calculations (Festivals, Tarabalam etc)
    tithi_idx = int(((moon_long - sun_long) % 360) / 12)
    nak_idx = int(moon_long / 13.333333)
    sun_nak_idx = int(sun_long / 13.333333)

    # Correct Chandramasa Calculation (Amanta) with Adika Masa detection
    chandramasa_name, is_adika = get_chandramasa(jd_noon)
    if not chandramasa_name:
        # Fallback to approximation if get_chandramasa failed
        sun_rashi_new_moon = int((sun_long - (tithi_idx * 1.0)) / 30)
        chandramasa_name = MONTHS[(sun_rashi_new_moon + 1) % 12]
        is_adika = False
    current_chandramasa = chandramasa_name
    
    # Now call get_samvat_details with lunar info
    samvat = get_samvat_details(dt, lunar_month=current_chandramasa, tithi=tithi_idx)
    samvat["chandramasa"] = current_chandramasa
    samvat["is_adika"] = is_adika
    
    ritu_ayana = get_ritu_ayana_details(rise)
    muhurtas = calculate_muhurtas(rise, set_, rise_next, w_idx)

    fn_tithi = lambda j: (int((get_pos(j)[1] - get_pos(j)[0]) % 360 / 12), 0)
    fn_nak = lambda j: (int(get_pos(j)[1] / 13.333333333), 0)
    fn_yoga = lambda j: (int((get_pos(j)[1] + get_pos(j)[0]) % 360 / 13.333333333), 0)
    fn_karana = lambda j: (int((get_pos(j)[1] - get_pos(j)[0]) % 360 / 6), 0)
    tithi_events = get_events(rise, rise_next, fn_tithi, TITHIS, 30)
    nak_events = get_events(rise, rise_next, fn_nak, NAKSHATRAS, 27)

    # Calculate Daily Nivas/Shool with full timings
    nivas_shool = get_daily_nivas_details(rise, rise_next, w_idx, tithi_events, nak_events, moon_rashi_idx, sun_rashi_idx, sun_long, tz)
    
    # Generate Moon Rashi Events locally for Chandrabalam Logic
    # We need to find Moon Sign changes for the period `rise` to `rise_next`
    target_next_rashi = (moon_rashi_idx + 1) % 12
    def check_sign(t): return int(swe.calc_ut(t, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)[0][0] / 30)
    
    rashi_events_list = []
    # Current rashi
    r_end = find_trans(rise, check_sign, target_next_rashi)
    
    if not r_end or r_end >= rise_next:
        rashi_events_list.append({'index': moon_rashi_idx, 'start': rise, 'end': rise_next})
    else:
        rashi_events_list.append({'index': moon_rashi_idx, 'start': rise, 'end': r_end})
        # Next rashi
        rashi_events_list.append({'index': target_next_rashi, 'start': r_end, 'end': rise_next})

    epoch = get_epoch_details(jd_noon, dt)
    chandrabalam_tarabalam = get_chandrabalam_tarabalam_details(rashi_events_list, nak_events, tz, rise)
    udaya_lagna = get_udaya_lagna_details(rise, rise_next, tz, loc['lat'], loc['lon'])
    panchaka_rahita = get_panchaka_rahita_details(udaya_lagna, tithi_events, nak_events, w_idx)
    festivals = get_festivals_details(rise, tithi_idx, sun_long, dt, nak_idx, moon_rashi_idx)
    dinamana = fmt_duration(rise, set_)
    ratrimana = fmt_duration(set_, rise_next)
    madhyahna_jd = rise + (set_ - rise) / 2
    def fmt_dt(jd): 
        d = dt_from_jd(jd, tz)
        if not d: return "---"
        return d.strftime('%b %d, %I:%M %p') if d.date() != dt.date() else d.strftime('%I:%M %p')
    def fmt_range(start, end): return f"{fmt_dt(start)} - {fmt_dt(end)}"
    calc_timings = get_calculated_timings(nak_events, w_idx, sun_nak_idx, tithi_events, rise, rise_next, tz)
    # --- Fix for Amrit/Varjyam (Calculate for all active Nakshatras) ---
    def get_special_timing(events, start_offsets, duration_mins=96):
        timings = []
        duration_ghatis = duration_mins / 24.0
        
        # Helper to find exact Nakshatra Entry (True Start) and Exit
        def get_true_start_end(nak_idx, ref_jd):
            def check_long(t):
                 l = swe.calc_ut(t, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)[0][0]
                 return (int(l / 13.333333333), 0)
            
            prev = (nak_idx - 1) % 27
            limit = 2.0 # Look back 2 days max
            
            t_start = find_trans(ref_jd - limit, check_long, prev, limit=limit)
            
            if t_start:
                 t_end = find_trans(t_start + 0.1, check_long, nak_idx, limit=limit)
            else:
                 t_end = None
            return t_start, t_end

        for n in events:
            idx = n['index']
            
            ref = n['end'] if n['end'] else (n['start'] + 0.5 if n['start'] else rise)
            
            true_start, true_end = get_true_start_end(idx, ref)
            if not true_start: 
                 true_start = n['start']
            if not true_end:
                 true_end = true_start + 1.0 if true_start else rise + 1.0
            
            if not true_start: continue

            n_duration = true_end - true_start
            
            offset_ghati = start_offsets[idx]
            # Proportional calculation based on actual Nakshatra duration being 60 ghatis
            s_jd = true_start + (n_duration * (offset_ghati / 60.0))
            e_jd = s_jd + (n_duration * (duration_ghatis / 60.0))
            
            # Check overlap with "Today"
            if e_jd < rise: continue
            if s_jd > rise_next: continue 
            
            s_fmt = fmt_dt(s_jd)
            e_fmt = fmt_dt(e_jd)
            timings.append(f"{s_fmt} - {e_fmt}")
            
        return " | ".join(timings) if timings else "None"

    varjyam_time = get_special_timing(nak_events, VARJYAM_STARTS)
    amrit_time = get_special_timing(nak_events, AMRIT_STARTS)
    moon_rashi_start, moon_rashi_end = get_entry_exit_times(jd_noon, swe.MOON, moon_rashi_idx, 30, tz)
    sun_rashi_start, sun_rashi_end = get_entry_exit_times(jd_noon, swe.SUN, sun_rashi_idx, 30, tz)
    sun_nak_start, sun_nak_end = get_entry_exit_times(jd_noon, swe.SUN, sun_nak_idx, 13.333333333, tz)
    
    data = {"meta": {"location": loc['name'], "date": dt_from_jd(rise, tz).strftime("%A, %d %B %Y"), "sunrise": fmt_dt(rise), "sunset": fmt_dt(set_), "moonrise": fmt_dt(moon_rise), "moonset": fmt_dt(moon_set)}, "details": {"moonsign": RASHIS[moon_rashi_idx], "sunsign": RASHIS[sun_rashi_idx], "sun_nakshatra": NAKSHATRAS[sun_nak_idx], "samvat": samvat, "ritu_ayana": ritu_ayana, "dinamana": dinamana, "ratrimana": ratrimana, "madhyahna": fmt_dt(madhyahna_jd), "nivas_shool": nivas_shool, "epoch": epoch, "chandrabalam_tarabalam": chandrabalam_tarabalam, "panchaka_rahita": panchaka_rahita, "udaya_lagna": udaya_lagna, "festivals": festivals, "moonsign_start": moon_rashi_start, "moonsign_end": moon_rashi_end, "sunsign_start": sun_rashi_start, "sunsign_end": sun_rashi_end, "sun_nakshatra_start": sun_nak_start, "sun_nakshatra_end": sun_nak_end}, "tithi": tithi_events, "nakshatra": nak_events, "yoga": get_events(rise, rise_next, fn_yoga, YOGAS, 27), "karana": get_events(rise, rise_next, fn_karana, [], 60, True), "moon_pada": get_events(rise, rise_next, lambda j: (int(get_pos(j)[1] / 3.333333333), 0), PADA_NAMES, 108), "sun_pada": get_events(rise, rise_next, lambda j: (int(get_pos(j)[0] / 3.333333333), 0), PADA_NAMES, 108), "timings": {"brahma": fmt_range(*muhurtas["brahma"]), "pratah": fmt_range(*muhurtas["pratah"]), "vijaya": fmt_range(*muhurtas["vijaya"]), "godhuli": fmt_range(*muhurtas["godhuli"]), "sayahna": fmt_range(*muhurtas["sayahna"]), "nishita": fmt_range(*muhurtas["nishita"]), "dur_day": ", ".join([fmt_range(s, e) for s, e in muhurtas["dur_day"]]), "sarvartha": calc_timings["sarvartha"], "baana": calc_timings["baana"], "vidaal": calc_timings["vidaal"], "anandadi": calc_timings["anandadi"], "tamil": calc_timings["tamil"], "jeevanama": calc_timings["jeevanama"], "netrama": calc_timings["netrama"], "tripushkara": calc_timings["tripushkara"], "rahu": rahu_time, "yama": yama_time, "guli": guli_time, "varjyam": varjyam_time, "amrit": amrit_time}}
    if isinstance(muhurtas["abhijit"], tuple): data["timings"]["abhijit"] = fmt_range(*muhurtas["abhijit"])
    else: data["timings"]["abhijit"] = muhurtas["abhijit"]
    for item in data['tithi']: item['start_fmt'] = fmt_dt(item['start']); item['end_fmt'] = fmt_dt(item['end']); item['icon'] = TITHI_ICONS.get(item['name'], "🌑")
    for item in data['nakshatra']: item['start_fmt'] = fmt_dt(item['start']); item['end_fmt'] = fmt_dt(item['end']); item['icon'] = NAK_ICONS.get(item['name'], "✨")
    for k in ['yoga', 'karana', 'moon_pada', 'sun_pada']:
        for item in data[k]: item['start_fmt'] = fmt_dt(item['start']); item['end_fmt'] = fmt_dt(item['end'])
    return data
