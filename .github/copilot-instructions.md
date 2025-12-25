## Copilot / AI assistant instructions for VedicCal

Summary
- This repository is a single Python CLI utility that computes a complete Vedic
  panchanga and muhurtas using the Swiss Ephemeris. Primary entry: `vedic_calendar_complete.py`.

Quick setup
- Install runtime deps: `pip install swisseph requests` (the code imports `swisseph` and `requests`).
- Run locally: `python vedic_calendar_complete.py` — it prints results and writes `complete_panchanga.json`.

Big picture (what to know)
- Single-module app: all calculation logic lives in `vedic_calendar_complete.py`.
  - It detects location via IP (`detect_user_location()`) with fallbacks to a Delhi default.
  - Uses Swiss Ephemeris in sidereal (Lahiri) mode for astronomical data (`swe.set_sid_mode(swe.SIDM_LAHIRI)`).
  - Core output shape is the `complete_panchanga` dict (saved as `complete_panchanga.json`).
- Major concerns: numeric precision, timezone handling, and external network calls for location.

Key files and patterns
- [vedic_calendar_complete.py](vedic_calendar_complete.py)
  - Helper functions return mixed types: both human-readable strings (e.g. `start`) and `datetime` objects (e.g. `start_time`).
  - Many transition-time calculations use binary search over Julian Day (1 minute tolerance).
  - Muhurta functions take/expect `sunrise`/`sunset` datetimes and a `vaara` (1..7) value.
- [complete_panchanga.json](complete_panchanga.json)
  - The script overwrites this file when run; JSON serialization uses `default=str` for datetimes.

Project-specific conventions
- Use sidereal Lahiri mode via Swiss Ephemeris everywhere — do not change to tropical without explicit intent.
- `vaara['number']` is 1..7 (Sunday=1). Many functions index into weekday tables and expect 1-based input.
- Preserve both `*_str`/`start` keys and `*_time`/`start_time` keys — tests/consumers may expect either.

Integration points & external dependencies
- Network: `detect_user_location()` calls `http://ip-api.com/json/` and `https://ipapi.co/json/`.
  - Offline/dev: expect fallback to hard-coded Delhi coordinates.
- Swiss Ephemeris: all planetary and rise/set computations use `swisseph` (`swe`) APIs. Confirm platform-native library availability when running on CI/containers.

Developer workflows (practical commands)
- Run once and inspect output:
  ```powershell
  python vedic_calendar_complete.py
  type complete_panchanga.json
  ```
- Run for a specific date interactively (script prompts), or change the `dt` in `__main__` for non-interactive runs.

Common pitfalls and what to check in PRs
- Watch for inconsistent types (string vs datetime) when modifying functions that participate in JSON output.
- Don't change the default sidereal mode or the usage of `swe.set_topo` unless you verify sunrise/sunset changes across multiple locations.
- Network calls in `detect_user_location()` can fail silently; prefer adding a clearly testable injection point for `location` if writing tests.

Where to change behavior intentionally
- To adjust varjyam rules: `calculate_varjyam()` — it accepts an optional `k_table` mapping.
- To change Muhurta rules (durations/offsets): update the relevant functions named `calculate_*` (e.g. `calculate_durmuhurta`, `calculate_brahma_muhurta`).

What to include in PR descriptions
- State any change to astronomical modes (sidereal/tropical), units (minutes vs seconds), or the public JSON schema.
- If adding new external calls, list the domains used (e.g., `ip-api.com`) and fallbacks provided.

If anything in this guidance is unclear or missing examples you want me to add (for example, a small unit-test harness or Dockerfile to ensure `swisseph` availability), tell me which area to expand.
