function triggerEvent() {
    const eventType = document.getElementById("eventType").value;
    const eventData = document.getElementById("eventData").value;
    const user_id = 1;  // Aquí defines el user_id

    fetch("/trigger_event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            tipo: eventType,
            datos: { message: eventData },
            user_id: user_id  // Agregamos el user_id al cuerpo de la solicitud
        })
    })
    .then(response => response.json())
    .then(data => {
        alert("Evento enviado: " + JSON.stringify(data));

        // Vaciar los campos del formulario después de que el evento haya sido enviado correctamente
        document.getElementById("eventType").value = '';
        document.getElementById("eventData").value = '';
    })
    .catch(error => {
        console.error("Error:", error);
    });
}


function addWorkflow() {
    const workflowName = document.getElementById("workflowName").value;
    const eventTrigger = document.getElementById("eventTrigger").value;
    const usuarioId = 1;  // O obtén el valor dinámicamente si es necesario

    const requestData = {
        nombre: workflowName,
        usuario_id: usuarioId,  // Añade el usuario_id si es necesario en tu backend
        configuraciones: { evento: eventTrigger }
    };

    fetch("/add_workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert("Workflow agregado: " + JSON.stringify(data));
            // Vaciar los campos del formulario
            document.getElementById("workflowName").value = '';
            document.getElementById("eventTrigger").value = '';
        } else {
            alert("Hubo un error al agregar el workflow.");
        }
    })
    .catch(error => console.error("Error:", error));
}