from flask import Flask, render_template_string, request
import yfinance as yf
import pandas as pd
import plotly
import plotly.graph_objs as go
import json
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Stock Predictor</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial; margin: 40px; }
        input, select { padding: 8px; margin: 5px; }
        button { padding: 8px 16px; background: #007bff; color: white; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <h1>?? Stock Market Predictor</h1>
    <form method="GET">
        Symbol: <input name="symbol" value="{{ symbol }}" placeholder="AAPL">
        Period: 
        <select name="period">
            {% for p in ['1d','5d','1mo','3mo','6mo','1y'] %}
            <option value="{{ p }}" {% if period==p %}selected{% endif %}>{{ p }}</option>
            {% endfor %}
        </select>
        <button type="submit">Analyze</button>
    </form>
    {% if graph_json %}
        <div id="chart"></div>
        <script>
            var graph = {{ graph_json | safe }};
            Plotly.newPlot('chart', graph.data, graph.layout);
        </script>
        <h3>Recent Data</h3>
        {{ data_table | safe }}
        <p>Latest Close: ${{ latest_price }}</p>
    {% endif %}
</body>
</html>
'''

@app.route('/')
def index():
    symbol = request.args.get('symbol', 'AAPL').upper()
    period = request.args.get('period', '1mo')
    graph_json = None
    data_table = None
    latest_price = None
    if symbol:
        try:
            df = yf.download(symbol, period=period, progress=False)
            if not df.empty:
                latest_price = f"{df['Close'].iloc[-1]:.2f}"
                # Create plotly chart
                fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close')])
                fig.update_layout(title=f'{symbol} Price', xaxis_title='Date', yaxis_title='Price (USD)')
                graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
                # Table
                data_table = df[['Close', 'Volume']].tail(10).to_html(classes='dataframe')
        except Exception as e:
            data_table = f"<p>Error: {e}</p>"
    return render_template_string(HTML_TEMPLATE, symbol=symbol, period=period, graph_json=graph_json, data_table=data_table, latest_price=latest_price)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
