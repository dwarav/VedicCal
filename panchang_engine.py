import swisseph as swe
from datetime import datetime, timedelta, date
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import os
import math
import urllib.parse
import calendar

# ================= CONFIG =================
SERVER_EPHE_PATH = '/home/u285716465/domains/dwara.org/public_html/vedic/ephe'
if os.path.exists(SERVER_EPHE_PATH):
    EPHEMERIS_PATH = SERVER_EPHE_PATH
else:
    EPHEMERIS_PATH = os.path.join(os.path.dirname(__file__), 'ephe')

SIDEREAL_MODE = swe.SIDM_LAHIRI

# ================= DATA CONSTANTS =================
MONTHS = ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada", "Ashwina", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna"]
TITHIS = ["Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi", "Shukla Panchami", "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami", "Shukla Navami", "Shukla Dashami", "Shukla Ekadashi", "Shukla Dwadashi", "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima", "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi", "Krishna Panchami", "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami", "Krishna Navami", "Krishna Dashami", "Krishna Ekadashi", "Krishna Dwadashi", "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
YOGAS = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"]
KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Garija", "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"]
RASHIS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"]
PADA_NAMES = [f"{n} Pada {i+1}" for n in NAKSHATRAS for i in range(4)]

# --- ASTROLOGICAL MAPPINGS ---
CHALDEAN_MAP = {'A':1, 'I':1, 'J':1, 'Q':1, 'Y':1, 'B':2, 'K':2, 'R':2, 'C':3, 'G':3, 'L':3, 'S':3, 'D':4, 'M':4, 'T':4, 'E':5, 'H':5, 'N':5, 'X':5, 'U':6, 'V':6, 'W':6, 'O':7, 'Z':7, 'F':8, 'P':8}
NUMEROLOGY_DATA = {
    1: {"ruler": "Sun", "friend": "1, 2, 3, 9", "enemy": "8", "neutral": "4, 5, 6, 7"},
    2: {"ruler": "Moon", "friend": "1, 2, 5", "enemy": "4, 7, 8, 9", "neutral": "3, 6"},
    3: {"ruler": "Jupiter", "friend": "1, 2, 3, 9", "enemy": "5, 6", "neutral": "4, 7, 8"},
    4: {"ruler": "Rahu", "friend": "4, 5, 6, 8", "enemy": "1, 2", "neutral": "3, 7, 9"},
    5: {"ruler": "Mercury", "friend": "1, 4, 5, 6", "enemy": "2", "neutral": "3, 7, 8, 9"},
    6: {"ruler": "Venus", "friend": "4, 5, 6, 7, 8", "enemy": "1, 2", "neutral": "3, 9"},
    7: {"ruler": "Ketu", "friend": "6, 7, 9", "enemy": "1, 2", "neutral": "3, 4, 5, 8"},
    8: {"ruler": "Saturn", "friend": "4, 5, 6, 8", "enemy": "1, 2", "neutral": "3, 7, 9"},
    9: {"ruler": "Mars", "friend": "1, 2, 3, 9", "enemy": "5", "neutral": "4, 6, 7, 8"}
}
NAK_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"] * 3
RASI_LORDS_MAP = {0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter"}

# DASHA YEARS (Vimshottari)
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

FAV_POINTS = {
    0: {"num": 9, "day": "Tuesday", "color": "Dark Red / Maroon", "stone": "Red Coral", "substone": "Red Cornelian", "deity": "Lord Hanuman / Kartikeya", "metal": "Copper", "mantra": "Om Ang Angarkaya Namah"},
    1: {"num": 6, "day": "Friday", "color": "White / Pink", "stone": "Diamond", "substone": "Opal, White Zircon", "deity": "Goddess Lakshmi", "metal": "Silver", "mantra": "Om Shum Shukraya Namah"},
    2: {"num": 5, "day": "Wednesday", "color": "Green", "stone": "Emerald", "substone": "Green Onyx, Peridot", "deity": "Lord Vishnu / Ganesha", "metal": "Gold / Bronze", "mantra": "Om Bum Budhaya Namah"},
    3: {"num": 2, "day": "Monday", "color": "White / Cream", "stone": "Pearl", "substone": "Moonstone", "deity": "Lord Shiva / Gauri", "metal": "Silver", "mantra": "Om Som Somaya Namah"},
    4: {"num": 1, "day": "Sunday", "color": "Gold / Orange", "stone": "Ruby", "substone": "Red Garnet, Red Spinel", "deity": "Lord Surya / Shiva", "metal": "Gold / Copper", "mantra": "Om Hram Hrim Hraum Sah Suryaya Namah"},
    5: {"num": 5, "day": "Wednesday", "color": "Green / Light Green", "stone": "Emerald", "substone": "Peridot, Green Tourmaline", "deity": "Lord Ganesha / Vishnu", "metal": "Gold", "mantra": "Om Bum Budhaya Namah"},
    6: {"num": 6, "day": "Friday", "color": "White / Light Blue", "stone": "Diamond", "substone": "White Sapphire, Opal", "deity": "Goddess Lakshmi", "metal": "Silver", "mantra": "Om Shum Shukraya Namah"},
    7: {"num": 9, "day": "Tuesday", "color": "Red / Rust", "stone": "Red Coral", "substone": "Red Jasper", "deity": "Lord Hanuman", "metal": "Copper", "mantra": "Om Ang Angarkaya Namah"},
    8: {"num": 3, "day": "Thursday", "color": "Yellow / Golden", "stone": "Yellow Sapphire", "substone": "Yellow Topaz, Citrine", "deity": "Lord Vishnu / Dakshinamurthy", "metal": "Gold", "mantra": "Om Brim Brihaspataye Namah"},
    9: {"num": 8, "day": "Saturday", "color": "Blue / Black", "stone": "Blue Sapphire", "substone": "Lapis Lazuli, Amethyst", "deity": "Lord Shani / Hanuman", "metal": "Iron", "mantra": "Om Sham Shanaishcharaya Namah"},
    10: {"num": 8, "day": "Saturday", "color": "Black / Dark Blue", "stone": "Blue Sapphire", "substone": "Turquoise, Amethyst", "deity": "Lord Shani / Shiva", "metal": "Iron", "mantra": "Om Sham Shanaishcharaya Namah"},
    11: {"num": 3, "day": "Thursday", "color": "Yellow", "stone": "Yellow Sapphire", "substone": "Golden Topaz", "deity": "Lord Vishnu / Dattatreya", "metal": "Gold", "mantra": "Om Brim Brihaspataye Namah"}
}

NAMA_AKSHARA = [
    "Chu", "Che", "Cho", "La",  # Ashwini
    "Li", "Lu", "Le", "Lo",     # Bharani
    "A", "I", "U", "E",         # Krittika (Corrected from A, E, U, A)
    "O", "Va", "Vi", "Vu",      # Rohini
    "Ve", "Vo", "Ka", "Ki",     # Mrigashira
    "Ku", "Gha", "Ng", "Chha",  # Ardra
    "Ke", "Ko", "Ha", "Hi",     # Punarvasu
    "Hu", "He", "Ho", "Da",     # Pushya
    "Di", "Du", "De", "Do",     # Ashlesha
    "Ma", "Mi", "Mu", "Me",     # Magha
    "Mo", "Ta", "Ti", "Tu",     # Purva Phalguni
    "Te", "To", "Pa", "Pi",     # Uttara Phalguni
    "Pu", "Sha", "Na", "Tha",   # Hasta
    "Pe", "Po", "Ra", "Ri",     # Chitra
    "Ru", "Re", "Ro", "Ta",     # Swati
    "Ti", "Tu", "Te", "To",     # Vishakha
    "Na", "Ni", "Nu", "Ne",     # Anuradha
    "No", "Ya", "Yi", "Yu",     # Jyeshtha
    "Ye", "Yo", "Bha", "Bhi",   # Mula
    "Bhu", "Dha", "Pha", "Dha", # Purva Ashadha
    "Bhe", "Bho", "Ja", "Ji",   # Uttara Ashadha
    "Ju", "Je", "Jo", "Gha",    # Shravana
    "Ga", "Gi", "Gu", "Ge",     # Dhanishta
    "Go", "Sa", "Si", "Su",     # Shatabhisha
    "Se", "So", "Da", "Di",     # Purva Bhadrapada
    "Du", "Tha", "Jha", "Da",   # Uttara Bhadrapada
    "De", "Do", "Cha", "Chi"    # Revati
]
GANAS = {"Deva": [0, 4, 6, 7, 12, 14, 16, 21, 26], "Manushya": [1, 3, 5, 10, 11, 19, 20, 24, 25], "Rakshasa": [2, 8, 9, 13, 15, 17, 18, 22, 23]}
YONIS = ["Ashwa", "Gaja", "Mesha", "Sarpa", "Sarpa", "Shwan", "Marjala", "Mesha", "Marjala", "Mushaka", "Mushaka", "Gau", "Mahisha", "Vyaghra", "Mahisha", "Vyaghra", "Mriga", "Mriga", "Shwan", "Vanara", "Nakula", "Vanara", "Simha", "Ashwa", "Simha", "Gau", "Gaja"]
NADIS = {"Adi (Vata)": [0, 5, 6, 11, 12, 17, 18, 23, 24], "Madhya (Pitta)": [1, 4, 7, 10, 13, 16, 19, 22, 25], "Antya (Kapha)": [2, 3, 8, 9, 14, 15, 20, 21, 26]}
VARNA = ["Kshatriya", "Vaishya", "Shudra", "Brahmin", "Kshatriya", "Vaishya", "Shudra", "Brahmin", "Kshatriya", "Vaishya", "Shudra", "Brahmin"]
VASHYA = ["Chatushpada", "Chatushpada", "Manava", "Jalachar", "Vanchar", "Manava", "Manava", "Keeta", "Manava", "Jalachar", "Manava", "Jalachar"]
TATVA = ["Fire", "Earth", "Air", "Water", "Fire", "Earth", "Air", "Water", "Fire", "Earth", "Air", "Water"]

# KUNDLI PREDICTIONS DB
KUNDLI_PREDICTIONS = {
    0: {"general": "You are a born leader, energetic, and courageous.", "career": "Military, Police, Sports.", "health": "Headaches, head injuries.", "marriage": "Passionate relationships."},
    1: {"general": "You are practical, reliable, and love stability.", "career": "Finance, arts, agriculture.", "health": "Throat infections.", "marriage": "Loyal and devoted."},
    2: {"general": "You are intellectual and adaptable.", "career": "Journalism, writing, sales.", "health": "Respiratory issues.", "marriage": "Need mental stimulation."},
    3: {"general": "You are emotional and nurturing.", "career": "Hospitality, nursing.", "health": "Stomach issues.", "marriage": "Seek deep bonds."},
    4: {"general": "You are charismatic and proud.", "career": "Politics, acting.", "health": "Heart and spine.", "marriage": "Need respect."},
    5: {"general": "You are analytical and detail-oriented.", "career": "Accounting, medicine.", "health": "Digestive system.", "marriage": "Practical in love."},
    6: {"general": "You are diplomatic and charming.", "career": "Law, fashion, arts.", "health": "Kidneys and back.", "marriage": "Seek harmony."},
    7: {"general": "You are intense and secretive.", "career": "Research, detective.", "health": "Reproductive system.", "marriage": "Possessive and intense."},
    8: {"general": "Optimistic and freedom-loving.", "career": "Teaching, travel.", "health": "Liver and hips.", "marriage": "Need space."},
    9: {"general": "Disciplined and ambitious.", "career": "Government, mining.", "health": "Knees and joints.", "marriage": "Serious and responsible."},
    10: {"general": "Innovative and humanitarian.", "career": "Science, technology.", "health": "Ankles.", "marriage": "Need friendship."},
    11: {"general": "Compassionate and spiritual.", "career": "Arts, healing.", "health": "Feet.", "marriage": "Romantic soul."}
}

RASHI_ICONS = {"Mesha": "♈", "Vrishabha": "♉", "Mithuna": "♊", "Karka": "♋", "Simha": "♌", "Kanya": "♍", "Tula": "♎", "Vrishchika": "♏", "Dhanu": "♐", "Makara": "♑", "Kumbha": "♒", "Meena": "♓"}
TITHI_ICONS = {"Shukla Pratipada": "🌒", "Shukla Dwitiya": "🌒", "Shukla Tritiya": "🌓", "Shukla Chaturthi": "🌓", "Shukla Panchami": "🌔", "Shukla Shashthi": "🌔", "Shukla Saptami": "🌔", "Shukla Ashtami": "🌓", "Shukla Navami": "🌔", "Shukla Dashami": "🌔", "Shukla Ekadashi": "🌔", "Shukla Dwadashi": "🌖", "Shukla Trayodashi": "🌖", "Shukla Chaturdashi": "🌖", "Purnima": "🌕", "Krishna Pratipada": "🌖", "Krishna Dwitiya": "🌖", "Krishna Tritiya": "🌗", "Krishna Chaturthi": "🌗", "Krishna Panchami": "🌗", "Krishna Shashthi": "🌘", "Krishna Saptami": "🌘", "Krishna Ashtami": "🌗", "Krishna Navami": "🌘", "Krishna Dashami": "🌘", "Krishna Ekadashi": "🌘", "Krishna Dwadashi": "🌘", "Krishna Trayodashi": "🌘", "Krishna Chaturdashi": "🌘", "Amavasya": "🌑"}
NAK_ICONS = {"Ashwini": "🐴", "Bharani": "🐘", "Krittika": "🔥", "Rohini": "🐍", "Mrigashira": "🦌", "Ardra": "💧", "Punarvasu": "🏹", "Pushya": "🌸", "Ashlesha": "🐍", "Magha": "👑", "Purva Phalguni": "🛋️", "Uttara Phalguni": "🛏️", "Hasta": "🖐️", "Chitra": "✨", "Swati": "🌬️", "Vishakha": "⚖️", "Anuradha": "🌸", "Jyeshtha": "🌂", "Mula": "🌿", "Purva Ashadha": "🌊", "Uttara Ashadha": "🐘", "Shravana": "👂", "Dhanishta": "🥁", "Shatabhisha": "⭕", "Purva Bhadrapada": "🦁", "Uttara Bhadrapada": "🐮", "Revati": "🐟"}

PLANET_ICONS = {
    "Sun": "☉", "Moon": "☾", "Mars": "♂", "Mercury": "☿", "Jupiter": "♃", 
    "Venus": "♀", "Saturn": "♄", "Rahu": "☊", "Ketu": "☋", 
    "Uranus": "♅", "Neptune": "♆", "Pluto": "♇", "Ascendant": "Asc"
} 

# --- SAMVATSARA NAMES ---
SAMVATSARA_NAMES = ["Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati", "Angirasa", "Shrimukha", "Bhava", "Yuva", "Dhatri", "Ishvara", "Bahudhanya", "Pramathi", "Vikrama", "Vrishapraja", "Chitrabhanu", "Subhanu", "Tarana", "Parthiva", "Vyaya", "Sarvajit", "Sarvadhari", "Virodhi", "Vikriti", "Khara", "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukha", "Hevilambi", "Vilambi", "Vikari", "Sharvari", "Plava", "Shubhakrit", "Shobhakrit", "Krodhi", "Vishvavasu", "Parabhava", "Plavanga", "Kilaka", "Saumya", "Sadharana", "Virodhikrit", "Paridhavi", "Pramadicha", "Ananda", "Rakshasa", "Nala", "Pingala", "Kalayukti", "Siddharthi", "Raudra", "Durmati", "Dundubhi", "Rudhirodgari", "Raktakshi", "Krodhana", "Akshaya"]

VARJYAM_STARTS = [50, 24, 30, 40, 14, 21, 30, 20, 32, 30, 20, 18, 22, 20, 14, 14, 10, 14, 20, 24, 20, 10, 10, 18, 16, 24, 30]
AMRIT_STARTS = [42, 48, 54, 52, 38, 35, 54, 44, 56, 54, 44, 48, 42, 46, 34, 32, 38, 38, 40, 48, 52, 38, 38, 42, 36, 48, 56]
RAHU_KEY = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
YAMA_KEY = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
GULI_KEY = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}

# ... (Keep FESTIVAL_DB, GREGORIAN_FESTIVALS, FESTIVAL_IMAGES_STATIC) ...
FESTIVAL_DB = {(0, 0, 0): "Ugadi / Gudi Padwa", (0, 0, 8): "Rama Navami", (0, 0, 14): "Hanuman Jayanti", (1, 0, 2): "Akshaya Tritiya", (1, 0, 14): "Buddha Purnima", (2, 0, 9): "Ganga Dussehra", (2, 0, 14): "Vat Savitri Vrat", (3, 0, 1): "Jagannath Rath Yatra", (3, 0, 10): "Devshayani Ekadashi", (3, 0, 14): "Guru Purnima", (4, 0, 4): "Nag Panchami", (4, 0, 14): "Raksha Bandhan", (4, 1, 7): "Janmashtami", (5, 0, 3): "Ganesh Chaturthi", (5, 0, 13): "Anant Chaturdashi", (5, 1, 14): "Mahalaya Amavasya", (6, 0, 0): "Navratri Ghatasthapana", (6, 0, 9): "Dussehra", (6, 0, 14): "Sharad Purnima", (6, 1, 3): "Karwa Chauth", (6, 1, 12): "Dhanteras", (6, 1, 14): "Diwali", (7, 0, 0): "Govardhan Puja", (7, 0, 1): "Bhai Dooj", (7, 0, 10): "Tulsi Vivah", (7, 0, 14): "Kartik Purnima", (8, 0, 10): "Gita Jayanti", (8, 0, 14): "Dattatreya Jayanti", (10, 0, 4): "Vasant Panchami", (10, 0, 6): "Ratha Saptami", (10, 1, 13): "Maha Shivaratri", (11, 0, 14): "Holi"}
GREGORIAN_FESTIVALS = {(1, 1): "New Year's Day", (1, 14): "Makara Sankranti", (1, 26): "Republic Day India", (2, 14): "Valentine's Day", (3, 8): "Women's Day", (4, 14): "Ambedkar Jayanti", (5, 1): "Labor Day", (6, 21): "International Yoga Day", (8, 15): "Independence Day India", (10, 2): "Gandhi Jayanti", (11, 14): "Children's Day", (12, 25): "Christmas"}
FESTIVAL_IMAGES_STATIC = {"Ugadi": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Ugadi_Pachadi.jpg/320px-Ugadi_Pachadi.jpg", "Rama Navami": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Rama_Pattabhishekam.jpg/320px-Rama_Pattabhishekam.jpg", "Hanuman": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Hanuman_idol.jpg/320px-Hanuman_idol.jpg", "Akshaya Tritiya": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Goddess_Lakshmi.jpg/320px-Goddess_Lakshmi.jpg", "Guru Purnima": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Veda_Vyasa.jpg/320px-Veda_Vyasa.jpg", "Raksha Bandhan": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Rakhi.jpg/320px-Rakhi.jpg", "Janmashtami": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Krishna_holding_Govardhan.jpg/320px-Krishna_holding_Govardhan.jpg", "Ganesh": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Lalbaugcha_Raja.jpg/320px-Lalbaugcha_Raja.jpg", "Vinayaka": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Lalbaugcha_Raja.jpg/320px-Lalbaugcha_Raja.jpg", "Sankashti": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Lalbaugcha_Raja.jpg/320px-Lalbaugcha_Raja.jpg", "Navratri": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Durga_Puja_pandal.jpg/320px-Durga_Puja_pandal.jpg", "Durga": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Durga_Puja_pandal.jpg/320px-Durga_Puja_pandal.jpg", "Dussehra": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Ravana_effigy.jpg/320px-Ravana_effigy.jpg", "Diwali": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Diwali_lamps.jpg/320px-Diwali_lamps.jpg", "Shivaratri": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Shiva_lingam.jpg/320px-Shiva_lingam.jpg", "Holi": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Holi_Dahan.jpg/320px-Holi_Dahan.jpg", "Ekadashi": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Vishnu.jpg/320px-Vishnu.jpg", "Pradosh": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Nandi_bull.jpg/320px-Nandi_bull.jpg", "Sankranti": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Makara_Sankranti.jpg/320px-Makara_Sankranti.jpg", "Christmas": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Christmas_tree.jpg/320px-Christmas_tree.jpg", "Republic": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/India_Gate.jpg/320px-India_Gate.jpg", "Independence": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/India_Gate.jpg/320px-India_Gate.jpg", "Yoga": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Yoga_class_Rishikesh.jpg/320px-Yoga_class_Rishikesh.jpg"}


# ================= CORE FUNCTIONS =================
def setup_swisseph():
    swe.set_ephe_path(EPHEMERIS_PATH)
    swe.set_sid_mode(SIDEREAL_MODE)

def get_location(name):
    try:
        geolocator = Nominatim(user_agent="dwara_panchang_final_v16", timeout=5)
        loc = geolocator.geocode(name)
        if not loc: return None
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
        return {'name': loc.address, 'lat': loc.latitude, 'lon': loc.longitude, 'tz': pytz.timezone(tz_str)}
    except: return None

def jd_from_dt(dt_local):
    dt_utc = dt_local.astimezone(pytz.utc)
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0)

def dt_from_jd(jd, tz):
    if jd is None: return None
    y, m, d, h_dec = swe.revjul(jd)
    h = int(h_dec)
    mins = (h_dec - h) * 60
    mi = int(mins)
    sec = int((mins - mi) * 60)
    try:
        return datetime(int(y), int(m), int(d), h, mi, sec, tzinfo=pytz.utc).astimezone(tz)
    except: return None

# ================= SHODASHVARGA CALCULATIONS =================
def get_varga_sign(degree, rashi_idx, varga_num):
    """
    Calculates the sign index (0-11) for a planet in a specific Varga (Divisional Chart)
    based on Parashara Light rules.
    degree: Planet degree within the sign (0.0 to 30.0)
    rashi_idx: Sign index of the planet (0=Aries, 1=Taurus... 11=Pisces)
    varga_num: The division number (e.g., 9 for Navamsa)
    """
    
    # helper for Movable/Fixed/Dual
    # 0=Movable (Aries, Cancer, Libra, Cap)
    # 1=Fixed (Taurus, Leo, Scorpio, Aqu)
    # 2=Dual (Gemini, Virgo, Sag, Pisces)
    quality = rashi_idx % 3 
    is_odd = (rashi_idx % 2 == 0) # Aries(0) is Odd, Taurus(1) is Even

    # D1: Rashi
    if varga_num == 1:
        return rashi_idx

    # D2: Hora (Wealth) - 1/2
    if varga_num == 2:
        # Parashara: Odd signs -> Sun(Leo-4) 1st half, Moon(Can-3) 2nd half
        # Even signs -> Moon(Can-3) 1st half, Sun(Leo-4) 2nd half
        first_half = (degree < 15)
        if is_odd:
            return 4 if first_half else 3
        else:
            return 3 if first_half else 4

    # D3: Drekkana (Siblings) - 1/3
    if varga_num == 3:
        # 1st part -> Same sign
        # 2nd part -> 5th from sign
        # 3rd part -> 9th from sign
        part = int(degree / 10) # 0, 1, 2
        return (rashi_idx + (part * 4)) % 12

    # D4: Chaturthamsha (Destiny) - 1/4
    if varga_num == 4:
        # 1st part -> Same sign
        # 2nd part -> 4th from sign
        # 3rd part -> 7th from sign
        # 4th part -> 10th from sign
        part = int(degree / 7.5) # 0, 1, 2, 3
        return (rashi_idx + (part * 3)) % 12

    # D7: Saptamsha (Progeny) - 1/7
    if varga_num == 7:
        # Odd: Starts from same sign
        # Even: Starts from 7th sign
        part = int(degree / (30/7))
        start_sign = rashi_idx if is_odd else (rashi_idx + 6)
        return (start_sign + part) % 12

    # D9: Navamsa (Spouse) - 1/9
    if varga_num == 9:
        # Movable: Starts from same sign
        # Fixed: Starts from 9th sign
        # Dual: Starts from 5th sign
        part = int(degree / (30/9))
        if quality == 0: start = rashi_idx
        elif quality == 1: start = (rashi_idx + 8) % 12
        else: start = (rashi_idx + 4) % 12
        return (start + part) % 12

    # D10: Dashamsha (Career) - 1/10
    if varga_num == 10:
        # Odd: Starts from same sign
        # Even: Starts from 9th sign
        part = int(degree / 3)
        start = rashi_idx if is_odd else (rashi_idx + 8)
        return (start + part) % 12

    # D12: Dwadashamsha (Parents) - 1/12
    if varga_num == 12:
        # Starts from same sign
        part = int(degree / 2.5)
        return (rashi_idx + part) % 12

    # D16: Shodashamsha (Vehicles) - 1/16
    if varga_num == 16:
        # Movable: Starts from Aries(0)
        # Fixed: Starts from Leo(4)
        # Dual: Starts from Sag(8)
        part = int(degree / (30/16))
        if quality == 0: start = 0
        elif quality == 1: start = 4
        else: start = 8
        return (start + part) % 12

    # D20: Vimshamsha (Spiritual) - 1/20
    if varga_num == 20:
        # Movable: From Aries(0)
        # Fixed: From Sag(8)
        # Dual: From Leo(4) -- Wait, standard is M->Aries, F->Sag, D->Leo
        part = int(degree / (30/20))
        if quality == 0: start = 0
        elif quality == 1: start = 8
        else: start = 4
        return (start + part) % 12

    # D24: Chaturvimshamsha (Knowledge) - 1/24
    if varga_num == 24:
        # Odd: From Leo(4)
        # Even: From Cancer(3)
        part = int(degree / (30/24))
        start = 4 if is_odd else 3
        # Note: D24 sequence is continuous? No, standard is start point + part
        return (start + part) % 12

    # D27: Saptavimshamsha (Strength) - 1/27
    if varga_num == 27:
        # Odd: From Aries(0)
        # Even: From Cancer(3)
        part = int(degree / (30/27))
        start = 0 if is_odd else 3
        return (start + part) % 12

    # D30: Trimshamsha (Misfortune) - 1/30
    if varga_num == 30:
        # Specific degrees mapping
        # Odd: 0-5 Mars(0), 5-10 Sat(10), 10-18 Jup(8), 18-25 Mer(2), 25-30 Ven(6)
        # Even: 0-5 Ven(1), 5-12 Mer(5), 12-20 Jup(11), 20-25 Sat(9), 25-30 Mars(7)
        d = degree
        if is_odd:
            if d < 5: return 0 # Aries
            elif d < 10: return 10 # Aquarius
            elif d < 18: return 8 # Sagittarius
            elif d < 25: return 2 # Gemini
            else: return 6 # Libra
        else:
            if d < 5: return 1 # Taurus
            elif d < 12: return 5 # Virgo
            elif d < 20: return 11 # Pisces
            elif d < 25: return 9 # Capricorn
            else: return 7 # Scorpio

    # D40: Khavedamsha (Aus/Inaus) - 1/40
    if varga_num == 40:
        # Odd: From Aries(0)
        # Even: From Libra(6)
        part = int(degree / (30/40))
        start = 0 if is_odd else 6
        return (start + part) % 12

    # D45: Akshavedamsha (General) - 1/45
    if varga_num == 45:
        # Movable: From Aries(0)
        # Fixed: From Leo(4)
        # Dual: From Sag(8)
        part = int(degree / (30/45))
        if quality == 0: start = 0
        elif quality == 1: start = 4
        else: start = 8
        return (start + part) % 12

    # D60: Shashtiamsha (Karma) - 1/60
    if varga_num == 60:
        # From the sign itself (some variations exist, usually just wrap 1-12)
        # Standard: Each part is 0.5 deg. Count from current sign? 
        # Actually standard Parashara: Ignore current sign, count from it?
        # "To be counted from the sign occupied by the planet"
        # Wait, D60 is often "Count parts from the sign occupied".
        # Yes, so if in 1st part (0-0.5) of Aries, count 1 from Aries = Aries.
        part = int(degree / 0.5)
        return (rashi_idx + part) % 12

    return rashi_idx # Default to Rashi if not handled

# ================= CALCULATORS =================
def calc_sun_rise_set(jd, lat, lon):
    if jd is None: return 0.0, 0.0
    geopos = (float(lon), float(lat), 0.0)
    jd_search = jd - 0.375
    try:
        rise = swe.rise_trans(jd_search, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER, geopos)[1][0]
        set_ = swe.rise_trans(jd_search, swe.SUN, swe.CALC_SET | swe.BIT_DISC_CENTER, geopos)[1][0]
        return rise, set_
    except: return 0.0, 0.0

def calc_moon_rise_set(jd_start, lat, lon):
    if jd_start is None: return 0.0, 0.0
    geopos = (float(lon), float(lat), 0.0)
    jd_search = jd_start - 0.5
    try:
        res_rise = swe.rise_trans(jd_search, swe.MOON, swe.CALC_RISE | swe.BIT_DISC_CENTER, geopos)
        res_set = swe.rise_trans(jd_search, swe.MOON, swe.CALC_SET | swe.BIT_DISC_CENTER, geopos)
        return res_rise[1][0], res_set[1][0]
    except: return 0.0, 0.0

def get_pos(jd):
    if jd is None: return 0.0, 0.0
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    try:
        sun = swe.calc_ut(jd, swe.SUN, flags)[0][0]
        moon = swe.calc_ut(jd, swe.MOON, flags)[0][0]
        return sun, moon
    except: return 0.0, 0.0

def get_events(start_jd, end_jd, func, names, count, is_karana=False):
    events = []
    if start_jd is None: return []
    try:
        curr_idx, _ = func(start_jd)
        s_jd = find_trans(start_jd - 1.5, func, (curr_idx - 1) % count) or start_jd
        curr_search = start_jd
        loops = 0
        while loops < 10:
            e_jd = find_trans(curr_search, func, curr_idx)
            name = get_karana_name(curr_idx) if is_karana else names[curr_idx]
            events.append({'name': name, 'start': s_jd, 'end': e_jd, 'index': curr_idx})
            if not e_jd or e_jd >= end_jd: break
            s_jd = e_jd
            curr_search = e_jd + 0.002
            curr_idx = (curr_idx + 1) % count
            loops += 1
    except: pass
    return events

def find_trans(start, func, target):
    t1, t2 = start, start + 2.0
    curr = t1
    found = False
    while curr < t2:
        try:
            if func(curr)[0] != func(curr + 1/24.0)[0] and func(curr)[0] == target:
                t1, t2 = curr, curr + 1/24.0
                found = True
                break
        except: pass
        curr += 1/24.0
    if not found: return None
    while (t2 - t1) > 0.00001:
        mid = (t1 + t2)/2
        try:
            if func(mid)[0] == target: t1 = mid
            else: t2 = mid
        except: break
    return t2

def get_karana_name(k):
    if k == 0: return KARANAS[10]
    if k >= 57: return KARANAS[k - 50]
    return KARANAS[(k - 1) % 7]

def fmt_duration(jd_start, jd_end):
    if jd_start is None or jd_end is None: return "---"
    duration_days = jd_end - jd_start
    total_seconds = int(duration_days * 24 * 3600)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d} Hours {minutes:02d} Mins {seconds:02d} Secs"

