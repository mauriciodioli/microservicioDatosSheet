from flask import Blueprint, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from keras.models import Sequential
from keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
from dotenv import load_dotenv

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

    # Preparar datos para RNN
    def crear_secuencias(data, seq_len):
        X, y = [], []
        for i in range(len(data) - seq_len):
            X.append(data.iloc[i:i+seq_len][['Apertura', 'Cierre']].values)
            y.append(data.iloc[i+seq_len]['Cierre'])
        return np.array(X), np.array(y)

    seq_len = 10  # número de pasos de tiempo
    X_train, y_train = crear_secuencias(train_data, seq_len)
    X_test, y_test = crear_secuencias(test_data, seq_len)

    # Reshape datos para RNN
    X_train = X_train.reshape((X_train.shape[0], seq_len, 2))
    X_test = X_test.reshape((X_test.shape[0], seq_len, 2))

    # Entrenar modelo RNN
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(seq_len, 2)))
    model.add(LSTM(units=50))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')

    model.fit(X_train, y_train, epochs=50, batch_size=32)

    # Realizar predicciones
    y_pred = model.predict(X_test)
    y_pred = scaler.inverse_transform(np.concatenate((np.zeros((y_pred.shape[0], 1)), y_pred), axis=1))[:, 1]

    # Evaluar modelo
    mse = np.mean((y_test - y_pred) ** 2)
    print(f'MSE: {mse:.2f}')

    # Obtener las fechas, precios reales y predicciones
    fechas = df.index[train_size:].strftime('%Y-%m-%d').tolist()
    precios_reales = df['Cierre'][train_size:].tolist()
    predicciones = y_pred.tolist()

    # Retornar respuesta JSON
  
    
    
    return jsonify({
    "message": "Modelo entrenado y predicciones realizadas.",
    "fechas": fechas,
    "precios_reales": precios_reales,
    "predicciones": predicciones
})
