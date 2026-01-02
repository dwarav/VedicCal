import calendar
from flask import Flask, render_template, request
from panchang_engine import fetch_panchang
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    location = "Bangalore, India" 
    date = datetime.now().strftime("%Y-%m-%d")
    error = None
    is_first_load = False
    
    if request.method == 'POST':
        user_loc = request.form.get('location')
        user_date = request.form.get('date')
        if user_loc and user_date:
            location = user_loc
            date = user_date
        else:
            error = "Please provide both location and date."
    else:
        is_first_load = True

    try:
        data = fetch_panchang(location, date)
        if "error" in data:
            error = data["error"]
            data = None
    except Exception as e:
        error = str(e)
        data = None

    return render_template('home.html', data=data, today=date, location_val=location, error=error, is_first_load=is_first_load)

@app.route('/month', methods=['GET', 'POST'])
def monthly_view():
    today = datetime.now()
    year = today.year
    month = today.month
    location = "Bangalore, India"

    if request.method == 'POST':
        if request.form.get('month_year'):
            ym_str = request.form.get('month_year')
            year, month = map(int, ym_str.split('-'))
        if request.form.get('location'):
            location = request.form.get('location')

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
                    p_data = fetch_panchang(location, date_str)
                    
                    # Get Main Tithi & Nakshatra (First one at Sunrise)
                    t_item = p_data['tithi'][0]
                    n_item = p_data['nakshatra'][0]

                    day_info = {
                        "day": day,
                        "date_str": date_str,
                        
                        # Tithi Data
                        "tithi": t_item['name'].split(' ')[-1],
                        "tithi_icon": t_item.get('icon', ''),
                        "tithi_start": t_item['start_fmt'],
                        "tithi_end": t_item['end_fmt'],
                        
                        # Nakshatra Data
                        "nakshatra": n_item['name'],
                        "nak_start": n_item['start_fmt'],
                        "nak_end": n_item['end_fmt'],
                        
                        # Festival
                        "is_festival": len(p_data['details']['festivals']) > 0,
                        "festival_name": p_data['details']['festivals'][0]['name'] if p_data['details']['festivals'] else ""
                    }
                    week_data.append(day_info)
                except:
                    week_data.append({"day": day, "error": True})
        
        calendar_data.append(week_data)

    return render_template('month.html', 
                           calendar_data=calendar_data, 
                           month_name=month_name, 
                           year=year, 
                           location=location,
                           current_ym=f"{year}-{month:02d}")

if __name__ == '__main__':
    app.run(debug=True)