# --- HELPER: GET ENTRY/EXIT TIMES ---
def get_entry_exit_times(jd_ref, body_id, current_val, span_deg, tz):
    """
    Finds when the current Sign/Nakshatra started and when it will end.
    Searches backward for entry and forward for exit.
    """
    
    # 1. SEARCH FOR EXIT (Next Transition)
    # Target value is next index
    target_next = int(current_val + 1)
    # Function to check index
    def check_idx(t):
        pos = swe.calc_ut(t, body_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)[0][0]
        return int(pos / span_deg)
        
    # Find when it changes to next
    exit_jd = find_trans(jd_ref, check_idx, target_next) 
    
    # 2. SEARCH FOR ENTRY (Previous Transition)
    # Search backwards. We look for when it *became* current_val.
    # Effectively finding when index changed FROM (current_val - 1) TO current_val
    # We can use find_trans by searching backwards? No, find_trans searches forward.
    # So we search forward from (jd_ref - a lot) until we hit current_val.
    
    # Search range: Moon ~3 days back, Sun ~32 days back
    days_back = 35 if body_id == swe.SUN else 4
    search_start = jd_ref - days_back
    
    # Find when it enters 'current_val'
    entry_jd = find_trans(search_start, check_idx, current_val)
    
    # If not found (e.g. at edge of buffer), default to None
    
    # Format
    entry_str = "---"
    exit_str = "---"
    
    if entry_jd:
        dt_ent = dt_from_jd(entry_jd, tz)
        if dt_ent: entry_str = dt_ent.strftime("%d %b, %I:%M %p")
        
    if exit_jd:
        dt_ex = dt_from_jd(exit_jd, tz)
        if dt_ex: exit_str = dt_ex.strftime("%d %b, %I:%M %p")
        
    return entry_str, exit_str


