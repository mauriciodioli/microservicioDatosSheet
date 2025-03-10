from flask import Flask, Blueprint,request, jsonify,current_app
import sqlite3
import json
import datetime

from app.models.usuario import Usuario
from app.models.accionWorkflow import AccionWorkflow
from app.models.workflows import Workflows
from app.models.events import Events


workflowController = Blueprint('workflowController', __name__)

@workflowController.route('/alta', methods=['POST'])
def init_db():
    conn = sqlite3.connect("workflow.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tipo TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        datos TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS workflows (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT,
                        activado BOOLEAN DEFAULT 1,
                        usuario_id INTEGER,
                        configuraciones TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS acciones (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tipo TEXT,
                        parametros TEXT,
                        workflow_id INTEGER,
                        orden INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS historial_ejecucion (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        workflow_id INTEGER,
                        estado TEXT,
                        resultado TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

@workflowController.route("/trigger_event", methods=["POST"])
def trigger_event():
    data = request.json
    tipo = data.get("tipo")
    datos = json.dumps(data.get("datos", {}))
    
    conn = sqlite3.connect("workflow.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (tipo, datos) VALUES (?, ?)", (tipo, datos))
    conn.commit()
    
    # Evaluar workflows que respondan a este evento
    cursor.execute("SELECT id, nombre, configuraciones FROM workflows WHERE activado = 1")
    workflows = cursor.fetchall()
    for wf in workflows:
        workflow_id, nombre, configuraciones = wf
        configuraciones = json.loads(configuraciones)
        
        if configuraciones.get("evento") == tipo:
            execute_workflow(workflow_id)
    
    conn.close()
    return jsonify({"message": "Evento recibido y procesado", "tipo": tipo})

def execute_workflow(workflow_id):
    conn = sqlite3.connect("workflow.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, tipo, parametros FROM acciones WHERE workflow_id = ? ORDER BY orden", (workflow_id,))
    acciones = cursor.fetchall()
    
    for accion in acciones:
        accion_id, tipo, parametros = accion
        resultado = execute_action(tipo, json.loads(parametros))
        cursor.execute("INSERT INTO historial_ejecucion (workflow_id, estado, resultado) VALUES (?, ?, ?)", (workflow_id, "Ejecutado", json.dumps(resultado)))
        conn.commit()
    
    conn.close()

def execute_action(tipo, parametros):
    if tipo == "log":
        return {"status": "logged", "message": parametros.get("mensaje", "Acción sin mensaje")}
    elif tipo == "http_request":
        return {"status": "http_sent", "url": parametros.get("url", "No URL provided")}
    else:
        return {"status": "unknown", "message": "Tipo de acción no reconocido"}

@workflowController.route("/add_workflow", methods=["POST"])
def add_workflow():
    from app import db  # Importar aquí dentro de la función
    # Obtener datos del cuerpo de la solicitud (en formato JSON).
    data = request.get_json()

    # Obtener los valores del JSON. Si alguno no existe, se puede establecer un valor predeterminado.
    nombre = data.get("nombre")
    usuario_id = data.get("usuario_id", 0)  # Valor predeterminado es 0 si no se pasa
    configuraciones = json.dumps(data.get("configuraciones", {}))  # Si no hay configuraciones, se pasa un dict vacío.

    # Asegúrate de que `nombre` esté presente antes de crear el nuevo flujo de trabajo
    if not nombre:
        return jsonify({"error": "El nombre es obligatorio"}), 400

    # Crear la instancia de Workflows con los datos recibidos.
    new_workflow = Workflows(
        nombre=nombre,
        activado=1,  # Asumo que activado es siempre True por defecto. Cambia si es necesario.
        configuraciones=configuraciones,
        user_id=int(usuario_id)  # Asegúrate de que el modelo Workflows tenga este campo.
    )

    # Agregar a la sesión de la base de datos y hacer commit.
    try:
        db.session.add(new_workflow)
        db.session.commit()  # Intentar hacer commit
        db.session.close()
    except Exception as e:
        db.session.rollback()  # Rollback en caso de error
        return jsonify({"error": "Hubo un error al agregar el workflow", "details": str(e)}), 500
    finally:
        db.session.remove()  # Se recomienda usar remove() en lugar de close() para gestionar correctamente la sesión en Flask.

    # Retornar un mensaje con el nombre del nuevo workflow.
    return jsonify({"message": "Workflow agregado", "workflow": nombre}), 201