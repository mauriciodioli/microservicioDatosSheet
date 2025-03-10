from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from flask_marshmallow import Marshmallow
from app.utils.common import db
from sqlalchemy import inspect
from datetime import datetime  # Importar datetime para usar en el modelo

ma = Marshmallow()

workflows = Blueprint('workflows', __name__)

class Workflows(db.Model):
    __tablename__ = 'workflows'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # AUTO_INCREMENT
    user_id = db.Column(db.Integer, nullable=True)  # Puede ser NULL
    nombre = db.Column(db.String(120), nullable=False)  # No puede ser NULL
    activado = db.Column(db.Integer, nullable=False)  # No puede ser NULL
    configuraciones = db.Column(db.String(255), nullable=False)  # No puede ser NULL
    # Constructor
    def __init__(self, user_id, nombre, activado, configuraciones):
        self.user_id = user_id
        self.nombre = nombre,
        self.activado = activado,
        self.configuraciones = configuraciones

    def __repr__(self):
        return f"Workflows(id={self.id}, user_id={self.user_id}, nombre={self.nombre}, activado={self.activado}, configuraciones={self.configuraciones})"

 

class WorkflowSchema(ma.Schema):
    class Meta:
        fields = ("id", "user_id", "nombre", "activado", "configuraciones")

workflow_schema = WorkflowSchema()
workflows_schema = WorkflowSchema(many=True)  # Cambiado a workflows_schema para evitar confusión