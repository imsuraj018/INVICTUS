from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from weather_fetch import fetch_weather_data, predict_future_weather  

app = Flask(__name__)
CORS(app)

@app.route('/weather', methods=['GET'])
def get_weather():
    location = request.args.get('location')
    if not location:
        return jsonify({"error": "Location parameter is required"}), 400

    weather_data = fetch_weather_data(location)
    if weather_data.empty:
        return jsonify({"error": f"No weather data found for {location}"}), 404

    return jsonify(weather_data.to_dict(orient='records'))

@app.route('/predict', methods=['GET'])
def get_future_weather():
    location = request.args.get('location')
    if not location:
        return jsonify({"error": "Location parameter is required"}), 400

    weather_data = fetch_weather_data(location)
    if weather_data.empty:
        return jsonify({"error": f"No weather data found for {location}, cannot predict future weather."}), 404

    future_weather = predict_future_weather(weather_data, days_ahead=7)
    return jsonify(future_weather.to_dict(orient='records'))

if __name__ == "__main__":
    app.run(debug=True)
