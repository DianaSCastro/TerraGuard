import ee
import requests
import json
import pandas as pd
import random

# Inicializar Google Earth Engine
ee.Initialize(project='terraguard-477621')

class DataLayer:
    def __init__(self):
        pass

    # -----------------------------
    # 1. Datos de riesgo de inundación (GEE)
    # -----------------------------
    def get_flood_risk(self, lon, lat, rp="RP10_depth_category"):
        """
        Devuelve el valor de riesgo de inundación para un punto.
        rp: 'RP10_depth_category', 'RP50_depth_category', 'RP100_depth_category', etc.
        """
        point = ee.Geometry.Point([lon, lat])
        flood_col = ee.ImageCollection("JRC/CEMS_GLOFAS/FloodHazard/v2_1").mosaic()
        flood_val = flood_col.select(rp).sample(point, 30).first().getInfo()
        return flood_val

    # -----------------------------
    # 2. Vegetación (NDVI) y Elevación (SRTM)
    # -----------------------------
    def get_ndvi(self, lon, lat):
        point = ee.Geometry.Point([lon, lat])
        ndvi_col = ee.ImageCollection('MODIS/006/MOD13A2').select('NDVI')
        ndvi_img = ndvi_col.filterBounds(point).sort('system:time_start', False).first()
        ndvi_val = ndvi_img.sample(point, 30).first().get('NDVI').getInfo()
        return ndvi_val

    def get_elevation(self, lon, lat):
        point = ee.Geometry.Point([lon, lat])
        srtm = ee.Image("USGS/SRTMGL1_003")
        elev_val = srtm.sample(point, 30).first().get('elevation').getInfo()
        return elev_val

    # -----------------------------
    # 3. Datos climáticos en tiempo real (Open-Meteo)
    # -----------------------------
    def get_weather(self, lon, lat):
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()


             # 👇 Imprime las primeras 5 fechas y horas disponibles (verifica que son de hoy)
            print("🕒 Horas disponibles:", data['hourly']['time'][:5])

            # Retornar promedios de las últimas 24 horas
            temp = sum(data['hourly']['temperature_2m'])/len(data['hourly']['temperature_2m'])
            humidity = sum(data['hourly']['relative_humidity_2m'])/len(data['hourly']['relative_humidity_2m'])
            precipitation = sum(data['hourly']['precipitation'])
            wind_speed = sum(data['hourly']['wind_speed_10m'])/len(data['hourly']['wind_speed_10m'])
            return {
                "temperature": temp,
                "humidity": humidity,
                "precipitation": precipitation,
                "wind_speed": wind_speed
            }
        else:
            return None

    # -----------------------------
    # 4. Riesgo sísmico (USGS)
    # -----------------------------
    def get_earthquake_frequency(self, lon, lat, past_days=365):
        """
        Número de terremotos en el último año dentro de 50km del punto.
        """
        radius_km = 50
        endtime = pd.Timestamp.now()
        starttime = endtime - pd.Timedelta(days=past_days)
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime={starttime.date()}&endtime={endtime.date()}&latitude={lat}&longitude={lon}&maxradiuskm={radius_km}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return len(data['features'])
        else:
            return 0

    # -----------------------------
    # 5. Huracanes / tormentas (NOAA)
    # -----------------------------
    def get_hurricane_frequency(self, lon, lat, years=5):
        """
        Número de tormentas / huracanes en los últimos 'years' años.
        """
        url = f"https://www.ncei.noaa.gov/access/services/data/v1?dataset=stormevents&dataTypes=all&format=json"
        # Nota: Para producción, filtrar por ubicación y fecha
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Se puede procesar para contar eventos cercanos
            return len(data)
        else:
            return 0

    # -----------------------------
    # 6. Incendios forestales (NASA FIRMS)
    # -----------------------------
    def get_fire_frequency(self, lon, lat, past_days=365):
        """
        Número de incendios detectados por satélite en el último año
        """
        url = "https://firms.modaps.eosdis.nasa.gov/api/active_fire.json"  # API hipotética
        # Filtrar por lat/lon y fecha
        # Retornar número de eventos
        return 0  # Placeholder

    # -----------------------------
    # 7. Actividad volcánica (Global Volcano Locations)
    # -----------------------------
    def get_volcano_proximity(self, lon, lat):
        """
        Devuelve la distancia al volcán más cercano en km
        """
        # Cargar dataset de volcanes previamente descargado y almacenado localmente
        with open("data_layer/volcanoes.json") as f:
            volcanoes = json.load(f)
        min_dist = min([self.haversine(lon, lat, v['longitude'], v['latitude']) for v in volcanoes])
        return min_dist

    def haversine(self, lon1, lat1, lon2, lat2):
        """
        Calcula distancia en km entre dos coordenadas
        """
        from math import radians, cos, sin, asin, sqrt
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        c = 2*asin(sqrt(a))
        km = 6371 * c
        return km
    


     # -----------------------------
    # MÉTODOS PREDICTIVOS A FUTURO
    # -----------------------------
    def get_future_weather(self, lon, lat, target_year):
        """
        Predicción simplificada de clima.
        target_year: año futuro (int)
        """
        current = self.get_weather(lon, lat)
        years_ahead = target_year - 2025  # usar 2025 como referencia

        # Tendencia lineal simple: por año +0.2°C, -0.5% humedad, +0.1 mm precipitación
        future = {
            "temperature": current['temperature'] + 0.2 * years_ahead,
            "humidity": max(0, min(100, current['humidity'] - 0.5 * years_ahead)),
            "wind_speed": current['wind_speed'],  # sin cambio
            "precipitation": max(0, current['precipitation'] + 0.1 * years_ahead)
        }
        return future
    
    def get_future_ndvi(self, lon, lat, target_year):
        """
        Predicción simplificada de NDVI.
        """
        current_ndvi = self.get_ndvi(lon, lat)
        years_ahead = target_year - 2025

        # Simulamos tendencia de vegetación: +/- 10 por año
        trend = random.choice([-1, 1]) * 10
        future_ndvi = max(0, min(1000, current_ndvi + trend * years_ahead))
        return future_ndvi

