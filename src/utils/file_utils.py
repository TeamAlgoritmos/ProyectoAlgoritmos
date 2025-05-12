import pandas as pd

def load_network_data(filepath):
    """Carga los datos de la red vial desde CSV"""
    return pd.read_csv(filepath)

def load_points_of_interest(filepath):
    """Carga los puntos de interés desde CSV"""
    return pd.read_csv(filepath)