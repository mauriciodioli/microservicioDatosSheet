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
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical
import os
from io import BytesIO
import base64
import math

load_dotenv()

# Definir el Blueprint
analisis_por_primos = Blueprint('analisis_por_primos', __name__)

# Verificar si un número es primo utilizando el Teorema de Wilson
def es_primo_wilson(n):
    if n < 2:
        return False
    if n == 2:
        return True
    return math.factorial(n - 1) % n == n - 1

@analisis_por_primos.route('/experimental_analisis_por_primos_busca_primos/', methods=['POST'])
def experimental_analisis_por_primos_busca_primos():
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

  # Total de valores
    total_open = len(df['Apertura'])
    total_close = len(df['Cierre'])


    total = sumaValores(df)



    # Identificar valores primos en Apertura y Cierre
    df['Apertura_Primo'] = df['Apertura'].apply(lambda x: es_primo_wilson(int(x)) if x.is_integer() else False)
    df['Cierre_Primo'] = df['Cierre'].apply(lambda x: es_primo_wilson(int(x)) if x.is_integer() else False)

    # Filtrar valores primos
    open_primos = df[df['Apertura_Primo']]
    close_primos = df[df['Cierre_Primo']]

 # Cantidad de valores primos
    total_open_primos = len(open_primos)
    total_close_primos = len(close_primos)

    # Imprimir los totales para depuración
    print(f"Total valores enviados - Apertura: {total_open}, Cierre: {total_close}")
    print(f"Total valores primos - Apertura: {total_open_primos}, Cierre: {total_close_primos}")


    # Crear gráfico de coordenadas polares si hay valores primos
    if not open_primos.empty or not close_primos.empty:
       
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, polar=True)

        # Convertir fechas a ángulos
        open_angles = [i.timestamp() % (2 * math.pi) for i in open_primos.index] if not open_primos.empty else []
        close_angles = [i.timestamp() % (2 * math.pi) for i in close_primos.index] if not close_primos.empty else []

        # Imprimir los vectores x (ángulos) e y (valores)
        if open_angles:
            print("Open Primos - Ángulos (x):", open_angles)
            print("Open Primos - Aperturas (y):", open_primos['Apertura'].tolist())
        if close_angles:
            print("Close Primos - Ángulos (x):", close_angles)
            print("Close Primos - Cierres (y):", close_primos['Cierre'].tolist())

        # Graficar
        if open_angles:
            ax.scatter(open_angles, open_primos['Apertura'], label='Apertura Primos', color='blue', alpha=0.7)
        if close_angles:
            ax.scatter(close_angles, close_primos['Cierre'], label='Cierre Primos', color='red', alpha=0.7)

        ax.legend()
        ax.set_title('Números Primos en Apertura y Cierre (Coordenadas Polares)')

        # Guardar gráfico en base64
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')

        return jsonify({"plot": plot_url})

    # Si no hay valores primos, retornar mensaje adecuado
    return jsonify({"message": "No se encontraron valores primos en los datos proporcionados."})


@analisis_por_primos.route('/experimental_analisis_por_todos/', methods=['POST'])
def experimental_analisis_por_todos():
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

  # Total de valores
    total_open = len(df['Apertura'])
    total_close = len(df['Cierre'])
    

    total = sumaValores(df)
    
    
    tiempo = 24
    # Llamar a la función para el análisis diario
    df_resampled, resultados = definicionDePosiblesResultados(df, periodo='H')

    # Imprimir el DataFrame resampleado con las categorías
    print("Datos resampleados con categorías:")
    print(df_resampled)

    # Imprimir el DataFrame con los resultados de las categorías
    print("\nResultados de las categorías:")
    print(resultados)


    df_resampled_bajista, resultados_bajista =definicionDePosiblesResultados_bajista(df, periodo='H')
    # Imprimir el DataFrame resampleado con las categorías
    print("Datos resampleados con categorías bajistas:")
    print(df_resampled_bajista)

    # Imprimir el DataFrame con los resultados de las categorías
    print("\nResultados de las categoríasbajistas :")
    print(resultados_bajista)
    
    return jsonify({'total_valores': df_resampled})

def sumaValores(df):
    # Total de valores
    total_open = len(df['Apertura'])
    total_close = len(df['Cierre'])

    # Suma total de valores
    total_valores = total_open + total_close

    return jsonify({'total_valores': total_valores})


import numpy as np
import pandas as pd

