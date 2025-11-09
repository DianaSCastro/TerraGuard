#Obtiene datos de GEE, Open-Meteo, Gemini y otros servicios

# data_layer/data.py
import requests
import pandas as pd
import ee 

# Inicia sesión con la nueva cuenta
ee.Authenticate()
ee.Initialize(project='terraguard-477621')
print('Earth Engine funcionando correctamente 🌎')



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
    
