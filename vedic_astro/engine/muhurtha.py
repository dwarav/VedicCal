import calendar
from datetime import datetime
import swisseph as swe
from .core import fetch_month_day_data, fetch_panchang, setup_swisseph, jd_from_dt

# --- HELPER: COMBUSTION CHECK (MOODAMI) ---
def get_combustion_status(jd):
    """
    Checks if Venus (Shukra) or Jupiter (Guru) is combust (Moodami).
    Moodami is inauspicious for Marriage and House Warming.
    
    Combustion Orb (Approx):
    - Venus: ~10 degrees from Sun is common, but strict Telugu 'Moodami' 
      often refers to specific periods defined in Panchangam. 
      Astronomically we use 8-10 deg.
    - Jupiter: ~11 degrees.
    """
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    
    try:
        sun_res = swe.calc_ut(jd, swe.SUN, flags)
        venus_res = swe.calc_ut(jd, swe.VENUS, flags)
        jup_res = swe.calc_ut(jd, swe.JUPITER, flags)
        
        sun_lon = sun_res[0][0]
        venus_lon = venus_res[0][0]
        jup_lon = jup_res[0][0]
        
        # Calculate minimum difference dealing with 360 wrap
        def ang_diff(a1, a2):
            d = abs(a1 - a2)
            return d if d < 180 else 360 - d

        is_venus_combust = ang_diff(sun_lon, venus_lon) < 10.0 # Shukra Moudyami
        is_guru_combust = ang_diff(sun_lon, jup_lon) < 11.0    # Guru Moudyami
        
        return is_venus_combust, is_guru_combust
    except Exception:
        return False, False

