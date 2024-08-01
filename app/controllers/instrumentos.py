from pipes import Template
from unittest import result
import requests
import json
import pyRofex
from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify
from app.models.instrumento import Instrumento

import app.controllers.get_login as get
import app.controllers.validaInstrumentos as valida
import time

import re


from app.utils.common import db


instrumentos = Blueprint('instrumentos',__name__)



##########################AQUI ES LA ENTRADA A LA PAGINA INSTRUMENTOS####################

def Getinstrumentos(account=None): 
     repuesta_listado_instrumento = get.ConexionesBroker['pyRofex'].get_detailed_instruments(environment=account)  
     
     listado_instrumento = repuesta_listado_instrumento["instruments"]
     
     #for listado_instrumento in listado_instrumento:     
      #   print(listado_instrumento['instrumentId']['symbol'])#aqui muestro los instrumentos por pantalla
    
     
     return listado_instrumento
     
     
    
################delete de Instrumento##################
@instrumentos.route("/delete/<string:id>")
def delete_mer(id):
    dato = Instrumento.query.get(id)
    db.session.delete(dato)
    db.session.commit()
    db.session.close()
    flash('Operation Removed successfully')
    return redirect('/')

def instrument_por_symbol_para_sugerir_ut(symbol,account):
    try:
        pyRofexInicializada = get.ConexionesBroker.get(account)['pyRofex']
        entries = [pyRofexInicializada.MarketDataEntry.BIDS,
                        pyRofexInicializada.MarketDataEntry.OFFERS,
                        pyRofexInicializada.MarketDataEntry.LAST]
        merdado_id = pyRofexInicializada.Market.ROFEX
       
       # repuesta_instrumento = get.pyRofexInicializada.get_market_data(ticker=symbol, entries=entries, depth=2)
        repuesta_instrumento = pyRofexInicializada.get_market_data(ticker=symbol, entries=entries,environment=account)

        objeto = repuesta_instrumento['marketData']

        jdato = str(objeto['LA'])
       

        if jdato.find('price') == -1:
            return ''
        
        dato = zip([symbol], [jdato])
        return dato

    except:
        flash('Symbol Incorrect')
        return render_template("instrumentos.html")

def instrument_por_symbol(symbol,account):
    try:
        pyRofexInicializada = get.ConexionesBroker.get(account)['pyRofex']
        entries = [pyRofexInicializada.MarketDataEntry.BIDS,
                        pyRofexInicializada.MarketDataEntry.OFFERS,
                        pyRofexInicializada.MarketDataEntry.LAST]
        merdado_id = pyRofexInicializada.Market.ROFEX
       
       # repuesta_instrumento = get.pyRofexInicializada.get_market_data(ticker=symbol, entries=entries, depth=2)
        repuesta_instrumento = pyRofexInicializada.get_market_data(ticker=symbol, entries=entries,environment=account)

        objeto = repuesta_instrumento['marketData']

        jdato = str(objeto['LA'])
        jdato1 = str(objeto['BI'])
        jdato2 = str(objeto['OF'])

        if jdato.find('price') == -1 or jdato1.find('price') == -1 or jdato2.find('price') == -1:
            return ''
        
        dato = zip([symbol], [jdato], [jdato1], [jdato2])
        return dato

    except:
        flash('Symbol Incorrect')
        return render_template("instrumentos.html")