def definicionDePosiblesResultados(df, periodo='D'):
    """
    Compara los precios de apertura y cierre para cada período especificado y asigna una categoría.
    También calcula el porcentaje de ocurrencia de cada categoría.
    """
    # Asegurarse de que el índice sea de tipo datetime
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        df.index = pd.to_datetime(df.index)  # Convertir el índice a datetime si no lo es

    # Resamplear los datos según el período
    df_resampled = df.resample(periodo).agg({'Apertura': 'first', 'Cierre': 'last'})

    # Calcular el porcentaje de cambio
    df_resampled['Porcentaje_Cambio'] = ((df_resampled['Cierre'] - df_resampled['Apertura']) / df_resampled['Apertura']) * 100
 # Calcular el porcentaje de cambio
    df_resampled['Porcentaje_Cambio'] = (( df_resampled['Apertura']- df_resampled['Cierre'] ) / df_resampled['Cierre']) * 100
    # Eliminar filas con NaN en 'Apertura', 'Cierre' o 'Porcentaje_Cambio'
    df_resampled = df_resampled.dropna(subset=['Apertura', 'Cierre', 'Porcentaje_Cambio'])

    # Asignar categorías basadas en el porcentaje de cambio
    conditions = [
        df_resampled['Porcentaje_Cambio'] <= -1.5,
        (df_resampled['Porcentaje_Cambio'] > -1.5) & (df_resampled['Porcentaje_Cambio'] <= 3),
        (df_resampled['Porcentaje_Cambio'] > 3) & (df_resampled['Porcentaje_Cambio'] <= 10),
        df_resampled['Porcentaje_Cambio'] > 10
    ]
    
    # Asignar las categorías con el porcentaje real
    df_resampled['Categoria'] = np.select(
        conditions,
        [
            f'amague ({df_resampled["Porcentaje_Cambio"].where(conditions[0]).round(2).fillna(0).astype(str)}%)',
            f'leve ({df_resampled["Porcentaje_Cambio"].where(conditions[1]).round(2).fillna(0).astype(str)}%)',
            f'moderado ({df_resampled["Porcentaje_Cambio"].where(conditions[2]).round(2).fillna(0).astype(str)}%)',
            f'alto ({df_resampled["Porcentaje_Cambio"].where(conditions[3]).round(2).fillna(0).astype(str)}%)'
        ],
        default='Otro'
    )

    # Calcular el porcentaje de ocurrencia de cada categoría
    categoria_counts = df_resampled['Categoria'].value_counts()
    total_count = df_resampled['Categoria'].count()
    porcentaje_ocurrencia = (categoria_counts / total_count) * 100

    # Crear un DataFrame para mostrar los resultados
    resultados = pd.DataFrame({
        'Cantidad': categoria_counts,
        'Porcentaje': porcentaje_ocurrencia
    })

    return df_resampled, resultados



def definicionDePosiblesResultados_bajista(df, periodo='D'):
    """
    Compara los precios de apertura y cierre para cada período especificado y asigna una categoría.
    También calcula el porcentaje de ocurrencia de cada categoría.
    """
    # Asegurarse de que el índice sea de tipo datetime
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        df.index = pd.to_datetime(df.index)  # Convertir el índice a datetime si no lo es

    # Resamplear los datos según el período
    df_resampled = df.resample(periodo).agg({'Apertura': 'first', 'Cierre': 'last'})

    # Calcular el porcentaje de cambio como valor absoluto
    df_resampled['Porcentaje_Cambio'] = abs((df_resampled['Apertura'] - df_resampled['Cierre']) / df_resampled['Cierre']) * 100

    # Eliminar filas con NaN en 'Apertura', 'Cierre' o 'Porcentaje_Cambio'
    df_resampled = df_resampled.dropna(subset=['Apertura', 'Cierre', 'Porcentaje_Cambio'])

    # Asignar categorías basadas en el porcentaje de cambio
    conditions = [
        df_resampled['Porcentaje_Cambio'] <= 1.5,
        (df_resampled['Porcentaje_Cambio'] > 1.5) & (df_resampled['Porcentaje_Cambio'] <= 3),
        (df_resampled['Porcentaje_Cambio'] > 3) & (df_resampled['Porcentaje_Cambio'] <= 10),
        df_resampled['Porcentaje_Cambio'] > 10
    ]
    
    # Asignar las categorías con el porcentaje real
    df_resampled['Categoria'] = np.select(
        conditions,
        [
            f'amague ({df_resampled["Porcentaje_Cambio"].where(conditions[0]).round(2).fillna(0).astype(str)}%)',
            f'leve ({df_resampled["Porcentaje_Cambio"].where(conditions[1]).round(2).fillna(0).astype(str)}%)',
            f'moderado ({df_resampled["Porcentaje_Cambio"].where(conditions[2]).round(2).fillna(0).astype(str)}%)',
            f'alto ({df_resampled["Porcentaje_Cambio"].where(conditions[3]).round(2).fillna(0).astype(str)}%)'
        ],
        default='Otro'
    )

    # Calcular el porcentaje de ocurrencia de cada categoría
    categoria_counts = df_resampled['Categoria'].value_counts()
    total_count = df_resampled['Categoria'].count()
    porcentaje_ocurrencia = (categoria_counts / total_count) * 100

    # Crear un DataFrame para mostrar los resultados
    resultados = pd.DataFrame({
        'Cantidad': categoria_counts,
        'Porcentaje': porcentaje_ocurrencia
    })

    return df_resampled, resultados