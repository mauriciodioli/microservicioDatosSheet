from flask_sqlalchemy import SQLAlchemy
from .cuentas import Cuenta
from .orden import Orden
from .usuario import Usuario


db = SQLAlchemy()
