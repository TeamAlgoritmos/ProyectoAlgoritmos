document.addEventListener('DOMContentLoaded', function() {
    console.log('Frontend cargado correctamente');
    
    // Elementos del DOM
    const loadNetworkBtn = document.getElementById('load-network');
    const loadPointsBtn = document.getElementById('load-points');
    const solveTspBtn = document.getElementById('solve-tsp');
    const resultsContainer = document.getElementById('results');
    const networkFileInput = document.getElementById('network-file');
    const pointsFileInput = document.getElementById('points-file');
    const algorithmSelect = document.getElementById('algorithm');

    // Estado inicial
    solveTspBtn.disabled = true;
    algorithmSelect.disabled = true;
    let networkData = null;
    let pointsData = null;

    // Mostrar mensaje de estado
    function showStatus(message, isError = false) {
        const statusElement = document.createElement('div');
        statusElement.className = isError ? 'status-error' : 'status-success';
        statusElement.textContent = message;
        resultsContainer.prepend(statusElement);
        setTimeout(() => statusElement.remove(), 5000);
    }

    // Habilitar/deshabilitar controles
    function updateControls() {
        const networkLoaded = !!networkData;
        const pointsLoaded = !!pointsData;
        
        pointsFileInput.disabled = !networkLoaded;
        loadPointsBtn.disabled = !networkLoaded;
        algorithmSelect.disabled = !networkLoaded || !pointsLoaded;
        solveTspBtn.disabled = !networkLoaded || !pointsLoaded || !algorithmSelect.value;
    }

    // Event listeners para cambios
    networkFileInput.addEventListener('change', updateControls);
    pointsFileInput.addEventListener('change', updateControls);
    algorithmSelect.addEventListener('change', updateControls);

    // Cargar red vial
    loadNetworkBtn.addEventListener('click', async function() {
        const file = networkFileInput.files[0];
        if (!file) {
            showStatus('Por favor seleccione un archivo CSV para la red vial', true);
            return;
        }

        showStatus('Cargando red vial...');
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
                throw new Error(data.error || 'Error al cargar la red vial');
            }

            networkData = data;
            showStatus(`Red vial cargada (${data.nodes.length} nodos)`);
            updateControls();

        } catch (error) {
            console.error('Error:', error);
            showStatus(error.message, true);
        } finally {
            loadNetworkBtn.disabled = false;
        }
    });

    // Cargar puntos de interés
    loadPointsBtn.addEventListener('click', async function() {
        const file = pointsFileInput.files[0];
        if (!file) {
            showStatus('Por favor seleccione un archivo CSV para los puntos de interés', true);
            return;
        }

        showStatus('Cargando puntos de interés...');
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
                throw new Error(data.error || 'Error al cargar los puntos de interés');
            }

            pointsData = data;
            showStatus(`Puntos de interés cargados (${data.points.length} puntos)`);
            
            // Mostrar puntos en el mapa
            if (data.points && data.points.length > 0) {
                initMap(data.points[0].Y, data.points[0].X);
                addMarkersToMap(data.points);
                drawNetworkBoundary(networkData);
            }

            updateControls();

        } catch (error) {
            console.error('Error:', error);
            showStatus(error.message, true);
        } finally {
            loadPointsBtn.disabled = false;
        }
    });

    // Resolver TSP
    solveTspBtn.addEventListener('click', async function() {
        const algorithm = algorithmSelect.value;
        if (!algorithm) {
            showStatus('Por favor seleccione un algoritmo', true);
            return;
        }

        showStatus(`Ejecutando algoritmo ${algorithm}...`);
        solveTspBtn.disabled = true;

        try {
            const response = await fetch('/api/solve_tsp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ algorithm })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Error al ejecutar el algoritmo');
            }

            // Mostrar resultados
            resultsContainer.innerHTML = `
                <div class="result-card">
                    <h3>Resultados: ${data.algorithm}</h3>
                    <p><strong>Ruta:</strong> ${data.path}</p>
                    <p><strong>Distancia:</strong> ${data.distance} unidades</p>
                    <p><strong>Tiempo:</strong> ${data.execution_time_ms} ms</p>
                    <p><strong>Nodos:</strong> ${data.nodes_visited}</p>
                    <p><strong>Eficiencia:</strong> ${data.efficiency} unidades/ms</p>
                </div>
            `;
            
            showStatus(`Algoritmo ${algorithm} completado exitosamente`);
        } catch (error) {
            console.error('Error:', error);
            showStatus(error.message, true);
            resultsContainer.innerHTML = `
                <div class="error-card">
                    <h3>Error en ${algorithm}</h3>
                    <p>${error.message}</p>
                    <p>Ver la consola para más detalles (F12)</p>
                </div>
            `;
        } finally {
            solveTspBtn.disabled = false;
        }
    });
});

