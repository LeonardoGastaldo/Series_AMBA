"""Utilidades compartidas para los notebooks de Deep Learning (08_lstm) y
librerías multi-modelo (09_prophet_neuralprophet, 10_darts).

Sigue el mismo patrón que usa la cátedra en los ejemplos de Clase 6
(`crear_dataset_supervisado`, `escalar_dataset`), adaptado a nuestras series.
"""

import numpy as np
from sklearn.preprocessing import MinMaxScaler


def crear_dataset_supervisado(array: np.ndarray, input_length: int, output_length: int = 1):
    """Convierte un array 1D en (X, Y) para aprendizaje supervisado con ventana
    deslizante: X tiene forma (n_muestras, input_length), Y tiene forma
    (n_muestras, output_length)."""
    X, Y = [], []
    n = len(array) - input_length - output_length + 1
    for i in range(n):
        X.append(array[i : i + input_length])
        Y.append(array[i + input_length : i + input_length + output_length])
    return np.array(X), np.array(Y)


def escalar_serie(train: np.ndarray, *otras: np.ndarray, rango=(-1, 1)):
    """Ajusta un MinMaxScaler sólo con `train` (evita fuga de información) y
    transforma `train` y cualquier otra serie adicional (val/test) con el
    mismo scaler. Devuelve (scaler, train_escalado, *otras_escaladas)."""
    scaler = MinMaxScaler(feature_range=rango)
    train_s = scaler.fit_transform(train.reshape(-1, 1)).flatten()
    otras_s = [scaler.transform(o.reshape(-1, 1)).flatten() for o in otras]
    return (scaler, train_s, *otras_s)
