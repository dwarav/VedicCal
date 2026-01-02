import calendar
from flask import Flask, render_template, request
from panchang_engine import fetch_panchang, get_location, fetch_month_day_data
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

if __name__ == '__main__':
    app.run(debug=True)