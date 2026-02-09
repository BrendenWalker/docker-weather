from flask import Flask, render_template
import requests
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv  # type: ignore

app = Flask(__name__)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y/%m/%d %H:%M:%S",
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _parse_locations() -> List[Dict[str, str]]:
    """
    Parse LOCATIONS from environment.

    Format examples:
        LOCATIONS=Home:47.0,10.0;Office:47.1,10.2
        LOCATIONS=47.0,10.0;47.1,10.2  (names will be Location 1, Location 2)
    """
    raw = os.getenv("LOCATIONS")

    if not raw:
        # Fallback to single-location env vars
        lat = os.getenv("LATITUDE")
        lon = os.getenv("LONGITUDE")
        name = os.getenv("LOCATION_NAME", "Your Location")

        if not lat or not lon:
            logger.error("LATITUDE or LONGITUDE not configured")
            return []

        return [
            {
                "id": "location-1",
                "name": name,
                "lat": lat,
                "lon": lon,
            }
        ]

    locations: List[Dict[str, str]] = []

    for idx, part in enumerate(raw.split(";"), start=1):
        part = part.strip()
        if not part:
            continue

        if ":" in part:
            name_part, coords_part = part.split(":", 1)
            name = name_part.strip() or f"Location {idx}"
        else:
            name = f"Location {idx}"
            coords_part = part

        try:
            lat_str, lon_str = [c.strip() for c in coords+part.split(",", 1)]
        except ValueError:
            logger.error("Invalid location format in LOCATIONS: %s", part)
            continue

        if not lat_str or not lon_str:
            logger.error("Missing latitude or longitude in LOCATIONS: %s", part)
            continue

        locations.append(
            {
                "id": f"location-{idx}",
                "name": name,
                "lat": lat_str,
                "lon": lon_str,
            }
        )

    if not locations:
        logger.error("No valid locations parsed from LOCATIONS env")

    return locations


def _get_refresh_interval() -> int:
    """Refresh interval in seconds for each location cache."""
    try:
        return int(os.getenv("REFRESH_INTERVAL_SECONDS", "600"))
    except ValueError:
        logger.warning("Invalid REFRESH_INTERVAL_SECONDS, falling back to 600")
        return 600


# ---------------------------------------------------------------------------
# Weather API + caching
# ---------------------------------------------------------------------------

_location_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}


def _get_weather_data_for_coords(lat: str, lon: str) -> Dict[str, Any]:
    api_key = os.getenv("API_KEY")

    if not api_key:
        logger.error("API_KEY not configured")
        return {}

    try:
        units = os.getenv("UNITS", "metric")
        # Include daily data so we can build up to a 10-day forecast
        url = (
            "https://api.openweathermap.org/data/3.0/onecall"
            f"?lat={lat}&lon={lon}&exclude=minutely,alerts"
            f"&units={units}&appid={api_key}"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        logger.error("API request timed out for coordinates %s,%s", lat, lon)
        return {}

    except requests.exceptions.RequestException as e:
        logger.error("API error for coordinates %s,%s: %s", lat, lon, str(e))
        return {}


def get_weather_for_location(lat: str, lon: str) -> Dict[str, Any]:
    """
    Get weather data for a specific set of coordinates with simple caching.

    Each location is refreshed at most once per REFRESH_INTERVAL_SECONDS.
    """
    cache_key = (lat, lon)
    refresh_interval = _get_refresh_interval()

    cached = _location_cache.get(cache_key)
    now = datetime.utcnow()

    if cached:
        last_updated = cached.get("last_updated")
        if isinstance(last_updated, datetime):
            if now - last_updated < timedelta(seconds=refresh_interval):
                return cached.get("raw", {})

    raw = _get_weather_data_for_coords(lat, lon)
    _location_cache[cache_key] = {"raw": raw, "last_updated": now}
    return raw

def safe_extract_pop(hour_data: Dict[str, Any]) -> int:
    try:
        pop = hour_data.get('pop')
        
        if callable(pop):
            logger.warning("Received pop method instead of value")
            pop = 0

        else:
            pop = float(pop or 0)
        
        return min(100, max(0, int(pop * 100)))
    
    except Exception as e:
        logger.error(f"Error processing pop value: {str(e)}")
        return 0

def process_weather_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize weather data into a structure the templates can easily use.

    - current: current conditions
    - hourly: up to 36 hours
    - daily: up to 10 days
    """
    if not data:
        return {"current": {}, "hourly": [], "daily": []}

    current = data.get("current", {})
    hourly = data.get("hourly", [])[:36]
    daily = data.get("daily", [])[:10]

    processed: Dict[str, Any] = {
        "current": {
            "temp": current.get("temp", "N/A"),
            "feels_like": current.get("feels_like", "N/A"),
            "humidity": current.get("humidity", "N/A"),
            "pressure": current.get("pressure", "N/A"),
            "uvi": current.get("uvi", "N/A"),
            "wind_speed": current.get("wind_speed", "N/A"),
            "weather": current.get("weather", [{}])[0].get("main", "N/A"),
            "icon": current.get("weather", [{}])[0].get("icon", ""),
            "time": datetime.fromtimestamp(current.get("dt", 0)).strftime(
                "%H:%M %d.%m.%Y"
            ),
        },
        "hourly": [],
        "daily": [],
    }

    for hour in hourly:
        hour_copy = {k: v for k, v in hour.items() if not callable(v)}
        processed_hour = {
            "time": datetime.fromtimestamp(hour_copy.get("dt", 0)).strftime("%H:%M"),
            "temp": hour_copy.get("temp", "N/A"),
            "humidity": hour_copy.get("humidity", "N/A"),
            "wind_speed": hour_copy.get("wind_speed", "N/A"),
            "weather": hour_copy.get("weather", [{}])[0].get("main", "N/A"),
            "icon": hour_copy.get("weather", [{}])[0].get("icon", ""),
            "pop": safe_extract_pop(hour_copy),
        }
        processed["hourly"].append(processed_hour)

    for day in daily:
        day_copy = {k: v for k, v in day.items() if not callable(v)}
        temps = day_copy.get("temp", {}) or {}
        processed_day = {
            "date": datetime.fromtimestamp(day_copy.get("dt", 0)).strftime("%a %d.%m"),
            "temp_min": temps.get("min", "N/A"),
            "temp_max": temps.get("max", "N/A"),
            "weather": day_copy.get("weather", [{}])[0].get("main", "N/A"),
            "icon": day_copy.get("weather", [{}])[0].get("icon", ""),
            "pop": safe_extract_pop(day_copy),
        }
        processed["daily"].append(processed_day)

    return processed


@app.route("/")
def index():
    locations_config = _parse_locations()
    webcam_id = os.getenv("WEBCAM_ID", None)
    iframe_url = os.getenv("RADAR_IFRAME")

    locations_weather: List[Dict[str, Any]] = []

    for loc in locations_config:
        raw_data = get_weather_for_location(loc["lat"], loc["lon"])
        weather_data = process_weather_data(raw_data)
        if weather_data.get("hourly"):
            logger.info(
                "Sample pop values for %s: %s",
                loc["name"],
                [hour["pop"] for hour in weather_data["hourly"][:3]],
            )

        locations_weather.append(
            {
                "id": loc["id"],
                "name": loc["name"],
                "weather": weather_data,
            }
        )

    is_multi_location = len(locations_weather) > 1

    return render_template(
        "index.html",
        locations=locations_weather,
        is_multi_location=is_multi_location,
        webcam_id=webcam_id,
        iframe_url=iframe_url,
    )

@app.route("/impressum")
def impressum():
    return render_template("impressum.html")

@app.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)