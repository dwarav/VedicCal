from flask import Flask, render_template, request
from panchang_engine import fetch_panchang
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    # Defaults
    location = "Rajamahendravaram, India" 
    date = datetime.now().strftime("%Y-%m-%d")
    
    error = None
    is_first_load = False # Flag to control auto-detection
    
    if request.method == 'POST':
        # User manually searched or Auto-location script submitted
        user_loc = request.form.get('location')
        user_date = request.form.get('date')
        
        if user_loc and user_date:
            location = user_loc
            date = user_date
        else:
            error = "Please provide both location and date."
    else:
        # Initial GET request (Page Open)
        is_first_load = True 

    # Calculate Panchang
    try:
        data = fetch_panchang(location, date)
        if "error" in data:
            error = data["error"]
            data = None
    except Exception as e:
        error = str(e)
        data = None

    return render_template('home.html', 
                           data=data, 
                           today=date, 
                           location_val=location, 
                           error=error,
                           is_first_load=is_first_load) # Pass the flag

if __name__ == '__main__':
    app.run(debug=True)
    # # app.run(host="0.0.0.0", port=8012, debug=False)  # port matches your Service
    # port = int(os.environ.get("PORT", 8080))
    # app.run(host="0.0.0.0", port=port, debug=False)

    