from flask import Blueprint, render_template,abort, request,current_app, redirect, url_for, flash,jsonify
import app.controllers.get_login as get
from datetime import datetime
from app.models.sheetModels.GoogleSheetManager  import GoogleSheetManager
from app.models.sheetModels.sheet_handler import SheetHandler
import json
from app.models.instrumentosSuscriptos import InstrumentoSuscriptos
from app.utils.common import  db
from dotenv import load_dotenv
#from pydrive.auth import GoogleAuth
#from pydrive.drive import GoogleDrive
#import routes.api_externa_conexion.cuenta as cuenta
#import gspread
#from oauth2client.service_account import ServiceAccountCredentials
import pprint
import os #obtener el directorio de trabajo actual
import json
import sys
import csv
import re
import threading

load_dotenv()
#import drive
#drive.mount('/content/gdrive')



datoSheet = Blueprint('datoSheet',__name__)

lock = threading.Lock()
newPath = os.path.join(os.getcwd(), 'strategies/credentials_module.json') 
directorio_credenciales = newPath 

SPREADSHEET_ID = '1GMv6fwa1-4iwhPBZqY6ZNEVppPeyZY0R4JB39Xmkc5s'


precios_data = {}

    

datoSheet = Blueprint('datoSheet',__name__)


newPath = os.path.join(os.getcwd(), 'strategies/credentials_module.json') 
directorio_credenciales = newPath 

SPREADSHEET_ID = '1GMv6fwa1-4iwhPBZqY6ZNEVppPeyZY0R4JB39Xmkc5s'


precios_data = {}

def enviar_leer_sheet(app,pais,user_id,hilo,selector):
    
     if hilo == 'hilo':
        pais = 'argentina'
        app.logger.info('ENTRA A THREAD Y LEE EL SHEET POR HILO')       
     else: 
        app.logger.info('LEE EL SHEET POR LLAMADA DE FUNCION')

     if pais not in ["argentina", "usa","hilo"]:
        # Si el país no es válido, retorna un código de estado HTTP 404 y un mensaje de error
        abort(404, description="País no válido")
        
     
     if selector != "simulado" or selector =='vacio':
        if pais == "argentina":
            if len(get.diccionario_global_sheet) > 0:
               if not get.conexion_existente(app,get.USER_CUENTA,get.CORREO_E_ACTUALIZAR_SHEET,get.VARIABLE_ACTUALIZAR_SHEET,get.ID_USER_ACTUALIZAR_SHEET):
                  modifico = datoSheet.actualizar_precios(get.SPREADSHEET_ID_PRUEBA,'valores',pais)
                  #modifico = datoSheet.actualizar_precios(get.SPREADSHEET_ID_PRODUCCION,'valores',pais)
                  print(' PANELCONTROL.PY ESTA COMENTADA LA LINEA DESCOMENTAR ANTES DE SUBIR A GIT ACTION') 
                  app.logger.info('MODIFICO EL SHEET CORRECTAMENTE')
            ContenidoSheet=leerSheet(get.SPREADSHEET_ID_PRUEBA,'bot')
            #ContenidoSheet=datoSheet.leerSheet(get.SPREADSHEET_ID_PRODUCCION,'bot')
        elif pais == "usa":
            ContenidoSheet =  leerSheet(get.SPREADSHEET_ID_PRODUCCION,'drpibotUSA')    
        else:
            return "País no válido"
     else:   
        if pais == "argentina":
            ContenidoSheet =  leerSheet(get.SPREADSHEET_ID_PRUEBA,'bot')
        elif pais == "usa":
            ContenidoSheet =  leerSheet(get.SPREADSHEET_ID_PRUEBA,'bot')
        else:
            return "País no válido"
        
     ContenidoSheetList = list(ContenidoSheet)
     get.diccionario_global_sheet[pais] ={}
     # Adquirir el bloqueo antes de modificar las variables compartidas
     with lock:
            get.diccionario_global_sheet[pais] = ContenidoSheetList
      
     
     return  get.diccionario_global_sheet[pais]
 

