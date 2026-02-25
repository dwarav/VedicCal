MONTHS = ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada", "Ashwina", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna"]

TITHIS = [
    "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi", "Shukla Panchami", 
    "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami", "Shukla Navami", "Shukla Dashami", 
    "Shukla Ekadashi", "Shukla Dwadashi", "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima", 
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi", "Krishna Panchami", 
    "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami", "Krishna Navami", "Krishna Dashami", 
    "Krishna Ekadashi", "Krishna Dwadashi", "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", 
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", 
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", 
    "Uttara Bhadrapada", "Revati"
]

YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma", "Dhriti", "Shula", 
    "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", 
    "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"
]

KARANAS = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garija", "Vanija", "Vishti", 
    "Shakuni", "Chatushpada", "Naga", "Kimstughna"
]

RASHIS = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrishchika", "Dhanu", 
    "Makara", "Kumbha", "Meena"
]

PADA_NAMES = [f"{n} Pada {i+1}" for n in NAKSHATRAS for i in range(4)]

# --- ASTROLOGICAL MAPPINGS ---
CHALDEAN_MAP = {
    'A':1, 'I':1, 'J':1, 'Q':1, 'Y':1, 
    'B':2, 'K':2, 'R':2, 
    'C':3, 'G':3, 'L':3, 'S':3, 
    'D':4, 'M':4, 'T':4, 
    'E':5, 'H':5, 'N':5, 'X':5, 
    'U':6, 'V':6, 'W':6, 
    'O':7, 'Z':7, 
    'F':8, 'P':8
}

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

# --- SAMVATSARA NAMES ---
SAMVATSARA_NAMES = ["Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati", "Angirasa", "Shrimukha", "Bhava", "Yuva", "Dhatri", "Ishvara", "Bahudhanya", "Pramathi", "Vikrama", "Vrishapraja", "Chitrabhanu", "Subhanu", "Tarana", "Parthiva", "Vyaya", "Sarvajit", "Sarvadhari", "Virodhi", "Vikriti", "Khara", "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukha", "Hevilambi", "Vilambi", "Vikari", "Sharvari", "Plava", "Shubhakrit", "Shobhakrit", "Krodhi", "Vishvavasu", "Parabhava", "Plavanga", "Kilaka", "Saumya", "Sadharana", "Virodhikrit", "Paridhavi", "Pramadicha", "Ananda", "Rakshasa", "Nala", "Pingala", "Kalayukti", "Siddharthi", "Raudra", "Durmati", "Dundubhi", "Rudhirodgari", "Raktakshi", "Krodhana", "Akshaya"]

VARJYAM_STARTS = [50, 24, 30, 40, 14, 21, 30, 20, 32, 30, 20, 18, 21, 20, 14, 14, 10, 14, 56, 24, 20, 10, 10, 18, 16, 24, 30]
AMRIT_STARTS = [42, 48, 54, 52, 38, 35, 54, 44, 56, 54, 44, 48, 42, 46, 34, 32, 38, 38, 40, 48, 52, 38, 38, 42, 36, 48, 56]

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
