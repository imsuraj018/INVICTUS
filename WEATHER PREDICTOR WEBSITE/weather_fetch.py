from meteostat import Daily, Point
from datetime import datetime, timedelta
import pandas as pd
import requests
import numpy as np  

def get_coordinates(location_name):
    """
    Fetch latitude, longitude, and elevation using OpenCage API.
    """
    try:
        api_key = "c55228db31d8491b8b2a9a52b7f8299d"  # Replace with a valid OpenCage API key
        url = f"https://api.opencagedata.com/geocode/v1/json?q={location_name}&key={api_key}"

        response = requests.get(url)
        if response.status_code != 200:
            return None, None, None

        data = response.json()
        if 'results' in data and len(data['results']) > 0:
            lat = data['results'][0]['geometry']['lat']
            lon = data['results'][0]['geometry']['lng']
            elevation = 0  
            return lat, lon, elevation
        return None, None, None

    except Exception:
        return None, None, None

def calculate_absolute_humidity(temp):
    """
    Calculate absolute humidity (g/m³) using temperature (°C).
    """
    try:
        temp = np.array(temp)
        svp = 6.112 * np.exp((17.67 * temp) / (temp + 243.5))  # hPa
        rh = 85.0  # Default RH = 85%
        ah = (svp * rh * 2.16679) / (temp + 273.15)
        return ah, svp
    except Exception:
        return np.nan, np.nan  

def fetch_weather_data(location_name):
    """
    Fetch temperature and calculate absolute & relative humidity.
    """
    try:
        latitude, longitude, elevation = get_coordinates(location_name)
        if latitude is None:
            return pd.DataFrame()

        location = Point(latitude, longitude, elevation)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        weather_data = Daily(location, start_date, end_date).fetch()

        if weather_data.empty:
            return pd.DataFrame()

        temp = weather_data['tavg'] if 'tavg' in weather_data.columns else (weather_data['tmin'] + weather_data['tmax']) / 2
        absolute_humidity, svp = calculate_absolute_humidity(temp)
        relative_humidity = (absolute_humidity * (temp + 273.15)) / (2.16679 * svp)

        rainy_condition = ["Yes" if rh > 80 and t < 30 else "No" for rh, t in zip(relative_humidity, temp)]
        foggy_condition = ["Yes" if rh > 90 and t < 20 else "No" for rh, t in zip(relative_humidity, temp)]

        return pd.DataFrame({
            'Date': weather_data.index.date.astype(str),  # Convert to string to remove time
            'Temperature (°C)': temp,
            'Relative Humidity (%)': relative_humidity,
            'Rainy Condition': rainy_condition,
            'Foggy Condition': foggy_condition,
            'Location': location_name
        })

    except Exception:
        return pd.DataFrame()

def predict_future_weather(past_weather, days_ahead=7):
    """
    Predict the next `days_ahead` days' weather using a simple trend model.
    """
    if past_weather.empty:
        return pd.DataFrame()

    last_temp = past_weather['Temperature (°C)'].iloc[-1]
    last_rh = past_weather['Relative Humidity (%)'].iloc[-1]

    future_dates = [(datetime.now() + timedelta(days=i)).date().strftime('%Y-%m-%d') for i in range(1, days_ahead + 1)]
    future_temps = [last_temp + (i * 0.08) for i in range(1, days_ahead + 1)]
    future_humidities = [last_rh for _ in range(1, days_ahead + 1)]

    rainy_condition = ["Yes" if rh > 80 and temp < 30 else "No" for rh, temp in zip(future_humidities, future_temps)]
    foggy_condition = ["Yes" if rh > 90 and temp < 20 else "No" for rh, temp in zip(future_humidities, future_temps)]

    return pd.DataFrame({
        'Date': future_dates,  # Already formatted as YYYY-MM-DD
        'Temperature (°C)': future_temps,
        'Relative Humidity (%)': future_humidities,
        'Rainy Condition': rainy_condition,
        'Foggy Condition': foggy_condition
    })