// Inicializar el mapa
let map = null;
let markers = [];
let boundaryPolygon = null;

function initMap(latitude, longitude) {
    if (map !== null) {
        map.remove();
    }
    map = L.map('map').setView([latitude, longitude], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}

// Añadir marcadores al mapa
function addMarkersToMap(points) {
    // Limpiar marcadores existentes
    markers.forEach(marker => marker.remove());
    markers = [];

    points.forEach(point => {
        const marker = L.marker([point.Y, point.X])
            .bindPopup(`<b>Punto ID: ${point.id}</b>`);
        markers.push(marker);
        marker.addTo(map);
    });

    // Ajustar el mapa para que se vean todos los marcadores
    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds());
    }
}

// Dibujar el límite de la red
function drawNetworkBoundary(networkData) {
    if (boundaryPolygon) {
        map.removeLayer(boundaryPolygon);
    }

    // Obtener las coordenadas extremas de la red
    const points = networkData.points || [];
    if (points.length === 0) return;

    const bounds = points.reduce((acc, point) => {
        return {
            minLat: Math.min(acc.minLat, point.Y),
            maxLat: Math.max(acc.maxLat, point.Y),
            minLng: Math.min(acc.minLng, point.X),
            maxLng: Math.max(acc.maxLng, point.X)
        };
    }, {
        minLat: points[0].Y,
        maxLat: points[0].Y,
        minLng: points[0].X,
        maxLng: points[0].X
    });

    // Crear el polígono que enmarca la red
    const polygonPoints = [
        [bounds.minLat, bounds.minLng],
        [bounds.minLat, bounds.maxLng],
        [bounds.maxLat, bounds.maxLng],
        [bounds.maxLat, bounds.minLng]
    ];

    boundaryPolygon = L.polygon(polygonPoints, {
        color: 'red',
        fillColor: '#f03',
        fillOpacity: 0.1
    }).addTo(map);

    // Ajustar el mapa para mostrar todo el polígono
    map.fitBounds(boundaryPolygon.getBounds());
}

// La carga inicial del mapa ahora se hace despues de cargar los puntos de interes
// La funcion loadAndDisplayMapPoints() ya no es necesaria para la carga inicial de la pagina
// Se mantiene porque podria ser util para refactorizacion futura o si se desea
// cargar los puntos del mapa desde otra fuente en algun momento.
async function loadAndDisplayMapPoints_deprecated() {
    try {
        // Este endpoint ya no se usa para la carga inicial
        // Los datos para el mapa ahora vienen con la carga de puntos de interes
        console.log('Esta funcion loadAndDisplayMapPoints_deprecated no se usa para la carga inicial.');
        /*
        const response = await fetch('/api/map_points');
        const points = await response.json();

        if (!response.ok) {
            throw new Error(points.error || 'Error al cargar puntos del mapa');
        }

        if (points.length > 0) {
            // Inicializar mapa con las coordenadas del primer punto
            initMap(points[0].Y, points[0].X);
            // Añadir todos los puntos como marcadores
            addMarkersToMap(points);
        } else {
            showStatus('No se encontraron puntos con coordenadas para mostrar en el mapa.', true);
        }
        */

    } catch (error) {
        console.error('Error en loadAndDisplayMapPoints_deprecated:', error);
    }
}

// La llamada a loadAndDisplayMapPoints() al cargar la pagina ya no es necesaria
// loadAndDisplayMapPoints();