from flask import Flask, request, render_template_string
import yfinance as yf
import pandas as pd

app = Flask(__name__)

HTML = '''<!DOCTYPE html>
<html>
<head><title>Stock Predictor</title>
<style>
    body { font-family: Arial; margin: 40px; }
    input, select { padding: 8px; margin: 5px; }
    button { padding: 8px 16px; background: #007bff; color: white; border: none; cursor: pointer; }
    table { border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
    th { background: #f2f2f2; }
</style>
</head>
<body>
<h1>?? Stock Predictor</h1>
<form method="GET">
    Symbol: <input name="symbol" value="{{ symbol }}" placeholder="AAPL">
    Period:
    <select name="period">
        {% for p in ['1d','5d','1mo','3mo','6mo','1y'] %}
        <option value="{{ p }}" {% if period==p %}selected{% endif %}>{{ p }}</option>
        {% endfor %}
    </select>
    <button>Get Data</button>
</form>
{% if error %}<p style="color:red">Error: {{ error }}</p>{% endif %}
{% if table %}
    <h3>Latest Close: ${{ latest }}</h3>
    <h3>Last 10 Days</h3>
    {{ table | safe }}
{% endif %}
</body>
</html>'''

@app.route('/')
def index():
    symbol = request.args.get('symbol', 'AAPL').upper()
    period = request.args.get('period', '1mo')
    error = None
    table = None
    latest = None
    try:
        df = yf.download(symbol, period=period, progress=False)
        if df.empty:
            error = "No data"
        else:
            latest = f"{df['Close'].iloc[-1]:.2f}"
            table = df[['Close', 'Volume']].tail(10).to_html()
    except Exception as e:
        error = str(e)
    return render_template_string(HTML, symbol=symbol, period=period, table=table, latest=latest, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
