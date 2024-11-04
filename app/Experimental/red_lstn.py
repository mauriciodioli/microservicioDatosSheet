from flask import Blueprint, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from keras.models import Sequential, load_model  # Importar load_model
from keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
from dotenv import load_dotenv
import os

load_dotenv()

# Definir el Blueprint
red_lstn = Blueprint('red_lstn', __name__)

@red_lstn.route('/cargar_datos', methods=['POST'])
def cargar_datos():
    # Obtener datos del request
    ticker = request.json.get('asset_type', 'AAPL')  # Obtener el ticker del request
    start_date = request.json.get('start_date', '2024-01-01')  # Fecha de inicio
    end_date = request.json.get('end_date', '2024-10-31')  # Fecha de fin

    # Descargar datos
    df = yf.download(ticker, start=start_date, end=end_date)

    # Asegurarse de que se tienen los datos necesarios
    if df.empty or 'Open' not in df.columns or 'Close' not in df.columns:
        return jsonify({"error": "No se encontraron datos para el ticker proporcionado."}), 404

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
    train_months = (train_data.index[-1] - train_data.index[0]).days / 30
    test_months = (test_data.index[-1] - test_data.index[0]).days / 30 if not test_data.empty else 0

  
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
   
    # Preparar datos para RNN
    def crear_secuencias(data, seq_len):
        X, y = [], []
        for i in range(len(data) - seq_len):
            X.append(data.iloc[i:i + seq_len][['Apertura', 'Cierre']].values)
            y.append(data.iloc[i + seq_len]['Cierre'])
        return np.array(X), np.array(y)

    seq_len = 60  # número de pasos de tiempo
    X_train, y_train = crear_secuencias(train_data, seq_len)
    X_test, y_test = crear_secuencias(test_data, seq_len)

    # Reshape datos para RNN
    X_train = X_train.reshape((X_train.shape[0], seq_len, 2))
    X_test = X_test.reshape((X_test.shape[0], seq_len, 2))

    # Entrenar modelo RNN
    model = Sequential()
    model.add(LSTM(units=500, return_sequences=True, input_shape=(seq_len, 2)))
    model.add(LSTM(units=500))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')

    # Entrenar el modelo
    #epochs = 39
    epochs = 6
    batch_size = 64
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size)

    # Guardar el modelo entrenado
    model.save('modelo_entrenado.h5')

  # Realizar predicciones para los datos de prueba
    y_pred = model.predict(X_test)
    y_pred = scaler.inverse_transform(np.concatenate((np.zeros((y_pred.shape[0], 1)), y_pred), axis=1))[:, 1]

    # Desnormalizar precios reales
    precios_reales_desnormalizados = scaler.inverse_transform(np.concatenate((np.zeros((len(y_test), 1)), y_test.reshape(-1, 1)), axis=1))[:, 1]

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
    valor_predicho_para_mañana_cierre = scaler.inverse_transform(np.concatenate((np.zeros((valor_predicho_para_mañana_cierre.shape[0], 1)), valor_predicho_para_mañana_cierre), axis=1))[:, 1][0]

    # Obtener el último precio de cierre real
    ultimo_precio_real = precios_reales_desnormalizados[-1]

    # Calcular el porcentaje de crecimiento o decrecimiento
    porcentaje_cambio = ((valor_predicho_para_mañana_cierre - ultimo_precio_real) / ultimo_precio_real) * 100
    porcentaje_crecimiento = porcentaje_cambio if porcentaje_cambio > 0 else 0
    porcentaje_decrecimiento = -porcentaje_cambio if porcentaje_cambio < 0 else 0
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
    # Retornar respuesta JSON
    return jsonify({
        "message": "Modelo entrenado y guardado.",
        "fechas": fechas,
        "precios_reales": precios_reales_desnormalizados.tolist(),
        "predicciones": predicciones,
        "mse": mse,
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
        "valor_predicho_para_mañana_cierre": valor_predicho_para_mañana_cierre
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