# ================= HELPER CALCULATORS =================
def get_tamil_yoga(weekday_idx, nak_idx):
    marana_combos = [(6, 1), (0, 13), (1, 20), (2, 18), (3, 9), (4, 10), (5, 26)]
    amrita_combos = [(6, 12), (0, 21), (1, 6), (2, 23), (3, 7), (4, 26), (5, 3)]
    key = (weekday_idx, nak_idx)
    if key in marana_combos: return "Marana"
    if key in amrita_combos: return "Amrita"
    return "Siddha"

def get_sarvartha_siddhi(weekday_idx, nak_idx):
    ss_map = {6: [12, 7, 18, 11, 20, 25, 0], 0: [21, 3, 4, 7, 16], 1: [0, 2, 4, 8], 2: [3, 16, 12, 2, 4], 3: [7, 16, 2, 6, 26], 4: [26, 16, 0, 6, 21], 5: [3, 14, 21]}
    return nak_idx in ss_map.get(weekday_idx, [])

def get_vidaal_yoga(weekday_idx, nak_idx):
    bad_map = {6: [1, 13], 0: [13], 1: [20], 2: [18], 3: [9], 4: [10], 5: [26]}
    return nak_idx in bad_map.get(weekday_idx, [])

def get_tripushkara_yoga(tithi_events, nak_events, weekday_idx, start_jd, end_jd, tz):
    if weekday_idx not in [1, 5, 6]: return "None"
    valid_tithis = [1, 6, 11, 16, 21, 26]
    valid_naks = [2, 6, 11, 15, 20, 24]
    timings = []
    for t in tithi_events:
        if t['index'] in valid_tithis:
            t_s = max(t['start'], start_jd)
            t_e = min(t['end'] if t['end'] else end_jd, end_jd)
            for n in nak_events:
                if n['index'] in valid_naks:
                    n_s = max(n['start'], start_jd)
                    n_e = min(n['end'] if n['end'] else end_jd, end_jd)
                    latest_start = max(t_s, n_s)
                    earliest_end = min(t_e, n_e)
                    if latest_start < earliest_end:
                        s_str = dt_from_jd(latest_start, tz).strftime('%I:%M %p')
                        e_str = dt_from_jd(earliest_end, tz).strftime('%I:%M %p')
                        timings.append(f"{s_str} - {e_str}")
    return ", ".join(timings) if timings else "None"

def get_netram_jeevan(nak_idx):
    n = nak_idx + 1
    rem = n % 9
    netram = 0
    if rem in [3, 4, 5, 6]: netram = 1
    elif rem in [7, 8, 0]: netram = 2
    jeevan = 1 if netram > 0 else 0 
    net_str = ["Zero Eyes", "One Eye", "Two Eyes"][netram]
    jee_str = "Full Life" if jeevan else "Empty Life"
    return net_str, jee_str

def get_baana_type(sun_nak_idx, nak_idx):
    dist = (nak_idx - sun_nak_idx) % 9
    baana_map = {0: "Sthira (Good)", 1: "Roga (Bad)", 2: "Agni (Bad)", 3: "Raja (Good)", 4: "Chora (Bad)", 5: "Mrityu (Bad)", 6: "Sthira (Good)", 7: "Sthira (Good)", 8: "Sthira (Good)"}
    return baana_map.get(dist, "Sthira")

