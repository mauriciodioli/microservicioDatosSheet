# Creating  Routes

from sqlalchemy.exc import InvalidRequestError
from sqlalchemy import and_
import requests

from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify, abort,current_app

import threading
import app.controllers.datoSheet as datoSheet
import app.controllers.get_login as get
import time
from datetime import datetime



panelControl = Blueprint('panelControl',__name__)

# Crear una cola global para la comunicación
lock = threading.Lock()

def obtener_pais():
    ip = request.remote_addr
    response = requests.get(f'http://ipinfo.io/{ip}')
    data = response.json()
    pais = data.get('country')
    return f'El país de la conexión es: {pais}'

@panelControl.route("/panel_control", methods=['POST'])
def panel_control():
    if request.method == 'POST':
        try:
            # Obtener los datos del formulario
            origin_page = request.form.get('origin_page')
            pais = request.form.get('pais')   
            usuario_id = request.form.get('usuario_id')
            access_token = request.form.get('access_token')
            accountCuenta = request.form.get('account')
            selector = request.form.get('selector')
        
            app = current_app._get_current_object()
            
            # Llamar a la función que puede lanzar excepciones
            respuesta = llenar_diccionario_cada_15_segundos_sheet(app, pais, accountCuenta, selector)
            
            # Si todo va bien, devolver una respuesta exitosa
            return jsonify({'message': 'Conexión exitosa'})
        
        except Exception as e:
            # Manejar la excepción y devolver un mensaje de error
            return jsonify({'error': f'Ocurrió un error: {str(e)}'}), 500
    
    # Manejar otros métodos HTTP si es necesario
    return jsonify({'error': 'Método no permitido'}), 405



def llenar_diccionario_cada_15_segundos_sheet(app, pais, user_id, selector):
    try:
        if pais in get.hilo_iniciado_panel_control and get.hilo_iniciado_panel_control[pais].is_alive():
            return f"Hilo para {pais} ya está en funcionamiento"

        hilo = threading.Thread(target=ejecutar_en_hilo, args=(app, pais, user_id, selector,))
        get.hilo_iniciado_panel_control[pais] = hilo
        hilo.start()

        return f"Hilo iniciado para {pais}"
    except Exception as e:
        print(f"Error en llenar_diccionario_cada_15_segundos_sheet: {str(e)}")


    return f"Hilo iniciado para {pais}"

def ejecutar_en_hilo(app, pais, user_id, selector):
    while True:
        # Obtener el día actual de la semana
        dia_actual = datetime.now().weekday()

        # Verificar si el día actual está en la lista de días de ejecución
        if dia_actual in [get.DIAS_SEMANA[dia] for dia in get.DIAS_EJECUCION]:
                time.sleep(30)  # Espera de 4 minutos
                now = datetime.now()
                if not get.luzThred_funcionando['luz']:
                    get.luzThred_funcionando['luz'] = True
                    get.luzThred_funcionando['hora'] = now.hour
                    get.luzThred_funcionando['minuto'] = now.minute
                    get.luzThred_funcionando['segundo'] = now.second

                # Preguntar si son las 11:00 y pasar la lectura
                if (now.hour >= 8 and now.hour < 23) or (now.hour == 23 and now.minute <= 5):
                        datoSheet.enviar_leer_sheet(app, pais, user_id, 'hilo', selector)
                
                # Preguntar si son las 20:00 y apagar el ws y limpiar precios_data
        #        if (now.hour == 2 and now.minute >= 6 and now.minute <= 59) and get.luzMDH_funcionando:
                  #  terminaConexionParaActualizarSheet(get.CUENTA_ACTUALIZAR_SHEET)
        #            get.symbols_sheet_valores.clear()
        #            get.sheet_manager = None
        #            get.autenticado_sheet = False
          
                
       # else:
       #     time.sleep(86400)  # Espera de 24 horas
                        
                    

 
 
def determinar_pais(pais):
    if hasattr(get, 'diccionario_global_sheet') and isinstance(get.diccionario_global_sheet, dict):
        # Asegúrate de que 'get.diccionario_global_sheet' exista y sea un diccionario

        lista_asociada = get.diccionario_global_sheet.get(pais, None)
        if lista_asociada is not None:
           # print(f"La lista asociada a {pais} es: {lista_asociada}")
            return lista_asociada
        else:
            #print(f"No se encontró una lista asociada a {pais}")
            return None
    else:
        print(f"'get.diccionario_global_sheet' no está disponible o no es un diccionario con las listas asociadas a los países.")
        return None

def procesar_datos(app,pais, accountCuenta,user_id,selector):
    if determinar_pais(pais) is not None:
        if pais not in get.diccionario_global_sheet_intercambio:
            datos_desempaquetados = forma_datos_para_envio_paneles(app,get.diccionario_global_sheet[pais], user_id)
            if len(datos_desempaquetados) != 0:
                get.diccionario_global_sheet_intercambio[pais] = datos_desempaquetados
        else:
            return get.diccionario_global_sheet_intercambio[pais]
    else:
        if len(get.diccionario_global_sheet) == 0 or pais not in get.diccionario_global_sheet:
            datoSheet.enviar_leer_sheet(app,pais,accountCuenta,None,selector)      
        if pais in get.diccionario_global_sheet_intercambio:
           return   get.diccionario_global_sheet_intercambio[pais]
       