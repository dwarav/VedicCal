# Vedic Astrology Calculator - Swiss Ephemeris

A complete, production-ready Python application for calculating Vedic astrology parameters using the Swiss Ephemeris library (`pyswisseph`).

## Features

✅ **Sunrise & Sunset Calculations**
- Accurate solar rise/set times for any location
- Based on Sun's declination and observer's latitude/longitude

✅ **Thithi Calculation** (Lunar Days)
- 30 lunar days per month
- Based on Sun-Moon elongation (angular separation)
- Divided into Shukla Paksha (Waxing) and Krishna Paksha (Waning)

✅ **Nakshatra Calculation** (Lunar Mansions)
- 27 fixed lunar houses in the sidereal zodiac
- Each spans 13°20' (13.333...°)
- Position percentage within nakshatra

✅ **Yoga Calculation** (Planetary Union Periods)
- 27 yogas per lunar month
- Based on sum of Sun and Moon longitudes
- Shubha yoga (auspicious) vs Asubha yoga (inauspicious)

✅ **Karana Calculation** (Half-Thithis)
- 60 karanas per lunar month
- Each karana spans 6°
- 8 rotating + 3 fixed karana types

✅ **Paksha Identification** (Lunar Fortnight)
- Shukla Paksha (Waxing/Bright)
- Krishna Paksha (Waning/Dark)

✅ **Moon Phase Calculation**
- Phase fraction (0-1 range)
- Descriptive phase names (New, Waxing, Full, Waning)

## Installation

### Prerequisites
- Python 3.7+
- pip package manager

### Step 1: Install Dependencies

```bash
pip install pyswisseph
```

### Step 2: Download the Script

```bash
# Save the vedic_astrology.py file to your project directory
curl -O https://your-url/vedic_astrology.py
```

Or create the file manually and copy the contents from this repository.

## Usage

### Basic Usage

```python
from vedic_astrology import VedicAstrologyCalculator
from datetime import datetime

# Initialize calculator with location (latitude, longitude)
calc = VedicAstrologyCalculator(
    latitude=28.6139,    # Delhi latitude
    longitude=77.2090    # Delhi longitude
)

# Calculate all parameters for a specific date/time (UTC)
dt = datetime(2025, 1, 15, 6, 0, 0)  # Jan 15, 2025, 6:00 AM UTC
results = calc.calculate_all(dt)

# Access individual results
print(f"Thithi: {results['thithi']['name']}")
print(f"Nakshatra: {results['nakshatra']['name']}")
print(f"Yoga: {results['yoga']['name']}")
print(f"Moon Phase: {results['moon_phase']['description']}")
```

### Running the Script

```bash
python vedic_astrology.py
```

This will execute 3 example calculations:
1. Frankfurt, Germany - December 28, 2025
2. Delhi, India - January 15, 2025 (Makar Sankranti)
3. New York, USA - January 13, 2025 (Full Moon)

### Advanced Usage: Custom Functions

```python
from vedic_astrology import VedicAstrologyCalculator
from datetime import datetime

calc = VedicAstrologyCalculator(latitude=50.1109, longitude=8.6821)
dt = datetime(2025, 12, 28, 12, 0, 0)

# Convert datetime to Julian Day
jd = calc.datetime_to_julian_day(dt)
print(f"Julian Day: {jd}")

# Get ayanamsa
ayanamsa = calc.get_ayanamsa(jd)
print(f"Ayanamsa: {ayanamsa}°")

# Get sidereal positions
sun_long, moon_long = calc.get_sun_moon_positions(jd)
print(f"Sun: {sun_long:.2f}°, Moon: {moon_long:.2f}°")

# Get sunrise/sunset
sunrise, sunset = calc.get_sunrise_sunset(jd)
print(f"Sunrise: {sunrise}, Sunset: {sunset}")

# Calculate individual elements
thithi_num, elongation, thithi_name = calc.calculate_thithi(sun_long, moon_long)
print(f"Thithi #{thithi_num}: {thithi_name} (elongation: {elongation:.2f}°)")

nakshatra_num, nak_pos, nak_name = calc.calculate_nakshatra(moon_long)
print(f"Nakshatra #{nakshatra_num}: {nak_name} ({nak_pos:.2f}% through)")

yoga_num, yoga_sum, yoga_name = calc.calculate_yoga(sun_long, moon_long)
print(f"Yoga #{yoga_num}: {yoga_name}")

karana_num, karana_name = calc.calculate_karana(elongation)
print(f"Karana #{karana_num}: {karana_name}")

paksha = calc.calculate_paksha(elongation)
print(f"Paksha: {paksha}")

phase_frac, phase_desc = calc.calculate_moon_phase(elongation)
print(f"Moon Phase: {phase_desc} ({phase_frac:.3f})")
```

