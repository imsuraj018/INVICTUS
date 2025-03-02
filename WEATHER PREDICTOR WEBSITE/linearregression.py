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
            print(f"Error: OpenCage API request failed with status code {response.status_code}.")
            return None, None, None

        data = response.json()

        if 'results' in data and len(data['results']) > 0:
            lat = data['results'][0]['geometry']['lat']
            lon = data['results'][0]['geometry']['lng']
            elevation = 0  
            return lat, lon, elevation
        else:
            print(f"Error: No results found for {location_name}.")
            return None, None, None

    except Exception as e:
        print(f"An error occurred while fetching coordinates: {e}")
        return None, None, None

def calculate_absolute_humidity(temp):
    """
    Calculate absolute humidity (g/m³) using temperature (°C).
    """
    try:
        temp = np.array(temp)

        # Estimate Saturation Vapor Pressure (SVP) using the Magnus formula
        svp = 6.112 * np.exp((17.67 * temp) / (temp + 243.5))  # hPa

        # Assume high humidity (default RH = 85%) when RH is not available
        rh = 85.0

        # Absolute Humidity (AH) formula in g/m³
        ah = (svp * rh * 2.16679) / (temp + 273.15)
        return ah, svp  # Return both AH and SVP for RH calculation
    except Exception as e:
        print(f"Error calculating absolute humidity: {e}")
        return np.nan, np.nan  

def fetch_weather_data(location_name):
    """
    Fetch temperature and calculate absolute humidity & relative humidity.
    """
    try:
        latitude, longitude, elevation = get_coordinates(location_name)

        if latitude is None or longitude is None:
            print(f"Could not fetch weather data for {location_name} due to missing coordinates.")
            return pd.DataFrame()

        location = Point(latitude, longitude, elevation)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Fetch daily weather data
        weather_data = Daily(location, start_date, end_date).fetch()

        if weather_data.empty:
            print(f"No weather data available for {location_name}.")
            return pd.DataFrame()

        # Handle missing temperature fields
        if 'tavg' in weather_data.columns:
            temp = weather_data['tavg']
        elif 'tmin' in weather_data.columns and 'tmax' in weather_data.columns:
            temp = (weather_data['tmin'] + weather_data['tmax']) / 2  # Estimate avg temp
        else:
            print(f"Temperature data missing for {location_name}.")
            return pd.DataFrame()

        # Calculate absolute humidity and saturation vapor pressure
        absolute_humidity, svp = calculate_absolute_humidity(temp)

        # Calculate relative humidity in percentage
        relative_humidity = (absolute_humidity * (temp + 273.15)) / (2.16679 * svp) * 1

        # Detect Rainy & Foggy Conditions
        rainy_condition = ["Yes" if rh > 80 and temp < 30 else "No" for rh, temp in zip(relative_humidity, temp)]
        foggy_condition = ["Yes" if rh > 90 and temp < 20 else "No" for rh, temp in zip(relative_humidity, temp)]

        # Create DataFrame
        final_data = pd.DataFrame({
            'Date': weather_data.index.date,  # Use `.date()` to remove timestamp
            'Temperature (°C)': temp,
            'Relative Humidity (%)': relative_humidity,
            'Rainy Condition': rainy_condition,
            'Foggy Condition': foggy_condition,
            'Location': location_name
        })

        print(f"Weather data for {location_name} fetched successfully!")
        return final_data.reset_index(drop=True)

    except Exception as e:
        print(f"An error occurred while fetching weather data for {location_name}: {e}")
        return pd.DataFrame()

def predict_future_weather(past_weather, days_ahead=7):
    """
    Predict the next `days_ahead` days' weather using a simple trend model.
    """
    if past_weather.empty:
        print("No past data available for prediction.")
        return pd.DataFrame()

    # Get last known temperature and humidity
    last_temp = past_weather['Temperature (°C)'].iloc[-1]
    last_rh = past_weather['Relative Humidity (%)'].iloc[-1]

    # Generate future dates
    future_dates = [(datetime.now() + timedelta(days=i)).date() for i in range(1, days_ahead + 1)]

    # Predict temperature and humidity with a slight increasing trend
    future_temps = [last_temp + (i * 0.08) for i in range(1, days_ahead + 1)]
    future_humidities = [last_rh for _ in range(1, days_ahead + 1)]  # Keeping RH constant

    # Detect Rainy & Foggy Conditions
    rainy_condition = ["Yes" if rh > 80 and temp < 30 else "No" for rh, temp in zip(future_humidities, future_temps)]
    foggy_condition = ["Yes" if rh > 90 and temp < 20 else "No" for rh, temp in zip(future_humidities, future_temps)]

    # Create DataFrame
    future_data = pd.DataFrame({
        'Date': future_dates,
        'Temperature (°C)': future_temps,
        'Relative Humidity (%)': future_humidities,
        'Rainy Condition': rainy_condition,
        'Foggy Condition': foggy_condition
    })

    print("Future Weather Predictions:")
    return future_data

if __name__ == "__main__":
    location_name = "Mumbai"
    
    # Fetch past weather data
    weather_data = fetch_weather_data(location_name)
    print(weather_data)

    # Predict future weather for next 7 days
    future_weather = predict_future_weather(weather_data, days_ahead=7)
    print(future_weather)
