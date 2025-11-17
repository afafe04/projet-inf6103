FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système avec retry
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des bibliothèques Python avec retry et timeout plus long
RUN pip install --no-cache-dir --timeout=120 --retries=5 \
    pymodbus==3.5.4 \
    traci \
    sumolib || \
    pip install --no-cache-dir --index-url=https://pypi.tuna.tsinghua.edu.cn/simple \
    pymodbus==3.5.4 \
    traci \
    sumolib

# Copie des scripts
COPY sumo_modbus_bridge.py /app/
COPY modbus_registers.py /app/

# Exposition du port Modbus
EXPOSE 5020

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD nc -z localhost 5020 || exit 1

CMD ["python3", "sumo_modbus_bridge.py"]
