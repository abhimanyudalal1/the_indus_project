import pandas as pd

def datesync(in_path, out_path, df=None, start_date='2000-06-01', end_date='2026-01-01',date_col=None):
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
    if df is None: 
        df= pd.read_csv(in_path)

    if date_col in df.columns:
        df[date_col]= pd.to_datetime(df[date_col])
        df = df.set_index(date_col)
    elif isinstance(df.index, pd.DatetimeIndex):
        df.index= pd.to_datetime(df.index)
    else:
        raise ValueError("No valid date column or datetime index found")

    df_filtered= df.loc[start_date:end_date]
    df_filtered.to_csv(out_path)

    return df_filtered

