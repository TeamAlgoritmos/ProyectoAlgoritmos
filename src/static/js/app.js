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
    let map = null;
    let routeLayer = null;
    let markersLayer = null;
    let roadNetworkLayer = null;

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

    // Inicializar mapa
    function initMap() {
        if (map) {
            map.remove();
        }
        map = L.map('map').setView([0, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
    }

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
            initMap();

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
        const params = {};
        
        if (algorithm === 'genetic') {
            params.population_size = parseInt(document.getElementById('population-size').value);
            params.generations = parseInt(document.getElementById('generations').value);
            params.mutation_rate = parseInt(document.getElementById('mutation-rate').value) / 100;
        }

        showStatus(`⚙️ Ejecutando ${algorithm}...`);
        solveTspBtn.disabled = true;

        try {
            const response = await fetch('/api/solve_tsp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ algorithm, ...params })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Error en el algoritmo');

            // Renderizar resultados
            renderResults(data, algorithm);
            renderMap(data);

        } catch (error) {
            console.error("Error:", error);
            showStatus(`❌ ${error.message}`, true);
            resultsContainer.innerHTML = `
                <div class="error-card">
                    <h3>Error</h3>
                    <p>${error.message}</p>
                    <button class="retry-btn" onclick="location.reload()">Reintentar</button>
                </div>
            `;
        } finally {
            solveTspBtn.disabled = false;
        }
    });

    // Renderizar resultados
    function renderResults(data, algorithm) {
        resultsContainer.innerHTML = `
            <div class="result-card">
                <h3>Resultados: ${algorithm.replace('_', ' ').toUpperCase()}</h3>
                <div class="result-grid">
                    <div>Ruta optimizada:</div>
                    <div>${data.path.join(' → ')}</div>
                    <div>Distancia total:</div>
                    <div>${data.distance.toFixed(2)} metros</div>
                    <div>Tiempo de ejecución:</div>
                    <div>${data.execution_time ? data.execution_time.toFixed(2) + ' segundos' : 'N/A'}</div>
                </div>
            </div>
        `;
    }

    // Renderizar mapa
    function renderMap(data) {
        if (!map) initMap();

        // Limpiar capas anteriores
        if (routeLayer) map.removeLayer(routeLayer);
        if (markersLayer) map.removeLayer(markersLayer);
        if (roadNetworkLayer) map.removeLayer(roadNetworkLayer);

        // Centrar mapa en la ruta
        const center = data.center || [data.path_coordinates[0][0], data.path_coordinates[0][1]];
        map.setView(center, 15);

        // Dibujar red vial (si existe)
        if (data.visualization_data?.graph_edges) {
            roadNetworkLayer = L.layerGroup();
            data.visualization_data.graph_edges.forEach(edge => {
                const line = L.polyline(
                    edge.geometry.coordinates.map(coord => [coord[1], coord[0]]),
                    { color: edge.properties.color || '#cccccc', weight: 2 }
                );
                roadNetworkLayer.addLayer(line);
            });
            roadNetworkLayer.addTo(map);
        }

        // Dibujar puntos de interés (si existen)
        if (data.visualization_data?.points) {
            markersLayer = L.layerGroup();
            data.visualization_data.points.forEach((point, index) => {
                const marker = L.circleMarker(
                    [point.geometry.coordinates[1], point.geometry.coordinates[0]],
                    {
                        radius: 6,
                        fillColor: point.properties.color || (index === 0 ? '#2ecc71' : '#e74c3c'),
                        color: '#fff',
                        weight: 1,
                        fillOpacity: 1
                    }
                ).bindPopup(point.properties.popup || `Punto ${index + 1}`);
                markersLayer.addLayer(marker);
            });
            markersLayer.addTo(map);
        }

        // Dibujar ruta óptima
        if (data.path_coordinates) {
            const routeCoords = data.path_coordinates.map(coord => [coord[0], coord[1]]);
            routeLayer = L.polyline(routeCoords, {
                color: '#3498db',
                weight: 4,
                opacity: 1,
                dashArray: '0',
                lineJoin: 'round'
            }).addTo(map);

            // Añadir marcadores de inicio/fin
            L.marker([routeCoords[0][0], routeCoords[0][1]], {
                icon: L.divIcon({
                    className: 'start-marker',
                    html: '🏁',
                    iconSize: [25, 25]
                })
            }).addTo(map).bindPopup('Punto de inicio');

            L.marker([routeCoords[routeCoords.length-1][0], routeCoords[routeCoords.length-1][1]], {
                icon: L.divIcon({
                    className: 'end-marker',
                    html: '⛳',
                    iconSize: [25, 25]
                })
            }).addTo(map).bindPopup('Punto final');

            // Ajustar vista para mostrar toda la ruta
            map.fitBounds(routeCoords);
        }
    }

    // Inicializar el mapa al cargar la página
    initMap();

    // Event listeners
    networkFileInput.addEventListener('change', updateControls);
    pointsFileInput.addEventListener('change', updateControls);
    algorithmSelect.addEventListener('change', updateControls);
});