from flask import Flask, request, jsonify
from prophet import Prophet
import pandas as pd

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/anomaly', methods=['POST'])
def anomaly_detection():
    """
    Expects a JSON payload like:
    {
       "data": [
         {"ds": "2024-01-01", "y": 100.0},
         {"ds": "2024-01-02", "y": 120.0},
         ...
       ]
    }
    Returns:
    {
       "anomalies": [
          {"ds": "2024-01-05", "y": 80.0, "yhat_lower": 110.0, ...},
          ...
       ]
    }
    """
    payload = request.get_json()
    data = payload.get('data', [])

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df['ds'] = pd.to_datetime(df['ds'])

    # Fit Prophet
    m = Prophet(weekly_seasonality=True, yearly_seasonality=False)
    m.fit(df)

    # Forecast
    future = m.make_future_dataframe(periods=7, freq='D')
    forecast = m.predict(future)

    # Merge to compare actual vs. forecast (for historical part)
    merged = pd.merge(
        df,
        forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
        on='ds',
        how='left'
    )

    # Flag anomalies
    merged['anomaly'] = (
        (merged['y'] < merged['yhat_lower']) |

        (merged['y'] > merged['yhat_upper'])
    )

    anomalies = merged[merged['anomaly']].to_dict(orient='records')
    return jsonify({"anomalies": anomalies, "forecast": forecast.to_dict(orient='records'), "merged": merged.to_dict(orient='records')})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