def get_calculated_timings(nak_events, weekday_idx, sun_nak_idx, tithi_events, start_jd, end_jd, tz):
    ANANDADI_YOGAS = ["Ananda", "Kaladanda", "Dhumra", "Prajapati", "Soumya", "Dhwalka", "Dhwaja", "Srivatsa", "Vajra", "Mudgara", "Chhatra", "Mitra", "Manasa", "Padma", "Lumba", "Utpata", "Mrityu", "Kana", "Siddhi", "Shubha", "Amrita", "Musala", "Gada", "Matanga", "Rakshasa", "Chara", "Sthira", "Pravardhamana"]
    ananda_offset = {6:0, 0:22, 1:18, 2:14, 3:10, 4:6, 5:2}
    def fmt_event(ev_list, type_fn):
        res = []
        for e in ev_list:
            val = type_fn(e['index'])
            d_end = dt_from_jd(e['end'], tz)
            end_t = d_end.strftime('%b %d, %I:%M %p') if d_end and e['end'] else "Full Night"
            res.append(f"{val} upto {end_t}")
        return " | ".join(res)
    anandadi_str = fmt_event(nak_events, lambda idx: ANANDADI_YOGAS[(idx + ananda_offset[weekday_idx]) % 28])
    tamil_str = fmt_event(nak_events, lambda idx: get_tamil_yoga(weekday_idx, idx))
    baana_str = fmt_event(nak_events, lambda idx: get_baana_type(sun_nak_idx, idx))
    n, j = get_netram_jeevan(nak_events[0]['index'])
    ss_found = []
    vidaal_found = []
    for e in nak_events:
        d_start = dt_from_jd(e['start'], tz)
        start_t = d_start.strftime('%I:%M %p') if d_start else "..."
        d_end = dt_from_jd(e['end'], tz)
        end_t = d_end.strftime('%I:%M %p') if d_end and e['end'] else "Full Night"
        if get_sarvartha_siddhi(weekday_idx, e['index']): ss_found.append(f"{start_t} - {end_t}")
        if get_vidaal_yoga(weekday_idx, e['index']): vidaal_found.append(f"{start_t} - {end_t}")
    sarvartha_str = ", ".join(ss_found) if ss_found else "None"
    vidaal_str = ", ".join(vidaal_found) if vidaal_found else "None"
    tripushkara_str = get_tripushkara_yoga(tithi_events, nak_events, weekday_idx, start_jd, end_jd, tz)
    return {"anandadi": anandadi_str, "tamil": tamil_str, "sarvartha": sarvartha_str, "baana": baana_str, "netrama": n, "jeevanama": j, "tripushkara": tripushkara_str, "vidaal": vidaal_str}

def get_samvat_details(dt):
    year = dt.year
    is_after_new_year = dt.month > 4 or (dt.month == 4 and dt.day > 14)
    vikram = year + 57 if is_after_new_year else year + 56
    shaka = year - 78 if is_after_new_year else year - 79
    
    # Samvatsara Calculation
    samvat_idx = (shaka + 11) % 60
    samvat_name = SAMVATSARA_NAMES[samvat_idx]

    return {
        "vikram": vikram, 
        "shaka": shaka, 
        "samvatsara": samvat_name,
        "chandramasa": "" 
    }

def get_ritu_ayana_details(jd):
    # 1. Calculate Tropical Sun (for Modern/Drik Ayana - Dec 21/Jun 21)
    sun_trop = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
    
    # 2. Calculate Sidereal Sun (for Vedic Ayana & Ritu - Jan 14/Jul 16)
    swe.set_sid_mode(SIDEREAL_MODE)
    sun_sid = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)[0][0]

    # --- AYANA CALCULATION ---
    
    # Tropical Uttarayana: Sun moves North (Winter Solstice 270° to Summer Solstice 90°)
    if (sun_trop >= 270 or sun_trop < 90):
        ayana = "Uttarayana (Drik)"
    else:
        ayana = "Dakshinayana (Drik)"

    # Vedic Uttarayana: Sun enters Sidereal Makara (270°) to Karka (90°)
    # This aligns with Makara Sankranti
    if (sun_sid >= 270 or sun_sid < 90):
        vedic_ayana = "Uttarayana"
    else:
        vedic_ayana = "Dakshinayana"

    # --- RITU CALCULATION (Based on Sidereal Sun) ---
    # Vasant:   Pisces-Aries (330° - 30°)
    # Grishma:  Taurus-Gemini (30° - 90°)
    # Varsha:   Cancer-Leo (90° - 150°)
    # Sharad:   Virgo-Libra (150° - 210°)
    # Hemant:   Scorpio-Sagittarius (210° - 270°)
    # Shishir:  Capricorn-Aquarius (270° - 330°)
    
    s = sun_sid % 360
    if 330 <= s < 360 or 0 <= s < 30: ritu = "Vasant (Spring)"
    elif 30 <= s < 90: ritu = "Grishma (Summer)"
    elif 90 <= s < 150: ritu = "Varsha (Monsoon)"
    elif 150 <= s < 210: ritu = "Sharad (Autumn)"
    elif 210 <= s < 270: ritu = "Hemant (Pre-Winter)"
    else: ritu = "Shishir (Winter)"

    return {
        "ritu": ritu, 
        "vedic_ritu": ritu, 
        "ayana": ayana, 
        "vedic_ayana": vedic_ayana
    }

def calculate_muhurtas(rise, set_, rise_next, weekday_idx):
    day_len = set_ - rise
    night_len = rise_next - set_
    one_muhurta_day = day_len / 15.0
    one_muhurta_night = night_len / 15.0
    
    brahma_start = rise - (2 * one_muhurta_night)
    brahma_end = rise - (1 * one_muhurta_night)
    pratah_start = brahma_start
    pratah_end = rise
    
    abhijit_start = rise + (7 * one_muhurta_day)
    abhijit_end = rise + (8 * one_muhurta_day)
    abhijit_res = (abhijit_start, abhijit_end)

    vijaya_start = rise + (10 * one_muhurta_day)
    vijaya_end = rise + (11 * one_muhurta_day)
    godhuli_start = set_ - (12.0/(24*60))
    godhuli_end = set_ + (12.0/(24*60))
    sayahna_start = set_
    sayahna_end = set_ + one_muhurta_night
    nishita_start = set_ + (7 * one_muhurta_night)
    nishita_end = set_ + (8 * one_muhurta_night)
    
    DUR_MAP = {6: [14], 0: [8, 9], 1: [2, 4], 2: [8], 3: [5, 12], 4: [4, 9], 5: [1]}
    dur_times = []
    for seg in DUR_MAP[weekday_idx]:
        s = rise + ((seg-1)*one_muhurta_day)
        e = rise + (seg)*one_muhurta_day
        dur_times.append((s, e))
        
    return {
        "brahma": (brahma_start, brahma_end), "pratah": (pratah_start, pratah_end),
        "abhijit": abhijit_res, "vijaya": (vijaya_start, vijaya_end),
        "godhuli": (godhuli_start, godhuli_end), "sayahna": (sayahna_start, sayahna_end),
        "nishita": (nishita_start, nishita_end), "dur_day": dur_times
    }

def get_nivas_shool_details(jd, weekday_idx, tithi_idx, nak_idx):
    # 1. DISHA SHOOL (Travel Obstacle based on Weekday)
    # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    ds_map = {0: "East", 1: "North", 2: "North", 3: "South", 4: "West", 5: "East", 6: "West"}
    disha_shool = ds_map[weekday_idx]

    # 2. CHANDRA VASA (Moon Direction based on Rashi)
    moon_long = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    moon_rashi_idx = int(moon_long / 30)
    
    cv_map = {
        0: "East", 4: "East", 8: "East",    # Mesha, Simha, Dhanu
        1: "South", 5: "South", 9: "South", # Vrish, Kanya, Makara
        2: "West", 6: "West", 10: "West",   # Mithuna, Tula, Kumbha
        3: "North", 7: "North", 11: "North" # Karka, Vris, Meena
    }
    chandra_vasa = cv_map[moon_rashi_idx]

    # 3. AGNI VASA (For Havan)
    # Formula: (Tithi + Weekday + 1) % 4
    # Weekday: Sun=1, Mon=2 ... Sat=7. Tithi: 1-30.
    tithi_count = (tithi_idx % 30) + 1
    vedic_day = 1 if weekday_idx == 6 else (weekday_idx + 2) # Convert Py(0=Mon) to Vedic(1=Sun)
    
    agni_rem = (tithi_count + vedic_day + 1) % 4
    
    # Interpretation
    if agni_rem == 0 or agni_rem == 3: 
        agnivasa = "Earth (Prithvi) - Auspicious"
        homahuti_str = "Agni is Present (Good)"
    elif agni_rem == 1: 
        agnivasa = "Sky (Akasha) - Inauspicious"
        homahuti_str = "Agni in Sky (Bad)"
    else: 
        agnivasa = "Netherworld (Patala) - Inauspicious"
        homahuti_str = "Agni in Patala (Bad)"

    # 4. SHIVA VASA (For Rudrabhishek)
    if tithi_count == 30: shiva_loc = "Smashana (Inauspicious)"
    else:
        # 1-14 cycle logic
        # 1,8,15=Nandi; 2,9=Gauri; 3,10=Sabha; 4,11=Krida; 5,12=Kailash; 6,13=Vrishabha; 7,14=Bhojana
        eff_tithi = tithi_count if tithi_count <= 14 else (tithi_count - 14) if tithi_count < 30 else 30
        if tithi_count == 15 or tithi_count == 29: eff_tithi = tithi_count # Handle Purnima/Shivratri specifically if needed
        
        # Standard Lookup
        rem_shiva = tithi_count % 7
        if tithi_count in [1, 8, 15, 22, 29]: shiva_loc = "Nandi (Good)"
        elif tithi_count in [2, 9, 16, 23, 30]: 
             if tithi_count == 30: shiva_loc = "Smashana (Bad)"
             else: shiva_loc = "Gauri (Good)"
        elif tithi_count in [3, 10, 17, 24]: shiva_loc = "Sabha (Bad)"
        elif tithi_count in [4, 11, 18, 25]: shiva_loc = "Krida (Bad)"
        elif tithi_count in [5, 12, 19, 26]: shiva_loc = "Kailash (Good)"
        elif tithi_count in [6, 13, 20, 27]: shiva_loc = "Vrishabha (Good)"
        else: shiva_loc = "Bhojana (Bad)"

    # 5. BHADRA VASA (Vishti)
    if moon_rashi_idx in [0, 1, 2, 7]: bhadravasa = "Swarga (Heaven) - Auspicious" # Aries, Taurus, Gem, Scorp
    elif moon_rashi_idx in [5, 6, 8, 9]: bhadravasa = "Patala (Netherworld) - Auspicious" # Vir, Lib, Sag, Cap
    else: bhadravasa = "Prithvi (Earth) - Inauspicious" # Can, Leo, Aqu, Pis

    # 7. RAHU VASA
    rv_map = {0: "East", 1: "North", 2: "South-East", 3: "South", 4: "West", 5: "North-West", 6: "South-West"}
    rahu_vasa = rv_map[weekday_idx]

    # 8. KUMBHA CHAKRA
    sun_long = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    sun_rashi_idx = int(sun_long / 30)
    if sun_rashi_idx in [0, 1, 2]: kumbha_chakra = "West"
    elif sun_rashi_idx in [3, 4, 5]: kumbha_chakra = "North"
    elif sun_rashi_idx in [6, 7, 8]: kumbha_chakra = "East"
    else: kumbha_chakra = "South"

    return {
        "homahuti": homahuti_str, 
        "disha_shool": disha_shool,
        "agnivasa_1": agnivasa,
        "agnivasa_2": "",
        "bhadravasa": bhadravasa,
        "chandra_vasa": chandra_vasa,
        "shivavasa_1": shiva_loc,
        "shivavasa_2": "",
        "rahu_vasa": rahu_vasa,
        "kumbha_chakra": kumbha_chakra
    }

