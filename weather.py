import requests
from Speech_Drive.Short_speech import *

def speak(audio):
    asyncio.run(speech(audio))
    playsound("output.mp3")

api_key = "1ac5fe9217d14f20bca64622231311"

def get_weather(city):
    """
    Fetches and returns a detailed weather report for the specified city.
    :param city: The name of the city.
    :return: A formatted weather report as a string.
    """
    try:
        API_KEY = api_key  # Replace with your WeatherAPI.com key
        BASE_URL = "http://api.weatherapi.com/v1/forecast.json"
    
        params = {
            "key": API_KEY,
            "q": city,
            "days": 3,
            "alerts": "yes",
            "aqi": "yes"
        }
    
        response = requests.get(BASE_URL, params=params)
        data = response.json()
    
        if "error" in data:
            return f"Error: {data['error']['message']}"
    
        location = data["location"]["name"]
        country = data["location"]["country"]
        temp_c = data["current"]["temp_c"]
        condition = data["current"]["condition"]["text"]
        wind_speed = data["current"]["wind_kph"]
        humidity = data["current"]["humidity"]
        chance_of_rain = data["forecast"]["forecastday"][0]["day"]["daily_chance_of_rain"]
        alerts = data.get("alerts", {}).get("alert", [])
    
        forecast = data["forecast"]["forecastday"]
        forecast_details = "\n".join(
            [f"- {day['date']}: {day['day']['condition']['text']}, High: {day['day']['maxtemp_c']}°C, Low: {day['day']['mintemp_c']}°C" for day in forecast]
        )
    
        alert_text = "No severe weather alerts."
        if alerts:
            alert_text = "\n".join([f"- {alert['headline']}" for alert in alerts])
    
    # report = f"""
    # Weather Report for {location}, {country}:
    # - Temperature: {temp_c}°C
    # - Condition: {condition}
    # - Wind Speed: {wind_speed} km/h
    # - Humidity: {humidity}%
    # - Chance of Rain: {chance_of_rain}%
    
    # Forecast:
    # {forecast_details}
    
    # Alerts:
    # {alert_text}
    # """.strip()
        report = f"""
        Sir! Here’s the latest weather update for {location}, {country}. Right now, it’s {temp_c}°C with {condition}. The wind is blowing at {wind_speed} km/h, and humidity is at {humidity}%, making it feel {'humid' if humidity > 60 else 'dry'}. There’s a {chance_of_rain}% chance of rain today.
    
        Looking ahead, here’s the forecast for the next few days:
        {forecast_details}
    
        Alerts:
        {alert_text}
    
        Stay safe and have a great day Sir!
        """.strip()
    
        print(report)
        speak(f"Sir! Here’s the latest weather update for {location}, {country}. Right now, it’s {temp_c}°C with {condition}. The wind is blowing at {wind_speed} km/h, and humidity is at {humidity}%, making it feel {'humid' if humidity > 60 else 'dry'}. There’s a {chance_of_rain}% chance of rain today.")
        # return report
    except Exception as e:
        print(e)
        

# Example Usage:
if __name__ == "__main__":
    print(get_weather("Allahabad"))