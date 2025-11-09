from data_layer.data2 import DataLayer

class RiskModel:
    """
    Calcula un índice de riesgo ambiental (0-100) para una ubicación,
    combinando factores geoespaciales y climáticos.
    """
    def __init__(self):
        self.data_layer = DataLayer()
        # Ponderaciones de cada factor (ajustables)
        self.weights = {
            "seismic": 0.25,
            "flood": 0.2,
            "hurricane": 0.15,
            "fire": 0.1,
            "temperature": 0.05,
            "humidity": 0.05,
            "wind": 0.05,
            "precipitation": 0.05,
            "vegetation": 0.05,
            "elevation": 0.05,
            "volcano_proximity": 0.05
        }

    # -----------------------------
    # 1. Calcular riesgo total
    # -----------------------------
    def calculate_risk(self, lon, lat):
        # Obtener datos de la capa de datos
        seismic_rate = self.normalize(self.data_layer.get_earthquake_frequency(lon, lat))
        flood_rate = self.normalize(self.data_layer.get_flood_risk(lon, lat, rp="RP10_depth_category"))
        hurricane_rate = self.normalize(self.data_layer.get_hurricane_frequency(lon, lat))
        fire_rate = self.normalize(self.data_layer.get_fire_frequency(lon, lat))
        
        weather = self.data_layer.get_weather(lon, lat)
        temp = self.normalize(weather['temperature']) if weather else 0
        humidity = self.normalize(weather['humidity']) if weather else 0
        wind = self.normalize(weather['wind_speed']) if weather else 0
        precipitation = self.normalize(weather['precipitation']) if weather else 0

        ndvi = self.data_layer.get_ndvi(lon, lat)
        vegetation = 1 - self.normalize(ndvi)  # menos vegetación → más riesgo

        elevation = self.data_layer.get_elevation(lon, lat)
        elevation_risk = 1 - self.normalize(elevation, max_value=3000)  # más bajo → más riesgo

       #volcano_distance = self.data_layer.get_volcano_proximity(lon, lat)
        #volcano_risk = self.volcano_score(volcano_distance)

        # Calcular score ponderado
        risk = (
            seismic_rate * self.weights['seismic'] +
            flood_rate * self.weights['flood'] +
            hurricane_rate * self.weights['hurricane'] +
            fire_rate * self.weights['fire'] +
            temp * self.weights['temperature'] +
            humidity * self.weights['humidity'] +
            wind * self.weights['wind'] +
            precipitation * self.weights['precipitation'] +
            vegetation * self.weights['vegetation'] +
            elevation_risk * self.weights['elevation']
            #volcano_risk * self.weights['volcano_proximity']
        )

        # Escalar a 0-100
        return int(risk * 100)

    # -----------------------------
    # 2. Normalización simple
    # -----------------------------
    def normalize(self, value, max_value=100):
        try:
            return min(float(value)/max_value, 1.0)
        except:
            return 0

    # -----------------------------
    # 3. Escala de riesgo volcánico
    # -----------------------------
    def volcano_score(self, distance_km):
        """
        Distancia <10 km → riesgo 1
        10-50 km → riesgo 0.5
        >50 km → riesgo 0
        """
        if distance_km < 10:
            return 1.0
        elif distance_km < 50:
            return 0.5
        else:
            return 0

    # -----------------------------
    # 4. Obtener todos los factores (para reporte / interpretación)
    # -----------------------------
    def get_factors(self, lon, lat):
        factors = {}
        factors['seismic_rate'] = self.data_layer.get_earthquake_frequency(lon, lat)
        factors['flood_rate'] = self.data_layer.get_flood_risk(lon, lat, rp="RP10_depth_category")
        factors['hurricane_rate'] = self.data_layer.get_hurricane_frequency(lon, lat)
        factors['fire_rate'] = self.data_layer.get_fire_frequency(lon, lat)
        weather = self.data_layer.get_weather(lon, lat)
        factors['temperature'] = weather['temperature'] if weather else None
        factors['humidity'] = weather['humidity'] if weather else None
        factors['wind'] = weather['wind_speed'] if weather else None
        factors['precipitation'] = weather['precipitation'] if weather else None
        factors['vegetation'] = self.data_layer.get_ndvi(lon, lat)
        factors['elevation'] = self.data_layer.get_elevation(lon, lat)
        #factors['volcano_distance_km'] = self.data_layer.get_volcano_proximity(lon, lat)

        for key in factors:
            if factors[key] is None:
                factors[key] = 0  # o valor seguro

        return factors
