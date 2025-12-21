# 🌤️ Weather Dashboard

A modern, responsive weather dashboard built with Flask and Docker. Features real-time weather data, 36-hour forecasts, live radar, and webcam integration.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.2-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features
- **Real-time Weather Data** - Current temperature, humidity, wind speed, UV index
- **36-Hour Forecast** - Detailed hourly predictions
- **Modern UI** - Dark theme with glassmorphism effects
- **Fully Responsive** - Works on desktop, tablet, and mobile
- **Live Weather Radar** - Real-time precipitation tracking
- **Webcam Integration** - Live city view
- **Docker Support** - Easy deployment via Docker Compose

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenWeatherMap API Key ([Get one here](https://openweathermap.org/api))

### Using Docker Compose (Recommended)

Create a `docker-compose.yml`:
```yaml
services:
  watchless:
    image: fish906/weather-dashboard:latest
    container_name: weather-dashboard
    ports:
      - "5000:5000"
    environment:
      - API_KEY=<YOUR_API_KEY>
      - LATITUDE=<YOUR_LAT>
      - LONGITUDE=<YOUR_LON>
      - UNITS=metric # options are 'metric' and 'imperial'
      - LOCATION_NAME=<YOUR_CITY_NAME # Replace with your city name to have it displayed on the Dashboard
    restart: unless-stopped
```

Start the Dashboard:
```bash
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_KEY` | OpenWeatherMap API key | `abc123def456...` |
| `LATITUDE` | Location latitude | `47.000` |
| `LONGITUDE` | Location longitude | `10.000` |
| `UNITS` | Temperature units | `metric` or `imperial` |
| `LOCATION_NAME` | Display name | `City` |

## 🎨 Customization

### Change Location
Update the `LATITUDE`, `LONGITUDE`, and `LOCATION_NAME` in your `.env` file.

### Modify Webcam
Edit the webcam ID in `templates/index.html`:
```html
data-id="YOUR_WEBCAM_ID"
```

Will be possible to edit webcam ID via env.

### Customize Radar Location
Update the coordinates in the radar iframe URL in `templates/index.html`.

Will be possible to edit via env.

## Licence

This project is licensed under the MIT License.

## Acknowledgments

- [OpenWeatherMap API](https://openweathermap.org/) - Weather data
- [RainViewer](https://www.rainviewer.com/) - Live radar
- [Windy Webcams](https://www.windy.com/webcams) - Webcam integration
- [Font Awesome](https://fontawesome.com/) - Icons