from flask import Flask, render_template
import requests
import os
from datetime import datetime
import logging
from typing import Dict, Any
from dotenv import load_dotenv # type: ignore

app = Flask(__name__)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    datefmt= '%Y/%m/%d %H:%M:%S',
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_weather_data() -> Dict[str, Any]:
    api_key = os.getenv('API_KEY')

    if not api_key:
        logger.error("API_KEY not configured")
        return {}
    
    lat = os.getenv('LATITUDE')
    lon = os.getenv('LONGITUDE')

    if not lat or not lon:
        logger.error("LATITUDE or LONGITUDE not configured")
        return {}
    
    try:
        units = os.getenv('UNITS', 'metric')
        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,daily,alerts&units={units}&appid={api_key}"
        response = requests.get(url, timeout=10)  # Add timeout
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return {}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API Error: {str(e)}")
        return {}

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
    if not data:
        return {'current': {}, 'hourly': []}
    
    current = data.get('current', {})
    hourly = data.get('hourly', [])[:36]
    
    processed = {
        'current': {
            'temp': current.get('temp', 'N/A'),
            'feels_like': current.get('feels_like', 'N/A'),
            'humidity': current.get('humidity', 'N/A'),
            'pressure': current.get('pressure', 'N/A'),
            'uvi': current.get('uvi', 'N/A'),
            'wind_speed': current.get('wind_speed', 'N/A'),
            'weather': current.get('weather', [{}])[0].get('main', 'N/A'),
            'icon': current.get('weather', [{}])[0].get('icon', ''),
            'time': datetime.fromtimestamp(current.get('dt', 0)).strftime('%H:%M %d/%m')
        },
        'hourly': []
    }
    
    for hour in hourly:
        hour_copy = {k: v for k, v in hour.items() if not callable(v)}
        processed_hour = {
            'time': datetime.fromtimestamp(hour_copy.get('dt', 0)).strftime('%H:%M'),
            'temp': hour_copy.get('temp', 'N/A'),
            'humidity': hour_copy.get('humidity', 'N/A'),
            'wind_speed': hour_copy.get('wind_speed', 'N/A'),
            'weather': hour_copy.get('weather', [{}])[0].get('main', 'N/A'),
            'icon': hour_copy.get('weather', [{}])[0].get('icon', ''),
            'pop': safe_extract_pop(hour_copy)  # Get the processed integer
        }
        processed['hourly'].append(processed_hour)

    return processed

@app.route('/')
def index():
    raw_data = get_weather_data()
    weather_data = process_weather_data(raw_data)
    location_name = os.getenv('LOCATION_NAME', 'Your Location')
    
    if weather_data['hourly']:
        logger.info(f"Sample pop values: {[hour['pop'] for hour in weather_data['hourly'][:3]]}")
    
    return render_template(
        'index.html', 
        weather=weather_data,
        location_name=location_name
        )

@app.route("/impressum")
def impressum():
    return render_template("impressum.html")

@app.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)