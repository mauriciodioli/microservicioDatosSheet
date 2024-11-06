from flask import Blueprint, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from keras.models import Sequential, load_model  # Importar load_model
from keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
from dotenv import load_dotenv
from tensorflow.keras.layers import Dropout, Dense, LSTM, Input
import json
import itertools
import tensorflow as tf
import os

load_dotenv()

# Definir el Blueprint
red_lstn = Blueprint('red_lstn', __name__)



def calcularMeses(train_data, test_data):
    # Calcular diferencia de meses exacta para train_data
    start_train = train_data.index[0]
    end_train = train_data.index[-1]
    train_months = (end_train.year - start_train.year) * 12 + (end_train.month - start_train.month)

    # Calcular diferencia de meses exacta para test_data, si no está vacío
    if not test_data.empty:
        start_test = test_data.index[0]
        end_test = test_data.index[-1]
        test_months = (end_test.year - start_test.year) * 12 + (end_test.month - start_test.month)
    else:
        test_months = 0

    return train_months, test_months

def rangoPrecioDesnormalizado(test_data,scaler):
    
    # Calcular rango de precios desnormalizado para los datos de prueba
    precio_min_normalizado = test_data['Cierre'].min()
    precio_max_normalizado = test_data['Cierre'].max()

    # Desnormalizar precios mínimo y máximo
    precio_min_desnormalizado = scaler.inverse_transform(
        np.concatenate((np.zeros((1, 1)), [[precio_min_normalizado]]), axis=1)
    )[0, 1]
    precio_max_desnormalizado = scaler.inverse_transform(
        np.concatenate((np.zeros((1, 1)), [[precio_max_normalizado]]), axis=1)
    )[0, 1]

    # Calcular el rango de precios desnormalizado
    rango_precios_desnormalizado = precio_max_desnormalizado - precio_min_desnormalizado
    return rango_precios_desnormalizado



def precioReal(y_test,scaler):
    precios_reales_desnormalizados = scaler.inverse_transform(np.concatenate((np.zeros((len(y_test), 1)), y_test.reshape(-1, 1)), axis=1))[:, 1]
    return precios_reales_desnormalizados

 # Preparar datos para RNN
def crear_secuencias(data, seq_len):
        X, y = [], []
        for i in range(len(data) - seq_len):
            X.append(data.iloc[i:i + seq_len][['Apertura', 'Cierre']].values)
            y.append(data.iloc[i + seq_len]['Cierre'])
        return np.array(X), np.array(y)


def calcular_mape(precios_reales, predicciones):
    precios_reales, predicciones = np.array(precios_reales), np.array(predicciones)
    return np.mean(np.abs((precios_reales - predicciones) / precios_reales)) * 100



# Rango de hiperparámetros para optimizar
param_grid = {
    'epochs': [10, 20, 30],
    'batch_size': [32, 64, 128],
    'seq_len': [30, 60, 90],
    'units': [100, 200, 500],  # Número de unidades en las capas LSTM
}

# Función para guardar los resultados en un archivo JSON
def save_results(filename, params, results):
    # Crea un diccionario que contenga ambos parámetros
    data_to_save = {
        'params': params,
        'results': results
    }

    # Abre el archivo y guarda el diccionario en formato JSON
    with open(filename, 'w') as f:
        json.dump(data_to_save, f)
        
        
        