##########################AQUI LLAMO A UN INSTRUMENTO####################
@instrumentos.route("/instrument_by_symbol/",methods=['POST'])
def instrument_by_symbol():
         
      try:
        
        if request.method == 'POST': 
            symbol = request.form.get('symbol')
            marketId = request.form.get('selctorEnvironment')
            account = request.form.get('accountCuenta')
            print("llego aquiiiiiiiiiiiiii",symbol)
            #print("llego aquiiiiiiiiiiiiii",marketId)
            #if marketId == '1':
            #   rofex = 'ROFX'
            #   print(rofex)
            pyRofexInicializada = get.ConexionesBroker.get(account)['pyRofex']
            entries =  [ pyRofexInicializada.MarketDataEntry.BIDS,
                        pyRofexInicializada.MarketDataEntry.OFFERS,
                        pyRofexInicializada.MarketDataEntry.LAST,
                        pyRofexInicializada.MarketDataEntry.CLOSING_PRICE,
                        pyRofexInicializada.MarketDataEntry.OPENING_PRICE,
                        pyRofexInicializada.MarketDataEntry.HIGH_PRICE,
                        pyRofexInicializada.MarketDataEntry.LOW_PRICE,
                        pyRofexInicializada.MarketDataEntry.SETTLEMENT_PRICE,
                        pyRofexInicializada.MarketDataEntry.NOMINAL_VOLUME,
                        pyRofexInicializada.MarketDataEntry.TRADE_EFFECTIVE_VOLUME,
                        pyRofexInicializada.MarketDataEntry.TRADE_VOLUME,
                        pyRofexInicializada.MarketDataEntry.OPEN_INTEREST]
            print("symbol ",symbol)
           #https://api.remarkets.primary.com.ar/rest/instruments/detail?symbol=DLR/NOV23&marketId=ROFX
            repuesta_instrumento = pyRofexInicializada.get_market_data(ticker=symbol, entries=entries, depth=2)
           
            
            #repuesta_instrumento = get.pyRofexInicializada.get_instrument_details(ticker=symbol)
            #for repuesta_instrumento in repuesta_instrumento:        
            objeto = repuesta_instrumento['marketData']   
           # for objeto in objeto:     
            
            print(" LA ",objeto['LA'])
            print(" BI ",objeto['BI'])            
            print(" OF ",objeto['OF'])
            jdato = str(objeto['LA'])
            jdato1 = str(objeto['BI'])
            jdato2 = str(objeto['OF'])
            if jdato.find('price')==-1:
                print("no tiene nada LA ",jdato1.find('price'))
                
            elif jdato1.find('price')==-1:
                print("no tiene nada BI ",jdato1.find('price'))
                
            
            elif jdato2.find('price')==-1:
                print("no tiene nada OF",jdato2.find('price'))
           
            return render_template("UnInstrumentoSolo.html", dato = [objeto,symbol] )
        
      except:       
        flash('Symbol Incorrect')   
        return render_template("instrumentos.html" )
   
########################################################################

@instrumentos.route("/add_instrumento/<string>" )
def add_instrumento(string):
    print("entra aquiiiiiiiiiiiiiiiiiiiiiiiiiiii")
    especie = string.split(',')[0]
    c_compra = string.split(',')[1]
    p_compra = string.split(',')[2]
    p_venta = string.split(',')[2]
    c_venta = string.split(',')[2]
    ultimo = string.split(',')[2]
    var = string.split(',')[2]
    apertura = string.split(',')[2]
    minimo = string.split(',')[2]
    maximo = string.split(',')[2]
    cierre_anterior = string.split(',')[2]
    volumen = string.split(',')[2]
    vol_monto = string.split(',')[2] 
    vwap = string.split(',')[2]
    idsegmento = string.split(',')[2]
    idmarket = string.split(',')[2]
    print(especie)
    new_mer = Instrumento(especie,c_compra,p_compra,p_venta,c_venta,ultimo,var,apertura,minimo,maximo,cierre_anterior,volumen,vol_monto,vwap,idsegmento,idmarket)
    db.session.add(new_mer)
    db.session.commit()
    db.session.close()
    flash('Operation Added successfully')
    return redirect('/')

# Creating simple Routes
@instrumentos.route("/add_inst",methods=['POST'])
def add_inst():
    # Obtenga los parámetros en la URL, por ejemplo: http://127.0.0.1:5000/data?page=1&limit=10.
   
    
    # jsonify puede devolver datos en lista, dict y otros formatos
    # print json content
    
    return "salida"

@instrumentos.route("/eliminar/<id>" )
def eliminar(id):
    dato = Instrumento.query.get(id)
    db.session.delete(dato)
    db.session.commit()
    db.session.close()
    flash('Operation Removed successfully')
    ###url_for('index') redirecciona a la funcion index
    return redirect('index')    
    

