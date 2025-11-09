import ee
import folium
from processing_layer.risk_model import RiskModel
from business_layer.rules import InsuranceRules
from data_layer.data2 import DataLayer

# Inicializar Earth Engine
ee.Initialize(project='terraguard-477621')
print("Earth Engine funcionando correctamente 🌎")

class TerraGuardUI:
    """
    Interfaz para mostrar mapas de riesgo ambiental y puntuaciones,
    renderizados con Mapbox (sin geemap).
    """
    def __init__(self):
        self.risk_model = RiskModel()
        self.rules = InsuranceRules()
        self.data_layer = DataLayer()

        # Token de Mapbox
        self.mapbox_token = "sk.eyJ1Ijoic2FtdW1hbXUiLCJhIjoiY21ocjhoNmt1MTRycjJqb29xcXBlbGFwbyJ9.lDsItTFuKz9UUCyDqshagQ"

        # Configuración del mapa base
        self.map_center = [25.6866, -99.1332]  # Monterrey
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
    # 3. Color según score
    # -----------------------------
    def score_color(self, score):
        if score <= 30:
            return 'green'
        elif score <= 60:
            return 'orange'
        else:
            return 'red'
        
    def add_marker(self, lon, lat, popup_text="Ubicación seleccionada"):
        folium.Marker(
            location=[lat, lon],
            popup=popup_text,
            icon=folium.Icon(color='blue', icon='map-marker')
        ).add_to(self.map)


    # -----------------------------
    # 4. Mostrar mapa
    # -----------------------------
    def show_map(self):
        folium.LayerControl().add_to(self.map)
        output_file = "mapa_riesgo.html"
        self.map.save(output_file)
        print(f"✅ Mapa guardado como {output_file}")

        import webbrowser, os
        webbrowser.open('file://' + os.path.realpath(output_file))


# -----------------------------
# Ejemplo de uso
# -----------------------------
if __name__ == "__main__":
    lon, lat = -99.1332, 25.6866  # Monterrey
    app = TerraGuardUI()
    #app.add_risk_layers(lon, lat)
    #app.add_risk_marker(lon, lat)
    app.add_marker(lon, lat, "Punto central: Monterrey")
    app.show_map()