# Función para cargar resultados previos
def load_results(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    
    

@red_lstn.route('/optimizar_modelo', methods=['POST'])
def optimizar_modelo():
     # Obtener datos del request
    ticker = request.json.get('asset_type', 'AAPL')  # Obtener el ticker del request
    start_date = request.json.get('start_date', '2024-01-01')  # Fecha de inicio
    end_date = request.json.get('end_date', '2024-10-31')  # Fecha de fin
    seq_len =  request.json.get('seq_len')
    epochs = request.json.get('epochs')
    batch_size = request.json.get('batch_size')
    # Llamar a la función de optimización con los parámetros especificados
    best_params, best_score = optimize_model(ticker, start_date, end_date, seq_len, epochs, batch_size)

    return jsonify({
        "message": "Optimización de hiperparámetros completada.",
        "best_params": best_params,
        "best_score": best_score
    })




# Optimización de hiperparámetros
def optimize_model(ticker, start_date, end_date, seq_len, epochs, batch_size):

    best_score = float('inf')
    best_params = None
    results_filename = 'model_results.json'

    # Cargar resultados previos
    previous_results = load_results(results_filename)

    # Iterar por cada combinación de parámetros posibles
    for epochs, batch_size, seq_len, units in itertools.product(
            param_grid['epochs'], param_grid['batch_size'], param_grid['seq_len'], param_grid['units']):
        
        # Si ya se probó esta configuración, continuar con la siguiente
        params = {'epochs': epochs, 'batch_size': batch_size, 'seq_len': seq_len, 'units': units}
        if str(params) in previous_results:
            continue

        # Ejecutar el modelo y guardar resultados
        resultado = cargar_datos_con_parametros(ticker, start_date, end_date,params)
        mse = resultado.get('mse')
        training_loss = resultado.get('training_loss')
        validation_loss = resultado.get('validation_loss')
        sobreentrenado = resultado.get('sobreentrenado')
         # Comparar modelos con condiciones adicionales
        if (mse < best_score and not sobreentrenado and 
            validation_loss <= training_loss * 1.1):  # Valida que validation_loss no sea mucho mayor a training_loss
            
            best_score = mse
            best_params = params
            best_model = resultado.get('model')  # Guardar la instancia del modelo entrenado
            save_results(results_filename, params, resultado)

        # Guardar el mejor modelo encontrado
        if best_model:
            best_model.save('modelo_entrenado.h5')
            print("Mejor modelo guardado en 'modelo_entrenado.h5'")
        
        print("Mejor configuración encontrada:", best_params)
        print("Mejor MSE:", best_score)

        return best_params, best_score


def procesar_y_entrenar_modelo(ticker, start_date, end_date, seq_len, epochs, batch_size, units):
 # Descargar datos
    df = yf.download(ticker, start=start_date, end=end_date)

    # Asegurarse de que se tienen los datos necesarios
    if df.empty or 'Open' not in df.columns or 'Close' not in df.columns:
        return jsonify({"error": "No se encontraron datos para el ticker proporcionado."}), 404
    
    
    
    seq_len = int(seq_len)  # número de pasos de tiempo
    epochs = int(epochs) # cantidad de pasadas   
    #epochs = 39
    batch_size = int(batch_size) # paquete de datos de entrada
    
    # Preprocesamiento de datos
    df.reset_index(inplace=True)
    df = df[['Date', 'Open', 'Close']]
    df.columns = ['Fecha', 'Apertura', 'Cierre']
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df.set_index('Fecha', inplace=True)

    # Normalizar ambas columnas
    scaler = MinMaxScaler()
    df[['Apertura', 'Cierre']] = scaler.fit_transform(df[['Apertura', 'Cierre']])

    # División de datos
    train_size = int(0.8 * len(df))
    train_data, test_data = df[:train_size], df[train_size:]

    # Calcular cuántos datos son el 80% y el 20%
    num_train_data = len(train_data)
    num_test_data = len(test_data)
 
   
    # Calcular cuántos meses representa cada conjunto 
    train_months, test_months = calcularMeses(train_data, test_data)
    # Calcular rango de precios
    rango_precios_desnormalizado = rangoPrecioDesnormalizado(test_data,scaler) 

   
    X_train, y_train = crear_secuencias(train_data, seq_len)
    X_test, y_test = crear_secuencias(test_data, seq_len)

    # Reshape datos para RNN
    X_train = X_train.reshape((X_train.shape[0], seq_len, 2))
    X_test = X_test.reshape((X_test.shape[0], seq_len, 2))

    # Entrenar modelo RNN
       
    # Creación y entrenamiento del modelo
    model = Sequential()
    model.add(LSTM(units=units, return_sequences=True, input_shape=(seq_len, 2)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=units))
    model.add(Dropout(0.2))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')
   
   # model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size)
    history = model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_test, y_test))
    

    # Guardar el modelo entrenado
    model.save('modelo_entrenado.h5')

  # Realizar predicciones para los datos de prueba
    y_pred = model.predict(X_test)
    y_pred = scaler.inverse_transform(np.concatenate((np.zeros((y_pred.shape[0], 1)), y_pred), axis=1))[:, 1]

    # Desnormalizar precios reales
    precios_reales_desnormalizados = precioReal(y_test,scaler)
    # Calcular MAPE
    mape = calcular_mape(precios_reales_desnormalizados, y_pred)
    print(f'MAPE: {mape:.2f}%')

    # Evaluar modelo con precios desnormalizados
    mse = np.mean((precios_reales_desnormalizados - y_pred) ** 2)
    print(f'MSE: {mse:.2f}')

    # Obtener las fechas, precios reales y predicciones
    fechas = df.index[train_size:].strftime('%Y-%m-%d').tolist()
    predicciones = y_pred.tolist()

    # Calcular el número de parámetros
    num_parametros = model.count_params()

    # Predecir el valor de apertura y cierre para el día siguiente
    X_next = df[['Apertura', 'Cierre']].values[-seq_len:].reshape((1, seq_len, 2))
    valor_predicho_para_mañana_cierre = model.predict(X_next)
    valor_predicho_para_mañana_cierre = scaler.inverse_transform(np.concatenate((np.zeros((valor_predicho_para_mañana_cierre.shape[0], 1)), 
                                                                                           valor_predicho_para_mañana_cierre), axis=1))[:, 1][0]

    # Obtener el último precio de cierre real
    ultimo_precio_real = precios_reales_desnormalizados[-1]

    # Calcular el porcentaje de crecimiento o decrecimiento
    porcentaje_cambio = ((valor_predicho_para_mañana_cierre - ultimo_precio_real) / ultimo_precio_real) * 100
    porcentaje_crecimiento = porcentaje_cambio if porcentaje_cambio > 0 else 0
    porcentaje_decrecimiento = -porcentaje_cambio if porcentaje_cambio < 0 else 0
   
   # Obtener las pérdidas de entrenamiento y validación
    training_loss = history.history['loss'][-1]  # Último valor de la lista
    validation_loss = history.history['val_loss'][-1]  # Último valor de la lista

    # Determinar si hay sobreentrenamiento
    sobreentrenado = validation_loss > training_loss and (validation_loss - training_loss) > 0.1


    # Imprimir valores relevantes para la depuración
    print("Fechas:", fechas)
    print("Precios Reales (Desnormalizados):", precios_reales_desnormalizados.tolist())
    print("Predicciones:", predicciones)
    print("MSE:", mse)
    print("Epochs:", epochs)
    print("Batch Size:", batch_size)
    print("Número de Parámetros:", num_parametros)
    print("Número de Datos de Entrenamiento:", num_train_data)
    print("Número de Datos de Prueba:", num_test_data)
    print("Meses de Entrenamiento:", train_months)
    print("Meses de Prueba:", test_months)
    print("Rango de Precios (Desnormalizado):", rango_precios_desnormalizado)
    print("Porcentaje de Crecimiento:", porcentaje_crecimiento)
    print("Porcentaje de Decrecimiento:", porcentaje_decrecimiento)
    print("Valor Predicho para el Cierre de Mañana:", valor_predicho_para_mañana_cierre)
    print("training_loss:",training_loss)
    print("validation_loss:",validation_loss)
    print("sobreentrenado:",sobreentrenado) 


    return {
        "mse": mse,
        "epochs": epochs,
        "batch_size": batch_size,
        "seq_len": seq_len,
        "units": units,
        "model": model,  # Incluye el modelo en el resultado para guardar el mejor
        "training_loss": training_loss,
        "validation_loss": validation_loss,
        "sobreentrenado": sobreentrenado
    }

