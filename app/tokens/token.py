import jwt
from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify,current_app
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    set_access_cookies, 
    set_refresh_cookies,
    get_jwt_identity)
import random
import secrets
from app.utils.db import db
from app.models.usuario import Usuario
import jwt


token = Blueprint('token',__name__)

SECRET_KEY = 'supersecreto'
# Duración de los tokens
TOKEN_DURATION = 1  # minutos
REFRESH_TOKEN_DURATION = 5  # minutos

def generar_token(user_id, valor, cuenta):
    llave = secrets.token_hex(32)
    print(llave)
    # Generar un número aleatorio utilizando el ID de usuario y el valor proporcionado
   
    random_number = random.randint(1, 10000)

    # Obtener la fecha de generación actual
    fecha_generacion = datetime.now()

    # Agregar los datos al token como claims personalizados
    token_data = {
        'user_id': user_id,
        'random_number': random_number,
        'fecha_generacion': fecha_generacion.isoformat(),
        'valor': valor,
        'cuenta': cuenta
    }

  
    # Crear el token
    token_generado = jwt.encode(token_data, llave , algorithm='HS256')
    dato = token_generado + llave
    return dato

def permiso_para_procesar_logica(token_acceso, token_actualizacion, correo_electronico, numero_de_cuenta, tipo_de_acceso):
    if validar_token(token_acceso, "acceso", correo_electronico, numero_de_cuenta, tipo_de_acceso):
        print("El token de acceso es válido. Procesando el archivo...")
        # Aquí procesas el archivo utilizando el token de acceso
        
        # Verificar si el token de actualización es válido
        if validar_token(token_actualizacion, "actualizacion", correo_electronico, numero_de_cuenta, tipo_de_acceso):
            # Si el token de actualización es válido, generar un nuevo token de acceso
            nuevo_token_acceso = generar_nuevo_token_acceso(correo_electronico,numero_de_cuenta,tipo_de_acceso)
            print("Se generó un nuevo token de acceso:", nuevo_token_acceso)
            return nuevo_token_acceso
        else:
            print("El token de actualización no es válido. No se puede generar un nuevo token de acceso.")
            return False
    else:
        print("El token de acceso no es válido. No se puede procesar el archivo.")
        return False

def validar_token(token=None, tipo=None, correo_electronico=None, numero_de_cuenta=None, tipo_de_acceso=None):
    try:
        # Decodificar el token y verificar la firma
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # Verificar la identidad del usuario (correo electrónico)
        if payload["identity"] != correo_electronico:
            print("El token no pertenece al usuario especificado.")
            return False

        # Verificar la cuenta asociada
        if payload.get("numero_de_cuenta") != numero_de_cuenta:
            print("El token no pertenece a la cuenta especificada.")
            return False

        # Verificar el tipo de acceso
        if payload.get("acceso") != tipo_de_acceso:
            print("El token no tiene el tipo de acceso correcto.")
            return False

        # Verificar la fecha de expiración
        exp_timestamp = payload["exp"]
        if exp_timestamp < datetime.now().timestamp():
            print("El token ha expirado.")
            return False

        # Verificar el tipo de token
        if tipo == "acceso":
            if payload.get("typ") != "access":
                print("El token no es del tipo de acceso.")
                return False
        elif tipo == "actualizacion":
            if payload.get("typ") != "refresh":
                print("El token no es del tipo de actualización.")
                return False
        else:
            print("Tipo de token no válido.")
            return False

        # Si todas las verificaciones pasan, el token es válido
        return True
    
    except jwt.ExpiredSignatureError:
        print("El token ha expirado.")
        return False
    except jwt.InvalidTokenError:
        print("El token no es válido.")
        return False


def validar_expiracion_token(access_token):
    try:
        # Decodificar el token para obtener la información del usuario ('sub')
        token_info = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        username = token_info['sub']

        # Obtener la fecha de expiración del token
        exp_timestamp = token_info.get('exp')
        
        # Verificar si existe una fecha de expiración
        if exp_timestamp is None:
            print("No se encontró la fecha de expiración en el token.")
            return False

        # Convertir el tiempo de expiración a formato datetime
        exp_date = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        # Obtener el tiempo de creación del token (opcional)
        iat_timestamp = token_info.get('iat')
        if iat_timestamp is not None:
            iat_date = datetime.fromtimestamp(iat_timestamp, tz=timezone.utc)
            print("Tiempo de creación del token:", iat_date)

       

        # Verificar si el token ha expirado
        current_time = datetime.now(timezone.utc)
        print("Tiempo actual:", current_time)
        
        # Calcular la diferencia de tiempo hasta la expiración del token
        tiempo_restante = exp_date - current_time
        
        if current_time < exp_date:
            # El token no ha expirado
            print("Tiempo restante para la expiración del token:", tiempo_restante)
            return True
        else:
            # El token ha expirado
            print("El token ha expirado.")
            return False

    except jwt.ExpiredSignatureError:
        # Error si el token ha expirado
        print("El token ha expirado.")
        return False
    except jwt.InvalidTokenError:
        # Error si el token no es válido
        print("El token no es válido.")
        return False

def generar_nuevo_token_acceso(correo_electronico,numero_de_cuenta,tipo_de_acceso):
    return create_access_token(identity=correo_electronico, numero_de_cuenta=numero_de_cuenta, acceso=tipo_de_acceso, expires_delta=timedelta(minutes=TOKEN_DURATION))
   

def decode_token(token):
    try:
        # Decodificar el token con la clave secreta
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        # Devolver el nombre de usuario almacenado en el token
        return payload['sub']

    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
        # Si el token es inválido o ha expirado, devolver None
        return None