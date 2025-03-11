from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from flask_marshmallow import Marshmallow
from app.utils.common import db
from sqlalchemy import inspect
from datetime import datetime  # Importar datetime para usar en el modelo

ma = Marshmallow()

historial = Blueprint('historial', __name__)

class Historial(db.Model):
    __tablename__ = 'historial'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # AUTO_INCREMENT
    user_id = db.Column(db.Integer, nullable=True)  # Puede ser NULL
    workflow_id = db.Column(db.Integer, nullable=True)  # Puede ser NULL
    fechaCreacion = db.Column(db.DateTime, default=datetime.utcnow)  # Usar db.DateTime y establecer un valor por defecto
    estado = db.Column(db.String(120), nullable=False)  # No puede ser NULL   
    reintentos = db.Column(db.String(255), nullable=False)  # No puede ser NULL
    # Constructor
    def __init__(self, user_id, workflow_id, fechaCreacion, estado,reintentos):
        self.user_id = user_id
        self.workflow_id = workflow_id,
        self.activado = fechaCreacion,
        self.estado = estado,
        self.reintentos = reintentos

    def __repr__(self):
        return f"Historial(id={self.id}, user_id={self.user_id}, evento_id={self.workflow_id}, fechaCreacion={self.fechaCreacion}, estado={self.estado},reintentos={self.reintentos})"

 

class HistorialSchema(ma.Schema):
    class Meta:
        fields = ("id", "user_id", "workflow_id", "fechaCreacion", "estado","reintentos")

historial_schema = HistorialSchema()
historials_schema = HistorialSchema(many=True)  # Cambiado a Historial_schema para evitar confusión