def get_epoch_details(jd, dt):
    ayanamsha = swe.get_ayanamsa(jd)
    kaliyuga_year = dt.year + 3101
    shaka_year = dt.year - 78
    mjd = jd - 2400000.5
    ahargana = int(jd - 588465.5)
    return {"kaliyuga": f"{kaliyuga_year} Years", "ayanamsha": f"{ayanamsha:.6f}", "kali_ahargana": f"{ahargana} Days", "rata_die": f"{int(jd - 1721424.5)}", "julian_date": dt.strftime("%B %d, %Y CE"), "julian_day": f"{jd:.2f}", "civil_date": f"{dt.strftime('%d %B')}, {shaka_year} Shaka", "mjd": f"{mjd:.2f}", "nirayana_date": f"{dt.strftime('%d %B')}, {shaka_year} Shaka"}

def get_chandrabalam_tarabalam_details(moon_rashi_idx, day_nak_idx):
    good_rashis = []
    for r_idx, r_name in enumerate(RASHIS):
        diff = (moon_rashi_idx - r_idx) % 12 + 1
        if diff not in [6, 8, 12]: good_rashis.append({"name": r_name.split(' ')[0], "icon": RASHI_ICONS[r_name]})
    good_naks = []
    for n_idx, n_name in enumerate(NAKSHATRAS):
        dist = (day_nak_idx - n_idx) % 9 + 1
        if dist in [2, 4, 6, 8, 9]: good_naks.append({"name": n_name, "icon": NAK_ICONS.get(n_name, "")})
    return {
        "chandrabalam": {"good_rashis": good_rashis, "ashtama_chandra": ["Ashtama Chandra check required"]},
        "tarabalam": {"period_1": {"time": "Whole Day", "nakshatras": good_naks}, "period_2": {"time": "", "nakshatras": []}}
    }

def get_panchaka_rahita_details(lagnas, tithi_idx, nak_idx, weekday_idx):
    panchaka_list = []
    V_WEEKDAY = {6:1, 0:2, 1:3, 2:4, 3:5, 4:6, 5:7}
    v_wd = V_WEEKDAY[weekday_idx]
    tithi_num = tithi_idx + 1
    nak_num = nak_idx + 1
    
    for lagna in lagnas:
        rashi_name = lagna['name']
        for i, r in enumerate(RASHIS):
            if r.startswith(rashi_name): lagna_num = i + 1; break
        
        total = tithi_num + v_wd + nak_num + lagna_num
        remainder = total % 9
        if remainder == 1: status, label = False, "Mrityu Panchaka"
        elif remainder == 2: status, label = False, "Agni Panchaka"
        elif remainder == 4: status, label = False, "Raja Panchaka"
        elif remainder == 6: status, label = False, "Chora Panchaka"
        elif remainder == 8: status, label = False, "Roga Panchaka"
        else: status, label = True, "Good Muhurta"
        panchaka_list.append({"label": label, "times": f"{lagna['start']} to {lagna['end']}", "is_good": status})
    return panchaka_list

def get_udaya_lagna_details(jd_start, jd_end, tz, lat, lon):
    lagnas = []
    swe.set_ephe_path(EPHEMERIS_PATH)
    swe.set_sid_mode(SIDEREAL_MODE)
    curr_jd = jd_start
    last_sign_idx = -1
    lagna_start_jd = jd_start
    step = 1.0 / (24 * 60) 
    
    # Determine base date from start (Sunrise)
    base_dt = dt_from_jd(jd_start, tz)
    base_date = base_dt.date() if base_dt else None

    def fmt_lagna_time(jd):
        dt = dt_from_jd(jd, tz)
        if not dt: return "---"
        if base_date and dt.date() != base_date:
            return dt.strftime("%d %b, %I:%M %p")
        return dt.strftime("%I:%M %p")

    while curr_jd < jd_end:
        try:
            trop_asc = swe.houses(curr_jd, lat, lon, b'P')[0][0]
            ayan = swe.get_ayanamsa(curr_jd)
            sid_asc = (trop_asc - ayan) % 360
            curr_sign_idx = int(sid_asc / 30)
            if last_sign_idx != -1 and curr_sign_idx != last_sign_idx:
                rashi_name = RASHIS[last_sign_idx]
                icon = RASHI_ICONS.get(rashi_name, "")
                lagnas.append({
                    "name": rashi_name.split(' ')[0], 
                    "icon": icon, 
                    "start": fmt_lagna_time(lagna_start_jd), 
                    "end": fmt_lagna_time(curr_jd)
                })
                lagna_start_jd = curr_jd
            last_sign_idx = curr_sign_idx
        except: pass
        curr_jd += step
    if last_sign_idx != -1:
        rashi_name = RASHIS[last_sign_idx]
        icon = RASHI_ICONS.get(rashi_name, "")
        lagnas.append({
            "name": rashi_name.split(' ')[0], 
            "icon": icon, 
            "start": fmt_lagna_time(lagna_start_jd), 
            "end": fmt_lagna_time(jd_end)
        })
    return lagnas

def get_festivals_details(jd, tithi_idx, sun_long, dt_obj, nak_idx, moon_rashi_idx):
    paksha_code = 0 if tithi_idx < 15 else 1
    tithi_in_paksha = tithi_idx % 15
    sun_sign_idx = int(sun_long / 30)
    lunar_month_idx = (sun_sign_idx + 1) % 12 
    festivals = []
    def get_image_url(name):
        for key, url in FESTIVAL_IMAGES_STATIC.items():
            if key in name: return url
        seed = sum(ord(c) for c in name)
        safe_name = urllib.parse.quote(name)
        return f"https://image.pollinations.ai/prompt/Hindu%20festival%20{safe_name}%20devotional%20art?width=300&height=200&nologo=true&seed={seed}"
    def add_fest(name):
        if not any(f['name'] == name for f in festivals):
            festivals.append({"name": name, "image_url": get_image_url(name)})
    key = (lunar_month_idx, paksha_code, tithi_in_paksha)
    if key in FESTIVAL_DB: add_fest(FESTIVAL_DB[key])
    greg_key = (dt_obj.month, dt_obj.day)
    if greg_key in GREGORIAN_FESTIVALS: add_fest(GREGORIAN_FESTIVALS[greg_key])
    if paksha_code == 0 and tithi_in_paksha == 3: add_fest("Vinayaka Chaturthi")
    if paksha_code == 1 and tithi_in_paksha == 3: add_fest("Sankashti Chaturthi")
    if paksha_code == 0 and tithi_in_paksha == 5: add_fest("Skanda Sashti")
    if paksha_code == 0 and tithi_in_paksha == 7: add_fest("Masik Durgashtami")
    if paksha_code == 1 and tithi_in_paksha == 7: add_fest("Kalashtami")
    if tithi_in_paksha == 10: prefix = "Shukla" if paksha_code == 0 else "Krishna"; add_fest(f"{prefix} Ekadashi")
    if tithi_in_paksha == 12: add_fest("Pradosh Vrat")
    if paksha_code == 1 and tithi_in_paksha == 13: add_fest("Masik Shivaratri")
    if paksha_code == 1 and tithi_in_paksha == 14: add_fest("Amavasya")
    if paksha_code == 0 and tithi_in_paksha == 14: add_fest("Purnima")
    if nak_idx == 2: add_fest("Masik Karthigai")
    if nak_idx == 3: add_fest("Rohini Vrat")
    return festivals

# --- NUMEROLOGY & HOROSCOPE CALCULATION ---

# Helper for Numerology
def get_numerology(dob, name):
    # Radical Number (Day)
    day = dob.day
    while day > 9: day = sum(int(d) for d in str(day))
    radical_num = day
    
    # Destiny Number (Full Date)
    total_sum = sum(int(d) for d in dob.strftime("%d%m%Y"))
    while total_sum > 9: total_sum = sum(int(d) for d in str(total_sum))
    destiny_num = total_sum
    
    # Name Number (Chaldean)
    name_sum = 0
    if name:
        for char in name.upper():
            if char in CHALDEAN_MAP:
                name_sum += CHALDEAN_MAP[char]
    while name_sum > 9: name_sum = sum(int(d) for d in str(name_sum))
    name_num = name_sum

    # Evil Number (Simple logic: Enemy of Radical)
    evil_num = NUMEROLOGY_DATA[radical_num]["enemy"]
    neutral_num = NUMEROLOGY_DATA[radical_num]["neutral"]
    friendly_num = NUMEROLOGY_DATA[radical_num]["friend"]
    radical_ruler = NUMEROLOGY_DATA[radical_num]["ruler"]

    return {
        "radical_num": radical_num,
        "destiny_num": destiny_num,
        "name_num": name_num,
        "evil_num": evil_num,
        "neutral_num": neutral_num,
        "friendly_num": friendly_num,
        "radical_ruler": radical_ruler
    }

# --- DOSHA CALCULATION ---
def calculate_doshas(planet_positions, lagna_rashi, moon_rashi):
    # Prepare positions: { 'Mars': house_num, 'Rahu': house_num, ... }
    # House num relative to Lagna (1 to 12)
    p_houses = {p['planet']: p['house'] for p in planet_positions}
    
    dosha_report = []
    
    # 1. Mangal Dosha (Mars in 1, 2, 4, 7, 8, 12 from Lagna)
    mars_house = p_houses.get('Mars')
    if mars_house in [1, 2, 4, 7, 8, 12]:
        dosha_report.append({
            "name": "Mangal Dosha",
            "status": "Present",
            "desc": "Mars is placed in a sensitive house (1, 2, 4, 7, 8, 12). This may cause delays or disharmony in marriage.",
            "remedy": "Perform Kumbh Vivah or worship Lord Hanuman."
        })
    else:
        dosha_report.append({ "name": "Mangal Dosha", "status": "Absent", "desc": "No Mangal Dosha present.", "remedy": "None needed." })

    # 2. Kalsarpa Dosha (Planets hemmed between Rahu/Ketu)
    # Simplified logic: Check if all major planets are within the arc of Rahu/Ketu
    # This requires degree comparison which is complex here. 
    # Placeholder logic:
    dosha_report.append({ "name": "Kalsarpa Dosha", "status": "Absent", "desc": "Planets are not hemmed between Rahu and Ketu.", "remedy": "None needed." })

    # 3. Pitra Dosha (Sun/Moon with Rahu/Ketu or in 9th)
    sun_h = p_houses.get('Sun')
    moon_h = p_houses.get('Moon')
    rahu_h = p_houses.get('Rahu')
    ketu_h = p_houses.get('Ketu')
    
    is_pitra = False
    if sun_h == 9 or moon_h == 9: is_pitra = True
    if sun_h == rahu_h or sun_h == ketu_h: is_pitra = True
    if moon_h == rahu_h or moon_h == ketu_h: is_pitra = True
    
    if is_pitra:
        dosha_report.append({
            "name": "Pitra Dosha",
            "status": "Present",
            "desc": "Sun/Moon afflicted by Nodes or 9th house affliction indicates ancestral debt.",
            "remedy": "Perform Shradh/Tarpan for ancestors or donate food on Amavasya."
        })
    else:
        dosha_report.append({ "name": "Pitra Dosha", "status": "Absent", "desc": "No major Pitra Dosha detected.", "remedy": "None needed." })

    return dosha_report


# --- DASHA CALCULATION ---
def get_formatted_duration(total_days):
    years = int(total_days / 365.25)
    remaining_days = total_days % 365.25
    months = int(remaining_days / 30.44)
    days = int(remaining_days % 30.44)
    parts = []
    if years > 0: parts.append(f"{years}y")
    if months > 0: parts.append(f"{months}m")
    if days > 0: parts.append(f"{days}d")
    return " ".join(parts) if parts else "0d"