################editar Instrumento##################
@instrumentos.route("/editar/<id>", methods=['POST',"GET"])
def get_instrumento(id):
   
    dato = Instrumento.query.get(id)
    print(dato)
    if request.method == "POST":       
        instrumento = Instrumento.query.filter_by(id=id).first()  
        instrumento.especie = request.form["especie"]
        instrumento.c_compra = request.form["c_compra"]
        instrumento.p_compra = request.form["p_compra"]
        instrumento.p_venta = request.form["p_venta"]
        instrumento.c_venta = request.form["c_venta"]
        instrumento.ultimo = request.form["ultimo"]
        instrumento.var = request.form["var"]
        instrumento.apertura = request.form["apertura"]
        instrumento.minimo = request.form["minimo"]
        instrumento.maximo = request.form["maximo"]
        instrumento.cierre_anterior = request.form["cierre_anterior"]
        instrumento.volumen = request.form["volumen"]
        instrumento.vol_monto = request.form["vol_monto"]
        instrumento.vwap = request.form["vwap"]
        instrumento.idsegmento = request.form["idsegmento"]
        instrumento.idmarket = request.form["idmarket"]
       
        db.session.commit()
        db.session.close()
        flash('Operation successfully')
        return redirect('index')
   
   
    
    registroAEditar = db.session.query(Instrumento).get(dato.id)
    db.session.close()
    return render_template("editarInstrumento.html", dato = registroAEditar)
  
 
def instrumentos_existentes(account,listado):
     listado_final = []
     pyRofexInicializada = get.ConexionesBroker.get(account)['pyRofex']
     repuesta_listado_instrumento = pyRofexInicializada.get_detailed_instruments(environment=account)
     listado_instrumentos = repuesta_listado_instrumento['instruments']
     tickers_existentes = obtener_array_tickers(listado_instrumentos)
     #print(tickers_existentes)     
     
     for inst in listado:
      listado_final.append(inst['instrumentId']['symbol'])
     return listado_final

def instrumentos_existentes_by_symbol(pyRofexInicializada=None,message=None,account=None):
    listado_final = []

    repuesta_listado_instrumento = pyRofexInicializada.get_detailed_instruments(environment=account)
    listado_instrumentos = repuesta_listado_instrumento['instruments']
    tickers_existentes = obtener_array_tickers(listado_instrumentos)

    for ticker in tickers_existentes:
        if ticker in message:
            return True

    return False
@instrumentos.route("/instrumentos_existentes_by_listado/", methods = ['POST'])
def instrumentos_existentes_by_listado():
    listado_final = []
    account = request.form['account']
    symbol = request.form['symbol']
    pyRofexInicializada = get.ConexionesBroker.get(account)['pyRofex']
    respuesta_listado_instrumento = pyRofexInicializada.get_detailed_instruments(environment=account)
    listado_instrumentos = respuesta_listado_instrumento.get('instruments', [])
    
    # Inicializar la lista final
    listado_final = []

    # Convertir el símbolo a una expresión regular, ignorando mayúsculas y minúsculas
    pattern = re.compile(re.escape(symbol), re.IGNORECASE)

    # Verificar si el símbolo proporcionado está en el listado de instrumentos usando la expresión regular
    if any(pattern.search(inst['instrumentId']['symbol']) for inst in listado_instrumentos):
        for inst in listado_instrumentos:
            if pattern.search(inst['instrumentId']['symbol']):
                listado_final.append(inst['instrumentId']['symbol'])
    
    per_page = 10
    offset = (1 - 1) * per_page
    datos_paginated = listado_final[offset:offset + per_page]

    pagination = Pagination(page=1, total=len(listado_final), per_page=per_page, css_framework='bootstrap4')

    return jsonify(datos_paginated)


