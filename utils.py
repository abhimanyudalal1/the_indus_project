from duckdb import Value
import pandas as pd

def datesync(in_path=None, out_path=None, df=None, start_date='2000-06-01', end_date='2026-01-01',date_col=None):
    """
    Synchronize date range in a DataFrame and save to CSV
    
    Args:
        in_path: Path to input CSV
        out_path: Path to output CSV
        df: Optional pre-loaded DataFrame (if None, reads from in_path)
        date_col: Name of date column (default 'date')
        start_date: Start of date range
        end_date: End of date range
    """
    if df is None and in_path is None:
        raise ValueError("Either 'df' or 'in_path' must be provided")
    if df is None: 
        df= pd.read_csv(in_path)

    if date_col is None:
        if isinstance(df.index, pd.DatetimeIndex):
            pass
        else:
            common_date_columns= ['date','Date','DATE']
            date_col = next((col for col in common_date_columns if col in df.columns),None)
        if date_col is None:
            for col in df.columns:
                try:
                    pd.to_datetime(df[col])
                    date_col = col
                    break
                except:
                    continue

        if date_col is None:
            raise ValueError('No date column found. Please specify the date_col parameter')

    if date_col and date_col in df.columns:
        df[date_col]= pd.to_datetime(df[date_col])
        df = df.set_index(date_col)
    elif isinstance(df.index, pd.DatetimeIndex):
        df.index= pd.to_datetime(df.index)
    else:
        raise ValueError("No valid date column or datetime index found")

    df_filtered= df.loc[start_date:end_date]
    if out_path is None:
        df_filtered.to_csv(f'{in_path}_processed.csv')
    else:
        df_filtered.to_csv(out_path)


    return df_filtered

#####
from sklearn.linear_model import LinearRegression
def create_lag(df, lag_sca, lag_dd, lag_precip, lag_et):
    df['sca_lagged'] = df['sca'].shift(lag_sca)
    df['dd_lagged'] = df['dd'].shift(lag_dd)
    df['et_loss_lagged'] = df['et_loss'].shift(lag_et)
    df['melt_proxy'] = df['sca_lagged']*df['dd_lagged']
    df['precipitation_lagged'] = df['precipitation'].shift(lag_precip)
    df['precipitation_lagged-1'] = df['precipitation'].shift(lag_precip-1)
    df['precipitation_lagged_cum'] = ((df['precipitation']+df['precipitation_lagged'])/2)
    
    df_clean = df.dropna()

    return df_clean

#####
import numpy as np
def calculate_nse(observed, predicted):
    mean_obs = np.mean(observed)
    numerator = np.sum((observed - predicted) ** 2)
    denominator = np.sum((observed - mean_obs) ** 2)
    return 1 - (numerator / denominator)