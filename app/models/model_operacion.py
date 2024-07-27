from . import db
from sqlalchemy import inspect

class Operacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(100), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    usuario_id = db.Column(db.Integer, nullable=False) 

    @classmethod
    def crear_tabla_Operacion(cls):
        insp = inspect(db.engine)
        if not insp.has_table("operacion"):  # Corregido el nombre de la tabla esperada
            db.create_all()
