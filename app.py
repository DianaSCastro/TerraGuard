import ee
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS  # Aún útil para desarrollo local

# Asumiendo que tus módulos están en las carpetas correctas
from processing_layer.risk_model import RiskModel
from business_layer.rules import InsuranceRules
from data_layer.data2 import DataLayer

# --- Inicialización Global ---
try:
    ee.Initialize(project='terraguard-477621')
    print("🌍 Earth Engine funcionando correctamente")
except Exception as e:
    print(f"Error inicializando Earth Engine: {e}")

risk_model = RiskModel()

# --- Configuración de Flask ---

# 💡 **CAMBIO 1: Indicar a Flask dónde están los archivos del frontend**
app = Flask(__name__,
            static_folder="frontend",       # Carpeta para archivos estáticos (css, js)
            template_folder="frontend")     # Carpeta para plantillas (html)

# Habilitar CORS. Aunque Flask sirve todo, es buena práctica
# mantenerlo por si pruebas el index.html como archivo local.
CORS(app)


# --- Funciones de Utilidad (Sin cambios) ---
def validate_coords(lon, lat):
    """
    Si el usuario ingresó lat/lon invertidos (caso común),
    intenta detectarlo e invertirlos automáticamente.
    """
    if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
        if -180 <= lat <= 180 and -90 <= lon <= 90:
            print("⚠️ Detectadas coordenadas invertidas; intercambiando valores (lat<->lon).")
            return lat, lon
        else:
            raise ValueError(f"Coordenadas inválidas: lon={lon}, lat={lat}")
    return lon, lat

# --- Endpoints de la API ---

# 💡 **CAMBIO 2: Nueva ruta para servir la página principal**
@app.route('/')
def index():
    """Sirve el archivo index.html del frontend."""
    return render_template('index.html')

# 💡 (Opcional pero recomendado) Ruta para servir archivos estáticos dinámicamente
# Esto ya debería funcionar con 'static_folder', pero es una garantía.
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)


@app.route('/api/analyze', methods=['POST'])
def analyze_location_api():
    """
    Endpoint de la API para analizar una ubicación.
    (Esta función no cambia en absoluto)
    """
    data = request.get_json()
    if not data or 'lat' not in data or 'lon' not in data:
        return jsonify({"error": "Faltan 'lat' y 'lon' en el JSON body"}), 400

    try:
        lon_in = float(data['lon'])
        lat_in = float(data['lat'])
        target_year_input = data.get('year')
        target_year = int(target_year_input) if target_year_input else None

        lon, lat = validate_coords(lon_in, lat_in)

        if target_year:
            print(f"📍 Analizando API request: (lat={lat}, lon={lon}) para año {target_year}...")
        else:
            print(f"📍 Analizando API request: (lat={lat}, lon={lon}) con datos actuales...")

        result = risk_model.calculate_risk_with_breakdown(lon, lat, target_year=target_year)
        return jsonify(result)

    except ValueError as e:
        print(f"ERROR (ValueError): {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"ERROR (Exception): {e}")
        return jsonify({"error": f"Error interno del servidor: {e}"}), 500

# --- Ejecutar el Servidor ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)