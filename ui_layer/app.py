import ee
import geemap
from processing_layer.risk_model import RiskModel
from business_layer.rules import InsuranceRules
from data_layer.data2 import DataLayer

# Inicializar Earth Engine
ee.Initialize(project='terraguard-477621')
print("Earth Engine funcionando correctamente 🌎")

class TerraGuardUI:
    """
    Interfaz para mostrar mapas de riesgo ambiental y puntuaciones.
    """
    def __init__(self):
        self.risk_model = RiskModel()
        self.rules = InsuranceRules()
        self.data_layer = DataLayer()

        # Inicializar mapa centrado en México
        self.map_center = (25.6866, -99.1332)  # Monterrey
        self.zoom = 6
        self.map = geemap.Map(center=self.map_center, zoom=self.zoom)

    # -----------------------------
    # 1. Agregar capas de riesgo
    # -----------------------------
    def add_risk_layers(self, lon, lat):
        # Dataset de inundación RP100
        flood_col = ee.ImageCollection("JRC/CEMS_GLOFAS/FloodHazard/v2_1").mosaic().select('RP100_depth_category')
        flood_vis = {'min':1, 'max':5, 'palette':['#ffffff','#b3e5fc','#0288d1','#01579b','#001f54']}
        flood_layer = geemap.ee_tile_layer(flood_col, flood_vis, name='Riesgo inundación (100 años)')
        self.map.add_layer(flood_layer)

        # NDVI MODIS actualizado
        ndvi_col = ee.ImageCollection('MODIS/061/MOD13A2').select('NDVI').mosaic()
        ndvi_vis = {'min':0, 'max':100, 'palette':['white','green']}
        ndvi_layer = geemap.ee_tile_layer(ndvi_col, ndvi_vis, name='Vegetación (NDVI)')
        self.map.add_layer(ndvi_layer)

        # Elevación SRTM
        elev_col = ee.Image("USGS/SRTMGL1_003")
        elev_vis = {'min':0, 'max':3000, 'palette':['white','sienna','brown']}
        elev_layer = geemap.ee_tile_layer(elev_col, elev_vis, name='Elevación')
        self.map.add_layer(elev_layer)

    # -----------------------------
    # 2. Agregar marcador de riesgo
    # -----------------------------
    def add_risk_marker(self, lon, lat):
        score = self.risk_model.calculate_risk(lon, lat)
        factors = self.risk_model.get_factors(lon, lat)
        policy = self.rules.suggest_policy_type(factors)
        actions = self.rules.mitigation_actions(score, factors)
        insurability = self.rules.evaluate_insurability(score)

        popup_text = f"""
        <b>Riesgo Ambiental:</b> {score}/100<br>
        <b>Asegurabilidad:</b> {insurability}<br>
        <b>Póliza recomendada:</b> {', '.join(policy)}<br>
        <b>Acciones recomendadas:</b> {', '.join(actions)}
        """

        import folium
        folium_map = folium.Map(location=self.map_center, zoom_start=self.zoom)

        folium.Marker(
            location=(lat, lon),
            popup=popup_text,
            icon=folium.Icon(color=self.score_color(score))
        ).add_to(folium_map)

        folium_map.save("mapa_riesgo.html")
        print("✅ Mapa de riesgo guardado como mapa_riesgo.html")

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

    # -----------------------------
    # 4. Mostrar mapa
    # -----------------------------
    def show_map(self):
        self.map.add_layer_control()
        return self.map

# -----------------------------
# Ejemplo de uso
# -----------------------------
if __name__ == "__main__":
    lon, lat = -99.1332, 25.6866  # Monterrey
    app = TerraGuardUI()
    app.add_risk_layers(lon, lat)
    app.add_risk_marker(lon, lat)
    app.show_map()
