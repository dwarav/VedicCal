import calendar
from datetime import datetime
import swisseph as swe
from .core import fetch_month_day_data, fetch_panchang, setup_swisseph, jd_from_dt, calc_sun_rise_set, dt_from_jd

# ---------------------------------------------------------------------------
# TELUGU / GANTALA PANCHANGAM MUHURTHA ENGINE
# All rules follow Andhra-Telangana Gantala Panchangam tradition.
# ---------------------------------------------------------------------------

# Rahu Kalam part index (1-indexed, divide day into 8 parts)
# Python weekday: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
RAHU_KEY = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}

# Inauspicious yogas — how many ghatis from start are bad
YOGA_BAD_GHATIS = {
    "Vishkambha": 3,
    "Atiganda": 6,
    "Shula": 5,
    "Ganda": 6,
    "Vyaghata": 9,
    "Vajra": 3,
    "Vyatipata": 60,   # entire yoga
    "Parigha": 30,     # first half
    "Vaidhriti": 60    # entire yoga
}

# Chaturmas: Lord Vishnu in Yoga Nidra — no marriages (Ashadha–Kartika)
CHATURMAS_MONTHS = {"Ashadha", "Shravana", "Bhadrapada", "Ashwina", "Kartika"}

# Rikta Tithis — inauspicious for marriage in Telugu tradition
RIKTA_TITHIS = {"Chaturthi", "Navami", "Chaturdashi"}

# Used for Lagna naming
RASHI_NAMES = ["Mesha", "Vrishabha", "Mithuna", "Karkataka", "Simha", "Kanya", 
               "Tula", "Vrischika", "Dhanus", "Makara", "Kumbha", "Meena"]

RASHI_TO_NAKS = {
    0: ['Ashwini', 'Bharani', 'Krittika'], 
    1: ['Krittika', 'Rohini', 'Mrigashira'], 
    2: ['Mrigashira', 'Ardra', 'Punarvasu'], 
    3: ['Punarvasu', 'Pushya', 'Ashlesha'], 
    4: ['Magha', 'Purva Phalguni', 'Uttara Phalguni'], 
    5: ['Uttara Phalguni', 'Hasta', 'Chitra'], 
    6: ['Chitra', 'Swati', 'Vishakha'], 
    7: ['Vishakha', 'Anuradha', 'Jyeshtha'], 
    8: ['Mula', 'Purva Ashadha', 'Uttara Ashadha'], 
    9: ['Uttara Ashadha', 'Shravana', 'Dhanishta'], 
    10: ['Dhanishta', 'Shatabhisha', 'Purva Bhadrapada'], 
    11: ['Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati']
}

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def get_combustion_status(jd):
    """
    Checks if Venus (Shukra) or Jupiter (Guru) is combust — Moodami.
    Orbs: Venus < 10°, Jupiter < 11° from Sun.
    """
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    try:
        sun_lon  = swe.calc_ut(jd, swe.SUN,     flags)[0][0]
        venus_lon= swe.calc_ut(jd, swe.VENUS,   flags)[0][0]
        jup_lon  = swe.calc_ut(jd, swe.JUPITER, flags)[0][0]

        def ang_diff(a1, a2):
            d = abs(a1 - a2)
            return d if d < 180 else 360 - d

        return ang_diff(sun_lon, venus_lon) < 10.0, ang_diff(sun_lon, jup_lon) < 11.0
    except Exception:
        return False, False


def get_sun_rashi_idx(jd):
    """Returns sidereal rashi index 0–11 of the Sun."""
    try:
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
        return int(swe.calc_ut(jd, swe.SUN, flags)[0][0] / 30)
    except Exception:
        return -1


def get_lagna_at_jd(jd, lat, lon):
    """Returns the sidereal Lagna (Ascendant) index 0-11 at a given time and location."""
    try:
        swe.set_topo(lon, lat, 0)
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')
        asc_trop = ascmc[0]
        ayanamsa = swe.get_ayanamsa_ut(jd)
        asc_sid = (asc_trop - ayanamsa) % 360
        return int(asc_sid / 30)
    except Exception:
        return -1


def is_chaturmas(lunar_month):
    return lunar_month in CHATURMAS_MONTHS


def is_rikta_tithi(tithi_name):
    suffix = tithi_name.split(' ')[-1]
    return suffix in RIKTA_TITHIS


