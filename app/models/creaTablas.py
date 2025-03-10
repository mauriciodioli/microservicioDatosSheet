from app.models.usuario import Usuario
from app.models.cuentas import Cuenta
from app.models.ficha import Ficha
from app.models.logs import Logs
from app.models.orden import Orden
from app.models.instrumento import Instrumento
from app.models.instrumentoGet import InstrumentoGet
from app.models.instrumentosSuscriptos import InstrumentoSuscriptos
from app.models.instrumentoEstrategiaUno import InstrumentoEstrategiaUno
from app.models.trades import Trade
from app.models.trazaFicha import TrazaFicha
from app.models.triggerEstrategia import TriggerEstrategia
from app.models.accionWorkflow import AccionWorkflow
from app.models.events import Events
from app.models.workflows import Workflows

from datetime import datetime
from flask import Blueprint

creaTabla = Blueprint('creaTabla',__name__)

def crea_tablas_DB():
    
    Events.crear_tabla_events()
    AccionWorkflow.crear_tabla_accionWorkflow()
    Workflows.crear_tabla_workflows()
    Usuario.crear_tabla_usuarios()
    Cuenta.crear_tabla_cuentas()   
    Logs.crear_tabla_logs()    
    
    
    
    
    
    
   
    