def cargar_datos_con_parametros(ticker, start_date, end_date,params):
    # Aquí llamarías a cargar_datos con los parámetros de entrada ajustados
    epochs = params['epochs']
    batch_size = params['batch_size']
    seq_len = params['seq_len']
    units = params['units']
    
    # Modifica la función cargar_datos para aceptar estos parámetros dinámicamente
    resultado = procesar_y_entrenar_modelo(ticker, start_date, end_date, seq_len, epochs, batch_size, units)

    # Asegúrate de que `resultado` contenga el MSE y otros datos relevantes
    mse = resultado.get('mse', None)  # Cambia aquí dependiendo de cómo esté estructurado `resultado`
    
    return {
        "mse": mse,
        "epochs": epochs,
        "batch_size": batch_size,
        "seq_len": seq_len,
        "units": units
    }
    

@red_lstn.route('/cargar_datos', methods=['POST'])
def cargar_datos():
    # Obtener datos del request
    ticker = request.json.get('asset_type', 'AAPL')  # Obtener el ticker del request
    start_date = request.json.get('start_date', '2024-01-01')  # Fecha de inicio
    end_date = request.json.get('end_date', '2024-10-31')  # Fecha de fin
    seq_len =  request.json.get('seq_len')
    epochs = request.json.get('epochs')
    batch_size = request.json.get('batch_size')
    # Descargar datos
    df = yf.download(ticker, start=start_date, end=end_date)
    print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))

    # Asegurarse de que se tienen los datos necesarios
    if df.empty or 'Open' not in df.columns or 'Close' not in df.columns:
        return jsonify({"error": "No se encontraron datos para el ticker proporcionado."}), 404
    
    
    
    seq_len = int(seq_len)  # número de pasos de tiempo
    epochs = int(epochs) # cantidad de pasadas   
    #epochs = 39
    batch_size = int(batch_size) # paquete de datos de entrada
    
    # Preprocesamiento de datos
    df.reset_index(inplace=True)
    df = df[['Date', 'Open', 'Close']]
    df.columns = ['Fecha', 'Apertura', 'Cierre']
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df.set_index('Fecha', inplace=True)

    # Normalizar ambas columnas
    scaler = MinMaxScaler()
    df[['Apertura', 'Cierre']] = scaler.fit_transform(df[['Apertura', 'Cierre']])

    # División de datos
    train_size = int(0.8 * len(df))
    train_data, test_data = df[:train_size], df[train_size:]

    # Calcular cuántos datos son el 80% y el 20%
    num_train_data = len(train_data)
    num_test_data = len(test_data)
 
   
    # Calcular cuántos meses representa cada conjunto 
    train_months, test_months = calcularMeses(train_data, test_data)
    # Calcular rango de precios
    rango_precios_desnormalizado = rangoPrecioDesnormalizado(test_data,scaler) 

   
    X_train, y_train = crear_secuencias(train_data, seq_len)
    X_test, y_test = crear_secuencias(test_data, seq_len)

    # Reshape datos para RNN
    X_train = X_train.reshape((X_train.shape[0], seq_len, 2))
    X_test = X_test.reshape((X_test.shape[0], seq_len, 2))

    # Entrenar modelo RNN
       
    model = Sequential()
    model.add(LSTM(units=500, return_sequences=True, input_shape=(seq_len, 2)))
    model.add(Dropout(0.2))  # Añadir Dropout
    model.add(LSTM(units=500))
    model.add(Dropout(0.2))  # Añadir Dropout
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')
   
   # model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size)
    history = model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_test, y_test))

    # Guardar el modelo entrenado
    model.save('modelo_entrenado.h5')

  # Realizar predicciones para los datos de prueba
    y_pred = model.predict(X_test)
    y_pred = scaler.inverse_transform(np.concatenate((np.zeros((y_pred.shape[0], 1)), y_pred), axis=1))[:, 1]

    # Desnormalizar precios reales
    precios_reales_desnormalizados = precioReal(y_test,scaler)
    # Calcular MAPE
    mape = calcular_mape(precios_reales_desnormalizados, y_pred)
    print(f'MAPE: {mape:.2f}%')

    # Evaluar modelo con precios desnormalizados
    mse = np.mean((precios_reales_desnormalizados - y_pred) ** 2)
    print(f'MSE: {mse:.2f}')

    # Obtener las fechas, precios reales y predicciones
    fechas = df.index[train_size:].strftime('%Y-%m-%d').tolist()
    predicciones = y_pred.tolist()

    # Calcular el número de parámetros
    num_parametros = model.count_params()

    # Predecir el valor de apertura y cierre para el día siguiente
    X_next = df[['Apertura', 'Cierre']].values[-seq_len:].reshape((1, seq_len, 2))
    valor_predicho_para_mañana_cierre = model.predict(X_next)
    valor_predicho_para_mañana_cierre = scaler.inverse_transform(np.concatenate((np.zeros((valor_predicho_para_mañana_cierre.shape[0], 1)), 
                                                                                           valor_predicho_para_mañana_cierre), axis=1))[:, 1][0]

    # Obtener el último precio de cierre real
    ultimo_precio_real = precios_reales_desnormalizados[-1]

    # Calcular el porcentaje de crecimiento o decrecimiento
    porcentaje_cambio = ((valor_predicho_para_mañana_cierre - ultimo_precio_real) / ultimo_precio_real) * 100
    porcentaje_crecimiento = porcentaje_cambio if porcentaje_cambio > 0 else 0
    porcentaje_decrecimiento = -porcentaje_cambio if porcentaje_cambio < 0 else 0
   
   # Obtener las pérdidas de entrenamiento y validación
    training_loss = history.history['loss'][-1]  # Último valor de la lista
    validation_loss = history.history['val_loss'][-1]  # Último valor de la lista

    # Determinar si hay sobreentrenamiento
    sobreentrenado = validation_loss > training_loss and (validation_loss - training_loss) > 0.1


    # Imprimir valores relevantes para la depuración
    print("Fechas:", fechas)
    print("Precios Reales (Desnormalizados):", precios_reales_desnormalizados.tolist())
    print("Predicciones:", predicciones)
    print("MSE:", mse)
    print("Epochs:", epochs)
    print("Batch Size:", batch_size)
    print("Número de Parámetros:", num_parametros)
    print("Número de Datos de Entrenamiento:", num_train_data)
    print("Número de Datos de Prueba:", num_test_data)
    print("Meses de Entrenamiento:", train_months)
    print("Meses de Prueba:", test_months)
    print("Rango de Precios (Desnormalizado):", rango_precios_desnormalizado)
    print("Porcentaje de Crecimiento:", porcentaje_crecimiento)
    print("Porcentaje de Decrecimiento:", porcentaje_decrecimiento)
    print("Valor Predicho para el Cierre de Mañana:", valor_predicho_para_mañana_cierre)
    print("training_loss:",training_loss)
    print("validation_loss:",validation_loss)
    print("sobreentrenado:",sobreentrenado)
    
    # Retornar respuesta JSON
    return jsonify({
        "message": "Modelo entrenado y guardado.",
        "fechas": fechas,
        "precios_reales": precios_reales_desnormalizados.tolist(),
        "predicciones": predicciones,
        "mse": mse,
        "mape": mape,  # Agregar MAPE a la respuesta
        "epochs": epochs,
        "batch_size": batch_size,
        "num_parametros": num_parametros,
        "num_train_data": num_train_data,  # Número de datos de entrenamiento
        "num_test_data": num_test_data,      # Número de datos de prueba
        "train_months": train_months,         # Meses de entrenamiento
        "test_months": test_months,           # Meses de prueba
        "rango_precios": rango_precios_desnormalizado,       # Rango de precios
        "porcentaje_crecimiento": porcentaje_crecimiento,
        "porcentaje_decrecimiento": porcentaje_decrecimiento,
        "valor_predicho_para_mañana_cierre": valor_predicho_para_mañana_cierre,
        "training_loss": training_loss,
        "validation_loss": validation_loss,
        "sobreentrenado": sobreentrenado  # True si el modelo está sobreentrenado
    })

