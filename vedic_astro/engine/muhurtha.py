import calendar
from datetime import datetime
from .core import fetch_month_day_data, fetch_panchang

# --- MUHURTHA CALCULATOR ---
def get_monthly_muhurthas(loc, year, month):
    """
    Calculates auspicious muhurthas for Marriage, House Warming, Naming, and Vehicle Purchase
    for a given month and location.

    Args:
        loc (dict): Location dictionary with 'lat', 'lon', 'tz'.
        year (int): Year (e.g., 2024).
        month (int): Month (1-12).

    Returns:
        dict: A dictionary with keys 'marriage', 'gruha', 'naming', 'vehicle',
              each containing a list of auspicious dates and details.
    """
    # Define rules for different types of Muhurthas
    # naks: Good Nakshatras
    # tithis: Good Tithis
    # exclude_days: Wed (0=Mon, ... 6=Sun) to exclude? No, Python weekend is 0=Mon, 6=Sun. 
    # Actually swisseph/standard python: 0=Monday, 6=Sunday.
    # Logic below assumes standard python weekday.
    RULES = {
        "marriage": {
            "naks": ["Rohini", "Mrigashira", "Magha", "Uttara Phalguni", "Hasta", "Swati", "Anuradha", "Mula", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"], 
            "tithis": ["Dwitiya", "Tritiya", "Panchami", "Saptami", "Dashami", "Ekadashi", "Trayodashi"], 
            "exclude_days": [1, 6] # Exclude Tuesday (1) and Saturday (5)? Wait. 
            # 0:Mon, 1:Tue, 2:Wed, 3:Thu, 4:Fri, 5:Sat, 6:Sun.
            # So 1=Tuesday, 6=Sunday? Commonly Tuesday implies Mars (bad), Sunday implies Sun (often avoided for marriage).
        },
        "gruha": { # House Warming
            "naks": ["Rohini", "Mrigashira", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"], 
            "tithis": ["Dwitiya", "Tritiya", "Panchami", "Shashthi", "Saptami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi"], 
            "exclude_days": [1, 6] # Avoid Tuesday and Sunday
        },
        "naming": { # Namakarana
            "naks": ["Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"], 
            "tithis": ["Pratipada", "Dwitiya", "Tritiya", "Panchami", "Saptami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Purnima"], 
            "exclude_days": [] 
        },
        "vehicle": { # Vehicle Purchase
            "naks": ["Ashwini", "Rohini", "Punarvasu", "Pushya", "Hast", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Shatabhisha", "Revati"], 
            "tithis": ["Tritiya", "Panchami", "Shashthi", "Dashami", "Ekadashi", "Purnima"], 
            "exclude_days": [1] # Avoid Tuesday
        }
    }
    
    cal = calendar.monthcalendar(year, month)
    results = {k: [] for k in RULES.keys()}
    
    # Iterate through every day of the month
    for week in cal:
        for day in week:
            if day == 0: continue # Skip padding days
            
            date_str = f"{year}-{month:02d}-{day:02d}"
            try:
                # Fetch basic panchang data efficiently
                lite_data = fetch_month_day_data(loc, date_str)
                dt_obj = datetime(year, month, day)
                weekday = dt_obj.weekday()
                
                curr_nak = lite_data['nakshatra'].split(' ')[0]
                curr_tithi = lite_data['tithi']
                tithi_name = curr_tithi.split(' ')[-1]
                
                # Check against rules for each category
                for cat, rule in RULES.items():
                    if weekday in rule['exclude_days']: continue
                    
                    nak_match = any(n in curr_nak for n in rule['naks'])
                    tithi_match = any(t == tithi_name for t in rule['tithis'])
                    
                    # Special exclusions
                    if "Amavasya" in curr_tithi or "Chaturthi" in tithi_name or "Navami" in tithi_name: 
                        tithi_match = False
                    
                    if nak_match and tithi_match:
                        # Fetch full details if matches to get timings
                        full_data = fetch_panchang(loc, date_str)
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
                            "abhijit": full_data['timings']['abhijit']
                        })
            except: continue
            
    return results
