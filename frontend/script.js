document.addEventListener('DOMContentLoaded', () => {

    // --- Configuración Inicial ---
    const mapboxToken = "sk.eyJ1Ijoic2FtdW1hbXUiLCJhIjoiY21ocjhoNmt1MTRycjJqb29xcXBlbGFwbyJ9.lDsItTFuKz9UUCyDqshagQ";
    const mapCenter = [25.6866, -100.3161]; // Monterrey (Lat, Lon)
    const apiEndpoint = '/api/analyze'; // URL de tu API Flask

    // Formulario y botón
    const analysisForm = document.getElementById('analysis-form');
    const analyzeBtn = document.getElementById('analyze-btn');
    const resultsContainer = document.getElementById('results-container');
    const latInput = document.getElementById('lat');
    const lonInput = document.getElementById('lon');
    const yearInput = document.getElementById('year');

    let currentMarker = null; // Para guardar el marcador actual

    // --- 1. Inicializar Mapa Leaflet ---
    const map = L.map('map').setView(mapCenter, 12);

    L.tileLayer(
        `https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=${mapboxToken}`, {
            attribution: 'Mapbox Satellite',
            tileSize: 512,
            zoomOffset: -1
        }
    ).addTo(map);

    // --- 2. Manejador de Eventos del Formulario ---
    analysisForm.addEventListener('submit', (e) => {
        e.preventDefault(); // Evitar que la página se recargue

        const lat = parseFloat(latInput.value);
        const lon = parseFloat(lonInput.value);
        const year = yearInput.value ? parseInt(yearInput.value) : null;

        if (isNaN(lat) || isNaN(lon)) {
            alert("Por favor, introduce coordenadas válidas.");
            return;
        }

        // Llamar a la función de análisis
        runAnalysis(lat, lon, year);
    });

    // --- 3. Permitir análisis al hacer clic en el mapa ---
    map.on('click', (e) => {
        const { lat, lng } = e.latlng;
        
        // Actualizar formulario
        latInput.value = lat.toFixed(6);
        lonInput.value = lng.toFixed(6);
        
        // Ejecutar análisis (con el año que esté en el input)
        const year = yearInput.value ? parseInt(yearInput.value) : null;
        runAnalysis(lat, lng, year);
    });

    // --- 4. Función Principal: Llamar a la API y Mostrar Resultados ---
    async function runAnalysis(lat, lon, year) {
        
        // Mostrar estado de carga
        setLoading(true);

        try {
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    lat: lat,
                    lon: lon,
                    year: year
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Error ${response.status}`);
            }

            const results = await response.json();
            
            // Mostrar los resultados
            displayResults(lat, lon, results);
            map.setView([lat, lon], 14); // Centrar mapa en la nueva ubicación

        } catch (error) {
            console.error('Error en el análisis:', error);
            resultsContainer.innerHTML = `<p style="color:red;"><b>Error:</b> ${error.message}</p>`;
        } finally {
            // Quitar estado de carga
            setLoading(false);
        }
    }

    // --- 5. Funciones de Utilidad (Frontend) ---

    // Función para mostrar/ocultar estado de carga
    function setLoading(isLoading) {
        if (isLoading) {
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = 'Analizando...';
            resultsContainer.innerHTML = '<p>Cargando reporte...</p>';
        } else {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analizar Ubicación';
        }
    }

    // Función para determinar el color (re-implementada de tu Python)
    function getRiskClass(score) {
        if (score <= 30) return 'risk-low';
        if (score <= 60) return 'risk-medium';
        return 'risk-high';
    }

    // Función para mostrar resultados en el mapa y panel
    function displayResults(lat, lon, results) {
        const riskGeneral = results.risk_percent || 0;
        const metrics = results.metrics_percent || {};
        const raw = results.raw_factors || {};

        // a. Crear el texto para el Popup (similar a tu Python)
        const riskClass = getRiskClass(riskGeneral);
        const popupText = `
            <b>📍 Coordenadas:</b> (${lat.toFixed(6)}, ${lon.toFixed(6)})<br>
            <b>🌡️ Riesgo general: <span class="${riskClass}">${riskGeneral.toFixed(1)}%</span></b><hr>
            <b>📊 Riesgos por métrica:</b><br>
            🔹 Sísmico: ${metrics.seismic?.toFixed(1) || 0}%<br>
            🔹 Inundación: ${metrics.flood?.toFixed(1) || 0}%<br>
            🔹 Huracán: ${metrics.hurricane?.toFixed(1) || 0}%<br>
            🔹 Incendio: ${metrics.fire?.toFixed(1) || 0}%<br>
            🔹 Precipitación: ${metrics.precipitation?.toFixed(1) || 0}%<br>
            🔹 Vegetación: ${metrics.vegetation?.toFixed(1) || 0}%<br>
        `;

        // b. Actualizar el marcador en el mapa
        if (currentMarker) {
            map.removeLayer(currentMarker); // Quitar marcador anterior
        }
        
        currentMarker = L.marker([lat, lon])
            .addTo(map)
            .bindPopup(popupText)
            .openPopup(); // Abrir popup automáticamente

        // c. Actualizar el panel de resultados
        resultsContainer.innerHTML = popupText; // Reutilizamos el mismo HTML
    }

});