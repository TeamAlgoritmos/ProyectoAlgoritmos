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
    loadPointsBtn.disabled = true;
    solveTspBtn.disabled = true;
    algorithmSelect.disabled = true;

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
        loadPointsBtn.disabled = !networkFileInput.files.length;
        algorithmSelect.disabled = !pointsFileInput.files.length;
        solveTspBtn.disabled = !algorithmSelect.value || !pointsFileInput.files.length;
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

            showStatus(`Red vial cargada con ${data.nodes.length} nodos y ${data.edges.length} conexiones`);
            pointsFileInput.disabled = false;
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
            showStatus('Por favor seleccione un archivo con los puntos de interés', true);
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
                throw new Error(data.error || 'Error al cargar los puntos');
            }

            showStatus(`${data.points.length} puntos cargados correctamente`);
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