def _compute_bad_windows(rule, karana_events, yoga_events, weekday, rise_jd, set_jd):
    """Collects Bhadra, bad-yoga, and Rahu Kalam windows to subtract."""
    bad = []

    # Bhadra (Vishti Karana)
    if rule.get('avoid_bhadra'):
        for ke in karana_events:
            if ke['name'] == 'Vishti' and ke.get('start') and ke.get('end'):
                bad.append((ke['start'], ke['end']))

    # Inauspicious yoga periods
    if rule.get('avoid_bad_yoga', True):
        for ye in yoga_events:
            name = ye['name']
            if name in YOGA_BAD_GHATIS and ye.get('start') and ye.get('end'):
                dur = ye['end'] - ye['start']
                bad_frac = YOGA_BAD_GHATIS[name] / 60.0
                bad.append((ye['start'], ye['start'] + dur * bad_frac))

    # Rahu Kalam
    if rule.get('avoid_rahu_kalam') and rise_jd and set_jd and rise_jd < set_jd:
        day_len = set_jd - rise_jd
        part    = day_len / 8.0
        rpart   = RAHU_KEY.get(weekday, 1)
        bad.append((rise_jd + (rpart - 1) * part, rise_jd + rpart * part))

    return bad


def _subtract_bad(clean_windows, bad_windows):
    """Subtracts bad time intervals from a list of clean windows."""
    for bs, be in bad_windows:
        new = []
        for ws, we in clean_windows:
            if be <= ws or bs >= we:
                new.append((ws, we))
            else:
                if bs > ws: new.append((ws, bs))
                if be < we: new.append((be, we))
        clean_windows = new
    return clean_windows


def compute_muhurtha_window(rule, full_data, jd_noon, loc, tz, weekday, year, month, day):
    """
    Finds the longest clean overlap of auspicious Nakshatra + auspicious Tithi
    within the Vedic day (sunrise → next sunrise), after subtracting bad periods.

    Returns (start_jd, end_jd, nak_name, tithi_name) or None.
    """
    nak_events    = full_data.get('nakshatra', [])
    tithi_events  = full_data.get('tithi', [])
    karana_events = full_data.get('karana', [])
    yoga_events   = full_data.get('yoga', [])

    rise, set_jd = calc_sun_rise_set(jd_noon,     loc['lat'], loc['lon'])
    rise_next, _ = calc_sun_rise_set(jd_noon + 1, loc['lat'], loc['lon'])

    if not rise or rise == 0.0:
        return None

    # Auspicious nak windows
    good_naks = [
        (ne['start'], ne['end'], ne['name'])
        for ne in nak_events
        if ne['name'] in rule['naks'] and ne.get('start') and ne.get('end')
    ]

    # Auspicious tithi windows
    good_tithis = [
        (te['start'], te['end'], te['name'])
        for te in tithi_events
        if te['name'].split(' ')[-1] in rule['tithis'] and te.get('start') and te.get('end')
    ]

    bad_windows = _compute_bad_windows(rule, karana_events, yoga_events, weekday, rise, set_jd)

    all_lagnas = []

    for ns, ne_jd, nak_name in good_naks:
        for ts, te_jd, tithi_name in good_tithis:
            overlap_s = max(ns, ts, rise)
            overlap_e = min(ne_jd, te_jd, rise_next)
            if overlap_s >= overlap_e:
                continue

            clean = _subtract_bad([(overlap_s, overlap_e)], bad_windows)

            for ws, we in clean:
                dur = we - ws
                # We need at least an hour to find a good Lagna
                if dur >= 1 / 24.0:
                    
                    # ── Lagna scanning (step 5 minutes) ──
                    step = 5 / 1440.0
                    curr = ws
                    lagna_start = -1
                    current_l_idx = -1
                    allowed_lagnas = rule.get('lagnas', [0,1,2,3,4,5,6,7,8,9,10,11])
                    
                    while curr <= we:
                        l_idx = get_lagna_at_jd(curr, loc['lat'], loc['lon'])
                        if l_idx != current_l_idx:
                            # Lagna transition
                            if current_l_idx in allowed_lagnas and lagna_start != -1:
                                l_dur = curr - lagna_start
                                if l_dur >= 15 / 1440.0: # At least 15 mins
                                    exact_s = lagna_start + (15 / 1440.0) if l_dur > (30 / 1440.0) else lagna_start + (l_dur / 2.0)
                                    all_lagnas.append((exact_s, lagna_start, curr, nak_name, tithi_name, RASHI_NAMES[current_l_idx]))
                            current_l_idx = l_idx
                            lagna_start = curr
                        curr += step
                    
                    # Process final remaining lagna window at end of overall block
                    if current_l_idx in allowed_lagnas and lagna_start != -1:
                        l_dur = we - lagna_start
                        if l_dur >= 15 / 1440.0:
                            exact_s = lagna_start + (15 / 1440.0) if l_dur > (30 / 1440.0) else lagna_start + (l_dur / 2.0)
                            all_lagnas.append((exact_s, lagna_start, we, nak_name, tithi_name, RASHI_NAMES[current_l_idx]))

    if not all_lagnas:
        return None

    # Sort lagnas by start time
    all_lagnas.sort(key=lambda x: x[0])
    return all_lagnas


