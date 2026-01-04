import calendar
from flask import Flask, render_template, request
from panchang_engine import fetch_panchang, get_location, fetch_month_day_data, get_monthly_muhurthas, get_horoscope_by_birth_details, get_location
from datetime import datetime
import pytz

app = Flask(__name__)

# --- HARDCODED FALLBACK (No API Call) ---
def get_default_location_data():
    return {
        'name': "Bangalore, India",
        'lat': 12.9716,
        'lon': 77.5946,
        'tz': pytz.timezone('Asia/Kolkata')
    }

@app.route('/', methods=['GET', 'POST'])
def home():
    # Default: Use Hardcoded Data initially to save API calls
    loc_data = get_default_location_data()
    location_name = loc_data['name']
    
    date = datetime.now().strftime("%Y-%m-%d")
    error = None
    is_first_load = False
    
    if request.method == 'POST':
        user_loc = request.form.get('location')
        user_date = request.form.get('date')
        
        if user_loc and user_date:
            date = user_date
            location_name = user_loc
            
            # Try finding user location
            fetched_loc = get_location(user_loc)
            if fetched_loc:
                loc_data = fetched_loc
            else:
                # If fail, keep default but show error
                error = f"Could not find '{user_loc}'. Using default."
        else:
            error = "Please provide both location and date."
    else:
        is_first_load = True

    try:
        # Pass the DICTIONARY, not the string
        data = fetch_panchang(loc_data, date)
        if "error" in data:
            error = data["error"]
            data = None
    except Exception as e:
        error = str(e)
        data = None

    return render_template('home.html', 
                           data=data, 
                           today=date, 
                           location_val=location_name, 
                           error=error, 
                           is_first_load=is_first_load)

@app.route('/month', methods=['GET', 'POST'])
def monthly_view():
    today = datetime.now()
    year = today.year
    month = today.month
    
    # Start with Hardcoded Default
    loc_data = get_default_location_data()
    loc_name_display = loc_data['name']

    if request.method == 'POST':
        if request.form.get('month_year'):
            ym_str = request.form.get('month_year')
            year, month = map(int, ym_str.split('-'))
        
        if request.form.get('location'):
            req_loc = request.form.get('location')
            # Try fetching new location
            found_loc = get_location(req_loc)
            if found_loc:
                loc_data = found_loc
                loc_name_display = req_loc
            # If not found, it silently falls back to Bangalore (loc_data remains default)

    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    calendar_data = []
    
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                try:
                    # USE LITE FUNCTION with VALID LOC DATA
                    day_data = fetch_month_day_data(loc_data, date_str)
                    
                    day_info = {
                        "day": day,
                        "date_str": date_str,
                        **day_data
                    }
                    week_data.append(day_info)
                except Exception as e:
                    print(f"Error for {date_str}: {e}")
                    week_data.append({"day": day, "error": True})
        
        calendar_data.append(week_data)

    return render_template('month.html', 
                           calendar_data=calendar_data, 
                           month_name=month_name, 
                           year=year, 
                           location=loc_name_display, 
                           current_ym=f"{year}-{month:02d}")


@app.route('/muhurtha', methods=['GET', 'POST'])
def muhurtha_view():
    today = datetime.now()
    year = today.year
    month = today.month
    
    # Default Location Logic (Same as other pages)
    loc_name = "Bangalore, India"
    loc_data = {
        'name': "Bangalore, India",
        'lat': 12.9716,
        'lon': 77.5946,
        'tz': pytz.timezone('Asia/Kolkata')
    }

    if request.method == 'POST':
        if request.form.get('month_year'):
            ym_str = request.form.get('month_year')
            year, month = map(int, ym_str.split('-'))
        
        if request.form.get('location'):
            loc_name = request.form.get('location')
            found_loc = get_location(loc_name)
            if found_loc:
                loc_data = found_loc

    # Calculate Muhurthas
    muhurtha_data = get_monthly_muhurthas(loc_data, year, month)
    month_name = calendar.month_name[month]

    return render_template('muhurtha.html', 
                           muhurtha_data=muhurtha_data, 
                           month_name=month_name, 
                           year=year, 
                           location=loc_name, 
                           current_ym=f"{year}-{month:02d}")



@app.route('/horoscope', methods=['GET', 'POST'])
def horoscope_view():
    birth_date = ""
    birth_time = ""
    city_name = "Bangalore, India" # Default
    data = None
    
    if request.method == 'POST':
        birth_date = request.form.get('birth_date')
        birth_time = request.form.get('birth_time')
        city_name = request.form.get('location')
        
        if birth_date and birth_time and city_name:
            # Get Coords
            loc = get_location(city_name)
            if loc:
                # Calculate using local Swiss Ephemeris (100% Accurate)
                data = get_horoscope_by_birth_details(loc, birth_date, birth_time)
            
            # (Optional) Add dummy predictions based on Sign
            # Real predictions would require a massive database
            if data and "moon_sign" in data:
                sign = data['moon_sign'].split(' ')[0] # Get just the name
                data["predictions"] = {
                    "daily": f"Today is a good day for {sign} to focus on personal growth.",
                    "weekly": f"This week brings new opportunities in career for {sign}.",
                    "yearly": f"2025 is a transformative year for {sign} natives."
                }

    return render_template('horoscope.html', data=data, 
                           birth_date=birth_date, birth_time=birth_time, location=city_name)


if __name__ == '__main__':
    app.run(debug=True)