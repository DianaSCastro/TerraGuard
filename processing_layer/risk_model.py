# processing_layer/risk_model.py
from data_layer.data2 import DataLayer

class RiskModel:
    """
    Calcula un índice de riesgo ambiental (0-100) para una ubicación,
    combinando factores geoespaciales y climáticos.
    Versión robusta: devuelve riesgo general y % por métrica.
    """
    def __init__(self):
        self.data_layer = DataLayer()
        # Ponderaciones (deben sumar aproximadamente 1.0)
        self.weights = {
            "seismic": 0.4,
            "flood": 0.3,
            "hurricane": 0.2,
            "fire": 0.1,
            "temperature": 0.,
            "humidity": 0.10,
            "wind": 0.10,
            "precipitation": 0.10,
            "vegetation": 0.10,
            "elevation": 0.10
        }
        # Máximos razonables para normalizar cada métrica a [0,1]
        self.max_values = {
            "seismic": 1000.0,
            "flood": 5.0,
            "hurricane": 50.0,
            "fire": 200.0,
            "temperature": 50.0,
            "humidity": 100.0,
            "wind": 50.0,
            "precipitation": 200.0,
            "vegetation": 1.0,   # NDVI normalizado 0..1
            "elevation": 3000.0
        }

    def adjust_weights(self, raw):
        """
        Ajusta las ponderaciones según el contexto real de la zona.
        Los pesos siempre se normalizan para que sumen 1.0.
        """
        w = self.weights.copy()

        # Variables base
        fire = float(raw.get('fire_rate') or 0)
        hurricane = float(raw.get('hurricane_rate') or 0)
        wind = float(raw.get('wind') or 0)
        precip = float(raw.get('precipitation') or 0)
        temp = float(raw.get('temperature') or 0)
        ndvi = float(raw.get('vegetation') or 0)

        # 🔹 Reglas solicitadas:
        # 1️⃣ Si el índice de fuego = 0, reducir viento y precipitación a la mitad
        if fire == 0:
            w['wind'] *= 0.5
            w['precipitation'] *= 0.5

        # 2️⃣ Si el índice de fuego = 0, la vegetación se pondera con 0
        if fire == 0:
            w['vegetation'] = 0

        # 3️⃣ Si el índice de huracanes = 0, el viento se reduce a la mitad
        if hurricane == 0:
            w['wind'] *= 0.5

        # 4️⃣ El índice de temperatura se pondera siempre con 0
        w['temperature'] = 0

        # 🔸 Ajustes de contexto (los que ya tenías antes)
        if not raw.get('seismic_rate'):
            w['seismic'] *= 0.5

        if ndvi > 0.5:
            w['fire'] *= 0.6

        elev = raw.get('elevation') or 0
        if elev < 100:
            w['flood'] *= 1.3
            w['hurricane'] *= 1.2

        humidity = raw.get('humidity') or 0
        if humidity < 30:
            w['fire'] *= 1.4

        # 🔹 Normalizar para que los pesos sumen 1.0
        total = sum(w.values())
        if total > 0:
            for k in w:
                w[k] /= total

        return w


    

    # -----------------------------
    # Public: calcula riesgo y devuelve desglose
    # -----------------------------
    def calculate_risk_with_breakdown(self, lon, lat, target_year=None):
    # 1️⃣ Guardar los valores crudos
        raw = self.get_factors(lon, lat, target_year=target_year)

        # 2️⃣ Normalización de métricas
        m = {}
        n = {}

        # Si existe el valor, asignar 1; si no, usar normalización original
        seismic_raw = float(raw.get('seismic_rate'))
        m['seismic'] = 1.0 if seismic_raw else 0.0
        n['seismic'] = self._clip01(seismic_raw / self.max_values['seismic'])
        print(n['seismic'])

        flood_raw = raw.get('flood_rate')
        flood_val = self._extract_numeric(flood_raw)
        m['flood'] = 1.0 if flood_raw else 0.0
        n['flood'] = self._clip01(flood_val / self.max_values['flood'])

        hurricane_raw = raw.get('hurricane_rate')
        m['hurricane'] = 1.0 if hurricane_raw else 0.0
        n['hurricane'] = self._clip01(hurricane_raw / self.max_values['hurricane'])

        fire_raw = raw.get('fire_rate')
        m['fire'] = 1.0 if fire_raw else 0.0
        n['fire'] = self._clip01(fire_raw / self.max_values['fire'])

        temp_raw = raw.get('temperature')
        m['temperature'] = 1.0 if temp_raw else 0.0
        n['temperature'] = self._clip01(temp_raw / self.max_values['temperature'])

        humidity_raw = raw.get('humidity')
        m['humidity'] = 1.0 if humidity_raw else 0.0
        n['humidity'] = self._clip01(humidity_raw / self.max_values['humidity']) 

        wind_raw = raw.get('wind')
        m['wind'] = 1.0 if wind_raw else 0.0
        n['wind'] = self._clip01(wind_raw / self.max_values['wind'])

        precip_raw = raw.get('precipitation')
        m['precipitation'] = 1.0 if precip_raw else 0.0
        n['precipitation'] = self._clip01(precip_raw / self.max_values['precipitation'])

        vegetation_raw = raw.get('vegetation')
        if vegetation_raw is not None:
            m['vegetation'] = 1.0
        else:
           m['vegetation'] = 0.0
        ndvi_norm_0_1 = self._normalize_ndvi(vegetation_raw)
        n['vegetation'] = self._clip01(1.0 - ndvi_norm_0_1)

        elev_raw = raw.get('elevation')
        elev = float(elev_raw or 0)
        elev_norm = self._clip01(elev / self.max_values['elevation'])
        m['elevation'] = 1.0 if elev_raw else 0.0
        n['elevation'] = self._clip01(1.0 - elev_norm)
        # ✅ Devolver resultados

        # Ajuste dinámico de pesos
        adjusted_weights = self.adjust_weights(raw)

        # Calcular riesgo ponderado
        total = 0.0
        for key, w in adjusted_weights.items():
            total += m.get(key, 0) * w

        risk_percent = int(round(total * 100))
        metrics_percent = {k: round(v*100, 2) for k, v in n.items()}

        return {
            'raw_factors': raw,
            'metrics_percent': metrics_percent,
            'risk_percent': risk_percent  # ejemplo de cálculo de riesgo general
        }


        # Ajuste dinámico de pesos
        adjusted_weights = self.adjust_weights(raw)

        # Calcular riesgo ponderado
        total = 0.0
        for key, w in adjusted_weights.items():
            total += m.get(key, 0) * w

        risk_percent = int(round(total * 100))
        metrics_percent = {k: round(v*100, 2) for k, v in m.items()}

        return {
            "risk_percent": risk_percent,
            "metrics_percent": metrics_percent,
            "raw_factors": raw
        }

    # -----------------------------
    # Helpers
    # -----------------------------
    def _clip01(self, x):
        try:
            if x != x:  # NaN
                return 0.0
            return max(0.0, min(1.0, float(x)))
        except:
            return 0.0

    def _extract_numeric(self, val):
        """
        Extrae un valor numérico de una posible estructura (dict/list/number).
        """
        if val is None:
            return 0.0
        if isinstance(val, dict):
            # buscar valores numéricos en el dict
            for v in val.values():
                try:
                    return float(v)
                except:
                    continue
            return 0.0
        if isinstance(val, (list, tuple)):
            for item in val:
                try:
                    return float(item)
                except:
                    continue
            return 0.0
        try:
            return float(val)
        except:
            return 0.0

    def _normalize_ndvi(self, ndvi_val):
        """
        Normaliza NDVI a 0..1.
        Trata escalas comunes (MODIS 0..10000 o -2000..10000 con factor 0.0001).
        """
        if ndvi_val is None:
            return 0.0
        raw = self._extract_numeric(ndvi_val)
        if raw == 0:
            return 0.0
        # Si la magnitud es grande, dividir por 10000 (MODIS) o 1000
        if abs(raw) > 2:
            ndvi = raw / 10000.0
            if -1.0 <= ndvi <= 1.0:
                return self._clip01((ndvi + 1.0) / 2.0)
            ndvi = raw / 1000.0
            if -1.0 <= ndvi <= 1.0:
                return self._clip01((ndvi + 1.0) / 2.0)
            # fallback lineal
            return self._clip01((raw + 10000.0) / 20000.0)
        else:
            # ya en -1..1
            ndvi = raw
            return self._clip01((ndvi + 1.0) / 2.0)

    # -----------------------------
    # Obtener factores desde data_layer (si falla, devuelve 0 seguro)
    # -----------------------------
    def get_factors(self, lon, lat, target_year=None):
        """
        Obtiene factores crudos para la ubicación.
        Si target_year es None → datos actuales.
        Si target_year = N → usar proyecciones climáticas / NDVI proyectado.
        """
        f = {}
        
        # 🔹 Riesgos geológicos (sismos, elevación) → estáticos
        try:
            f['seismic_rate'] = self.data_layer.get_earthquake_frequency(lon, lat)
        except Exception:
            f['seismic_rate'] = 0
        try:
            f['flood_rate'] = self.data_layer.get_flood_risk(lon, lat, rp="RP10_depth_category")
        except Exception:
            f['flood_rate'] = 0
        try:
            f['hurricane_rate'] = self.data_layer.get_hurricane_frequency(lon, lat)
        except Exception:
            f['hurricane_rate'] = 0
        try:
            f['fire_rate'] = self.data_layer.get_fire_frequency(lon, lat)
        except Exception:
            f['fire_rate'] = 0
        
        # 🔹 Factores climáticos → proyectados si target_year no es None
        try:
            if target_year:
                # Aquí llamarías a tu método de predicción/clima proyectado
                weather = self.data_layer.get_future_weather(lon, lat, target_year)
            else:
                weather = self.data_layer.get_weather(lon, lat)
            
            f['temperature'] = weather.get('temperature', 0)
            f['humidity'] = weather.get('humidity', 0)
            f['wind'] = weather.get('wind_speed', 0)
            f['precipitation'] = weather.get('precipitation', 0)
        except Exception:
            f['temperature'] = f['humidity'] = f['wind'] = f['precipitation'] = 0

        # 🔹 Vegetación (NDVI)
        try:
            if target_year:
                f['vegetation'] = self.data_layer.get_future_ndvi(lon, lat, target_year)
            else:
                f['vegetation'] = self.data_layer.get_ndvi(lon, lat)
        except Exception:
            f['vegetation'] = 0
        
        # 🔹 Elevación → estático
        try:
            f['elevation'] = self.data_layer.get_elevation(lon, lat)
        except Exception:
            f['elevation'] = 0

        return f
