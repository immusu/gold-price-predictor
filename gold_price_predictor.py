import pandas as pd
import joblib
import os
import argparse
from sklearn.metrics import mean_squared_error, r2_score
from statsmodels.tsa.holtwinters import ExponentialSmoothing

MODEL_DIR = 'hw_models'
SERIES = ['k18', 'k21', 'k22', 'traditional']


def train_and_save(csv_path: str, test_size: float):
    df = pd.read_csv(csv_path, parse_dates=['date']).set_index('date')
    os.makedirs(MODEL_DIR, exist_ok=True)
    n_test = int(len(df) * test_size)
    train_df = df.iloc[:-n_test]
    test_df = df.iloc[-n_test:]
    metrics = {}
    print(f"Training Exponential Smoothing models; test size = {test_size:.2f}\n")
    for col in SERIES:
        print(f"Processing series: {col}")
        train_series = train_df[col]
        test_series = test_df[col]
        # Fit Holt-Winters: additive trend and weekly seasonality
        model = ExponentialSmoothing(
            train_series,
            trend='add',
            seasonal='add',
            seasonal_periods=7,
            initialization_method='estimated'
        ).fit(optimized=True)
        # Forecast
        preds = model.forecast(steps=n_test)
        mse = mean_squared_error(test_series, preds)
        r2 = r2_score(test_series, preds)
        metrics[col] = {'mse': mse, 'r2': r2}
        print(f"  MSE = {mse:.2f}, R2 = {r2:.4f}\n")
        # Refit on full data and save
        full_model = ExponentialSmoothing(
            df[col], trend='add', seasonal='add', seasonal_periods=7,
            initialization_method='estimated'
        ).fit(optimized=True)
        joblib.dump(full_model, os.path.join(MODEL_DIR, f"{col}.pkl"))
    print(f"Models saved in '{MODEL_DIR}/'\n")
    print("Summary of metrics:")
    for col, m in metrics.items():
        print(f"{col}: MSE={m['mse']:.2f}, R2={m['r2']:.4f}")


def predict_date(date_str: str, csv_path: str):
    df = pd.read_csv(csv_path, parse_dates=['date']).set_index('date')
    last_date = df.index.max()
    date = pd.to_datetime(date_str)
    steps = (date - last_date).days
    if steps < 0:
        # return actual
        row = df.loc[date]
        print(f"Date {date_str} within data; returning actuals.")
        return row.to_dict()
    forecasts = {}
    for col in SERIES:
        model_path = os.path.join(MODEL_DIR, f"{col}.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model for {col} not found. Run with --train first.")
        model = joblib.load(model_path)
        preds = model.forecast(steps=steps)
        forecasts[col] = float(preds.iloc[-1])
    return forecasts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Gold price forecasting with Holt-Winters")
    parser.add_argument('--csv', type=str, default='output_filled.csv', help='Path to filled CSV')
    parser.add_argument('--train', action='store_true', help='Train and evaluate models')
    parser.add_argument('--predict', type=str, help='YYYY-MM-DD to forecast')
    parser.add_argument('--test-size', type=float, default=0.2, help='Fraction of last data as test set')
    args = parser.parse_args()

    if args.train:
        train_and_save(args.csv, args.test_size)
    elif args.predict:
        preds = predict_date(args.predict, args.csv)
        print(f"Forecasts for {args.predict}:")
        for k, v in preds.items():
            print(f"  {k}: {v*11.664:.2f}")
    else:
        parser.print_help()
