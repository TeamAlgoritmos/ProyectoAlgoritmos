document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const loadNetworkBtn = document.getElementById('load-network');
    const loadPointsBtn = document.getElementById('load-points');
    const solveTspBtn = document.getElementById('solve-tsp');
    const resultsContainer = document.getElementById('results');
    const networkFileInput = document.getElementById('network-file');
    const pointsFileInput = document.getElementById('points-file');
    const algorithmSelect = document.getElementById('algorithm');
    const mapContainer = document.getElementById('map-container');

    // Estado inicial
    loadPointsBtn.disabled = true;
    solveTspBtn.disabled = true;
    algorithmSelect.disabled = true;

    // Mostrar mensajes de estado
    function showStatus(message, isError = false) {
        const statusElement = document.createElement('div');
        statusElement.className = isError ? 'status-error' : 'status-success';
        statusElement.innerHTML = message;
        resultsContainer.prepend(statusElement);
        setTimeout(() => statusElement.remove(), 5000);
    }

    // Actualizar estado de los controles
    function updateControls() {
        loadPointsBtn.disabled = !networkFileInput.files.length;
        algorithmSelect.disabled = !pointsFileInput.files.length;
        solveTspBtn.disabled = !algorithmSelect.value || !pointsFileInput.files.length;
    }

    // Event listeners
    networkFileInput.addEventListener('change', updateControls);
    pointsFileInput.addEventListener('change', updateControls);
    algorithmSelect.addEventListener('change', updateControls);

    // Cargar red vial
    loadNetworkBtn.addEventListener('click', async function() {
        const file = networkFileInput.files[0];
        if (!file) {
            showStatus('❌ Seleccione un archivo XML', true);
            return;
        }

        showStatus('⏳ Cargando red vial...');
        loadNetworkBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/load_network', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Error al cargar red vial');
            }

            showStatus(`✅ Red cargada: ${data.stats.nodes} nodos, ${data.stats.edges} conexiones`);
            pointsFileInput.disabled = false;
            updateControls();

        } catch (error) {
            console.error("Error:", error);
            showStatus(`❌ ${error.message}`, true);
        } finally {
            loadNetworkBtn.disabled = false;
        }
    });

    // Cargar puntos de interés
    loadPointsBtn.addEventListener('click', async function() {
        const file = pointsFileInput.files[0];
        if (!file) {
            showStatus('❌ Seleccione un archivo TSV/CSV', true);
            return;
        }

        showStatus('⏳ Cargando puntos...');
        loadPointsBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/load_points', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Error al cargar puntos');
            }

            showStatus(`✅ ${data.points_loaded} puntos cargados`);
            updateControls();

        } catch (error) {
            console.error("Error:", error);
            showStatus(`❌ ${error.message}`, true);
        } finally {
            loadPointsBtn.disabled = false;
        }
    });

    // Resolver TSP
    solveTspBtn.addEventListener('click', async function() {
        const algorithm = algorithmSelect.value;
        showStatus(`⚙️ Ejecutando ${algorithm}...`);
        solveTspBtn.disabled = true;

        try {
            const response = await fetch('/api/solve_tsp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ algorithm })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Error al ejecutar algoritmo');
            }

            // Mostrar resultados
            resultsContainer.innerHTML = `
                <div class="result-card">
                    <h3>Resultados: ${algorithm.toUpperCase()}</h3>
                    <div class="result-grid">
                        <div><strong>Ruta:</strong></div>
                        <div>${data.path.join(' → ')}</div>
                        <div><strong>Distancia total:</strong></div>
                        <div>${data.distance.toFixed(2)} metros</div>
                    </div>
                </div>
            `;

            // Mostrar mapa si hay coordenadas
            if (data.path_coordinates) {
                renderMap(data.path_coordinates);
            }

            showStatus(`✅ ${algorithm} completado`);

        } catch (error) {
            console.error("Error:", error);
            showStatus(`❌ ${error.message}`, true);
            resultsContainer.innerHTML = `
                <div class="error-card">
                    <h3>Error</h3>
                    <p>${error.message}</p>
                    <button onclick="location.reload()">Reintentar</button>
                </div>
            `;
        } finally {
            solveTspBtn.disabled = false;
        }
    });

    // Renderizar mapa (requiere Leaflet)
    function renderMap(coordinates) {
        if (typeof L === 'undefined') return;
        
        mapContainer.innerHTML = '<div id="map" style="height: 500px;"></div>';
        const map = L.map('map').setView([coordinates[0][0], coordinates[0][1]], 13);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);

        // Dibujar ruta
        const route = coordinates.map(coord => [coord[0], coord[1]]);
        L.polyline(route, {color: 'blue'}).addTo(map);
        
        // Marcadores
        coordinates.forEach((coord, i) => {
            if (i === 0 || i === coordinates.length - 1) {
                L.marker([coord[0], coord[1]])
                    .addTo(map)
                    .bindPopup(i === 0 ? 'Inicio' : 'Fin');
            }
        });
    }
});