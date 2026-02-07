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
    except:
        return False, False

# --- MUHURTHA CALCULATOR ---
def get_monthly_muhurthas(loc, year, month):
    """
    Calculates auspicious muhurthas for Marriage, House Warming, Naming, and Vehicle Purchase
    based on Telugu Panchangam rules.
    """
    setup_swisseph() # Ensure SWISSEPH is setup
    
    # TELEGU RULES
    RULES = {
        "marriage": {
            # Telugu Marriage Naks: Rohini, Mrigashira, Magha, U.Phalguni, Hasta, Swati, 
            # Anuradha, Mula, U.Ashadha, U.Bhadra, Revati (Key ones).
            "naks": ["Rohini", "Mrigashira", "Magha", "Uttara Phalguni", "Hasta", "Swati", "Anuradha", "Mula", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"], 
            # Avoid Rikta tithis (4, 9, 14), Amavasya.
            "tithis": ["Dwitiya", "Tritiya", "Panchami", "Saptami", "Dashami", "Ekadashi", "Trayodashi"], 
            # Avoid Tuesday (1). Some avoid Sunday (6) too for night weddings, but day weddings OK? 
            # Lets stick to strict: No Tue.
            "exclude_days": [1],
            "check_moodami": True
        },
        "gruha": { # House Warming
            # Naks: Rohini, Mrigashira, U.Phalguni, Hasta, Chitra, Swati, Anuradha, U.Ashadha, Shravana, Dhanishta, Shatabhisha, U.Bhadra, Revati.
            "naks": ["Rohini", "Mrigashira", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"],
            "tithis": ["Dwitiya", "Tritiya", "Panchami", "Saptami", "Dashami", "Ekadashi", "Trayodashi"], 
            # Strictly avoid Tue(1), Sat(5), Sun(6).
            "exclude_days": [1, 5, 6],
            "check_moodami": True
        },
        "naming": { # Namakarana
            "naks": ["Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"], 
            "tithis": ["Pratipada", "Dwitiya", "Tritiya", "Panchami", "Saptami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Purnima"], 
            "exclude_days": [], # Generally ok any day if Nakshatra is good
            "check_moodami": False
        },
        "vehicle": { # Vehicle Purchase
            "naks": ["Ashwini", "Rohini", "Punarvasu", "Pushya", "Hasta", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Shatabhisha", "Revati"], 
            "tithis": ["Pratipada", "Tritiya", "Panchami", "Shashthi", "Dashami", "Ekadashi", "Trayodashi", "Purnima"], 
            "exclude_days": [1], # Avoid Tuesday
            "check_moodami": False
        }
    }
    
    cal = calendar.monthcalendar(year, month)
    results = {k: [] for k in RULES.keys()}
    
    # Iterate through every day
    for week in cal:
        for day in week:
            if day == 0: continue 
            
            date_str = f"{year}-{month:02d}-{day:02d}"
            try:
                # Basic check logic
                lite_data = fetch_month_day_data(loc, date_str)
                dt_obj = datetime(year, month, day)
                weekday = dt_obj.weekday() # 0=Mon
                
                # Check Combustion (Moodami) for this day
                # We need JD for combustion check. 
                # fetch_month_day_data uses noon JD internally, let's recalculate or approximate.
                # Just use noon for the day.
                tz = loc['tz']
                jd_noon = jd_from_dt(tz.localize(datetime(year, month, day, 12, 0)))
                
                is_venus, is_guru = get_combustion_status(jd_noon)
                moodami_active = is_venus or is_guru
                
                curr_nak = lite_data['nakshatra'].split(' ')[0]
                curr_tithi = lite_data['tithi']
                tithi_name = curr_tithi.split(' ')[-1]
                
                for cat, rule in RULES.items():
                    # 1. Weekday Check
                    if weekday in rule['exclude_days']: continue
                    
                    # 2. Moodami Check
                    if rule.get('check_moodami') and moodami_active:
                        # Skip if Moodami is active (Combustion)
                        continue
                    
                    # 3. Nakshatra Check
                    nak_match = any(n in curr_nak for n in rule['naks'])
                    
                    # 4. Tithi Check
                    tithi_match = any(t == tithi_name for t in rule['tithis'])
                    
                    # Extra Tithi Exclusions for all (Rikta/Amavasya usually handled by white-list above, but double check)
                    # If Tithi is 'Chaturthi', 'Navami', 'Chaturdashi', 'Amavasya' -> Bad.
                    # Our whitelists exclude them mostly, but "Shashthi", "Ashtami", "Dwadashi" vary per event.
                    
                    if nak_match and tithi_match:
                        full_data = fetch_panchang(loc, date_str)
                        
                        # Add Moodami warning if present but category didn't strictly filter it (optional)
                        warnings = []
                        if moodami_active: warnings.append("Combustion (Moodami) Active")
                        
                        results[cat].append({
                            "date": f"{day} {calendar.month_name[month]}", 
                            "day_name": dt_obj.strftime("%A"), 
                            "nakshatra": curr_nak, 
                            "tithi": curr_tithi, 
                            "full_date": date_str,
                            "tithi_start": lite_data['tithi_start'], 
                            "tithi_end": lite_data['tithi_end'], 
                            "nak_end": lite_data['nak_end'],
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
        return 0 # Handle error gracefully? or throw
        
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
