FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE $PORT

CMD streamlit run railway_app.py --server.port=$PORT --server.address=0.0.0.0
