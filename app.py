from flask import Flask, render_template, request
from panchang_engine import fetch_panchang
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    # 1. Set Defaults (First Load)
    # You can change this default to your preferred city
    location = "Rajamahendravaram, India" 
    date = datetime.now().strftime("%Y-%m-%d")
    
    error = None
    
    # 2. Handle User Search
    if request.method == 'POST':
        user_loc = request.form.get('location')
        user_date = request.form.get('date')
        
        if user_loc and user_date:
            location = user_loc
            date = user_date
        else:
            error = "Please provide both location and date."

    # 3. Calculate Panchang
    try:
        data = fetch_panchang(location, date)
        if "error" in data:
            error = data["error"]
            data = None
    except Exception as e:
        error = str(e)
        data = None

    # 4. Render Single Page
    return render_template('home.html', data=data, today=date, location_val=location, error=error)

if __name__ == '__main__':
    app.run(debug=True)