from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from flask_marshmallow import Marshmallow
from app.utils.common import db
from sqlalchemy import inspect
from datetime import datetime  # Importar datetime para usar en el modelo

ma = Marshmallow()

accionWorkflow = Blueprint('accionWorkflow', __name__)

class AccionWorkflow(db.Model):
    __tablename__ = 'accionWorkflow'
    __table_args__ = {'extend_existing': True}  # Opcional, solo si es necesario
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo = db.Column(db.String(120), unique=True, nullable=False)
    parametros = db.Column(db.String(255))  # Cambiado a db.String o db.JSON
    workflow_id = db.Column(db.Integer)
    orden = db.Column(db.String(255), unique=True, nullable=False)

    # Constructor
    def __init__(self, tipo, parametros, workflow_id, orden):
        self.tipo = tipo
        self.parametros = parametros
        self.workflow_id = workflow_id
        self.orden = orden

    def __repr__(self):
        return f"AccionWorkflow(id={self.id}, tipo={self.tipo}, parametros={self.parametros}, workflow_id={self.workflow_id}, orden={self.orden})"

   

class AccionWorkflowSchema(ma.Schema):
    class Meta:
        fields = ("id", "tipo", "parametros", "workflow_id", "orden")

accion_workflow_schema = AccionWorkflowSchema()
accion_workflows_schema = AccionWorkflowSchema(many=True)