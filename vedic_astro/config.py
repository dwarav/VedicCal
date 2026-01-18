import os
import swisseph as swe

# ================= CONFIG =================
# Adjust path to look for 'ephe' in the project root
SERVER_EPHE_PATH = '/home/u285716465/domains/dwara.org/public_html/vedic/ephe'
if os.path.exists(SERVER_EPHE_PATH):
    EPHEMERIS_PATH = SERVER_EPHE_PATH
else:
    # Assuming this file is in vedic_astro/config.py, so root is ../
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    EPHEMERIS_PATH = os.path.join(BASE_DIR, 'ephe')

SIDEREAL_MODE = swe.SIDM_LAHIRI
