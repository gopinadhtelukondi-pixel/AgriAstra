"""SQLite persistence with authenticated-user ownership on every record."""
import json
import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

DB = Path(__file__).parent / "data" / "agri_astra.db"
DB.parent.mkdir(parents=True, exist_ok=True)
LEGACY_USER_ID = "legacy"


def _now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def _ensure_column(c, table, name, declaration):
    columns = {row[1] for row in c.execute(f"PRAGMA table_info({table})")}
    if name not in columns:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")


def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS app_users(
          user_id TEXT PRIMARY KEY, email TEXT NOT NULL, display_name TEXT NOT NULL,
          created_at TEXT NOT NULL, last_seen_at TEXT NOT NULL,
          password_salt TEXT, password_hash TEXT);
        CREATE TABLE IF NOT EXISTS farmer_profiles(
          farmer_id INTEGER PRIMARY KEY,location TEXT NOT NULL,latitude REAL,longitude REAL,crop TEXT NOT NULL,
          crop_variety TEXT,sowing_date TEXT,transplanting_date TEXT,growth_stage TEXT,soil_type TEXT,
          drainage TEXT,irrigation TEXT,language TEXT,created_at TEXT NOT NULL,user_id TEXT NOT NULL DEFAULT 'legacy');
        CREATE TABLE IF NOT EXISTS risk_assessments(
          assessment_id INTEGER PRIMARY KEY,farmer_id INTEGER NOT NULL REFERENCES farmer_profiles(farmer_id),
          indicators TEXT,factors TEXT,explanation TEXT,data_quality TEXT,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS weather_snapshots(
          weather_id INTEGER PRIMARY KEY,farmer_id INTEGER NOT NULL REFERENCES farmer_profiles(farmer_id),
          source TEXT,forecast_date TEXT,rainfall_mm REAL,min_temp REAL,max_temp REAL,fetched_at TEXT);
        CREATE TABLE IF NOT EXISTS simulation_runs(
          simulation_id INTEGER PRIMARY KEY,farmer_id INTEGER REFERENCES farmer_profiles(farmer_id),
          crop TEXT,rainfall_mm REAL,temperature_c REAL,original_assessment TEXT,simulated_assessment TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS advisories(
          advisory_id INTEGER PRIMARY KEY,assessment_id INTEGER REFERENCES risk_assessments(assessment_id),
          farmer_id INTEGER REFERENCES farmer_profiles(farmer_id),question TEXT,language TEXT,response TEXT,sources TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS saved_crop_profiles(
          profile_id INTEGER PRIMARY KEY,profile_name TEXT NOT NULL,profile_json TEXT NOT NULL,created_at TEXT NOT NULL,
          user_id TEXT NOT NULL DEFAULT 'legacy');
        """)
        # Preserve existing installations: older SQLite files predate ownership.
        _ensure_column(c, "farmer_profiles", "user_id", "TEXT NOT NULL DEFAULT 'legacy'")
        _ensure_column(c, "saved_crop_profiles", "user_id", "TEXT NOT NULL DEFAULT 'legacy'")
        _ensure_column(c, "app_users", "password_salt", "TEXT")
        _ensure_column(c, "app_users", "password_hash", "TEXT")
        c.execute("CREATE INDEX IF NOT EXISTS idx_farmer_user ON farmer_profiles(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_saved_profiles_user ON saved_crop_profiles(user_id)")
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_local_user_email ON app_users(email) WHERE user_id LIKE 'local:%'")


def register_user(user_id, email, display_name):
    with connect() as c:
        c.execute("""INSERT INTO app_users(user_id,email,display_name,created_at,last_seen_at) VALUES(?,?,?,?,?)
          ON CONFLICT(user_id) DO UPDATE SET email=excluded.email,display_name=excluded.display_name,last_seen_at=excluded.last_seen_at""",
          (user_id, email, display_name or email, _now(), _now()))


_PASSWORD_ITERATIONS = 310_000
_DUMMY_SALT = "agriaastra-invalid-user-salt"
_DUMMY_HASH = hashlib.pbkdf2_hmac("sha256", b"invalid", _DUMMY_SALT.encode(), _PASSWORD_ITERATIONS).hex()


def create_local_user(email, password, display_name):
    """Create a local MVP account; only salted PBKDF2 hashes are persisted."""
    email = str(email).strip().lower()
    if len(email) > 254 or "@" not in email or email.startswith("@") or email.endswith("@"):
        return None, "Enter a valid email address."
    if len(password) < 12:
        return None, "Use a password with at least 12 characters."
    salt = secrets.token_bytes(16).hex()
    password_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PASSWORD_ITERATIONS).hex()
    user_id = f"local:{uuid4()}"
    try:
        with connect() as c:
            c.execute("INSERT INTO app_users(user_id,email,display_name,created_at,last_seen_at,password_salt,password_hash) VALUES(?,?,?,?,?,?,?)",
                      (user_id, email, display_name.strip() or email, _now(), _now(), salt, password_hash))
    except sqlite3.IntegrityError:
        return None, "An account already exists for this email. Sign in instead."
    return {"user_id": user_id, "email": email, "display_name": display_name.strip() or email}, None


def authenticate_local_user(email, password):
    email = str(email).strip().lower()
    with connect() as c:
        row = c.execute("SELECT user_id,email,display_name,password_salt,password_hash FROM app_users WHERE email=? AND user_id LIKE 'local:%'", (email,)).fetchone()
    salt = bytes.fromhex(row["password_salt"]) if row and row["password_salt"] else _DUMMY_SALT.encode()
    stored = row["password_hash"] if row and row["password_hash"] else _DUMMY_HASH
    candidate = hashlib.pbkdf2_hmac("sha256", str(password).encode(), salt, _PASSWORD_ITERATIONS).hex()
    if not row or not hmac.compare_digest(candidate, stored):
        return None
    with connect() as c:
        c.execute("UPDATE app_users SET last_seen_at=? WHERE user_id=?", (_now(), row["user_id"]))
    return {"user_id": row["user_id"], "email": row["email"], "display_name": row["display_name"]}


def save_crop_profile(user_id, name, profile):
    with connect() as c:
        c.execute("INSERT INTO saved_crop_profiles(user_id,profile_name,profile_json,created_at) VALUES(?,?,?,?)",
                  (user_id, name, json.dumps(profile, default=str), _now()))


def saved_crop_profiles(user_id):
    with connect() as c:
        rows = c.execute("SELECT profile_id,profile_name,profile_json FROM saved_crop_profiles WHERE user_id=? ORDER BY profile_id DESC", (user_id,)).fetchall()
    return [dict(row) for row in rows]


def get_crop_profile(user_id, profile_id):
    with connect() as c:
        row = c.execute("SELECT profile_json FROM saved_crop_profiles WHERE user_id=? AND profile_id=?", (user_id, profile_id)).fetchone()
    if not row:
        return None
    result = json.loads(row[0])
    for key in ("sowing", "transplant"):
        if result.get(key):
            try:
                result[key] = date.fromisoformat(result[key])
            except (TypeError, ValueError):
                pass
    return result


def _profile(c, user_id, loc, p):
    cur = c.execute("""INSERT INTO farmer_profiles(user_id,location,latitude,longitude,crop,crop_variety,sowing_date,transplanting_date,growth_stage,soil_type,drainage,irrigation,language,created_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (user_id, loc["label"], loc["latitude"], loc["longitude"], p.get("crop"), p.get("variety", ""),
       str(p.get("sowing", "")), str(p.get("transplant", "")), p.get("stage", ""), p.get("soil", ""),
       p.get("drainage", ""), p.get("irrigation", ""), p.get("language", "English"), _now()))
    return cur.lastrowid


def save_assessment(user_id, loc, p, w, a):
    if not w or not a:
        return
    with connect() as c:
        fid = _profile(c, user_id, loc, p)
        factors = {"forecast_rain_mm": a.get("forecast_rain"), "forecast_mean_temp_c": a.get("forecast_temp"),
                   "rainfall_comparison": a.get("rain_text"), "temperature_comparison": a.get("temp_text")}
        c.execute("INSERT INTO risk_assessments(farmer_id,indicators,factors,explanation,data_quality,created_at) VALUES(?,?,?,?,?,?)",
                  (fid, json.dumps(a), json.dumps(factors), "Transparent climate exposure indicators; no validated crop risk score.",
                   json.dumps({"forecast_stale": w.get("stale", False), "historical_period": a.get("baseline_text"), "uncertainty": a.get("caveat")}), _now()))
        d = w.get("daily", {})
        times = d.get("time", [])
        for i, day in enumerate(times):
            val = lambda key: d.get(key, [None] * len(times))[i]
            c.execute("INSERT INTO weather_snapshots(farmer_id,source,forecast_date,rainfall_mm,min_temp,max_temp,fetched_at) VALUES(?,?,?,?,?,?,?)",
                      (fid, w.get("source", "Open-Meteo"), day, val("precipitation_sum"), val("temperature_2m_min"), val("temperature_2m_max"), w.get("fetched_at")))


def save_simulation(user_id, loc, p, base_r, base_t, rain, temp, scenario=None):
    with connect() as c:
        fid = _profile(c, user_id, loc, p)
        original = {"rainfall_mm": base_r, "temperature_c": base_t}
        simulated = {"rainfall_mm": rain, "temperature_c": temp, "hypothetical": True}
        if scenario:
            original["baseline_comparisons"] = {"rainfall": scenario.get("rainfall_baseline_comparison", {}).get("forecast"), "temperature": scenario.get("temperature_baseline_difference_c", {}).get("forecast")}
            simulated["baseline_comparisons"] = {"rainfall": scenario.get("rainfall_baseline_comparison", {}).get("hypothetical"), "temperature": scenario.get("temperature_baseline_difference_c", {}).get("hypothetical")}
        c.execute("INSERT INTO simulation_runs(farmer_id,crop,rainfall_mm,temperature_c,original_assessment,simulated_assessment,created_at) VALUES(?,?,?,?,?,?,?)",
                  (fid, p.get("crop"), rain, temp, json.dumps(original), json.dumps(simulated), _now()))


def save_advisory(user_id, loc, p, question, response, sources):
    with connect() as c:
        row = c.execute("SELECT farmer_id FROM farmer_profiles WHERE user_id=? AND location=? AND crop=? ORDER BY farmer_id DESC LIMIT 1",
                         (user_id, loc["label"], p.get("crop"))).fetchone()
        fid = row[0] if row else _profile(c, user_id, loc, p)
        latest = c.execute("SELECT r.assessment_id FROM risk_assessments r JOIN farmer_profiles p ON p.farmer_id=r.farmer_id WHERE r.farmer_id=? AND p.user_id=? ORDER BY r.assessment_id DESC LIMIT 1", (fid, user_id)).fetchone()
        c.execute("INSERT INTO advisories(assessment_id,farmer_id,question,language,response,sources,created_at) VALUES(?,?,?,?,?,?,?)",
                  (latest[0] if latest else None, fid, question, p.get("language", "English"), response, json.dumps(sources), _now()))


def history_frame(user_id):
    with connect() as c:
        assessments = pd.read_sql_query("""SELECT r.created_at AS timestamp,'Assessment' AS type,p.location,p.crop,p.growth_stage,
          json_extract(r.indicators,'$.forecast_rain') AS forecast_rain_mm,json_extract(r.indicators,'$.forecast_temp') AS mean_temp_c,
          json_extract(r.indicators,'$.rain_text') AS rainfall_comparison,json_extract(r.indicators,'$.temp_text') AS temperature_comparison
          FROM risk_assessments r JOIN farmer_profiles p ON p.farmer_id=r.farmer_id WHERE p.user_id=? ORDER BY r.assessment_id DESC""", c, params=(user_id,))
        simulations = pd.read_sql_query("""SELECT s.created_at AS timestamp,'Simulation (hypothetical)' AS type,p.location,s.crop AS crop,p.growth_stage,
          s.rainfall_mm AS forecast_rain_mm,s.temperature_c AS mean_temp_c,json_extract(s.simulated_assessment,'$.rainfall_mm') AS rainfall_comparison,
          json_extract(s.simulated_assessment,'$.temperature_c') AS temperature_comparison FROM simulation_runs s JOIN farmer_profiles p ON p.farmer_id=s.farmer_id
          WHERE p.user_id=? ORDER BY s.simulation_id DESC""", c, params=(user_id,))
        advisories = pd.read_sql_query("""SELECT a.created_at AS timestamp,'AI advisory' AS type,p.location,p.crop,p.growth_stage,a.question,a.response,a.sources
          FROM advisories a JOIN farmer_profiles p ON p.farmer_id=a.farmer_id WHERE p.user_id=? ORDER BY a.advisory_id DESC""", c, params=(user_id,))
    frames = [x for x in (assessments, simulations, advisories) if not x.empty]
    return pd.concat(frames, ignore_index=True, sort=False).sort_values("timestamp", ascending=False) if frames else pd.DataFrame()
