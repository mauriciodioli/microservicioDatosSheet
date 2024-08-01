from app.utils.db import  db
from ast import Return
from http.client import UnimplementedFileMode
import json
import copy
import jwt
from pyRofex.components.exceptions import ApiException

from re import template
from socket import socket
import pyRofex



from app.controllers.wsocket import wsocketConexion as conexion
from app.controllers.wsocket import websocketConexionShedule as conexionShedule
from app.controllers.wsocket import SuscripcionDeSheet

import app.tokens.token as Token
import app.controllers.instrumentos as inst
from app.models.instrumento import Instrumento
from app.models.cuentas import Cuenta

import ssl

from pyRofex.clients.rest_rfx import RestClient
from pyRofex.clients.websocket_rfx import WebSocketClient
from pyRofex.components.globals import environment_config

import threading
import os

from datetime import datetime, timezone
import time
from flask_jwt_extended import (
    JWTManager,    
    jwt_required,
    create_access_token,
    get_jwt_identity,
    create_refresh_token,
    set_access_cookies,
    set_refresh_cookies
    
)
from flask import (
    Flask,
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    current_app,
    g,
    session,
    make_response
)


get_login = Blueprint('get_login',__name__)

 
user = "{{usuario}}" 
password = "{{contraseña}}" 
account = "{{cuenta}}"  
market_data_recibida = []
reporte_de_ordenes = []


SPREADSHEET_ID_PRUEBA='1yQeBg8AWinDLaErqjIy6OFn2lp2UM8SRFIcVYyLH4Tg'#drpiBot3 de pruba
SPREADSHEET_ID_PRODUCCION='1GMv6fwa1-4iwhPBZqY6ZNEVppPeyZY0R4JB39Xmkc5s'#drpiBot de produccion
SPREADSHEET_ID_USA='1sxbKe5pjF3BsGgUCUzBDGmI-zV5hWbd6nzJwRFw3yyU'#de produccion USA
VARIABLE_ACTUALIZAR_SHEET = 'produccion'

USER_CUENTA =  os.environ.get("USER_CUENTA")
CUENTA_WS =  os.environ.get("CUENTA_WS")
PASSWORD_CUENTA =  os.environ.get("PASSWORD_CUENTA")



CORREO_E_ACTUALIZAR_SHEET =  os.environ.get("CORREO_E_ACTUALIZAR_SHEET")
ID_USER_ACTUALIZAR_SHEET =  os.environ.get("ID_USER_ACTUALIZAR_SHEET")

API_URL = os.environ.get("API_URL")
WS_URL = os.environ.get("WS_URL")

#CUENTA_ACTUALIZAR_SHEET = '10861'
#CORREO_E_ACTUALIZAR_SHEET = 'dpuntillo@gmail.com'
#ID_USER_ACTUALIZAR_SHEET = 2
# Días de la semana a los que debe ejecutar la función

DIAS_EJECUCION = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado"]

# Diccionario para convertir el nombre del día a su valor numérico
DIAS_SEMANA = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "domingo": 6
}
precios_data = {} #para mdh 0
symbols_sheet_valores = []
sheet = None
accountLocalStorage = ""
VariableParaBotonPanico = 0
VariableParaSaldoCta = 0
pyWsSuscriptionInicializada = pyRofex
pyRofexInicializada = pyRofex
ConexionesBroker = {}
luzMDH_funcionando = False
luzThred_funcionando = {'luz': False, 'hora': 0, 'minuto': 0, 'segundo': 0}
sheet_manager = None

indice_cuentas = {}
autenticado_sheet = False
diccionario_global_sheet = {}
diccionario_global_sheet_intercambio = {}
ya_ejecutado_hilo_panelControl = False
hilo_iniciado_panel_control = {}  # Un diccionario para mantener los hilos por país
hilo_iniciado_estrategia_usuario = {}
hilos_iniciados_shedule = []
ultima_entrada = time.time()
CUSTOM_LEVEL = 25  # Elige un número de nivel adecuado
detener_proceso_automatico_triggers = False  # Bucle hasta que la bandera detener_proceso sea True


