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
                            "warnings": warnings 
                        })
            except Exception as e:
                # print(f"Error processing {date_str}: {e}")
                continue
            
    return results
