from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from config.config import Config
from app.controllers.workflowController import workflowController
from app.controllers.usuario_controller import usuario_controller
from app.controllers.operacion_controller import operacion_controller
from app.controllers.panelControl import panelControl
from app.controllers.datoSheet import datoSheet
from app.controllers.wsocket import wsocket
from app.controllers.instrumentoGet import instrumentoGet
from app.controllers.validaInstrumentos import validaInstrumentos
from app.controllers.instrumentos import instrumentos
from app.controllers.get_login import get_login
from app.tokens.token import token
from app.controllers.views_controller import views_controller  # Nuevo import
from app.models.usuario import Usuario
from app.models.cuentas import Cuenta
from app.models.events import Events
from app.models.workflows import Workflows
from app.models.accionWorkflow import AccionWorkflow
from app.models.creaTablas import crea_tablas_DB
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

db = SQLAlchemy()
ma = Marshmallow()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, static_folder='static')
    app.config.from_object(Config)
    
    db.init_app(app)
    ma.init_app(app)
    CORS(app)
    
    app.config['JWT_SECRET_KEY'] = '621289'
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/api/'
    app.config['JWT_REFRESH_COOKIE_PATH'] = '/refresh/'
    app.config['JWT_COOKIE_CSRF_PROTECT'] = True
    jwt.init_app(app)
    
    # Crear engine para la base de datos
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, poolclass=QueuePool, pool_timeout=60, pool_size=1000)
    
    # Función para configurar la sesión de la base de datos
    def configure_db_session():
        with app.app_context():
            db.session.configure(bind=engine)

    configure_db_session()  # Configurar la sesión con el engine
    
    # Registrar los blueprints
    app.register_blueprint(panelControl)
    app.register_blueprint(wsocket)
    app.register_blueprint(datoSheet)
    app.register_blueprint(token)
    app.register_blueprint(instrumentoGet)
    app.register_blueprint(validaInstrumentos)
    app.register_blueprint(instrumentos)
    app.register_blueprint(get_login)
    app.register_blueprint(workflowController)
    app.register_blueprint(views_controller)  # Registrar el Blueprint de views_controller
    
    return app
