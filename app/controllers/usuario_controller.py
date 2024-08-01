from flask import Blueprint, jsonify, request
from app.models.usuario import Usuario, db
from app.interfaces.usuario_interface import validate_usuario

usuario_controller = Blueprint('usuario_controller', __name__)

@usuario_controller.route('/alta', methods=['POST'])
def alta_usuario():
    data = request.json
    if not validate_usuario(data):
        return jsonify({'message': 'Datos de usuario inválidos'}), 400

    nuevo_usuario = Usuario(nombre=data['nombre'], email=data['email'])

    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({'message': 'Usuario creado correctamente'})