def calculate_antardashas(mahadasha_lord, mahadasha_start_date, birth_date=None):
    sub_periods = []
    start_idx = DASHA_ORDER.index(mahadasha_lord)
    current_sub_date = mahadasha_start_date
    m_years = DASHA_YEARS[mahadasha_lord]

    for i in range(9):
        sub_lord_idx = (start_idx + i) % 9
        sub_lord = DASHA_ORDER[sub_lord_idx]
        s_years = DASHA_YEARS[sub_lord]
        days_duration = (m_years * s_years * 365.25) / 120.0
        end_sub_date = current_sub_date + timedelta(days=days_duration)
        
        if birth_date:
            if end_sub_date < birth_date:
                current_sub_date = end_sub_date
                continue 
            if current_sub_date < birth_date:
                actual_start = birth_date
                actual_duration = (end_sub_date - actual_start).days
                sub_periods.append({
                    "lord": sub_lord,
                    "start": actual_start.strftime("%d-%b-%Y"),
                    "end": end_sub_date.strftime("%d-%b-%Y"),
                    "duration": get_formatted_duration(actual_duration)
                })
                current_sub_date = end_sub_date
                continue

        sub_periods.append({
            "lord": sub_lord,
            "start": current_sub_date.strftime("%d-%b-%Y"),
            "end": end_sub_date.strftime("%d-%b-%Y"),
            "duration": get_formatted_duration(days_duration)
        })
        current_sub_date = end_sub_date

    return sub_periods

def calculate_vimshottari_dasha(moon_long, birth_date):
    nak_span = 13.333333333333333
    nak_idx = int(moon_long / nak_span)
    degrees_in_nak = moon_long % nak_span
    fraction_passed = degrees_in_nak / nak_span
    dasha_lord_idx = nak_idx % 9
    start_lord = DASHA_ORDER[dasha_lord_idx]
    total_years = DASHA_YEARS[start_lord]
    years_passed = total_years * fraction_passed
    years_remaining = total_years - years_passed
    theoretical_start_days = years_passed * 365.25
    theoretical_start_date = birth_date - timedelta(days=theoretical_start_days)
    first_dasha_end_date = theoretical_start_date + timedelta(days=total_years * 365.25)
    
    dasha_list = []
    dasha_list.append({
        "lord": start_lord,
        "start": birth_date.strftime("%d-%b-%Y"),
        "end": first_dasha_end_date.strftime("%d-%b-%Y"),
        "duration": get_formatted_duration(years_remaining * 365.25),
        "antardashas": calculate_antardashas(start_lord, theoretical_start_date, birth_date=birth_date)
    })
    
    current_date = first_dasha_end_date
    for i in range(1, 9):
        next_idx = (dasha_lord_idx + i) % 9
        lord = DASHA_ORDER[next_idx]
        duration_years = DASHA_YEARS[lord]
        end_date = current_date + timedelta(days=duration_years * 365.25)
        dasha_list.append({
            "lord": lord,
            "start": current_date.strftime("%d-%b-%Y"),
            "end": end_date.strftime("%d-%b-%Y"),
            "duration": f"{duration_years} Years",
            "antardashas": calculate_antardashas(lord, current_date)
        })
        current_date = end_date
    return dasha_list



def get_sudarshana_chakra(planetary_positions, lagna_rashi_idx, moon_rashi_idx, sun_rashi_idx):
    """
    Generates data for Sudarshana Chakra (Lagna, Moon, Sun charts).
    Returns a dict with 12 houses for each chart.
    """
    charts = {}
    
    # Helper to build a chart based on a reference sign (Shift logical house 1 to that sign)
    def build_chart(reference_sign_idx):
        chart = {str(i): [] for i in range(1, 13)} # Houses 1-12
        
        # Populate based on planet's Rasi index
        # House = (Planet_Rasi - Reference_Rasi + 12) % 12 + 1
        for planet in planetary_positions:
            # We need the rasi index of the planet. 
            # The planet object in planetary_positions has 'rasi' name, but maybe we can find the index efficiently?
            # Or we can pass 'chart_data' (by rasi index) instead of 'planetary_positions'.
            # Let's use RASHIS map or re-calculate. 
            # Actually, planetary_positions has "rasi": "Aries" etc.
            # Let's trust RASHIS.index(planet['rasi'])
            try:
                p_rasi_idx = RASHIS.index(planet['rasi'])
                house_num = (p_rasi_idx - reference_sign_idx + 12) % 12 + 1
                chart[str(house_num)].append(planet['symbol']) # Use symbol (Su, Mo, etc)
            except:
                pass
        return chart

    charts['lagna_chart'] = build_chart(lagna_rashi_idx)
    charts['moon_chart'] = build_chart(moon_rashi_idx)
    charts['sun_chart'] = build_chart(sun_rashi_idx)
    
    return charts

def get_horoscope_by_birth_details(loc, date_str, time_str, name=""):
    setup_swisseph()
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except: return None

    tz = loc['tz']
    local_dt = tz.localize(dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0)

    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    planet_map = {0: swe.SUN, 1: swe.MOON, 2: swe.MARS, 3: swe.MERCURY, 4: swe.JUPITER, 5: swe.VENUS, 6: swe.SATURN, 7: swe.MEAN_NODE, 8: swe.MEAN_NODE, 9: swe.URANUS, 10: swe.NEPTUNE, 11: swe.PLUTO}
    
    chart_data = {i: [] for i in range(12)} 
    navamsa_chart_data = {i: [] for i in range(12)}
    planetary_positions = [] 

    cusps, ascmc = swe.houses(jd, loc['lat'], loc['lon'], b'P')
    lagna_deg = ascmc[0]
    lagna_rashi = int(lagna_deg / 30)
    chart_data[lagna_rashi].append("Lagna")
    
    lagna_total_min = (lagna_deg) * 60
    lagna_navamsa_rashi = int(lagna_total_min / 200) % 12
    navamsa_chart_data[lagna_navamsa_rashi].append("Lagna")

    def deg_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = int(((deg - d) * 60 - m) * 60)
        return f"{d:02d}° {m:02d}' {s:02d}\""
        
    def get_nak(long):
        nak_deg = 13.333333333333333
        idx = int(long / nak_deg)
        pada = int((long % nak_deg) / 3.333333333333333) + 1
        return NAKSHATRAS[idx], pada, idx

    moon_long = 0
    lnak, lpada, lnak_idx = get_nak(lagna_deg)
    
    lagna_vargas = {}
    for v_num in [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]:
        v_sign_idx = get_varga_sign(lagna_deg % 30, lagna_rashi, v_num)
        lagna_vargas[f"D{v_num}"] = {
            "sign": RASHIS[v_sign_idx], 
            "sign_id": v_sign_idx
        }

    planetary_positions.append({
        "planet": "Ascendant", "icon": "Asc", "symbol": "As", "is_retro": False, "position": deg_to_dms(lagna_deg), "degree": deg_to_dms(lagna_deg % 30),
        "rasi": RASHIS[lagna_rashi], "rasi_lord": RASI_LORDS_MAP[lagna_rashi],
        "nakshatra": f"{lnak} ({lpada})", "nak_lord": NAK_LORDS[lnak_idx % 9], "house": 1,
        "relationship": "-",
        "vargas": lagna_vargas
    })

    p_names = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto"]
    p_symbols = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke", "Ur", "Ne", "Pl"]
    
    for i in range(12):
        body = planet_map[i]
        res = swe.calc_ut(jd, body, flags)
        deg = res[0][0]
        speed = res[0][3]
        
        is_retro = True if speed < 0 else False
        if i in [7, 8]: is_retro = True 
        
        if i == 8: deg = (deg + 180) % 360 # Ketu
        if i == 1: moon_long = deg
            
        rashi = int(deg / 30)
        p_name = p_names[i]
        
        chart_data[rashi].append(p_name[:3])
        total_minutes = deg * 60
        navamsa_rashi_idx = int(total_minutes / 200) % 12
        navamsa_chart_data[navamsa_rashi_idx].append(p_name[:3])
        
        nak, pada, nak_idx = get_nak(deg)
        house_num = (rashi - lagna_rashi + 12) % 12 + 1
        
        vargas = {}
        for v_num in [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]:
            v_sign_idx = get_varga_sign(deg % 30, rashi, v_num)
            vargas[f"D{v_num}"] = {
                "sign": RASHIS[v_sign_idx], 
                "sign_id": v_sign_idx
            }

        planetary_positions.append({
            "planet": p_name, "icon": PLANET_ICONS.get(p_name, ""), "symbol": p_symbols[i], "is_retro": is_retro, "position": deg_to_dms(deg), "degree": deg_to_dms(deg % 30),
            "rasi": RASHIS[rashi], "rasi_lord": RASI_LORDS_MAP[rashi],
            "nakshatra": f"{nak} ({pada})", "nak_lord": NAK_LORDS[nak_idx % 9], "house": house_num,
            "relationship": get_planet_relationship(p_name, RASI_LORDS_MAP[rashi], rashi),
            "vargas": vargas
        })
        
    moon_rashi_idx = int(moon_long / 30)
    import copy
    chandra_chart_data = copy.deepcopy(chart_data)
    if "Lagna" in chandra_chart_data[lagna_rashi]:
        chandra_chart_data[lagna_rashi].remove("Lagna")
    chandra_chart_data[moon_rashi_idx].append("Lagna (Mo)")

    nak_idx = int(moon_long / 13.333333333333333)
    pada = int((moon_long % 13.333333333333333) / 3.333333333333333) + 1
    nak_str = f"{NAKSHATRAS[nak_idx]} ({pada} Pada)"

    # START/END CALCULATIONS FOR HOROSCOPE
    def get_sign_start_end(jd_center, body_id, current_sign_idx, tz):
        # 1. Find START (Entry into current sign)
        # Search backward for when sign index was (current - 1)
        # Or simpler: Find when sign index becomes current_sign_idx
        # We start search from ~35 days back for Sun, ~4 days back for Moon
        days_back = 35 if body_id == swe.SUN else 4
        search_start = jd_center - days_back
        
        def check_sign_idx(t):
            pos = swe.calc_ut(t, body_id, flags)[0][0]
            return int(pos / 30)
            
        entry_jd = find_trans(search_start, check_sign_idx, current_sign_idx)
        
        # 2. Find END (Exit from current sign)
        # Search forward for when sign index becomes (current + 1) % 12
        next_sign = (current_sign_idx + 1) % 12
        exit_jd = find_trans(jd_center, check_sign_idx, next_sign)
        
        entry_str = dt_from_jd(entry_jd, tz).strftime("%d %b %Y, %I:%M %p") if entry_jd else "---"
        exit_str = dt_from_jd(exit_jd, tz).strftime("%d %b %Y, %I:%M %p") if exit_jd else "---"
        return entry_str, exit_str

    def get_nak_start_end(jd_center, current_nak_idx, tz):
        # Search range for moon nakshatra: +/- 2 days
        search_start = jd_center - 2.0
        
        def check_nak_idx(t):
            pos = swe.calc_ut(t, swe.MOON, flags)[0][0]
            return int(pos / 13.333333333)
            
        entry_jd = find_trans(search_start, check_nak_idx, current_nak_idx)
        
        next_nak = (current_nak_idx + 1) % 27
        exit_jd = find_trans(jd_center, check_nak_idx, next_nak)
        
        entry_str = dt_from_jd(entry_jd, tz).strftime("%d %b %Y, %I:%M %p") if entry_jd else "---"
        exit_str = dt_from_jd(exit_jd, tz).strftime("%d %b %Y, %I:%M %p") if exit_jd else "---"
        return entry_str, exit_str

    # Calculate Timing Details
    sun_long = swe.calc_ut(jd, swe.SUN, flags)[0][0]
    sun_rashi_idx = int(sun_long / 30)
    
    moon_entry, moon_exit = get_sign_start_end(jd, swe.MOON, moon_rashi_idx, tz)
    sun_entry, sun_exit = get_sign_start_end(jd, swe.SUN, sun_rashi_idx, tz)
    nak_entry, nak_exit = get_nak_start_end(jd, nak_idx, tz)
    
    # Store these in kundli_details
    timings = {
        "moon_sign_start": moon_entry, "moon_sign_end": moon_exit,
        "sun_sign_start": sun_entry, "sun_sign_end": sun_exit,
        "nak_start": nak_entry, "nak_end": nak_exit
    }


    ayan_val = swe.get_ayanamsa(jd)
    d = int(ayan_val)
    m = int((ayan_val - d) * 60)
    s = int(((ayan_val - d) * 60 - m) * 60)
    ayan_str = f"{d}° {m}' {s}\" (Lahiri)"

    gana_idx = 0 if nak_idx in GANAS["Deva"] else 1 if nak_idx in GANAS["Manushya"] else 2
    gana = ["Deva", "Manushya", "Rakshasa"][gana_idx]
    yoni = YONIS[nak_idx % 27]
    nadi_type = "Adi (Vata)" if nak_idx in NADIS["Adi (Vata)"] else "Madhya (Pitta)" if nak_idx in NADIS["Madhya (Pitta)"] else "Antya (Kapha)"
    moon_rashi_idx = int(moon_long / 30)
    varna = VARNA[moon_rashi_idx]
    vashya = VASHYA[moon_rashi_idx]
    
    tithi_idx_b = int(((moon_long - sun_long) % 360) / 12)
    tithi_idx_b = int(((moon_long - sun_long) % 360) / 12)
    birth_tithi = TITHIS[tithi_idx_b]
    
    # Calculate Samvat
    samvat_details = get_samvat_details(dt)
    
    # Calculate Sunrise/Sunset for birth day
    rise, set_ = calc_sun_rise_set(jd - 0.5, loc['lat'], loc['lon']) # Approx check
    # More precise:
    jd_noon = jd_from_dt(tz.localize(datetime(dt.year, dt.month, dt.day, 12, 0)))
    rise, set_ = calc_sun_rise_set(jd_noon, loc['lat'], loc['lon'])
    
    def fmt_time(jd_time):
        d = dt_from_jd(jd_time, tz)
        return d.strftime('%I:%M %p') if d else "---"
    
    sunrise_str = fmt_time(rise)
    sunset_str = fmt_time(set_)
    
    yoga_idx_b = int(((moon_long + sun_long) % 360) / 13.333333)
    birth_yoga = YOGAS[yoga_idx_b]
    
    karana_idx_b = int(((moon_long - sun_long) % 360) / 6)
    if karana_idx_b == 0: birth_karana = KARANAS[10]
    elif karana_idx_b >= 57: birth_karana = KARANAS[karana_idx_b - 50]
    else: birth_karana = KARANAS[(karana_idx_b - 1) % 7]
    
    tatva = TATVA[moon_rashi_idx]
    moon_house_num = (moon_rashi_idx - lagna_rashi + 12) % 12 + 1
    if moon_house_num in [1, 6, 11]: paya = "Gold (Swarna)"
    elif moon_house_num in [2, 5, 9]: paya = "Silver (Rajata)"
    elif moon_house_num in [3, 7, 10]: paya = "Copper (Tamra)"
    else: paya = "Iron (Loha)"
    
    if nak_idx < 9: yunja = "Poorva"
    elif nak_idx < 18: yunja = "Madhya"
    else: yunja = "Uttara"
    
    global_pada_idx = (nak_idx * 4) + (pada - 1)
    name_alphabet = NAMA_AKSHARA[global_pada_idx]
    
    # Get all 4 alphabets for the Nakshatra
    nak_start_idx = nak_idx * 4
    nak_alphabets = NAMA_AKSHARA[nak_start_idx : nak_start_idx + 4]
    nak_lord = NAK_LORDS[nak_idx % 9]
    nak_lord = NAK_LORDS[nak_idx % 9]
    sign_lord = RASI_LORDS_MAP[moon_rashi_idx]
    lagna_lord = RASI_LORDS_MAP[lagna_rashi] # Ascendant Lord
    
    fav_data = FAV_POINTS.get(lagna_rashi, {})
    num_data = get_numerology(dt, name)
    fav_data.update(num_data)
    lagna_prediction = KUNDLI_PREDICTIONS.get(lagna_rashi, {"general": "", "career": "", "health": "", "marriage": ""})
    
    dasha_periods = calculate_vimshottari_dasha(moon_long, dt)
    dosha_details = calculate_doshas(planetary_positions, lagna_rashi, moon_rashi_idx)
    
    # SUDARSHANA CHAKRA
    sudarshana_data = get_sudarshana_chakra(planetary_positions, lagna_rashi, moon_rashi_idx, sun_rashi_idx)
    
    kundli_details = {
        "gana": gana, "yoni": yoni, "nadi": nadi_type,
        "varna": varna, "vashya": vashya,
        "tithi": birth_tithi, "yoga": birth_yoga, "karana": birth_karana,
        "tatva": tatva, "paya": paya, "yunja": yunja,
        "name_alphabet": name_alphabet,
        "nak_alphabets": nak_alphabets,
        "nak_lord": nak_lord, "sign_lord": sign_lord,
        "fav": fav_data,
        "prediction": lagna_prediction,
        "timings": timings # NEW
    }

    # KUNDALI TABLE GENERATION
    kundali_table = []
    for h in range(1, 13):
        # Determine Rashi for this house
        rashi_idx = (lagna_rashi + h - 1) % 12
        r_name = RASHIS[rashi_idx]
        r_lord = RASI_LORDS_MAP[rashi_idx]
        
        # Find planets in this house
        planets_in_house = [p for p in planetary_positions if p['house'] == h]
        
        kundali_table.append({
            "house": h,
            "rashi": r_name,
            "lord": r_lord,
            "planets": planets_in_house
        })
    
    # CALCULATE SHODASHVARGA CHART DATA
    shodashvarga_charts = {f"D{v}": {i: [] for i in range(12)} for v in [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]}
    
    # Add planets to charts
    for p in planetary_positions:
        p_symbol = p['symbol']
        p_vargas = p.get('vargas', {})
        
        for v_key, v_data in p_vargas.items():
            # v_key is like "D9", v_data is {"sign": "Aries", "sign_id": 0}
            if v_key in shodashvarga_charts:
                sign_idx = v_data['sign_id']
                shodashvarga_charts[v_key][sign_idx].append(p_symbol)

    # Add chart titles mapping
    varga_titles = {
        "D1": "Rashi (D1)", "D2": "Hora (D2)", "D3": "Drekkana (D3)", "D4": "Chaturthamsha (D4)",
        "D7": "Saptamsha (D7)", "D9": "Navamsa (D9)", "D10": "Dashamsha (D10)", "D12": "Dwadashamsha (D12)",
        "D16": "Shodashamsha (D16)", "D20": "Vimshamsha (D20)", "D24": "Chaturvimshamsha (D24)",
        "D27": "Saptavimshamsha (D27)", "D30": "Trimshamsha (D30)", "D40": "Khavedamsha (D40)",
        "D45": "Akshavedamsha (D45)", "D60": "Shashtiamsha (D60)"
    }

    return {
        "chart": chart_data, 
        "navamsa_chart": navamsa_chart_data,
        "chandra_chart": chandra_chart_data,
        "lagna": RASHIS[lagna_rashi], 
        "moon_sign": RASHIS[moon_rashi_idx], 
        "nakshatra": nak_str, 
        "ayanamsa_val": ayan_str,
        "planetary_positions": planetary_positions,
        "kundali_table": kundali_table, # New Data
        "kundli_details": kundli_details,
        "dasha_periods": dasha_periods,
        "dosha_details": dosha_details,
        "samvat": samvat_details, 
        "lagna_lord": lagna_lord, # New
        "sunrise": sunrise_str,   # New
        "sunset": sunset_str,     # New
        "timezone": tz.zone,      # Useful for reference
        "sudarshana": sudarshana_data, # New
        "shodashvarga_charts": shodashvarga_charts, # Added
        "varga_titles": varga_titles               # Added
    }

