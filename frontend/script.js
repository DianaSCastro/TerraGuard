document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Element Selectors ---
    const apiEndpoint = '/api/analyze';
    
    // Global map variables
    const mapboxToken = "sk.eyJ1Ijoic2FtdW1hbXUiLCJhIjoiY21ocjhoNmt1MTRycjJqb29xcXBlbGFwbyJ9.lDsItTFuKz9UUCyDqshagQ"; // Your token
    let dashboardMap = null;
    let currentMapMarker = null;

    // Form Selectors
    const analysisForm = document.getElementById('analysis-form');
    const latInput = document.getElementById('lat');
    const lonInput = document.getElementById('lon');
    const yearInput = document.getElementById('year');
    const analyzeBtn = document.getElementById('analyze-btn');
    const errorMessage = document.getElementById('error-message');

    // --- 2. TAB LOGIC ---
    const allTabs = document.querySelectorAll('.tab-item');
    const allTabPanels = document.querySelectorAll('.tab-content-panel');
    const dashboardTabLink = document.getElementById('tab-link-dashboard');

    allTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            
            // 1. Remove 'active' from all tabs and panels
            allTabs.forEach(t => t.classList.remove('active'));
            allTabPanels.forEach(p => p.classList.remove('active'));
            
            // 2. Add 'active' to the clicked tab
            tab.classList.add('active');
            
            // 3. Add 'active' to the corresponding panel
            const targetId = tab.dataset.target; // Gets '#content-property', etc.
            const targetPanel = document.querySelector(targetId);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }

            // 4. Map Fix: If the dashboard tab is clicked, redraw the map
            if (targetId === '#content-dashboard' && dashboardMap) {
                setTimeout(() => dashboardMap.invalidateSize(), 100);
            }
        });
    });

    // --- 3. Form Submit Handler ---
    analysisForm.addEventListener('submit', (e) => {
        e.preventDefault();
        errorMessage.textContent = '';
        
        const lat = parseFloat(latInput.value);
        const lon = parseFloat(lonInput.value);
        const year = yearInput.value ? parseInt(yearInput.value) : null;

        if (isNaN(lat) || isNaN(lon)) {
            errorMessage.textContent = "Please enter valid coordinates.";
            return;
        }

        runAnalysis(lat, lon, year);
    });

    // --- 4. Main Analysis Function ---
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
            
            // 1. Populate the (hidden) dashboard
            populateDashboard(results, lat, lon);

            // 2. SIMULATE CLICK on the Dashboard tab
            dashboardTabLink.click(); 

            // 3. Map Logic (runs after the click makes the panel visible)
            if (!dashboardMap) {
                initDashboardMap();
            }
            setTimeout(() => {
                updateMapDisplay(lat, lon, results); 
            }, 100);


        } catch (error) {
            console.error('Analysis Error:', error);
            errorMessage.textContent = `Error: ${error.message}`;
        } finally {
            setLoading(false);
        }
    }

    // --- 5. Dashboard Population Functions (UPDATED) ---
    function populateDashboard(results, lat, lon) {
        const riskGeneral = results.risk_percent || 0;
        const metrics = results.metrics_percent || {};
        
        // General Risk Card (UPDATED)
        const generalCard = document.getElementById('result-riesgo-general-card');
        
        // This line updates the text "Low Level", "Medium Level", etc.
        document.getElementById('result-riesgo-general-level').textContent = getRiskLevelText(riskGeneral);
        
        // Assign color class to general card
        generalCard.className = 'card card-riesgo-general'; // Reset
        generalCard.classList.add(getRiskClass(riskGeneral));

        // Individual Metric Cards (Unchanged)
        updateMetricCard('sismico', metrics.seismic);
        updateMetricCard('inundacion', metrics.flood);
        updateMetricCard('huracan', metrics.hurricane);
        updateMetricCard('incendio', metrics.fire);
        updateMetricCard('precipitacion', metrics.precipitation);
        updateMetricCard('vegetacion', metrics.vegetation);
        
        // AI Analysis Card (Unchanged)
        // This function already includes the % in the text, as per the mockup
        document.getElementById('result-ai-summary').textContent = generateAIText(results);
    }

    /**
     * Updates a metric card (percentage and progress bar)
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
     * Generates simple dynamic text for the AI card
     */
    function generateAIText(results) {
        const riskGeneral = results.risk_percent || 0;
        const level = getRiskLevelText(riskGeneral).toUpperCase();
        
        let summary = `The risk analysis for the property indicates a ${level} RISK level (${riskGeneral.toFixed(0)}%). `;
        
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
            summary += `A special attention factor has been identified: ${translateMetric(highestRiskName)} (${highestRiskValue.toFixed(0)}%). `;
            summary += "Insurance is feasible, but adjusting the premium and considering specific clauses for this event is recommended. Periodic evaluation every 6 months.";
        } else if (level === 'MEDIUM') {
            summary += "Natural event frequency parameters show moderate levels. Climatic conditions require continuous monitoring. A standard premium with annual review is recommended.";
        } else {
            summary += "All parameters are within low and controlled levels. A preferential standard premium is recommended. Periodic evaluation every 12 months.";
        }
        return summary;
    }


    // --- 6. MAP FUNCTIONS ---

    /**
     * Initializes the Leaflet map in the 'map-dashboard' div.
     * Only runs once.
     */
    function initDashboardMap() {
        dashboardMap = L.map('map-dashboard', {
            zoomControl: false 
        }).setView([19.43, -99.13], 10); // Generic initial view

        L.tileLayer(
            `https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=${mapboxToken}`, {
                attribution: 'Mapbox Satellite', // Mapbox attribution
                tileSize: 512,
                zoomOffset: -1
            }
        ).addTo(dashboardMap);
    }

    /**
     * Updates the map with the new location and risk marker.
     */
    function updateMapDisplay(lat, lon, results) {
        if (!dashboardMap) return;

        // Fix to ensure the map redraws correctly
        dashboardMap.invalidateSize();
        
        dashboardMap.setView([lat, lon], 14);

        if (currentMapMarker) {
            dashboardMap.removeLayer(currentMapMarker);
        }

        const riskGeneral = results.risk_percent || 0;
        const metrics = results.metrics_percent || {};
        const riskClass = getRiskClass(riskGeneral);
        
        const popupText = `
            <b>📍 Coordinates:</b> (${lat.toFixed(6)}, ${lon.toFixed(6)})<br>
            <b>🌡️ General Risk: <span class="${riskClass}">${riskGeneral.toFixed(1)}%</span></b><hr>
            <b>📊 Risk Metrics:</b><br>
            🔹 Seismic: ${metrics.seismic?.toFixed(1) || 0}%<br>
            🔹 Flood: ${metrics.flood?.toFixed(1) || 0}%<br>
            🔹 Hurricane: ${metrics.hurricane?.toFixed(1) || 0}%<br>
            🔹 Wildfire: ${metrics.fire?.toFixed(1) || 0}%<br>
            🔹 Precipitation: ${metrics.precipitation?.toFixed(1) || 0}%<br>
            🔹 Vegetation: ${metrics.vegetation?.toFixed(1) || 0}%<br>
        `;

        currentMapMarker = L.marker([lat, lon])
            .addTo(dashboardMap)
            .bindPopup(popupText)
            .openPopup(); 
    }


    // --- 7. Utility Functions ---
    
    function setLoading(isLoading) {
        if (isLoading) {
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = `
                <span class="material-icons-outlined spin-animation">autorenew</span>
                Analyzing...
            `;
        } else {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = `
                <span class="material-icons-outlined">send</span>
                Generate Risk Analysis
            `;
        }
    }

    function getRiskClass(score) {
        if (score <= 30) return 'risk-low';
        if (score <= 60) return 'risk-medium';
        return 'risk-high';
    }

    function getRiskLevelText(score) {
        if (score <= 30) return 'Low Level';
        if (score <= 60) return 'Medium Level';
        return 'High Level';
    }
    
    function translateMetric(key) {
        const map = {
            'seismic': 'Seismic Risk',
            'flood': 'Flood Risk',
            'hurricane': 'Hurricane Risk',
            'fire': 'Wildfire Risk',
            'precipitation': 'Precipitation Risk',
            'vegetation': 'Vegetation Risk'
        };
        return map[key] || key;
    }
});