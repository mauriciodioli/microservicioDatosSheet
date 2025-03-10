from flask import Blueprint, render_template, session,request, redirect, url_for, flash,jsonify
from flask_marshmallow import Marshmallow
from app.utils.common import db
from sqlalchemy import inspect
from datetime import datetime  # Importar datetime para usar en el modelo

ma = Marshmallow()

events = Blueprint('events', __name__)

class Events(db.Model):
    __tablename__ = 'events'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=True) 
    tipo = db.Column(db.String(120), unique=True, nullable=True)
    fechaCreacion = db.Column(db.DateTime, default=datetime.utcnow)  # Usar db.DateTime y establecer un valor por defecto
    datosEvents = db.Column(db.String(255), unique=True, nullable=True)

    # Constructor
    def __init__(self, user_id, tipo, fechaCreacion, datosEvents):
        self.user_id = user_id
        self.tipo = tipo
        self.fechaCreacion = fechaCreacion
        self.datosEvents = datosEvents

    def __repr__(self):
        return f"Events(id={self.id}, user_id={self.user_id}, tipo={self.tipo}, fechaCreacion={self.fechaCreacion}, datosEvents={self.datosEvents})"

    

class MerShema(ma.Schema):
    class Meta:
        fields = ("id", "user_id", "tipo", "fechaCreacion", "datosEvents")

mer_schema = MerShema()
mer_schemas = MerShema(many=True)  # Cambiado a mer_schemas para evitar confusión