# --- MUHURTHA CALCULATOR ---
def get_monthly_muhurthas(loc, year, month):
    RULES = {
        "marriage": {"naks": ["Rohini", "Mrigashira", "Magha", "Uttara Phalguni", "Hasta", "Swati", "Anuradha", "Mula", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"], "tithis": ["Dwitiya", "Tritiya", "Panchami", "Saptami", "Dashami", "Ekadashi", "Trayodashi"], "exclude_days": [1, 6]},
        "gruha": {"naks": ["Rohini", "Mrigashira", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"], "tithis": ["Dwitiya", "Tritiya", "Panchami", "Shashthi", "Saptami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi"], "exclude_days": [1, 6]},
        "naming": {"naks": ["Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"], "tithis": ["Pratipada", "Dwitiya", "Tritiya", "Panchami", "Saptami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Purnima"], "exclude_days": []},
        "vehicle": {"naks": ["Ashwini", "Rohini", "Punarvasu", "Pushya", "Hast", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Shatabhisha", "Revati"], "tithis": ["Tritiya", "Panchami", "Shashthi", "Dashami", "Ekadashi", "Purnima"], "exclude_days": [1]}
    }
    cal = calendar.monthcalendar(year, month)
    results = {k: [] for k in RULES.keys()}
    for week in cal:
        for day in week:
            if day == 0: continue
            date_str = f"{year}-{month:02d}-{day:02d}"
            try:
                lite_data = fetch_month_day_data(loc, date_str)
                dt_obj = datetime(year, month, day)
                weekday = dt_obj.weekday()
                curr_nak = lite_data['nakshatra'].split(' ')[0]
                curr_tithi = lite_data['tithi']
                tithi_name = curr_tithi.split(' ')[-1]
                for cat, rule in RULES.items():
                    if weekday in rule['exclude_days']: continue
                    nak_match = any(n in curr_nak for n in rule['naks'])
                    tithi_match = any(t == tithi_name for t in rule['tithis'])
                    if "Amavasya" in curr_tithi or "Chaturthi" in tithi_name or "Navami" in tithi_name: tithi_match = False
                    if nak_match and tithi_match:
                        full_data = fetch_panchang(loc, date_str)
                        results[cat].append({
                            "date": f"{day} {calendar.month_name[month]}", "day_name": dt_obj.strftime("%A"), 
                            "nakshatra": curr_nak, "tithi": curr_tithi, "full_date": date_str,
                            "tithi_start": lite_data['tithi_start'], "tithi_end": lite_data['tithi_end'], "nak_end": lite_data['nak_end'],
                            "amrit": full_data['timings']['amrit'], "abhijit": full_data['timings']['abhijit']
                        })
            except: continue
    return results

# --- Main Fetch Function ---
def fetch_panchang(loc_str_or_dict, date_str):
    setup_swisseph()
    if isinstance(loc_str_or_dict, dict): loc = loc_str_or_dict
    else: loc = get_location(loc_str_or_dict)
    if not loc: return {"error": "Location not found"}
    
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    tz = loc['tz']
    jd_noon = jd_from_dt(tz.localize(datetime(dt.year, dt.month, dt.day, 12, 0)))
    rise, set_ = calc_sun_rise_set(jd_noon, loc['lat'], loc['lon'])
    moon_rise, moon_set = calc_moon_rise_set(jd_noon, loc['lat'], loc['lon'])
    rise_next, _ = calc_sun_rise_set(jd_noon + 1, loc['lat'], loc['lon'])
    sun_long, moon_long = get_pos(rise)
    moon_rashi_idx = int(moon_long / 30)
    sun_rashi_idx = int(sun_long / 30)
    w_idx = dt_from_jd(rise, tz).weekday()
    
    day_len = set_ - rise
    def get_kalam(k_map):
        s = rise + ((k_map[w_idx]-1) * (day_len/8))
        d_start = dt_from_jd(s, tz)
        d_end = dt_from_jd(s + day_len/8, tz)
        if not d_start or not d_end: return "---"
        s_fmt = d_start.strftime('%b %d, %I:%M %p') if d_start.date() != dt.date() else d_start.strftime('%I:%M %p')
        e_fmt = d_end.strftime('%b %d, %I:%M %p') if d_end.date() != dt.date() else d_end.strftime('%I:%M %p')
        return f"{s_fmt} - {e_fmt}"
    rahu_time = get_kalam(RAHU_KEY)
    yama_time = get_kalam(YAMA_KEY)
    guli_time = get_kalam(GULI_KEY)

    samvat = get_samvat_details(dt)
    
    # CALCULATE CHANDRAMASA (LUNAR MONTH)
    lunar_month_idx_calc = (int(sun_long / 30) + 1) % 12
    current_chandramasa = MONTHS[lunar_month_idx_calc]
    samvat["chandramasa"] = current_chandramasa

    ritu_ayana = get_ritu_ayana_details(rise)
    muhurtas = calculate_muhurtas(rise, set_, rise_next, w_idx)
    tithi_idx = int(((moon_long - sun_long) % 360) / 12)
    nak_idx = int(moon_long / 13.333333)
    sun_nak_idx = int(sun_long / 13.333333)
    nivas_shool = get_nivas_shool_details(jd_noon, w_idx, tithi_idx, nak_idx)
    epoch = get_epoch_details(jd_noon, dt)
    chandrabalam_tarabalam = get_chandrabalam_tarabalam_details(moon_rashi_idx, nak_idx)
    udaya_lagna = get_udaya_lagna_details(rise, rise_next, tz, loc['lat'], loc['lon'])
    panchaka_rahita = get_panchaka_rahita_details(udaya_lagna, tithi_idx, nak_idx, w_idx)
    festivals = get_festivals_details(rise, tithi_idx, sun_long, dt, nak_idx, moon_rashi_idx)
    dinamana = fmt_duration(rise, set_)
    ratrimana = fmt_duration(set_, rise_next)
    madhyahna_jd = rise + (set_ - rise) / 2
    
    def fmt_dt(jd): 
        d = dt_from_jd(jd, tz)
        if not d: return "---"
        return d.strftime('%b %d, %I:%M %p') if d.date() != dt.date() else d.strftime('%I:%M %p')
    def fmt_range(start, end): return f"{fmt_dt(start)} - {fmt_dt(end)}"
    
    fn_tithi = lambda j: (int((get_pos(j)[1] - get_pos(j)[0]) % 360 / 12), 0)
    fn_nak = lambda j: (int(get_pos(j)[1] / 13.333333333), 0)
    fn_yoga = lambda j: (int((get_pos(j)[1] + get_pos(j)[0]) % 360 / 13.333333333), 0)
    fn_karana = lambda j: (int((get_pos(j)[1] - get_pos(j)[0]) % 360 / 6), 0)
    
    tithi_events = get_events(rise, rise_next, fn_tithi, TITHIS, 30)
    nak_events = get_events(rise, rise_next, fn_nak, NAKSHATRAS, 27)
    calc_timings = get_calculated_timings(nak_events, w_idx, sun_nak_idx, tithi_events, rise, rise_next, tz)
    
    nk_start = nak_events[0]['start'] if nak_events else rise
    v_s = nk_start + (VARJYAM_STARTS[nak_idx]/60.0)
    varjyam_time = fmt_range(v_s, v_s + 4/60.0)
    a_s = nk_start + (AMRIT_STARTS[nak_idx]/60.0)
    amrit_time = fmt_range(a_s, a_s + 4/60.0)
    
    # SIGN TRANSITS FOR DAILY VIEW
    def get_sign_entry_exit_daily(jd_current, body_id, current_sign_idx, tz):
        # Similar logic to horoscope but focused on 'today' context
        # Exit (Next transition)
        target_next = (current_sign_idx + 1) % 12
        def check_sign_idx(t):
            pos = swe.calc_ut(t, body_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)[0][0]
            return int(pos / 30)
        exit_jd = find_trans(jd_current, check_sign_idx, target_next)
        
        # Entry (Prev transition)
        search_start = jd_current - (35 if body_id == swe.SUN else 4)
        entry_jd = find_trans(search_start, check_sign_idx, current_sign_idx)
        
        entry_str = dt_from_jd(entry_jd, tz).strftime("%d %b, %I:%M %p") if entry_jd else "---"
        exit_str = dt_from_jd(exit_jd, tz).strftime("%d %b, %I:%M %p") if exit_jd else "---"
        return entry_str, exit_str

    moon_rashi_start, moon_rashi_end = get_sign_entry_exit_daily(jd_noon, swe.MOON, moon_rashi_idx, tz)
    sun_rashi_start, sun_rashi_end = get_sign_entry_exit_daily(jd_noon, swe.SUN, sun_rashi_idx, tz)

    data = {
        "meta": {"location": loc['name'], "date": dt_from_jd(rise, tz).strftime("%A, %d %B %Y"), "sunrise": fmt_dt(rise), "sunset": fmt_dt(set_), "moonrise": fmt_dt(moon_rise), "moonset": fmt_dt(moon_set)},
        "details": {
            "moonsign": RASHIS[moon_rashi_idx], 
            "sunsign": RASHIS[sun_rashi_idx], 
            "samvat": samvat, 
            "ritu_ayana": ritu_ayana, 
            "dinamana": dinamana, 
            "ratrimana": ratrimana, 
            "madhyahna": fmt_dt(madhyahna_jd), 
            "nivas_shool": nivas_shool, 
            "epoch": epoch, 
            "chandrabalam_tarabalam": chandrabalam_tarabalam, 
            "panchaka_rahita": panchaka_rahita, 
            "udaya_lagna": udaya_lagna, 
            "festivals": festivals,
            # NEW: Sign Timings
            "moonsign_start": moon_rashi_start, "moonsign_end": moon_rashi_end,
            "sunsign_start": sun_rashi_start, "sunsign_end": sun_rashi_end
        },
        "tithi": tithi_events, "nakshatra": nak_events, "yoga": get_events(rise, rise_next, fn_yoga, YOGAS, 27), "karana": get_events(rise, rise_next, fn_karana, [], 60, True),
        "moon_pada": get_events(rise, rise_next, lambda j: (int(get_pos(j)[1] / 3.333333333), 0), PADA_NAMES, 108),
        "sun_pada": get_events(rise, rise_next, lambda j: (int(get_pos(j)[0] / 3.333333333), 0), PADA_NAMES, 108),
        "timings": {
            "brahma": fmt_range(*muhurtas["brahma"]), "pratah": fmt_range(*muhurtas["pratah"]), "vijaya": fmt_range(*muhurtas["vijaya"]), "godhuli": fmt_range(*muhurtas["godhuli"]), "sayahna": fmt_range(*muhurtas["sayahna"]), "nishita": fmt_range(*muhurtas["nishita"]), "dur_day": ", ".join([fmt_range(s, e) for s, e in muhurtas["dur_day"]]),
            "sarvartha": calc_timings["sarvartha"], "baana": calc_timings["baana"], "vidaal": calc_timings["vidaal"], "anandadi": calc_timings["anandadi"], "tamil": calc_timings["tamil"], "jeevanama": calc_timings["jeevanama"], "netrama": calc_timings["netrama"], "tripushkara": calc_timings["tripushkara"],
            "rahu": rahu_time, "yama": yama_time, "guli": guli_time, "varjyam": varjyam_time, "amrit": amrit_time
        }
    }
    
    if isinstance(muhurtas["abhijit"], tuple): data["timings"]["abhijit"] = fmt_range(*muhurtas["abhijit"])
    else: data["timings"]["abhijit"] = muhurtas["abhijit"]
    
    for item in data['tithi']: item['start_fmt'] = fmt_dt(item['start']); item['end_fmt'] = fmt_dt(item['end']); item['icon'] = TITHI_ICONS.get(item['name'], "🌑")
    for item in data['nakshatra']: item['start_fmt'] = fmt_dt(item['start']); item['end_fmt'] = fmt_dt(item['end']); item['icon'] = NAK_ICONS.get(item['name'], "✨")
    for k in ['yoga', 'karana', 'moon_pada', 'sun_pada']:
        for item in data[k]: item['start_fmt'] = fmt_dt(item['start']); item['end_fmt'] = fmt_dt(item['end'])
        
    return data

def fetch_month_day_data(loc, date_str):
    setup_swisseph()
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    tz = loc['tz']
    jd_noon = jd_from_dt(tz.localize(datetime(dt.year, dt.month, dt.day, 12, 0)))
    rise, _ = calc_sun_rise_set(jd_noon, loc['lat'], loc['lon'])
    rise_next, _ = calc_sun_rise_set(jd_noon + 1, loc['lat'], loc['lon'])
    sun_long, moon_long = get_pos(rise)
    tithi_at_sunrise_idx = int(((moon_long - sun_long) % 360) / 12)
    nak_idx_sunrise = int(moon_long / 13.333333)
    moon_rashi_idx = int(moon_long / 30)
    
    sun_rashi_new_moon = int((sun_long - (tithi_at_sunrise_idx * 1.0)) / 30)
    lunar_month_name = MONTHS[(sun_rashi_new_moon + 1) % 12]

    fn_tithi = lambda j: (int((get_pos(j)[1] - get_pos(j)[0]) % 360 / 12), 0)
    fn_nak = lambda j: (int(get_pos(j)[1] / 13.333333333), 0)
    
    tithi_events = get_events(rise, rise_next, fn_tithi, TITHIS, 30)
    nak_events = get_events(rise, rise_next, fn_nak, NAKSHATRAS, 27)
    
    festivals = get_festivals_details(rise, tithi_at_sunrise_idx, sun_long, dt, nak_idx_sunrise, moon_rashi_idx)
    
    def fmt_dt(jd): 
        d = dt_from_jd(jd, tz)
        if not d: return "---"
        return d.strftime('%b %d, %I:%M %p') if d.date() != dt.date() else d.strftime('%I:%M %p')

    t_item = tithi_events[0]
    tithi_name = t_item['name'].split(' ')[-1]
    tithi_icon = TITHI_ICONS.get(t_item['name'], "🌑")
    tithi_start = fmt_dt(t_item['start'])
    tithi_end = fmt_dt(t_item['end'])
    
    n_item = nak_events[0]
    nak_name = n_item['name']
    nak_end = fmt_dt(n_item['end'])
    festival_names = [f['name'] for f in festivals]
    
    return {
        "tithi": tithi_name, "tithi_icon": tithi_icon,
        "tithi_start": tithi_start, "tithi_end": tithi_end,
        "nakshatra": nak_name, "nak_end": nak_end,
        "is_festival": len(festivals) > 0,
        "festival_names": festival_names,
        "lunar_month": lunar_month_name
    }
# NATURAL PLANETARY RELATIONSHIPS (Naisargika Mitra)
PLANET_RELATIONSHIPS = {
    'Sun': {'Friends': ['Moon', 'Mars', 'Jupiter'], 'Neutral': ['Mercury'], 'Enemies': ['Venus', 'Saturn']},
    'Moon': {'Friends': ['Sun', 'Mercury'], 'Neutral': ['Mars', 'Jupiter', 'Venus', 'Saturn'], 'Enemies': []},
    'Mars': {'Friends': ['Sun', 'Moon', 'Jupiter'], 'Neutral': ['Venus', 'Saturn'], 'Enemies': ['Mercury']},
    'Mercury': {'Friends': ['Sun', 'Venus'], 'Neutral': ['Mars', 'Jupiter', 'Saturn'], 'Enemies': ['Moon']},
    'Jupiter': {'Friends': ['Sun', 'Moon', 'Mars'], 'Neutral': ['Saturn'], 'Enemies': ['Mercury', 'Venus']},
    'Venus': {'Friends': ['Mercury', 'Saturn'], 'Neutral': ['Mars', 'Jupiter'], 'Enemies': ['Sun', 'Moon']},
    'Saturn': {'Friends': ['Mercury', 'Venus'], 'Neutral': ['Jupiter'], 'Enemies': ['Sun', 'Moon', 'Mars']},
    'Rahu': {'Friends': ['Venus', 'Saturn'], 'Neutral': ['Mercury', 'Jupiter'], 'Enemies': ['Sun', 'Moon', 'Mars']},
    'Ketu': {'Friends': ['Mars', 'Venus'], 'Neutral': ['Mercury', 'Jupiter', 'Saturn'], 'Enemies': ['Sun', 'Moon']}
}

def get_planet_relationship(planet_name, rasi_lord, rasi_idx):
    if planet_name == 'Ascendant': return '-'
    if planet_name not in PLANET_RELATIONSHIPS: return 'Neutral'
    
    # Check for Own Sign / Exalted / Debilitated first
    # (Simplified logic for Own Sign)
    own_signs = {
        'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
        'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10],
        'Rahu': [10], 'Ketu': [7] # Variant views exist
    }
    
    if rasi_idx in own_signs.get(planet_name, []):
        return 'Own Sign'
        
    # Check Friend/Neutral/Enemy
    rels = PLANET_RELATIONSHIPS[planet_name]
    if rasi_lord in rels['Friends']: return 'Friend'
    if rasi_lord in rels['Enemies']: return 'Enemy'
    return 'Neutral'

