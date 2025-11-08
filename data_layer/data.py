# data_layer/data.py
import requests
import pandas as pd

def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        df = pd.DataFrame({
            "temperature": data["hourly"]["temperature_2m"],
            "precipitation": data["hourly"]["precipitation"]
        })
        return df
    else:
        return None
