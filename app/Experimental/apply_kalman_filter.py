from scipy.signal import argrelextrema
import pandas as pd
import numpy as np
import yfinance as yf
from arch import arch_model
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt

def butter_lowpass_filter(data, cutoff_frequency, fs, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff_frequency / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

def process_data(tickers, start_date, end_date):
    data = yf.download(tickers, start=start_date, end=end_date)['Adj Close']
    print(f"Datos obtenidos:\n{data.head()}")
    
    returns = data.pct_change().dropna()
    print(f"Retornos diarios calculados:\n{returns.head()}")
    return data, returns

def apply_logarithmic_filter(returns):
    print("Aplicando filtro logarítmico a los retornos...")
    log_returns = np.log(1 + returns)
    print(f"Retornos logarítmicos:\n{log_returns.head()}")
    
    mean_log_returns = log_returns.mean()
    if mean_log_returns > 0:
        print("Hay una tendencia hacia arriba en los retornos logarítmicos.")
    elif mean_log_returns < 0:
        print("Hay una tendencia hacia abajo en los retornos logarítmicos.")
    else:
        print("No hay una tendencia clara en los retornos logarítmicos.")
    
    return log_returns

def find_peaks(log_returns):
    max_idx = argrelextrema(log_returns.values, np.greater)[0]
    min_idx = argrelextrema(log_returns.values, np.less)[0]
    
    max_dates = log_returns.index[max_idx]
    min_dates = log_returns.index[min_idx]
    
    return max_dates, min_dates

def calculate_days_between_peaks(max_dates, min_dates):
    # Check if input is None or empty
    if max_dates is None or min_dates is None or len(max_dates) == 0 or len(min_dates) == 0:
        raise ValueError("max_dates and min_dates must not be None or empty")
    
    # Convertir las fechas a un array de días usando la propiedad 'days'
    try:
        days_between_max = np.diff(max_dates.values).astype('timedelta64[D]').astype(int)
        days_between_min = np.diff(min_dates.values).astype('timedelta64[D]').astype(int)
    except Exception as e:
        raise ValueError("Failed to calculate days between peaks: {}".format(str(e)))
    
    return days_between_max, days_between_min

def apply_garch_filter(ticker, returns, cutoff_frequency=0.1, fs=1):
    print(f"Procesando {ticker}...")
    model = arch_model(returns, vol='Garch', p=1, q=1)
    model_fit = model.fit(disp='off')
    volatility_forecast_garch = model_fit.conditional_volatility
    print(f"Volatilidad forecast (GARCH) para {ticker}:\n{volatility_forecast_garch.head()}")

    if len(volatility_forecast_garch) > 18:
        smoothed_volatility_garch = butter_lowpass_filter(volatility_forecast_garch, cutoff_frequency, fs=fs, order=5)
        print(f"Volatilidad suavizada (Butterworth) para {ticker}:\n{smoothed_volatility_garch}")  # Imprimir todos los valores
    else:
        print(f"Datos insuficientes para aplicar el filtro Butterworth a {ticker}")


def find_dates_for_average_days(days_between_dates, average_days, min_dates):
    dates_for_average_days = []
    for i in range(len(days_between_dates)):
        if days_between_dates[i] == average_days:
            dates_for_average_days.append(min_dates[i + 1])  # Agregar la fecha del siguiente mínimo
    return dates_for_average_days

def main():
    tickers = ['GGAL']
    start_date = '2012-09-17'
    end_date = '2024-06-24'
    
    print("Iniciando el proceso...")
    data, returns = process_data(tickers, start_date, end_date)
    
    log_returns = apply_logarithmic_filter(returns)
    
    max_dates, min_dates = find_peaks(log_returns)
    print(f"Fechas de picos máximos:\n{max_dates}")
    print(f"Fechas de picos mínimos:\n{min_dates}")
    
    days_between_max, days_between_min = calculate_days_between_peaks(max_dates, min_dates)
    print(f"Días entre picos máximos:\n{days_between_max}")
    media_dias_entre_picos_min = np.mean(days_between_min)
    print(f"La media de los días entre picos mínimos es: {media_dias_entre_picos_min}")
    print(f"Días entre picos mínimos:\n{days_between_min}")
    
    media_dias_entre_picos_max = np.mean(days_between_max)
    print(f"La media de los días entre picos máximos es: {media_dias_entre_picos_max}")
    
    fechas_promedio_baja = find_dates_for_average_days(days_between_min, media_dias_entre_picos_min, min_dates)
    fechas_promedio_suba = find_dates_for_average_days(days_between_max, media_dias_entre_picos_max, max_dates)

    for i in range(len(fechas_promedio_baja)):
        print(f"Fechas de baja cuando se cumplen los {media_dias_entre_picos_min} días: {fechas_promedio_baja[i]}")
        print(f"Fechas de suba cuando se cumplen los {media_dias_entre_picos_max} días: {fechas_promedio_suba[i]}")
    
    for ticker in tickers:
        try:
            if isinstance(returns, pd.Series):
                ticker_returns = returns.dropna()
            else:
                ticker_returns = returns[ticker].dropna()
            apply_garch_filter(ticker, ticker_returns)
        except KeyError as e:
            print(f"Error procesando {ticker}: {e}")
            
    

if __name__ == "__main__":
    main()
