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


# ... (Keep existing imports) ...
from panchang_engine import get_horoscope_by_birth_details, get_location

@app.route('/horoscope', methods=['GET', 'POST'])
def horoscope_view():
    # Defaults
    birth_date = ""
    birth_time = ""
    location_name = "Bangalore, India"
    name = ""
    gender = "Male"
    data = None
    bio_details = {} # Store formatted details for the view

    if request.method == 'POST':
        name = request.form.get('name', 'User')
        gender = request.form.get('gender', 'Male')
        birth_date = request.form.get('birth_date')
        birth_time = request.form.get('birth_time')
        location_name = request.form.get('location')
        
        if birth_date and birth_time and location_name:
            # 1. Get Coordinates
            loc = get_location(location_name)
            
            if loc:
                # 2. Calculate Horoscope
                data = get_horoscope_by_birth_details(loc, birth_date, birth_time, name)
                
                # 3. Format Date/Time for Display (e.g., "December 12, 1977 Monday")
                dt_obj = datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M")
                formatted_date = dt_obj.strftime("%B %d, %Y %A")
                formatted_time = dt_obj.strftime("%I:%M %p IST (+05:30)") # Assuming IST for now
                
                # 4. Prepare Bio Data
                bio_details = {
                    "Name": name,
                    "Gender": gender,
                    "Birth Date": formatted_date,
                    "Birth Time": formatted_time,
                    "Place of Birth": loc['name'],
                    "Nakshatra": data['nakshatra'],
                    "Rasi": data['moon_sign'],
                    "Ayanamsa": data.get('ayanamsa_val', "Lahiri (Calculated)")
                }
                
                # 5. Add Placeholder Predictions
                sign = data['moon_sign'].split(' ')[0]
                data["predictions"] = {
                    "daily": f"Today is a favorable day for {sign} rashi. Financial gains are indicated.",
                    "weekly": f"This week requires patience for {sign}. Career growth is steady.",
                    "yearly": f"2025 brings transformation for {sign}. Saturn's transit is favorable."
                }

    return render_template('horoscope.html', 
                           data=data, 
                           bio=bio_details,
                           birth_date=birth_date, 
                           birth_time=birth_time, 
                           location=location_name,
                           name=name,
                           gender=gender)

if __name__ == '__main__':
    app.run(debug=True)