def _fmt_jd(jd, tz, year, month, day):
    """Formats a Julian Day as a local time string."""
    d = dt_from_jd(jd, tz)
    if not d:
        return "---"
    if d.date() != datetime(year, month, day).date():
        return d.strftime('%b %d, %I:%M %p')
    return d.strftime('%I:%M %p')


def fmt_start(ws_jd, tz, year, month, day):
    """Returns only the auspicious muhurtha START time e.g. '10:24 AM'."""
    return _fmt_jd(ws_jd, tz, year, month, day)


def fmt_window(ws_jd, we_jd, tz, year, month, day):
    """Returns the full muhurtha time range e.g. '10:24 AM – 12:48 PM'."""
    return f"{_fmt_jd(ws_jd, tz, year, month, day)} – {_fmt_jd(we_jd, tz, year, month, day)}"



# ---------------------------------------------------------------------------
# TELUGU PANCHANGAM RULES
# ---------------------------------------------------------------------------
#
# Weekday index (Python): Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
#
# MARRIAGE (Vivah):
#   Nakshatras (9): Rohini, Mrigashira, Uttara Phalguni, Hasta, Swati,
#                   Anuradha, Uttara Ashadha, Uttara Bhadrapada, Revati
#   (Magha & Mula excluded — Pada 1 issues; Telugu tradition avoids both)
#   Tithis: Dwitiya, Tritiya, Panchami, Saptami, Dashami, Ekadashi, Trayodashi
#   Avoid: Tuesday only (not Saturday — Telugu tradition)
#   Shukla Paksha only
#   Avoid: Moodami (Venus/Jupiter combustion)
#   Avoid: Chaturmas (Ashadha–Kartika); Soonya Masa (Sun in Dhanu/Mithuna)
#   Avoid: Rikta Tithis (4/9/14); Rahu Kalam; Bhadra (Vishti Karana)
#
# GRIHA PRAVESH (House Warming):
#   Nakshatras (14): Rohini, Mrigashira, Punarvasu, Pushya, Uttara Phalguni,
#                    Hasta, Chitra, Swati, Anuradha, Uttara Ashadha, Shravana,
#                    Dhanishta, Uttara Bhadrapada, Revati
#   (Ashwini & Shatabhisha removed — not in Telugu Griha Pravesh)
#   Tithis: Dwitiya, Tritiya, Panchami, Saptami, Dashami, Ekadashi, Dwadashi, Trayodashi
#   Shukla Paksha only
#   Avoid: Tuesday, Saturday, Sunday
#   Avoid months: Chaitra, Ashadha, Bhadrapada, Ashwina
#   Avoid: Moodami; Rahu Kalam; Bhadra; bad Yogas
#
# NAMING CEREMONY (Namakaranam):
#   Nakshatras (16): Ashwini, Rohini, Mrigashira, Punarvasu, Pushya,
#                    Uttara Phalguni, Hasta, Chitra, Swati, Anuradha,
#                    Uttara Ashadha, Shravana, Dhanishta, Shatabhisha,
#                    Uttara Bhadrapada, Revati  (Uttara Ashadha added)
#   Tithis: Pratipada, Dwitiya, Tritiya, Panchami, Shashthi, Saptami,
#           Dashami, Ekadashi, Dwadashi, Trayodashi, Purnima
#   Avoid: Tuesday, Saturday  |  Both Pakshas allowed
#   Avoid: Rahu Kalam
#
# VEHICLE PURCHASE:
#   Nakshatras (10): Ashwini, Rohini, Punarvasu, Pushya, Hasta, Swati,
#                    Shravana, Dhanishta, Shatabhisha, Revati
#   (Chitra & Anuradha removed; Char nakshatras emphasised)
#   Tithis: Pratipada, Dwitiya, Tritiya, Panchami, Shashthi, Saptami,
#           Dashami, Ekadashi, Trayodashi, Purnima
#   Avoid: Tuesday, Saturday  |  Both Pakshas allowed
#   Avoid: Rahu Kalam

