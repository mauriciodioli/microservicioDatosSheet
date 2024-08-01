from flask import Blueprint, jsonify, request
from app.models.model_operacion import Operacion, db
from app.interfaces.operacion_interface import validate_operacion

operacion_controller = Blueprint('operacion_controller', __name__)

@operacion_controller.route('/alta', methods=['POST'])
def alta_operacion():
    data = request.json
    if not validate_operacion(data):
        return jsonify({'message': 'Datos de operación inválidos'}), 400

    nueva_operacion = Operacion(tipo=data['tipo'], monto=data['monto'], usuario_id=data['usuario_id'])

    db.session.add(nueva_operacion)
    db.session.commit()

    return jsonify({'message': 'Operación creada correctamente'})
