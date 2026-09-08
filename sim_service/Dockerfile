FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY etl_and_seed.py .
COPY live_simulator.py .
COPY entrypoint.sh .
COPY ../F1_Warehouse_Master_65_Columns_2004_2024.csv /app/F1_Warehouse_Master_65_Columns_2004_2024.csv

RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