def leerSheet(sheetId,sheet_name): 
     
        if not get.autenticado_sheet:        
            # recibo la tupla pero como este es para el bot leo el primer elemento 
            credentials_path = os.path.join(os.getcwd(), 'app/service_account.json')
            # Crear instancia del gestor de hojas
            get.sheet_manager = GoogleSheetManager(credentials_path)

            if get.sheet_manager.autenticar():
                get.autenticado_sheet = True
                handler = SheetHandler(get.sheet_manager, sheetId, sheet_name)
        else:
            # Autenticar
            if  get.autenticado_sheet:
                # Crear instancia del manejador de hoja con el gestor y los datos de la hoja
                handler = SheetHandler(get.sheet_manager, sheetId, sheet_name)
            else:
                    print("Error al autenticar. Revisa los detalles del error.")
                    get.autenticado_sheet = False
                    return render_template('notificaciones/noPoseeDatos.html',layout = 'layout_fichas')    
                
                # Ejemplo de uso de leerSheet
        return handler.leerSheet()
                
            





def actualizar_precios(sheetId, sheet_name, pais):
    try:
        if get.precios_data:
            batch_updates = []
            
            if len(get.symbols_sheet_valores) <= 0:
                if get.sheet_manager.autenticar():
                    get.sheet = get.sheet_manager.abrir_sheet(sheetId, sheet_name)
                    if get.sheet:
                        ranges = ['C:C']  # Rango de símbolos/tickers en la hoja de cálculo
                        try:
                            data = get.sheet.batch_get(ranges)
                            for index, row in enumerate(data[0]):
                                if isinstance(row, list) and row:
                                    symbol = str(row[0]).strip("['").strip("']")
                                    get.symbols_sheet_valores.append(symbol)                                    
                                    if symbol in get.precios_data:
                                        precios_data = get.precios_data[symbol]
                                        try:
                                            if 'max24hs' in precios_data:
                                                batch_updates.append({
                                                    'range': f"E{index + 1}", 
                                                    'values': [[str(precios_data['max24hs']).replace('.', ',')]]
                                                })
                                            if 'min24hs' in precios_data:
                                                batch_updates.append({
                                                    'range': f"F{index + 1}", 
                                                    'values': [[str(precios_data['min24hs']).replace('.', ',')]]
                                                })
                                            if 'p24hs' in precios_data:
                                                batch_updates.append({
                                                    'range': f"G{index + 1}", 
                                                    'values': [[str(precios_data['p24hs']).replace('.', ',')]]
                                                })
                                        except ValueError:
                                            print(f"El símbolo {symbol} no se encontró en la hoja de cálculo.")
                        except Exception as e:
                            print(f"Error en el proceso de actualización: {e}")
            else:
                for index, symbol in enumerate(get.symbols_sheet_valores):
                    if symbol in get.precios_data:
                        precios_data = get.precios_data[symbol]
                        try:
                            if 'max24hs' in precios_data:
                                batch_updates.append({
                                    'range': f"E{index + 1}", 
                                    'values': [[str(precios_data['max24hs']).replace('.', ',')]]
                                })
                            if 'min24hs' in precios_data:
                                batch_updates.append({
                                    'range': f"F{index + 1}", 
                                    'values': [[str(precios_data['min24hs']).replace('.', ',')]]
                                })
                            if 'p24hs' in precios_data:
                                batch_updates.append({
                                    'range': f"G{index + 1}", 
                                    'values': [[str(precios_data['p24hs']).replace('.', ',')]]
                                })
                        except ValueError:
                            print(f"El símbolo {symbol} no se encontró en la hoja de cálculo.")
            
            if batch_updates:
                try:
                    get.sheet.batch_update(batch_updates)
                    print("Actualización en lotes exitosa.")
                except Exception as e:
                    print(f"Error en la actualización en lotes: {e}")
            else:
                print("No hay datos para actualizar.")
    except Exception as e:
        print(f"Error en el proceso de actualización: {e}")
        return False
    return True

# Función de codificación personalizada para datetime
def datetime_encoder(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()




    # Defines the handlers that will process the Order Reports.

########################AQUI SE REALIZA EL JSON PARA LOS DATOS DEL SHEET#############
def construir_lista_de_datos(symbol, tipo_de_activo, trade_en_curso, ut, senial, gan_tot, dias_operado):
    datos = []
    for i in range(1, len(symbol)):
        datos.append({
            'symbol': symbol[i],
            'tipo_de_activo': tipo_de_activo[i],
            'trade_en_curso': trade_en_curso[i],
            'ut': ut[i],
            'senial': senial[i],
            'gan_tot': gan_tot[i],
            'dias_operado': dias_operado[i]
        })
    return datos
     