## Output Example

```
======================================================================
VEDIC ASTROLOGY CALCULATOR - SWISS EPHEMERIS
======================================================================

Date & Time:       2025-12-28 12:00:00 UTC
Location:          Lat: 50.1109°, Lon: 8.6821°
Julian Day:        2461038.000000
Ayanamsa (Lahiri): 25.1034°

----------------------------------------------------------------------
SUNRISE & SUNSET
----------------------------------------------------------------------
Sunrise Time:      05:25:16
Sunset Time:       17:25:16

----------------------------------------------------------------------
CELESTIAL POSITIONS (Sidereal)
----------------------------------------------------------------------
Sun Longitude:     251.90°
Moon Longitude:    350.84°
Sun-Moon Elongation: 98.94°

----------------------------------------------------------------------
VEDIC LUNAR ELEMENTS
----------------------------------------------------------------------
Thithi:            #9 - Navami
  Elongation:      98.94°

Nakshatra:         #27 - Revati
  Position:        31.30% through nakshatra

Yoga:              #19 - Sadhya
  Sun+Moon Sum:    242.74°

Karana:            #17 - Gara

Paksha:            Shukla Paksha (Waxing Moon)

Moon Phase:        Waxing (Growing)
  Phase Fraction:  0.275 (0=New, 0.5=Full, 1=New)

======================================================================
```

## Astronomical Theory

### Ayanamsa (Lahiri)

The ayanamsa is the difference between tropical (Western zodiac) and sidereal (fixed star) longitudes. Vedic astrology uses the sidereal zodiac, which is fixed to actual stars.

- **Lahiri Ayanamsa**: Fixed at 23°11' as of January 1, 1900
- **Precession**: Increases ~50.23" per year
- **Sidereal = Tropical - Ayanamsa**

### Thithi (Lunar Day)

Based on Sun-Moon elongation (angular separation):
- **Range**: 0-360°
- **Divisions**: 30 thithis × 12° each
- **Paksha division**: 0-180° = Shukla (Waxing), 180-360° = Krishna (Waning)
- **Usage**: Determines auspicious days (muhurat) for rituals

### Nakshatra (Lunar Mansion)

Fixed divisions of the sidereal zodiac:
- **Total**: 27 nakshatras
- **Size**: 13°20' (13.333...°) each
- **Padas**: 4 quarters of 3°20' each
- **Fixed**: Referenced to actual stars (not tropical)
- **Usage**: Birth chart analysis, Dasha periods, personality traits

### Yoga (Planetary Union)

Calculated from the sum of Sun and Moon longitudes:
- **Total**: 27 yogas per lunar month
- **Size**: 13°20' (13.333...°) each
- **Auspicious**: Vishkambha, Priti, Ayushman, etc.
- **Inauspicious**: Ganda, Vyaghata, Atiganda, etc.
- **Usage**: Muhurat (auspicious time) calculations

### Karana (Half-Thithi)

Each thithi divided into 2 karanas:
- **Total**: 60 karanas in lunar month
- **Size**: 6° each
- **Types**: 8 rotating (Bava, Balava, Kaulava, etc.) + 3 fixed
- **Usage**: Activity auspiciousness, travel timing

### Paksha (Lunar Fortnight)

Two 15-day periods per lunar month:
- **Shukla Paksha** (0-180° elongation): Waxing, constructive
- **Krishna Paksha** (180-360° elongation): Waning, purification
- **Usage**: Determines festival timing, daily rituals

### Moon Phase

Normalized illumination fraction:
- **0.0**: New Moon (Amavasya)
- **0.25**: First Quarter
- **0.5**: Full Moon (Purnima)
- **0.75**: Last Quarter
- **1.0**: Back to New Moon

## Code Structure