# --- MUHURTHA CALCULATOR ---
def get_monthly_muhurthas(loc, year, month):
    """
    Calculates auspicious muhurthas based on Drik Panchangam methodology.
    
    For Griha Pravesh: Checks if ANY time window during the day has an overlap
    of auspicious Nakshatra + auspicious Tithi (excluding Bhadra/Vishti Karana periods).
    This matches drikpanchang.com's approach rather than only checking sunrise values.
    
    For other categories (Marriage, Naming, Vehicle): Uses sunrise-based check.
    """
    setup_swisseph()
    
    # DRIK PANCHANGAM STANDARD RULES
    RULES = {
        "marriage": {
            "naks": ["Rohini", "Mrigashira", "Magha", "Uttara Phalguni", "Hasta", "Swati", "Anuradha", "Mula", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"], 
            "tithis": ["Dwitiya", "Tritiya", "Panchami", "Saptami", "Dashami", "Ekadashi", "Trayodashi"], 
            "exclude_days": [1, 5],  # Avoid Tue, Sat
            "check_moodami": True,
            "shukla_only": True,
            "use_window_check": False  # Sunrise-based check
        },
        "gruha": {  # Griha Pravesh — Drik Panchangam rules
            # Drik Panchangam standard Griha Pravesh Nakshatras (16)
            "naks": ["Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", 
                     "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", 
                     "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", 
                     "Uttara Bhadrapada", "Revati"],
            # Drik Panchangam standard tithis (8)
            "tithis": ["Dwitiya", "Tritiya", "Panchami", "Saptami", "Dashami", 
                       "Ekadashi", "Dwadashi", "Trayodashi"],
            # Avoid only Tue(1) and Sun(6) per Drik Panchangam
            "exclude_days": [1, 6],
            "check_moodami": True,
            "shukla_only": False,  # Drik checks both pakshas
            "use_window_check": True,  # Window-based overlap check
            "avoid_bhadra": True,  # Avoid Vishti Karana (Bhadra)
            # Inauspicious lunar months for Griha Pravesh per Drik Panchangam
            "avoid_lunar_months": ["Chaitra", "Ashada", "Bhadrapada", "Ashwina", "Pausha"]
        },
        "naming": {
            "naks": ["Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"], 
            "tithis": ["Pratipada", "Dwitiya", "Tritiya", "Panchami", "Saptami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Purnima"], 
            "exclude_days": [],
            "check_moodami": False,
            "shukla_only": False,
            "use_window_check": False
        },
        "vehicle": {
            "naks": ["Ashwini", "Rohini", "Punarvasu", "Pushya", "Hasta", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Shatabhisha", "Revati"], 
            "tithis": ["Pratipada", "Tritiya", "Panchami", "Shashthi", "Dashami", "Ekadashi", "Trayodashi", "Purnima"], 
            "exclude_days": [1],
            "check_moodami": False,
            "shukla_only": False,
            "use_window_check": False
        }
    }
    
    cal = calendar.monthcalendar(year, month)
    results = {k: [] for k in RULES.keys()}
    
    for week in cal:
        for day in week:
            if day == 0: continue 
            
            date_str = f"{year}-{month:02d}-{day:02d}"
            try:
                lite_data = fetch_month_day_data(loc, date_str)
                dt_obj = datetime(year, month, day)
                weekday = dt_obj.weekday()
                
                tz = loc['tz']
                jd_noon = jd_from_dt(tz.localize(datetime(year, month, day, 12, 0)))
                is_venus, is_guru = get_combustion_status(jd_noon)
                moodami_active = is_venus or is_guru
                
                curr_nak_full = lite_data['nakshatra']
                curr_tithi_name = lite_data['tithi']
                full_tithi = lite_data.get('full_tithi_name', '')
                is_shukla = full_tithi.startswith('Shukla') or full_tithi == 'Purnima'
                
                # Get lunar month for lunar month restrictions
                lunar_month = lite_data.get('lunar_month', '')
                
                for cat, rule in RULES.items():
                    if weekday in rule['exclude_days']: continue
                    if rule.get('check_moodami') and moodami_active: continue
                    if rule.get('shukla_only') and not is_shukla: continue
                    # Lunar month restriction (Griha Pravesh avoids certain months)
                    if rule.get('avoid_lunar_months') and lunar_month in rule['avoid_lunar_months']: continue
                    
                    if rule.get('use_window_check'):
                        # --- DRIK PANCHANGAM WINDOW-BASED CHECK ---
                        # Fetch full panchang to get all events during the day
                        full_data = fetch_panchang(loc, date_str)
                        if not full_data: continue
                        
                        # Find time windows where auspicious Nak + Tithi overlap
                        nak_events = full_data.get('nakshatra', [])
                        tithi_events = full_data.get('tithi', [])
                        karana_events = full_data.get('karana', [])
                        
                        # Find auspicious nakshatra windows
                        good_nak_windows = []
                        for ne in nak_events:
                            nak_name = ne['name']
                            if nak_name in rule['naks'] and ne.get('start') and ne.get('end'):
                                good_nak_windows.append((ne['start'], ne['end'], nak_name))
                        
                        # Find auspicious tithi windows
                        good_tithi_windows = []
                        for te in tithi_events:
                            tithi_suffix = te['name'].split(' ')[-1]
                            if tithi_suffix in rule['tithis'] and te.get('start') and te.get('end'):
                                good_tithi_windows.append((te['start'], te['end'], te['name']))
                        
                        # Find Bhadra (Vishti) windows to exclude
                        bad_windows = []
                        if rule.get('avoid_bhadra'):
                            for ke in karana_events:
                                if ke['name'] == 'Vishti' and ke.get('start') and ke.get('end'):
                                    bad_windows.append((ke['start'], ke['end']))
                        
                        # Inauspicious Yogas to exclude per Drik Panchangam
                        INAUSPICIOUS_YOGAS = {"Vishkambha", "Atiganda", "Shula", "Ganda", 
                                              "Vyaghata", "Vajra", "Vyatipata", "Parigha", "Vaidhriti"}
                        yoga_events = full_data.get('yoga', [])
                        for ye in yoga_events:
                            if ye['name'] in INAUSPICIOUS_YOGAS and ye.get('start') and ye.get('end'):
                                bad_windows.append((ye['start'], ye['end']))
                        
                        # Find overlapping windows (nak ∩ tithi) minus bad windows
                        best_window = None
                        for ns, ne_jd, nak_name in good_nak_windows:
                            for ts, te_jd, tithi_name in good_tithi_windows:
                                # Calculate overlap
                                overlap_start = max(ns, ts)
                                overlap_end = min(ne_jd, te_jd)
                                if overlap_start >= overlap_end: continue
                                
                                # Subtract Bhadra + inauspicious Yoga periods
                                clean_windows = [(overlap_start, overlap_end)]
                                for bs, be in bad_windows:
                                    new_clean = []
                                    for ws, we in clean_windows:
                                        if be <= ws or bs >= we:
                                            new_clean.append((ws, we))
                                        else:
                                            if bs > ws: new_clean.append((ws, bs))
                                            if be < we: new_clean.append((be, we))
                                    clean_windows = new_clean
                                
                                # Check if any clean window is at least 1 hour (1/24 JD)
                                for ws, we in clean_windows:
                                    duration = we - ws
                                    if duration >= 1/24.0:  # At least 1 hour
                                        if best_window is None or duration > (best_window[1] - best_window[0]):
                                            best_window = (ws, we, nak_name, tithi_name)
                        
                        if best_window:
                            ws_jd, we_jd, best_nak, best_tithi = best_window
                            from .core import dt_from_jd
                            
                            def fmt_muhurta_dt(jd):
                                d = dt_from_jd(jd, tz)
                                if not d: return "---"
                                dt_date = datetime(year, month, day)
                                if d.date() != dt_date.date():
                                    return d.strftime('%b %d, %I:%M %p')
                                return d.strftime('%I:%M %p')
                            
                            muhurta_window = f"{fmt_muhurta_dt(ws_jd)} - {fmt_muhurta_dt(we_jd)}"
                            
                            # Get display info from full_data
                            tithi_display = best_tithi
                            tithi_start_fmt = full_data['tithi'][0].get('start_fmt', '') if full_data.get('tithi') else ''
                            tithi_end_fmt = full_data['tithi'][0].get('end_fmt', '') if full_data.get('tithi') else ''
                            nak_end_fmt = full_data['nakshatra'][0].get('end_fmt', '') if full_data.get('nakshatra') else ''
                            
                            # For display, use nakshatra matching the best window
                            for ne in nak_events:
                                if ne['name'] == best_nak:
                                    nak_end_fmt = ne.get('end_fmt', nak_end_fmt)
                                    break
                            for te in tithi_events:
                                if te['name'] == best_tithi:
                                    tithi_start_fmt = te.get('start_fmt', tithi_start_fmt)
                                    tithi_end_fmt = te.get('end_fmt', tithi_end_fmt)
                                    break
                            
                            warnings = []
                            if moodami_active: warnings.append("Combustion (Moodami) Active")
                            
                            results[cat].append({
                                "date": f"{day} {calendar.month_name[month]}", 
                                "day_name": dt_obj.strftime("%A"), 
                                "nakshatra": best_nak, 
                                "tithi": tithi_display, 
                                "full_date": date_str,
                                "tithi_start": tithi_start_fmt, 
                                "tithi_end": tithi_end_fmt, 
                                "nak_end": nak_end_fmt,
                                "muhurta_window": muhurta_window,
                                "amrit": full_data['timings']['amrit'], 
                                "abhijit": full_data['timings']['abhijit'],
                                "nakshatra_idx": lite_data['nakshatra_idx'],
                                "moon_rashi_idx": lite_data['moon_rashi_idx'],
                                "warnings": warnings 
                            })
                    else:
                        # --- SUNRISE-BASED CHECK (other categories) ---
                        nak_match = curr_nak_full in rule['naks']
                        tithi_match = curr_tithi_name in rule['tithis']
                        
                        if nak_match and tithi_match:
                            full_data = fetch_panchang(loc, date_str)
                            
                            tithi_display = full_data['tithi'][0]['name'] if full_data.get('tithi') else curr_tithi_name
                            tithi_start_fmt = full_data['tithi'][0].get('start_fmt', lite_data['tithi_start']) if full_data.get('tithi') else lite_data['tithi_start']
                            tithi_end_fmt = full_data['tithi'][0].get('end_fmt', lite_data['tithi_end']) if full_data.get('tithi') else lite_data['tithi_end']
                            nak_end_fmt = full_data['nakshatra'][0].get('end_fmt', lite_data['nak_end']) if full_data.get('nakshatra') else lite_data['nak_end']
                            
                            warnings = []
                            if moodami_active: warnings.append("Combustion (Moodami) Active")
                            
                            results[cat].append({
                                "date": f"{day} {calendar.month_name[month]}", 
                                "day_name": dt_obj.strftime("%A"), 
                                "nakshatra": curr_nak_full, 
                                "tithi": tithi_display, 
                                "full_date": date_str,
                                "tithi_start": tithi_start_fmt, 
                                "tithi_end": tithi_end_fmt, 
                                "nak_end": nak_end_fmt,
                                "amrit": full_data['timings']['amrit'], 
                                "abhijit": full_data['timings']['abhijit'],
                                "nakshatra_idx": lite_data['nakshatra_idx'],
                                "moon_rashi_idx": lite_data['moon_rashi_idx'],
                                "warnings": warnings 
                            })
            except Exception as e:
                # print(f"Error processing {date_str}: {e}")
                continue
            
    return results

def get_nak_idx(loc_data, date_str, time_str):
    """
    Calculates Nakshatra Index for a given date/time/location.
    """
    dt_str = f"{date_str} {time_str}"
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return (0, 0) # Return tuple matching normal return type
        
    tz = loc_data['tz']
    # If dt is naive, localize it? 
    # Usually inputs are naive "Wall Time" at that location.
    local_dt = tz.localize(dt)
    jd = jd_from_dt(local_dt)
    setup_swisseph()
    moon_long = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    return int(moon_long / 13.333333333), int(moon_long / 30)

def check_tarabala(birth_nak_idx, day_nak_idx):
    """
    Checks Tara Bala strength.
    """
    # Count from Birth Nak to Day Nak
    count = (day_nak_idx - birth_nak_idx) % 27 + 1
    rem = count % 9
    if rem == 0: rem = 9
    
    # 1=Janma (Bad), 2=Sampat (Good), 3=Vipat (Bad), 4=Kshema (Good), 
    # 5=Pratyak (Bad), 6=Sadhana (Good), 7=Naidhana (Bad), 8=Mitra (Good), 9=Parama Mitra (Good)
    
    TARA_NAMES = {
        1: "Janma (Birth) - Avoid",
        2: "Sampat (Wealth) - Good",
        3: "Vipat (Danger) - Avoid",
        4: "Kshema (Well-being) - Good",
        5: "Pratyak (Obstacles) - Avoid",
        6: "Sadhana (Achievement) - Good",
        7: "Naidhana (Death/Loss) - Avoid",
        8: "Mitra (Friend) - Good",
        9: "Parama Mitra (Best Friend) - Good"
    }
    
    is_good = rem in [2, 4, 6, 8, 9]
    return is_good, TARA_NAMES[rem]

def check_chandrabala(birth_rashi_idx, day_rashi_idx):
    """
    Checks Chandra Bala (Moon Sign Strength).
    Avoid 6, 8, 12 from Birth Rashi.
    """
    count = (day_rashi_idx - birth_rashi_idx) % 12 + 1
    
    # 6=Roga (Bad), 8=Ashtama (Bad), 12=Vyaya (Bad)
    # Some also avoid 1 (Janma), but we'll focus on the strict negatives.
    # Good: 1, 2, 3, 4, 5, 7, 9, 10, 11
    
    is_good = count not in [6, 8, 12]
    
    status_msg = f"{count}th from Moon - "
    if count in [6, 8, 12]: status_msg += "Bad (Avoid)"
    else: status_msg += "Good"
    
    return is_good, status_msg

def filter_marriage_muhurthas(marriage_dates, bride_data, groom_data):
    """
    Filters using Tara Bala AND Chandra Bala.
    bride_data/groom_data = (nak_idx, rashi_idx)
    """
    b_nak, b_rashi = bride_data
    g_nak, g_rashi = groom_data
    
    personalized = []
    for item in marriage_dates:
        day_nak = item.get('nakshatra_idx')
        day_rashi = item.get('moon_rashi_idx')
        
        if day_nak is None or day_rashi is None: continue
        
        # Tara Bala
        bt_good, bt_msg = check_tarabala(b_nak, day_nak)
        gt_good, gt_msg = check_tarabala(g_nak, day_nak)
        
        # Chandra Bala
        bc_good, bc_msg = check_chandrabala(b_rashi, day_rashi)
        gc_good, gc_msg = check_chandrabala(g_rashi, day_rashi)
        
        if bt_good and gt_good and bc_good and gc_good:
            # Add to list
            item_copy = item.copy()
            item_copy['compatibility'] = {
                "bride_tara": bt_msg,
                "groom_tara": gt_msg,
                "bride_chandra": bc_msg,
                "groom_chandra": gc_msg
            }
            personalized.append(item_copy)
            
    return personalized
