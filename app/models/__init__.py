from flask_sqlalchemy import SQLAlchemy
from .cuentas import Cuenta
from .orden import Orden
from .usuario import Usuario
from .events import Events
from .workflows import Workflows
from .accionWorkflow import AccionWorkflow


db = SQLAlchemy()