marca_de_tiempo_para_leer_sheet = int(datetime.now().timestamp()) * 1000  # Tiempo inicial
VariableParaTiempoLeerSheet = 0  # Variable para guardar el tiempo transcurrido

ContenidoSheet_list = None
api_url = None
ws_url = None
api_url_veta = None
ws_url_veta = None
REMARKET ={"url": "https://api.remarkets.primary.com.ar/",
        "ws": "wss://api.remarkets.primary.com.ar/",
        "ssl": True,
        "proxies": None,
        "rest_client": None,
        "ws_client": None,
        "token": None,
        "user": None,
        "password": None,
        "account": None,
        "initialized": False,
        "proprietary": "PBCP",
        "heartbeat": 30,
        "ssl_opt": None}
envNuevo =  {"url": "https://api.primary.com.ar/",
        "ws": "wss://api.primary.com.ar/",
        "ssl": True,
        "proxies": None,
        "rest_client": None,
        "ws_client": None,
        "user": None,
        "password": None,
        "account": None,
        "initialized": False,
        "proprietary": "api",
        "heartbeat": 30,
        "ssl_opt": None }


@get_login.route("/index")
def index():
    return render_template('index.html')


@get_login.route("/loginExtCuentaSeleccionadaBroker", methods=['POST'])
def loginExtCuentaSeleccionadaBroker():
   
    try:
      if request.method == 'POST':
        origin_page = request.form.get('origin_page')
        user = request.form.get('usuario')
        password = request.form.get('contraseña')
        accountCuenta = request.form.get('cuenta')
        access_token = request.form.get('access_token')       
        src_directory1 = os.getcwd()#busca directorio raiz src o app 
        logs_file_path = os.path.join(src_directory1, 'logs.log')
        
        global ConexionesBroker,api_url, ws_url  
       
        if access_token and Token.validar_expiracion_token(access_token=access_token): 
                user_id = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])['sub']
       
                if origin_page == 'login':
                    selector = request.form.get('environment')
                    print('selector ',selector)
                    
                else: 
                    selector = request.form.get('selectorEnvironment')
                    print('selector ',selector)
                
                
            
                if not selector or not user or not password or not accountCuenta:
                    flash('Falta información requerida')
                    return redirect(url_for('autenticacion.index'))

            
            
                app = current_app._get_current_object() 
                #creaJsonParaConextarseSheetGoogle()
                if selector == 'simulado':
                    ambiente = copy.deepcopy(REMARKET)
                    pyRofexInicializada._add_environment_config(enumCuenta=accountCuenta,env=ambiente)
                    environments = accountCuenta                                        
                    pyRofexInicializada._set_environment_parameter("proprietary", "PBCP", environments) 
                    try:   
                        pyRofexInicializada.initialize(user=user, password=password, account=accountCuenta, environment=environments)                       
                    except ApiException as e:
                        print(f"ApiException occurred: {e}")
                        flash("Cuenta incorrecta: password o usuario incorrecto. Quite la cuenta")
                        return render_template("cuentas/registrarCuentaBroker.html") 
                    ConexionesBroker[accountCuenta] = {'pyRofex': pyRofexInicializada, 'cuenta': accountCuenta, 'identificador': False}
                                            
                else:
                    
                        # Configurar para el entorno LIVE              
                        endPoint = inicializar_variables(accountCuenta)
                    # app.logger.info(endPoint)
                    
                        api_url = endPoint[0]
                        ws_url = endPoint[1]
                        
                        
                    
                        sobreEscituraPyRofex = True
                            
                    
                    # Verificar si la cuenta con el valor accountCuenta no existe en el diccionario
                        if (not ConexionesBroker or 
                            all(entry['cuenta'] != accountCuenta for entry in ConexionesBroker.values()) or 
                            (accountCuenta in ConexionesBroker and ConexionesBroker[accountCuenta].get('identificador') == False)):
    
    
                                #pyRofexInicializada = pyRofex
                                if sobreEscituraPyRofex == True:
                                    ambiente = copy.deepcopy(envNuevo)
                                    pyRofexInicializada._add_environment_config(enumCuenta=accountCuenta,env=ambiente)
                                    environments = accountCuenta
                                else:    
                                    if selector == 'simulado':
                                        environments = pyRofexInicializada.Environment.REMARKET
                                    else:                                    
                                        environments = pyRofexInicializada.Environment.LIVE
                                
                                pyRofexInicializada._set_environment_parameter("url", api_url, environments)                          
                                pyRofexInicializada._set_environment_parameter("ws", ws_url, environments)                            
                                pyRofexInicializada._set_environment_parameter("proprietary", "PBCP", environments)    
                                pyRofexInicializada.initialize(user=user, password=password, account=accountCuenta, environment=environments)                       
                            #  restClientEnv = RestClient(environments)
                            #  wsClientEnv = WebSocketClient(environments)
                            
                                ConexionesBroker[accountCuenta] = {'pyRofex': pyRofexInicializada, 'cuenta': accountCuenta, 'identificador': False}
                                #ConexionesBroker[accountCuenta]['identificador'] = True
                
                            
                while True:
                            try:  
                                for elemento in ConexionesBroker:
                                    print("Variable agregada:", elemento)
                                    cuenta = ConexionesBroker[elemento]['cuenta']
                            
                                    if accountCuenta ==  cuenta and ConexionesBroker[elemento]['identificador'] == False:
                                    
                    
                                        conexion(app,ConexionesBroker[elemento]['pyRofex'], ConexionesBroker[elemento]['cuenta'],user_id,selector)
                        
                                      
                        
                                        print(f"Está logueado en {selector} en {environments}")
                                        ConexionesBroker[accountCuenta]['identificador'] = True
                                        break  # Salir del bucle for si se completa correctamente
                                    else:               
                                        pass
                                    
                            except RuntimeError:
                                    # Manejar la excepción aquí
                                    print("Se produjo un RuntimeError durante la iteración. Reiniciando el bucle...")
                                    continue  # Volver al inicio del bucle while para intentar de nuevo    
                                # Si llegamos aquí, significa que el bucle for se completó sin excepciones
                            break  # Salir del bucle while ya que se completó correctamente
    # Redirige a la página de origen según el valor de origin_page
                if origin_page == 'login':
                    return render_template('home.html', cuenta=[accountCuenta, user, selector])
                elif origin_page == 'cuentasDeUsusario':
                        return render_template('paneles/panelDeControlBroker.html', cuenta=[accountCuenta, user, selector])
                else:
                        # Si origin_page no coincide con ninguna ruta conocida, redirige a una página por defecto.
                        return render_template('registrarCuentaBroker.html')

    except jwt.ExpiredSignatureError:
        flash("El token ha expirado")
    except jwt.InvalidTokenError:
        flash("El token es inválido")
    #  except Exception as e:
    #      print('Error inesperado:', e)
    #      flash('No se pudo iniciar sesión')
    #      return render_template('errorLogueo.html')




def conexion_existente(app,accountCuenta,correo_electronico,selector,user_id):
    if len(precios_data)> 0:       
        return False
    else:        
        with app.app_context():
            conexionShedule(app, Cuenta=Cuenta, account=accountCuenta, idUser=user_id, correo_electronico=correo_electronico, selector=selector)           
        return True 
        
def buscar_conexion(client_id, cuenta):
    for key, websocket in ConexionesBroker.items():
        print(f"Comparando clave: (client_id={key[0]}, cuenta={key[1]})")  # Print para mostrar la clave que está siendo comparada
        if key[:2] == (client_id, cuenta):
            print(f"Comparando clave: (client_id={key[0]}, cuenta={key[1]})")
            resumenCuenta = websocket.get_account_report(account=cuenta)
            return websocket  # Retorna la conexión si se encuentra

    return None  # Retorna None si no se encuentra ninguna conexión