@instrumentos.route("/instrumentos_detalles_paginacion/<instrumentos_account_paginacion>/<pagina>", methods=['GET'])
def instrumentos_detalles_paginacion(instrumentos_account_paginacion,pagina):
    try:
        if request.method == 'GET':
            # Aquí maneja la lógica para las solicitudes POST
            
            account = instrumentos_account_paginacion
            return f'Valor de la página: {pagina}, Valor de la cuenta de instrumentos: {account}'
        elif request.method == 'GET':
            # Aquí maneja la lógica para las solicitudes GET
            pagina = request.args.get('page', default=1, type=int)
            # Puedes realizar cualquier acción necesaria para manejar la solicitud GET
            return f'Página solicitada: {pagina}'
        
        if account is not None:
            pyRofexInicializada = get.ConexionesBroker.get(account)
            if pyRofexInicializada:        
                repuesta_listado_instrumento = pyRofexInicializada['pyRofex'].get_detailed_instruments(environment=account)
                listado_instrumentos = repuesta_listado_instrumento['instruments']

                # Configurar paginación
               
                per_page = 10
                offset = (page - 1) * per_page
                datos_paginated = listado_instrumentos[offset:offset + per_page]

                pagination = Pagination(page=page, total=len(listado_instrumentos), per_page=per_page, css_framework='bootstrap4')

                return render_template("instrumentos/instrumentos.html", datos=datos_paginated, pagination=pagination)
    except Exception as e:
        print(e)  # Imprimir la excepción para depurar el error
        return str(e)
 

    
@instrumentos.route("/instrumentos_detalles/", methods=['POST'])
def instrumentos_detalles():
    try:
      
        account = request.form['instrumentos_account']
        page = request.form.get('page', 1, type=int)
        
        if account is not None:
            pyRofexInicializada = get.ConexionesBroker.get(account)
            if pyRofexInicializada:        
                repuesta_listado_instrumento = pyRofexInicializada['pyRofex'].get_detailed_instruments(environment=account)
                listado_instrumentos = repuesta_listado_instrumento['instruments']

                # Configurar paginación
               
                per_page = 10
                offset = (page - 1) * per_page
                datos_paginated = listado_instrumentos[offset:offset + per_page]

                pagination = Pagination(page=page, total=len(listado_instrumentos), per_page=per_page, css_framework='bootstrap4')

                return render_template("instrumentos/instrumentos.html", datos=datos_paginated, pagination=pagination)
    except Exception as e:
        print(e)  # Imprimir la excepción para depurar el error
        return str(e)
   
@instrumentos.route("/routes-instrumentos-lista-precios/", methods=['POST'])
def routes_instrumentos_lista_precios():
     # Obtener el símbolo del instrumento de la solicitud AJAX
     
    symbol = request.json.get('symbol')
    account = request.json.get('accountCuenta')

    respuesta_instrumento = []
    try:
        pyRofexInicializada = get.ConexionesBroker.get(account)
        if pyRofexInicializada:            
            entries = [pyRofexInicializada['pyRofex'].MarketDataEntry.BIDS,
                       pyRofexInicializada['pyRofex'].MarketDataEntry.OFFERS,
                       pyRofexInicializada['pyRofex'].MarketDataEntry.LAST]
    
        
        # Definir el rango de profundidades que deseas obtener
            profundidades = [4]

            # Lista para almacenar todos los precios
            precios = []

            # Iterar sobre cada profundidad y obtener los datos de mercado
            for profundidad in profundidades:
                response =  pyRofexInicializada['pyRofex'].get_market_data(ticker=symbol, entries=entries, depth=profundidad,environment=account)
                datos = response['marketData']
                precios.append(datos)  # Agregar los precios a la lista
                print(precios)  # Imprimir los precios obtenidos
            
            return jsonify(precios)

    except:
        flash('Symbol Incorrect')
        return render_template("instrumentos.html")
    
@instrumentos.route("/carga")
def carga():
     return "salida"
  #  return render_template('instrumentos.html', datos = r.json())

#defino funciones


def obtener_array_tickers(listado):
  listado_final = []
  for inst in listado:
    listado_final.append(inst['instrumentId']['symbol'])
  return listado_final

