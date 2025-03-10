from flask import Flask, request, jsonify
import sqlite3
import json
import datetime

app = Flask(__name__)

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

@app.route("/trigger_event", methods=["POST"])
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

@app.route("/add_workflow", methods=["POST"])
def add_workflow():
    data = request.json
    nombre = data.get("nombre")
    usuario_id = data.get("usuario_id", 0)
    configuraciones = json.dumps(data.get("configuraciones", {}))
    
    conn = sqlite3.connect("workflow.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO workflows (nombre, activado, usuario_id, configuraciones) VALUES (?, 1, ?, ?)", (nombre, usuario_id, configuraciones))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Workflow agregado", "workflow": nombre})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
