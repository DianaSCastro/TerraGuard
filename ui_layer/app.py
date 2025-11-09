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
        # 🔁 Capa de respaldo (OpenStreetMap) en caso de error con Mapbox
        #folium.TileLayer(
         #   'OpenStreetMap',
          #  name='Respaldo OSM'
            
        #).add_to(self.map)





    # -----------------------------
    # 1. Agregar capas (con opacidad baja)
    # -----------------------------
    def add_risk_layers(self, lon, lat):
        # Inundación
        flood_col = ee.ImageCollection("JRC/CEMS_GLOFAS/FloodHazard/v2_1").mosaic().select('RP100_depth_category')
        flood_vis = {'min': 1, 'max': 5, 'palette': ['#ffffff'], 'opacity': 0.05}
        flood_url = flood_col.getMapId(flood_vis)['tile_fetcher'].url_format
        folium.TileLayer(
            tiles=flood_url,
            attr='EE Flood',
            name='Riesgo inundación (100 años)',
            overlay=True,
            control=True,
            show=False,  # No se muestra por defecto
            opacity=0.05
        ).add_to(self.map)

        # NDVI
        ndvi_col = ee.ImageCollection('MODIS/061/MOD13A2').select('NDVI').mosaic()
        ndvi_vis = {'min': 0, 'max': 100, 'palette': ['#ffffff'], 'opacity': 0.05}
        ndvi_url = ndvi_col.getMapId(ndvi_vis)['tile_fetcher'].url_format
        folium.TileLayer(
            tiles=ndvi_url,
            attr='EE NDVI',
            name='Vegetación (NDVI)',
            overlay=True,
            control=True,
            show=False,
            opacity=0.05
        ).add_to(self.map)

        # Elevación
        elev_col = ee.Image("USGS/SRTMGL1_003")
        elev_vis = {'min': 0, 'max': 3000, 'palette': ['#ffffff'], 'opacity': 0.05}
        elev_url = elev_col.getMapId(elev_vis)['tile_fetcher'].url_format
        folium.TileLayer(
            tiles=elev_url,
            attr='EE Elevación',
            name='Elevación',
            overlay=True,
            control=True,
            show=False,
            opacity=0.05
        ).add_to(self.map)

        print("✅ Capas agregadas al control, mapa Mapbox visible por defecto")

    # -----------------------------
    # 2. Agregar marcador
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

        folium.Marker(
            location=[lat, lon],
            popup=popup_text,
            icon=folium.Icon(color=self.score_color(score))
        ).add_to(self.map)

        print("📍 Marcador de riesgo agregado")

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
    app.show_map()
