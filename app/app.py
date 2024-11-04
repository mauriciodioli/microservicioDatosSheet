from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, current_app
from config.config import Config
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from flask_marshmallow import Marshmallow
import os
import traceback
import jwt
from pyRofex.components.exceptions import ApiException
import copy
from app.models.usuario import Usuario
from app.models.cuentas import Cuenta
from app.controllers.usuario_controller import usuario_controller
from app.controllers.operacion_controller import operacion_controller
from app.controllers.panelControl import panelControl
from app.controllers.datoSheet import datoSheet
from app.controllers.wsocket import wsocket
from app.controllers.instrumentoGet import instrumentoGet
from app.controllers.validaInstrumentos import validaInstrumentos
from app.controllers.instrumentos import instrumentos
from app.tokens.token import token
from app.controllers.get_login import get_login
from app.Experimental.red_lstn import red_lstn


load_dotenv()

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)

db = SQLAlchemy()
db.init_app(app)

CORS(app)

app.config['JWT_SECRET_KEY'] = '621289'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/api/'
app.config['JWT_REFRESH_COOKIE_PATH'] = '/refresh/'
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
jwt = JWTManager(app)

app.register_blueprint(panelControl)
app.register_blueprint(wsocket)
app.register_blueprint(datoSheet)
app.register_blueprint(token)
app.register_blueprint(instrumentoGet)
app.register_blueprint(validaInstrumentos)
app.register_blueprint(instrumentos)
app.register_blueprint(get_login)
app.register_blueprint(red_lstn)

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, poolclass=QueuePool, pool_timeout=60, pool_size=1000)

def configure_db_session(app):
    with app.app_context():
        db.session.configure(bind=engine)

configure_db_session(app)

ma = Marshmallow(app)

app.secret_key = '*0984632'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    try:
        
        
             
        return render_template('index.html')
    except Exception as e:
        error_message = f"Error en index: {str(e)}"
        print(error_message)
        traceback.print_exc()
        return f"Error en index: {str(e)}", 500

@app.route('/check_db')
def check_db():
    try:
        result = db.session.execute(text('SELECT 1'))
        if result.scalar() == 1:
            return 'Conexión a la base de datos exitosa!'
        else:
            return 'No se pudo establecer conexión a la base de datos.'
    except Exception as e:
        return f'Error en la conexión a la base de datos: {str(e)}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