```
VedicAstrologyCalculator
├── __init__(latitude, longitude)
├── datetime_to_julian_day(datetime) → float
├── get_ayanamsa(jd) → float
├── normalize_longitude(longitude) → float
├── get_sun_moon_positions(jd) → (sun_long, moon_long)
├── get_sunrise_sunset(jd) → (sunrise, sunset)
├── calculate_thithi(sun_long, moon_long) → (num, elongation, name)
├── calculate_nakshatra(moon_long) → (num, position%, name)
├── calculate_yoga(sun_long, moon_long) → (num, sum, name)
├── calculate_karana(elongation) → (num, name)
├── calculate_paksha(elongation) → str
├── calculate_moon_phase(elongation) → (fraction, description)
└── calculate_all(datetime) → results_dict

Helper Functions
├── format_output(results) → formatted_string
└── _decimal_to_time(decimal_hours) → "HH:MM:SS"
```

## Integration with FastAPI

If integrating with your FastAPI horoscope application:

```python
from fastapi import FastAPI
from datetime import datetime
from vedic_astrology import VedicAstrologyCalculator, format_output

app = FastAPI()

@app.get("/horoscope/{date}/{lat}/{lon}")
async def get_horoscope(date: str, lat: float, lon: float):
    """
    Get horoscope for given date and location.
    
    Example: /horoscope/2025-01-15/28.6139/77.2090
    """
    try:
        dt = datetime.fromisoformat(f"{date}T12:00:00")
        calc = VedicAstrologyCalculator(lat, lon)
        results = calc.calculate_all(dt)
        
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/horoscope/detailed")
async def get_detailed_horoscope(date: str, time: str, lat: float, lon: str):
    """Get detailed horoscope with custom time."""
    datetime_str = f"{date} {time}"
    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    
    calc = VedicAstrologyCalculator(lat, lon)
    results = calc.calculate_all(dt)
    
    return {
        "datetime": results['datetime'],
        "location": results['location'],
        "elements": {
            "thithi": results['thithi'],
            "nakshatra": results['nakshatra'],
            "yoga": results['yoga'],
            "karana": results['karana'],
            "paksha": results['paksha'],
            "moon_phase": results['moon_phase']
        },
        "celestial": {
            "sun_longitude": results['sun_longitude'],
            "moon_longitude": results['moon_longitude'],
            "elongation": results['sun_moon_elongation'],
            "sunrise": results['sunrise'],
            "sunset": results['sunset']
        }
    }
```

## Testing

Run the built-in examples:

```bash
python vedic_astrology.py
```

Expected output includes calculations for 3 different locations with detailed breakdowns of all Vedic elements.

## Limitations

1. **Sunrise/Sunset**: Uses approximate mathematical method. For production, consider integrating with:
   - [timeanddate.com API](https://www.timeanddate.com/services/api/)
   - [sunrise-sunset.org API](https://sunrise-sunset.org/api)
   - [weather.gov API](https://api.weather.gov/)

2. **Polar Regions**: Sun may not rise/set in polar regions (long day/night seasons)

3. **Time Zone**: All input/output times are UTC. Convert as needed for local time.

4. **Accuracy**: Lahiri ayanamsa is standard but other systems exist:
   - Fagan/Bradley ayanamsa
   - Yukteshwar ayanamsa
   - Raman ayanamsa

## References

- **Swiss Ephemeris**: https://www.astro.com/swisseph/
- **Vedic Astrology**: https://en.wikipedia.org/wiki/Vedic_astrology
- **Nakshatras**: https://en.wikipedia.org/wiki/Nakshatra
- **Thithi**: https://en.wikipedia.org/wiki/Tithi

## License

MIT License - Feel free to use in your projects!

## Author

Vedic Astrology Calculator
- Python 3.7+
- Swiss Ephemeris Library
- Lahiri Ayanamsa calculations

## Support

For issues or questions:
1. Check the function docstrings for detailed parameter explanations
2. Review the example usage section
3. Verify your Swiss Ephemeris library installation

## Future Enhancements

- [ ] Support for multiple ayanamsa systems
- [ ] Tropical zodiac calculations
- [ ] Planetary positions (Mars, Mercury, etc.)
- [ ] House system calculations (Bhava)
- [ ] Dasha period calculations
- [ ] Compatibility analysis (Guna matching)
- [ ] REST API wrapper
- [ ] Web UI integration