RULES = {
    "marriage": {
        "naks": [
            "Rohini", "Mrigashira", "Uttara Phalguni", "Hasta", "Swati",
            "Anuradha", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"
        ],
        "tithis": [
            "Dwitiya", "Tritiya", "Panchami", "Saptami",
            "Dashami", "Ekadashi", "Trayodashi"
        ],
        "lagnas": [1, 2, 3, 4, 5, 6, 8, 10, 11], # Sthira & Dwisvabhava preferred
        "exclude_days":    [1],        # Avoid Tuesday only (Telugu tradition)
        "check_moodami":   True,
        "shukla_only":     True,
        "avoid_bhadra":    True,
        "avoid_rahu_kalam":True,
        "avoid_bad_yoga":  True,
        "avoid_chaturmas": True,
        "avoid_soonya_masa":True,
        "avoid_rikta_tithis":True,
    },
    "gruha": {
        "naks": [
            "Rohini", "Mrigashira", "Punarvasu", "Pushya",
            "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha",
            "Uttara Ashadha", "Shravana", "Dhanishta",
            "Uttara Bhadrapada", "Revati"
        ],
        "tithis": [
            "Dwitiya", "Tritiya", "Panchami", "Saptami",
            "Dashami", "Ekadashi", "Dwadashi", "Trayodashi"
        ],
        "lagnas": [1, 2, 4, 5, 8, 10, 11], # Sthira & Dwisvabhava, exclude Vrischika
        "exclude_days":    [1, 5, 6],  # Avoid Tue, Sat, Sun
        "check_moodami":   True,
        "shukla_only":     True,       # Shukla Paksha only
        "avoid_bhadra":    True,
        "avoid_rahu_kalam":True,
        "avoid_bad_yoga":  True,
        "avoid_lunar_months": ["Chaitra", "Ashadha", "Bhadrapada", "Ashwina"],
    },
    "naming": {
        "naks": [
            "Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya",
            "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha",
            "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
            "Uttara Bhadrapada", "Revati"
        ],
        "tithis": [
            "Pratipada", "Dwitiya", "Tritiya", "Panchami", "Shashthi",
            "Saptami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Purnima"
        ],
        "lagnas": [1, 2, 4, 5, 8, 10, 11], # Same as Gruha
        "exclude_days":    [1, 5],     # Avoid Tuesday, Saturday
        "check_moodami":   False,
        "shukla_only":     False,
        "avoid_bhadra":    False,
        "avoid_rahu_kalam":True,
        "avoid_bad_yoga":  False,
    },
    "vehicle": {
        "naks": [
            "Ashwini", "Rohini", "Punarvasu", "Pushya",
            "Hasta", "Swati", "Shravana", "Dhanishta", "Shatabhisha", "Revati"
        ],
        "tithis": [
            "Pratipada", "Dwitiya", "Tritiya", "Panchami", "Shashthi",
            "Saptami", "Dashami", "Ekadashi", "Trayodashi", "Purnima"
        ],
        "lagnas": [0, 2, 3, 5, 6, 8, 9, 11], # Chara & Dwisvabhava preferred
        "exclude_days":    [1, 5],     # Avoid Tuesday, Saturday
        "check_moodami":   False,
        "shukla_only":     False,
        "avoid_bhadra":    False,
        "avoid_rahu_kalam":True,
        "avoid_bad_yoga":  False,
    }
}


# ---------------------------------------------------------------------------
# MAIN CALCULATOR
# ---------------------------------------------------------------------------

