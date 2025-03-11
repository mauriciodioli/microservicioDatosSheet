function loadHistorial() {
    var workflowId = document.getElementById('workflowId').value;
    
    if (workflowId === '') {
        alert('Por favor, ingresa un ID de workflow');
        return;
    }

    // Hacer la petición AJAX al backend
    fetch(`/get_historial/${workflowId}`, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        // Limpiar la tabla antes de mostrar los nuevos resultados
        var tableBody = document.querySelector('#historialTable tbody');
        tableBody.innerHTML = '';

        // Insertar los datos en la tabla
        data.forEach(item => {
            var row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.id}</td>
                <td>${item.fecha}</td>
                <td>${item.estado}</td>
                <td>${JSON.stringify(item.resultado)}</td>
                <td>${item.intentos}</td>
            `;
            tableBody.appendChild(row);
        });
    })
    .catch(error => {
        console.error('Error al cargar el historial:', error);
        alert('Hubo un error al cargar el historial');
    });
}
