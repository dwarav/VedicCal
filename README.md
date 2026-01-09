# VedicCal - Advanced Vedic Astrology Web App

**VedicCal** is a high-precision, feature-rich Vedic Astrology and Panchang application built with Python and Flask. It leverages the **Swiss Ephemeris** for astronomical accuracy and provides detailed horoscopes, Sudarshana Chakra analysis, and life predictions.

## 🌟 Key Features

### 🔭 Precision Astrology
- **Swiss Ephemeris Core**: Utilizes `pyswisseph` with high-precision ephemeris files (in `ephe/` directory) for accurate planetary calculations (Graha Sthithi).
- **Ayanamsa**: Supports Lahiri Ayanamsa (Chitra Paksha).

### 🔮 Horoscope & Kundli
- **Planetary Positions**: Precise longitudes, rashi, and nakshatra placements for Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, and Ketu.
- **Charts**:
    - **Lagna Chart**: The main birth chart.
    - **Sudarshana Chakra**: Visual representation combining Lagna, Moon, and Sun charts for holistic analysis.
- **Vimshottari Dasha**: Accurate calculation of Mahadasha and Antardasha periods.
- **Life Predictions (Lagna Phal)**: Detailed insights into:
    - 👤 **General Nature**
    - 💼 **Career & Finance**
    - ❤️ **Marriage & Love**
    - 🏥 **Health**

### 📅 Advanced Panchang
- **Daily Elements**: Vara (Weekday), Tithi, Nakshatra, Yoga, Karana.
- **Fortnight**: Paksha (Shukla/Krishna) detection.
- **Special Times**: Accurate Rahu Kalam, Yamaganda, and Gulika Kalam based on sunrise/sunset.
- **Sun & Moon**: Sunrise, Sunset, Moonrise, Moonset times for any location.

### 🎨 Modern UI
- **Responsive Design**: Clean, mobile-friendly interface built with Bootstrap 5.
- **Interactive Input**: Auto-location detection and extensive city search database.
- **Visuals**: 
    - Dynamic SVG Charts for Sudarshana Chakra.
    - Grid-based prediction cards with intuitive icons.
    - Decorative Vedic-themed aesthetic.

## 🛠️ Technology Stack
- **Backend**: Python 3.9+, Flask
- **Astrology Library**: `pyswisseph` (Swiss Ephemeris)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, FontAwesome
- **Geodata**: `geopy`, `timezonefinder`

## 🚀 Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/VedicCal.git
    cd VedicCal
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ephemeris Files**
    Ensure you have the Swiss Ephemeris files in the `ephe/` directory.

## 🏃‍♂️ Usage

1.  **Run the Application**
    ```bash
    python app.py
    ```

2.  **Access in Browser**
    Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

3.  **Generate Horoscope**
    - Enter Name, Date, Time.
    - Enter Birth Place (uses auto-complete).
    - Click **Get Horoscope**.

## 📂 Project Structure

```
VedicCal/
├── app.py                 # Main Flask Application
├── panchang_engine.py     # Core Astrological Calculation Engine
├── ephe/                  # Swiss Ephemeris Data Files
├── templates/             # HTML Templates (horoscope.html, etc.)
├── static/                # CSS, JS, and Images
├── requirements.txt       # Python Dependencies
└── README.md              # Documentation
```

## 📄 License
MIT License.

---
*Built with ❤️ for Vedic Science.*
