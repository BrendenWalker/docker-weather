from flask import Flask, render_template
import requests
import os
from datetime import datetime
import logging
from typing import Dict, Any

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def get_weather_data() -> Dict[str, Any]:
    """Fetch weather data from OpenWeatherMap API"""
    try:
        api_key = os.getenv('API_KEY')
        lat = os.getenv('LATITUDE')
        lon = os.getenv('LONGITUDE')
        units = os.getenv('UNITS', 'metric')
        
        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,daily,alerts&units={units}&appid={api_key}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"API Error: {str(e)}")
        return {}

def safe_extract_pop(hour_data: Dict[str, Any]) -> int:
    """Completely safe precipitation probability extraction"""
    try:
        # First check if we have a direct pop value
        pop = hour_data.get('pop')
        
        # If we got the method instead of value
        if callable(pop):
            logging.warning("Received pop method instead of value")
            pop = 0
        else:
            pop = float(pop or 0)
        
        # Convert to percentage (0-100)
        return min(100, max(0, int(pop * 100)))
    except Exception as e:
        logging.error(f"Error processing pop value: {str(e)}")
        return 0

def process_weather_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process and sanitize all weather data"""
    if not data:
        return {'current': {}, 'hourly': []}
    
    current = data.get('current', {})
    hourly = data.get('hourly', [])[:36]
    
    # Process current weather
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
    
    # Process hourly forecast with guaranteed safe pop values
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
    
    # Debug output
    if weather_data['hourly']:
        logging.info(f"Sample pop values: {[hour['pop'] for hour in weather_data['hourly'][:3]]}")
    
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