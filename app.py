from flask import Flask, render_template, request
from panchang_engine import fetch_panchang
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        location = request.form.get('location')
        date = request.form.get('date')
        
        if not location or not date:
            return render_template('index.html', error="Please enter both location and date.")
            
        try:
            result = fetch_panchang(location, date)
            if "error" in result:
                return render_template('index.html', error=result['error'])
            return render_template('result.html', data=result)
        except Exception as e:
            return render_template('index.html', error=f"Calculation Error: {str(e)}")
            
    # Default: Show form
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template('index.html', today=today)

if __name__ == '__main__':
    app.run(debug=True)