@red_lstn.route('/utilizar_datos_entrenado', methods=['POST'])
def utilizar_datos_entrenado():
    ticker = request.json.get('asset_type', 'AAPL')  # Obtener el ticker del request
    start_date = request.json.get('start_date', '2024-01-01')  # Fecha de inicio
    end_date = request.json.get('end_date', '2024-10-31')  # Fecha de fin

    # Descargar datos
    df = yf.download(ticker, start=start_date, end=end_date)

    # Asegurarse de que se tienen los datos necesarios
    if df.empty or 'Open' not in df.columns or 'Close' not in df.columns:
        return jsonify({"error": "No se encontraron datos para el ticker proporcionado."}), 404

    # Cargar el modelo previamente guardado
    model = load_model('modelo_entrenado.h5')

    # Preprocesamiento de datos
    df.reset_index(inplace=True)
    df = df[['Date', 'Open', 'Close']]
    df.columns = ['Fecha', 'Apertura', 'Cierre']
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df.set_index('Fecha', inplace=True)

    # Normalizar ambas columnas (debe usar el mismo scaler que se utilizó para el entrenamiento)
    scaler = MinMaxScaler()
    df[['Apertura', 'Cierre']] = scaler.fit_transform(df[['Apertura', 'Cierre']])

    # Dividir los datos en entrenamiento y prueba según tu lógica (aquí ejemplo)
    test_data = df[-seq_len:]  # Tomar los últimos 'seq_len' como datos de prueba

    # Preparar datos para RNN (usar el mismo seq_len)
    seq_len = 60
    X_new = df[['Apertura', 'Cierre']].values[-seq_len:].reshape((1, seq_len, 2))

    # Realizar predicciones con el modelo cargado
    y_pred = model.predict(X_new)
    y_pred = scaler.inverse_transform(np.concatenate((np.zeros((y_pred.shape[0], 1)), y_pred), axis=1))[:, 1]

    # Obtener las fechas de las predicciones
    fechas_predicciones = df.index[-len(y_pred):].strftime('%Y-%m-%d').tolist()

    # Calcular el MSE si hay suficientes datos reales para comparar
    real_values = df['Cierre'].values[-len(y_pred):]  # Obtener los valores reales
    mse = np.mean((real_values - y_pred) ** 2) if len(real_values) == len(y_pred) else None

    # Calcular rango de precios desnormalizado para los datos de prueba
    precio_min_normalizado = test_data['Cierre'].min()
    precio_max_normalizado = test_data['Cierre'].max()

    # Desnormalizar precios mínimo y máximo
    precio_min_desnormalizado = scaler.inverse_transform(
        np.concatenate((np.zeros((1, 1)), [[precio_min_normalizado]]), axis=1)
    )[0, 1]
    precio_max_desnormalizado = scaler.inverse_transform(
        np.concatenate((np.zeros((1, 1)), [[precio_max_normalizado]]), axis=1)
    )[0, 1]

    # Calcular el rango de precios desnormalizado
    rango_precios_desnormalizado = (precio_min_desnormalizado, precio_max_desnormalizado)

    # Aquí necesitarás tener definidos los siguientes valores, asumiendo que son parte del entrenamiento anterior
    epochs = 39  # Define el número de épocas que usaste al entrenar
    batch_size = 64  # Define el tamaño de lote utilizado al entrenar
    num_parametros = model.count_params()  # Cantidad de parámetros en el modelo
    num_train_data = 0  # Debes calcular esto basado en tus datos de entrenamiento
    num_test_data = 0   # Debes calcular esto basado en tus datos de prueba
    train_months = 0    # Calcular meses de entrenamiento
    test_months = 0     # Calcular meses de prueba

    # Retornar respuesta JSON
    return jsonify({
        "message": "Predicciones realizadas con el modelo cargado.",
        "predicciones": y_pred.tolist(),
        "fechas": fechas_predicciones,
        "mse": mse,
        "epochs": epochs,
        "batch_size": batch_size,
        "num_parametros": num_parametros,
        "num_train_data": num_train_data,
        "num_test_data": num_test_data,
        "train_months": train_months,
        "test_months": test_months,
        "rango_precios": rango_precios_desnormalizado
    })



@red_lstn.route('/envia_parada', methods=['POST'])
def enviar_parada():
    data = request.json  # Obtener datos JSON del cuerpo de la solicitud
    parar = data.get('parar', False)  # Obtener el estado del checkbox
    
    # Aquí puedes realizar cualquier acción que necesites con el valor de 'parar'
    print(f"Estado de parada: {parar}")
    
    # Responder al cliente
    return jsonify({"message": "Estado de parada recibido", "parar": parar})
