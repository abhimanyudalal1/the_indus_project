# The Indus Project

## Project Overview
This project focuses on hydrological modeling of the Indus river basin (or specific sub-basins) using physically-based statistical approaches. The goal is to predict runoff based on meteorological and remote sensing data.

## Methodology
The current implementation uses a **Baseline Physics Model** which incorporates:
- **Precipitation**: Analysis of rainfall patterns (lagged).
- **Snow Cover Area (SCA)**: Satellite-derived snow cover data.
- **Degree Days (DD)**: Temperature-based melt index.
- **Evapotranspiration (ET)**: Water loss estimation.
- **Melt Proxy**: Interaction term between SCA and Degree Days.

We utilize `scikit-learn` for regression modeling (Linear Regression) and evaluate performance using hydrological metrics like **Nash-Sutcliffe Efficiency (NSE)** and **Root Mean Squared Error (RMSE)**.

## Project Structure
- `modelwithetloss.ipynb`: Main Jupyter notebook for data loading, processing, model training, and evaluation.
- `data_downloader.py`: Script for fetching necessary datasets.
- `final_data_physics_baseline/`: Directory containing processed input data (CSV files).

## Dependencies
- Python 3.x
- pandas
- numpy
- scikit-learn
- matplotlib
- seaborn

## Usage
1. Ensure all dependencies are installed.
2. Run `data_downloader.py` to fetch/update data if necessary.
3. Open `modelwithetloss.ipynb` to run the analysis pipeline:
   - Data cleaning and index handling.
   - Feature engineering (creating lag variables).
   - Model training (Train/Validation/Test splits).
   - Performance evaluation (NSE, RMSE).
