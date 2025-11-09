import ee
import folium
from processing_layer.risk_model import RiskModel
from business_layer.rules import InsuranceRules
from data_layer.data2 import DataLayer
import math 
from geopy.distance import geodesic, great_circle

# Inicializar Earth Engine
ee.Initialize(project='terraguard-477621')
print("🌍 Earth Engine funcionando correctamente")

class TerraGuardUI:
    """
    Interfaz para mostrar mapas de riesgo ambiental y puntuaciones.
    """
    def __init__(self):
        self.risk_model = RiskModel()
        self.rules = InsuranceRules()
        self.data_layer = DataLayer()

        

        # Token de Mapbox
        self.mapbox_token = "sk.eyJ1Ijoic2FtdW1hbXUiLCJhIjoiY21ocjhoNmt1MTRycjJqb29xcXBlbGFwbyJ9.lDsItTFuKz9UUCyDqshagQ"

        # Configuración inicial del mapa (lat, lon)
        self.map_center = [lat_in, lon_in]  # Monterrey (lat, lon)
        self.zoom = 12

        self.map = folium.Map(
            location=self.map_center,
            zoom_start=self.zoom,
            tiles=f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{{z}}/{{x}}/{{y}}?access_token={self.mapbox_token}",
            attr="Mapbox Satellite",
            name="Mapa Satelital (Mapbox)",
            zoom_offset=-1,
            tile_size=512,
        )


        # -----------------------------
    # Agregar un polígono alrededor de la ubicación
    # -----------------------------
    def add_risk_polygon(self, lon, lat, risk_general, radius_meters=500):
        """
        radius_meters: tamaño aproximado del área alrededor de la ubicación
        """
        import geopy.distance

        # Convertir distancia a grados aproximadamente (simplificado)
        lat_offset = radius_meters / 111320  # 1 grado lat ~ 111.32 km
        lon_offset = radius_meters / (111320 * abs(math.cos(math.radians(lat))))

        # Crear vértices del cuadrado
        polygon_coords = [
            [lat - lat_offset, lon - lon_offset],
            [lat - lat_offset, lon + lon_offset],
            [lat + lat_offset, lon + lon_offset],
            [lat + lat_offset, lon - lon_offset],
            [lat - lat_offset, lon - lon_offset]
        ]

        folium.Polygon(
            locations=polygon_coords,
            color=self.score_color(risk_general),  # borde
            fill=True,
            fill_color=self.score_color(risk_general),
            fill_opacity=0.2  # baja opacidad
        ).add_to(self.map)

    # -----------------------------
    # Determinar color del marcador según riesgo
    # -----------------------------
    def score_color(self, score):
        if score <= 30:
            return 'green'
        elif score <= 60:
            return 'orange'
        else:
            return 'red'

    # -----------------------------
    # Agregar marcador con popup
    # -----------------------------
    def add_risk_marker(self, lon, lat, risk_general, metrics, raw=None):
        # metrics: dict con claves como 'seismic','flood','hurricane',... en %
        popup_text = f"""
        <b>📍 Coordenadas:</b> ({lat:.6f}, {lon:.6f})<br>
        <b>🌡️ Riesgo general:</b> {risk_general}%<br><hr>
        <b>📊 Riesgos por métrica:</b><br>
        🔹 Sísmico: {metrics.get('seismic', 0):.1f}%<br>
        🔹 Inundación: {metrics.get('flood', 0):.1f}%<br>
        🔹 Huracán: {metrics.get('hurricane', 0):.1f}%<br>
        🔹 Incendio: {metrics.get('fire', 0):.1f}%<br>
        🔹 Precipitación: {metrics.get('precipitation', 0):.1f}%<br>
        🔹 Vegetación: {metrics.get('vegetation', 0):.1f}%<br>
        """

        # (Opcional) añadir botón para ver valores crudos (si se los quieres mostrar)
        if raw:
            popup_text += "<hr><b>Raw:</b><br>"
            # mostrar sólo algunas claves crudas para no saturar el popup
            for k in ['seismic_rate','flood_rate','temperature','vegetation','elevation']:
                if k in raw:
                    popup_text += f"{k}: {raw.get(k)}<br>"

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_text, max_width=420),
            icon=folium.Icon(color=self.score_color(risk_general), icon="info-sign")
        ).add_to(self.map)

    # -----------------------------
    # Mostrar mapa
    # -----------------------------
    def show_map(self):
        folium.LayerControl().add_to(self.map)
        output_file = "mapa_riesgo.html"
        self.map.save(output_file)
        print(f"✅ Mapa guardado como {output_file}")

        import webbrowser, os
        webbrowser.open('file://' + os.path.realpath(output_file))

    # -----------------------------
    # Validar e intercambiar coordenadas si están invertidas
    # -----------------------------
    def validate_coords(self, lon, lat):
        """
        Si el usuario ingresó lat/lon invertidos (caso común),
        intenta detectarlo e invertirlos automáticamente.
        """
        # Rango válido: lon [-180,180], lat [-90,90]
        if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
            # posible intercambio
            if -180 <= lat <= 180 and -90 <= lon <= 90:
                print("⚠️ Detectadas coordenadas invertidas; intercambiando valores (lat<->lon).")
                return lat, lon
            else:
                raise ValueError(f"Coordenadas inválidas: lon={lon}, lat={lat}")
        return lon, lat

    # -----------------------------
    # Ejecutar análisis completo
    # -----------------------------
    def analyze_location(self, lon, lat, target_year=None):
        # Validar / corregir posible inversión
        try:
            lon, lat = self.validate_coords(lon, lat)
        except ValueError as e:
            print(f"ERROR: {e}")
            return

        if target_year:
            print(f"📍 Analizando ubicación: (lat={lat}, lon={lon}) para año {target_year}...")
        else:
            print(f"📍 Analizando ubicación: (lat={lat}, lon={lon}) con datos actuales...")

        # Usar la función robusta del RiskModel
        result = self.risk_model.calculate_risk_with_breakdown(lon, lat, target_year=target_year)

        risk_general = result.get('risk_percent', 0)
        metrics = result.get('metrics_percent', {})  # cada métrica en %
        raw = result.get('raw_factors', {})

        # Mostrar en consola para debug
        print("RAW factors:", raw)
        print("Metrics (%):", metrics)
        print(f"Riesgo general: {risk_general}%")

        # Agregar marcador con la info ya normalizada
        self.add_risk_marker(lon, lat, risk_general, metrics, raw)
                # Agregar marcador con la info ya normalizada
        self.add_risk_marker(lon, lat, risk_general, metrics, raw)

        # Agregar polígono de la zona analizada
        self.add_risk_polygon(lon, lat, risk_general, radius_meters=500)



# -----------------------------
# Ejemplo de uso (App principal)
# -----------------------------
if __name__ == "__main__":
    # 🔹 Variables que asigna el usuario
    lon_in = float(input("Introduce la longitud (ej. -100.3161): "))
    lat_in = float(input("Introduce la latitud (ej. 25.6866): "))

    # Pedir año objetivo para predicción (puede dejar vacío para datos actuales)
    target_year_input = input("Introduce el año para predicción futura (dejar vacío para riesgo actual): ").strip()
    target_year = int(target_year_input) if target_year_input else None

    # Crear la app centrada en esa ubicación
    app = TerraGuardUI()

    # 💡 Ajustar el centro del mapa a las coordenadas ingresadas
    app.map.location = [lat_in, lon_in]
    app.map.zoom_start = 12  # puedes modificar el zoom si quieres más detalle

    # Analizar y mostrar resultados
    app.analyze_location(lon_in, lat_in, target_year=target_year)
    app.show_map()