def get_monthly_muhurthas(loc, year, month):
    """
    Calculates auspicious muhurthas per Telugu Gantala Panchangam rules.

    All 4 categories now use a window-based approach so the exact
    muhurtha time window (start – end) is returned for every result.

    Steps per day:
    1. Quick filters via fetch_month_day_data (weekday, moodami, paksha, etc.)
    2. fetch_panchang for full event data
    3. compute_muhurtha_window → exact overlap of nak ∩ tithi minus bad periods
    4. Only include days with ≥ 1 hour of clean window
    """
    setup_swisseph()
    cal     = calendar.monthcalendar(year, month)
    results = {k: [] for k in RULES}

    for week in cal:
        for day in week:
            if day == 0:
                continue

            date_str = f"{year}-{month:02d}-{day:02d}"
            try:
                lite_data = fetch_month_day_data(loc, date_str)
                dt_obj    = datetime(year, month, day)
                weekday   = dt_obj.weekday()

                tz     = loc['tz']
                jd_noon = jd_from_dt(tz.localize(datetime(year, month, day, 12, 0)))

                is_venus, is_guru = get_combustion_status(jd_noon)
                moodami_active    = is_venus or is_guru

                sun_rashi  = get_sun_rashi_idx(jd_noon)
                soonya_masa = sun_rashi in (2, 8)  # Mithuna=2, Dhanu=8

                curr_nak   = lite_data['nakshatra']
                curr_tithi = lite_data['tithi']
                full_tithi = lite_data.get('full_tithi_name', '')
                is_shukla   = full_tithi.startswith('Shukla') or full_tithi == 'Purnima'
                lunar_month = lite_data.get('lunar_month', '')
                is_adika    = lite_data.get('is_adika', False)
                # For Chaturmas/avoid-month checks, strip "Adika " prefix to get base name
                base_lunar_month = lunar_month.replace('Adika ', '') if is_adika else lunar_month

                for cat, rule in RULES.items():

                    # ── Quick filters ──────────────────────────────────────
                    if weekday in rule['exclude_days']:
                        continue
                    if rule.get('check_moodami') and moodami_active:
                        continue
                    if rule.get('shukla_only') and not is_shukla:
                        continue
                    # Adika Masa is always inauspicious for marriage & Griha Pravesh
                    if is_adika and cat in ('marriage', 'gruha'):
                        continue
                    if rule.get('avoid_chaturmas') and is_chaturmas(base_lunar_month):
                        continue
                    if rule.get('avoid_soonya_masa') and soonya_masa:
                        continue
                    if rule.get('avoid_lunar_months') and base_lunar_month in rule['avoid_lunar_months']:
                        continue

                    # Quick nakshatra / tithi pre-check using sunrise values
                    nak_ok   = curr_nak in rule['naks']
                    tithi_ok = curr_tithi in rule['tithis']
                    if rule.get('avoid_rikta_tithis') and is_rikta_tithi(curr_tithi):
                        tithi_ok = False

                    # For window-based categories (Griha Pravesh), skip the
                    # sunrise pre-check and always compute the window — the nak
                    # may have just started after midnight and is valid.
                    # For others, use the pre-check as a fast gate.
                    if cat != 'gruha' and not (nak_ok and tithi_ok):
                        continue

                    # ── Compute exact window ───────────────────────────────
                    full_data = fetch_panchang(loc, date_str)
                    if not full_data:
                        continue

                    lagnas_found = compute_muhurtha_window(
                        rule, full_data, jd_noon, loc, tz,
                        weekday, year, month, day
                    )
                    if not lagnas_found:
                        continue   # No clean window or no exact Lagna → skip this day

                    # Take the nakshatra/tithi of the first valid lagna to represent the day
                    best_nak = lagnas_found[0][3]
                    best_tithi = lagnas_found[0][4]

                    # Map all lagnas for display
                    formatted_lagnas = []
                    for ex_s, l_ws, l_we, n_name, t_name, l_name in lagnas_found:
                        l_idx = RASHI_NAMES.index(l_name)
                        bad_janma_rashi_idx = (l_idx + 5) % 12
                        bad_naks = ", ".join(RASHI_TO_NAKS[bad_janma_rashi_idx])
                        
                        formatted_lagnas.append({
                            "lagna_name": l_name,
                            "muhurta_start": fmt_start(ex_s, tz, year, month, day),
                            "muhurta_window": fmt_window(l_ws, l_we, tz, year, month, day),
                            "bad_for_naks": bad_naks
                        })

                    # ── Collect display metadata ───────────────────────────
                    nak_events   = full_data.get('nakshatra', [])
                    tithi_events = full_data.get('tithi', [])

                    tithi_display   = best_tithi
                    tithi_start_fmt = ''
                    tithi_end_fmt   = ''
                    nak_end_fmt     = ''

                    for ne in nak_events:
                        if ne['name'] == best_nak:
                            nak_end_fmt = ne.get('end_fmt', '')
                            break
                    for te in tithi_events:
                        if te['name'] == best_tithi:
                            tithi_start_fmt = te.get('start_fmt', '')
                            tithi_end_fmt   = te.get('end_fmt', '')
                            break

                    warnings = []
                    if moodami_active:
                        p = []
                        if is_venus: p.append("Venus (Shukra)")
                        if is_guru:  p.append("Jupiter (Guru)")
                        warnings.append(f"Moodami Active: {', '.join(p)}")

                    results[cat].append({
                        "date":           f"{day} {calendar.month_name[month]}",
                        "day_name":       dt_obj.strftime("%A"),
                        "nakshatra":      best_nak,
                        "tithi":          tithi_display,
                        "full_date":      date_str,
                        "tithi_start":    tithi_start_fmt,
                        "tithi_end":      tithi_end_fmt,
                        "nak_end":        nak_end_fmt,
                        "lagnas":         formatted_lagnas,
                        "amrit":          full_data['timings']['amrit'],
                        "abhijit":        full_data['timings']['abhijit'],
                        "nakshatra_idx":  lite_data['nakshatra_idx'],
                        "moon_rashi_idx": lite_data['moon_rashi_idx'],
                        "warnings":       warnings,
                    })

            except Exception:
                continue

    return results


