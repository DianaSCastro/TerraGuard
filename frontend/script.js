document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Selectores de Elementos ---
    const apiEndpoint = '/api/analyze';
    
    // Variables globales para el mapa
    const mapboxToken = "sk.eyJ1Ijoic2FtdW1hbXUiLCJhIjoiY21ocjhoNmt1MTRycjJqb29xcXBlbGFwbyJ9.lDsItTFuKz9UUCyDqshagQ"; // Tu token
    let dashboardMap = null;
    let currentMapMarker = null;

    // Vistas
    const formView = document.getElementById('form-view');
    const dashboardView = document.getElementById('dashboard-view');

    // Formulario
    const analysisForm = document.getElementById('analysis-form');
    const latInput = document.getElementById('lat');
    const lonInput = document.getElementById('lon');
    const yearInput = document.getElementById('year');
    const analyzeBtn = document.getElementById('analyze-btn');
    const errorMessage = document.getElementById('error-message');

    // Botón para volver
    const backToFormBtn = document.getElementById('back-to-form-btn');

    // --- 2. Manejadores de Eventos ---

    analysisForm.addEventListener('submit', (e) => {
        e.preventDefault();
        errorMessage.textContent = ''; // Limpiar errores
        
        const lat = parseFloat(latInput.value);
        const lon = parseFloat(lonInput.value);
        const year = yearInput.value ? parseInt(yearInput.value) : null;

        if (isNaN(lat) || isNaN(lon)) {
            errorMessage.textContent = "Por favor, introduce coordenadas válidas.";
            return;
        }

        runAnalysis(lat, lon, year);
    });

    backToFormBtn.addEventListener('click', () => {
        dashboardView.style.display = 'none';
        formView.style.display = 'block';
    });

    // --- 3. Función Principal de Análisis ---
    async function runAnalysis(lat, lon, year) {
        setLoading(true);

        try {
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lat, lon, year })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Error ${response.status}`);
            }

            const results = await response.json();
            
            // ¡Éxito! Poblar el dashboard y cambiar de vista
            populateDashboard(results, lat, lon);
            formView.style.display = 'none';
            dashboardView.style.display = 'grid'; // 'grid' para que coincida con el CSS

            // LÓGICA DEL MAPA: Inicializar (si es la primera vez) y actualizar
            if (!dashboardMap) {
                initDashboardMap();
            }
            // Retraso breve para asegurar que el div es visible antes de dibujar el mapa
            setTimeout(() => {
                updateMapDisplay(lat, lon, results); 
            }, 100);


        } catch (error) {
            console.error('Error en el análisis:', error);
            errorMessage.textContent = `Error: ${error.message}`;
        } finally {
            setLoading(false);
        }
    }

    // --- 4. Funciones de "Poblado" del Dashboard ---

    function populateDashboard(results, lat, lon) {
        const riskGeneral = results.risk_percent || 0;
        const metrics = results.metrics_percent || {};
        
        // Tarjeta de Riesgo General
        const generalCard = document.getElementById('result-riesgo-general-card');
        document.getElementById('result-riesgo-general-pct').textContent = `${riskGeneral.toFixed(0)}%`;
        document.getElementById('result-riesgo-general-level').textContent = getRiskLevelText(riskGeneral);
        
        // Asignar clase de color a la tarjeta general
        generalCard.className = 'card card-riesgo-general'; // Reset
        generalCard.classList.add(getRiskClass(riskGeneral));

        // Tarjetas de Métricas Individuales
        updateMetricCard('sismico', metrics.seismic);
        updateMetricCard('inundacion', metrics.flood);
        updateMetricCard('huracan', metrics.hurricane);
        updateMetricCard('incendio', metrics.fire);
        updateMetricCard('precipitacion', metrics.precipitation);
        updateMetricCard('vegetacion', metrics.vegetation);
        
        // Tarjeta de Análisis AI
        document.getElementById('result-ai-summary').textContent = generateAIText(results);
    }

    /**
     * Actualiza una tarjeta de métrica (porcentaje y barra de progreso)
     */
    function updateMetricCard(name, value) {
        const score = value || 0;
        const pctElement = document.getElementById(`result-${name}-pct`);
        const progressElement = document.getElementById(`progress-${name}`);

        if (pctElement) pctElement.textContent = `${score.toFixed(0)}%`;
        if (progressElement) {
            progressElement.value = score;
            progressElement.className = ''; // Reset
            progressElement.classList.add(getRiskClass(score));
        }
    }

    /**
     * Genera un texto dinámico simple para la tarjeta de AI
     */
    function generateAIText(results) {
        const riskGeneral = results.risk_percent || 0;
        const level = getRiskLevelText(riskGeneral).toUpperCase();
        
        let summary = `El análisis de riesgo para la propiedad indica un nivel de RIESGO ${level} (${riskGeneral.toFixed(0)}%). `;
        
        const metrics = results.metrics_percent || {};
        let highestRiskName = '';
        let highestRiskValue = 0;

        for (const [key, value] of Object.entries(metrics)) {
            if (value > highestRiskValue) {
                highestRiskValue = value;
                highestRiskName = key;
            }
        }

        if (highestRiskValue > 50) {
            summary += `Se ha identificado un factor de atención especial: ${traducirMetrica(highestRiskName)} (${highestRiskValue.toFixed(0)}%). `;
            summary += "Es factible el aseguramiento, pero se recomienda ajustar la prima y considerar cláusulas específicas para este evento. Evaluación periódica cada 6 meses.";
        } else if (level === 'MEDIO') {
            summary += "Los parámetros de frecuencia de eventos naturales muestran niveles moderados. Las condiciones climáticas requieren monitoreo continuo. Se recomienda una prima estándar con revisión anual.";
        } else {
            summary += "Todos los parámetros se encuentran dentro de niveles bajos y controlados. Se recomienda una prima estándar preferencial. Evaluación periódica cada 12 meses.";
        }
        return summary;
    }


    // --- 5. FUNCIONES PARA EL MAPA ---

    /**
     * Inicializa el mapa Leaflet en el div 'map-dashboard'.
     * Solo se ejecuta una vez.
     */
    function initDashboardMap() {
        dashboardMap = L.map('map-dashboard', {
            zoomControl: false 
        }).setView([19.43, -99.13], 10); // Vista inicial genérica

        L.tileLayer(
            `https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=${mapboxToken}`, {
                attribution: 'Mapbox Satellite',
                tileSize: 512,
                zoomOffset: -1
            }
        ).addTo(dashboardMap);
    }

    /**
     * Actualiza el mapa con la nueva ubicación y el marcador de riesgo.
     */
    function updateMapDisplay(lat, lon, results) {
        if (!dashboardMap) return;

        // Arreglo para asegurar que el mapa se redibuja correctamente
        dashboardMap.invalidateSize();
        
        dashboardMap.setView([lat, lon], 14);

        if (currentMapMarker) {
            dashboardMap.removeLayer(currentMapMarker);
        }

        const riskGeneral = results.risk_percent || 0;
        const metrics = results.metrics_percent || {};
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

        currentMapMarker = L.marker([lat, lon])
            .addTo(dashboardMap)
            .bindPopup(popupText)
            .openPopup(); 
    }


    // --- 6. Funciones de Utilidad ---
    
    /**
     * ESTA ES LA FUNCIÓN CORREGIDA
     */
    function setLoading(isLoading) {
        if (isLoading) {
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = `
                <span class="material-icons-outlined spin-animation">autorenew</span>
                Analizando...
            `;
        } else {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = `
                <span class="material-icons-outlined">send</span>
                Generar Análisis de Riesgo
            `;
        }
        // Ya no hay código problemático aquí
    }

    function getRiskClass(score) {
        if (score <= 30) return 'risk-low';
        if (score <= 60) return 'risk-medium';
        return 'risk-high';
    }

    function getRiskLevelText(score) {
        if (score <= 30) return 'Nivel Bajo';
        if (score <= 60) return 'Nivel Medio';
        return 'Nivel Alto';
    }
    
    function traducirMetrica(key) {
        const map = {
            'seismic': 'Riesgo Sísmico',
            'flood': 'Riesgo de Inundación',
            'hurricane': 'Riesgo de Huracanes',
            'fire': 'Riesgo de Incendios',
            'precipitation': 'Riesgo por Precipitación',
            'vegetation': 'Riesgo por Vegetación'
        };
        return map[key] || key;
    }
});