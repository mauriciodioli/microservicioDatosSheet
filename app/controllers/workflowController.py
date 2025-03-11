from flask import Flask, Blueprint, request, jsonify, current_app
import json
from datetime import datetime  
import redis

from app.models.usuario import Usuario
from app.models.accionWorkflow import AccionWorkflow
from app.models.workflows import Workflows
from app.models.events import Events
from app.models.historial import Historial

workflowController = Blueprint('workflowController', __name__)

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

@workflowController.route("/trigger_event", methods=["POST"])
def trigger_event():
    from app import db  
    data = request.json
    tipo = data.get("tipo")
    datos = json.dumps(data.get("datos", {}))
    user_id = data.get("user_id")
    fechaCreacion = datetime.now()

    if not tipo or not user_id:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    new_event = Events(
        user_id=int(user_id),
        tipo=tipo,
        fechaCreacion=fechaCreacion,
        datosEvents=datos
    )

    try:
        db.session.add(new_event)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Hubo un error al agregar el evento", "details": str(e)}), 500

    workflows = db.session.query(Workflows).filter_by(activado=1).all()

    for wf in workflows:
        workflow_id, nombre, configuraciones, user_id = wf.id, wf.nombre, wf.configuraciones, wf.user_id
        configuraciones = json.loads(configuraciones)
        if configuraciones.get("evento") == tipo:
            redis_client.rpush("workflow_queue", json.dumps({"workflow_id": workflow_id, "user_id": user_id}))

    db.session.close()
    return jsonify({"message": "Evento recibido y procesado", "tipo": tipo})

def process_workflows():
    from app import db
    while True:
        _, data = redis_client.blpop("workflow_queue")
        task = json.loads(data)
        workflow_id = task["workflow_id"]
        user_id = task["user_id"]
        execute_workflow(db, workflow_id, user_id)

def execute_workflow(db, workflow_id, user_id):
    acciones_workflow = db.session.query(AccionWorkflow).filter_by(workflow_id=workflow_id)
    fecha = datetime.now()
    max_reintentos = 3

    for accion in acciones_workflow:
        accion_id, tipo, parametros = accion
        intentos = 0
        resultado = None

        while intentos < max_reintentos:
            resultado = execute_action(tipo, json.loads(parametros))
            if resultado.get("status") != "unknown":
                break
            intentos += 1

        new_historial = Historial(
            fecha=fecha,
            user_id=user_id,           
            workflow_id=workflow_id,
            estado='Fallido' if intentos == max_reintentos else 'Ejecutado',
            resultado=json.dumps(resultado),
            intentos=intentos
        )
        db.session.add(new_historial)
        db.session.commit()
    return True

def execute_action(tipo, parametros):
    if tipo == "log":
        return {"status": "logged", "message": parametros.get("mensaje", "Acción sin mensaje")}
    elif tipo == "http_request":
        return {"status": "http_sent", "url": parametros.get("url", "No URL provided")}
    else:
        return {"status": "unknown", "message": "Tipo de acción no reconocido"}

@workflowController.route("/add_workflow", methods=["POST"])
def add_workflow():
    from app import db  
    data = request.get_json()
    nombre = data.get("nombre")
    usuario_id = data.get("usuario_id", 0)
    configuraciones = json.dumps(data.get("configuraciones", {}))

    if not nombre:
        return jsonify({"error": "El nombre es obligatorio"}), 400

    new_workflow = Workflows(
        nombre=nombre,
        activado=1,
        configuraciones=configuraciones,
        user_id=int(usuario_id)
    )

    try:
        db.session.add(new_workflow)
        db.session.commit()
        db.session.close()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Hubo un error al agregar el workflow", "details": str(e)}), 500
    finally:
        db.session.remove()

    return jsonify({"message": "Workflow agregado", "workflow": nombre}), 201

@workflowController.route("/get_historial/<int:workflow_id>", methods=["GET"])
def get_historial(workflow_id):
    from app import db
    historial = db.session.query(Historial).filter_by(workflow_id=workflow_id).all()
    historial_json = [{
        "id": h.id,
        "fecha": h.fecha.isoformat(),
        "estado": h.estado,
        "resultado": json.loads(h.resultado),
        "intentos": h.intentos
    } for h in historial]
    return jsonify(historial_json)