# ---------------------------------------------------------------------------
# COMPATIBILITY HELPERS (unchanged)
# ---------------------------------------------------------------------------

def get_nak_idx(loc_data, date_str, time_str):
    dt_str = f"{date_str} {time_str}"
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return (0, 0)
    tz       = loc_data['tz']
    local_dt = tz.localize(dt)
    jd       = jd_from_dt(local_dt)
    setup_swisseph()
    moon_long = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    return int(moon_long / 13.333333333), int(moon_long / 30)


def check_tarabala(birth_nak_idx, day_nak_idx):
    count = (day_nak_idx - birth_nak_idx) % 27 + 1
    rem   = count % 9 or 9
    TARA = {
        1: "Janma (Birth) - Avoid",    2: "Sampat (Wealth) - Good",
        3: "Vipat (Danger) - Avoid",   4: "Kshema (Well-being) - Good",
        5: "Pratyak (Obstacles) - Avoid", 6: "Sadhana (Achievement) - Good",
        7: "Naidhana (Death/Loss) - Avoid", 8: "Mitra (Friend) - Good",
        9: "Parama Mitra (Best Friend) - Good"
    }
    return rem in [2, 4, 6, 8, 9], TARA[rem]


def check_chandrabala(birth_rashi_idx, day_rashi_idx):
    count  = (day_rashi_idx - birth_rashi_idx) % 12 + 1
    is_good = count not in [6, 8, 12]
    msg    = f"{count}th from Moon - {'Good' if is_good else 'Bad (Avoid)'}"
    return is_good, msg


def filter_marriage_muhurthas(marriage_dates, bride_data, groom_data):
    b_nak, b_rashi = bride_data
    g_nak, g_rashi = groom_data
    personalized   = []
    for item in marriage_dates:
        day_nak   = item.get('nakshatra_idx')
        day_rashi = item.get('moon_rashi_idx')
        if day_nak is None or day_rashi is None:
            continue
        bt_good, bt_msg = check_tarabala(b_nak, day_nak)
        gt_good, gt_msg = check_tarabala(g_nak, day_nak)
        bc_good, bc_msg = check_chandrabala(b_rashi, day_rashi)
        gc_good, gc_msg = check_chandrabala(g_rashi, day_rashi)
        if bt_good and gt_good and bc_good and gc_good:
            item_copy = item.copy()
            item_copy['compatibility'] = {
                "bride_tara":    bt_msg,
                "groom_tara":   gt_msg,
                "bride_chandra": bc_msg,
                "groom_chandra": gc_msg,
            }
            personalized.append(item_copy)
    return personalized
